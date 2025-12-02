"""
MQTT Publisher for Home Assistant Discovery.

Handles:
- Connection to MQTT broker (Mosquitto)
- Publishing discovery configurations
- Publishing state updates
- Availability management
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
import paho.mqtt.client as mqtt

from config import Config
from collectors.base import SensorConfig, MetricValue

logger = logging.getLogger(__name__)

DISCOVERY_PREFIX = "homeassistant"


class MQTTPublisher:
    """Manages MQTT connection and message publishing."""

    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._availability_topic = f"{config.mqtt_topic_prefix}/status"
        self._connect_event = asyncio.Event()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            # Publish availability
            self.client.publish(self._availability_topic, "online", retain=True)
            self._connect_event.set()
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        self._connect_event.clear()
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")

    async def connect(self):
        """Connect to MQTT broker."""
        self.client = mqtt.Client(
            client_id=f"system_monitor_pro_{self.config.hostname}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Set credentials if provided
        if self.config.mqtt_username and self.config.mqtt_password:
            self.client.username_pw_set(
                self.config.mqtt_username,
                self.config.mqtt_password
            )

        # Set last will (availability offline)
        self.client.will_set(
            self._availability_topic,
            payload="offline",
            retain=True
        )

        # Connect
        logger.info(f"Connecting to MQTT broker at {self.config.mqtt_host}:{self.config.mqtt_port}")
        self.client.connect_async(
            self.config.mqtt_host,
            self.config.mqtt_port
        )
        self.client.loop_start()

        # Wait for connection with timeout
        try:
            await asyncio.wait_for(self._connect_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            raise ConnectionError("Failed to connect to MQTT broker within 30 seconds")

    async def disconnect(self):
        """Gracefully disconnect."""
        if self.client:
            self.client.publish(self._availability_topic, "offline", retain=True)
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

    async def publish_discovery(
        self,
        device_config: Dict[str, Any],
        sensor_configs: List[SensorConfig]
    ):
        """Publish MQTT discovery messages for all sensors."""
        logger.info(f"Publishing discovery for {len(sensor_configs)} sensors...")

        for sensor in sensor_configs:
            # Determine component type (sensor or binary_sensor)
            component = "binary_sensor" if sensor.is_binary else "sensor"
            topic = f"{DISCOVERY_PREFIX}/{component}/{sensor.unique_id}/config"

            payload = {
                "name": sensor.name,
                "unique_id": sensor.unique_id,
                "state_topic": sensor.state_topic,
                "availability_topic": self._availability_topic,
                "device": device_config,
            }

            # Add optional fields
            if sensor.device_class:
                payload["device_class"] = sensor.device_class
            if sensor.state_class:
                payload["state_class"] = sensor.state_class
            if sensor.unit_of_measurement:
                payload["unit_of_measurement"] = sensor.unit_of_measurement
            if sensor.icon:
                payload["icon"] = sensor.icon
            if sensor.entity_category:
                payload["entity_category"] = sensor.entity_category
            if sensor.value_template:
                payload["value_template"] = sensor.value_template
            if sensor.suggested_display_precision is not None:
                payload["suggested_display_precision"] = sensor.suggested_display_precision
            if sensor.json_attributes_topic:
                payload["json_attributes_topic"] = sensor.json_attributes_topic

            # Binary sensor specific
            if sensor.is_binary:
                payload["payload_on"] = "on"
                payload["payload_off"] = "off"

            self.client.publish(topic, json.dumps(payload), retain=True)
            logger.debug(f"Published discovery for {sensor.name}")

        logger.info("Discovery messages published successfully")

    async def publish_states(self, metrics: List[MetricValue]):
        """Publish state updates for collected metrics."""
        for metric in metrics:
            # Publish main state
            self.client.publish(metric.state_topic, str(metric.value), retain=False)

            # Publish attributes if any
            if metric.attributes and metric.attributes_topic:
                self.client.publish(
                    metric.attributes_topic,
                    json.dumps(metric.attributes),
                    retain=False
                )

    async def publish_alert(self, sensor_id: str, name: str, value: Any, threshold: Any = None):
        """Publish an alert event."""
        alert_topic = f"{self.config.mqtt_topic_prefix}/alerts"

        message = {
            "sensor": sensor_id,
            "name": name,
            "value": value,
            "threshold": threshold
        }

        self.client.publish(alert_topic, json.dumps(message))
        logger.warning(f"Alert: {name} = {value} (threshold: {threshold})")
