"""Tests for IdentityLock — token derivation, wrong-operator rejection."""
import json
import hashlib
import tempfile
import os
import pytest

from aios.core.identity_lock import IdentityLock, IdentityLockError


@pytest.fixture
def identity_file(tmp_path):
    """Write a valid identity.lock to a temp directory."""
    data = {
        "operator": "Chris",
        "locked": True,
        "level": "operator-only",
        "created": "2026-04-13T08:39:00Z",
    }
    p = tmp_path / "identity.lock"
    p.write_text(json.dumps(data))
    return str(p)


def test_load_valid(identity_file):
    il = IdentityLock()
    il.load(identity_file)
    assert il.get_operator() == "Chris"
    assert il.is_locked()


def test_token_is_deterministic(identity_file):
    il1 = IdentityLock()
    il1.load(identity_file)
    il2 = IdentityLock()
    il2.load(identity_file)
    assert il1.get_operator_token() == il2.get_operator_token()


def test_token_matches_manual_hash(identity_file):
    il = IdentityLock()
    il.load(identity_file)
    raw = "Chris-2026-04-13T08:39:00Z".encode()
    expected = hashlib.sha256(raw).hexdigest()
    assert il.get_operator_token() == expected


def test_is_operator_true(identity_file):
    il = IdentityLock()
    il.load(identity_file)
    token = il.get_operator_token()
    assert il.is_operator(token) is True


def test_is_operator_false(identity_file):
    il = IdentityLock()
    il.load(identity_file)
    assert il.is_operator("wrong-token") is False


def test_wrong_operator_raises(tmp_path):
    data = {
        "operator": "Mallory",
        "locked": True,
        "level": "operator-only",
        "created": "2026-01-01T00:00:00Z",
    }
    p = tmp_path / "bad.lock"
    p.write_text(json.dumps(data))
    il = IdentityLock()
    with pytest.raises(IdentityLockError):
        il.load(str(p))


def test_file_not_found_raises():
    il = IdentityLock()
    with pytest.raises(FileNotFoundError):
        il.load("/nonexistent/path/identity.lock")
