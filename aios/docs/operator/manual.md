# AI-OS Operator Manual

## Authentication

The system requires operator authentication via `identity.lock`.
Operator: **Chris** | Level: OPERATOR_ONLY

## Starting AI-OS

```bash
# Terminal UI (default)
python aios/main.py --ui terminal

# Web UI
python aios/main.py --ui web

# No UI (background mode)
python aios/main.py --ui none

# With operator token
python aios/main.py --operator-token <token>
```

## Command Center Menu

| No. | Category | Key Operations |
|-----|----------|----------------|
| 1 | System Status | Full report, layer health, subsystem list |
| 2 | Layer Control | Inspect/control each layer |
| 3 | Engine Control | AuraEngine, sub-engines |
| 4 | Virtual Hardware | CPU, memory, storage, sensors |
| 5 | Network Management | Interfaces, mesh, heartbeat |
| 6 | Security & Identity | Auth, policy, sandbox |
| 7 | Cloud Systems | Virtual cloud nodes |
| 8 | Cellular Systems | Signal simulation |
| 9 | Computer Systems | Supervisor, memory map |
| 10 | AI Systems | Evolution, builder, repair |
| 11 | Diagnostics | Health check, error log |
| 12 | Maintenance | Reset, repair, allocate |
| 13 | Legal & Compliance | Audit, violations |
| 14 | Documentation | Docs, API reference |
| 15 | Logs & Audit | All audit logs |
| 16 | Shutdown | Graceful / Emergency |

## Usage Examples

```
# In terminal menu:
1       → System Status menu
1.1     → Full System Report
3.2     → Tick AuraEngine
4.4     → View Sensor Readings
11.1    → Full Diagnostic Report
16.1    → Graceful Shutdown (requires token)
```

## Heartbeat

The system sends heartbeats every 5 seconds via NodeMesh.
Monitor: Menu 5.3 → Heartbeat Status

## Web API

- `GET /api/status` — Full JSON system status
- `GET /api/heartbeat` — Heartbeat status

## Security Notes

- Never share the operator token
- identity.lock must remain locked
- All OPERATOR_ONLY actions require valid token
- SandboxManager prevents external calls

---

## Troubleshooting

### OSError: [Errno 98] Address already in use

The web server could not bind to the configured port. Another process is using it.

**Resolution — use a different port:**
```bash
python aios/main.py --ui web --port 8080
```

**Resolution — free the port (Linux / Termux / Mac):**
```bash
lsof -i :1313       # find the PID
kill <PID>          # stop the old process
python aios/main.py --ui web
```

**Resolution — free the port (Windows):**
```cmd
netstat -ano | findstr :1313
taskkill /PID <PID> /F
```

This error is **non-fatal**. The rest of the system starts normally. Only the web UI is
unavailable until the port is free. Boot log message:
```
  [WEB] WARNING: Could not bind to port 1313: [Errno 98] Address already in use
  [WEB] Web UI unavailable. Use --port to choose a different port.
```

### Terminal UI does not appear (Windows)

Install the Windows curses library:
```
pip install windows-curses
```
Or switch to web mode: `python aios/main.py --ui web`

### System says "ready" but web UI cannot be reached

1. Check the boot log for `[WEB] Server started`. If you see `WARNING` instead, the port is
   in use — see above.
2. Confirm you are opening the correct port in the browser.
3. Test the API directly: `curl http://localhost:1313/api/status`

### Startup fails before "All subsystems ONLINE"

This indicates a missing file or import error. Common causes:
- `aios/identity/identity.lock` is missing or corrupted — restore from git.
- Running `python` (Python 2) instead of `python3` — use `python3 aios/main.py`.
- Working directory is wrong — run from the repo root (where `aios/` is a subdirectory).

---

## Startup Diagnostics

Run the following after launch to confirm everything is healthy:

```bash
# 1. Confirm process is running
ps aux | grep main.py

# 2. Confirm port is bound
lsof -i :1313

# 3. Test the API
curl -s http://localhost:1313/api/status | python3 -m json.tool

# 4. Test the heartbeat
curl -s http://localhost:1313/api/heartbeat

# 5. Run a command (full system report)
curl -s -X POST http://localhost:1313/api/command \
     -H "Content-Type: application/json" \
     -d '{"cmd":"1.1"}'
```

Expected healthy responses:
- `/api/status` → JSON object with `"status": "ONLINE"`
- `/api/heartbeat` → `{"alive": true, ...}`
- `/api/command` with `1.1` → full system report text

---

## Demo Flow (Operator Reference)

### Pre-demo go/no-go checks

| Check | Command | Expected result |
|-------|---------|-----------------|
| Python version | `python --version` | 3.8 or newer |
| Port 1313 free | `lsof -i :1313` | No output |
| Clean repo | `git status` | Nothing to commit |
| System boots | `python aios/main.py --ui none` | `All subsystems ONLINE` |
| API responds | `curl http://localhost:1313/api/status` | `"status":"ONLINE"` |

### Standard demo sequence

```
1. Start:   python aios/main.py --ui web
2. Confirm: "[WEB] Server started: http://localhost:1313"
3. Open:    http://localhost:1313 in browser
4. Demo:    Type 1.1 in CMD box → full system report
5. Demo:    Type 11.1 → diagnostic health check
6. Demo:    Type 4.4 → live sensor readings
7. Demo:    Type 5.3 → heartbeat status
8. Stop:    Ctrl+C → "AI-OS shutdown complete."
```

### Emergency restart

```bash
# Kill any lingering process on port 1313
lsof -i :1313 | awk 'NR>1 {print $2}' | xargs kill 2>/dev/null; true
# Restart
python aios/main.py --ui web
```
