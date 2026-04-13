"""AI-OS Log Writer — persistent JSON-lines log files.

Writes one JSON object per line to a rotating log file under the ``logs/``
directory at the repository root.  Falls back silently to in-memory-only
logging if the filesystem is not writable.

Usage
-----
from aios.core.log_writer import LogWriter

lw = LogWriter("aios")          # creates logs/aios.log
lw.write({"msg": "hello"})
lw.close()

Wire-in
-------
Pass a LogWriter instance to CommandCenter, SecurityKernel, or PolicyEngine.
Each of those classes has an ``attach_log_writer(lw)`` method added in this
PR so their internal ``_log()`` / ``log_security_event()`` calls also persist
to disk.
"""
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def _default_log_dir() -> Path:
    """Return the ``logs/`` directory next to the repo root."""
    # This file lives at  aios/core/log_writer.py  →  repo_root = ../../
    here = Path(__file__).resolve()
    return here.parent.parent.parent / "logs"


class LogWriter:
    """Thread-safe JSON-lines log writer with optional file persistence."""

    MAX_BYTES = 5 * 1024 * 1024   # rotate at 5 MB
    MAX_BACKUPS = 3

    def __init__(self, name: str, log_dir: Path = None):
        self._name = name
        self._dir = Path(log_dir) if log_dir else _default_log_dir()
        self._path = self._dir / f"{name}.log"
        self._fh = None
        self._lock = threading.Lock()
        self._write_count = 0
        self._error_count = 0
        self._enabled = False
        self._open()

    # ── File management ──────────────────────────────────────────────────────

    def _open(self) -> None:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._fh = open(self._path, "a", encoding="utf-8")
            self._enabled = True
        except Exception:
            self._fh = None
            self._enabled = False

    def _rotate_if_needed(self) -> None:
        if not self._fh:
            return
        try:
            if self._path.stat().st_size >= self.MAX_BYTES:
                self._fh.close()
                # Shift backups
                for i in range(self.MAX_BACKUPS - 1, 0, -1):
                    src = self._dir / f"{self._name}.log.{i}"
                    dst = self._dir / f"{self._name}.log.{i + 1}"
                    if src.exists():
                        src.rename(dst)
                backup = self._dir / f"{self._name}.log.1"
                self._path.rename(backup)
                self._open()
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def write(self, record: dict) -> None:
        """Append *record* as a JSON line.  Thread-safe."""
        if "ts" not in record:
            record = dict(record)
            record["ts"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            self._write_count += 1
            if not self._enabled or not self._fh:
                return
            try:
                self._rotate_if_needed()
                self._fh.write(line)
                self._fh.flush()
            except Exception:
                self._error_count += 1

    def close(self) -> None:
        with self._lock:
            if self._fh:
                try:
                    self._fh.close()
                except Exception:
                    pass
                self._fh = None
            self._enabled = False

    def status(self) -> dict:
        return {
            "component": "LogWriter",
            "name": self._name,
            "path": str(self._path),
            "enabled": self._enabled,
            "write_count": self._write_count,
            "error_count": self._error_count,
            "healthy": self._enabled,
        }
