"""
Disk metric collector.

Collects:
- Disk usage percentage (per filesystem)
- Disk free space (per filesystem)
- Disk total size (per filesystem)
"""

import logging
import re
from typing import List, Set

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)

# Filesystems to exclude (virtual, temporary, etc.)
EXCLUDED_FSTYPES = {
    "squashfs", "tmpfs", "devtmpfs", "overlay", "aufs",
    "proc", "sysfs", "devpts", "cgroup", "cgroup2",
    "securityfs", "debugfs", "tracefs", "configfs",
    "fusectl", "mqueue", "hugetlbfs", "pstore",
    "binfmt_misc", "rpc_pipefs", "nfsd", "autofs"
}


class DiskCollector(BaseCollector):
    """Collects disk-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._partitions = self._get_monitored_partitions()

    def _sanitize_mount_point(self, mount_point: str) -> str:
        """Convert mount point to a valid sensor ID."""
        if mount_point == "/":
            return "root"
        # Remove leading slash and replace special chars
        sanitized = mount_point.lstrip("/").replace("/", "_").replace("-", "_")
        # Remove any non-alphanumeric chars except underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
        return sanitized or "disk"

    def _get_monitored_partitions(self) -> List[dict]:
        """Get list of partitions to monitor."""
        partitions = []
        monitored_disks = set(self.config.monitored_disks) if self.config.monitored_disks else set()

        for partition in psutil.disk_partitions(all=False):
            # Skip excluded filesystem types
            if partition.fstype in EXCLUDED_FSTYPES:
                continue

            # Skip if user specified monitored_disks and this isn't in the list
            if monitored_disks and partition.mountpoint not in monitored_disks:
                continue

            # Try to get usage to verify partition is accessible
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.total > 0:
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "sensor_id": f"disk_{self._sanitize_mount_point(partition.mountpoint)}"
                    })
                    logger.debug(f"Monitoring disk: {partition.mountpoint} ({partition.device})")
            except (PermissionError, OSError) as e:
                logger.debug(f"Skipping inaccessible partition {partition.mountpoint}: {e}")

        logger.info(f"Monitoring {len(partitions)} disk partitions")
        return partitions

    async def collect(self) -> List[MetricValue]:
        metrics = []

        for partition in self._partitions:
            try:
                usage = psutil.disk_usage(partition["mountpoint"])
                sensor_id = partition["sensor_id"]

                # Disk usage percentage
                metrics.append(MetricValue(
                    sensor_id=f"{sensor_id}_usage",
                    state_topic=self._make_state_topic(f"{sensor_id}_usage"),
                    value=round(usage.percent, 1)
                ))

                # Disk free (GB)
                metrics.append(MetricValue(
                    sensor_id=f"{sensor_id}_free",
                    state_topic=self._make_state_topic(f"{sensor_id}_free"),
                    value=round(usage.free / (1024**3), 2)
                ))

                # Disk total (GB)
                metrics.append(MetricValue(
                    sensor_id=f"{sensor_id}_total",
                    state_topic=self._make_state_topic(f"{sensor_id}_total"),
                    value=round(usage.total / (1024**3), 2)
                ))

            except (PermissionError, OSError) as e:
                logger.debug(f"Failed to read disk {partition['mountpoint']}: {e}")

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        for partition in self._partitions:
            sensor_id = partition["sensor_id"]
            mountpoint = partition["mountpoint"]
            name_suffix = mountpoint if mountpoint != "/" else "Root"

            # Disk usage percentage
            configs.append(SensorConfig(
                unique_id=self._make_unique_id(f"{sensor_id}_usage"),
                name=f"Disk Usage {name_suffix}",
                state_topic=self._make_state_topic(f"{sensor_id}_usage"),
                state_class="measurement",
                unit_of_measurement="%",
                icon="mdi:harddisk",
                suggested_display_precision=1
            ))

            # Disk free
            configs.append(SensorConfig(
                unique_id=self._make_unique_id(f"{sensor_id}_free"),
                name=f"Disk Free {name_suffix}",
                state_topic=self._make_state_topic(f"{sensor_id}_free"),
                device_class="data_size",
                state_class="measurement",
                unit_of_measurement="GB",
                icon="mdi:harddisk",
                entity_category="diagnostic",
                suggested_display_precision=2
            ))

            # Disk total
            configs.append(SensorConfig(
                unique_id=self._make_unique_id(f"{sensor_id}_total"),
                name=f"Disk Total {name_suffix}",
                state_topic=self._make_state_topic(f"{sensor_id}_total"),
                device_class="data_size",
                state_class="measurement",
                unit_of_measurement="GB",
                icon="mdi:harddisk",
                entity_category="diagnostic",
                suggested_display_precision=2
            ))

        return configs
