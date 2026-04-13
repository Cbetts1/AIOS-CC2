"""AI-OS Virtual Memory - Simulates 64MB RAM."""
import time


class VirtualMemory:
    SIZE_MB = 64
    SIZE_BYTES = SIZE_MB * 1024 * 1024

    def __init__(self):
        self._ram = bytearray(self.SIZE_BYTES)
        self._reads = 0
        self._writes = 0
        self._read_bytes = 0
        self._write_bytes = 0
        self._init_time = time.time()

    def _check_bounds(self, addr: int, size: int) -> None:
        if addr < 0 or addr + size > self.SIZE_BYTES:
            raise ValueError(
                f"Address 0x{addr:08X} + {size} bytes exceeds memory bounds "
                f"(0x{self.SIZE_BYTES:08X})"
            )

    def read(self, addr: int, size: int) -> bytes:
        self._check_bounds(addr, size)
        self._reads += 1
        self._read_bytes += size
        return bytes(self._ram[addr: addr + size])

    def write(self, addr: int, data: bytes) -> None:
        self._check_bounds(addr, len(data))
        self._writes += 1
        self._write_bytes += len(data)
        self._ram[addr: addr + len(data)] = data

    def zero_fill(self, addr: int, size: int) -> None:
        self._check_bounds(addr, size)
        for i in range(size):
            self._ram[addr + i] = 0

    def read_word(self, addr: int) -> int:
        data = self.read(addr, 4)
        return int.from_bytes(data, "little")

    def write_word(self, addr: int, value: int) -> None:
        data = value.to_bytes(4, "little")
        self.write(addr, data)

    def dump_region(self, addr: int, size: int) -> str:
        data = self.read(addr, min(size, 256))
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i: i + 16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"0x{addr+i:08X}  {hex_part:<48}  {ascii_part}")
        return "\n".join(lines)

    def status(self) -> dict:
        used_estimate = sum(1 for b in self._ram[:65536] if b != 0) * (self.SIZE_BYTES // 65536)
        return {
            "component": "VirtualMemory",
            "size_mb": self.SIZE_MB,
            "total_bytes": self.SIZE_BYTES,
            "reads": self._reads,
            "writes": self._writes,
            "bytes_read": self._read_bytes,
            "bytes_written": self._write_bytes,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
