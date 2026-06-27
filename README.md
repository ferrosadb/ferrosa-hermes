# ferrosa-hermes

**Ferrosa Memory integration for [Hermes Agent](https://hermes-agent.nousresearch.com)** — memory provider plugin, session hooks, and one-shot installer.

This repo makes [ferrosa-memory](https://github.com/ferrosadb/ferrosa-memory) available as a first-class memory provider in Hermes, alongside built-in providers like Honcho, Mem0, and Supermemory.

## What's Included

| Component | Description |
|-----------|-------------|
| `plugin/` | Hermes `MemoryProvider` plugin — bridges ferrosa-memory's MCP server to Hermes' memory lifecycle (prefetch, turn sync, consolidation) |
| `hooks/` | Session hook installer — creates session-start, recall, and turn-ingest hooks for Hermes, Claude Code, Codex, and Pi |
| `setup.sh` | One-shot installer — copies the plugin into Hermes, activates it, installs hooks, and verifies MCP connectivity |

## Quick Start

### Prerequisites

1. **Hermes Agent** installed — `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`
2. **ferrosa-memory** running — either via [setup-memory.sh](https://ferrosadb.com/setup-memory.sh) or [from source](https://github.com/ferrosadb/ferrosa-memory)

### Install

```bash
git clone https://github.com/ferrosadb/ferrosa-hermes.git
cd ferrosa-hermes
./setup.sh
```

Or with options:

```bash
./setup.sh --mcp-url http://user:pass@127.0.0.1:18765/mcp --harness hermes
```

### Verify

```bash
hermes memory status
# Expected: Provider: ferrosa, Plugin: installed ✓, Status: available ✓
```

Start a new Hermes session (`/reset` or restart) and the ferrosa memory provider will be active.

## How It Works

When ferrosa is set as the memory provider (`memory.provider: ferrosa` in config.yaml), Hermes automatically:

- **Prefetches** relevant memories before each turn via ferrosa-memory's semantic search
- **Syncs** conversation turns to ferrosa-memory as durable entities with temporal edges
- **Consolidates** on session end — ferrosa-memory discovers cross-session connections
- **Mirrors** built-in memory writes (MEMORY.md / USER.md) to the ferrosa-memory graph
- **Injects** memory status into the system prompt

The built-in memory (MEMORY.md / USER.md) continues to work alongside it — the ferrosa provider is additive.

## Memory Provider Architecture

The plugin (`plugin/__init__.py`) implements the Hermes `MemoryProvider` ABC by talking to ferrosa-memory's HTTP JSON-RPC MCP endpoint — no SDK needed, just raw `urllib`.

| ABC method | ferrosa-memory tool | Purpose |
|-----------|---------------------|---------|
| `prefetch(query)` | `search` | Semantic recall before each turn |
| `sync_turn(user, assistant)` | `ingest` / `ctx_ingest` | Persist conversation turns |
| `on_pre_compress(messages)` | `ctx_ingest` | Flush context before compression |
| `on_session_end(messages)` | `consolidate` | Cross-session consolidation |
| `on_memory_write(...)` | `ingest` | Mirror built-in memory writes |
| `system_prompt_block()` | `stats` | Show memory status in system prompt |

### Config Resolution

The plugin resolves its MCP endpoint URL in this order:

1. `FERROSA_MEMORY_URL` env var (highest priority)
2. `$HERMES_HOME/plugins/ferrosa/config.json`
3. `mcp_servers.ferrosa-memory.url` in Hermes config.yaml
4. Fallback: `http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp`

## Session Hooks

The hooks installer (`hooks/install-agent-hooks.py`) creates wrapper scripts under `~/.config/ferrosa-memory/hooks/` and patches harness config files:

| Harness | Config file patched | Hooks installed |
|---------|---------------------|-----------------|
| Hermes | `~/.hermes/config.yaml` | session-start, recall (pre_llm_call), ingest-turn (on_session_end) |
| Claude Code | `~/.claude/settings.json` | SessionStart, UserPromptSubmit, Stop, SubagentStop, PreCompact |
| Codex | `~/.codex/hooks.json` | SessionStart, UserPromptSubmit, Stop, SubagentStop, PreCompact |
| Pi | `~/.pi/agent/extensions/ferrosa-memory.ts` | before_agent_start, agent_end |

The session-memory loop:

1. **Session-start** → establishes the active ferrosa-memory session
2. **Pre-turn recall** → injects relevant memories for the current working directory
3. **Turn-end capture** → stores the trajectory and surrounding context
4. **Search/rerank** → uses cwd/workspace metadata to prefer knowledge from the same repo

## Configuration

```yaml
# ~/.hermes/config.yaml
memory:
  provider: ferrosa
mcp_servers:
  ferrosa-memory:
    url: http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp
    ssl_verify: false
    supports_parallel_tool_calls: true
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FERROSA_MEMORY_URL` | MCP endpoint URL (overrides config) | — |
| `FERROSA_MEMORY_TENANT_ID` | Tenant ID for multi-tenant deployments | — |
| `FERROSA_MEMORY_VERIFY_TLS` | Set `false` to skip TLS verification | `true` |

## Development

```bash
# Run the plugin's tests against a live ferrosa-memory instance
cd ~/.hermes/hermes-agent
scripts/run_tests.sh tests/plugins/memory/test_ferrosa_provider.py -q

# Verify the provider is active
hermes memory status
```

## License

MIT

## Related

- [ferrosa-memory](https://github.com/ferrosadb/ferrosa-memory) — the MCP server this plugin connects to
- [ferrosa](https://github.com/ferrosadb/ferrosa) — the database engine backing ferrosa-memory
- [Hermes Agent](https://hermes-agent.nousresearch.com) — the agent framework this plugin extends
- [Memory Provider Plugins docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers)