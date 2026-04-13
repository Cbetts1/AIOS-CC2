"""AI-OS Evolution Engine - Tracks component evolution and versions."""
import time
from datetime import datetime


class EvolutionEngine:
    def __init__(self, state_registry=None):
        self._state = state_registry
        self._tick_count = 0
        self._last_tick = None
        self._evolution_log = []
        self._versions = {}
        self._cycle = 0

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        if self._tick_count % 10 == 0:
            self._cycle += 1
            self._run_evolution_cycle()

    def _run_evolution_cycle(self) -> None:
        snapshot = {
            "cycle": self._cycle,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "components_tracked": len(self._versions),
        }
        self._evolution_log.append(snapshot)
        if len(self._evolution_log) > 100:
            self._evolution_log = self._evolution_log[-50:]
        if self._state:
            self._state.set("evolution_cycle", self._cycle, namespace="evolution")
            self._state.set("evolution_snapshot", snapshot, namespace="evolution")

    def evolve(self, component: str) -> dict:
        current_version = self._versions.get(component, {"major": 1, "minor": 0, "patch": 0})
        current_version["patch"] += 1
        if current_version["patch"] >= 100:
            current_version["patch"] = 0
            current_version["minor"] += 1
        if current_version["minor"] >= 10:
            current_version["minor"] = 0
            current_version["major"] += 1
        self._versions[component] = current_version
        version_str = f"{current_version['major']}.{current_version['minor']}.{current_version['patch']}"
        record = {
            "component": component,
            "version": version_str,
            "evolved_at": datetime.utcnow().isoformat() + "Z",
            "cycle": self._cycle,
        }
        self._evolution_log.append(record)
        if self._state:
            self._state.set(f"version:{component}", version_str, namespace="evolution")
        return record

    def get_version(self, component: str) -> str:
        v = self._versions.get(component, {"major": 1, "minor": 0, "patch": 0})
        return f"{v['major']}.{v['minor']}.{v['patch']}"

    def get_evolution_log(self) -> list:
        return list(self._evolution_log[-20:])

    def status(self) -> dict:
        return {
            "component": "EvolutionEngine",
            "tick_count": self._tick_count,
            "evolution_cycles": self._cycle,
            "components_tracked": len(self._versions),
            "last_tick": self._last_tick,
            "healthy": True,
        }
