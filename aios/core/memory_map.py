"""AI-OS Memory Map Controller - Simulates virtual memory regions."""
import time
from datetime import datetime


class MemoryMapController:
    PAGE_SIZE = 4096  # bytes

    def __init__(self):
        self._regions = {}   # name -> {"data": bytearray, "size_kb": int, "alloc_time": float}

    def allocate(self, name: str, size_kb: int) -> bool:
        if name in self._regions:
            return False  # already allocated
        byte_count = size_kb * 1024
        self._regions[name] = {
            "data": bytearray(byte_count),
            "size_kb": size_kb,
            "alloc_time": time.time(),
            "reads": 0,
            "writes": 0,
        }
        return True

    def free(self, name: str) -> bool:
        if name not in self._regions:
            return False
        del self._regions[name]
        return True

    def read(self, name: str, offset: int, length: int) -> bytes:
        region = self._regions.get(name)
        if region is None:
            raise KeyError(f"Memory region '{name}' not allocated.")
        data = region["data"]
        if offset < 0 or offset + length > len(data):
            raise ValueError(f"Read out of bounds: offset={offset}, length={length}, size={len(data)}")
        region["reads"] += 1
        return bytes(data[offset: offset + length])

    def write(self, name: str, offset: int, data: bytes) -> None:
        region = self._regions.get(name)
        if region is None:
            raise KeyError(f"Memory region '{name}' not allocated.")
        buf = region["data"]
        if offset < 0 or offset + len(data) > len(buf):
            raise ValueError(f"Write out of bounds: offset={offset}, data_len={len(data)}, region_size={len(buf)}")
        buf[offset: offset + len(data)] = data
        region["writes"] += 1

    def map_report(self) -> dict:
        report = {}
        for name, region in self._regions.items():
            report[name] = {
                "size_kb": region["size_kb"],
                "alloc_time": region["alloc_time"],
                "reads": region["reads"],
                "writes": region["writes"],
                "usage_bytes": len(region["data"]),
            }
        return report

    def total_allocated_kb(self) -> int:
        return sum(r["size_kb"] for r in self._regions.values())

    def status(self) -> dict:
        return {
            "component": "MemoryMapController",
            "regions": len(self._regions),
            "total_allocated_kb": self.total_allocated_kb(),
            "region_names": list(self._regions.keys()),
            "healthy": True,
        }
