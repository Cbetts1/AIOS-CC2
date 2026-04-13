"""AI-OS Sandbox - Enforces no external calls during execution."""
import threading
import time
from datetime import datetime


class SandboxViolation(Exception):
    """Raised when execution is unsafe for the sandbox."""


class Sandbox:
    BLOCKED_MODULE_PREFIXES = (
        "urllib", "http.client", "ftplib", "smtplib", "telnetlib",
        "imaplib", "poplib", "xmlrpc.client", "subprocess",
    )

    def __init__(self):
        self._active = False
        self._lock = threading.Lock()
        self._run_count = 0
        self._blocked_count = 0
        self._execution_log = []
        self._init_time = time.time()

    def is_safe(self, fn) -> bool:
        fn_module = getattr(fn, "__module__", "") or ""
        for prefix in self.BLOCKED_MODULE_PREFIXES:
            if fn_module.startswith(prefix):
                return False
        fn_name = getattr(fn, "__qualname__", getattr(fn, "__name__", ""))
        unsafe_names = {"system", "popen", "exec", "eval", "compile", "execfile"}
        if fn_name.lower() in unsafe_names:
            return False
        return True

    def run(self, fn, *args, **kwargs):
        if not self.is_safe(fn):
            self._blocked_count += 1
            raise SandboxViolation(
                f"Unsafe function blocked by Sandbox: {getattr(fn, '__qualname__', str(fn))}"
            )
        with self._lock:
            self._active = True
        try:
            result = fn(*args, **kwargs)
            self._run_count += 1
            self._execution_log.append({
                "fn": getattr(fn, "__qualname__", str(fn)),
                "status": "ok",
                "ts": datetime.utcnow().isoformat() + "Z",
            })
            return result
        except SandboxViolation:
            raise
        except Exception as exc:
            self._execution_log.append({
                "fn": getattr(fn, "__qualname__", str(fn)),
                "status": f"error:{type(exc).__name__}",
                "ts": datetime.utcnow().isoformat() + "Z",
            })
            raise
        finally:
            with self._lock:
                self._active = False
            if len(self._execution_log) > 500:
                self._execution_log = self._execution_log[-250:]

    def status(self) -> dict:
        return {
            "component": "Sandbox",
            "active": self._active,
            "run_count": self._run_count,
            "blocked_count": self._blocked_count,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
