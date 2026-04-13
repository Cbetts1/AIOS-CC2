"""AI-OS Virtual Storage - Simulates a 1GB virtual disk with optional persistence."""
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


class VirtualStorage:
    CAPACITY_GB = 1
    CAPACITY_BYTES = CAPACITY_GB * 1024 * 1024 * 1024

    def __init__(self, persist_dir: str = None):
        self._store = {}     # path -> bytes
        self._metadata = {}  # path -> {created, modified, size}
        self._used_bytes = 0
        self._read_count = 0
        self._write_count = 0
        self._init_time = time.time()
        self._lock = threading.RLock()
        self._persist_dir = Path(persist_dir) if persist_dir else None
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    def _safe_name(self, path: str) -> str:
        """Convert a virtual path to a safe filename within persist_dir."""
        # Strip the virtual path to just the basename-like component and replace
        # separators to avoid any directory traversal into the real filesystem.
        safe = path.replace("\\", "/").replace("/", "__").replace("..", "__")
        safe = safe.lstrip("_").lstrip(".") or "_root_"
        return safe

    def _load_from_disk(self) -> None:
        """Load all previously persisted virtual files from disk."""
        if not self._persist_dir:
            return
        meta_path = self._persist_dir / "_meta.json"
        try:
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                for vpath, meta in saved.items():
                    fname = self._safe_name(vpath)
                    fpath = self._persist_dir / fname
                    if fpath.exists():
                        try:
                            data = fpath.read_bytes()
                            self._store[vpath] = data
                            self._metadata[vpath] = meta
                            self._used_bytes += len(data)
                        except Exception:
                            pass
        except Exception:
            pass

    def _persist(self, path: str) -> None:
        """Write a single virtual file and the metadata index to disk."""
        if not self._persist_dir:
            return
        try:
            fname = self._safe_name(path)
            fpath = self._persist_dir / fname
            data = self._store.get(path, b"")
            tmp = fpath.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(fpath)
            # Rewrite metadata index atomically
            meta_path = self._persist_dir / "_meta.json"
            tmp_meta = meta_path.with_suffix(".tmp")
            with open(tmp_meta, "w", encoding="utf-8") as fh:
                json.dump(self._metadata, fh, indent=2)
            tmp_meta.replace(meta_path)
        except Exception:
            pass

    def _persist_delete(self, path: str) -> None:
        """Remove a persisted file from disk."""
        if not self._persist_dir:
            return
        try:
            fname = self._safe_name(path)
            fpath = self._persist_dir / fname
            if fpath.exists():
                fpath.unlink(missing_ok=True)
            # Rewrite metadata index
            meta_path = self._persist_dir / "_meta.json"
            tmp_meta = meta_path.with_suffix(".tmp")
            with open(tmp_meta, "w", encoding="utf-8") as fh:
                json.dump(self._metadata, fh, indent=2)
            tmp_meta.replace(meta_path)
        except Exception:
            pass

    def write(self, path: str, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        with self._lock:
            old_size = len(self._store.get(path, b""))
            new_size = len(data)
            delta = new_size - old_size
            if self._used_bytes + delta > self.CAPACITY_BYTES:
                raise IOError(f"Virtual disk full: cannot write {new_size} bytes to '{path}'")
            self._store[path] = bytes(data)
            self._used_bytes += delta
            now = datetime.now(timezone.utc).isoformat()
            if path not in self._metadata:
                self._metadata[path] = {"created": now, "modified": now, "size": new_size}
            else:
                self._metadata[path]["modified"] = now
                self._metadata[path]["size"] = new_size
            self._write_count += 1
            self._persist(path)

    def read(self, path: str) -> bytes:
        with self._lock:
            if path not in self._store:
                raise FileNotFoundError(f"Virtual file not found: '{path}'")
            self._read_count += 1
            return self._store[path]

    def delete(self, path: str) -> bool:
        with self._lock:
            if path not in self._store:
                return False
            self._used_bytes -= len(self._store[path])
            del self._store[path]
            if path in self._metadata:
                del self._metadata[path]
            self._persist_delete(path)
            return True

    def list(self, prefix: str = "") -> list:
        with self._lock:
            return [p for p in self._store.keys() if p.startswith(prefix)]

    def exists(self, path: str) -> bool:
        with self._lock:
            return path in self._store

    def size(self, path: str) -> int:
        with self._lock:
            return len(self._store.get(path, b""))

    def get_metadata(self, path: str) -> dict:
        with self._lock:
            return dict(self._metadata.get(path, {}))

    def used_bytes(self) -> int:
        with self._lock:
            return self._used_bytes

    def free_bytes(self) -> int:
        with self._lock:
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

    def save_to_file(self, path: str) -> bool:
        """Atomically persist the virtual filesystem to a JSON file.

        File contents are base64-encoded so arbitrary byte payloads survive.
        Returns True on success, False on failure.
        """
        import base64
        import json
        from pathlib import Path
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            serialized = {
                fp: base64.b64encode(data).decode("ascii")
                for fp, data in self._store.items()
            }
            payload = {"store": serialized, "metadata": self._metadata}
            tmp = p.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, default=str)
            tmp.replace(p)
            return True
        except Exception:
            try:
                tmp = p.with_suffix(".tmp")
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            return False

    def load_from_file(self, path: str) -> bool:
        """Load virtual filesystem from a JSON file.  Returns True on success."""
        import base64
        import json
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return False
        try:
            with open(p, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            store_raw = payload.get("store", {})
            metadata = payload.get("metadata", {})
            store: dict = {}
            used = 0
            for fp, b64 in store_raw.items():
                data = base64.b64decode(b64)
                store[fp] = data
                used += len(data)
            self._store = store
            self._metadata = metadata
            self._used_bytes = used
            return True
        except Exception:
            return False
