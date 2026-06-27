#!/usr/bin/env bash
# ferrosa-hermes setup — installs the memory provider plugin, session hooks,
# and configures Hermes to use ferrosa-memory as its memory backend.
#
# Prerequisites:
#   - Hermes Agent installed (https://hermes-agent.nousresearch.com/docs)
#   - ferrosa-memory MCP server running (https://github.com/ferrosadb/ferrosa-memory)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ferrosadb/ferrosa-hermes/main/setup.sh | bash
#   ./setup.sh --mcp-url http://user:pass@127.0.0.1:18765/mcp --harness auto
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
MCP_URL="${FERROSA_MEMORY_URL:-http://ferrosa_user:ferrosa_user@127.0.0.1:18765/mcp}"
HARNESS="auto"
SKIP_HOOKS=false
SKIP_PLUGIN=false
DRY_RUN=false

while [ $# -gt 0 ]; do
  case "$1" in
    --mcp-url)   MCP_URL="$2"; shift 2 ;;
    --harness)   HARNESS="$2"; shift 2 ;;
    --no-hooks)  SKIP_HOOKS=true; shift ;;
    --no-plugin) SKIP_PLUGIN=true; shift ;;
    --dry-run)   DRY_RUN=true; shift ;;
    -h|--help)
      cat <<EOF
ferrosa-hermes setup
  --mcp-url <url>     ferrosa-memory MCP endpoint (default $MCP_URL)
  --harness <name>    which harness hooks: auto|all|codex|claude|hermes|pi|generic
  --no-hooks          skip hook installation
  --no-plugin         skip plugin installation
  --dry-run           print actions without executing
EOF
      exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

run() {
  if $DRY_RUN; then echo "[DRY-RUN] $*"; else echo "[RUN] $*"; "$@"; fi
}

# ------------------------------------------------------------------
# 1. Verify Hermes is installed and detect its layout
# ------------------------------------------------------------------
# Two supported layouts:
#   host      — installer-style tree at $HERMES_HOME/hermes-agent (plugins live
#               under .../plugins/memory/<name>).
#   container — official hermes-agent image: read-only agent at /opt/hermes with
#               the `hermes` CLI on PATH and writable plugins at $HERMES_HOME/plugins/<name>.
if [ -d "$HERMES_HOME/hermes-agent" ]; then
  HERMES_LAYOUT="host"
  PLUGIN_DIR="$HERMES_HOME/hermes-agent/plugins/memory/ferrosa"
elif command -v hermes >/dev/null 2>&1; then
  HERMES_LAYOUT="container"
  PLUGIN_DIR="$HERMES_HOME/plugins/ferrosa"
else
  echo "ERROR: Hermes Agent not found."
  echo "  - host install expected at: $HERMES_HOME/hermes-agent"
  echo "  - or the 'hermes' CLI on PATH (container/image install)"
  echo "Install Hermes first: https://hermes-agent.nousresearch.com/docs"
  exit 1
fi
echo "Detected Hermes layout: $HERMES_LAYOUT (plugin dir: $PLUGIN_DIR)"

# ------------------------------------------------------------------
# 2. Install memory provider plugin
# ------------------------------------------------------------------
if ! $SKIP_PLUGIN; then
  echo "=== Installing ferrosa memory provider plugin ==="
  run mkdir -p "$PLUGIN_DIR"
  run cp "$SCRIPT_DIR/plugin/__init__.py" "$PLUGIN_DIR/__init__.py"
  run cp "$SCRIPT_DIR/plugin/plugin.yaml" "$PLUGIN_DIR/plugin.yaml"
  run cp "$SCRIPT_DIR/plugin/README.md" "$PLUGIN_DIR/README.md"

  # Activate the provider. Non-fatal: on some installs `hermes config set` may
  # fail (e.g. the home dir is provisioned by a separate boot step) — the plugin
  # is still usable when the provider is selected via config.yaml or env, so we
  # warn rather than abort the whole install.
  echo ""
  echo "=== Activating ferrosa as memory provider ==="
  if ! run hermes config set memory.provider ferrosa; then
    echo "[WARN] 'hermes config set memory.provider ferrosa' failed."
    echo "       Ensure memory.provider: ferrosa is set in your Hermes config.yaml."
  fi

  # Save MCP URL to plugin config
  run mkdir -p "$HERMES_HOME/plugins/ferrosa"
  echo "{\"url\": \"$MCP_URL\"}" > "$HERMES_HOME/plugins/ferrosa/config.json"
  echo "[OK] Plugin installed (provider: ferrosa)"
fi

# ------------------------------------------------------------------
# 3. Install session hooks
# ------------------------------------------------------------------
if ! $SKIP_HOOKS; then
  echo ""
  echo "=== Installing session hooks (harness: $HARNESS) ==="
  run python3 "$SCRIPT_DIR/hooks/install-agent-hooks.py" \
    --harness "$HARNESS" \
    --mcp-url "$MCP_URL" \
    --verify
  echo "[OK] Hooks installed"
fi

# ------------------------------------------------------------------
# 4. Verify MCP connectivity
# ------------------------------------------------------------------
echo ""
echo "=== Verifying ferrosa-memory MCP connectivity ==="
if curl -sf -o /dev/null "$(echo "$MCP_URL" | sed 's|/mcp$|/health|')" 2>/dev/null; then
  echo "[OK] ferrosa-memory is reachable"
else
  echo "[WARN] ferrosa-memory health check failed at $MCP_URL"
  echo "       Make sure the MCP server is running."
  echo "       Start it with: ferrosa-memory --http-port 18765"
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Start a new Hermes session (/reset or restart hermes)"
echo "  2. Verify: hermes memory status"
echo "     Expected: Provider: ferrosa, Plugin: installed ✓, Status: available ✓"
echo "  3. Test recall: ask Hermes to search its memory"
