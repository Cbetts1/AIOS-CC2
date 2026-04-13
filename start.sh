#!/usr/bin/env bash
# AI-OS CC2 — Unix/Mac launcher
# Usage:
#   bash start.sh [terminal|web|none] [port] [operator-token]
#   bash start.sh check                         # preflight validation only
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Locate Python ────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Please install Python 3.8 or newer."
    exit 1
fi

# ── Check mode (preflight validation) ───────────────────────────────────────
if [ "${1:-}" = "check" ]; then
    echo "======================================================"
    echo "  AI-OS CC2 — Preflight Check"
    echo "======================================================"
    echo "  Python : $($PYTHON --version)"

    # Verify 3.8+
    OK=$("$PYTHON" -c "
import sys
v = sys.version_info
ok = (v.major, v.minor) >= (3, 8)
print('OK' if ok else 'FAIL')
")
    if [ "$OK" != "OK" ]; then
        echo "  ERROR: Python 3.8+ required."
        exit 1
    fi
    echo "  Version: OK (3.8+)"

    # Verify identity.lock
    LOCK="aios/identity/identity.lock"
    if [ ! -f "$LOCK" ]; then
        echo "  ERROR: $LOCK not found."
        exit 1
    fi
    echo "  identity.lock: found"

    # Print the operator token
    TOKEN=$("$PYTHON" -c "
import json, hashlib
with open('aios/identity/identity.lock') as f:
    d = json.load(f)
raw = (d['operator'] + '-' + d['created']).encode()
print(hashlib.sha256(raw).hexdigest())
" 2>/dev/null || echo "ERROR")
    if [ "$TOKEN" = "ERROR" ]; then
        echo "  WARNING: Could not compute operator token (identity.lock malformed?)."
    else
        echo "  Operator token: $TOKEN"
    fi

    # Check port 1313 availability (best-effort)
    PORT_CHECK="${2:-1313}"
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$PORT_CHECK" 2>/dev/null; then
            echo "  WARNING: Port $PORT_CHECK is already in use."
        else
            echo "  Port $PORT_CHECK: available"
        fi
    fi

    echo ""
    echo "  Preflight complete. Run: bash start.sh [terminal|web|none] [port]"
    exit 0
fi

# ── Normal launch ────────────────────────────────────────────────────────────
UI="${1:-terminal}"
PORT="${2:-1313}"
TOKEN="${3:-}"

echo "======================================================"
echo "  AI-OS CC2 — Starting in $UI mode on port $PORT"
echo "======================================================"

# Verify Python version (major, minor separately to avoid 3.10 = "40" ambiguity)
OK=$("$PYTHON" -c "
import sys
v = sys.version_info
ok = (v.major, v.minor) >= (3, 8)
print('OK' if ok else 'FAIL')
")
if [ "$OK" != "OK" ]; then
    echo "ERROR: Python 3.8+ required. Found: $($PYTHON --version)"
    exit 1
fi

echo "  Python: $($PYTHON --version)"
echo "  UI mode: $UI"

# Check port availability
if command -v nc >/dev/null 2>&1; then
    if nc -z localhost "$PORT" 2>/dev/null; then
        echo "  WARNING: Port $PORT may already be in use. Use a different port with:"
        echo "           bash start.sh $UI <port>"
    fi
fi

if [ "$UI" = "web" ]; then
    echo "  Web UI will be at: http://localhost:$PORT"
fi

echo ""
if [ -n "$TOKEN" ]; then
    "$PYTHON" aios/main.py --ui "$UI" --port "$PORT" --operator-token "$TOKEN"
else
    "$PYTHON" aios/main.py --ui "$UI" --port "$PORT"
fi
