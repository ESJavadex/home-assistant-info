"""
Configuration handler for System Monitor Pro.

Loads options from /data/options.json (standard HA add-on location).
Provides typed access to all configuration values with validation.
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional

OPTIONS_PATH = "/data/options.json"

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration container for System Monitor Pro."""

    # Update settings
    update_interval: int = 60

    # Alert thresholds
    cpu_threshold: int = 90
    memory_threshold: int = 85
    disk_threshold: int = 85
    temp_threshold: int = 80

    # Feature toggles
    enable_security_monitoring: bool = True
    enable_rpi_monitoring: bool = True
    enable_alerts: bool = True

    # Monitoring filters
    monitored_disks: List[str] = field(default_factory=list)

    # MQTT settings
    mqtt_topic_prefix: str = "system_monitor_pro"
    alert_cooldown: int = 300

    # MQTT connection (from Supervisor environment)
    mqtt_host: str = "core-mosquitto"
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None

    # System hostname
    hostname: str = "unknown"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from options.json and environment."""
        config = cls()

        # Load user options from add-on config
        if os.path.exists(OPTIONS_PATH):
            try:
                with open(OPTIONS_PATH) as f:
                    options = json.load(f)
                logger.info(f"Loaded options from {OPTIONS_PATH}")

                for key, value in options.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                        logger.debug(f"Set {key} = {value}")
            except Exception as e:
                logger.warning(f"Failed to load options: {e}")
        else:
            logger.info(f"No options file found at {OPTIONS_PATH}, using defaults")

        # Load MQTT credentials from Supervisor services (set by run.sh)
        config.mqtt_host = os.environ.get("MQTT_HOST", config.mqtt_host)
        config.mqtt_port = int(os.environ.get("MQTT_PORT", str(config.mqtt_port)))
        config.mqtt_username = os.environ.get("MQTT_USERNAME")
        config.mqtt_password = os.environ.get("MQTT_PASSWORD")

        # Get system hostname
        config.hostname = os.environ.get("SYSTEM_HOSTNAME", os.environ.get("HOSTNAME", "unknown"))

        logger.info(f"MQTT broker: {config.mqtt_host}:{config.mqtt_port}")
        logger.info(f"Update interval: {config.update_interval}s")
        logger.info(f"Hostname: {config.hostname}")

        return config

    def get_unique_id_prefix(self) -> str:
        """Get the prefix for unique IDs, including hostname."""
        # Sanitize hostname for use in unique IDs
        safe_hostname = self.hostname.replace("-", "_").replace(".", "_").lower()
        return f"system_monitor_pro_{safe_hostname}"
