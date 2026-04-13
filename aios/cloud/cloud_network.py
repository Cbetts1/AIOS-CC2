"""AI-OS Cloud Network — localhost TCP socket backbone.

All communication stays on 127.0.0.1 inside the port range 19000-19999.
The protocol is a simple 4-byte (big-endian) length prefix followed by a
UTF-8 JSON body, so it works with plain Python sockets and no external libs.
"""
import json
import socket
import struct
import threading
import time
from datetime import datetime, timezone

PORT_BASE = 19000
PORT_RANGE = 1000


# ── Low-level framing helpers ────────────────────────────────────────────────

def send_message(sock: socket.socket, msg: dict) -> None:
    """Send a length-prefixed JSON message over *sock*."""
    data = json.dumps(msg, default=str).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)


def recv_message(sock: socket.socket) -> dict:
    """Receive a length-prefixed JSON message from *sock*.  Returns {} on EOF."""
    raw_len = _recv_exactly(sock, 4)
    if len(raw_len) < 4:
        return {}
    (length,) = struct.unpack(">I", raw_len)
    if length == 0:
        return {}
    data = _recv_exactly(sock, length)
    if not data:
        return {}
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except (ConnectionResetError, OSError):
            return b""
        if not chunk:
            return b""
        buf += chunk
    return buf


# ── CloudNetwork ─────────────────────────────────────────────────────────────

class CloudNetwork:
    """Manages port allocation and provides direct socket messaging to nodes."""

    def __init__(self):
        self._allocated_ports: set = set()
        self._registry: dict = {}   # node_id -> {"port": int, "addr": str, ...}
        self._lock = threading.Lock()
        self._message_log: list = []
        self._msg_count = 0
        self._init_time = time.time()

    # ── Port management ──────────────────────────────────────────────────────

    def allocate_port(self) -> int:
        """Return a free localhost port in the cloud range."""
        with self._lock:
            for port in range(PORT_BASE, PORT_BASE + PORT_RANGE):
                if port in self._allocated_ports:
                    continue
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(("127.0.0.1", port))
                    s.close()
                    self._allocated_ports.add(port)
                    return port
                except OSError:
                    self._allocated_ports.add(port)  # mark as taken
            raise RuntimeError(
                f"No free ports available in cloud range "
                f"{PORT_BASE}-{PORT_BASE + PORT_RANGE - 1}"
            )

    def release_port(self, port: int) -> None:
        with self._lock:
            self._allocated_ports.discard(port)

    # ── Node registry ────────────────────────────────────────────────────────

    def register_node(self, node_id: str, port: int,
                      addr: str = "127.0.0.1") -> None:
        with self._lock:
            self._registry[node_id] = {
                "port": port,
                "addr": addr,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }

    def unregister_node(self, node_id: str) -> None:
        with self._lock:
            self._registry.pop(node_id, None)

    def get_node_addr(self, node_id: str):
        with self._lock:
            entry = self._registry.get(node_id)
            if entry:
                return entry["addr"], entry["port"]
            return None, None

    def list_nodes(self) -> list:
        with self._lock:
            return [{"id": k, **v} for k, v in self._registry.items()]

    def node_count(self) -> int:
        with self._lock:
            return len(self._registry)

    # ── Messaging ────────────────────────────────────────────────────────────

    def send_to_node(self, node_id: str, msg: dict,
                     timeout: float = 5.0) -> dict:
        """Open a fresh connection, send *msg*, receive the response, close."""
        addr, port = self.get_node_addr(node_id)
        if addr is None:
            return {"error": f"Node '{node_id}' not found in network registry"}
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((addr, port))
            send_message(s, msg)
            response = recv_message(s)
            s.close()
        except Exception as exc:
            return {"error": str(exc), "node_id": node_id}

        self._msg_count += 1
        ts = datetime.now(timezone.utc).isoformat()
        self._message_log.append({
            "to": node_id, "type": msg.get("type"), "ts": ts
        })
        if len(self._message_log) > 500:
            self._message_log = self._message_log[-250:]
        return response

    def broadcast(self, msg: dict) -> dict:
        """Send *msg* to every registered node; return {node_id: response}."""
        results = {}
        for node in self.list_nodes():
            nid = node["id"]
            results[nid] = self.send_to_node(nid, msg)
        return results

    def get_message_log(self, limit: int = 50) -> list:
        return list(self._message_log[-limit:])

    def status(self) -> dict:
        return {
            "component": "CloudNetwork",
            "registered_nodes": len(self._registry),
            "allocated_ports": len(self._allocated_ports),
            "messages_sent": self._msg_count,
            "port_range": f"{PORT_BASE}-{PORT_BASE + PORT_RANGE - 1}",
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
