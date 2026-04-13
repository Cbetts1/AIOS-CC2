"""AI-OS Repair Engine - Auto-diagnoses and repairs faults."""
import time
from datetime import datetime


class RepairEngine:
    FAULT_INDICATORS = ["error", "fault", "failed", "crash", "timeout"]

    def __init__(self, state_registry=None):
        self._state = state_registry
        self._tick_count = 0
        self._repairs_done = []
        self._last_scan_time = None
        self._last_tick = None

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
        result = {
            "component": component,
            "repaired_at": datetime.utcnow().isoformat() + "Z",
            "diagnosis": diag,
            "action": "state_reset" if diag["fault_detected"] else "no_action",
            "success": True,
        }
        if diag["fault_detected"] and self._state:
            ns, _, key = component.partition(":")
            self._state.set(key, {"status": "repaired", "repair_time": time.time()}, namespace=ns)
        self._repairs_done.append(result)
        if len(self._repairs_done) > 100:
            self._repairs_done = self._repairs_done[-50:]
        return result

    def diagnose(self, component: str) -> dict:
        fault = False
        if self._state:
            ns, _, key = component.partition(":")
            val = self._state.get(key, namespace=ns)
            if val is not None:
                val_str = str(val).lower()
                fault = any(ind in val_str for ind in self.FAULT_INDICATORS)
        return {
            "component": component,
            "fault_detected": fault,
            "diagnosed_at": datetime.utcnow().isoformat() + "Z",
            "indicators_checked": self.FAULT_INDICATORS,
        }

    def get_repair_history(self) -> list:
        return list(self._repairs_done[-20:])

    def status(self) -> dict:
        return {
            "component": "RepairEngine",
            "tick_count": self._tick_count,
            "repairs_done": len(self._repairs_done),
            "last_scan": self._last_scan_time,
            "last_tick": self._last_tick,
            "healthy": True,
        }
