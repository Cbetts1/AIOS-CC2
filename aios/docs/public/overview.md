# AI-OS Public Overview

## AI-OS v2.0-CC2

AI-OS is a 7-layer autonomous operating system that runs entirely on virtual hardware
abstracted from the host machine. It is designed for security, isolation, and intelligent
self-management.

## Architecture

AI-OS uses a layered architecture:

| Layer | Name | Purpose |
|-------|------|---------|
| 1 | Physical Abstraction | Security, policy, identity enforcement |
| 2 | Virtual Hardware | CPU, memory, storage, network, sensors |
| 3 | Kernel Bridge | Host isolation, permission sandboxing |
| 4 | Process & Memory | State management, process supervision |
| 5 | Engine & Intelligence | Aura engine, sub-engines, AI operations |
| 6 | Command & Interface | Command center, menus, API |
| 7 | Application & Output | Web UI, terminal UI, APK, documentation |

## Key Features

- **Fully Virtual**: All hardware is simulated. No host filesystem or network is accessed.
- **Identity Locked**: Operator identity (Chris) is enforced via `identity.lock`.
- **Self-Repairing**: RepairEngine scans for faults and auto-repairs.
- **Policy Controlled**: All actions require appropriate permission level.
- **Legal Compliance**: LegalCortex blocks non-compliant actions automatically.

## Web Interface

Access the web UI at: `http://localhost:1313`

## Terminal Interface

Launch: `python aios/main.py --ui terminal`

## Version

- **Version**: 2.0.0-CC2
- **Build Date**: 2026-04-13
- **Status**: VALID
