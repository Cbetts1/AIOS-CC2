"""AI-OS Cloud Node — independent worker unit with TCP socket server.

Each CloudNode:
- Listens on a dedicated localhost port assigned by CloudNetwork.
- Accepts tasks sent as JSON over the wire protocol defined in cloud_network.
- Executes tasks synchronously in a per-connection thread.
- Supports: echo, vcpu_exec, state_query, compute, info.
- Reports its own status on demand.
"""
import threading
import time
import uuid
from datetime import datetime, timezone

from aios.cloud.cloud_network import CloudNetwork, recv_message, send_message
import socket


class CloudNode:
    """A single cloud worker node."""

    def __init__(self, node_id: str = None, port: int = None):
        self._id = node_id or f"node-{uuid.uuid4().hex[:8]}"
        self._port = port
        self._server_sock: socket.socket = None
        self._serve_thread: threading.Thread = None
        self._running = False
        self._task_count = 0
        self._lock = threading.Lock()
        self._start_time: float = None
        self._node_status = "idle"
        # Optionally attached subsystems
        self._vcpu = None
        self._state_registry = None

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def node_id(self) -> str:
        return self._id

    @property
    def port(self) -> int:
        return self._port

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def attach(self, vcpu=None, state_registry=None) -> None:
        """Attach AI-OS subsystems so tasks can reach them."""
        if vcpu is not None:
            self._vcpu = vcpu
        if state_registry is not None:
            self._state_registry = state_registry

    def start(self, port: int) -> bool:
        """Bind to *port* and begin accepting connections.  Returns True on success."""
        self._port = port
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind(("127.0.0.1", port))
            self._server_sock.listen(32)
            self._server_sock.settimeout(1.0)
        except OSError as exc:
            return False

        self._running = True
        self._start_time = time.time()
        self._serve_thread = threading.Thread(
            target=self._serve_loop,
            name=f"cloud-node-{self._id}",
            daemon=True,
        )
        self._serve_thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    # ── Socket server ────────────────────────────────────────────────────────

    def _serve_loop(self) -> None:
        while self._running:
            try:
                conn, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(
                target=self._handle_conn, args=(conn,), daemon=True
            )
            t.start()

    def _handle_conn(self, conn: socket.socket) -> None:
        try:
            msg = recv_message(conn)
            if not msg:
                return
            response = self._dispatch(msg)
            send_message(conn, response)
        except Exception as exc:
            try:
                send_message(conn, {"error": str(exc), "node_id": self._id})
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ── Message dispatch ─────────────────────────────────────────────────────

    def _dispatch(self, msg: dict) -> dict:
        mtype = msg.get("type", "unknown")
        if mtype == "ping":
            return {"type": "pong", "node_id": self._id,
                    "ts": datetime.now(timezone.utc).isoformat()}
        if mtype == "heartbeat":
            return {
                "type": "heartbeat_ack",
                "node_id": self._id,
                "status": self._node_status,
                "task_count": self._task_count,
                "uptime_seconds": self.uptime(),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        if mtype == "status":
            return self.status()
        if mtype == "task":
            return self._run_task(msg.get("data", {}))
        return {"error": f"Unknown message type: '{mtype}'", "node_id": self._id}

    # ── Task execution ───────────────────────────────────────────────────────

    def _run_task(self, task: dict) -> dict:
        task_id = task.get("task_id", f"task-{uuid.uuid4().hex[:6]}")
        task_type = task.get("type", "echo")
        with self._lock:
            self._task_count += 1
            self._node_status = "busy"
        try:
            result = self._execute(task_type, task)
            with self._lock:
                self._node_status = "idle"
            return {
                "type": "task_result",
                "task_id": task_id,
                "status": "complete",
                "result": result,
                "node_id": self._id,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            with self._lock:
                self._node_status = "idle"
            return {
                "type": "task_result",
                "task_id": task_id,
                "status": "error",
                "error": str(exc),
                "node_id": self._id,
                "ts": datetime.now(timezone.utc).isoformat(),
            }

    def _execute(self, task_type: str, task: dict):
        """Route a task to the appropriate handler."""
        payload = task.get("payload", {})

        if task_type == "echo":
            return payload

        if task_type == "vcpu_exec":
            if self._vcpu is None:
                return {"error": "No vCPU attached to this node"}
            instruction = task.get("instruction", payload) or {"op": "NOP"}
            return self._vcpu.execute(instruction)

        if task_type == "state_query":
            if self._state_registry is None:
                return {"error": "No StateRegistry attached to this node"}
            key = task.get("key", payload.get("key", ""))
            ns = task.get("namespace", payload.get("namespace", "default"))
            return self._state_registry.get(key, namespace=ns)

        if task_type == "compute":
            a = float(payload.get("a", 0))
            b = float(payload.get("b", 0))
            op = payload.get("op", "add")
            ops = {
                "add": a + b,
                "sub": a - b,
                "mul": a * b,
                "div": a / b if b != 0 else 0.0,
                "mod": a % b if b != 0 else 0.0,
                "pow": a ** b,
            }
            if op not in ops:
                return {"error": f"Unknown compute op: '{op}'"}
            return {"op": op, "a": a, "b": b, "result": ops[op]}

        if task_type == "info":
            return self.status()

        return {"error": f"Unknown task type: '{task_type}'"}

    # ── Status / uptime ──────────────────────────────────────────────────────

    def uptime(self) -> float:
        if self._start_time is None:
            return 0.0
        return round(time.time() - self._start_time, 2)

    def status(self) -> dict:
        return {
            "component": "CloudNode",
            "node_id": self._id,
            "port": self._port,
            "addr": "127.0.0.1",
            "running": self._running,
            "status": self._node_status,
            "task_count": self._task_count,
            "uptime_seconds": self.uptime(),
            "has_vcpu": self._vcpu is not None,
            "has_state_registry": self._state_registry is not None,
            "healthy": self._running,
        }
