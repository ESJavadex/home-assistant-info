"""
Alert Manager for threshold-based notifications.

Monitors metrics against configured thresholds and triggers alerts
when values exceed limits. Implements cooldown to prevent notification spam.
"""

import time
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config
    from mqtt_publisher import MQTTPublisher
    from collectors.base import MetricValue

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages threshold alerts and notifications."""

    # Mapping of sensor_id to (config_threshold_key, display_name, comparison_type)
    # comparison_type: "greater" = alert when value > threshold, "binary" = alert when value is "on"
    THRESHOLD_CONFIG = {
        "cpu_usage": ("cpu_threshold", "CPU Usage", "greater"),
        "memory_usage": ("memory_threshold", "Memory Usage", "greater"),
        "cpu_temperature": ("temp_threshold", "CPU Temperature", "greater"),
        "rpi_gpu_temperature": ("temp_threshold", "GPU Temperature", "greater"),
        "rpi_under_voltage": (None, "Under Voltage", "binary"),
        "rpi_throttled": (None, "Thermal Throttling", "binary"),
        "rpi_temp_limited": (None, "Temperature Limited", "binary"),
    }

    # Disk usage is handled specially (matches disk_*_usage pattern)
    DISK_USAGE_PATTERN = "_usage"

    def __init__(self, config: "Config", mqtt: "MQTTPublisher"):
        self.config = config
        self.mqtt = mqtt
        self.last_alerts: Dict[str, float] = {}
        self._alert_states: Dict[str, bool] = {}  # Track current alert state

    def _should_alert(self, sensor_id: str) -> bool:
        """Check if enough time has passed since the last alert for this sensor."""
        current_time = time.time()
        last_alert_time = self.last_alerts.get(sensor_id, 0)
        return (current_time - last_alert_time) >= self.config.alert_cooldown

    def _get_threshold_for_sensor(self, sensor_id: str) -> Optional[tuple]:
        """
        Get threshold configuration for a sensor.
        Returns (threshold_value, display_name, comparison_type) or None.
        """
        # Check direct mapping
        if sensor_id in self.THRESHOLD_CONFIG:
            threshold_key, display_name, comparison_type = self.THRESHOLD_CONFIG[sensor_id]
            if threshold_key:
                threshold_value = getattr(self.config, threshold_key, None)
                return (threshold_value, display_name, comparison_type)
            else:
                # Binary sensor (no threshold value)
                return (None, display_name, comparison_type)

        # Check for disk usage pattern
        if sensor_id.startswith("disk_") and sensor_id.endswith("_usage"):
            return (self.config.disk_threshold, f"Disk Usage ({sensor_id})", "greater")

        return None

    async def check_thresholds(self, metrics: List["MetricValue"]):
        """Check all metrics against thresholds and trigger alerts."""
        if not self.config.enable_alerts:
            return

        current_time = time.time()

        for metric in metrics:
            threshold_config = self._get_threshold_for_sensor(metric.sensor_id)
            if threshold_config is None:
                continue

            threshold_value, display_name, comparison_type = threshold_config

            # Determine if alert condition is met
            alert_condition = False

            if comparison_type == "binary":
                alert_condition = metric.value == "on"
            elif comparison_type == "greater" and threshold_value is not None:
                try:
                    alert_condition = float(metric.value) > threshold_value
                except (ValueError, TypeError):
                    continue

            # Track state changes
            previous_state = self._alert_states.get(metric.sensor_id, False)
            self._alert_states[metric.sensor_id] = alert_condition

            # Only alert on transition to alert state (rising edge)
            # or if in alert state and cooldown has passed
            should_send = False

            if alert_condition:
                if not previous_state:
                    # New alert (rising edge)
                    should_send = True
                elif self._should_alert(metric.sensor_id):
                    # Recurring alert after cooldown
                    should_send = True

            if should_send:
                await self._send_alert(
                    metric.sensor_id,
                    display_name,
                    metric.value,
                    threshold_value
                )
                self.last_alerts[metric.sensor_id] = current_time

    async def _send_alert(
        self,
        sensor_id: str,
        name: str,
        value: Any,
        threshold: Optional[Any] = None
    ):
        """Send alert notification."""
        # Log the alert
        if threshold is not None:
            logger.warning(f"ALERT: {name} = {value} (threshold: {threshold})")
        else:
            logger.warning(f"ALERT: {name} is active")

        # Publish alert via MQTT
        await self.mqtt.publish_alert(sensor_id, name, value, threshold)

    def get_active_alerts(self) -> Dict[str, bool]:
        """Get currently active alert states."""
        return {k: v for k, v in self._alert_states.items() if v}
