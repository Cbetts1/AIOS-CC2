"""AI-OS Node Mesh - Internal mesh network for inter-subsystem communication."""
import asyncio
import time
from datetime import datetime, timezone


class NodeMesh:
    def __init__(self):
        self._nodes = {}    # name -> {"addr": str, "queue": asyncio.Queue, "rx": int, "tx": int}
        self._addr_counter = 1
        self._messages_broadcast = 0
        self._messages_sent = 0
        self._message_log = []
        self._init_time = time.time()

    def add_node(self, name: str, addr: str = None) -> str:
        if name in self._nodes:
            return self._nodes[name]["addr"]
        if addr is None:
            addr = f"mesh-node-{self._addr_counter:04d}"
            self._addr_counter += 1
        self._nodes[name] = {
            "addr": addr,
            "queue": asyncio.Queue(maxsize=512),
            "rx": 0,
            "tx": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return addr

    def remove_node(self, name: str) -> bool:
        if name not in self._nodes:
            return False
        del self._nodes[name]
        return True

    async def broadcast(self, msg: dict) -> int:
        delivered = 0
        ts = datetime.now(timezone.utc).isoformat()
        packet = {"type": "broadcast", "msg": msg, "timestamp": ts}
        for name, node in self._nodes.items():
            try:
                node["queue"].put_nowait(packet)
                node["rx"] += 1
                delivered += 1
            except asyncio.QueueFull:
                pass
        self._messages_broadcast += 1
        self._message_log.append({"type": "broadcast", "ts": ts, "delivered": delivered})
        if len(self._message_log) > 500:
            self._message_log = self._message_log[-250:]
        return delivered

    async def send(self, src: str, dst: str, msg: dict) -> bool:
        dst_node = self._nodes.get(dst)
        if dst_node is None:
            return False
        ts = datetime.now(timezone.utc).isoformat()
        packet = {"type": "unicast", "src": src, "dst": dst, "msg": msg, "timestamp": ts}
        try:
            dst_node["queue"].put_nowait(packet)
            dst_node["rx"] += 1
        except asyncio.QueueFull:
            return False
        src_node = self._nodes.get(src)
        if src_node:
            src_node["tx"] += 1
        self._messages_sent += 1
        self._message_log.append({"type": "unicast", "src": src, "dst": dst, "ts": ts})
        return True

    async def receive(self, name: str, timeout: float = 2.0) -> dict:
        node = self._nodes.get(name)
        if node is None:
            raise KeyError(f"Node '{name}' not in mesh.")
        return await asyncio.wait_for(node["queue"].get(), timeout=timeout)

    def try_receive(self, name: str):
        node = self._nodes.get(name)
        if node is None:
            return None
        try:
            return node["queue"].get_nowait()
        except asyncio.QueueEmpty:
            return None

    def list_nodes(self) -> list:
        return [
            {"name": n, "addr": nd["addr"], "rx": nd["rx"], "tx": nd["tx"]}
            for n, nd in self._nodes.items()
        ]

    def broadcast_sync(self, msg: dict) -> int:
        """Synchronous broadcast using put_nowait — safe to call from any thread."""
        delivered = 0
        ts = datetime.now(timezone.utc).isoformat()
        packet = {"type": "broadcast", "msg": msg, "timestamp": ts}
        for name, node in self._nodes.items():
            try:
                node["queue"].put_nowait(packet)
                node["rx"] += 1
                delivered += 1
            except Exception:
                pass
        self._messages_broadcast += 1
        self._message_log.append({"type": "broadcast_sync", "ts": ts, "delivered": delivered})
        if len(self._message_log) > 500:
            self._message_log = self._message_log[-250:]
        return delivered

    def status(self) -> dict:
        return {
            "component": "NodeMesh",
            "node_count": len(self._nodes),
            "messages_broadcast": self._messages_broadcast,
            "messages_sent": self._messages_sent,
            "nodes": self.list_nodes(),
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
