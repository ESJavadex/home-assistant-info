"""
CPU metric collector.

Collects:
- Total CPU usage percentage
- Per-core CPU usage
- CPU temperature (if available)
- CPU frequency
"""

import platform
import logging
from typing import List

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)


class CPUCollector(BaseCollector):
    """Collects CPU-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self.cpu_count = psutil.cpu_count() or 1
        self.cpu_model = self._get_cpu_model()
        self._has_temp = self._check_temperature_available()

        # Initialize CPU percent tracking
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(percpu=True, interval=None)

    def _get_cpu_model(self) -> str:
        """Get CPU model string."""
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":")[1].strip()
                    if line.startswith("Model"):  # Raspberry Pi
                        return line.split(":")[1].strip()
        except (FileNotFoundError, PermissionError):
            pass
        return platform.processor() or "Unknown"

    def _check_temperature_available(self) -> bool:
        """Check if temperature sensors are available."""
        try:
            temps = psutil.sensors_temperatures()
            return bool(temps)
        except Exception:
            return False

    def _get_cpu_temperature(self) -> float | None:
        """Get CPU temperature."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Try common temperature sensor names
            for sensor_name in ["coretemp", "cpu_thermal", "cpu-thermal", "k10temp", "zenpower"]:
                if sensor_name in temps and temps[sensor_name]:
                    return temps[sensor_name][0].current

            # Fallback to first available
            for readings in temps.values():
                if readings:
                    return readings[0].current
        except Exception as e:
            logger.debug(f"Failed to read CPU temperature: {e}")
        return None

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # Total CPU usage (non-blocking, uses cached values)
        cpu_percent = psutil.cpu_percent(interval=None)
        metrics.append(MetricValue(
            sensor_id="cpu_usage",
            state_topic=self._make_state_topic("cpu_usage"),
            value=round(cpu_percent, 1)
        ))

        # Per-core usage
        per_cpu = psutil.cpu_percent(percpu=True, interval=None)
        for i, usage in enumerate(per_cpu):
            metrics.append(MetricValue(
                sensor_id=f"cpu_core_{i}_usage",
                state_topic=self._make_state_topic(f"cpu_core_{i}_usage"),
                value=round(usage, 1)
            ))

        # CPU temperature (if available)
        if self._has_temp:
            temp = self._get_cpu_temperature()
            if temp is not None:
                metrics.append(MetricValue(
                    sensor_id="cpu_temperature",
                    state_topic=self._make_state_topic("cpu_temperature"),
                    value=round(temp, 1)
                ))

        # CPU frequency
        freq = psutil.cpu_freq()
        if freq:
            metrics.append(MetricValue(
                sensor_id="cpu_frequency",
                state_topic=self._make_state_topic("cpu_frequency"),
                value=round(freq.current)
            ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # Total CPU usage
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("cpu_usage"),
            name="CPU Usage",
            state_topic=self._make_state_topic("cpu_usage"),
            state_class="measurement",
            unit_of_measurement="%",
            icon="mdi:cpu-64-bit",
            suggested_display_precision=1
        ))

        # Per-core sensors
        for i in range(self.cpu_count):
            configs.append(SensorConfig(
                unique_id=self._make_unique_id(f"cpu_core_{i}_usage"),
                name=f"CPU Core {i} Usage",
                state_topic=self._make_state_topic(f"cpu_core_{i}_usage"),
                state_class="measurement",
                unit_of_measurement="%",
                icon="mdi:chip",
                entity_category="diagnostic",
                suggested_display_precision=1
            ))

        # CPU temperature
        if self._has_temp:
            configs.append(SensorConfig(
                unique_id=self._make_unique_id("cpu_temperature"),
                name="CPU Temperature",
                state_topic=self._make_state_topic("cpu_temperature"),
                device_class="temperature",
                state_class="measurement",
                unit_of_measurement="°C",
                suggested_display_precision=1
            ))

        # CPU frequency
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("cpu_frequency"),
            name="CPU Frequency",
            state_topic=self._make_state_topic("cpu_frequency"),
            device_class="frequency",
            state_class="measurement",
            unit_of_measurement="MHz",
            icon="mdi:speedometer"
        ))

        return configs
