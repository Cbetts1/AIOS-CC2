"""AI-OS Virtual CPU - Simulates a CPU with registers and program counter."""
import time
from datetime import datetime


class VirtualCPU:
    NUM_REGISTERS = 8
    STACK_SIZE = 256

    INSTRUCTIONS = {
        "NOP": 0x00, "MOV": 0x01, "ADD": 0x02, "SUB": 0x03,
        "MUL": 0x04, "DIV": 0x05, "AND": 0x06, "OR": 0x07,
        "XOR": 0x08, "NOT": 0x09, "PUSH": 0x0A, "POP": 0x0B,
        "JMP": 0x0C, "JZ": 0x0D, "JNZ": 0x0E, "HALT": 0xFF,
    }

    def __init__(self):
        self.registers = {f"r{i}": 0 for i in range(self.NUM_REGISTERS)}
        self.pc = 0          # program counter
        self.sp = 0          # stack pointer
        self.stack = [0] * self.STACK_SIZE
        self.flags = {"zero": False, "carry": False, "overflow": False}
        self.cycles = 0
        self.halted = False
        self._tick_count = 0
        self._last_tick = None
        self._instruction_log = []

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        if not self.halted:
            self.cycles += 1
            self.pc += 1
            if self.pc > 0xFFFF:
                self.pc = 0

    def execute(self, instruction: dict) -> dict:
        op = instruction.get("op", "NOP").upper()
        src = instruction.get("src", 0)
        dst = instruction.get("dst", "r0")
        result = {"op": op, "src": src, "dst": dst, "cycles": self.cycles, "success": True}

        if op == "NOP":
            pass
        elif op == "MOV":
            if dst in self.registers:
                self.registers[dst] = int(src) & 0xFFFF
        elif op == "ADD":
            if dst in self.registers:
                val = self.registers[dst] + int(src)
                self.flags["carry"] = val > 0xFFFF
                self.registers[dst] = val & 0xFFFF
                self.flags["zero"] = self.registers[dst] == 0
        elif op == "SUB":
            if dst in self.registers:
                val = self.registers[dst] - int(src)
                self.flags["carry"] = val < 0
                self.registers[dst] = max(0, val) & 0xFFFF
                self.flags["zero"] = self.registers[dst] == 0
        elif op == "PUSH":
            if self.sp < self.STACK_SIZE:
                val = self.registers.get(str(src), int(src) if isinstance(src, int) else 0)
                self.stack[self.sp] = val
                self.sp += 1
        elif op == "POP":
            if self.sp > 0:
                self.sp -= 1
                if dst in self.registers:
                    self.registers[dst] = self.stack[self.sp]
        elif op == "JMP":
            self.pc = int(src) & 0xFFFF
        elif op == "HALT":
            self.halted = True
        else:
            result["success"] = False
            result["error"] = f"Unknown instruction: {op}"

        self.cycles += 1
        self._instruction_log.append(result)
        if len(self._instruction_log) > 200:
            self._instruction_log = self._instruction_log[-100:]
        return result

    def reset(self) -> None:
        self.registers = {f"r{i}": 0 for i in range(self.NUM_REGISTERS)}
        self.pc = 0
        self.sp = 0
        self.stack = [0] * self.STACK_SIZE
        self.flags = {"zero": False, "carry": False, "overflow": False}
        self.halted = False

    def status(self) -> dict:
        return {
            "component": "VirtualCPU",
            "tick_count": self._tick_count,
            "cycles": self.cycles,
            "pc": hex(self.pc),
            "sp": self.sp,
            "registers": dict(self.registers),
            "flags": dict(self.flags),
            "halted": self.halted,
            "last_tick": self._last_tick,
            "healthy": not self.halted,
        }
