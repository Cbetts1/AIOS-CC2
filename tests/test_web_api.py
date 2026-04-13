"""Tests for the web API — start server, hit all endpoints, check responses."""
import json
import socket
import threading
import time
import urllib.request
import urllib.error
import pytest

from aios.web.server import AIWebServer, _ADMIN_PASSWORD
from aios.command.command_center import CommandCenter


def _free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server():
    """Spin up a real AIWebServer on a free port, yield its base URL."""
    cc = CommandCenter()
    cc.boot()

    port = _free_port()
    srv = AIWebServer(command_center=cc)
    srv.PORT = port
    srv.start()
    time.sleep(0.2)   # let the thread bind

    yield f"http://127.0.0.1:{port}", srv

    srv.stop()


def _get(url: str) -> tuple:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read())


def _post(url: str, body: dict) -> tuple:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ── Open endpoints ───────────────────────────────────────────────────────────

def test_health(server):
    base, _ = server
    status, body = _get(f"{base}/api/health")
    assert status == 200
    assert body["status"] == "OK"
    assert "uptime_seconds" in body


def test_status(server):
    base, _ = server
    status, body = _get(f"{base}/api/status")
    assert status == 200
    assert "version" in body or "operator" in body


def test_heartbeat(server):
    base, _ = server
    status, body = _get(f"{base}/api/heartbeat")
    assert status == 200
    assert body.get("alive") is True


def test_proc(server):
    base, _ = server
    status, body = _get(f"{base}/api/proc")
    assert status == 200
    assert "proc_files" in body


# ── Protected endpoints ──────────────────────────────────────────────────────

def test_command_requires_password(server):
    base, _ = server
    status, body = _post(f"{base}/api/command", {"cmd": "1.1"})
    assert status == 403
    assert "Forbidden" in body.get("error", "")


def test_command_with_correct_password(server):
    base, _ = server
    status, body = _post(f"{base}/api/command",
                         {"cmd": "1.1", "password": _ADMIN_PASSWORD})
    assert status == 200
    assert "result" in body
    assert body["result"].strip()


def test_command_with_header_password(server):
    base, _ = server
    data = json.dumps({"cmd": "1"}).encode()
    req = urllib.request.Request(
        f"{base}/api/command",
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Admin-Password": _ADMIN_PASSWORD,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.loads(resp.read())
    assert "result" in body


def test_debug_requires_password(server):
    base, _ = server
    try:
        _get(f"{base}/api/debug")
        pytest.fail("Expected 403")
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_debug_with_correct_password(server):
    base, _ = server
    status, body = _get(f"{base}/api/debug?password={_ADMIN_PASSWORD}")
    assert status == 200
    assert isinstance(body, dict)
