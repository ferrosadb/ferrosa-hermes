"""Ferrosa Memory — MemoryProvider plugin backed by the ferrosa-memory MCP server.

Connects to ferrosa-memory via its HTTP JSON-RPC endpoint.  No client SDK needed;
talks raw JSON-RPC over urllib.

Config (env var takes precedence over saved config):
  FERROSA_MEMORY_URL   — full MCP endpoint, e.g.
                         http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp
  FERROSA_MEMORY_TENANT_ID — optional tenant override (default: read from server)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from agent.memory_provider import MemoryProvider
from agent.skill_providers import SkillMetadata, SkillPayload

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple JSON-RPC MCP client (raw HTTP, no SDK)
# ---------------------------------------------------------------------------

class _McpClient:
    def __init__(self, url: str):
        self.url, self._headers = self._prepare_url_and_headers(url)
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE

    @staticmethod
    def _prepare_url_and_headers(url: str) -> tuple[str, Dict[str, str]]:
        """Strip URL userinfo into an Authorization header.

        urllib does not consistently turn http://user:pass@host URLs into Basic
        auth headers. Keeping the sanitized URL separately also prevents
        accidental credential logging.
        """
        parts = urllib.parse.urlsplit(url)
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if parts.username is None:
            return url, headers
        username = urllib.parse.unquote(parts.username)
        password = urllib.parse.unquote(parts.password or "")
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        sanitized = urllib.parse.urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
        return sanitized, headers

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return the parsed result."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(4):
            req = urllib.request.Request(
                self.url,
                data=data,
                headers=self._headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30, context=self._ctx) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    if "error" in body:
                        raise RuntimeError(body["error"])
                    result = body.get("result", {})
                    # MCP text content
                    if "content" in result:
                        for item in result["content"]:
                            if item.get("type") == "text":
                                try:
                                    return json.loads(item["text"])
                                except json.JSONDecodeError:
                                    return item["text"]
                    return result
            except Exception as exc:
                last_error = exc
                code = getattr(exc, "code", None)
                if code != 429 or attempt == 3:
                    break
                time.sleep(1.5 * (attempt + 1))
        if last_error:
            raise last_error
        return {}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_saved_config(hermes_home: str) -> Dict[str, Any]:
    cfg_path = Path(hermes_home) / "plugins" / "ferrosa" / "config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text())
        except Exception:
            pass
    return {}


def _save_config(values: Dict[str, Any], hermes_home: str) -> None:
    cfg_dir = Path(hermes_home) / "plugins" / "ferrosa"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.json"
    try:
        cfg_path.write_text(json.dumps(values, indent=2))
    except Exception as e:
        logger.debug("Failed to write ferrosa config: %s", e)


def _resolve_url(saved: Dict[str, Any]) -> Optional[str]:
    # 1. env var
    url = os.environ.get("FERROSA_MEMORY_URL", "").strip()
    if url:
        return url
    # 2. saved config
    url = (saved.get("url") or "").strip()
    if url:
        return url
    # 3. fallback
    return "http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp"


def _csv_env(name: str, default: Iterable[str]) -> List[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return [str(item).strip() for item in default if str(item).strip()]
    return [item.strip() for item in raw.split(",") if item.strip()]


_DEFAULT_SKILL_LIST_CONTEXTS = [
    "skill",
    "blueprint project architecture plan",
    "task-level software development testing security audit",
    "tech language cloud database infrastructure",
    "management product marketing",
]


def _format_skill_payload_content(data: Dict[str, Any]) -> str:
    name = str(data.get("skill_name") or data.get("name") or "").strip()
    description = str(data.get("description") or "").strip()
    category = str(data.get("category") or "fmem").strip()
    version = str(data.get("version") or "").strip()
    steps = data.get("steps") if isinstance(data.get("steps"), list) else []
    output_artifacts = data.get("output_artifacts") if isinstance(data.get("output_artifacts"), list) else []
    completion = str(data.get("completion_criteria") or "").strip()
    first_step = str(data.get("first_step_prompt") or "").strip()

    frontmatter = ["---", f"name: {json.dumps(name)}"]
    if description:
        frontmatter.append(f"description: {json.dumps(description)}")
    if category:
        frontmatter.append(f"category: {json.dumps(category)}")
    if version:
        frontmatter.append(f"version: {json.dumps(version)}")
    frontmatter.append("---")

    body = ["", f"# {name}", ""]
    if description:
        body.extend([description, ""])
    if first_step:
        body.extend(["## First step", "", first_step, ""])
    if steps:
        body.extend(["## Steps", ""])
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                continue
            phase = str(step.get("phase") or f"Step {index}").strip()
            instruction = str(step.get("instruction") or "").strip()
            body.extend([f"### {phase}", "", instruction, ""])
    if output_artifacts:
        body.extend(["## Output artifacts", ""])
        for artifact in output_artifacts:
            body.append(f"- {artifact}")
        body.append("")
    if completion:
        body.extend(["## Completion criteria", "", completion, ""])
    return "\n".join(frontmatter + body).rstrip() + "\n"


class FerrosaSkillProvider:
    """Virtual Hermes skills backed by fmem's global skill catalog."""

    namespace = "fmem"

    def __init__(self, client: Optional[_McpClient] = None, url: Optional[str] = None):
        self._client = client
        self._url = url
        self._metadata_cache: Optional[List[SkillMetadata]] = None

    @property
    def client(self) -> _McpClient:
        if self._client is None:
            url = self._url or _resolve_url({})
            if not url:
                raise RuntimeError("ferrosa-memory URL is not configured")
            self._client = _McpClient(url)
        return self._client

    def list_skills(self) -> List[SkillMetadata]:
        if self._metadata_cache is not None:
            return list(self._metadata_cache)
        by_name: Dict[str, SkillMetadata] = {}
        contexts = _csv_env("FERROSA_MEMORY_SKILL_LIST_CONTEXTS", _DEFAULT_SKILL_LIST_CONTEXTS)
        limit = int(os.environ.get("FERROSA_MEMORY_SKILL_LIST_LIMIT", "200") or "200")
        for context in contexts:
            try:
                result = self.client.call(
                    "retrieve_skills_for_context",
                    {"context": context, "limit": limit, "min_score": 0},
                )
            except Exception as exc:
                logger.debug("ferrosa skill list query failed for %r: %s", context, exc)
                continue
            for hit in result.get("results", []) if isinstance(result, dict) else []:
                name = str(hit.get("skill_name") or hit.get("name") or "").strip()
                if not name or name in by_name:
                    continue
                by_name[name] = SkillMetadata(
                    name=name,
                    description=str(hit.get("description") or ""),
                    category=str(hit.get("category") or "fmem"),
                    tags=[str(hit.get("category") or "fmem")],
                )
        self._metadata_cache = sorted(by_name.values(), key=lambda item: item.name)
        return list(self._metadata_cache)

    def resolve_skill(self, name: str) -> Optional[SkillPayload]:
        name = str(name or "").strip()
        if not name:
            return None
        result = self.client.call("invoke_skill", {"skill_name": name})
        if not isinstance(result, dict) or result.get("error"):
            return None
        skill_name = str(result.get("skill_name") or name)
        description = str(result.get("description") or "")
        category = str(result.get("category") or "fmem")
        return SkillPayload(
            name=skill_name,
            description=description,
            content=_format_skill_payload_content(result),
            linked_files=None,
            tags=[category] if category else [],
            metadata={"fmem": {"entity_id": result.get("entity_id"), "version": result.get("version")}},
        )

    def read_supporting_file(self, name: str, file_path: str) -> None:
        return None


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class FerrosaMemoryProvider(MemoryProvider):
    def __init__(self):
        self._url: Optional[str] = None
        self._client: Optional[_McpClient] = None
        self._session_id: str = ""
        self._tenant_id: str = ""
        self._hermes_home: str = ""
        self._saved_config: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "ferrosa"

    def is_available(self) -> bool:
        """Return True if we can reach the ferrosa-memory MCP endpoint."""
        url = _resolve_url(self._saved_config)
        if not url:
            return False
        try:
            _McpClient(url).call("get_stats", {})
            return True
        except Exception:
            return False

    def get_config_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": "url",
                "description": "Ferrosa Memory MCP HTTP endpoint (include credentials if auth required). Example: http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp",
                "default": "http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp",
                "required": True,
            },
            {
                "key": "tenant_id",
                "description": "Tenant ID for multi-tenant deployments (optional)",
                "required": False,
            },
        ]

    def save_config(self, values: Dict[str, Any], hermes_home: str) -> None:
        _save_config(values, hermes_home)

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._hermes_home = str(kwargs.get("hermes_home", "~/.hermes"))
        self._saved_config = _load_saved_config(self._hermes_home)
        self._url = _resolve_url(self._saved_config)
        if not self._url:
            logger.warning("ferrosa-memory: no URL configured; skipping activation")
            return
        self._client = _McpClient(self._url)
        tenant = os.environ.get("FERROSA_MEMORY_TENANT_ID", "")
        if tenant:
            self._tenant_id = tenant
        else:
            self._tenant_id = self._saved_config.get("tenant_id", "")
        logger.info("ferrosa-memory: connected to %s", self._url.rsplit("@", 1)[-1] if "@" in self._url else self._url)

    def system_prompt_block(self) -> str:
        if not self._client:
            return ""
        try:
            stats = self._client.call("get_stats", {})
            e = stats.get("entity_count", 0)
            f = stats.get("fold_count", 0)
            if e == 0 and f == 0:
                return "# Ferrosa Memory\nActive. No memories yet — use `smart_ingest` via the MCP tools to save persistent knowledge.\n"
            return f"# Ferrosa Memory\nActive. {e} entities, {f} folds indexed across sessions.\n"
        except Exception:
            return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._client or not query:
            return ""
        try:
            # Use hybrid_search for broad recall
            result = self._client.call("hybrid_search", {
                "query": query,
                "limit": 5,
            })
            results = result.get("results", []) if isinstance(result, dict) else []
            if not results:
                return ""
            lines = ["## Ferrosa Memory"]
            for r in results:
                name = r.get("entity_name", "?")
                etype = r.get("entity_type", "?")
                content = r.get("content", "")[:250]
                lines.append(f"- [{etype}] {name}: {content}")
            return "\n".join(lines)
        except Exception as e:
            logger.debug("ferrosa prefetch failed: %s", e)
            return ""

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if not self._client:
            return
        try:
            self._client.call("smart_ingest", {
                "content": f"User turn in session {session_id or self._session_id}: {user_content[:800]}",
                "entity_type": "conversation_turn",
                "entity_name": f"user-{session_id or self._session_id}",
                "session_id": session_id or self._session_id,
            })
        except Exception as e:
            logger.debug("ferrosa sync_turn user failed: %s", e)
        try:
            self._client.call("smart_ingest", {
                "content": f"Assistant turn in session {session_id or self._session_id}: {assistant_content[:800]}",
                "entity_type": "conversation_turn",
                "entity_name": f"assistant-{session_id or self._session_id}",
                "session_id": session_id or self._session_id,
            })
        except Exception as e:
            logger.debug("ferrosa sync_turn assistant failed: %s", e)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        # We do NOT replicate fmem tools here — they are already exposed
        # as MCP tools via the ferrosa-memory MCP server. This provider is
        # context-only: prefetch + sync_turn.
        return []

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        return json.dumps({"error": "ferrosa memory provider has no provider-local tools; use the fmem MCP tools directly."})

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._client:
            return
        try:
            self._client.call("run_consolidation", {})
            logger.info("ferrosa-memory: ran session-end consolidation")
        except Exception as e:
            logger.debug("ferrosa consolidation failed: %s", e)

    def on_memory_write(self, action: str, target: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self._client or action != "add" or not content:
            return
        try:
            self._client.call("smart_ingest", {
                "content": content,
                "entity_type": target if target in ("memory", "user") else "memory",
                "session_id": self._session_id,
            })
        except Exception as e:
            logger.debug("ferrosa on_memory_write mirror failed: %s", e)

    def shutdown(self) -> None:
        self._client = None


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register ferrosa memory and virtual fmem skill providers."""
    ctx.register_memory_provider(FerrosaMemoryProvider())
    if hasattr(ctx, "register_skill_provider"):
        ctx.register_skill_provider(FerrosaSkillProvider(), namespace="fmem")
