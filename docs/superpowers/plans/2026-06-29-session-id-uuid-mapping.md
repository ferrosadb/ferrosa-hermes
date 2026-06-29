# Session-ID UUID Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Map Hermes' native session id to a deterministic ferrosa-memory session UUID in the provider, so sessions stop collapsing into the server default while preserving cross-session recall.

**Architecture:** A pure, stdlib-only module (`plugin/session.py`) provides UUIDv5 mapping + namespace resolution. `plugin/__init__.py` applies the mapping in `initialize` and threads the mapped UUID through `prefetch` (with `scope="both"`), `sync_turn`, `on_memory_write`, and `on_session_end`. An in-repo `unittest` suite covers the pure module and runs in CI.

**Tech Stack:** Python 3.12, standard library only (`uuid`, `os`, `importlib`), `unittest`, pre-commit (ruff/bandit), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-06-29-session-id-uuid-mapping-design.md`

**Branch:** `fix/session-id-uuid-mapping` (already created from `origin/main`).

---

## Task 1: Pure session-mapping module (TDD)

**Files:**
- Create: `plugin/session.py`
- Test: `tests/test_session.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_session.py`. It loads `plugin/session.py` directly by path so it does **not** import the `plugin` package (whose `__init__.py` imports `agent.*`, unavailable in CI).

```python
import importlib.util
import unittest
import uuid
from pathlib import Path

_SESSION_PATH = Path(__file__).resolve().parents[1] / "plugin" / "session.py"
_spec = importlib.util.spec_from_file_location("ferrosa_session_under_test", _SESSION_PATH)
session = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(session)


class FerrosaSessionIdTests(unittest.TestCase):
    def setUp(self):
        self.ns = session.DEFAULT_SESSION_NS

    def test_deterministic(self):
        a = session.ferrosa_session_id("20260628_134834_d90c1c66", self.ns)
        b = session.ferrosa_session_id("20260628_134834_d90c1c66", self.ns)
        self.assertEqual(a, b)

    def test_distinct_inputs_distinct_uuids(self):
        a = session.ferrosa_session_id("session-a", self.ns)
        b = session.ferrosa_session_id("session-b", self.ns)
        self.assertNotEqual(a, b)

    def test_output_is_valid_uuid(self):
        out = session.ferrosa_session_id("anything", self.ns)
        self.assertEqual(str(uuid.UUID(out)), out)

    def test_valid_uuid_passthrough(self):
        existing = "b4c62491-fb35-4fbb-b670-5f29dd2d5adf"
        self.assertEqual(session.ferrosa_session_id(existing, self.ns), existing)

    def test_empty_and_none_return_none(self):
        self.assertIsNone(session.ferrosa_session_id("", self.ns))
        self.assertIsNone(session.ferrosa_session_id("   ", self.ns))
        self.assertIsNone(session.ferrosa_session_id(None, self.ns))


class ResolveSessionNamespaceTests(unittest.TestCase):
    def test_blank_returns_default(self):
        self.assertEqual(session.resolve_session_namespace({}), session.DEFAULT_SESSION_NS)
        self.assertEqual(
            session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": "  "}),
            session.DEFAULT_SESSION_NS,
        )

    def test_uuid_env_used_directly(self):
        ns = "11111111-1111-1111-1111-111111111111"
        self.assertEqual(
            session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": ns}),
            uuid.UUID(ns),
        )

    def test_arbitrary_string_env_derives_stable_namespace(self):
        env = {"FERROSA_MEMORY_SESSION_NS": "team-alpha"}
        ns1 = session.resolve_session_namespace(env)
        ns2 = session.resolve_session_namespace(env)
        self.assertEqual(ns1, ns2)
        self.assertNotEqual(ns1, session.DEFAULT_SESSION_NS)

    def test_namespace_override_changes_mapping(self):
        default_out = session.ferrosa_session_id("s1", session.DEFAULT_SESSION_NS)
        other_ns = session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": "team-alpha"})
        self.assertNotEqual(session.ferrosa_session_id("s1", other_ns), default_out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: FAIL — `FileNotFoundError`/`exec_module` error because `plugin/session.py` does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

Create `plugin/session.py`:

```python
"""Pure, dependency-free mapping of harness-native session ids to ferrosa-memory
session UUIDs.

ferrosa-memory requires ``session_id`` to be a UUID (it reaches CQL partition
keys). Hermes' native session ids are not UUIDs, so this adapter maps them
deterministically. UUIDv5 is used so the mapping is stateless (no lookup table)
and stable across horizontally-scaled Hermes instances and ferrosa-memory
replicas.

This module imports nothing from ``agent.*`` so it can be unit-tested without a
Hermes install.
"""

from __future__ import annotations

import os
import uuid
from typing import Optional

# Stable default namespace for deriving ferrosa-memory session UUIDs from
# harness-native session ids. Minted once; DO NOT change — altering it re-keys
# every existing Hermes->ferrosa session mapping.
DEFAULT_SESSION_NS = uuid.UUID("ea88216a-73a3-447a-85e5-6176640ac4ac")

_NAMESPACE_ENV = "FERROSA_MEMORY_SESSION_NS"


def resolve_session_namespace(env: Optional[dict] = None) -> uuid.UUID:
    """Resolve the UUIDv5 namespace.

    ``FERROSA_MEMORY_SESSION_NS`` may be a UUID (used directly) or any string (a
    stable namespace is derived from it). Blank/unset falls back to
    ``DEFAULT_SESSION_NS``.
    """
    env = os.environ if env is None else env
    raw = (env.get(_NAMESPACE_ENV) or "").strip()
    if not raw:
        return DEFAULT_SESSION_NS
    try:
        return uuid.UUID(raw)
    except ValueError:
        return uuid.uuid5(DEFAULT_SESSION_NS, raw)


def ferrosa_session_id(raw, namespace: uuid.UUID) -> Optional[str]:
    """Map a harness-native session id to a ferrosa-memory session UUID string.

    - empty / None    -> ``None`` (caller omits session_id; server default applies)
    - already a UUID   -> returned unchanged (matches ferrosa-memory's contract)
    - any other string -> deterministic ``uuid5(namespace, raw)``
    """
    s = ("" if raw is None else str(raw)).strip()
    if not s:
        return None
    try:
        return str(uuid.UUID(s))
    except ValueError:
        return str(uuid.uuid5(namespace, s))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: PASS — 9 tests OK.

- [ ] **Step 5: Run pre-commit on the new files**

Run: `pre-commit run --files plugin/session.py tests/test_session.py`
Expected: PASS (ruff-format may reformat; re-run until clean).

- [ ] **Step 6: Commit**

```bash
git add plugin/session.py tests/test_session.py
git commit -m "feat(plugin): deterministic UUIDv5 mapping for session ids"
```

---

## Task 2: Wire the mapping into the provider

**Files:**
- Modify: `plugin/__init__.py` (imports; `__init__`; `initialize`; `_sid` helper; `prefetch`; `sync_turn`; `on_memory_write`; `on_session_end`)

- [ ] **Step 1: Add the import (defensive: package-relative with path-load fallback)**

Find the optional skill-providers import block near the top of `plugin/__init__.py`:

```python
try:
    from agent.skill_providers import SkillMetadata, SkillPayload

    _HAS_SKILL_PROVIDERS = True
except Exception:  # pragma: no cover - depends on host Hermes version
    SkillMetadata = SkillPayload = None  # type: ignore[assignment]
    _HAS_SKILL_PROVIDERS = False
```

Immediately AFTER that block, add:

```python
import uuid

# Pure session-mapping helpers. Prefer the package-relative import; fall back to
# loading the sibling module by path for hosts that load this file as a
# standalone module rather than a package.
try:
    from .session import (
        DEFAULT_SESSION_NS,
        ferrosa_session_id,
        resolve_session_namespace,
    )
except ImportError:  # pragma: no cover - non-package load path
    import importlib.util as _ilu
    from pathlib import Path as _Path

    _sp = _ilu.spec_from_file_location(
        "ferrosa_session", _Path(__file__).with_name("session.py")
    )
    _sm = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(_sm)
    DEFAULT_SESSION_NS = _sm.DEFAULT_SESSION_NS
    ferrosa_session_id = _sm.ferrosa_session_id
    resolve_session_namespace = _sm.resolve_session_namespace
```

- [ ] **Step 2: Extend `__init__` state**

Replace:

```python
    def __init__(self):
        self._url: Optional[str] = None
        self._client: Optional[_McpClient] = None
        self._session_id: str = ""
        self._tenant_id: str = ""
        self._hermes_home: str = ""
        self._saved_config: Dict[str, Any] = {}
```

with:

```python
    def __init__(self):
        self._url: Optional[str] = None
        self._client: Optional[_McpClient] = None
        self._session_id: str = ""
        self._ferrosa_session_id: str = ""
        self._session_ns: uuid.UUID = DEFAULT_SESSION_NS
        self._tenant_id: str = ""
        self._hermes_home: str = ""
        self._saved_config: Dict[str, Any] = {}
```

- [ ] **Step 3: Map the session id in `initialize`**

Replace the first line of `initialize`:

```python
    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
```

with:

```python
    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._session_ns = resolve_session_namespace()
        self._ferrosa_session_id = ferrosa_session_id(session_id, self._session_ns) or ""
```

- [ ] **Step 4: Add the `_sid` helper**

Insert this method directly AFTER `initialize` (before `system_prompt_block`):

```python
    def _sid(self, per_call: str = "") -> Optional[str]:
        """Map a (per-call or initialized) session id to a ferrosa-memory UUID."""
        return ferrosa_session_id(per_call or self._session_id, self._session_ns)
```

- [ ] **Step 5: Fix `prefetch` (cross-session scope + mapped session id)**

Replace:

```python
            # Use hybrid_search for broad recall
            result = self._client.call(
                "hybrid_search",
                {
                    "query": query,
                    "limit": 5,
                },
            )
```

with:

```python
            # Use hybrid_search for broad recall. scope="both" spans the current
            # session AND tenant-global consolidated/curated memory so recall
            # stays cross-session even though writes are session-scoped.
            args: Dict[str, Any] = {"query": query, "limit": 5, "scope": "both"}
            sid = self._sid(session_id)
            if sid:
                args["session_id"] = sid
            result = self._client.call("hybrid_search", args)
```

- [ ] **Step 6: Map the session id in `sync_turn`**

Replace the body of `sync_turn` (both `smart_ingest` calls) with the version below. The `session_id` field becomes the mapped UUID (omitted when `None`); `entity_name`/`content` keep the human-readable raw id for readability.

```python
    def sync_turn(
        self, user_content: str, assistant_content: str, *, session_id: str = ""
    ) -> None:
        if not self._client:
            return
        label = session_id or self._session_id
        sid = self._sid(session_id)
        try:
            args: Dict[str, Any] = {
                "content": f"User turn in session {label}: {user_content[:800]}",
                "entity_type": "conversation_turn",
                "entity_name": f"user-{label}",
            }
            if sid:
                args["session_id"] = sid
            self._client.call("smart_ingest", args)
        except Exception as e:
            logger.debug("ferrosa sync_turn user failed: %s", e)
        try:
            args = {
                "content": f"Assistant turn in session {label}: {assistant_content[:800]}",
                "entity_type": "conversation_turn",
                "entity_name": f"assistant-{label}",
            }
            if sid:
                args["session_id"] = sid
            self._client.call("smart_ingest", args)
        except Exception as e:
            logger.debug("ferrosa sync_turn assistant failed: %s", e)
```

- [ ] **Step 7: Map the session id in `on_session_end`**

Replace:

```python
    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._client:
            return
        try:
            self._client.call("run_consolidation", {})
            logger.info("ferrosa-memory: ran session-end consolidation")
        except Exception as e:
            logger.debug("ferrosa consolidation failed: %s", e)
```

with:

```python
    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._client:
            return
        try:
            sid = self._sid()
            args: Dict[str, Any] = {"session_id": sid} if sid else {}
            self._client.call("run_consolidation", args)
            logger.info("ferrosa-memory: ran session-end consolidation")
        except Exception as e:
            logger.debug("ferrosa consolidation failed: %s", e)
```

- [ ] **Step 8: Map the session id in `on_memory_write`**

Replace:

```python
        try:
            self._client.call(
                "smart_ingest",
                {
                    "content": content,
                    "entity_type": target if target in ("memory", "user") else "memory",
                    "session_id": self._session_id,
                },
            )
```

with:

```python
        try:
            args: Dict[str, Any] = {
                "content": content,
                "entity_type": target if target in ("memory", "user") else "memory",
            }
            sid = self._sid()
            if sid:
                args["session_id"] = sid
            self._client.call("smart_ingest", args)
```

- [ ] **Step 9: Compile + pre-commit**

Run: `python -m compileall -q plugin && pre-commit run --files plugin/__init__.py`
Expected: PASS (re-run if ruff-format reformats).

- [ ] **Step 10: Commit**

```bash
git add plugin/__init__.py
git commit -m "fix(plugin): map Hermes session id to ferrosa UUID across all calls

Closes #5"
```

---

## Task 3: Run the unit tests in CI

**Files:**
- Modify: `.github/workflows/ci.yml` (add a step after "Compile Python")

- [ ] **Step 1: Add the unit-test step**

Find:

```yaml
      - name: Compile Python
        run: python -m compileall -q hooks plugin

      - name: Installer dry-run (hermetic)
```

Replace with:

```yaml
      - name: Compile Python
        run: python -m compileall -q hooks plugin

      - name: Unit tests
        run: python -m unittest discover -s tests -p 'test_*.py' -v

      - name: Installer dry-run (hermetic)
```

- [ ] **Step 2: Verify locally**

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: PASS — 9 tests OK.

- [ ] **Step 3: Lint the workflow file**

Run: `pre-commit run --files .github/workflows/ci.yml`
Expected: PASS (check-yaml).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run in-repo unit tests"
```

---

## Task 4: Documentation

**Files:**
- Modify: `plugin/README.md` (env vars table + how-it-works)
- Modify: `CLAUDE.md` (plugin section / fmem mapping table)

- [ ] **Step 1: Update `plugin/README.md`**

In the environment-variable documentation, add a row/line for the namespace var (match the file's existing table/format):

```markdown
| FERROSA_MEMORY_SESSION_NS | UUIDv5 namespace for deriving ferrosa-memory session UUIDs from Hermes session ids. May be a UUID or any string. | (built-in default) |
```

And add a short note in the "how it works" prose:

```markdown
Session ids: Hermes' native session id is mapped to a deterministic UUID
(UUIDv5) before being sent to ferrosa-memory, which requires UUID `session_id`s.
The mapping is stateless, so it is stable across restarts and replicas. Recall
(`prefetch`) uses `scope="both"`, spanning the current session and tenant-global
consolidated memory.
```

- [ ] **Step 2: Update `CLAUDE.md`**

In the plugin section (near the fmem mapping table / URL-resolution notes), add:

```markdown
### Session id mapping

Hermes session ids are not UUIDs, but ferrosa-memory requires UUID `session_id`s.
`plugin/session.py` maps the native id to a deterministic UUIDv5
(`resolve_session_namespace` + `ferrosa_session_id`); valid UUIDs pass through,
empty ids are omitted (server default applies). The mapped id is used in
`prefetch` (with `scope="both"`), `sync_turn`, `on_memory_write`, and
`on_session_end`. Override the namespace with `FERROSA_MEMORY_SESSION_NS`.
Keep the mapping pure/stdlib-only so it stays unit-testable without a Hermes install.
```

- [ ] **Step 3: pre-commit (docs)**

Run: `pre-commit run --files plugin/README.md CLAUDE.md`
Expected: PASS (end-of-file-fixer/trailing-whitespace may adjust; re-run until clean).

- [ ] **Step 4: Commit**

```bash
git add plugin/README.md CLAUDE.md
git commit -m "docs: document session-id UUID mapping and scope"
```

---

## Task 5: Full local verification + open PR

**Files:** none (verification + PR)

- [ ] **Step 1: Full pre-commit + tests + compile**

```bash
pre-commit run --all-files
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q hooks plugin
```
Expected: all PASS.

- [ ] **Step 2: Installer dry-run (mirror CI's hermetic check)**

```bash
mkdir -p scripts/hooks
printf '#!/usr/bin/env python3\n' > scripts/hooks/ferrosa-memory-turn-hook.py
python3 hooks/install-agent-hooks.py \
  --harness all --dry-run --no-apply-config --skip-auth-check \
  --install-dir "${TMPDIR:-/tmp}/fmem-hooks"
rm -rf scripts/hooks
```
Expected: exits 0 (dry-run prints planned actions).

- [ ] **Step 3: Push the branch**

```bash
git push -u origin fix/session-id-uuid-mapping
```

- [ ] **Step 4: Open the PR (closes #5)**

```bash
gh pr create -R ferrosadb/ferrosa-hermes \
  --title "fix(plugin): map Hermes session id to a deterministic ferrosa UUID" \
  --body "$(cat <<'EOF'
Closes #5.

## Summary
- Add `plugin/session.py`: pure, stdlib-only UUIDv5 mapping of Hermes session ids to ferrosa-memory session UUIDs (deterministic, stateless, valid-UUID passthrough, empty→omit).
- Thread the mapped UUID through `initialize`, `prefetch` (with `scope="both"`), `sync_turn`, `on_memory_write`, and `on_session_end`.
- Add in-repo `unittest` suite + a CI step.
- Docs: README + CLAUDE.md.

## Why
ferrosa-memory requires UUID `session_id`s; the plugin was sending the raw Hermes id, which the server rejected and replaced with the default session — collapsing all sessions into one. `prefetch` also sent no session id, so reads/writes diverge once writes are session-scoped. This fixes both while preserving cross-session recall via `scope="both"`.

## Test plan
- [ ] `python -m unittest discover -s tests -p 'test_*.py' -v` passes
- [ ] `pre-commit run --all-files` passes
- [ ] Against a live ferrosa-memory: the `substituted configured default for caller-provided session_id` warning no longer appears for Hermes traffic
- [ ] Distinct Hermes sessions produce distinct ferrosa-memory sessions
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- Mapping (UUIDv5, passthrough, empty→None) → Task 1.
- Namespace env override → Task 1 (`resolve_session_namespace`) + tests.
- Wiring of all five call sites + `scope="both"` → Task 2.
- In-repo stdlib unittest + CI step → Task 1 + Task 3.
- Docs → Task 4.
- Rollout (PR closing #5) → Task 5. (Infra image refresh is post-merge, out of this repo's scope — noted in the spec.)

**Placeholder scan:** none — all steps contain concrete code/commands.

**Type/name consistency:** `DEFAULT_SESSION_NS`, `resolve_session_namespace`, `ferrosa_session_id`, `_sid`, `_session_ns`, `_ferrosa_session_id` used consistently across Tasks 1–4. `args: Dict[str, Any]` matches the existing `Dict`/`Any` imports already present in `plugin/__init__.py`.

**Note:** The namespace constant `ea88216a-73a3-447a-85e5-6176640ac4ac` is identical in the spec, `plugin/session.py`, and must never change after merge.
