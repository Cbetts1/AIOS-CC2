"""AI-OS Virtual Network - Simulates private internal network 10.0.0.0/8."""
import asyncio
import time
from datetime import datetime


class VirtualNetwork:
    NETWORK = "10.0.0.0/8"
    BASE_IP = "10.0.0."

    def __init__(self):
        self._interfaces = {}   # name -> {"ip": str, "queue": asyncio.Queue}
        self._ip_counter = 1
        self._packets_sent = 0
        self._packets_received = 0
        self._packet_log = []
        self._init_time = time.time()

    def create_interface(self, name: str) -> str:
        if name in self._interfaces:
            return self._interfaces[name]["ip"]
        ip = f"{self.BASE_IP}{self._ip_counter}"
        self._ip_counter += 1
        self._interfaces[name] = {
            "ip": ip,
            "queue": asyncio.Queue(maxsize=256),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "rx": 0,
            "tx": 0,
        }
        return ip

    def remove_interface(self, name: str) -> bool:
        if name not in self._interfaces:
            return False
        del self._interfaces[name]
        return True

    async def send(self, src: str, dst: str, payload: bytes) -> bool:
        if not isinstance(payload, (bytes, bytearray)):
            payload = str(payload).encode("utf-8")
        # Find dst interface by name or IP
        dst_iface = None
        for name, iface in self._interfaces.items():
            if name == dst or iface["ip"] == dst:
                dst_iface = iface
                dst_name = name
                break
        if dst_iface is None:
            return False
        packet = {
            "src": src,
            "dst": dst,
            "payload": payload,
            "timestamp": time.time(),
            "size": len(payload),
        }
        try:
            dst_iface["queue"].put_nowait(packet)
            dst_iface["rx"] += 1
        except asyncio.QueueFull:
            return False

        # Update sender tx counter
        for name, iface in self._interfaces.items():
            if name == src or iface["ip"] == src:
                iface["tx"] += 1
                break

        self._packets_sent += 1
        self._packet_log.append({
            "src": src, "dst": dst,
            "size": len(payload),
            "ts": datetime.utcnow().isoformat() + "Z",
        })
        if len(self._packet_log) > 500:
            self._packet_log = self._packet_log[-250:]
        return True

    async def receive(self, dst: str) -> dict:
        iface = self._interfaces.get(dst)
        if iface is None:
            raise KeyError(f"Interface '{dst}' not found.")
        packet = await asyncio.wait_for(iface["queue"].get(), timeout=5.0)
        self._packets_received += 1
        return packet

    def try_receive(self, dst: str):
        iface = self._interfaces.get(dst)
        if iface is None:
            return None
        try:
            return iface["queue"].get_nowait()
        except asyncio.QueueEmpty:
            return None

    def get_ip(self, name: str) -> str:
        iface = self._interfaces.get(name)
        return iface["ip"] if iface else None

    def list_interfaces(self) -> list:
        return [
            {"name": n, "ip": iface["ip"], "rx": iface["rx"], "tx": iface["tx"]}
            for n, iface in self._interfaces.items()
        ]

    def status(self) -> dict:
        return {
            "component": "VirtualNetwork",
            "network": self.NETWORK,
            "interfaces": len(self._interfaces),
            "packets_sent": self._packets_sent,
            "packets_received": self._packets_received,
            "interface_list": self.list_interfaces(),
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
            "note": "VIRTUAL ONLY - never touches host network",
        }
