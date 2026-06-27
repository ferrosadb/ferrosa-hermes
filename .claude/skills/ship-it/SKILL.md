---
name: "ship-it"
# prettier-ignore
description: "Discovers all local branches, tests each, pushes passing ones as PRs, monitors CI, and cleans up superseded branches. Use when asked to 'ship it', 'push everything', or 'clean up branches'."
tags: [repo-workflow]
argument-hint: "[int|integrate] [--dry-run] [--skip-cleanup] [branch-filter]"
supplementary-files:
  - ship-strategies.md
---

# Ship It — Multi-Branch Integration Workflow

Discover all local branches and worktrees, validate each one, push PRs for branches that pass, monitor CI to completion, and clean up superseded work.

## Before you start (memory-first)

Before reading files or grepping:

1. `ferrosa-memory.hybrid_search` on active branch names and work items
2. `ferrosa-memory.retrieve_skills_for_context` with tags `task-level`, `ship-it`, `repo-workflow`
3. `ferrosa-memory.check_intentions` — act on any triggered intentions

If memory tracks branch ownership or in-flight PRs, prefer those hints. On fallback, call `record_outcome` with `program_type="retrieval_miss"`. Escape-hatch tools: see `skills/quality/skill-dev-methodology-quality-gates.v2.md` § "ferrosa-memory Integration".

## Forge tools

| Step | frg command | What it does |
|------|-------------|--------------|
| Step 1 (discover) | `frg git-summary` | Branch and worktree inventory |
| Step 3 (test) | `frg test-summary` | Last-known test results by branch |
| Step 4 (ship) | `frg merge-check` | Conflict prediction before pushing |
| Step 5 (monitor) | `frg log-monitor` | Tail CI logs during polling |

Fallback to raw Bash (git/gh) must be logged (see `skills/rules/safety.md`).

## Markdown Output

Pull request bodies and integration summaries are Markdown fragments. Follow
`/markdown-writing` style and start generated PR bodies with `## Executive
Summary` instead of YAML front matter.

## Arguments

- `$ARGUMENTS` - Optional mode, flags, and filters:
  - `int` or `integrate` — Merge all passing branches into one integration branch and create a single PR (see Integrate Mode)
  - `--dry-run` — Discovery and testing only, no push/PR/cleanup
  - `--skip-cleanup` — Ship but don't delete superseded branches
  - `<branch-filter>` — Glob pattern to limit scope (e.g., `feature/*`)

## Overview

```
Phase 1: Discover    — enumerate branches + worktrees
Phase 2: Assess      — classify each (merged, superseded, active, stale)
Phase 3: Test        — run project tests per branch
Phase 4: Ship        — push + create PRs for passing branches
  4a: Integrate mode — merge all passing into one branch, single PR
Phase 5: Monitor     — poll CI status until all PRs resolve
Phase 6: Cleanup     — remove merged/superseded branches and worktrees
```


## Instructions

### Step 1: Discover Branches and Worktrees

See `ship-strategies.md` in this skill folder for the full branch discovery commands and inventory table format.

**Skip:** `main`, `master`, and the default branch itself.

**If `$ARGUMENTS` contains a branch filter**, only include matching branches.

### Step 2: Assess Each Branch

Classify each branch as `merged`, `superseded`, `active`, `dirty`, `stale`, or `has-pr`. See `ship-strategies.md` in this skill folder for classification rules, superseded detection (including cherry-based detection for rebased branches), and stale branch policies.

**Present the assessment table to the user and wait for confirmation before proceeding.**

### Step 3: Test Each Active Branch

For each branch classified as `active` or `has-pr`:

1. If branch has a worktree, use it; otherwise create a temporary worktree
2. Detect project type and run tests using the forge MCP server when available

| Indicator | Test Command | Forge MCP Tool |
|-----------|-------------|---------------------|
| `Cargo.toml` | `cargo test` | `cargo` (command: "test") |
| `package.json` | `npm test` | `npm_tools` (command: "test") |
| `mix.exs` | `mix test` | `mix_test` |
| `go.mod` | `go test ./...` | `go_tools` (command: "test") |
| `pyproject.toml` / `setup.py` | `pytest` | `python_tools` (command: "test") |
| `Makefile` with `test` target | `make test` | (use Bash) |

3. Record results per branch
4. Clean up temporary worktrees

**Update the inventory with test results.** If `--dry-run`, stop here and report.

### Step 4: Ship Passing Branches

**If `$ARGUMENTS` contains `int` or `integrate`**, skip to Integrate Mode (Phase 4a below).

For each branch that passed tests and is classified `active`:

1. **Push to remote:** `git push -u origin <branch>`
2. **Check for existing PR:** `gh pr list --head <branch> --json number,url,state --jq '.[0]'`
3. **Create PR if none exists** with conventional title and structured body (summary, changes, stats, test plan)
4. **Record PR URL and number**

**Use parallel agents** when shipping multiple independent branches.

#### Step 4a: Integrate Mode

**Activated when `$ARGUMENTS` contains `int` or `integrate`.**

Merge all passing branches into one integration branch and create a single PR. This is **all-or-nothing** — if any merge conflicts or tests fail, the integration branch is deleted.

See `ship-strategies.md` in this skill folder for the full integration workflow (create branch, merge ordered by commit date, abort on conflict, test merged result, build combined PR body, push and create single PR, report).

**Key safety rules for integrate mode:**
- If any merge conflict → abort immediately, delete integration branch, leave source branches untouched
- If integration tests fail → abort, delete integration branch, report which branch introduced the failure
- After integration PR passes CI, all source branches become cleanup candidates (confirm before deleting)

### Step 5: Monitor CI

Poll CI status on all shipped PRs until they resolve.

- First check: immediately after all PRs created
- Subsequent checks: every 30 seconds
- Timeout: 10 minutes (then report status and stop polling)

See `ship-strategies.md` in this skill folder for detailed CI monitoring patterns and failure handling.

**If a PR fails CI:** Report failing checks, do NOT auto-close or auto-fix. Suggest: "PR #N has CI failures. Fix locally and push, or close with `gh pr close N`"

### Step 6: Cleanup

**Only runs if not `--dry-run` and not `--skip-cleanup`.**

See `ship-strategies.md` in this skill folder for detailed cleanup procedures covering:
- Merged branches (local + remote deletion)
- Superseded branches (confirm before deleting)
- PRs that passed CI (report ready-to-merge, never auto-merge)
- Integration mode cleanup (source branches after CI passes)
- Worktree cleanup safety checks

### Final Report

```
Ship It — Summary
=================
Discovered:  5 branches, 1 worktree
Assessed:    2 active, 1 merged, 1 superseded, 1 stale
Tested:      2 branches (2 passed, 0 failed)
Shipped:     2 PRs created
CI:          2 passed, 0 failed
Cleaned up:  2 branches removed (1 merged, 1 superseded)

Open PRs:
  #47 feature/auth           READY TO MERGE
  #48 feature/new-api        READY TO MERGE

Skipped:
  feature/experiment         stale (last commit 4 months ago)
```

## Error Handling

| Error | Recovery |
|-------|----------|
| `gh` not installed | Stop, suggest `brew install gh` or `apt install gh` |
| `gh auth` fails | Stop, suggest `! gh auth login` |
| Push rejected (non-fast-forward) | Report conflict, skip branch, continue others |
| Worktree locked | Report, skip branch, continue others |
| Test timeout (>5 min) | Kill, mark as `test-timeout`, skip |
| CI poll timeout (>10 min) | Report current status, stop polling |

## Safety Rules

- **Never force-push.** If push is rejected, report and skip.
- **Never auto-merge PRs.** Report ready-to-merge status only.
- **Never delete branches without classification.** Only `merged` and confirmed `superseded`.
- **Always confirm before deleting superseded branches.**
- **Never delete `main`, `master`, or the default branch.**
- **Dirty branches are never shipped.** Report and skip.
- **Stale branches require user decision.** Don't auto-delete.

## Integration

**Builds on:**
- `/repo/push-it` — PR creation patterns
- `/repo/commit-it` — Branch naming conventions
- `superpowers:using-git-worktrees` — Worktree management
- `superpowers:finishing-a-development-branch` — Single-branch completion

**Pairs with:**
- `/repo/commit-it` — Commit outstanding work before shipping
- `superpowers:verification-before-completion` — Test verification discipline

## Notes

- Uses parallel agents for testing and shipping independent branches
- Prefers MCP forge over raw Bash for test execution
- All destructive operations (branch deletion) require user confirmation
- CI monitoring uses `gh pr checks`, not direct API polling
- **IMPORTANT: Do NOT add `Co-Authored-By`, `Generated with AI`, or any AI/Claude attribution to PR titles or descriptions.**
