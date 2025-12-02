"""
Collector Registry for System Monitor Pro.

Manages all metric collectors and provides a unified interface for collection.
"""

import logging
from typing import List, TYPE_CHECKING

from .base import SensorConfig, MetricValue
from .cpu import CPUCollector
from .memory import MemoryCollector
from .disk import DiskCollector
from .network import NetworkCollector
from .security import SecurityCollector
from .system import SystemCollector
from .rpi import RPiCollector
from .homeassistant import HomeAssistantCollector

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)

__all__ = [
    "SensorConfig",
    "MetricValue",
    "CollectorRegistry",
]


class CollectorRegistry:
    """Registry of all metric collectors."""

    def __init__(self, config: "Config"):
        self.config = config
        self._collectors = []
        self._initialize_collectors()

    def _initialize_collectors(self):
        """Initialize all available collectors."""
        topic_prefix = self.config.mqtt_topic_prefix
        unique_id_prefix = self.config.get_unique_id_prefix()

        # Core collectors (always available)
        collector_classes = [
            CPUCollector,
            MemoryCollector,
            DiskCollector,
            SystemCollector,
        ]

        # Network collector
        collector_classes.append(NetworkCollector)

        # Security collector (optional)
        if self.config.enable_security_monitoring:
            collector_classes.append(SecurityCollector)

        # Raspberry Pi collector (optional)
        if self.config.enable_rpi_monitoring:
            collector_classes.append(RPiCollector)

        # Home Assistant collector (always try to load)
        collector_classes.append(HomeAssistantCollector)

        # Instantiate collectors
        for collector_class in collector_classes:
            try:
                collector = collector_class(self.config, topic_prefix, unique_id_prefix)
                if collector.is_available():
                    self._collectors.append(collector)
                    logger.info(f"Initialized collector: {collector_class.__name__}")
                else:
                    logger.debug(f"Collector not available: {collector_class.__name__}")
            except Exception as e:
                logger.warning(f"Failed to initialize {collector_class.__name__}: {e}")

        logger.info(f"Active collectors: {len(self._collectors)}")

    def get_all_sensor_configs(self) -> List[SensorConfig]:
        """Get sensor configurations from all collectors."""
        configs = []
        for collector in self._collectors:
            try:
                configs.extend(collector.get_sensor_configs())
            except Exception as e:
                logger.error(f"Failed to get sensor configs from {type(collector).__name__}: {e}")
        return configs

    async def collect_all(self) -> List[MetricValue]:
        """Collect metrics from all collectors."""
        metrics = []
        for collector in self._collectors:
            try:
                collector_metrics = await collector.collect()
                metrics.extend(collector_metrics)
            except Exception as e:
                logger.error(f"Failed to collect from {type(collector).__name__}: {e}")
        return metrics
