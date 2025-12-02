"""
Main application entry point for System Monitor Pro.

Orchestrates the monitoring system:
- Initializes configuration from add-on options
- Establishes MQTT connection with Home Assistant broker
- Publishes device and sensor discovery messages
- Schedules and executes metric collection loop
- Handles graceful shutdown on SIGTERM/SIGINT
"""

import asyncio
import signal
import logging
import sys
from typing import Optional

from config import Config
from mqtt_publisher import MQTTPublisher
from device_registry import DeviceRegistry
from alert_manager import AlertManager
from collectors import CollectorRegistry
from webserver import WebServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class SystemMonitorPro:
    """Main application class for System Monitor Pro."""

    def __init__(self):
        self.config: Optional[Config] = None
        self.mqtt: Optional[MQTTPublisher] = None
        self.device: Optional[DeviceRegistry] = None
        self.alerts: Optional[AlertManager] = None
        self.collectors: Optional[CollectorRegistry] = None
        self.webserver: Optional[WebServer] = None
        self.running = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize all components."""
        logger.info("=" * 50)
        logger.info("System Monitor Pro v0.2.3")
        logger.info("=" * 50)

        # Load configuration
        logger.info("Loading configuration...")
        self.config = Config.load()

        # Initialize components
        logger.info("Initializing MQTT publisher...")
        self.mqtt = MQTTPublisher(self.config)

        logger.info("Initializing device registry...")
        self.device = DeviceRegistry(self.config)

        logger.info("Initializing alert manager...")
        self.alerts = AlertManager(self.config, self.mqtt)

        logger.info("Initializing collectors...")
        self.collectors = CollectorRegistry(self.config)

        logger.info("Initializing web dashboard...")
        self.webserver = WebServer(self.collectors)

    async def start(self):
        """Start the monitoring service."""
        await self.initialize()

        # Connect to MQTT broker
        logger.info("Connecting to MQTT broker...")
        await self.mqtt.connect()

        # Publish device and sensor discovery
        logger.info("Publishing discovery messages...")
        device_config = self.device.get_device_config()
        sensor_configs = self.collectors.get_all_sensor_configs()
        await self.mqtt.publish_discovery(device_config, sensor_configs)

        logger.info(f"Registered {len(sensor_configs)} sensors")

        # Start web dashboard
        await self.webserver.start()

        # Start main monitoring loop
        self.running = True
        logger.info(f"Starting monitoring loop (interval: {self.config.update_interval}s)")
        logger.info("=" * 50)

        await self.run_loop()

    async def run_loop(self):
        """Main update loop - collects and publishes metrics."""
        while self.running:
            try:
                # Collect all metrics
                metrics = await self.collectors.collect_all()

                # Check thresholds and trigger alerts
                await self.alerts.check_thresholds(metrics)

                # Publish state updates
                await self.mqtt.publish_states(metrics)

                logger.debug(f"Published {len(metrics)} metrics")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)

            # Wait for next interval or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.update_interval
                )
                # If we get here, shutdown was requested
                break
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                pass

    async def stop(self):
        """Graceful shutdown."""
        logger.info("Shutting down System Monitor Pro...")
        self.running = False
        self._shutdown_event.set()

        if self.webserver:
            await self.webserver.stop()

        if self.mqtt:
            await self.mqtt.disconnect()

        logger.info("Shutdown complete")

    def handle_signal(self, sig):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point."""
    app = SystemMonitorPro()

    # Get the event loop
    loop = asyncio.get_running_loop()

    # Set up signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: app.handle_signal(s))

    try:
        await app.start()
    except ConnectionError as e:
        logger.error(f"Failed to connect: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
