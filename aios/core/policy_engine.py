"""AI-OS Policy Engine - Permission and access control."""
import json
from datetime import datetime, timezone
from pathlib import Path


class PolicyViolation(Exception):
    """Raised when a policy check fails."""


class PolicyEngine:
    PUBLIC = 0
    INTERNAL = 1
    RESTRICTED = 2
    OPERATOR_ONLY = 3

    LEVEL_NAMES = {0: "PUBLIC", 1: "INTERNAL", 2: "RESTRICTED", 3: "OPERATOR_ONLY"}

    # Action -> minimum permission level required
    ACTION_POLICY = {
        "read_status": PUBLIC,
        "list_systems": PUBLIC,
        "read_docs": PUBLIC,
        "write_state": INTERNAL,
        "start_engine": INTERNAL,
        "stop_engine": RESTRICTED,
        "modify_policy": OPERATOR_ONLY,
        "shutdown": OPERATOR_ONLY,
        "identity_unlock": OPERATOR_ONLY,
        "security_override": OPERATOR_ONLY,
        "install_module": RESTRICTED,
        "run_diagnostic": INTERNAL,
        "legal_audit": INTERNAL,
        "evolution_trigger": RESTRICTED,
        "bridge_access": RESTRICTED,
        "sandbox_escape": OPERATOR_ONLY,
        "network_send": INTERNAL,
        "hardware_write": RESTRICTED,
        "hardware_read": INTERNAL,
        "process_kill": RESTRICTED,
    }

    _LOG_ROTATE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(self):
        self._custom_policies = {}
        self._audit_log = []
        self._log_file: Path = None

    def set_log_file(self, path: str) -> None:
        """Configure file-based policy audit logging.

        Replays the last 500 entries from an existing log on startup.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = p
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
                for line in lines[-500:]:
                    line = line.strip()
                    if line:
                        try:
                            self._audit_log.append(json.loads(line))
                        except Exception:
                            pass
            except Exception:
                pass

    def _get_identity_level(self, identity: dict) -> int:
        role = identity.get("role", "public")
        level_map = {
            "public": self.PUBLIC,
            "internal": self.INTERNAL,
            "restricted": self.RESTRICTED,
            "operator": self.OPERATOR_ONLY,
        }
        return level_map.get(role, self.PUBLIC)

    def check_permission(self, action: str, level: int, identity: dict) -> bool:
        required = self._custom_policies.get(
            action, self.ACTION_POLICY.get(action, self.OPERATOR_ONLY)
        )
        identity_level = self._get_identity_level(identity)
        # Also respect the explicitly passed level
        effective_level = max(level, identity_level)
        return effective_level >= required

    def enforce(self, action: str, identity: dict) -> None:
        identity_level = self._get_identity_level(identity)
        allowed = self.check_permission(action, identity_level, identity)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "identity": identity.get("name", "unknown"),
            "level": self.LEVEL_NAMES.get(identity_level, "UNKNOWN"),
            "allowed": allowed,
        }
        self._audit_log.append(event)
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]
        # Append to JSONL file if configured
        if self._log_file is not None:
            try:
                # Single-generation rotation.
                # TODO: upgrade to logging.handlers.RotatingFileHandler for multi-gen rotation.
                if (self._log_file.exists()
                        and self._log_file.stat().st_size > self._LOG_ROTATE_BYTES):
                    self._log_file.replace(self._log_file.with_suffix(".1.jsonl"))
                with open(self._log_file, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(event) + "\n")
            except Exception:
                pass
        if not allowed:
            required = self._custom_policies.get(
                action, self.ACTION_POLICY.get(action, self.OPERATOR_ONLY)
            )
            raise PolicyViolation(
                f"Action '{action}' requires level "
                f"'{self.LEVEL_NAMES.get(required, 'UNKNOWN')}', "
                f"but identity '{identity.get('name', 'unknown')}' has level "
                f"'{self.LEVEL_NAMES.get(identity_level, 'UNKNOWN')}'."
            )

    def set_policy(self, action: str, level: int) -> None:
        self._custom_policies[action] = level

    def get_audit_log(self, limit: int = 50) -> list:
        return list(self._audit_log[-limit:])

    def status(self) -> dict:
        return {
            "component": "PolicyEngine",
            "defined_actions": len(self.ACTION_POLICY) + len(self._custom_policies),
            "audit_entries": len(self._audit_log),
            "healthy": True,
        }
