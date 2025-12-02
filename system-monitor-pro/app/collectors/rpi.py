"""
Raspberry Pi specific collector.

Collects (via vcgencmd):
- Thermal throttling status
- Under-voltage warnings
- Soft temperature limit
- Core voltage
- GPU temperature
"""

import subprocess
import logging
from typing import List, Optional, Dict

from .base import BaseCollector, SensorConfig, MetricValue

logger = logging.getLogger(__name__)

# Throttled flag bit positions
THROTTLED_FLAGS = {
    "under_voltage": 0,
    "arm_frequency_capped": 1,
    "throttled": 2,
    "soft_temp_limit": 3,
    "under_voltage_occurred": 16,
    "arm_freq_capped_occurred": 17,
    "throttled_occurred": 18,
    "soft_temp_limit_occurred": 19,
}


class RPiCollector(BaseCollector):
    """Raspberry Pi specific metrics via vcgencmd."""

    def __init__(self, config, topic_prefix: str, unique_id_prefix: str):
        super().__init__(config, topic_prefix, unique_id_prefix)
        self._is_rpi = self._detect_raspberry_pi()
        if self._is_rpi:
            logger.info("Raspberry Pi detected - enabling RPi-specific sensors")

    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on a Raspberry Pi."""
        if not self.config.enable_rpi_monitoring:
            return False

        # Check for vcgencmd availability
        try:
            result = subprocess.run(
                ["vcgencmd", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> bool:
        return self._is_rpi

    def _run_vcgencmd(self, *args) -> Optional[str]:
        """Run vcgencmd and return output."""
        try:
            result = subprocess.run(
                ["vcgencmd", *args],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug(f"vcgencmd failed: {e}")
        return None

    def _parse_throttled(self, value: int) -> Dict[str, bool]:
        """Parse throttled status into individual flags."""
        return {
            name: bool(value & (1 << bit))
            for name, bit in THROTTLED_FLAGS.items()
        }

    async def collect(self) -> List[MetricValue]:
        if not self._is_rpi:
            return []

        metrics = []

        # Get throttled status
        throttled_output = self._run_vcgencmd("get_throttled")
        if throttled_output:
            try:
                # Format: throttled=0x50000
                value = int(throttled_output.split("=")[1], 16)
                flags = self._parse_throttled(value)

                # Current throttling state
                metrics.append(MetricValue(
                    sensor_id="rpi_throttled",
                    state_topic=self._make_state_topic("rpi_throttled"),
                    value="on" if flags["throttled"] else "off"
                ))

                # Under-voltage
                metrics.append(MetricValue(
                    sensor_id="rpi_under_voltage",
                    state_topic=self._make_state_topic("rpi_under_voltage"),
                    value="on" if flags["under_voltage"] else "off"
                ))

                # Soft temperature limit
                metrics.append(MetricValue(
                    sensor_id="rpi_temp_limited",
                    state_topic=self._make_state_topic("rpi_temp_limited"),
                    value="on" if flags["soft_temp_limit"] else "off"
                ))

                # Frequency capped
                metrics.append(MetricValue(
                    sensor_id="rpi_freq_capped",
                    state_topic=self._make_state_topic("rpi_freq_capped"),
                    value="on" if flags["arm_frequency_capped"] else "off"
                ))

                # Raw throttle value (for diagnostics)
                metrics.append(MetricValue(
                    sensor_id="rpi_throttle_raw",
                    state_topic=self._make_state_topic("rpi_throttle_raw"),
                    value=hex(value),
                    attributes=flags,
                    attributes_topic=self._make_attributes_topic("rpi_throttle_raw")
                ))

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse throttle status: {e}")

        # Get core voltage
        voltage_output = self._run_vcgencmd("measure_volts", "core")
        if voltage_output:
            try:
                # Format: volt=1.2000V
                voltage = float(voltage_output.split("=")[1].rstrip("V"))
                metrics.append(MetricValue(
                    sensor_id="rpi_core_voltage",
                    state_topic=self._make_state_topic("rpi_core_voltage"),
                    value=round(voltage, 4)
                ))
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse voltage: {e}")

        # Get GPU temperature
        temp_output = self._run_vcgencmd("measure_temp")
        if temp_output:
            try:
                # Format: temp=42.0'C
                temp = float(temp_output.split("=")[1].rstrip("'C"))
                metrics.append(MetricValue(
                    sensor_id="rpi_gpu_temperature",
                    state_topic=self._make_state_topic("rpi_gpu_temperature"),
                    value=round(temp, 1)
                ))
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse GPU temperature: {e}")

        return metrics

    def get_sensor_configs(self) -> List[SensorConfig]:
        if not self._is_rpi:
            return []

        configs = []

        # Throttling status (binary sensor)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_throttled"),
            name="RPi Throttled",
            state_topic=self._make_state_topic("rpi_throttled"),
            device_class="running",
            icon="mdi:speedometer-slow",
            entity_category="diagnostic",
            is_binary=True
        ))

        # Under-voltage (binary sensor)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_under_voltage"),
            name="RPi Under Voltage",
            state_topic=self._make_state_topic("rpi_under_voltage"),
            device_class="problem",
            icon="mdi:flash-alert",
            entity_category="diagnostic",
            is_binary=True
        ))

        # Temperature limited (binary sensor)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_temp_limited"),
            name="RPi Temperature Limited",
            state_topic=self._make_state_topic("rpi_temp_limited"),
            device_class="heat",
            icon="mdi:thermometer-alert",
            entity_category="diagnostic",
            is_binary=True
        ))

        # Frequency capped (binary sensor)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_freq_capped"),
            name="RPi Frequency Capped",
            state_topic=self._make_state_topic("rpi_freq_capped"),
            device_class="running",
            icon="mdi:speedometer-slow",
            entity_category="diagnostic",
            is_binary=True
        ))

        # Core voltage
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_core_voltage"),
            name="RPi Core Voltage",
            state_topic=self._make_state_topic("rpi_core_voltage"),
            device_class="voltage",
            state_class="measurement",
            unit_of_measurement="V",
            suggested_display_precision=4,
            entity_category="diagnostic"
        ))

        # GPU temperature
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_gpu_temperature"),
            name="RPi GPU Temperature",
            state_topic=self._make_state_topic("rpi_gpu_temperature"),
            device_class="temperature",
            state_class="measurement",
            unit_of_measurement="°C",
            suggested_display_precision=1
        ))

        # Raw throttle value (diagnostic)
        configs.append(SensorConfig(
            unique_id=self._make_unique_id("rpi_throttle_raw"),
            name="RPi Throttle Status",
            state_topic=self._make_state_topic("rpi_throttle_raw"),
            icon="mdi:information",
            entity_category="diagnostic",
            json_attributes_topic=self._make_attributes_topic("rpi_throttle_raw")
        ))

        return configs
