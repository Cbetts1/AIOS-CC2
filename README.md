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

# 2. Preflight check (Python version, identity.lock, port)
bash start.sh check

# 3. Launch with the Terminal UI (default — works in any terminal)
python aios/main.py

# 4. OR launch in Web mode (opens a browser dashboard)
python aios/main.py --ui web
# Then open:  http://localhost:1313

# 5. OR run in the background (no UI, just the engine)
python aios/main.py --ui none

# Windows users: double-click start.bat  (or run: start.bat)
# Linux/Mac users: run: bash start.sh
```

### Canned demo
```bash
bash demo.sh          # starts AI-OS, walks every menu via curl, saves logs/demo.log
```

---

## Boot Paths

There are three ways to start AI-OS — use `main.py` for everything except quick
terminal-only work:

| Command | Notes |
|---|---|
| `python aios/main.py` | **Recommended.** Full subsystem boot — all 15 subsystems, cloud loop, web server. |
| `python aios/terminal/start_terminal.py` | Convenience alias — identical to `main.py` but forces terminal UI. |
| `bash start.sh [terminal\|web\|none] [port] [token]` | Shell wrapper for Unix/Mac. |
| `start.bat [terminal\|web\|none] [port] [token]` | Shell wrapper for Windows. |
| `bash start.sh check` | Preflight validation: Python version, identity.lock, port availability. |

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
│   ├── core/                ← Kernel-layer: state, policy, security, identity, memory, log_writer
│   ├── engine/              ← AuraEngine + Builder/Repair/Doc/Evolution/Legal sub-engines
│   ├── virtual/             ← Simulated CPU, RAM, storage, network, sensors
│   ├── bridge/              ← Host-bridge: capability detection, permissions, sandbox
│   ├── mesh/                ← Internal node mesh + heartbeat (asyncio)
│   ├── cloud/               ← CloudController, CloudLoop, CloudNode (TCP socket workers)
│   ├── command/             ← CommandCenter: 16-category menu, banner, status
│   ├── terminal/            ← Curses terminal UI
│   ├── web/                 ← HTTP server + HTML/CSS/JS dashboard
│   ├── apk/                 ← Android app blueprints (bootloader, chat, operator panel)
│   ├── procwriters/         ← /proc-style virtual filesystem writer
│   ├── sandbox/             ← Sandbox policy enforcer
│   └── docs/                ← Markdown documentation (legal, brand, operator, public)
├── tests/                   ← pytest suite (test_boot, test_command_center, test_web_api, …)
├── logs/                    ← Persistent log files (aios.log, debug.log, demo.log)
├── README.md
├── CHANGELOG.md             ← What changed and when
├── DEPLOY.md                ← Deployment guide (bare-metal, Docker, remote, systemd)
├── Buidrhis.md              ← Full design specification / master architecture doc
├── Dockerfile               ← Container build
├── docker-compose.yml       ← One-command demo launch
├── aios.service             ← systemd unit for long-running demo host
├── Procfile                 ← Heroku / Render entry point
├── pytest.ini               ← Test runner configuration
├── requirements.txt         ← Python version note (stdlib only — nothing to install)
├── start.sh                 ← Unix/Mac launcher (also: bash start.sh check)
└── start.bat                ← Windows launcher (also: start.bat check)
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
python aios/main.py [--ui terminal|web|none] [--port PORT]
                    [--operator-token TOKEN] [--debug]

  --ui terminal        Launch curses terminal UI (default)
  --ui web             Launch web server only; open http://localhost:PORT
  --ui none            Background mode (engine runs, no UI)
  --port 1313          Web server port (default: 1313 or $AIOS_PORT env var)
  --operator-token T   Validate an operator token at startup
  --debug              Verbose exception output + write logs/debug.log
```

The web server port can also be set via the `AIOS_PORT` environment variable
(the `--port` flag takes precedence if both are given):

```bash
# Termux / Linux / Mac
export AIOS_PORT=8080
python aios/main.py --ui web

# One-liner
AIOS_PORT=8080 python aios/main.py --ui web

# start.sh respects AIOS_PORT automatically
export AIOS_PORT=8080
bash start.sh web
```

To generate your operator token:
```python
import hashlib
raw = "Chris-2026-04-13T08:39:00Z".encode()
print(hashlib.sha256(raw).hexdigest())
```

---

## Web API

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | none | Liveness probe: `{"status":"OK","uptime_seconds":N}` |
| `/api/status` | GET | none | Full JSON status of all subsystems |
| `/api/heartbeat` | GET | none | Heartbeat beat count and timestamp |
| `/api/proc` | GET | none | Virtual `/proc/aios/` file listing |
| `/api/command` | POST | **password** | Execute a command |
| `/api/debug` | GET | **password** | Full `StateRegistry` dump |

### Admin password

`/api/command` and `/api/debug` require the admin password **`7212`**.
Pass it in any of these ways:

```bash
# JSON body key
curl -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -d '{"cmd": "1.1", "password": "7212"}'

# HTTP header
curl -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -H "X-Admin-Password: 7212" \
     -d '{"cmd": "1.1"}'

# Query param (GET endpoints)
curl "http://localhost:1313/api/debug?password=7212"
```

Open endpoints (no password needed):
```bash
curl http://localhost:1313/api/health
curl http://localhost:1313/api/status
curl http://localhost:1313/api/heartbeat
curl http://localhost:1313/api/proc
```

> **⚠ Security note:** The admin password is a shared secret stored in plain text
> in `aios/web/server.py`.  Change `_ADMIN_PASSWORD` before any public-internet
> deployment.  See [DEPLOY.md](DEPLOY.md) for full security guidance.

---

## Operator Token

The `IdentityLock` uses a SHA-256 token derived from the operator name and the
`created` timestamp in `aios/identity/identity.lock`.

To compute your token:
```python
import hashlib
raw = "Chris-2026-04-13T08:39:00Z".encode()
print(hashlib.sha256(raw).hexdigest())
```

> **⚠ Security note:** Because `identity.lock` is committed to the public repo,
> anyone can compute the default token.  For a private deployment, update the
> `created` field to a new private timestamp and keep it secret.  Then recompute
> the token using the formula above.

---

## Remote Access (ngrok)

The server binds `0.0.0.0:1313` so it accepts remote connections.  For a quick
public demo use [ngrok](https://ngrok.com):

```bash
# Terminal 1 — start AI-OS
python aios/main.py --ui none

# Terminal 2 — expose to the internet
ngrok http 1313
# → https://xxxx.ngrok.io
```

See [DEPLOY.md](DEPLOY.md) for Docker, nginx, systemd, and Heroku options.

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests cover: subsystem boot, all 16 menu commands, web API endpoints (including
admin-password enforcement), identity token derivation, and cloud lifecycle.

---

## Frequently Asked Questions

**Q: I get `OSError: [Errno 98] Address already in use` on startup.**  
A: Another process is already using the web server port (default 1313).
Options:

1. **Use a different port** (quickest fix):
   ```bash
   python aios/main.py --port 8080
   # or
   export AIOS_PORT=8080 && python aios/main.py
   ```

2. **Find and stop the conflicting process** (Linux / Mac / Termux):
   ```bash
   lsof -i :1313        # shows which process owns the port
   kill <PID>           # stop it, then relaunch AI-OS
   ```
   Windows:
   ```
   netstat -ano | findstr :1313
   taskkill /PID <PID> /F
   ```

3. **Kill a stale AI-OS process** (Termux):
   ```bash
   pkill -f "aios/main.py"
   ```

The system will still start and all subsystems will be ONLINE even if the web
server cannot bind — only the browser dashboard will be unavailable.

**Q: Nothing happens when I run it on Windows.**  
A: The terminal UI requires `curses`. On Windows, install `windows-curses`:
```
pip install windows-curses
```
Or use Web mode instead: `python aios/main.py --ui web`

**Q: Where are logs stored?**  
A: Log files are written to the `logs/` directory:
- `logs/aios.log` — all `CommandCenter` console log entries (JSON-lines, rotates at 5 MB)
- `logs/debug.log` — written when `--debug` is passed
- `logs/demo.log` — written by `demo.sh`

**Q: How do I shut down cleanly?**  
A: In the terminal UI, press `q` to exit the UI (the engine keeps running). To stop everything, press `Ctrl+C` in the terminal where you launched `main.py`. SIGTERM is also handled (for Docker `docker stop` and systemd).

**Q: What is `identity.lock`?**  
A: A JSON file that hard-locks the operator identity to "Chris". The `IdentityLock` module reads it at boot. Do not delete it. See the "Operator Token" section above for regeneration instructions.

**Q: Can I add my own commands?**  
A: Yes — edit `aios/command/command_center.py`. The `MENU` dict defines the menu structure, and `_render_status_for()` is the dispatcher. Add a new `elif top == "X"` block.

---

## Roadmap (what still needs to be built)

See `Buidrhis.md` for the full annotated design spec.

- [x] Persistent log files (`logs/aios.log` via `LogWriter`)
- [x] Automated tests (`tests/` pytest suite)
- [x] Web API authentication (admin password `7212`)
- [x] Docker container + docker-compose
- [x] CI (GitHub Actions)
- [x] `/api/health`, `/api/debug`, `/api/proc` endpoints
- [x] `--debug` flag and SIGTERM handler
- [ ] Real APK — integrate Kivy or BeeWare to produce an Android package
- [ ] Real cloud bridge (optional external API layer on top of the virtual one)
- [ ] Mobile-responsive web UI (CSS media queries)

---

*AI-OS v2.0.0-CC2 — Operator: Chris*

