"""AI-OS State Registry - Thread-safe in-memory state store."""
import threading
import time
from datetime import datetime, timezone


class StateRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._store = {}
                cls._instance._store_lock = threading.RLock()
        return cls._instance

    def set(self, key: str, value, namespace: str = "default") -> None:
        with self._store_lock:
            ns = self._store.setdefault(namespace, {})
            ns[key] = {
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_at": time.time(),
            }

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
            import copy
            return copy.deepcopy(self._store)

    def clear_namespace(self, namespace: str) -> None:
        with self._store_lock:
            if namespace in self._store:
                self._store[namespace] = {}

    def status(self) -> dict:
        with self._store_lock:
            total_keys = sum(len(v) for v in self._store.values())
            return {
                "component": "StateRegistry",
                "namespaces": len(self._store),
                "total_keys": total_keys,
                "healthy": True,
            }
