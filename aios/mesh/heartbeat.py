"""AI-OS Heartbeat System - Sends periodic heartbeats via NodeMesh."""
import asyncio
import time
from datetime import datetime


class HeartbeatSystem:
    INTERVAL = 5.0  # seconds

    def __init__(self, node_mesh=None):
        self._mesh = node_mesh
        self._running = False
        self._task = None
        self._beat_count = 0
        self._last_beat_time = None
        self._last_beat_ts = None
        self._init_time = time.time()

    def set_mesh(self, node_mesh) -> None:
        self._mesh = node_mesh

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.ensure_future(self._run())

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    async def _run(self) -> None:
        while self._running:
            await self.beat()
            try:
                await asyncio.sleep(self.INTERVAL)
            except asyncio.CancelledError:
                break

    async def beat(self) -> dict:
        self._beat_count += 1
        self._last_beat_time = time.time()
        self._last_beat_ts = datetime.utcnow().isoformat() + "Z"
        pulse = {
            "type": "heartbeat",
            "beat": self._beat_count,
            "timestamp": self._last_beat_ts,
            "uptime": round(time.time() - self._init_time, 1),
        }
        if self._mesh is not None:
            try:
                await self._mesh.broadcast(pulse)
            except Exception:
                pass
        return pulse

    def last_beat(self) -> dict:
        return {
            "beat_count": self._beat_count,
            "last_beat_time": self._last_beat_time,
            "last_beat_ts": self._last_beat_ts,
            "seconds_since_last": round(time.time() - self._last_beat_time, 1)
            if self._last_beat_time
            else None,
        }

    def status(self) -> dict:
        return {
            "component": "HeartbeatSystem",
            "running": self._running,
            "beat_count": self._beat_count,
            "last_beat_ts": self._last_beat_ts,
            "interval_seconds": self.INTERVAL,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": self._running,
        }
