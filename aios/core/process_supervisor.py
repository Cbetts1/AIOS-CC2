"""AI-OS Process Supervisor - Manages asyncio coroutine tasks."""
import asyncio
import time
from datetime import datetime


class ProcessSupervisor:
    def __init__(self):
        self._registry = {}   # name -> {"coro_factory": fn, "task": Task|None, "status": str}
        self._start_times = {}
        self._restarts = {}

    def register(self, name: str, coro_factory) -> None:
        """Register a coroutine factory (callable returning a coroutine)."""
        self._registry[name] = {
            "coro_factory": coro_factory,
            "task": None,
            "status": "registered",
        }
        self._restarts[name] = 0

    async def start_all(self) -> None:
        for name in list(self._registry.keys()):
            await self._start_one(name)

    async def _start_one(self, name: str) -> None:
        entry = self._registry.get(name)
        if entry is None:
            return
        if entry["task"] is not None and not entry["task"].done():
            return  # already running
        coro_factory = entry["coro_factory"]
        task = asyncio.ensure_future(self._watched(name, coro_factory))
        entry["task"] = task
        entry["status"] = "running"
        self._start_times[name] = time.time()

    async def _watched(self, name: str, coro_factory) -> None:
        try:
            await coro_factory()
        except asyncio.CancelledError:
            self._registry[name]["status"] = "cancelled"
            raise
        except Exception as exc:
            self._registry[name]["status"] = f"error:{type(exc).__name__}"
            self._restarts[name] = self._restarts.get(name, 0) + 1

    async def stop(self, name: str) -> None:
        entry = self._registry.get(name)
        if entry and entry["task"] and not entry["task"].done():
            entry["task"].cancel()
            try:
                await entry["task"]
            except (asyncio.CancelledError, Exception):
                pass
            entry["status"] = "stopped"
            entry["task"] = None

    async def stop_all(self) -> None:
        for name in list(self._registry.keys()):
            await self.stop(name)

    def status(self) -> dict:
        result = {}
        for name, entry in self._registry.items():
            task = entry["task"]
            uptime = None
            if name in self._start_times:
                uptime = round(time.time() - self._start_times[name], 1)
            result[name] = {
                "status": entry["status"],
                "running": task is not None and not task.done(),
                "restarts": self._restarts.get(name, 0),
                "uptime_seconds": uptime,
            }
        return {"component": "ProcessSupervisor", "processes": result, "healthy": True}

    def list_processes(self) -> list:
        return list(self._registry.keys())
