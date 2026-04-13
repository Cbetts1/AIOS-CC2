"""AI-OS Cloud API — clean internal interface for cloud operations.

Callable by:
- CommandCenter (via attached _cloud attribute)
- AuraEngine sub-engines
- Any other AI-OS subsystem that imports this module

The API is intentionally thin: it validates that a controller is attached,
records call counts, and delegates everything to CloudController.
"""
import time
from datetime import datetime


class CloudAPI:
    """Internal API surface for the cloud layer."""

    def __init__(self, cloud_controller=None):
        self._controller = cloud_controller
        self._call_count = 0
        self._init_time = time.time()

    # ── Attachment ───────────────────────────────────────────────────────────

    def set_controller(self, controller) -> None:
        self._controller = controller

    def _check(self) -> bool:
        """Return True if a controller is attached."""
        return self._controller is not None

    def _count(self) -> None:
        self._call_count += 1

    # ── Node management ──────────────────────────────────────────────────────

    def create_node(self, node_id: str = None) -> dict:
        """Spawn a new cloud node.  Returns {node_id, port, status}."""
        self._count()
        if not self._check():
            return {"error": "CloudController not attached"}
        return self._controller.spawn_node(node_id)

    def list_nodes(self) -> dict:
        """Return all active nodes with their status."""
        self._count()
        if not self._check():
            return {"error": "CloudController not attached", "nodes": []}
        nodes = self._controller.list_nodes()
        return {
            "nodes": nodes,
            "count": len(nodes),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # ── Task dispatch ────────────────────────────────────────────────────────

    def send_task(self, task_type: str, payload=None,
                  target_node: str = None) -> dict:
        """Submit a task to the cloud compute engine."""
        self._count()
        if not self._check():
            return {"error": "CloudController not attached"}
        return self._controller.exec_task(task_type, payload, target_node)

    # ── Cloud lifecycle ──────────────────────────────────────────────────────

    def start_cloud(self) -> dict:
        self._count()
        if not self._check():
            return {"error": "CloudController not attached"}
        return self._controller.boot()

    def stop_cloud(self) -> dict:
        self._count()
        if not self._check():
            return {"error": "CloudController not attached"}
        return self._controller.stop()

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        self._count()
        if not self._check():
            return {"error": "CloudController not attached", "status": "OFFLINE"}
        return self._controller.status()

    def heartbeat(self) -> dict:
        self._count()
        if not self._check():
            return {"error": "CloudController not attached"}
        return self._controller.heartbeat()

    def get_event_log(self, limit: int = 20) -> list:
        self._count()
        if not self._check():
            return []
        return self._controller.get_event_log(limit)

    # ── Self-status ──────────────────────────────────────────────────────────

    def status(self) -> dict:
        ctrl = self._controller.status() if self._controller else {"status": "OFFLINE"}
        return {
            "component": "CloudAPI",
            "api_calls": self._call_count,
            "controller_attached": self._controller is not None,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "controller_status": ctrl,
            "healthy": self._controller is not None,
        }
