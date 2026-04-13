#!/usr/bin/env bash
# AI-OS CC2 — Unix/Mac launcher
# Usage: bash start.sh [terminal|web|none] [port]
set -e

UI="${1:-terminal}"
PORT="${2:-1313}"

echo "======================================================"
echo "  AI-OS CC2 — Starting in $UI mode on port $PORT"
echo "======================================================"

# Make sure we're in the repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python version
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Please install Python 3.8 or newer."
    exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
if [ "$PYVER" -lt 38 ]; then
    echo "ERROR: Python 3.8+ required. Found: $($PYTHON --version)"
    exit 1
fi

echo "  Python: $($PYTHON --version)"
echo "  UI mode: $UI"

if [ "$UI" = "web" ]; then
    echo "  Web UI will be at: http://localhost:$PORT"
fi

echo ""
"$PYTHON" aios/main.py --ui "$UI" --port "$PORT"
