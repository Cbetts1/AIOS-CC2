#!/usr/bin/env bash
# AI-OS CC2 — Unix/Mac/Termux launcher
# Usage: bash start.sh [terminal|web|none] [port]
#
# Port resolution order (highest to lowest priority):
#   1. Second argument to this script:  bash start.sh web 8080
#   2. AIOS_PORT environment variable:  export AIOS_PORT=8080
#   3. Built-in default:                1313

UI="${1:-terminal}"

# Honour AIOS_PORT env var; fall back to 1313 if not set
PORT="${2:-${AIOS_PORT:-1313}}"
# Export so the Python process inherits it
export AIOS_PORT="$PORT"

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
