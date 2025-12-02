"""
Security metric collector.

Collects:
- Open/listening ports
- Active network connections
- Connection states
"""

import logging
from typing import List, Dict, Any
from collections import Counter

import psutil

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)


class SecurityCollector(BaseCollector):
    """Collects security-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)

    def _get_listening_ports(self) -> List[Dict[str, Any]]:
        """Get list of listening ports with service info."""
        listening = []

        try:
            connections = psutil.net_connections(kind='inet')

            for conn in connections:
                if conn.status == 'LISTEN':
                    port = conn.laddr.port
                    protocol = 'tcp' if conn.type.name == 'SOCK_STREAM' else 'udp'

                    # Try to get process name
                    process_name = "unknown"
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            process_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    listening.append({
                        "port": port,
                        "protocol": protocol,
                        "address": conn.laddr.ip,
                        "service": process_name,
                        "pid": conn.pid
                    })

        except (psutil.AccessDenied, OSError) as e:
            logger.warning(f"Limited access to connection info: {e}")

        # Sort by port number
        listening.sort(key=lambda x: x["port"])
        return listening

    def _get_connection_stats(self) -> Dict[str, int]:
        """Get connection statistics by state."""
        stats = Counter()

        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                stats[conn.status] += 1
        except (psutil.AccessDenied, OSError) as e:
            logger.warning(f"Limited access to connection info: {e}")

        return dict(stats)

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # Get listening ports
        listening_ports = self._get_listening_ports()
        open_ports_count = len(listening_ports)

        metrics.append(MetricValue(
            sensor_id="open_ports",
            state_topic=self._make_state_topic("open_ports"),
            value=open_ports_count,
            attributes={
                "ports": listening_ports[:50]  # Limit to 50 for attribute size
            },
            attributes_topic=self._make_attributes_topic("open_ports")
        ))

        # Get connection statistics
        conn_stats = self._get_connection_stats()

        # Total active connections (ESTABLISHED)
        established = conn_stats.get("ESTABLISHED", 0)
        metrics.append(MetricValue(
            sensor_id="active_connections",
            state_topic=self._make_state_topic("active_connections"),
            value=established,
            attributes=conn_stats,
            attributes_topic=self._make_attributes_topic("active_connections")
        ))

        # Total connections
        total_connections = sum(conn_stats.values())
        metrics.append(MetricValue(
            sensor_id="total_connections",
            state_topic=self._make_state_topic("total_connections"),
            value=total_connections
        ))

        # Listening sockets (LISTEN state)
        listening = conn_stats.get("LISTEN", 0)
        metrics.append(MetricValue(
            sensor_id="listening_sockets",
            state_topic=self._make_state_topic("listening_sockets"),
            value=listening
        ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # Open ports count
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("open_ports"),
            name="Open Ports",
            state_topic=self._make_state_topic("open_ports"),
            state_class="measurement",
            icon="mdi:lan-connect",
            json_attributes_topic=self._make_attributes_topic("open_ports")
        ))

        # Active connections (ESTABLISHED)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("active_connections"),
            name="Active Connections",
            state_topic=self._make_state_topic("active_connections"),
            state_class="measurement",
            icon="mdi:lan-pending",
            json_attributes_topic=self._make_attributes_topic("active_connections")
        ))

        # Total connections
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("total_connections"),
            name="Total Connections",
            state_topic=self._make_state_topic("total_connections"),
            state_class="measurement",
            icon="mdi:lan",
            entity_category="diagnostic"
        ))

        # Listening sockets
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("listening_sockets"),
            name="Listening Sockets",
            state_topic=self._make_state_topic("listening_sockets"),
            state_class="measurement",
            icon="mdi:server-network",
            entity_category="diagnostic"
        ))

        return configs
