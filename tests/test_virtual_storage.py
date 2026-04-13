"""Tests for VirtualStorage — read/write/delete/persistence."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aios.virtual.vstorage import VirtualStorage


class TestVirtualStorage(unittest.TestCase):

    def setUp(self):
        self.vs = VirtualStorage()

    def test_write_and_read(self):
        self.vs.write("/test/file.txt", b"hello world")
        self.assertEqual(self.vs.read("/test/file.txt"), b"hello world")

    def test_write_string_converted_to_bytes(self):
        self.vs.write("/str/file", "string data")
        data = self.vs.read("/str/file")
        self.assertIsInstance(data, bytes)

    def test_delete(self):
        self.vs.write("/del/me", b"bye")
        self.assertTrue(self.vs.delete("/del/me"))
        self.assertFalse(self.vs.exists("/del/me"))

    def test_read_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.vs.read("/no/such/file")

    def test_list_by_prefix(self):
        self.vs.write("/proc/cpu", b"cpu info")
        self.vs.write("/proc/mem", b"mem info")
        self.vs.write("/other/file", b"other")
        proc_files = self.vs.list("/proc/")
        self.assertIn("/proc/cpu", proc_files)
        self.assertIn("/proc/mem", proc_files)
        self.assertNotIn("/other/file", proc_files)

    def test_used_bytes_tracking(self):
        self.vs.write("/a", b"abc")
        self.assertEqual(self.vs.used_bytes(), 3)
        self.vs.write("/b", b"de")
        self.assertEqual(self.vs.used_bytes(), 5)
        self.vs.delete("/a")
        self.assertEqual(self.vs.used_bytes(), 2)

    def test_save_and_load_from_file(self):
        self.vs.write("/persist/data", b"\x00\x01\x02\x03binary")
        self.vs.write("/text/file", b"plain text")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.assertTrue(self.vs.save_to_file(path))
            fresh = VirtualStorage()
            self.assertTrue(fresh.load_from_file(path))
            self.assertEqual(fresh.read("/persist/data"), b"\x00\x01\x02\x03binary")
            self.assertEqual(fresh.read("/text/file"), b"plain text")
            self.assertEqual(fresh.used_bytes(), self.vs.used_bytes())
        finally:
            os.unlink(path)

    def test_load_from_nonexistent_file(self):
        self.assertFalse(self.vs.load_from_file("/tmp/no_such_vstorage.json"))

    def test_status(self):
        st = self.vs.status()
        self.assertTrue(st["healthy"])
        self.assertEqual(st["component"], "VirtualStorage")


if __name__ == "__main__":
    unittest.main()
