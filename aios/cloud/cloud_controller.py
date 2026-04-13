"""AI-OS Cloud Controller — master orchestrator for the cloud layer.

Responsibilities:
- Boot / stop the cloud service.
- Spawn and stop CloudNode workers.
- Delegate task execution to CloudCompute.
- Expose status and event log to the Command Center.
- Tick on every main-loop iteration (lightweight).
"""
import threading
import time
import uuid
from datetime import datetime

from aios.cloud.cloud_network import CloudNetwork
from aios.cloud.cloud_node import CloudNode
from aios.cloud.cloud_compute import CloudCompute
from aios.cloud.cloud_storage import CloudStorage


class CloudController:
    """Orchestrates the entire cloud layer."""

    def __init__(self, state_registry=None, mesh=None, vcpu=None):
        self._state = state_registry
        self._mesh = mesh
        self._vcpu = vcpu

        self._network = CloudNetwork()
        self._storage = CloudStorage()
        self._compute = CloudCompute(
            cloud_network=self._network,
            state_registry=state_registry,
            vcpu=vcpu,
        )

        self._nodes: dict = {}    # node_id -> CloudNode
        self._lock = threading.Lock()
        self._running = False
        self._boot_time: float = None
        self._tick_count = 0
        self._event_log: list = []

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def boot(self) -> dict:
        self._boot_time = time.time()
        self._running = True
        self._log("CloudController ONLINE")
        if self._state:
            self._state.set("cloud_status", "ONLINE", namespace="cloud")
            self._state.set("cloud_boot_time", self._boot_time, namespace="cloud")
        return {
            "status": "ONLINE",
            "boot_time": datetime.utcnow().isoformat() + "Z",
        }

    def stop(self) -> dict:
        self._running = False
        with self._lock:
            for node in list(self._nodes.values()):
                try:
                    node.stop()
                except Exception:
                    pass
            self._nodes.clear()
        self._log("CloudController STOPPED")
        if self._state:
            self._state.set("cloud_status", "OFFLINE", namespace="cloud")
        return {"status": "OFFLINE"}

    # ── Node management ──────────────────────────────────────────────────────

    def spawn_node(self, node_id: str = None) -> dict:
        """Create, bind, and register a new CloudNode.  Returns status dict."""
        nid = node_id or f"node-{uuid.uuid4().hex[:8]}"
        with self._lock:
            if nid in self._nodes:
                return {"error": f"Node '{nid}' already exists"}

        try:
            port = self._network.allocate_port()
        except RuntimeError as exc:
            return {"error": str(exc)}

        node = CloudNode(node_id=nid, port=port)
        node.attach(vcpu=self._vcpu, state_registry=self._state)

        if not node.start(port):
            self._network.release_port(port)
            return {"error": f"Failed to start node '{nid}' on port {port}"}

        with self._lock:
            self._nodes[nid] = node

        self._network.register_node(nid, port)
        self._storage.set(nid, {
            "port": port,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }, namespace="nodes")

        if self._state:
            self._state.set(f"node:{nid}",
                            {"port": port, "status": "running"},
                            namespace="cloud")

        self._log(f"Spawned node {nid} on port {port}")
        return {"node_id": nid, "port": port, "status": "running"}

    def stop_node(self, node_id: str) -> dict:
        """Stop and deregister a node by ID."""
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                return {"error": f"Node '{node_id}' not found"}
            node.stop()
            port = node.port
            del self._nodes[node_id]

        self._network.unregister_node(node_id)
        if port:
            self._network.release_port(port)

        self._log(f"Stopped node {node_id}")
        return {"node_id": node_id, "status": "stopped"}

    def list_nodes(self) -> list:
        with self._lock:
            return [n.status() for n in self._nodes.values()]

    # ── Task execution ───────────────────────────────────────────────────────

    def exec_task(self, task_type: str, payload=None,
                  target_node: str = None) -> dict:
        """Execute a task, auto-spawning a node if the pool is empty."""
        if not self._nodes:
            spawn_result = self.spawn_node()
            if "error" in spawn_result:
                return {"error": "No nodes available and could not auto-spawn one",
                        "detail": spawn_result["error"]}
        return self._compute.submit_task(task_type, payload or {}, target_node)

    # ── Heartbeat ────────────────────────────────────────────────────────────

    def heartbeat(self) -> dict:
        """Ping all registered nodes and summarise results."""
        msg = {"type": "heartbeat", "ts": datetime.utcnow().isoformat() + "Z"}
        results = self._network.broadcast(msg)
        alive = sum(1 for r in results.values() if "error" not in r)
        total = len(results)
        self._log(f"HB: {alive}/{total} nodes alive")
        return {"alive": alive, "total": total, "results": results}

    # ── Main-loop tick ───────────────────────────────────────────────────────

    def tick(self) -> None:
        """Lightweight tick called every second from the endless loop."""
        if not self._running:
            return
        self._tick_count += 1
        if self._state:
            self._state.set("cloud_nodes", len(self._nodes), namespace="cloud")
            self._state.set("cloud_tick", self._tick_count, namespace="cloud")

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        entry = {"msg": msg, "ts": datetime.utcnow().isoformat() + "Z"}
        self._event_log.append(entry)
        if len(self._event_log) > 300:
            self._event_log = self._event_log[-150:]

    def get_event_log(self, limit: int = 30) -> list:
        return list(self._event_log[-limit:])

    # ── Status ───────────────────────────────────────────────────────────────

    def uptime(self) -> float:
        if not self._boot_time:
            return 0.0
        return round(time.time() - self._boot_time, 1)

    def status(self) -> dict:
        return {
            "component": "CloudController",
            "running": self._running,
            "node_count": len(self._nodes),
            "tick_count": self._tick_count,
            "uptime_seconds": self.uptime(),
            "network": self._network.status(),
            "storage": self._storage.status(),
            "compute": self._compute.status(),
            "healthy": self._running,
        }
