"""AI-OS Cloud Storage — persistent file-based key-value store.

All data is written to ~/.aios/cloud_storage/ as JSON files, one file per
namespace.  This gives true persistence across process restarts while using
only the Python standard library.
"""
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path


class CloudStorage:
    """File-backed, namespace-scoped key-value store."""

    DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".aios", "cloud_storage")

    def __init__(self, storage_dir: str = None):
        self._dir = Path(storage_dir or self.DEFAULT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: dict = {}          # namespace -> {key -> {value, updated_at}}
        self._write_count = 0
        self._read_count = 0
        self._init_time = time.time()
        self._load_all()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _namespace_path(self, namespace: str) -> Path:
        safe = namespace.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self._dir / f"{safe}.json"

    def _load_all(self) -> None:
        """Load every *.json file from the storage directory into the cache."""
        with self._lock:
            for f in self._dir.glob("*.json"):
                ns = f.stem
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        if isinstance(data, dict):
                            self._cache[ns] = data
                except Exception:
                    self._cache[ns] = {}

    def _flush(self, namespace: str) -> None:
        """Write a single namespace to disk atomically (write-then-rename)."""
        path = self._namespace_path(namespace)
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._cache.get(namespace, {}), fh,
                          indent=2, default=str)
            tmp.replace(path)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    # ── Public API ───────────────────────────────────────────────────────────

    def set(self, key: str, value, namespace: str = "default") -> None:
        with self._lock:
            ns = self._cache.setdefault(namespace, {})
            ns[key] = {
                "value": value,
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
            self._write_count += 1
            self._flush(namespace)

    def get(self, key: str, namespace: str = "default", default=None):
        with self._lock:
            self._read_count += 1
            entry = self._cache.get(namespace, {}).get(key)
            return default if entry is None else entry["value"]

    def delete(self, key: str, namespace: str = "default") -> bool:
        with self._lock:
            ns = self._cache.get(namespace, {})
            if key in ns:
                del ns[key]
                self._flush(namespace)
                return True
            return False

    def list(self, namespace: str = "default") -> dict:
        with self._lock:
            return {k: v["value"]
                    for k, v in self._cache.get(namespace, {}).items()}

    def list_namespaces(self) -> list:
        with self._lock:
            return list(self._cache.keys())

    def clear_namespace(self, namespace: str) -> None:
        with self._lock:
            self._cache[namespace] = {}
            self._flush(namespace)

    def status(self) -> dict:
        with self._lock:
            total_keys = sum(len(v) for v in self._cache.values())
        return {
            "component": "CloudStorage",
            "storage_dir": str(self._dir),
            "namespaces": len(self._cache),
            "total_keys": total_keys,
            "write_count": self._write_count,
            "read_count": self._read_count,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
