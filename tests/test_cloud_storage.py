"""Tests for CloudStorage — set/get/delete/namespace/persist."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aios.cloud.cloud_storage import CloudStorage


class TestCloudStorage(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.cs = CloudStorage(storage_dir=self._tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_set_and_get(self):
        self.cs.set("key1", "value1", namespace="ns1")
        self.assertEqual(self.cs.get("key1", namespace="ns1"), "value1")

    def test_get_missing_returns_default(self):
        self.assertIsNone(self.cs.get("missing_key", namespace="ns1"))
        self.assertEqual(self.cs.get("missing_key", namespace="ns1", default=42), 42)

    def test_delete(self):
        self.cs.set("del_key", "bye", namespace="ns1")
        self.assertTrue(self.cs.delete("del_key", namespace="ns1"))
        self.assertIsNone(self.cs.get("del_key", namespace="ns1"))

    def test_list_namespace(self):
        self.cs.set("a", 1, namespace="ns2")
        self.cs.set("b", 2, namespace="ns2")
        keys_dict = self.cs.list(namespace="ns2")
        self.assertIn("a", keys_dict)
        self.assertIn("b", keys_dict)

    def test_persistence_across_instances(self):
        self.cs.set("data", {"hello": "world"}, namespace="persist_ns")
        cs2 = CloudStorage(storage_dir=self._tmpdir)
        result = cs2.get("data", namespace="persist_ns")
        self.assertEqual(result, {"hello": "world"})

    def test_status(self):
        st = self.cs.status()
        self.assertTrue(st["healthy"])
        self.assertIn("storage_dir", st)

    def test_complex_value_types(self):
        self.cs.set("int_val", 42, namespace="types")
        self.cs.set("list_val", [1, 2, 3], namespace="types")
        self.cs.set("dict_val", {"a": "b"}, namespace="types")
        self.assertEqual(self.cs.get("int_val", namespace="types"), 42)
        self.assertEqual(self.cs.get("list_val", namespace="types"), [1, 2, 3])
        self.assertEqual(self.cs.get("dict_val", namespace="types"), {"a": "b"})


if __name__ == "__main__":
    unittest.main()
