"""Tests for StateRegistry — thread safety, persistence, namespaces."""
import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestStateRegistry(unittest.TestCase):

    def setUp(self):
        # Reset singleton between tests by clearing _instance
        from aios.core.state_registry import StateRegistry
        StateRegistry._instance = None
        self.registry = StateRegistry()

    def test_set_and_get(self):
        self.registry.set("key1", "value1")
        self.assertEqual(self.registry.get("key1"), "value1")

    def test_default_namespace(self):
        self.registry.set("x", 42, namespace="default")
        self.assertEqual(self.registry.get("x", namespace="default"), 42)

    def test_separate_namespaces(self):
        self.registry.set("k", "ns1_val", namespace="ns1")
        self.registry.set("k", "ns2_val", namespace="ns2")
        self.assertEqual(self.registry.get("k", namespace="ns1"), "ns1_val")
        self.assertEqual(self.registry.get("k", namespace="ns2"), "ns2_val")

    def test_missing_key_returns_default(self):
        self.assertIsNone(self.registry.get("does_not_exist"))
        self.assertEqual(self.registry.get("does_not_exist", default=99), 99)

    def test_delete(self):
        self.registry.set("del_me", "bye")
        self.assertTrue(self.registry.delete("del_me"))
        self.assertIsNone(self.registry.get("del_me"))

    def test_singleton(self):
        from aios.core.state_registry import StateRegistry
        r2 = StateRegistry()
        self.assertIs(self.registry, r2)

    def test_thread_safety(self):
        errors = []

        def worker(i):
            try:
                self.registry.set(f"k{i}", i, namespace="thread_test")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(self.registry.list(namespace="thread_test")), 50)

    def test_flush_and_load_from_file(self):
        self.registry.set("persist_key", "hello", namespace="persist_ns")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.assertTrue(self.registry.flush_to_file(path))
            # Reset and load
            from aios.core.state_registry import StateRegistry
            StateRegistry._instance = None
            fresh = StateRegistry()
            self.assertTrue(fresh.load_from_file(path))
            self.assertEqual(fresh.get("persist_key", namespace="persist_ns"), "hello")
        finally:
            os.unlink(path)

    def test_flush_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "dir", "state.json")
            self.registry.set("x", 1)
            self.assertTrue(self.registry.flush_to_file(path))
            self.assertTrue(os.path.exists(path))

    def test_load_from_nonexistent_file(self):
        self.assertFalse(self.registry.load_from_file("/tmp/does_not_exist_aios.json"))

    def test_status(self):
        self.registry.set("a", 1)
        st = self.registry.status()
        self.assertTrue(st["healthy"])
        self.assertGreaterEqual(st["total_keys"], 1)


if __name__ == "__main__":
    unittest.main()
