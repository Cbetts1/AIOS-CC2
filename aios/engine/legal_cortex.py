"""AI-OS Legal Cortex - Compliance and legal enforcement."""
import time
from datetime import datetime


class LegalViolation(Exception):
    """Raised when a legal compliance check fails."""


class LegalCortex:
    # Actions that are always blocked as non-compliant
    BLOCKED_ACTIONS = {
        "external_network_call",
        "write_host_filesystem",
        "exec_arbitrary_code",
        "access_host_credentials",
        "modify_host_environment",
        "bypass_sandbox",
        "disable_identity_lock",
    }

    # Actions that require audit before execution
    AUDIT_REQUIRED = {
        "shutdown",
        "evolution_trigger",
        "security_override",
        "identity_unlock",
        "modify_policy",
        "install_module",
        "sandbox_escape",
    }

    def __init__(self, state_registry=None):
        self._state = state_registry
        self._tick_count = 0
        self._last_tick = None
        self._audit_log = []
        self._violations = []
        self._compliant_actions = set()

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()

    def enforce(self, action: str) -> None:
        if action in self.BLOCKED_ACTIONS:
            event = {
                "action": action,
                "result": "BLOCKED",
                "reason": "Non-compliant action - permanently blocked by LegalCortex",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            self._violations.append(event)
            if self._state:
                self._state.set(f"violation:{action}", event, namespace="legal")
            raise LegalViolation(f"Action '{action}' is blocked: non-compliant with AI-OS legal policy.")
        self._compliant_actions.add(action)

    def audit(self, action: str) -> dict:
        requires_audit = action in self.AUDIT_REQUIRED
        blocked = action in self.BLOCKED_ACTIONS
        record = {
            "action": action,
            "audit_required": requires_audit,
            "blocked": blocked,
            "compliant": not blocked,
            "audited_at": datetime.utcnow().isoformat() + "Z",
            "tick": self._tick_count,
        }
        self._audit_log.append(record)
        if len(self._audit_log) > 500:
            self._audit_log = self._audit_log[-250:]
        if self._state:
            self._state.set(f"audit:{action}", record, namespace="legal")
        return record

    def is_compliant(self, action: str) -> bool:
        return action not in self.BLOCKED_ACTIONS

    def get_audit_log(self, limit: int = 50) -> list:
        return list(self._audit_log[-limit:])

    def get_violations(self) -> list:
        return list(self._violations[-50:])

    def status(self) -> dict:
        return {
            "component": "LegalCortex",
            "tick_count": self._tick_count,
            "audit_entries": len(self._audit_log),
            "violations": len(self._violations),
            "blocked_action_count": len(self.BLOCKED_ACTIONS),
            "last_tick": self._last_tick,
            "healthy": True,
        }
