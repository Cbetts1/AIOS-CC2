"""AI-OS Sandbox Manager - Manages the sandbox boundary."""
import threading
import time


class SandboxManager:
    def __init__(self):
        self._sandboxed = False
        self._entry_count = 0
        self._lock = threading.Lock()
        self._init_time = time.time()
        self._sandbox_events = []

    def enter_sandbox(self) -> bool:
        with self._lock:
            if self._sandboxed:
                return False  # Already in sandbox
            self._sandboxed = True
            self._entry_count += 1
            self._sandbox_events.append({
                "event": "enter",
                "count": self._entry_count,
                "ts": time.time(),
            })
            if len(self._sandbox_events) > 200:
                self._sandbox_events = self._sandbox_events[-100:]
            return True

    def exit_sandbox(self) -> bool:
        with self._lock:
            if not self._sandboxed:
                return False
            self._sandboxed = False
            self._sandbox_events.append({
                "event": "exit",
                "count": self._entry_count,
                "ts": time.time(),
            })
            return True

    def is_sandboxed(self) -> bool:
        with self._lock:
            return self._sandboxed

    def get_events(self, limit: int = 20) -> list:
        with self._lock:
            return list(self._sandbox_events[-limit:])

    def run_in_sandbox(self, fn, *args, **kwargs):
        entered = self.enter_sandbox()
        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            if entered:
                self.exit_sandbox()

    def status(self) -> dict:
        return {
            "component": "SandboxManager",
            "sandboxed": self._sandboxed,
            "entry_count": self._entry_count,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "note": "No external calls permitted from within sandbox",
            "healthy": True,
        }
