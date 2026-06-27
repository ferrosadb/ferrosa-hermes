---
name: python
description: Python with pytest, type hints, pandas/NumPy, and virtual environments. Use when writing Python code, configuring projects, building data pipelines, or debugging Python applications.
tags: [languages]
argument-hint: <task-or-module> [--framework flask|fastapi|pytest]
supplementary-files:
  - static-perf.md
  - references/toolchain-install.md
  - references/external-data-e2e-seeding.md
---


Version date: 2026-01-28

# Shared Policy: Literate + Tests + CI Gates

This language skill implements the project-wide literate and quality-gate rules:

- Literate programming: narrative (intent, invariants, rationale) is first-class, and docs are generated from code in CI. Doc drift is a defect.
- CI gates are mandatory for every PR and main build.
- Coverage is measured and gated. Baseline new/changed code line coverage >= 80%.
- Cyclomatic complexity is measured per function/method and gated.
- Complexity-coverage coupling (defaults):
  - CC >= 15: coverage >= 90% line and >= 80% branch (if available) AND explicit local documentation for the unit.
  - CC >= 25: coverage >= 95% line and >= 90% branch (if available) AND a refactor plan or explicit waiver.
- Pragmatic testing: do not require tests for trivial, logic-free accessors unless they embed logic or are safety-critical.
- Semantic Versioning (SemVer 2.0.0): multi-component projects use independent semver per component. API changes follow contract-first development with OpenAPI specs. See `semver-api.skill.md`.

## Functional streaming & persistent data structures

Default to immutable/persistent, structurally-shared data and lazy, composable stream pipelines — even though Python is not functional-first. For state shared across threads, prefer a lock-free immutable value behind an atomic reference over locking a mutable collection.

Python idioms: generators + `itertools` (`islice`, `chain`, `groupby`, `tee`), `yield from`, and `async` generators / `async for` for lazy streams; `asyncio.Queue` (bounded) for backpressured/CSP-style pipelines; **pyrsistent** (`PVector`/`PMap`) for persistent collections.

Escalate when designing data pipelines or concurrent/shared state:
- `skills/task-level/fp-patterns/streaming-catalog.md` — lazy iterators · transducers · staged/backpressured · channels/CSP
- `skills/task-level/fp-patterns/persistent-data-structures.md` — persistent collections + lock-free sharing (atomic swap / CAS)

## Before you start (memory-first)

Before reading files or grepping:
1. `ferrosa-memory.hybrid_search` on the task topic + key nouns in `$ARGUMENTS`
2. `ferrosa-memory.retrieve_skills_for_context` with tags `tech`, `languages`, `python`
3. `ferrosa-memory.check_intentions` — act on any triggered intentions

On fallback, call `record_outcome` with `program_type="retrieval_miss"`. Escape-hatch tools: see `skills/quality/skill-dev-methodology-quality-gates.v2.md` § "ferrosa-memory Integration".

## Forge tools

| Step | frg command | What it does |
|------|-------------|--------------|
| 1 Detect | `frg project-detect` | Identify `pyproject.toml`, `requirements*.txt`, `uv.lock` |
| 1 Summary | `frg project-summary` | Dependency + script inventory |
| 2 Outline | `frg module-outline` | Extract module shape without bodies |
| 3 Coverage | `frg coverage-gate` | CC-coupled coverage thresholds |
| 3 Docs | `frg doc-coverage` | Flag public APIs missing docstrings |
| 4 Tests | `frg test-summary` | Distill pytest output |
| 5 Format | `frg format-fix` | black/ruff format wrapper |
| 5 Lint | `frg lint-dedup` | Collapse ruff/mypy noise |
| 6 Deps | `frg deps-audit` | Wrap pip-audit / pip-licenses |

Fallback: if forge is unavailable, run `ruff check`, `black --check`, `pytest -q`, `pip-audit --strict` directly. Log the fallback (`skills/rules/safety.md`).

## Canonical References
- Python official documentation and standard library docs.
- PEP 8 for style, plus team formatter/linter conventions.

## Progressive Corpus Reference

Use references in this order:

1. This skill for default Python guidance.
2. **`references/toolchain-install.md`** — what to install for every tool below and how, per platform, with a check-then-install procedure. Consult it whenever a referenced tool is missing instead of skipping the gate.
3. `static-perf.md` for static performance patterns; `references/external-data-e2e-seeding.md` for external-data E2E test seeding.
4. Local repo conventions and tests.
5. `corpus/python/` for deeper Python-specific book references.
6. `corpus/ml-ai/` when the task is Python-based ML, deep learning, NLP, or data pipelines.
7. `corpus/downloads-import-2026-04-11.md` to find the imported titles by bucket if you need to browse.

Do not load the corpus by default. Use it only when idiom, architecture, or library tradeoffs need more depth than the skill provides.

## Instructions

### Step 1: Detect project setup

Run `frg project-detect` and `frg project-summary` to verify Python toolchain: `pyproject.toml` (preferred), `requirements*.txt`, a lockfile (`uv.lock`, `poetry.lock`, or pinned `requirements.txt`), and virtualenv marker. Refuse to install without a lockfile — unpinned installs defeat supply chain guarantees.

**Toolchain check.** Before running any gate, confirm the tools it needs are installed (`command -v ruff`, `command -v mypy`, etc.). If one is missing, install it from **`references/toolchain-install.md`** (check-then-install, matched to the project's manager — uv/poetry/pip) and log the install — never silently skip a gate because a tool is absent (`skills/rules/safety.md`).

### Step 2: Apply literate-programming front matter

Every new or materially changed non-trivial Python source file must start with a module docstring acting as literate front matter, answering: responsibility, correctness signal, `Last revised: YYYY-MM-DD`, `Last changed:` (one sentence).

```python
"""
Module: Parse and normalize inbound webhook payloads into internal events.
Correctness: Correct when malformed payloads are rejected, valid payloads normalize deterministically, and regression/property tests stay green.
Last revised: 2026-04-11
Last changed: Tightened idempotency-key validation and normalized timestamp parsing.
"""
```

Rules:
- Keep it brief: 4-8 lines, high signal only.
- Update `Last revised` and `Last changed` whenever behavior, invariants, or external contracts change.
- Pure formatting, renames with no semantic effect, or import reordering do not require churning this block.

Use docstrings as the primary narrative surface: module docstring for purpose/invariants/design choices; class/function docstring for intent, parameters, returns, errors, edge cases. Use ADRs (Markdown) for cross-cutting decisions. Generate docs in CI (Sphinx autodoc or pdoc) and publish as artifact.

### Step 3: Enforce CI quality gates

CI minimum (drive via `frg coverage-gate` + language-specific tools):

1) Format: black (or team formatter) and import sort
2) Lint: ruff (or flake8) + typecheck if used (mypy/pyright)
3) Tests: pytest
4) Coverage: coverage.py via pytest-cov
5) Complexity: radon cc (or equivalent) + gating thresholds
6) Docs: Sphinx build (or pdoc) + publish as artifact
7) **Dependency advisories**: `pip-audit --strict` — fails on any known CVE in the dependency tree
8) **License compliance**: `pip-licenses --fail-on='GPL.*;AGPL.*;BUSL.*;CC-BY-NC.*'` — flag copyleft licenses for review

Gate configuration: baseline new/changed line coverage >= 80%. CC >= 15 requires 90% line + 80% branch coverage + explicit local docs; CC >= 25 requires 95% line coverage + refactor plan/waiver.

### Step 4: Run tests

- Unit tests: pytest for pure logic; keep I/O at edges.
- Property tests: hypothesis for path-rich logic (see below).
- Integration tests for external boundaries (DB, services) with fixtures and test containers if needed.
- For external-data E2E seed/backfill paths, use the pattern in `references/external-data-e2e-seeding.md`: explicit real-provider modes fail loud on missing keys/dependencies, fixture modes are deterministic, and verification reads back through the same public catalog/API path.
- For DuckDB over partitioned Parquet with a local S3-compatible smoke test, use `references/duckdb-minio-s3-catalog.md`: write via PyArrow S3 filesystem, read via DuckDB `httpfs` + S3 secret, and verify through the public catalog/API boundary.
- Avoid testing the compiler: do not add tests for trivial accessors.

Pragmatic testing applies. Use `frg test-summary` to distill pytest output.

**Property-Based Testing (Hypothesis)** — basic usage:

```python
# pip install hypothesis
from hypothesis import given, settings, example
import hypothesis.strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
```

Settings profiles in `conftest.py`:

```python
import os
from hypothesis import settings, HealthCheck, Phase

settings.register_profile("dev", max_examples=100, deadline=200)
settings.register_profile("ci", max_examples=1000, deadline=None,
                           derandomize=True, print_blob=True)
settings.register_profile("fast", max_examples=10, deadline=None)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
```

Regression prevention — `.hypothesis/examples/` stores shrunken failing cases. `.gitignore`: add `.hypothesis/*` then `!.hypothesis/examples/` (commit the examples dir). `@example(x=value)` — permanent regression pin; `@reproduce_failure('version', blob)` — temporary replay. Workflow: CI fails → blob printed → reproduce locally → pin with `@example` → delete blob decorator.

Stateful testing uses `RuleBasedStateMachine`. Health checks: fix the root cause, don't suppress. Suppressing `HealthCheck.all()` hides real performance problems.

### Step 5: Lint and format

Use `frg format-fix` (black/ruff formatter) and `frg lint-dedup` (dedupe ruff/mypy noise). Fast local loop: `ruff check .`, `black --check .`, `pytest -q`. Coverage: `pytest --cov=PACKAGE --cov-report=term-missing`.

### Step 6: Audit supply chain

Python packages can introduce known CVEs via transitive dependencies. Use two complementary tools via `frg deps-audit` or directly:

```bash
pip install pip-audit
pip-audit                              # audit current environment
pip-audit -r requirements.txt          # audit from requirements file
pip-audit --strict                     # CI mode: non-zero exit on any finding
```

For projects using `uv`: `uv run pip-audit --strict`.

License compliance: `pip-licenses --fail-on='GPL.*;AGPL.*;BUSL.*;CC-BY-NC.*'`.

Pre-commit hook (advisory) + pre-push (strict):

```yaml
  - repo: local
    hooks:
      # Pre-commit: advisory check
      - id: pip-audit-<project-name>
        name: pip-audit (<project-name>)
        entry: bash -c 'cd <project-path> && uv run pip-audit -r requirements.txt'
        language: system
        files: ^<project-path>/requirements.*\.txt$|^<project-path>/pyproject\.toml$
        pass_filenames: false

      # Pre-push: strict mode — non-zero exit on any advisory
      - id: pip-audit-strict-<project-name>
        name: pip-audit strict (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && uv run pip-audit --strict'
        language: system
        files: ^<project-path>/requirements.*\.txt$|^<project-path>/pyproject\.toml$
        pass_filenames: false
```

When a CVE blocks you:

1. Identify: `pip-audit --format json | jq '.dependencies[].vulns[]'`
2. If a fix exists: `pip install --upgrade <package>` and re-lock (`uv lock`)
3. If no fix: add `--ignore-vuln GHSA-XXXX-XXXX-XXXX` with a documented comment and review date
4. Never ignore an RCE or credential-exfiltration advisory without team sign-off

## Reference

### Failure Philosophy

> **Fail loud, Erlang-style. Never fake success.**
>
> Priority: (1) works correctly, (2) falls back visibly with clear signal, (3) fails with clear error, (4) never silently degrades to look fine.
> A crash with a stack trace is debuggable. Silent degradation that returns wrong data is not. See `skills/rules/safety.md` for the full failure philosophy.

### Refactoring Loop (Tiny Steps)

- Extract pure functions to reduce branching.
- Add seams for I/O boundaries (dependency injection, adapters).
- When cyclomatic complexity stays high, add documentation + stronger tests per policy.

### Debugging with pdb / ipdb / debugpy

Python's built-in `pdb` is always available. `ipdb` adds IPython features. `debugpy` enables VS Code and remote debugging.

```python
# Built-in (always available, no install)
breakpoint()          # Python 3.7+ — respects PYTHONBREAKPOINT env var

# Or explicitly
import pdb; pdb.set_trace()
import ipdb; ipdb.set_trace()

# Conditional
if count > 1000:
    breakpoint()
```

Running under the debugger:

```bash
python -m pdb script.py
pytest --pdb                    # Drop into pdb on first failure
pytest --pdb -x                 # Stop after first failure + debug
python -m pdb -c continue script.py   # Run until crash, then debug
python -m ipdb script.py
pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

Essential pdb commands:

| Command | Purpose |
|---------|---------|
| `n` (next) | Step over |
| `s` (step) | Step into function call |
| `c` (continue) | Run until next breakpoint |
| `r` (return) | Run until current function returns |
| `l` / `ll` | Show source / show entire function |
| `p expr` / `pp expr` | Print / pretty-print expression |
| `w` | Stack trace |
| `u` / `d` | Up / down the call stack |
| `b file:line` / `b func` | Set breakpoint |
| `condition N expr` | Conditional breakpoint |
| `commands N` | Commands on breakpoint hit |
| `interact` | Interactive shell at frame (pdb 3.13+) |

Key patterns:

- **Post-mortem debugging** — `import pdb; pdb.pm()` opens a debugger at the exception site.
- **Debug a specific test** — `pytest --pdb -k "test_parse_header"`.
- **Remote debugging with debugpy** — `debugpy.listen(5678)` + `debugpy.wait_for_client()`.
- **Debugging in notebooks** — `%debug` magic after an exception.
- **PYTHONBREAKPOINT env var** — `PYTHONBREAKPOINT=ipdb.set_trace` or `=0` to disable.

Supplementary tools:

| Tool | Purpose |
|------|---------|
| `ipdb` | IPython-powered pdb |
| `debugpy` | VS Code / DAP debugger (remote capable) |
| `pudb` | Full-screen TUI debugger |
| `py-spy` | Sampling profiler (no code changes) |
| `traceback` module | Programmatic stack trace formatting |
| `faulthandler` | Dump tracebacks on segfaults/hangs |
| `objgraph` | Visualize object reference graphs |

See also: `/debug` skill for the full systematic debugging methodology.

### PR Checklist

- [ ] Docstrings updated where intent/invariants changed
- [ ] Tests updated/added (pytest, hypothesis where needed)
- [ ] Coverage and complexity gates satisfied
- [ ] Docs build in CI
- [ ] `pip-audit` passes (no unpatched CVEs in dependency tree)
- [ ] License compliance verified (no unexpected copyleft dependencies)
- [ ] CI green
