"""AI-OS Builder Engine - Builds virtual components."""
import time
from datetime import datetime, timezone


class BuilderEngine:
    def __init__(self, state_registry=None):
        self._state = state_registry
        self._build_queue = []
        self._completed = []
        self._tick_count = 0
        self._last_tick = None

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        if self._build_queue:
            target = self._build_queue.pop(0)
            result = self._perform_build(target)
            self._completed.append(result)
            if self._state:
                self._state.set(f"build:{target}", result, namespace="builder")

    def build(self, target: str) -> dict:
        self._build_queue.append(target)
        if self._state:
            self._state.set(f"build_queued:{target}", {"queued_at": time.time()}, namespace="builder")
        return {"queued": target, "position": len(self._build_queue)}

    def _perform_build(self, target: str) -> dict:
        return {
            "target": target,
            "status": "success",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round((time.time() % 1) * 200 + 50, 2),
            "artifacts": [f"{target}.bin", f"{target}.map"],
        }

    def get_queue(self) -> list:
        return list(self._build_queue)

    def get_completed(self) -> list:
        return list(self._completed[-20:])

    def status(self) -> dict:
        return {
            "component": "BuilderEngine",
            "tick_count": self._tick_count,
            "queue_depth": len(self._build_queue),
            "completed_builds": len(self._completed),
            "last_tick": self._last_tick,
            "healthy": True,
        }
