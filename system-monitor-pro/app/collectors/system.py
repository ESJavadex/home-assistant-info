"""
System info metric collector.

Collects:
- System uptime
- OS version
- Kernel version
- Architecture
- Process count
- Load average
"""

import platform
import logging
from typing import List
from datetime import datetime

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)


class SystemCollector(BaseCollector):
    """Collects system information metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._static_info = self._get_static_info()

    def _get_static_info(self) -> dict:
        """Get static system information (collected once)."""
        info = {
            "os": platform.system(),
            "os_version": self._get_os_version(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "cpu_model": self._get_cpu_model(),
            "python_version": platform.python_version()
        }
        return info

    def _get_os_version(self) -> str:
        """Get detailed OS version."""
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=")[1].strip().strip('"')
        except (FileNotFoundError, PermissionError):
            pass
        return f"{platform.system()} {platform.release()}"

    def _get_cpu_model(self) -> str:
        """Get CPU model string."""
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":")[1].strip()
                    if line.startswith("Model"):
                        return line.split(":")[1].strip()
        except (FileNotFoundError, PermissionError):
            pass
        return platform.processor() or "Unknown"

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # System uptime (seconds)
        boot_time = psutil.boot_time()
        uptime_seconds = int(datetime.now().timestamp() - boot_time)
        metrics.append(MetricValue(
            sensor_id="uptime",
            state_topic=self._make_state_topic("uptime"),
            value=uptime_seconds
        ))

        # Process count
        process_count = len(psutil.pids())
        metrics.append(MetricValue(
            sensor_id="process_count",
            state_topic=self._make_state_topic("process_count"),
            value=process_count
        ))

        # Load average (1, 5, 15 minutes)
        try:
            load1, load5, load15 = psutil.getloadavg()
            metrics.append(MetricValue(
                sensor_id="load_1m",
                state_topic=self._make_state_topic("load_1m"),
                value=round(load1, 2)
            ))
            metrics.append(MetricValue(
                sensor_id="load_5m",
                state_topic=self._make_state_topic("load_5m"),
                value=round(load5, 2)
            ))
            metrics.append(MetricValue(
                sensor_id="load_15m",
                state_topic=self._make_state_topic("load_15m"),
                value=round(load15, 2)
            ))
        except (AttributeError, OSError):
            # Load average not available on all platforms
            pass

        # System info (with attributes)
        metrics.append(MetricValue(
            sensor_id="system_info",
            state_topic=self._make_state_topic("system_info"),
            value=self._static_info["os_version"],
            attributes=self._static_info,
            attributes_topic=self._make_attributes_topic("system_info")
        ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # System uptime
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("uptime"),
            name="System Uptime",
            state_topic=self._make_state_topic("uptime"),
            device_class="duration",
            state_class="total_increasing",
            unit_of_measurement="s",
            icon="mdi:clock-outline"
        ))

        # Process count
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("process_count"),
            name="Process Count",
            state_topic=self._make_state_topic("process_count"),
            state_class="measurement",
            icon="mdi:format-list-numbered",
            entity_category="diagnostic"
        ))

        # Load averages
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("load_1m"),
            name="Load Average 1m",
            state_topic=self._make_state_topic("load_1m"),
            state_class="measurement",
            icon="mdi:gauge",
            suggested_display_precision=2
        ))
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("load_5m"),
            name="Load Average 5m",
            state_topic=self._make_state_topic("load_5m"),
            state_class="measurement",
            icon="mdi:gauge",
            entity_category="diagnostic",
            suggested_display_precision=2
        ))
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("load_15m"),
            name="Load Average 15m",
            state_topic=self._make_state_topic("load_15m"),
            state_class="measurement",
            icon="mdi:gauge",
            entity_category="diagnostic",
            suggested_display_precision=2
        ))

        # System info
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("system_info"),
            name="System Info",
            state_topic=self._make_state_topic("system_info"),
            icon="mdi:information",
            entity_category="diagnostic",
            json_attributes_topic=self._make_attributes_topic("system_info")
        ))

        return configs
