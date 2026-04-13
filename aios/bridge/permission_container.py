"""AI-OS Permission Container - Whitelist-based host call sandboxing."""
import time


class PermissionContainer:
    # Default whitelist of permitted internal actions
    DEFAULT_WHITELIST = {
        "read_vram", "write_vram",
        "read_vstorage", "write_vstorage", "delete_vstorage",
        "read_vsensor", "tick_vsensor",
        "vnet_send", "vnet_receive",
        "state_get", "state_set",
        "log_write",
        "heartbeat_send",
        "mesh_broadcast",
        "engine_tick",
        "proc_write",
    }

    def __init__(self):
        self._whitelist = set(self.DEFAULT_WHITELIST)
        self._denied_actions = set()
        self._check_log = []
        self._init_time = time.time()

    def allow(self, action: str) -> None:
        self._whitelist.add(action)
        self._denied_actions.discard(action)

    def deny(self, action: str) -> None:
        self._denied_actions.add(action)
        self._whitelist.discard(action)

    def check(self, action: str) -> bool:
        if action in self._denied_actions:
            result = False
        elif action in self._whitelist:
            result = True
        else:
            result = False
        self._check_log.append({
            "action": action,
            "result": "allowed" if result else "denied",
            "ts": time.time(),
        })
        if len(self._check_log) > 1000:
            self._check_log = self._check_log[-500:]
        return result

    def get_whitelist(self) -> list:
        return sorted(self._whitelist)

    def get_denied(self) -> list:
        return sorted(self._denied_actions)

    def get_check_log(self, limit: int = 50) -> list:
        return list(self._check_log[-limit:])

    def status(self) -> dict:
        return {
            "component": "PermissionContainer",
            "whitelist_count": len(self._whitelist),
            "denied_count": len(self._denied_actions),
            "checks_performed": len(self._check_log),
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
