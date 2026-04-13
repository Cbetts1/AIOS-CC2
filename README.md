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
├── start.sh                 ← Unix/Mac launcher
└── start.bat                ← Windows launcher
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
python aios/main.py [--ui terminal|web|none] [--port PORT] [--operator-token TOKEN]

  --ui terminal        Launch curses terminal UI (default)
  --ui web             Launch web server only; open http://localhost:PORT
  --ui none            Background mode (engine runs, no UI)
  --port 1313          Web server port (default: 1313)
  --operator-token T   Validate an operator token at startup
```

To generate your operator token:
```python
import hashlib
raw = "Chris-2026-04-13T08:39:00Z".encode()
print(hashlib.sha256(raw).hexdigest())
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

## Frequently Asked Questions

**Q: Nothing happens when I run it on Windows.**  
A: The terminal UI requires `curses`. On Windows, install `windows-curses`:
```
pip install windows-curses
```
Or use Web mode instead: `python aios/main.py --ui web`

**Q: Where are logs stored?**  
A: All logs are in-memory. They are visible via the command menus (Menu 15) and the `/api/status` JSON. Persistent log files are on the roadmap.

**Q: How do I shut down cleanly?**  
A: In the terminal UI, press `q` to exit the UI (the engine keeps running). To stop everything, press `Ctrl+C` in the terminal where you launched `main.py`.

**Q: What is `identity.lock`?**  
A: A JSON file that hard-locks the operator identity to "Chris". The `IdentityLock` module reads it at boot. Do not delete it.

**Q: Can I add my own commands?**  
A: Yes — edit `aios/command/command_center.py`. The `MENU` dict defines the menu structure, and `_render_status_for()` is the dispatcher. Add a new `elif top == "X"` block.

---

## Roadmap (what still needs to be built)

See `Buidrhis.md` for the full design spec. Key next steps:

- [ ] Persistent log files (write security/audit logs to `VirtualStorage` and optionally to disk)
- [ ] Real APK — integrate Kivy or BeeWare to produce an Android package
- [ ] Automated tests (`pytest` suite for each subsystem)
- [ ] Web UI authentication (login form before `/api/status` is accessible)
- [ ] Real cloud bridge (allow an optional external API layer on top of the virtual one)
- [ ] Self-hosting: package as a Docker container so the system can host itself

---

*AI-OS v2.0.0-CC2 — Operator: Chris*

