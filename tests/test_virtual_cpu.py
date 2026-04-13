"""Tests for VirtualCPU — registers, instructions, tick, status."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aios.virtual.vcpu import VirtualCPU


class TestVirtualCPU(unittest.TestCase):

    def setUp(self):
        self.cpu = VirtualCPU()

    def test_initial_registers_zero(self):
        for reg, val in self.cpu.registers.items():
            self.assertEqual(val, 0, f"Register {reg} should start at 0")

    def test_mov_instruction(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 42})
        self.assertEqual(self.cpu.registers["r0"], 42)

    def test_add_instruction(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 10})
        self.cpu.execute({"op": "ADD", "dst": "r0", "src": 5})
        self.assertEqual(self.cpu.registers["r0"], 15)

    def test_sub_instruction(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 20})
        self.cpu.execute({"op": "SUB", "dst": "r0", "src": 8})
        self.assertEqual(self.cpu.registers["r0"], 12)

    def test_push_and_pop(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 99})
        self.cpu.execute({"op": "PUSH", "src": "r0"})
        self.cpu.execute({"op": "POP", "dst": "r1"})
        self.assertEqual(self.cpu.registers["r1"], 99)

    def test_tick_increments_cycles(self):
        cycles_before = self.cpu.cycles
        self.cpu.tick()
        self.assertGreater(self.cpu.cycles, cycles_before)

    def test_status(self):
        st = self.cpu.status()
        self.assertTrue(st["healthy"])
        self.assertEqual(st["component"], "VirtualCPU")

    def test_reset_clears_registers(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 100})
        self.cpu.reset()
        self.assertEqual(self.cpu.registers["r0"], 0)

    def test_nop_does_nothing(self):
        before = dict(self.cpu.registers)
        self.cpu.execute({"op": "NOP"})
        self.assertEqual(self.cpu.registers, before)

    def test_16bit_overflow_wraps(self):
        self.cpu.execute({"op": "MOV", "dst": "r0", "src": 65535})
        self.cpu.execute({"op": "ADD", "dst": "r0", "src": 1})
        # 65535 + 1 = 65536 → wraps to 0 (& 0xFFFF)
        self.assertEqual(self.cpu.registers["r0"], 0)
        self.assertTrue(self.cpu.flags["carry"])

    def test_halt_sets_halted_flag(self):
        self.cpu.execute({"op": "HALT"})
        self.assertTrue(self.cpu.halted)

    def test_halted_cpu_reports_not_healthy(self):
        self.cpu.execute({"op": "HALT"})
        st = self.cpu.status()
        self.assertFalse(st["healthy"])


if __name__ == "__main__":
    unittest.main()
