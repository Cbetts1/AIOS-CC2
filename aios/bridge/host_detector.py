"""AI-OS Host Capability Detector - Detects host environment capabilities."""
import os
import platform
import sys
import time


class HostCapabilityDetector:
    def __init__(self):
        self._capabilities = {}
        self._detected = False
        self._detect_time = None

    def detect(self) -> dict:
        cpu_count = os.cpu_count() or 1
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
        except Exception:
            pass

        total_ram_gb = 0.0
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        total_ram_gb = round(kb / (1024 * 1024), 2)
                        break
        except Exception:
            total_ram_gb = 4.0  # safe default

        self._capabilities = {
            "os_name": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python_version": sys.version,
            "python_version_tuple": list(sys.version_info[:3]),
            "cpu_count": cpu_count,
            "total_ram_gb": total_ram_gb,
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "detected_at": time.time(),
        }
        self._detected = True
        self._detect_time = time.time()
        return self._capabilities

    def capabilities(self) -> dict:
        if not self._detected:
            self.detect()
        return dict(self._capabilities)

    def get(self, key: str, default=None):
        return self.capabilities().get(key, default)

    def status(self) -> dict:
        caps = self.capabilities()
        return {
            "component": "HostCapabilityDetector",
            "detected": self._detected,
            "os": caps.get("os_name", "unknown"),
            "cpu_count": caps.get("cpu_count", 0),
            "total_ram_gb": caps.get("total_ram_gb", 0),
            "python_version": caps.get("python_version_tuple", []),
            "detect_time": self._detect_time,
            "healthy": True,
        }
