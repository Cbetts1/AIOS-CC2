"""AI-OS Virtual Storage - Simulates a 1GB virtual disk."""
import time
from datetime import datetime


class VirtualStorage:
    CAPACITY_GB = 1
    CAPACITY_BYTES = CAPACITY_GB * 1024 * 1024 * 1024

    def __init__(self):
        self._store = {}     # path -> bytes
        self._metadata = {}  # path -> {created, modified, size}
        self._used_bytes = 0
        self._read_count = 0
        self._write_count = 0
        self._init_time = time.time()

    def write(self, path: str, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        old_size = len(self._store.get(path, b""))
        new_size = len(data)
        delta = new_size - old_size
        if self._used_bytes + delta > self.CAPACITY_BYTES:
            raise IOError(f"Virtual disk full: cannot write {new_size} bytes to '{path}'")
        self._store[path] = bytes(data)
        self._used_bytes += delta
        now = datetime.utcnow().isoformat() + "Z"
        if path not in self._metadata:
            self._metadata[path] = {"created": now, "modified": now, "size": new_size}
        else:
            self._metadata[path]["modified"] = now
            self._metadata[path]["size"] = new_size
        self._write_count += 1

    def read(self, path: str) -> bytes:
        if path not in self._store:
            raise FileNotFoundError(f"Virtual file not found: '{path}'")
        self._read_count += 1
        return self._store[path]

    def delete(self, path: str) -> bool:
        if path not in self._store:
            return False
        self._used_bytes -= len(self._store[path])
        del self._store[path]
        if path in self._metadata:
            del self._metadata[path]
        return True

    def list(self, prefix: str = "") -> list:
        return [p for p in self._store.keys() if p.startswith(prefix)]

    def exists(self, path: str) -> bool:
        return path in self._store

    def size(self, path: str) -> int:
        return len(self._store.get(path, b""))

    def get_metadata(self, path: str) -> dict:
        return dict(self._metadata.get(path, {}))

    def used_bytes(self) -> int:
        return self._used_bytes

    def free_bytes(self) -> int:
        return self.CAPACITY_BYTES - self._used_bytes

    def status(self) -> dict:
        return {
            "component": "VirtualStorage",
            "capacity_gb": self.CAPACITY_GB,
            "used_bytes": self._used_bytes,
            "free_bytes": self.free_bytes(),
            "used_percent": round(self._used_bytes / self.CAPACITY_BYTES * 100, 4),
            "file_count": len(self._store),
            "reads": self._read_count,
            "writes": self._write_count,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
