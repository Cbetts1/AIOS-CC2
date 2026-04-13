"""AI-OS Repair Engine - Auto-diagnoses and repairs faults."""
import time
from datetime import datetime, timezone


class RepairEngine:
    FAULT_INDICATORS = ["error", "fault", "failed", "crash", "timeout"]

    def __init__(self, state_registry=None):
        self._state = state_registry
        self._tick_count = 0
        self._repairs_done = []
        self._last_scan_time = None
        self._last_tick = None
        # Optional callbacks: component_name -> callable() for restart
        self._restart_callbacks: dict = {}
        # Escalation log for persistent unresolved faults
        self._escalations: list = []

    def register_restart_callback(self, component: str, callback) -> None:
        """Register a zero-argument callable that restarts the named component."""
        self._restart_callbacks[component] = callback

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        if self._tick_count % 5 == 0:
            self._auto_scan()

    def _auto_scan(self) -> None:
        self._last_scan_time = time.time()
        if not self._state:
            return
        for ns in self._state.list_namespaces():
            entries = self._state.list(namespace=ns)
            for key, entry in entries.items():
                val = str(entry.get("value", "")).lower()
                for indicator in self.FAULT_INDICATORS:
                    if indicator in val:
                        self.repair(f"{ns}:{key}")
                        break

    def repair(self, component: str) -> dict:
        diag = self.diagnose(component)
        action = "no_action"
        if diag["fault_detected"]:
            # Try restart callback first; fall back to state_reset
            cb = self._restart_callbacks.get(component)
            if cb is not None:
                try:
                    cb()
                    action = "restart_engine"
                except Exception:
                    action = "state_reset"
            else:
                action = "state_reset"

            if action == "state_reset" and self._state:
                namespace, _, key = component.partition(":")
                self._state.set(key, {"status": "repaired", "repair_time": time.time()},
                                namespace=namespace)

        result = {
            "component": component,
            "repaired_at": datetime.now(timezone.utc).isoformat(),
            "diagnosis": diag,
            "action": action,
            "success": True,
        }
        self._repairs_done.append(result)
        if len(self._repairs_done) > 100:
            self._repairs_done = self._repairs_done[-50:]
        return result

    def escalate_to_operator(self, component: str, reason: str) -> dict:
        """Record a persistent fault that could not be auto-repaired."""
        entry = {
            "component": component,
            "reason": reason,
            "escalated_at": datetime.now(timezone.utc).isoformat(),
            "resolved": False,
        }
        self._escalations.append(entry)
        if len(self._escalations) > 50:
            self._escalations = self._escalations[-25:]
        if self._state:
            self._state.set(f"escalation:{component}", entry, namespace="repair")
        return entry

    def get_escalations(self) -> list:
        return list(self._escalations)

    def diagnose(self, component: str) -> dict:
        fault = False
        if self._state:
            namespace, _, key = component.partition(":")
            val = self._state.get(key, namespace=namespace)
            if val is not None:
                val_str = str(val).lower()
                fault = any(ind in val_str for ind in self.FAULT_INDICATORS)
        return {
            "component": component,
            "fault_detected": fault,
            "diagnosed_at": datetime.now(timezone.utc).isoformat(),
            "indicators_checked": self.FAULT_INDICATORS,
        }

    def get_repair_history(self) -> list:
        return list(self._repairs_done[-20:])

    def status(self) -> dict:
        return {
            "component": "RepairEngine",
            "tick_count": self._tick_count,
            "repairs_done": len(self._repairs_done),
            "escalations": len(self._escalations),
            "last_scan": self._last_scan_time,
            "last_tick": self._last_tick,
            "healthy": True,
        }
