"""AI-OS Policy Engine - Permission and access control."""
from datetime import datetime, timezone


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

    def __init__(self):
        self._custom_policies = {}
        self._audit_log = []

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
