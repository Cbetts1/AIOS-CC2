"""AI-OS Cloud Loop — the continuous cloud event loop (NEVER EXITS).

This module runs in its own daemon thread and performs four duties every tick:

1. Tick the CloudController (update state counters).
2. Send a node heartbeat every HEARTBEAT_INTERVAL seconds.
3. Synchronise cloud state into the NodeMesh every SYNC_INTERVAL seconds.
4. Accept any pending work queued through CloudAPI.

The loop only stops when stop() is called (e.g. during operator shutdown).
"""
import asyncio
import threading
import time
from datetime import datetime, timezone


class CloudLoop:
    """Daemon thread that keeps the cloud layer alive."""

    TICK_INTERVAL = 1.0           # seconds between loop iterations
    HEARTBEAT_INTERVAL = 10.0     # seconds between node heartbeats
    SYNC_INTERVAL = 5.0           # seconds between mesh sync broadcasts

    def __init__(self, cloud_controller=None, mesh=None):
        self._controller = cloud_controller
        self._mesh = mesh
        self._running = False
        self._thread: threading.Thread = None
        self._tick_count = 0
        self._last_heartbeat = 0.0
        self._last_sync = 0.0
        self._init_time = time.time()
        self._loop_log: list = []

    # ── Attachment ───────────────────────────────────────────────────────────

    def set_controller(self, controller) -> None:
        self._controller = controller

    def set_mesh(self, mesh) -> None:
        self._mesh = mesh

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run,
            name="cloud-loop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    # ── Main loop ────────────────────────────────────────────────────────────

    def _run(self) -> None:
        """The never-exit loop.  Runs until stop() sets _running = False."""
        self._log("CloudLoop started")

        while self._running:
            now = time.time()
            self._tick_count += 1

            # 1. Tick controller
            self._safe_tick()

            # 2. Node heartbeat
            if now - self._last_heartbeat >= self.HEARTBEAT_INTERVAL:
                self._last_heartbeat = now
                self._do_heartbeat()

            # 3. Mesh sync
            if now - self._last_sync >= self.SYNC_INTERVAL:
                self._last_sync = now
                self._do_mesh_sync()

            time.sleep(self.TICK_INTERVAL)

        self._log("CloudLoop stopped")

    # ── Per-iteration work ───────────────────────────────────────────────────

    def _safe_tick(self) -> None:
        try:
            if self._controller and self._controller._running:
                self._controller.tick()
        except Exception:
            pass

    def _do_heartbeat(self) -> None:
        try:
            if self._controller and self._controller._running:
                result = self._controller.heartbeat()
                alive = result.get("alive", 0)
                total = result.get("total", 0)
                self._log(f"HB: {alive}/{total} nodes alive")
        except Exception:
            pass

    def _do_mesh_sync(self) -> None:
        """Broadcast a cloud_sync pulse into the AI-OS NodeMesh."""
        if self._mesh is None or self._controller is None:
            return
        try:
            node_count = len(self._controller._nodes)
            running = self._controller._running
            payload = {
                "type": "cloud_sync",
                "node_count": node_count,
                "cloud_running": running,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            # NodeMesh.broadcast is a coroutine; spin up a minimal event loop
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._mesh.broadcast(payload))
            loop.close()
        except Exception:
            pass

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        entry = {"msg": msg, "ts": datetime.now(timezone.utc).isoformat()}
        self._loop_log.append(entry)
        if len(self._loop_log) > 200:
            self._loop_log = self._loop_log[-100:]

    def get_log(self, limit: int = 20) -> list:
        return list(self._loop_log[-limit:])

    # ── Status ───────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "component": "CloudLoop",
            "running": self._running,
            "tick_count": self._tick_count,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "last_heartbeat": self._last_heartbeat,
            "last_sync": self._last_sync,
            "healthy": self._running,
        }
