"""AI-OS Proc Writers - Writes system state to /proc-like virtual files."""
import time
from datetime import datetime


class ProcWriters:
    PROC_PREFIX = "/proc/aios/"

    def __init__(self, vstorage=None):
        self._storage = vstorage
        self._tick_count = 0
        self._last_tick = None
        self._write_count = 0
        self._proc_cache = {}

    def set_storage(self, vstorage) -> None:
        self._storage = vstorage

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        self._write_system_procs()

    def _write_system_procs(self) -> None:
        self.write_proc("uptime", str(round(time.time(), 2)))
        self.write_proc("tick", str(self._tick_count))
        self.write_proc("timestamp", datetime.utcnow().isoformat() + "Z")
        self.write_proc("status", "ONLINE")

    def write_proc(self, name: str, data) -> str:
        path = f"{self.PROC_PREFIX}{name}"
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        self._proc_cache[name] = {"data": data, "written_at": time.time()}
        if self._storage:
            try:
                self._storage.write(path, data)
            except Exception:
                pass
        self._write_count += 1
        return path

    def read_proc(self, name: str) -> str:
        path = f"{self.PROC_PREFIX}{name}"
        cached = self._proc_cache.get(name)
        if cached:
            return cached["data"].decode("utf-8", errors="replace")
        if self._storage:
            try:
                return self._storage.read(path).decode("utf-8", errors="replace")
            except FileNotFoundError:
                return ""
        return ""

    def list_procs(self) -> list:
        return list(self._proc_cache.keys())

    def status(self) -> dict:
        return {
            "component": "ProcWriters",
            "tick_count": self._tick_count,
            "write_count": self._write_count,
            "proc_count": len(self._proc_cache),
            "proc_names": self.list_procs(),
            "last_tick": self._last_tick,
            "healthy": True,
        }
