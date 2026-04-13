# AIOS-CC2 — Live Demo & Go/No-Go Guide

> Use this file before every external demo or real-world test run.
> Go through the checklist top-to-bottom. Do not proceed if any item fails.

---

## 1. Master Go/No-Go Checklist

| # | Item | How to check | Pass condition |
|---|------|--------------|----------------|
| 1 | **Python 3.8+** installed | `python --version` or `python3 --version` | Version ≥ 3.8 |
| 2 | **Repo is clean** | `git status` | `nothing to commit` |
| 3 | **identity.lock present** | `ls aios/identity/identity.lock` | File exists |
| 4 | **Port 1313 is free** | `lsof -i :1313` (Linux/Mac) or `netstat -ano \| findstr :1313` (Windows) | No output |
| 5 | **Dry run boots** | `python aios/main.py --ui none` — watch output, then Ctrl+C | `All subsystems ONLINE` printed, no ERROR lines |
| 6 | **Web server starts** | Look for `[WEB] Server started:` in the boot log | URL printed, no WARNING |
| 7 | **API responds** | `curl -s http://localhost:1313/api/status` | JSON with `"status":"ONLINE"` |
| 8 | **Heartbeat alive** | `curl -s http://localhost:1313/api/heartbeat` | `"alive":true` |
| 9 | **Command works** | `curl -s -X POST http://localhost:1313/api/command -H "Content-Type: application/json" -d '{"cmd":"1.1"}'` | Report text in response |
| 10 | **Browser UI loads** | Open `http://localhost:1313` | Dashboard visible, right panel shows heartbeat ticking |

All 10 items must be ✓ before proceeding to the demo.

---

## 2. Setup Steps

```bash
# Clone (if needed)
git clone https://github.com/Cbetts1/AIOS-CC2.git
cd AIOS-CC2

# Verify Python (no extra packages needed)
python --version   # must be 3.8+

# Windows only: install curses support for terminal mode
pip install windows-curses
```

---

## 3. Start the System

### Option A — Web UI (recommended for demos)
```bash
python aios/main.py --ui web
# OR using the launcher:
bash start.sh web

# On Windows:
start.bat web
```

Wait for both lines before opening the browser:
```
  All subsystems ONLINE. AI-OS is ready.
  [WEB] Server started: http://localhost:1313
```

Then open `http://localhost:1313`.

### Option B — Terminal UI
```bash
python aios/main.py --ui terminal
# OR:
bash start.sh terminal
```

### Option C — Background mode (headless)
```bash
python aios/main.py --ui none
```
Poll status via API: `curl http://localhost:1313/api/status`

### Custom port
```bash
python aios/main.py --ui web --port 8080
# Then open: http://localhost:8080
```

---

## 4. Verify the System

Run each of these after startup to confirm health:

```bash
# Full subsystem status (JSON)
curl -s http://localhost:1313/api/status | python3 -m json.tool

# Heartbeat
curl -s http://localhost:1313/api/heartbeat

# Full system report (command 1.1)
curl -s -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -d '{"cmd":"1.1"}'

# Diagnostic report (command 11.1)
curl -s -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -d '{"cmd":"11.1"}'
```

---

## 5. Repeatable Demo Flow (≈ 5 minutes)

```
STEP 1 — Launch
    python aios/main.py --ui web
    Wait for: "All subsystems ONLINE." and "[WEB] Server started:"

STEP 2 — Open dashboard
    Open http://localhost:1313 in browser.
    Confirm heartbeat counter is incrementing in the right panel.

STEP 3 — Full system report
    CMD> box: type  1.1  and press Enter / SEND
    Show: all 14 subsystems listed as ONLINE

STEP 4 — Diagnostics
    CMD> box: type  11.1
    Show: health check, all layers green

STEP 5 — Live sensors
    CMD> box: type  4.4
    Show: simulated CPU temp, load, battery

STEP 6 — Heartbeat
    CMD> box: type  5.3
    Show: beat count, last beat timestamp

STEP 7 — Layer status
    CMD> box: type  1.2
    Show: all 7 layers listed

STEP 8 — Clean shutdown
    Ctrl+C in the terminal
    Expected: "AI-OS shutdown complete."
```

### Key talking points

| Point | What to say |
|-------|-------------|
| Architecture | "7-layer OS running entirely on Python stdlib — no pip installs needed." |
| Virtual hardware | "CPU, memory (64MB virtual), storage (1GB virtual), network (10.0.0.0/8 virtual), sensors — all simulated." |
| Self-managing | "AuraEngine ticks every second: builder, repair, docs, and evolution sub-engines run continuously." |
| Identity | "Operator identity is locked in identity.lock — cannot be overridden without the token." |
| Web UI | "Dashboard auto-refreshes every 3 seconds. Full REST API: /api/status, /api/heartbeat, /api/command." |

---

## 6. Debug Steps

### System won't boot

```bash
# Run with verbose Python to see the exact import that fails
python -v aios/main.py --ui none 2>&1 | head -50

# Check Python path is correct (run from repo root)
ls aios/main.py   # must exist
```

### Port already in use

```bash
# Find the conflicting process
lsof -i :1313        # Linux / Mac / Termux
netstat -ano | findstr :1313   # Windows

# Kill it
kill <PID>           # Linux / Mac / Termux
taskkill /PID <PID> /F   # Windows

# Or use a different port
python aios/main.py --ui web --port 8080
```

Boot log when port is in use (non-fatal — system still runs):
```
  [WEB] WARNING: Could not bind to port 1313: [Errno 98] Address already in use
  [WEB] Web UI unavailable. Use --port to choose a different port.
```

### Web UI loads but shows no data

1. Check boot log for `[WEB] Server started:` — if missing, port was in use (see above).
2. Refresh the page (it auto-refreshes every 3 seconds).
3. Test the API directly: `curl http://localhost:1313/api/status`

### Terminal UI is blank or crashes

- Windows: `pip install windows-curses` then retry.
- SSH/headless: use `--ui web` or `--ui none`.
- Small terminal window: resize to at least 80×24.

### identity.lock missing

```bash
git checkout aios/identity/identity.lock
```

### Emergency restart

```bash
# Kill any lingering process on the default port and restart
lsof -i :1313 | awk 'NR>1 {print $2}' | xargs kill 2>/dev/null; true
python aios/main.py --ui web
```

---

## 7. Shutdown

```bash
# Normal: press Ctrl+C in the launch terminal
# Expected output:
#   Interrupted by operator.
#   AI-OS shutdown complete.

# Verify port is released
lsof -i :1313   # should return nothing
```

---

## 8. Quick Reference

| Task | Command |
|------|---------|
| Start web mode | `python aios/main.py --ui web` |
| Start terminal mode | `python aios/main.py --ui terminal` |
| Start background mode | `python aios/main.py --ui none` |
| Custom port | `python aios/main.py --ui web --port 8080` |
| Check status | `curl http://localhost:1313/api/status` |
| Check heartbeat | `curl http://localhost:1313/api/heartbeat` |
| Run a command | `curl -X POST http://localhost:1313/api/command -H "Content-Type: application/json" -d '{"cmd":"1.1"}'` |
| Check port in use | `lsof -i :1313` |
| Stop old process | `kill $(lsof -t -i :1313)` |
| Windows launcher | `start.bat web` |
| Unix launcher | `bash start.sh web` |

---

*AIOS-CC2 — Operator: Chris | v2.0.0-CC2*
