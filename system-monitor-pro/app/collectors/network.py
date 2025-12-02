"""
Network metric collector.

Collects:
- Network bytes sent/received (total)
- Network interfaces and their IP addresses
- Network errors and dropped packets
"""

import logging
from typing import List, Dict, Any

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)

# Interfaces to exclude
EXCLUDED_INTERFACES = {"lo", "localhost"}


class NetworkCollector(BaseCollector):
    """Collects network-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._interfaces = self._get_interfaces()

    def _get_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get network interfaces with their addresses."""
        interfaces = {}

        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for iface_name, iface_addrs in addrs.items():
                # Skip excluded interfaces
                if iface_name.lower() in EXCLUDED_INTERFACES:
                    continue

                # Skip interfaces that are down
                if iface_name in stats and not stats[iface_name].isup:
                    continue

                ipv4 = None
                ipv6 = None
                mac = None

                for addr in iface_addrs:
                    if addr.family.name == "AF_INET":
                        ipv4 = addr.address
                    elif addr.family.name == "AF_INET6":
                        # Skip link-local IPv6
                        if not addr.address.startswith("fe80"):
                            ipv6 = addr.address
                    elif addr.family.name == "AF_PACKET":
                        mac = addr.address

                if ipv4 or ipv6:
                    interfaces[iface_name] = {
                        "ipv4": ipv4,
                        "ipv6": ipv6,
                        "mac": mac
                    }
                    logger.debug(f"Found interface: {iface_name} - IPv4: {ipv4}, IPv6: {ipv6}")

        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")

        logger.info(f"Monitoring {len(interfaces)} network interfaces")
        return interfaces

    def _get_primary_ip(self) -> str:
        """Get the primary IP address."""
        for iface_name, info in self._interfaces.items():
            if info["ipv4"] and not info["ipv4"].startswith("127."):
                return info["ipv4"]
        return "unknown"

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # Network I/O counters (total)
        net_io = psutil.net_io_counters()

        # Bytes sent (GB)
        metrics.append(MetricValue(
            sensor_id="network_bytes_sent",
            state_topic=self._make_state_topic("network_bytes_sent"),
            value=round(net_io.bytes_sent / (1024**3), 3)
        ))

        # Bytes received (GB)
        metrics.append(MetricValue(
            sensor_id="network_bytes_recv",
            state_topic=self._make_state_topic("network_bytes_recv"),
            value=round(net_io.bytes_recv / (1024**3), 3)
        ))

        # Packets sent
        metrics.append(MetricValue(
            sensor_id="network_packets_sent",
            state_topic=self._make_state_topic("network_packets_sent"),
            value=net_io.packets_sent
        ))

        # Packets received
        metrics.append(MetricValue(
            sensor_id="network_packets_recv",
            state_topic=self._make_state_topic("network_packets_recv"),
            value=net_io.packets_recv
        ))

        # Errors and drops (combined)
        total_errors = net_io.errin + net_io.errout
        total_drops = net_io.dropin + net_io.dropout
        metrics.append(MetricValue(
            sensor_id="network_errors",
            state_topic=self._make_state_topic("network_errors"),
            value=total_errors
        ))
        metrics.append(MetricValue(
            sensor_id="network_drops",
            state_topic=self._make_state_topic("network_drops"),
            value=total_drops
        ))

        # Primary IP address
        primary_ip = self._get_primary_ip()
        metrics.append(MetricValue(
            sensor_id="network_ip_address",
            state_topic=self._make_state_topic("network_ip_address"),
            value=primary_ip,
            attributes={
                "interfaces": {
                    name: info for name, info in self._interfaces.items()
                }
            },
            attributes_topic=self._make_attributes_topic("network_ip_address")
        ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # Bytes sent
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_bytes_sent"),
            name="Network Bytes Sent",
            state_topic=self._make_state_topic("network_bytes_sent"),
            device_class="data_size",
            state_class="total_increasing",
            unit_of_measurement="GB",
            icon="mdi:upload-network",
            suggested_display_precision=3
        ))

        # Bytes received
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_bytes_recv"),
            name="Network Bytes Received",
            state_topic=self._make_state_topic("network_bytes_recv"),
            device_class="data_size",
            state_class="total_increasing",
            unit_of_measurement="GB",
            icon="mdi:download-network",
            suggested_display_precision=3
        ))

        # Packets sent
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_packets_sent"),
            name="Network Packets Sent",
            state_topic=self._make_state_topic("network_packets_sent"),
            state_class="total_increasing",
            icon="mdi:upload-network",
            entity_category="diagnostic"
        ))

        # Packets received
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_packets_recv"),
            name="Network Packets Received",
            state_topic=self._make_state_topic("network_packets_recv"),
            state_class="total_increasing",
            icon="mdi:download-network",
            entity_category="diagnostic"
        ))

        # Errors
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_errors"),
            name="Network Errors",
            state_topic=self._make_state_topic("network_errors"),
            state_class="total_increasing",
            icon="mdi:alert-circle",
            entity_category="diagnostic"
        ))

        # Drops
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_drops"),
            name="Network Drops",
            state_topic=self._make_state_topic("network_drops"),
            state_class="total_increasing",
            icon="mdi:alert-circle",
            entity_category="diagnostic"
        ))

        # Primary IP address
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("network_ip_address"),
            name="IP Address",
            state_topic=self._make_state_topic("network_ip_address"),
            icon="mdi:ip-network",
            json_attributes_topic=self._make_attributes_topic("network_ip_address")
        ))

        return configs
