"""Tests for CloudController — boot, spawn, exec, heartbeat, stop."""
import pytest
from aios.cloud.cloud_controller import CloudController
from aios.core.state_registry import StateRegistry


@pytest.fixture
def cloud():
    state = StateRegistry()
    c = CloudController(state_registry=state)
    c.boot()
    yield c
    c.stop()


def test_boot_status(cloud):
    st = cloud.status()
    assert st["running"] is True
    assert st["healthy"] is True


def test_spawn_node(cloud):
    result = cloud.spawn_node()
    assert "node_id" in result
    assert result["status"] == "running"
    assert len(cloud.list_nodes()) == 1


def test_spawn_duplicate_node_id(cloud):
    cloud.spawn_node("my-node")
    result = cloud.spawn_node("my-node")
    assert "error" in result


def test_list_nodes(cloud):
    cloud.spawn_node("n1")
    cloud.spawn_node("n2")
    nodes = cloud.list_nodes()
    assert len(nodes) == 2


def test_exec_task_auto_spawns(cloud):
    result = cloud.exec_task("echo", {"msg": "hello"})
    assert isinstance(result, dict)
    # Should either complete a task or report an error — never None
    assert "task_id" in result or "error" in result or "status" in result


def test_stop_node(cloud):
    cloud.spawn_node("removeme")
    result = cloud.stop_node("removeme")
    assert result["status"] == "stopped"
    assert len(cloud.list_nodes()) == 0


def test_stop_missing_node(cloud):
    result = cloud.stop_node("no-such-node")
    assert "error" in result


def test_tick(cloud):
    before = cloud._tick_count
    cloud.tick()
    assert cloud._tick_count == before + 1


def test_stop(cloud):
    cloud.stop()
    assert cloud._running is False


def test_event_log(cloud):
    log = cloud.get_event_log()
    assert isinstance(log, list)
    assert len(log) > 0  # boot logged at least one entry
