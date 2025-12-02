"""
Memory metric collector.

Collects:
- Total memory
- Used memory
- Available memory
- Memory usage percentage
- Swap usage (if available)
"""

import logging
from typing import List

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)


class MemoryCollector(BaseCollector):
    """Collects memory-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._has_swap = self._check_swap_available()

    def _check_swap_available(self) -> bool:
        """Check if swap is available."""
        try:
            swap = psutil.swap_memory()
            return swap.total > 0
        except Exception:
            return False

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # Virtual memory
        mem = psutil.virtual_memory()

        # Memory usage percentage
        metrics.append(MetricValue(
            sensor_id="memory_usage",
            state_topic=self._make_state_topic("memory_usage"),
            value=round(mem.percent, 1)
        ))

        # Total memory (GB)
        metrics.append(MetricValue(
            sensor_id="memory_total",
            state_topic=self._make_state_topic("memory_total"),
            value=round(mem.total / (1024**3), 2)
        ))

        # Used memory (GB)
        metrics.append(MetricValue(
            sensor_id="memory_used",
            state_topic=self._make_state_topic("memory_used"),
            value=round(mem.used / (1024**3), 2)
        ))

        # Available memory (GB)
        metrics.append(MetricValue(
            sensor_id="memory_available",
            state_topic=self._make_state_topic("memory_available"),
            value=round(mem.available / (1024**3), 2)
        ))

        # Swap memory (if available)
        if self._has_swap:
            swap = psutil.swap_memory()
            metrics.append(MetricValue(
                sensor_id="swap_usage",
                state_topic=self._make_state_topic("swap_usage"),
                value=round(swap.percent, 1)
            ))
            metrics.append(MetricValue(
                sensor_id="swap_used",
                state_topic=self._make_state_topic("swap_used"),
                value=round(swap.used / (1024**3), 2)
            ))
            metrics.append(MetricValue(
                sensor_id="swap_total",
                state_topic=self._make_state_topic("swap_total"),
                value=round(swap.total / (1024**3), 2)
            ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # Memory usage percentage
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("memory_usage"),
            name="Memory Usage",
            state_topic=self._make_state_topic("memory_usage"),
            state_class="measurement",
            unit_of_measurement="%",
            icon="mdi:memory",
            suggested_display_precision=1
        ))

        # Total memory
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("memory_total"),
            name="Memory Total",
            state_topic=self._make_state_topic("memory_total"),
            device_class="data_size",
            state_class="measurement",
            unit_of_measurement="GB",
            icon="mdi:memory",
            entity_category="diagnostic",
            suggested_display_precision=2
        ))

        # Used memory
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("memory_used"),
            name="Memory Used",
            state_topic=self._make_state_topic("memory_used"),
            device_class="data_size",
            state_class="measurement",
            unit_of_measurement="GB",
            icon="mdi:memory",
            suggested_display_precision=2
        ))

        # Available memory
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("memory_available"),
            name="Memory Available",
            state_topic=self._make_state_topic("memory_available"),
            device_class="data_size",
            state_class="measurement",
            unit_of_measurement="GB",
            icon="mdi:memory",
            suggested_display_precision=2
        ))

        # Swap sensors (if available)
        if self._has_swap:
            configs.append(SensorConfig(
                unique_id=self._make_unique_id("swap_usage"),
                name="Swap Usage",
                state_topic=self._make_state_topic("swap_usage"),
                state_class="measurement",
                unit_of_measurement="%",
                icon="mdi:harddisk",
                entity_category="diagnostic",
                suggested_display_precision=1
            ))
            configs.append(SensorConfig(
                unique_id=self._make_unique_id("swap_used"),
                name="Swap Used",
                state_topic=self._make_state_topic("swap_used"),
                device_class="data_size",
                state_class="measurement",
                unit_of_measurement="GB",
                icon="mdi:harddisk",
                entity_category="diagnostic",
                suggested_display_precision=2
            ))
            configs.append(SensorConfig(
                unique_id=self._make_unique_id("swap_total"),
                name="Swap Total",
                state_topic=self._make_state_topic("swap_total"),
                device_class="data_size",
                state_class="measurement",
                unit_of_measurement="GB",
                icon="mdi:harddisk",
                entity_category="diagnostic",
                suggested_display_precision=2
            ))

        return configs
