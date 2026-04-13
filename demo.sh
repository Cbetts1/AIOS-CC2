#!/usr/bin/env bash
# AI-OS CC2 — Canned Live Demo Runner
#
# Usage: bash demo.sh [port]
#
# This script:
#   1. Starts AI-OS in background mode (--ui none)
#   2. Waits until the web server is ready (/api/health)
#   3. Runs a sequence of curl commands hitting every major menu section
#   4. Prints the results in a readable format
#   5. Stops AI-OS when done (Ctrl+C exits cleanly too)
#
# Admin password for /api/command is 7212.
# All output is also saved to logs/demo.log

set -e

PORT="${1:-1313}"
BASE="http://localhost:$PORT"
PW="7212"
LOG="logs/demo.log"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p logs

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found."
    exit 1
fi

# ── Helper functions ─────────────────────────────────────────────────────────

section() {
    echo ""
    echo "══════════════════════════════════════════════════════"
    echo "  $1"
    echo "══════════════════════════════════════════════════════"
}

run_cmd() {
    local label="$1"
    local cmd_val="$2"
    echo ""
    echo "  ── CMD: $cmd_val  ($label) ──"
    local result
    result=$(curl -s -X POST "$BASE/api/command" \
        -H "Content-Type: application/json" \
        -d "{\"cmd\":\"$cmd_val\",\"password\":\"$PW\"}" | \
        "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('result','(no result)'))" 2>/dev/null || echo "  (curl failed)")
    echo "$result"
    echo "$result" >> "$LOG"
}

# ── Start AI-OS in background ────────────────────────────────────────────────

section "Starting AI-OS (background mode, port $PORT)"
"$PYTHON" aios/main.py --ui none --port "$PORT" &
AIOS_PID=$!
echo "  PID: $AIOS_PID"

trap 'echo ""; echo "  Stopping AI-OS (PID $AIOS_PID)..."; kill $AIOS_PID 2>/dev/null; echo "  Demo complete. Log: $LOG"; exit 0' INT TERM EXIT

# ── Wait for readiness ───────────────────────────────────────────────────────

section "Waiting for /api/health..."
ATTEMPTS=0
until curl -sf "$BASE/api/health" > /dev/null 2>&1; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -gt 30 ]; then
        echo "  ERROR: AI-OS did not start within 30 seconds."
        kill "$AIOS_PID" 2>/dev/null
        exit 1
    fi
    printf "  ."
    sleep 1
done
echo ""
echo "  AI-OS is ONLINE."

# ── Log header ───────────────────────────────────────────────────────────────
{
    echo "AI-OS CC2 Demo Log"
    echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "Port: $PORT"
    echo "======================================================"
} > "$LOG"

# ── Open endpoints ───────────────────────────────────────────────────────────

section "1. Health Check (GET /api/health)"
curl -s "$BASE/api/health" | "$PYTHON" -m json.tool
echo ""

section "2. System Status (GET /api/status)"
curl -s "$BASE/api/status" | "$PYTHON" -m json.tool | head -40
echo ""

section "3. Heartbeat (GET /api/heartbeat)"
curl -s "$BASE/api/heartbeat" | "$PYTHON" -m json.tool
echo ""

section "4. Virtual /proc files (GET /api/proc)"
curl -s "$BASE/api/proc" | "$PYTHON" -m json.tool
echo ""

# ── Command menu walkthrough ─────────────────────────────────────────────────

section "5. Menu walkthrough (POST /api/command, password=7212)"

run_cmd "System Status — Full Report"     "1.1"
run_cmd "System Status — Layer Health"    "1.2"
run_cmd "System Status — Subsystem List"  "1.3"
run_cmd "System Status — Resource Usage"  "1.4"
run_cmd "Layer Control — Layer 5"         "2.5"
run_cmd "Engine — Start All Engines"      "3.1"
run_cmd "Engine — AuraEngine Tick"        "3.2"
run_cmd "Virtual HW — CPU Status"         "4.1"
run_cmd "Virtual HW — Memory Status"      "4.2"
run_cmd "Virtual HW — Execute Instruction" "4.5"
run_cmd "Network — List Interfaces"       "5.1"
run_cmd "Network — Node Mesh Status"      "5.2"
run_cmd "Network — Heartbeat"             "5.3"
run_cmd "Security — Identity Status"      "6.1"
run_cmd "Cloud — Status"                  "7.1"
run_cmd "Cloud — Start"                   "7.3"
run_cmd "Cloud — Spawn Node"              "7.5"
run_cmd "Cloud — Execute Task"            "7.6"
run_cmd "Cloud — Heartbeat"               "7.7"
run_cmd "Cellular — Signal Simulation"    "8.2"
run_cmd "Computer — Process Supervisor"   "9.1"
run_cmd "Computer — Memory Map"           "9.2"
run_cmd "AI Systems — AuraEngine Status"  "10.1"
run_cmd "AI Systems — Builder Queue"      "10.3"
run_cmd "Diagnostics — Full Report"       "11.1"
run_cmd "Diagnostics — Health Check All"  "11.2"
run_cmd "Diagnostics — Performance"       "11.4"
run_cmd "Legal — Compliance Status"       "13.1"
run_cmd "Legal — Audit Log"               "13.2"
run_cmd "Documentation — System Overview" "14.1"
run_cmd "Logs — Full Audit Dump"          "15.5"

# ── Debug dump (admin only) ──────────────────────────────────────────────────

section "6. Debug state dump (GET /api/debug?password=$PW)"
curl -s "$BASE/api/debug?password=$PW" | "$PYTHON" -m json.tool | head -60
echo ""

section "Demo complete!"
echo "  Full output saved to: $LOG"
echo "  Press Ctrl+C or wait for cleanup."
sleep 2
