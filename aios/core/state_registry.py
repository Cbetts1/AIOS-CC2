"""AI-OS State Registry - Thread-safe in-memory state store with optional disk persistence."""
import copy
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


class StateRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._store = {}
                cls._instance._store_lock = threading.RLock()
                cls._instance._persist_path = None
        return cls._instance

    def set_persist_path(self, path: str) -> None:
        """Configure a JSON file for snapshot persistence and load any existing data."""
        with self._store_lock:
            self._persist_path = Path(path)
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_snapshot()

    def _load_snapshot(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            if isinstance(saved, dict):
                for ns, entries in saved.items():
                    if isinstance(entries, dict):
                        self._store.setdefault(ns, {}).update(entries)
        except Exception:
            pass

    def _flush(self) -> None:
        if not self._persist_path:
            return
        try:
            tmp = self._persist_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._store, fh, default=str)
            tmp.replace(self._persist_path)
        except Exception:
            pass

    def set(self, key: str, value, namespace: str = "default") -> None:
        with self._store_lock:
            ns = self._store.setdefault(namespace, {})
            ns[key] = {
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_at": time.time(),
            }
            self._flush()

    def get(self, key: str, namespace: str = "default", default=None):
        with self._store_lock:
            ns = self._store.get(namespace, {})
            entry = ns.get(key)
            if entry is None:
                return default
            return entry["value"]

    def delete(self, key: str, namespace: str = "default") -> bool:
        with self._store_lock:
            ns = self._store.get(namespace, {})
            if key in ns:
                del ns[key]
                self._flush()
                return True
            return False

    def list(self, namespace: str = "default") -> dict:
        with self._store_lock:
            return dict(self._store.get(namespace, {}))

    def list_namespaces(self) -> list:
        with self._store_lock:
            return list(self._store.keys())

    def dump(self) -> dict:
        with self._store_lock:
            return copy.deepcopy(self._store)

    def clear_namespace(self, namespace: str) -> None:
        with self._store_lock:
            if namespace in self._store:
                self._store[namespace] = {}
                self._flush()

    def flush_to_file(self, path: str) -> bool:
        """Atomically persist the entire registry to a JSON file.

        Returns True on success, False on failure.
        """
        import copy
        import json
        from pathlib import Path
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with self._store_lock:
                data = copy.deepcopy(self._store)
            tmp = p.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, default=str, indent=2)
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
        """Load registry state from a JSON file.  Returns True on success."""
        import json
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return False
        try:
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                with self._store_lock:
                    self._store = data
                return True
            return False
        except Exception:
            return False

    def status(self) -> dict:
        with self._store_lock:
            total_keys = sum(len(v) for v in self._store.values())
            return {
                "component": "StateRegistry",
                "namespaces": len(self._store),
                "total_keys": total_keys,
                "persist_path": str(self._persist_path) if self._persist_path else None,
                "healthy": True,
            }
