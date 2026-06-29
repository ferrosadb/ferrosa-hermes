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
