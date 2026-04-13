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
