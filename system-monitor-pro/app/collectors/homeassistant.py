"""
Home Assistant metric collector.

Collects:
- Running add-ons count and details
- Entity count
- Automation count
- Script count
- Core info
"""

import logging
import os
from typing import List, Dict, Any, Optional

import aiohttp

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)

# Supervisor API base URL (available inside add-ons)
SUPERVISOR_URL = "http://supervisor"
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")


class HomeAssistantCollector(BaseCollector):
    """Collects Home Assistant related metrics."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
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

    async def _api_call(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a call to the Supervisor API."""
        if not SUPERVISOR_TOKEN:
            logger.debug("No SUPERVISOR_TOKEN available, skipping HA metrics")
            return None

        try:
            session = await self._get_session()
            url = f"{SUPERVISOR_URL}{endpoint}"
            async with session.get(url, headers=self._headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.warning(f"Supervisor API returned {response.status} for {endpoint}")
                    return None
        except aiohttp.ClientError as e:
            logger.warning(f"Failed to call Supervisor API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Supervisor API: {e}")
            return None

    async def _get_addons(self) -> List[Dict[str, Any]]:
        """Get list of installed add-ons."""
        data = await self._api_call("/addons")
        if data and "addons" in data:
            return data["addons"]
        return []

    async def _get_core_info(self) -> Optional[Dict[str, Any]]:
        """Get Home Assistant Core info."""
        return await self._api_call("/core/info")

    async def _get_supervisor_info(self) -> Optional[Dict[str, Any]]:
        """Get Supervisor info."""
        return await self._api_call("/supervisor/info")

    async def _get_host_info(self) -> Optional[Dict[str, Any]]:
        """Get Host info."""
        return await self._api_call("/host/info")

    async def _count_entities(self, core_info: Optional[Dict]) -> int:
        """Try to get entity count from Core API."""
        # This requires homeassistant_api: true in config
        try:
            session = await self._get_session()
            url = f"{SUPERVISOR_URL}/core/api/states"
            async with session.get(url, headers=self._headers, timeout=10) as response:
                if response.status == 200:
                    states = await response.json()
                    return len(states)
        except Exception as e:
            logger.debug(f"Could not get entity count: {e}")
        return 0

    async def _count_automations(self) -> int:
        """Count automations via Core API."""
        try:
            session = await self._get_session()
            url = f"{SUPERVISOR_URL}/core/api/states"
            async with session.get(url, headers=self._headers, timeout=10) as response:
                if response.status == 200:
                    states = await response.json()
                    return sum(1 for s in states if s.get("entity_id", "").startswith("automation."))
        except Exception as e:
            logger.debug(f"Could not count automations: {e}")
        return 0

    async def _count_scripts(self) -> int:
        """Count scripts via Core API."""
        try:
            session = await self._get_session()
            url = f"{SUPERVISOR_URL}/core/api/states"
            async with session.get(url, headers=self._headers, timeout=10) as response:
                if response.status == 200:
                    states = await response.json()
                    return sum(1 for s in states if s.get("entity_id", "").startswith("script."))
        except Exception as e:
            logger.debug(f"Could not count scripts: {e}")
        return 0

    async def collect(self) -> List[MetricValue]:
        metrics = []

        # Get add-ons info
        addons = await self._get_addons()

        # Log add-on states for debugging
        if addons:
            states = set(a.get("state", "unknown") for a in addons)
            logger.debug(f"Found {len(addons)} add-ons with states: {states}")

        # Filter running add-ons (check multiple possible state values)
        running_addons = [a for a in addons if a.get("state") in ("started", "running", True)]

        # If no running found, show all installed add-ons
        display_addons = running_addons if running_addons else addons

        metrics.append(MetricValue(
            sensor_id="ha_addons_running",
            state_topic=self._make_state_topic("ha_addons_running"),
            value=len(running_addons) if running_addons else len(addons),
            attributes={
                "addons": [
                    {
                        "name": a.get("name", "Unknown"),
                        "slug": a.get("slug", ""),
                        "version": a.get("version", ""),
                        "state": a.get("state", "unknown"),
                        "installed": a.get("installed", False)
                    }
                    for a in display_addons if a.get("installed", False)
                ],
                "total_installed": sum(1 for a in addons if a.get("installed", False))
            },
            attributes_topic=self._make_attributes_topic("ha_addons_running")
        ))

        # Get Core info
        core_info = await self._get_core_info()
        if core_info:
            metrics.append(MetricValue(
                sensor_id="ha_core_version",
                state_topic=self._make_state_topic("ha_core_version"),
                value=core_info.get("version", "unknown"),
                attributes={
                    "arch": core_info.get("arch", ""),
                    "machine": core_info.get("machine", ""),
                    "image": core_info.get("image", "")
                },
                attributes_topic=self._make_attributes_topic("ha_core_version")
            ))

        # Count entities
        entity_count = await self._count_entities(core_info)
        if entity_count > 0:
            metrics.append(MetricValue(
                sensor_id="ha_entities",
                state_topic=self._make_state_topic("ha_entities"),
                value=entity_count
            ))

        # Count automations
        automation_count = await self._count_automations()
        metrics.append(MetricValue(
            sensor_id="ha_automations",
            state_topic=self._make_state_topic("ha_automations"),
            value=automation_count
        ))

        # Count scripts
        script_count = await self._count_scripts()
        metrics.append(MetricValue(
            sensor_id="ha_scripts",
            state_topic=self._make_state_topic("ha_scripts"),
            value=script_count
        ))

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        configs = []

        # Running add-ons
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("ha_addons_running"),
            name="HA Running Add-ons",
            state_topic=self._make_state_topic("ha_addons_running"),
            state_class="measurement",
            icon="mdi:puzzle",
            json_attributes_topic=self._make_attributes_topic("ha_addons_running")
        ))

        # Core version
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("ha_core_version"),
            name="HA Core Version",
            state_topic=self._make_state_topic("ha_core_version"),
            icon="mdi:home-assistant",
            json_attributes_topic=self._make_attributes_topic("ha_core_version")
        ))

        # Entity count
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("ha_entities"),
            name="HA Entity Count",
            state_topic=self._make_state_topic("ha_entities"),
            state_class="measurement",
            icon="mdi:format-list-bulleted"
        ))

        # Automation count
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("ha_automations"),
            name="HA Automations",
            state_topic=self._make_state_topic("ha_automations"),
            state_class="measurement",
            icon="mdi:robot"
        ))

        # Script count
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("ha_scripts"),
            name="HA Scripts",
            state_topic=self._make_state_topic("ha_scripts"),
            state_class="measurement",
            icon="mdi:script-text"
        ))

        return configs

    async def cleanup(self):
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
