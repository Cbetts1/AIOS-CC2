"""AI-OS Host Bridge - Aggregates all bridge components."""
import time
from datetime import datetime

from aios.bridge.resource_translator import ResourceTranslator
from aios.bridge.permission_container import PermissionContainer
from aios.bridge.host_detector import HostCapabilityDetector
from aios.bridge.sandbox_manager import SandboxManager


class HostBridge:
    def __init__(self):
        self.translator = ResourceTranslator()
        self.permissions = PermissionContainer()
        self.detector = HostCapabilityDetector()
        self.sandbox = SandboxManager()
        self._tick_count = 0
        self._boot_time = None
        self._last_tick = None

    def boot(self) -> dict:
        self._boot_time = time.time()
        caps = self.detector.detect()
        self.sandbox.enter_sandbox()
        return {
            "status": "ONLINE",
            "boot_time": datetime.utcnow().isoformat() + "Z",
            "host_os": caps.get("os_name", "unknown"),
            "cpu_count": caps.get("cpu_count", 0),
            "sandboxed": self.sandbox.is_sandboxed(),
        }

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()

    def translate_read(self, vaddr: int) -> dict:
        if not self.permissions.check("read_vram"):
            return {"error": "permission denied", "vaddr": hex(vaddr)}
        return self.translator.translate_read(vaddr)

    def translate_write(self, vaddr: int, data: bytes) -> dict:
        if not self.permissions.check("write_vram"):
            return {"error": "permission denied", "vaddr": hex(vaddr)}
        return self.translator.translate_write(vaddr, data)

    def uptime(self) -> float:
        if self._boot_time is None:
            return 0.0
        return round(time.time() - self._boot_time, 2)

    def status(self) -> dict:
        return {
            "component": "HostBridge",
            "status": "ONLINE" if self._boot_time else "OFFLINE",
            "tick_count": self._tick_count,
            "uptime_seconds": self.uptime(),
            "last_tick": self._last_tick,
            "sandboxed": self.sandbox.is_sandboxed(),
            "sub_components": {
                "ResourceTranslator": self.translator.status(),
                "PermissionContainer": self.permissions.status(),
                "HostCapabilityDetector": self.detector.status(),
                "SandboxManager": self.sandbox.status(),
            },
            "healthy": self._boot_time is not None,
        }
