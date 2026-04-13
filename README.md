# AIOS-CC2

> **AI-OS Command Center v2** — a self-contained, virtual AI operating system
> with a 7-layer architecture, terminal UI, web UI, and simulated hardware.
> Operator: **Chris** | Version: **2.0.0-CC2**

---

## Quick Start (5 steps)

**Requirements:** Python 3.8 or newer.  No extra packages needed.

```bash
# 1. Clone the repo (if you haven't already)
git clone https://github.com/Cbetts1/AIOS-CC2.git
cd AIOS-CC2

# 2. Launch with the Terminal UI (default — works in any terminal)
python aios/main.py

# 3. OR launch in Web mode (opens a browser dashboard)
python aios/main.py --ui web
# Then open:  http://localhost:1313

# 4. OR run in the background (no UI, just the engine)
python aios/main.py --ui none

# 5. Windows users: double-click start.bat  (or run: start.bat)
#    Linux/Mac users: run: bash start.sh
```

---

## Terminal UI — How to use it

Once launched you will see:

```
=======================================================================
     AI-OS COMMAND CENTER v2.0-CC2
     Operator: Chris  |  10.0.0.0/8  |  ONLINE
=======================================================================

┌──────────────┐
│  MAIN MENU   │
│  1. System   │        ┌─ CONSOLE ────────────────────────┐
│  2. Layers   │        │                                  │
│  3. Engines  │        │  AI-OS is ready.                 │
│  ...         │        │                                  │
└──────────────┘        └──────────────────────────────────┘
  CMD> _
```

### Controls

| Key / Input | Action |
|-------------|--------|
| `↑` / `↓`  | Move the highlighted menu selection up/down |
| `Enter`     | Execute the highlighted menu item |
| Type `1.1` + Enter | Run command 1.1 directly (Full System Report) |
| Type `11.1` + Enter | Full diagnostic report |
| `q`         | Quit the terminal UI (system keeps running) |

### Quick command reference

| Command | What it does |
|---------|-------------|
| `1`     | System Status menu |
| `1.1`   | Full system report |
| `1.2`   | Layer health (Layers 1–7) |
| `1.3`   | List all subsystems |
| `3`     | Engine Control menu |
| `3.2`   | Tick the AuraEngine manually |
| `4.1`   | Virtual CPU status |
| `4.4`   | Live sensor readings |
| `5.1`   | List virtual network interfaces |
| `5.3`   | Heartbeat status |
| `6.1`   | Identity / security lock status |
| `7.1`   | Cloud layer status |
| `8.1`   | Cellular layer status |
| `9.1`   | Process supervisor status |
| `10.1`  | AI engine (AuraEngine) full status |
| `11.1`  | Full diagnostic report |
| `12.2`  | Reset the virtual CPU |
| `13.1`  | Legal compliance status |
| `14.1`  | System overview documentation |
| `15.1`  | Security audit log |
| `16.1`  | Graceful shutdown (requires token) |

---

## Web UI — How to use it

```bash
python aios/main.py --ui web
# Open browser: http://localhost:1313
```

- **Left panel** — 16-category navigation menu. Click any category to expand it, then click a sub-item.
- **Center console** — Output panel. Type any command (e.g. `1.1`, `3.2`) in the `CMD>` box and press **SEND** or **Enter**.
- **Right panel** — Live dashboard: heartbeat, uptime, layer dots, sensor readings, network stats.
- **Status bar** — Bottom bar shows AIOS status, layer health, heartbeat count, operator.

The web UI auto-refreshes status every 3 seconds.

---

## Project layout

```
AIOS-CC2/
├── aios/
│   ├── main.py              ← Entry point (run this)
│   ├── system.manifest      ← Version / subsystem manifest (JSON)
│   ├── architecture.map     ← ASCII layer diagram
│   ├── identity/
│   │   └── identity.lock    ← Operator identity (JSON, do not edit)
│   ├── core/                ← Kernel-layer: state, policy, security, identity, memory
│   ├── engine/              ← AuraEngine + Builder/Repair/Doc/Evolution/Legal sub-engines
│   ├── virtual/             ← Simulated CPU, RAM, storage, network, sensors
│   ├── bridge/              ← Host-bridge: capability detection, permissions, sandbox
│   ├── mesh/                ← Internal node mesh + heartbeat (asyncio)
│   ├── command/             ← CommandCenter: 16-category menu, banner, status
│   ├── terminal/            ← Curses terminal UI
│   ├── web/                 ← HTTP server + HTML/CSS/JS dashboard
│   ├── apk/                 ← Android app blueprints (bootloader, chat, operator panel)
│   ├── procwriters/         ← /proc-style virtual filesystem writer
│   ├── sandbox/             ← Sandbox policy enforcer
│   └── docs/                ← Markdown documentation (legal, brand, operator, public)
├── README.md
├── Buidrhis.md              ← Full design specification / master architecture doc
├── requirements.txt         ← Python version note (stdlib only — nothing to install)
├── health_check.py          ← Standalone health check (exit 0 = all clear)
├── demo.py                  ← Repeatable live-demo script
├── start.sh                 ← Unix/Mac launcher
├── start.bat                ← Windows launcher
└── tests/
    └── test_boot.py         ← pytest suite (42 tests, stdlib + pytest)
```

---

## Architecture — 7 Layers

```
LAYER 7  Application & Output  →  Web UI (port 1313), Terminal UI, APK
LAYER 6  Command & Interface   →  CommandCenter, Menu, REPL, API
LAYER 5  Engine & Intelligence →  AuraEngine, Builder, Repair, Docs, Evolution, LegalCortex
LAYER 4  Process & Memory      →  ProcessSupervisor, MemoryMap, StateRegistry, ProcWriters
LAYER 3  Kernel Bridge         →  HostBridge, SandboxManager, PermissionContainer
LAYER 2  Virtual Hardware      →  VirtualCPU, VirtualMemory (64MB), VirtualStorage (1GB)
                                   VirtualNetwork (10.0.0.0/8), VirtualSensors
LAYER 1  Physical Abstraction  →  PolicyEngine, SecurityKernel, IdentityLock, Heartbeat
```

---

## Command-line options

```
python aios/main.py [--ui terminal|web|none] [--port PORT] [--operator-token TOKEN] [--trace-file PATH]

  --ui terminal        Launch curses terminal UI (default)
  --ui web             Launch web server only; open http://localhost:PORT
  --ui none            Background mode (engine runs, no UI)
  --port 1313          Web server port (default: 1313)
  --operator-token T   Validate an operator token at startup
  --trace-file PATH    Write append-only event/command trace to PATH
```

To generate your operator token:
```python
import hashlib
raw = "Chris-2026-04-13T08:39:00Z".encode()
print(hashlib.sha256(raw).hexdigest())
```

To launch with persistent trace logging:
```bash
python aios/main.py --ui none --trace-file aios_trace.log
```

---

## Web API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Full JSON status of all subsystems |
| `/api/heartbeat` | GET | Heartbeat beat count and timestamp |
| `/api/command` | POST | Execute a command; body: `{"cmd": "1.1"}` |

Example:
```bash
curl http://localhost:1313/api/status
curl -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -d '{"cmd": "1.1"}'
```

---

## Health Check

Run the built-in health check at any time (no server required):

```bash
# Quick check — exit 0 means all clear
python health_check.py

# Verbose output (shows component detail)
python health_check.py --verbose

# JSON output (for CI / automation)
python health_check.py --json
```

Expected output:
```
========================================================
  AI-OS CC2 — Health Check Results
========================================================
  ✓  state
  ✓  policy
  ✓  security
  ✓  identity
  ✓  memory
  ✓  vcpu
  ✓  vmem
  ✓  vstorage
  ✓  vnet
  ✓  vsensors
  ✓  bridge
  ✓  mesh
  ✓  aura
  ✓  cloud
  ✓  heartbeat
  ✓  command_routing  (7/7 commands OK)
  ✓  api_status_dict
--------------------------------------------------------
  Result : PASS
  Passed : 17/17
========================================================
```

---

## Live Demo

Run the repeatable live demo (no TTY/curses required):

```bash
# Full demo with step pauses (ideal for showing live)
python demo.py

# Fast demo — no pauses (CI / quick check)
python demo.py --fast

# Demo with trace log written to demo_trace.log
python demo.py --trace
```

The demo boots all 14+ subsystems, runs 14 key commands across every system
layer, starts the cloud layer, then prints a pass/fail summary.

---

## Testing

Run the full pytest suite:

```bash
# Install pytest once (nothing else needed — stdlib only otherwise)
pip install pytest

# Run all 42 tests
python -m pytest tests/ -v

# Run just health checks
python -m pytest tests/test_boot.py::TestHealth -v

# Run just command routing tests
python -m pytest tests/test_boot.py::TestCommands -v
```

---

## Observability

### In-memory logs (always available via menu)

| Menu | What it shows |
|------|--------------|
| `15.1` | Security event log (last 20 entries) |
| `15.2` | Policy audit log (last 20 entries) |
| `15.3` | Legal audit log |
| `15.4` | Engine evolution log |
| `15.5` | Full audit dump (entry counts for all logs) |
| `11.3` | Error log (last 10 security events) |

### Trace file (persistent, append-only)

Enable with `--trace-file PATH`. Each line is:
```
[2026-04-13T17:25:14.001497+00:00] CMD   1.1 -> version: 2.0.0-CC2 ...
```

### Web API health endpoint

```bash
# Returns JSON with all subsystem health states
curl http://localhost:1313/api/status | python3 -m json.tool

# Returns heartbeat state
curl http://localhost:1313/api/heartbeat
```

---

## Troubleshooting

### Terminal UI is blank or crashes
- Try `--ui none` or `--ui web` as a fallback.
- On Windows, install `windows-curses`:  `pip install windows-curses`
- Terminal must be at least 80×24 characters.

### Web UI is not accessible
- Check nothing else is on port 1313: `lsof -i :1313`
- Use `--port 1314` (or any free port) to change it.
- Firewall: make sure the port is open if testing remotely.

### `IdentityLockError: Identity mismatch`
- Do not edit `aios/identity/identity.lock`. It must contain `"operator":"Chris"`.
- If the file is missing or corrupted, restore it from the repo or recreate:
  ```json
  {"operator":"Chris","locked":true,"level":"operator-only","created":"2026-04-13T08:39:00Z"}
  ```

### Heartbeat shows as unhealthy at boot
- The heartbeat starts asynchronously.  It will show as healthy once the
  endless loop calls `beat_sync()` (within ~1 second of startup).
- Run `5.3` in the terminal to confirm — `beat_count > 0` means it is working.

### `ModuleNotFoundError: No module named 'aios'`
- Run from the repo root: `python aios/main.py`
- Do **not** cd into `aios/` before running.

### Cloud layer shows `Running: False`
- The cloud layer starts automatically. Use `7.3` (Start Cloud) to manually
  start it if it reports as stopped.
- Cloud is a virtual layer and does not require any external service.

### Port already in use
```bash
# Find what is using port 1313
lsof -i :1313
# Use a different port
python aios/main.py --ui web --port 1314
```

### Silent crash with no output
- Run `python health_check.py` to isolate which component failed.
- Run `python health_check.py --verbose` for detailed output.
- Check Python version: `python --version` — must be 3.8 or newer.

---

## Deployment Guide

### Minimum requirements
- Python 3.8 or newer
- ~50 MB disk (for trace logs if enabled)
- 64 MB RAM
- No internet connection required
- No external services required
- No environment variables required

### One-command startup

```bash
# Terminal (default)
python aios/main.py

# Web only
python aios/main.py --ui web

# Background + trace
python aios/main.py --ui none --trace-file /tmp/aios_trace.log

# Shell script launchers
bash start.sh              # Linux / macOS
start.bat                  # Windows (double-click or run in cmd)
bash start.sh web 1313     # Web mode, port 1313
```

### Running as a background service (Linux)

```bash
# Using nohup (logs go to aios_stdout.log)
nohup python aios/main.py --ui none --trace-file ~/aios_trace.log > aios_stdout.log 2>&1 &
echo $! > ~/aios.pid

# Stop the process
kill $(cat ~/aios.pid)
```

### Checking if it is running

```bash
# If web mode: check the heartbeat endpoint
curl http://localhost:1313/api/heartbeat

# Python health check (no server needed)
python health_check.py
```

---

## Acceptance Criteria

The system is **READY** when all of the following are true:

- [ ] `python health_check.py` exits with code 0 and "PASS"
- [ ] `python demo.py --fast` exits with "PASS (14/14 steps)"
- [ ] `python -m pytest tests/ -v` shows 42/42 passed
- [ ] `python aios/main.py --ui none` boots without errors
- [ ] `curl http://localhost:1313/api/heartbeat` returns `{"alive": true, ...}`
- [ ] `curl http://localhost:1313/api/status` returns JSON with `"running": true`
- [ ] Terminal UI renders without errors on the target platform
- [ ] `identity.lock` is present and contains `"operator":"Chris"`

The system is **NOT READY** if any of the above fails.

---

## Live Demo Readiness Checklist

Use this checklist before any live demo or real-world test:

### Environment
- [ ] Python 3.8+ confirmed: `python --version`
- [ ] No conflicting process on port 1313: `lsof -i :1313`
- [ ] Repo is up to date: `git pull`
- [ ] `aios/identity/identity.lock` exists and is valid JSON

### Boot validation
- [ ] `python health_check.py` — PASS (17/17)
- [ ] `python demo.py --fast` — PASS (14/14)
- [ ] `python -m pytest tests/ -v` — 42 passed

### Runtime validation
- [ ] `python aios/main.py --ui web` starts without error
- [ ] Browser opens `http://localhost:1313` — dashboard visible
- [ ] Left menu shows all 16 categories
- [ ] Right panel shows heartbeat, uptime, layer dots
- [ ] Type `1.1` in CMD box — Full system report appears
- [ ] Type `11.2` in CMD box — All components show a check mark

### Trace / observability (optional)
- [ ] `python aios/main.py --ui none --trace-file /tmp/demo_trace.log` runs
- [ ] Inspect `/tmp/demo_trace.log` — shows BOOT and CMD entries

### Known-good demo commands
1. `1.1` — Full system report: version 2.0.0-CC2, all layers online
2. `11.2` — Health check: every component shows a check mark
3. `4.4` — Live sensor readings: CPU temp, load, memory
4. `5.3` — Heartbeat: beat count is incrementing
5. `7.1` — Cloud layer: running, nodes, tasks
6. `15.5` — Full audit dump: security, policy, legal event counts

---

## Master Checklist — Forgotten Items

Items that are easy to miss during setup, demo, or deployment:

### Setup
- [ ] Run from **repo root** (not inside `aios/`)
- [ ] Do not edit `aios/identity/identity.lock`
- [ ] No `pip install` needed (stdlib only) except `pytest` for tests and `windows-curses` on Windows
- [ ] Python path is automatically configured by `aios/main.py`

### Demo
- [ ] Run `demo.py` first to confirm the system is live-demo ready
- [ ] Use `health_check.py --json` for CI integration
- [ ] The web UI auto-refreshes every 3 s — wait a moment after boot before showing it
- [ ] The trace file is append-only — delete or truncate it before a fresh demo

### Debugging
- [ ] Use `11.1` for a quick full diagnostic
- [ ] Use `11.2` to see which component failed its health check
- [ ] Use `15.1` through `15.5` for all audit logs
- [ ] Use `python health_check.py --verbose` for root-cause isolation

### Deployment
- [ ] `start.sh` / `start.bat` handle Python version checks automatically
- [ ] Port 1313 can be changed with `--port PORT`
- [ ] Trace file is optional but recommended for production use
- [ ] No external services, no internet, no cloud accounts required

### After-demo / post-build
- [ ] Clear trace log before next session
- [ ] Re-run health check to confirm clean state
- [ ] Commit any changes made during the demo session

### Security
- [ ] `identity.lock` is operator-only — do not share or commit modified versions
- [ ] The web server binds to `0.0.0.0` — restrict with a firewall if on a shared network
- [ ] No passwords or API keys are stored in the codebase
- [ ] All logs are in-memory unless `--trace-file` is set

### Versioning / updates
- [ ] `aios/system.manifest` contains the canonical version: `2.0.0-CC2`
- [ ] `CommandCenter.VERSION` must match the manifest on release
- [ ] Update `Buidrhis.md` when the architecture changes

---

## Go / No-Go Criteria

| Criterion | Go | No-Go |
|-----------|-----|-------|
| `health_check.py` exits 0 | Yes | No |
| `demo.py --fast` exits 0 | Yes | No |
| 42/42 pytest tests pass | Yes | No |
| `/api/heartbeat` returns `alive:true` | Yes | No |
| Terminal UI renders | Yes | No |
| `identity.lock` intact | Yes | No |

If any No-Go condition is true — do not demo. Fix it first.

---

## Post-Demo Follow-up Checklist

After a live demo or real-world test session:

- [ ] Note any command that produced unexpected output
- [ ] Save the trace log with a date stamp for reference
- [ ] Run `python health_check.py` again to confirm post-demo state
- [ ] File issues for anything that behaved unexpectedly
- [ ] Update `Buidrhis.md` if architecture decisions changed
- [ ] Bump version in `aios/system.manifest` and `CommandCenter.VERSION` for the next release

---

## Frequently Asked Questions

**Q: Nothing happens when I run it on Windows.**
A: The terminal UI requires `curses`. On Windows, install `windows-curses`:
```
pip install windows-curses
```
Or use Web mode instead: `python aios/main.py --ui web`

**Q: Where are logs stored?**
A: All logs are in-memory. They are visible via the command menus (Menu 15)
and the `/api/status` JSON. Use `--trace-file` to persist them to disk.

**Q: How do I shut down cleanly?**
A: In the terminal UI, press `q` to exit the UI (the engine keeps running).
To stop everything, press `Ctrl+C` in the terminal where you launched `main.py`.

**Q: What is `identity.lock`?**
A: A JSON file that hard-locks the operator identity to "Chris". The
`IdentityLock` module reads it at boot. Do not delete or edit it.

**Q: Can I add my own commands?**
A: Yes — edit `aios/command/command_center.py`. The `MENU` dict defines the
menu structure, and `_generic_handler()` is the dispatcher. Add a new
`elif top == "X"` block and a matching `MENU` entry.

**Q: How do I run the system in CI?**
A: Use `python health_check.py --json` — it exits 0 on pass, 1 on fail, and
outputs structured JSON for easy parsing. Or run `python -m pytest tests/ -v`.

**Q: Is any internet connection required?**
A: No. AIOS-CC2 is fully self-contained. The cloud layer is virtual and
requires no external cloud provider.

---

## Roadmap (what still needs to be built)

See `Buidrhis.md` for the full design spec. Key next steps:

- [ ] Persistent log files (write security/audit logs to `VirtualStorage` and optionally to disk)
- [ ] Real APK — integrate Kivy or BeeWare to produce an Android package
- [ ] Web UI authentication (login form before `/api/status` is accessible)
- [ ] Real cloud bridge (allow an optional external API layer on top of the virtual one)
- [ ] Self-hosting: package as a Docker container so the system can host itself
- [ ] Expanded test coverage (integration tests for web server, cloud loop)

---

*AI-OS v2.0.0-CC2 — Operator: Chris*
