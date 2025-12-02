"""
Abstract base class for metric collectors.

Defines the interface all collectors must implement:
- collect(): Gather current metrics
- get_sensor_configs(): Return MQTT discovery configurations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config


@dataclass
class SensorConfig:
    """Configuration for a single sensor entity."""

    unique_id: str
    name: str
    state_topic: str
    device_class: Optional[str] = None
    state_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    icon: Optional[str] = None
    entity_category: Optional[str] = None  # "config" or "diagnostic"
    value_template: Optional[str] = None
    suggested_display_precision: Optional[int] = None
    json_attributes_topic: Optional[str] = None
    is_binary: bool = False  # True for binary_sensor


@dataclass
class MetricValue:
    """A single metric measurement."""

    sensor_id: str
    state_topic: str
    value: Any
    attributes: Optional[Dict[str, Any]] = None
    attributes_topic: Optional[str] = None


class BaseCollector(ABC):
    """Abstract base class for all metric collectors."""

    def __init__(self, config: "Config", topic_prefix: str, unique_id_prefix: str):
        self.config = config
        self.topic_prefix = topic_prefix
        self.unique_id_prefix = unique_id_prefix

    def _make_state_topic(self, sensor_id: str) -> str:
        """Generate state topic for a sensor."""
        return f"{self.topic_prefix}/sensor/{sensor_id}/state"

    def _make_attributes_topic(self, sensor_id: str) -> str:
        """Generate attributes topic for a sensor."""
        return f"{self.topic_prefix}/sensor/{sensor_id}/attributes"

    def _make_unique_id(self, sensor_id: str) -> str:
        """Generate unique ID for a sensor."""
        return f"{self.unique_id_prefix}_{sensor_id}"

    @abstractmethod
    async def collect(self) -> List[MetricValue]:
        """Collect current metrics. Returns list of MetricValue objects."""
        pass

    @abstractmethod
    def get_sensor_configs(self) -> List[SensorConfig]:
        """Return sensor configurations for MQTT discovery."""
        pass

    def is_available(self) -> bool:
        """Check if this collector can run on current system."""
        return True
