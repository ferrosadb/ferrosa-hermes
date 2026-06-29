# Design: Map Hermes session id to a deterministic UUID (fixes #5)

> Status: Approved design (pre-implementation)
> Date: 2026-06-29
> Repo: ferrosadb/ferrosa-hermes
> Issue: https://github.com/ferrosadb/ferrosa-hermes/issues/5

## Problem

`FerrosaMemoryProvider` passes Hermes' native session identifier (e.g.
`20260628_134834_d90c1c66`) straight through to ferrosa-memory as `session_id`.
ferrosa-memory requires `session_id` to be a **UUID**; a non-UUID value is
rejected and substituted with the server's configured default session (with a
`WARN ... substituted configured default for caller-provided session_id`). Net
effects:

1. **No session isolation** — every Hermes session collapses into the one
   server default session, so per-session structure (consolidation scenes,
   workspace profiles) cannot distinguish sessions.
2. **Read/write inconsistency risk** — `prefetch` sends *no* `session_id` at all
   (it relies on the server default), while writes send the raw Hermes id. Today
   both happen to land in the same default bucket; any fix that gives writes a
   real session id must also fix `prefetch`, or reads and writes diverge.

ferrosa-memory is intentionally generic (multi-agent); its UUID `session_id`
contract reaches down to CQL partition keys. The harness-specific id→UUID
mapping therefore belongs in this adapter, not in ferrosa-memory.

## Goals

- Give each Hermes session a stable, distinct ferrosa-memory session UUID.
- Preserve **cross-session recall** (the core value of ferrosa-memory).
- Be **stateless and deterministic** — no mapping table, no lookup — so it is
  correct under horizontally-scaled Hermes instances and ferrosa-memory replicas.
- Stay within repo conventions: **stdlib only**, fail-open at runtime, graceful
  degradation preserved.

## Non-goals

- The `hooks/` installer path (this deployment uses the plugin only, installed
  via `setup.sh --no-hooks`).
- Engine-side issues already tracked separately (ferrosa-memory #129 derived
  cache, #130 cross-replica consolidation).
- Any change to ferrosa-memory's `session_id` contract.

## Key facts that shape the design

- ferrosa-memory's MCP `hybrid_search` tool **defaults `scope` to `both`**
  (current session + tenant-global). Cross-session memory works by: per-session
  writes → background consolidation promotes/folds to the tenant-**global**
  partition → recall with `scope=both` surfaces current-session **and** global.
  So per-session write attribution and cross-session recall are compatible.
- ferrosa-memory's `resolve_session_id` passes a valid UUID through unchanged and
  only substitutes the default for non-UUID / empty values.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Recall scope | Cross-session: `prefetch` passes `scope="both"` + mapped `session_id` |
| Mapping | UUIDv5 (deterministic, stateless); valid-UUID input passes through; empty → omit |
| Namespace | Env-overridable `FERROSA_MEMORY_SESSION_NS`, hardcoded default constant |
| Testing | In-repo stdlib `unittest` over a pure mapping module + a CI step |

## Design

### 1. New module `plugin/session.py` (pure, stdlib only, no `agent.*` import)

```python
import os
import uuid

# Stable default namespace for deriving ferrosa-memory session UUIDs from
# harness-native session ids. Minted once; do not change (would re-key every
# existing Hermes->ferrosa session mapping).
DEFAULT_SESSION_NS = uuid.UUID("ea88216a-73a3-447a-85e5-6176640ac4ac")


def resolve_session_namespace(env=None) -> uuid.UUID:
    """Resolve the UUIDv5 namespace. FERROSA_MEMORY_SESSION_NS may be a UUID
    (used directly) or any string (a stable namespace is derived from it).
    Falls back to DEFAULT_SESSION_NS when unset/blank."""
    env = os.environ if env is None else env
    raw = (env.get("FERROSA_MEMORY_SESSION_NS") or "").strip()
    if not raw:
        return DEFAULT_SESSION_NS
    try:
        return uuid.UUID(raw)
    except ValueError:
        return uuid.uuid5(DEFAULT_SESSION_NS, raw)


def ferrosa_session_id(raw, namespace):
    """Map a harness-native session id to a ferrosa-memory session UUID string.

    - empty / None        -> None  (caller omits session_id; server default applies)
    - already a UUID       -> returned unchanged (matches fmem contract)
    - any other string     -> deterministic uuid5(namespace, raw)
    """
    s = ("" if raw is None else str(raw)).strip()
    if not s:
        return None
    try:
        return str(uuid.UUID(s))
    except ValueError:
        return str(uuid.uuid5(namespace, s))
```

Why UUIDv5: deterministic (same input → same output), stateless (no shared
mapping store), collision-resistant (namespaced SHA-1). This is what makes the
mapping safe under horizontal scaling.

### 2. `plugin/__init__.py` wiring

- `__init__`: add `self._ferrosa_session_id: str = ""` and
  `self._session_ns: uuid.UUID = DEFAULT_SESSION_NS`.
- `initialize(session_id, ...)`: keep `self._session_id = session_id` (raw, for
  human-readable labels); set `self._session_ns = resolve_session_namespace()`
  and `self._ferrosa_session_id = ferrosa_session_id(session_id, self._session_ns) or ""`.
- Add a small helper:

  ```python
  def _sid(self, per_call: str = "") -> Optional[str]:
      return ferrosa_session_id(per_call or self._session_id, self._session_ns)
  ```

- `prefetch`: send `scope="both"` and, when `_sid()` is not `None`, `session_id`:

  ```python
  args = {"query": query, "limit": 5, "scope": "both"}
  sid = self._sid(session_id)
  if sid:
      args["session_id"] = sid
  result = self._client.call("hybrid_search", args)
  ```

- `sync_turn`: `session_id` argument = `self._sid(session_id)` (omit if `None`).
  `entity_name` / `content` keep the raw human id (`session_id or self._session_id`)
  for readability — only the `session_id` field must be the UUID.
- `on_memory_write`: `session_id` = `self._sid()` (omit if `None`).
- `on_session_end`: call `run_consolidation` with `{"session_id": sid}` when
  `self._sid()` is not `None`, else `{}` — so consolidation targets the real
  session and promotes to global.

### 3. Error handling

Unchanged fail-open posture. `ferrosa_session_id` does not raise on normal
input. Call sites keep their existing `except Exception: logger.debug(...)`
swallows; if mapping ever yields `None`, the `session_id` field is omitted and
the server default applies rather than breaking the turn.

### 4. Testing — `tests/test_session.py` (stdlib `unittest`)

Pure-function tests, no Hermes import required:

- determinism: `ferrosa_session_id("abc", ns) == ferrosa_session_id("abc", ns)`
- distinctness: different raw ids → different UUIDs
- UUID passthrough: a valid UUID string returns itself unchanged
- empty/None → `None`
- output is a parseable UUID string
- `resolve_session_namespace`: blank → default; valid-UUID env → that UUID;
  arbitrary-string env → stable derived namespace (and changes the mapping output
  vs default)

CI (`.github/workflows/ci.yml`) gains one step after `Compile Python`:

```yaml
- name: Unit tests
  run: python -m unittest discover -s tests -p 'test_*.py'
```

### 5. Docs

Update `plugin/README.md` and `CLAUDE.md` (the fmem mapping table / plugin
section) to document: session-id → UUIDv5 mapping, the
`FERROSA_MEMORY_SESSION_NS` env var, and `scope=both` recall.

### 6. Rollout (post-merge, tracked, not in this change)

1. Branch `fix/session-id-uuid-mapping`; PR to `ferrosadb/ferrosa-hermes`
   closing #5.
2. After merge, refresh the infra `hermes-ferrosa` seed/image so the running
   agent picks up the new plugin (the image clones ferrosa-hermes).
3. Verify the `substituted configured default for caller-provided session_id`
   warning is gone and distinct sessions produce distinct ferrosa sessions.

## Acceptance criteria

- Distinct Hermes sessions map to distinct, stable ferrosa-memory session UUIDs;
  an already-UUID session id passes through unchanged.
- `prefetch`, `sync_turn`, `on_memory_write`, and `on_session_end` all use the
  same mapped UUID; `prefetch` requests `scope="both"`.
- ferrosa-memory no longer logs `substituted configured default for
  caller-provided session_id` for Hermes traffic.
- In-repo `unittest` passes locally and in CI; pre-commit (ruff/bandit/etc.)
  passes; no third-party dependencies added.
- Runtime memory operations remain fail-open.

## Files touched

- `plugin/session.py` (new)
- `plugin/__init__.py` (wiring)
- `tests/test_session.py` (new)
- `.github/workflows/ci.yml` (add unit-test step)
- `plugin/README.md`, `CLAUDE.md` (docs)
