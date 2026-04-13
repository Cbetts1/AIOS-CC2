# AI-OS Legal & Compliance Documentation

## Overview

AI-OS is designed with legal compliance and ethical operation as core principles,
enforced at the kernel level by the LegalCortex engine.

## Permanently Blocked Actions

The following actions are blocked unconditionally:

| Action | Reason |
|--------|--------|
| `external_network_call` | No external network access permitted |
| `write_host_filesystem` | Host filesystem is read-only |
| `exec_arbitrary_code` | No arbitrary code execution |
| `access_host_credentials` | No access to host credentials |
| `modify_host_environment` | Host environment is immutable |
| `bypass_sandbox` | Sandbox cannot be bypassed |
| `disable_identity_lock` | Identity lock is permanent |

## Audit Requirements

The following actions require audit before execution:

- `shutdown` — Operator authentication required
- `evolution_trigger` — Evolution requires authorization
- `security_override` — Security changes are logged
- `identity_unlock` — Identity operations are audited
- `modify_policy` — Policy changes are logged
- `install_module` — Module installation is audited
- `sandbox_escape` — Always denied

## Compliance Standards

1. **Isolation**: AI-OS operates entirely in virtual space. No host resources are modified.
2. **Identity**: Operator Chris is the sole authorized operator. Identity is enforced.
3. **Audit Trail**: All security events, policy decisions, and legal actions are logged.
4. **No External Communication**: AI-OS uses a virtual internal network (10.0.0.0/8) only.
5. **Self-Containment**: The system does not make external API calls, CDN requests, or network connections.

## Data Handling

- All data is stored in VirtualStorage (virtual 1GB disk)
- No data is written to host filesystem
- State is held in memory (StateRegistry) and virtual disk
- Logs are stored in `/aios/logs/` directory on virtual storage

## Contact

For compliance questions, contact the designated operator (Chris).

*Document version: 2.0.0-CC2 | Date: 2026-04-13*
