# Changelog

All notable changes to AI-OS CC2 are documented here.

---

## [2.0.1] — 2026-04-13

### Fixed
- **`command_center.py`**: Removed dead duplicate `elif top == "7"` block that
  shadowed the real cloud command dispatcher (menu items 7.1–7.9 now work correctly).
- **`web/server.py`**: Removed `os.chdir()` call from the GET handler — it caused
  a race condition when concurrent requests were served from different threads.
- **`start.sh`**: Replaced `major * 10 + minor` Python version arithmetic (broken
  for Python 3.10+) with a proper `(major, minor) >= (3, 8)` tuple comparison.
- **`start_terminal.py`**: Upgraded legacy boot path to match `main.py`'s full
  subsystem sequence — it now attaches `supervisor`, `proc_writers`, `cloud`, and
  the `CloudLoop` so all menu commands work when launched from this file.

### Added
- **Admin password auth (`7212`)** on `POST /api/command` and `GET /api/debug`.
  Pass in JSON body (`"password": "7212"`), query param (`?password=7212`), or
  HTTP header (`X-Admin-Password: 7212`).  Open endpoints unchanged.
- **`GET /api/health`** — unauthenticated liveness/readiness probe returning
  `{"status":"OK","version":"...","uptime_seconds":N}`.
- **`GET /api/debug`** (admin only) — full `StateRegistry.dump()` as JSON.
- **`GET /api/proc`** — lists and reads virtual `/proc/aios/` files.
- **`aios/core/log_writer.py`** — thread-safe JSON-lines log writer with rotation.
  Wired into `CommandCenter._log()` so all console log entries are persisted to
  `logs/aios.log`.
- **`--debug` flag** for `main.py` — enables verbose exception tracebacks in the
  endless loop, shortens heartbeat interval to 1 s, and writes `logs/debug.log`.
- **SIGTERM handler** in `main.py` — Docker `docker stop` and systemd now shut
  down cleanly instead of being killed.
- **`StateRegistry.reset()`** class-method for test isolation.
- **`CommandCenter.attach_log_writer(lw)`** — wire in a `LogWriter` after boot.
- **`tests/`** — full pytest suite:
  - `conftest.py` — auto-resets `StateRegistry` singleton between tests.
  - `test_boot.py` — verifies every subsystem boots with `healthy: True`.
  - `test_command_center.py` — exercises all 16 top-level menus and sub-commands.
  - `test_web_api.py` — starts a live server, hits every endpoint.
  - `test_identity.py` — deterministic token derivation, wrong-operator rejection.
  - `test_cloud.py` — boot, spawn, exec, stop lifecycle.
- **`pytest.ini`** — test runner configuration.
- **`.github/workflows/ci.yml`** — GitHub Actions CI (Python 3.9 + 3.11).
- **`demo.sh`** — canned live demo runner: starts AI-OS, waits for readiness,
  walks through every menu section via `curl`, saves log to `logs/demo.log`.
- **`start.sh` improvements**:
  - `bash start.sh check` — preflight: Python version, identity.lock, operator token, port availability.
  - Third argument `[operator-token]` passed through to `--operator-token`.
  - Port pre-check warns if the port is already in use.
- **`start.bat` improvements**: same `check` mode and token passthrough.
- **`Dockerfile`** + **`docker-compose.yml`** — containerised deployment with
  health check.
- **`aios.service`** — systemd unit file for long-running demo host.
- **`Procfile`** — Heroku/Render one-liner.
- **`logs/.gitkeep`** — placeholder so the log directory is tracked by git.
- **`DEPLOY.md`** — deployment guide (bare-metal, Docker, remote/ngrok).
- **`CHANGELOG.md`** — this file.

---

## [2.0.0] — 2026-04-13  (initial CC2 release)

- 7-layer AI-OS architecture fully implemented in stdlib Python.
- `CommandCenter` with 16-section menu, curses terminal UI, web dashboard.
- `AuraEngine` orchestrating `BuilderEngine`, `RepairEngine`, `DocumentationEngine`,
  `EvolutionEngine`, `LegalCortex`.
- `VirtualCPU`, `VirtualMemory`, `VirtualStorage`, `VirtualNetwork`, `VirtualSensors`.
- `HostBridge`, `NodeMesh`, `HeartbeatSystem`, `Sandbox`, `ProcWriters`.
- `CloudController`, `CloudLoop`, `CloudNode` (TCP socket-based compute nodes).
- `IdentityLock` hard-locked to operator "Chris".
- Web server (`AIWebServer`) on port 1313 serving static dashboard + JSON API.
