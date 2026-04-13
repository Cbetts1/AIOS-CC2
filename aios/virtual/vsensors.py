"""AI-OS Virtual Sensors - Simulates temperature, voltage, and load sensors."""
import random
import time
from datetime import datetime


class VirtualSensors:
    def __init__(self):
        self._tick_count = 0
        self._last_tick = None
        self._readings = {
            "cpu_temp": 42.0,
            "gpu_temp": 38.0,
            "motherboard_temp": 30.0,
            "cpu_voltage": 1.25,
            "ram_voltage": 1.35,
            "pcie_voltage": 3.3,
            "cpu_load": 15.0,
            "memory_load": 30.0,
            "disk_load": 5.0,
            "fan_rpm": 1200.0,
            "power_draw_watts": 45.0,
        }
        self._history = {k: [] for k in self._readings}
        self._init_time = time.time()

    def tick(self) -> None:
        self._tick_count += 1
        self._last_tick = time.time()
        self._update_sensors()

    def _update_sensors(self) -> None:
        base = {
            "cpu_temp": (35.0, 85.0, 0.5),
            "gpu_temp": (30.0, 80.0, 0.3),
            "motherboard_temp": (25.0, 50.0, 0.2),
            "cpu_voltage": (1.20, 1.35, 0.005),
            "ram_voltage": (1.30, 1.40, 0.002),
            "pcie_voltage": (3.25, 3.35, 0.01),
            "cpu_load": (5.0, 95.0, 2.0),
            "memory_load": (20.0, 80.0, 1.5),
            "disk_load": (0.0, 50.0, 1.0),
            "fan_rpm": (800.0, 2400.0, 50.0),
            "power_draw_watts": (30.0, 120.0, 2.0),
        }
        for sensor, (low, high, jitter) in base.items():
            current = self._readings[sensor]
            delta = random.uniform(-jitter, jitter)
            new_val = current + delta
            new_val = max(low, min(high, new_val))
            self._readings[sensor] = round(new_val, 3)
            history = self._history[sensor]
            history.append({"value": new_val, "ts": self._last_tick})
            if len(history) > 60:
                self._history[sensor] = history[-30:]

    def read(self, sensor_name: str) -> float:
        if sensor_name not in self._readings:
            raise KeyError(f"Sensor '{sensor_name}' not found. Available: {list(self._readings.keys())}")
        return self._readings[sensor_name]

    def read_all(self) -> dict:
        return dict(self._readings)

    def get_history(self, sensor_name: str) -> list:
        return list(self._history.get(sensor_name, []))

    def status(self) -> dict:
        return {
            "component": "VirtualSensors",
            "tick_count": self._tick_count,
            "sensor_count": len(self._readings),
            "readings": dict(self._readings),
            "last_tick": self._last_tick,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "healthy": True,
        }
