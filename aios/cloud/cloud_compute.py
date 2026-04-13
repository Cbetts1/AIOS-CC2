"""AI-OS Cloud Compute Engine — task submission and routing.

Responsibilities:
- Accept task submissions from any AI-OS subsystem.
- Select a target node (round-robin or explicit).
- Delegate to CloudNetwork for actual delivery.
- Fall back to in-process execution when no nodes are available.
- Keep a task log visible to the Command Center.
"""
import time
import uuid
from datetime import datetime, timezone


class CloudCompute:
    """Routes and executes tasks across cloud nodes."""

    TASK_TYPES = ("echo", "vcpu_exec", "state_query", "compute", "info")

    def __init__(self, cloud_network=None, state_registry=None, vcpu=None):
        self._network = cloud_network
        self._state = state_registry
        self._vcpu = vcpu
        self._task_log: list = []
        self._task_count = 0
        self._init_time = time.time()

    # ── Attachment ───────────────────────────────────────────────────────────

    def attach(self, cloud_network=None, state_registry=None, vcpu=None) -> None:
        if cloud_network is not None:
            self._network = cloud_network
        if state_registry is not None:
            self._state = state_registry
        if vcpu is not None:
            self._vcpu = vcpu

    # ── Task submission ──────────────────────────────────────────────────────

    def submit_task(self, task_type: str, payload=None,
                    target_node: str = None) -> dict:
        """Submit a task and return the result dict."""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        payload = payload or {}
        self._task_count += 1

        # Build the wire-level message
        msg = {
            "type": "task",
            "data": {
                "task_id": task_id,
                "type": task_type,
                "payload": payload,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        # Also pass instruction at top-level for vcpu_exec convenience
        if task_type == "vcpu_exec" and "instruction" in payload:
            msg["data"]["instruction"] = payload["instruction"]

        result = self._route(msg, task_id, task_type, target_node)

        # Record in task log
        self._task_log.append({
            "task_id": task_id,
            "type": task_type,
            "target_node": target_node,
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": result.get("status", "unknown"),
        })
        if len(self._task_log) > 300:
            self._task_log = self._task_log[-150:]

        if self._state:
            self._state.set("last_task_id", task_id, namespace="cloud")
            self._state.set("task_count", self._task_count, namespace="cloud")

        return result

    def _route(self, msg: dict, task_id: str, task_type: str,
               target_node: str) -> dict:
        """Decide which node gets this task, or run locally."""
        if self._network and self._network.node_count() > 0:
            nodes = self._network.list_nodes()
            if target_node and target_node in {n["id"] for n in nodes}:
                node_id = target_node
            else:
                # Round-robin selection
                node_id = nodes[self._task_count % len(nodes)]["id"]
            result = self._network.send_to_node(node_id, msg)
            result.setdefault("task_id", task_id)
            return result

        # No network nodes — run inline
        return self._execute_local(task_type, msg["data"].get("payload", {}),
                                   msg["data"].get("instruction"), task_id)

    # ── Local (inline) execution fallback ───────────────────────────────────

    def _execute_local(self, task_type: str, payload: dict,
                       instruction, task_id: str) -> dict:
        base = {"task_id": task_id, "node": "local"}
        try:
            if task_type == "echo":
                return {**base, "status": "complete", "result": payload}

            if task_type == "vcpu_exec":
                instr = instruction or payload.get("instruction", {"op": "NOP"})
                if self._vcpu:
                    return {**base, "status": "complete",
                            "result": self._vcpu.execute(instr)}
                return {**base, "status": "error", "error": "No vCPU attached"}

            if task_type == "state_query":
                key = payload.get("key", "")
                ns = payload.get("namespace", "default")
                if self._state:
                    val = self._state.get(key, namespace=ns)
                    return {**base, "status": "complete", "result": val}
                return {**base, "status": "error",
                        "error": "No StateRegistry attached"}

            if task_type == "compute":
                a = float(payload.get("a", 0))
                b = float(payload.get("b", 0))
                op = payload.get("op", "add")
                ops = {
                    "add": a + b, "sub": a - b, "mul": a * b,
                    "div": a / b if b != 0 else 0.0,
                    "mod": a % b if b != 0 else 0.0,
                }
                return {**base, "status": "complete",
                        "result": {"op": op, "result": ops.get(op, 0)}}

            return {**base, "status": "complete",
                    "result": f"local:{task_type}:{payload}"}
        except Exception as exc:
            return {**base, "status": "error", "error": str(exc)}

    # ── Convenience methods ──────────────────────────────────────────────────

    def exec_vcpu(self, instruction: dict, target_node: str = None) -> dict:
        return self.submit_task("vcpu_exec",
                                {"instruction": instruction}, target_node)

    def exec_compute(self, op: str, a, b, target_node: str = None) -> dict:
        return self.submit_task("compute",
                                {"op": op, "a": a, "b": b}, target_node)

    # ── Status ───────────────────────────────────────────────────────────────

    def get_task_log(self, limit: int = 20) -> list:
        return list(self._task_log[-limit:])

    def status(self) -> dict:
        return {
            "component": "CloudCompute",
            "task_count": self._task_count,
            "task_types": list(self.TASK_TYPES),
            "log_entries": len(self._task_log),
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
