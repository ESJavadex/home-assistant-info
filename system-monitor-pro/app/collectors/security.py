"""
Security metric collector.

Collects:
- Open/listening ports
- Active network connections
- Connection states
"""

import logging
import os
import socket
from typing import List, Dict, Any, Optional
from collections import Counter

import psutil
import aiohttp

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)

# Supervisor API
SUPERVISOR_URL = "http://supervisor"
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

# Well-known system ports as fallback
SYSTEM_PORTS = {
    22: "SSH",
    53: "DNS",
    80: "HTTP",
    111: "RPC",
    443: "HTTPS",
    5353: "mDNS",
    5355: "LLMNR",
    8123: "Home Assistant",
}


class SecurityCollector(BaseCollector):
    """Collects security-related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._port_map: Dict[int, str] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
            "Content-Type": "application/json"
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _build_port_map(self) -> Dict[int, str]:
        """Build a mapping of ports to service names from Supervisor API."""
        port_map = dict(SYSTEM_PORTS)  # Start with system ports

        if not SUPERVISOR_TOKEN:
            return port_map

        try:
            session = await self._get_session()

            # Get all addons
            async with session.get(
                f"{SUPERVISOR_URL}/addons",
                headers=self._headers,
                timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    addons = data.get("data", {}).get("addons", [])

                    for addon in addons:
                        if not addon.get("installed"):
                            continue

                        name = addon.get("name", addon.get("slug", "unknown"))

                        # Get detailed addon info for port mappings
                        slug = addon.get("slug")
                        if slug:
                            try:
                                async with session.get(
                                    f"{SUPERVISOR_URL}/addons/{slug}/info",
                                    headers=self._headers,
                                    timeout=3
                                ) as addon_resp:
                                    if addon_resp.status == 200:
                                        addon_data = await addon_resp.json()
                                        addon_info = addon_data.get("data", {})

                                        # Get network ports
                                        network = addon_info.get("network", {})
                                        if network:
                                            for container_port, host_port in network.items():
                                                if host_port:
                                                    port_map[int(host_port)] = name

                                        # Get ingress port
                                        ingress_port = addon_info.get("ingress_port")
                                        if ingress_port:
                                            port_map[int(ingress_port)] = f"{name}"

                                        # Get webui port from webui URL
                                        webui = addon_info.get("webui")
                                        if webui and ":" in webui:
                                            try:
                                                port_str = webui.split(":")[-1].split("/")[0].replace("[", "").replace("]", "")
                                                if port_str.isdigit():
                                                    port_map[int(port_str)] = name
                                            except:
                                                pass

                            except Exception as e:
                                logger.debug(f"Could not get info for addon {slug}: {e}")

            logger.debug(f"Built port map with {len(port_map)} entries")

        except Exception as e:
            logger.warning(f"Could not fetch addon port mappings: {e}")

        return port_map

    def _get_listening_ports(self, port_map: Dict[int, str]) -> List[Dict[str, Any]]:
        """Get list of listening ports with service info."""
        listening = []
        seen_ports = set()  # Deduplicate by port

        try:
            connections = psutil.net_connections(kind='inet')

            for conn in connections:
                if conn.status == 'LISTEN':
                    port = conn.laddr.port

                    # Skip if we've already seen this port
                    if port in seen_ports:
                        continue
                    seen_ports.add(port)

                    protocol = 'tcp' if conn.type.name == 'SOCK_STREAM' else 'udp'

                    # Try to get process name from psutil
                    process_name = None
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            process_name = proc.name()
                            # Don't use generic process names
                            if process_name in ("python", "python3", "node", "java"):
                                process_name = None
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Use port map from Supervisor API
                    if not process_name:
                        process_name = port_map.get(port)

                    # Final fallback
                    if not process_name:
                        process_name = f"port-{port}"

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

        # Build port map from Supervisor API (maps ports to addon names)
        port_map = await self._build_port_map()

        # Get listening ports with service names
        listening_ports = self._get_listening_ports(port_map)
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
