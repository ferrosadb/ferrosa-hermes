# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Start (ferrosa-memory first)

Before reading files or grepping:
1. `ferrosa-memory.check_intentions` with the current branch/context
2. `ferrosa-memory.hybrid_search` for the topic you're working on
3. `ferrosa-memory.retrieve_skills_for_context` to surface relevant skills

Only fall back to grep/find/read if memory genuinely doesn't have what you need. If you had to fall back, call `record_outcome` with `program_type="retrieval_miss"` so the system learns.

## What this repo is

`ferrosa-hermes` is the **integration glue** that makes [ferrosa-memory](https://github.com/ferrosadb/ferrosa-memory) usable as a memory backend for AI agent harnesses. It contains no product logic of its own — it is an installer plus a thin adapter. There are three deliverables, and they are independent:

1. **`plugin/`** — a Hermes `MemoryProvider` (and optional `SkillProvider`) that bridges Hermes' memory lifecycle to ferrosa-memory's MCP server.
2. **`hooks/install-agent-hooks.py`** — a harness-agnostic installer that writes lifecycle hook wrappers and patches the config of Hermes, Claude Code, Codex, and Pi.
3. **`setup.sh`** — the one-shot entry point that runs both of the above and verifies connectivity.

It is a sibling under `ferrosa-suite/` but is **not** a Rust/cargo project like the other sub-repos — it is pure Python + Bash with no build step and no committed test suite.

## Commands

There is nothing to build. Validate changes by exercising the scripts directly.

```bash
# Smoke-test the installer without touching any real config (always do this first)
python3 hooks/install-agent-hooks.py --harness all --dry-run --no-apply-config

# Full local install against a running ferrosa-memory (patches ~/.hermes, ~/.claude, etc.)
./setup.sh --mcp-url http://user:pass@127.0.0.1:18765/mcp --harness auto

# Install hooks only, with live verification of each generated wrapper
python3 hooks/install-agent-hooks.py --harness auto --mcp-url <url> --verify

# Plugin tests live in the HERMES tree after install, not in this repo:
cd ~/.hermes/hermes-agent
scripts/run_tests.sh tests/plugins/memory/test_ferrosa_provider.py -q
```

`setup.sh` flags: `--mcp-url`, `--harness {auto|all|codex|claude|hermes|pi|generic}`, `--no-hooks`, `--no-plugin`, `--dry-run`.

## Critical cross-repo dependency

**The installer depends on a file that does not live in this repo.** `install-agent-hooks.py` resolves `repo_root()/scripts/hooks/ferrosa-memory-turn-hook.py` and `raise SystemExit` if it is missing. That turn-hook helper (the script the generated wrappers actually `exec`) ships with **ferrosa-memory**, not here. So:

- The generated wrapper scripts are *launchers*; the recall/ingest logic they invoke is the ferrosa-memory turn-hook.
- Running `install-agent-hooks.py` from a bare checkout of *this* repo will fail at the `missing hook helper` check unless that path exists. In practice the installer is run from a tree where ferrosa-memory's `scripts/hooks/` is present.
- When changing wrapper invocation (the `--harness/--format/--mode/--event` flags in `create_wrappers`), keep them in sync with the turn-hook's CLI in ferrosa-memory.

## How the plugin works (`plugin/__init__.py`)

The plugin talks to ferrosa-memory over **raw JSON-RPC via `urllib`** — there is deliberately no client SDK dependency. `_McpClient` POSTs `tools/call` and unwraps MCP text content (JSON-decoding it when possible). It strips `user:pass@` userinfo from the URL into a Basic `Authorization` header itself (urllib won't do this reliably) and retries on HTTP 429 with backoff.

`FerrosaMemoryProvider` maps the Hermes `MemoryProvider` ABC onto fmem tools:

| ABC method | fmem tool | Notes |
|------------|-----------|-------|
| `is_available` / `system_prompt_block` | `get_stats` | availability probe + status line |
| `prefetch` | `hybrid_search` | top-5 semantic recall before a turn |
| `sync_turn` / `on_memory_write` | `smart_ingest` | persist turns; mirror MEMORY.md/USER.md writes |
| `on_session_end` | `run_consolidation` | cross-session dream/consolidation |

`get_tool_schemas` returns `[]` **by design** — the plugin is context-only. fmem tools are already exposed directly via the MCP server (under `fmem_*`), so re-exposing them would be duplicative. Don't add tool schemas here.

`FerrosaSkillProvider` exposes fmem's global skill catalog as virtual Hermes skills (namespace `fmem`) via `retrieve_skills_for_context` / `invoke_skill`. It is **optional**: `agent.skill_providers` only exists on newer Hermes builds, so the import is guarded by `_HAS_SKILL_PROVIDERS` and the provider only registers when both the import and `ctx.register_skill_provider` are present. Preserve this graceful-degradation pattern when editing — the core memory provider must still load on older Hermes (e.g. v0.17.0).

### URL resolution order

`_resolve_url`: `FERROSA_MEMORY_URL` env → saved `$HERMES_HOME/plugins/ferrosa/config.json` → fallback `http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp`. (The README also lists `mcp_servers.ferrosa-memory.url` from Hermes config.yaml as a layer; the plugin code itself reads the first three.)

### Session id mapping

Hermes session ids are not UUIDs, but ferrosa-memory requires UUID `session_id`s.
`plugin/session.py` maps the native id to a deterministic UUIDv5
(`resolve_session_namespace` + `ferrosa_session_id`); valid UUIDs pass through,
empty ids are omitted (server default applies). The mapped id is used in
`prefetch` (with `scope="both"`), `sync_turn`, `on_memory_write`, and
`on_session_end`. Override the namespace with `FERROSA_MEMORY_SESSION_NS`.
Keep the mapping pure/stdlib-only so it stays unit-testable without a Hermes install.

## How the installer works (`hooks/install-agent-hooks.py`)

Design stance: **conservative and idempotent**. It always writes wrappers + an `env` file + JSON/YAML snippets under `~/.config/ferrosa-memory/hooks/`, backs up any file it edits, and re-running it does not duplicate hooks (`ensure_hook` / `ensure_hook_with_entry` match on `command`).

Per-harness behavior differs and is intentional:
- **Claude Code** (`~/.claude/settings.json`) and **Codex** (`~/.codex/hooks.json`): patched in place (JSON). Events: `SessionStart`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`.
- **Hermes** (`~/.hermes/config.yaml`): patched **only** when the hooks block is literally `hooks: {}`. Any custom/non-empty block → snippet written, file left untouched (avoids clobbering hand-edited YAML; there's no YAML parser dependency).
- **Pi**: no config to patch — an auto-loaded TypeScript extension is written to `~/.pi/agent/extensions/ferrosa-memory.ts` from `PI_EXTENSION_TEMPLATE`. It shells out to the *same* wrapper scripts as every other harness, so there is one hook implementation.

Two hard-won safety checks — keep them, they encode real footguns:
- `validate_auth_header` rejects empty/multi-line values and the literal `Basic <base64 user:password>` placeholder (a `grep` once captured the commented template line, producing a two-line header urllib rejected at request time).
- `probe_auth_required` + `auth_consistency_error` preflight: if the endpoint returns 401/403 unauthenticated but no usable credentials are configured, the installer **refuses to install** rather than silently produce hooks that 401. Override with `--skip-auth-check`.

The hook `env` file is written `0o600` and carries tuning knobs (`FERROSA_MEMORY_HOOK_*`). Note `FERROSA_MEMORY_TENANT_ID` must match the authenticated principal's tenant or ingests are silently dropped server-side.

## Two Hermes install layouts (`setup.sh`)

`setup.sh` detects and supports both — get this right when touching the plugin install path:
- **host**: `$HERMES_HOME/hermes-agent` exists → plugin goes to `$HERMES_HOME/hermes-agent/plugins/memory/ferrosa`.
- **container**: official image, `hermes` CLI on PATH, agent read-only at `/opt/hermes` → plugin goes to `$HERMES_HOME/plugins/ferrosa`.

`hermes config set memory.provider ferrosa` is treated as **non-fatal** (some installs provision the home dir separately) — it warns instead of aborting, since the provider also activates via config.yaml/env.

## Conventions

- **Fail loud, never fake** is the house style across the suite, but note these scripts deliberately **fail-open at runtime**: hook wrappers and the Pi extension must never block or break the host agent if ferrosa-memory is down. Install-time checks fail loud (auth preflight, missing helper); runtime memory operations degrade silently with a debug log. Don't "fix" the runtime `except Exception: logger.debug(...)` swallows into hard failures — that is the intended posture for a non-critical memory sidecar.
- No third-party Python dependencies. Standard library only (`urllib`, `json`, `ssl`, `pathlib`). Keep it that way — the plugin runs inside whatever Python the host harness provides.
- This repo's own work is committed/PR'd here (it has a real GitHub remote, unlike most ferrosa-suite sub-repos). Standard branch-before-change rules apply.
