"""
Device Registry for Home Assistant.

Creates the device entity that groups all sensors in the HA device registry.
"""

import platform
import logging
from typing import Dict, Any

from config import Config

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Manages the Home Assistant device entity for System Monitor Pro."""

    def __init__(self, config: Config):
        self.config = config
        self._device_config = None

    def _get_hardware_model(self) -> str:
        """Detect hardware model (Raspberry Pi or generic)."""
        # Try to detect Raspberry Pi model
        try:
            with open("/proc/device-tree/model", "r") as f:
                model = f.read().strip().rstrip('\x00')
                if model:
                    return model
        except (FileNotFoundError, PermissionError):
            pass

        # Fallback to generic platform info
        machine = platform.machine()
        system = platform.system()
        return f"{system} {machine}"

    def _get_os_version(self) -> str:
        """Get OS version string."""
        try:
            # Try to read from /etc/os-release
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=")[1].strip().strip('"')
        except (FileNotFoundError, PermissionError):
            pass

        return f"{platform.system()} {platform.release()}"

    def get_device_config(self) -> Dict[str, Any]:
        """Get the device configuration for MQTT Discovery."""
        if self._device_config is None:
            hardware_model = self._get_hardware_model()
            os_version = self._get_os_version()

            self._device_config = {
                "identifiers": [self.config.get_unique_id_prefix()],
                "name": f"System Monitor ({self.config.hostname})",
                "model": hardware_model,
                "manufacturer": "System Monitor Pro",
                "sw_version": "0.0.3",
                "hw_version": os_version,
                "configuration_url": f"homeassistant://hassio/addon/{self.config.mqtt_topic_prefix}/info"
            }

            logger.info(f"Device registered: {self._device_config['name']}")
            logger.info(f"Hardware model: {hardware_model}")
            logger.info(f"OS version: {os_version}")

        return self._device_config
