"""AI-OS Aura Engine - Master orchestrator of all sub-engines."""
import time
from datetime import datetime, timezone

from aios.engine.builder import BuilderEngine
from aios.engine.repair import RepairEngine
from aios.engine.documentation import DocumentationEngine
from aios.engine.evolution import EvolutionEngine
from aios.engine.legal_cortex import LegalCortex


class AuraEngine:
    def __init__(self, state_registry=None):
        self._state = state_registry
        self._tick_count = 0
        self._boot_time = None
        self._last_tick = None

        self.builder = BuilderEngine(state_registry)
        self.repair = RepairEngine(state_registry)
        self.documentation = DocumentationEngine(state_registry)
        self.evolution = EvolutionEngine(state_registry)
        self.legal = LegalCortex(state_registry)

        self._sub_engines = [
            self.builder,
            self.repair,
            self.documentation,
            self.evolution,
            self.legal,
        ]

    def boot(self) -> dict:
        self._boot_time = time.time()
        if self._state:
            self._state.set("aura_boot_time", self._boot_time, namespace="aura")
            self._state.set("aura_status", "ONLINE", namespace="aura")
        return {
            "status": "ONLINE",
            "boot_time": datetime.now(timezone.utc).isoformat(),
            "sub_engines": [e.__class__.__name__ for e in self._sub_engines],
        }

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        for engine in self._sub_engines:
            try:
                engine.tick()
            except Exception as exc:
                if self._state:
                    self._state.set(
                        f"{engine.__class__.__name__}_error",
                        str(exc),
                        namespace="aura",
                    )
        if self._state:
            self._state.set("aura_tick", self._tick_count, namespace="aura")

    def uptime(self) -> float:
        if self._boot_time is None:
            return 0.0
        return round(time.time() - self._boot_time, 2)

    def status(self) -> dict:
        return {
            "component": "AuraEngine",
            "status": "ONLINE" if self._boot_time else "OFFLINE",
            "tick_count": self._tick_count,
            "uptime_seconds": self.uptime(),
            "last_tick": self._last_tick,
            "sub_engines": {
                e.__class__.__name__: e.status() for e in self._sub_engines
            },
            "healthy": self._boot_time is not None,
        }
