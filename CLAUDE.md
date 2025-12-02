# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Home Assistant add-on repository containing custom add-ons. The repository uses the standard Home Assistant add-on structure with `repository.yaml` at the root.

## Repository Structure

```
home-assistant-info/
├── repository.yaml          # Required for HA to recognize as add-on repo
├── README.md
├── LICENSE
└── system-monitor-pro/      # Add-on directory
    ├── config.yaml          # Add-on metadata and user options schema
    ├── build.yaml           # Multi-arch build config (amd64, aarch64)
    ├── Dockerfile           # Alpine-based container
    ├── run.sh               # Bashio entrypoint
    ├── requirements.txt     # Python deps: psutil, paho-mqtt
    └── app/                 # Python application
```

## System Monitor Pro Architecture

The add-on uses MQTT Discovery to automatically create sensors in Home Assistant.

**Flow:** `run.sh` → `main.py` → Collectors → MQTT Publisher → Home Assistant

### Key Components

- **main.py**: Async orchestration loop, handles SIGTERM/SIGINT
- **collectors/**: Modular metric collectors inheriting from `BaseCollector`
  - Each collector implements `collect()` and `get_sensor_configs()`
  - RPi collector auto-detects Raspberry Pi via `vcgencmd`
- **mqtt_publisher.py**: Handles MQTT Discovery config and state publishing
- **alert_manager.py**: Threshold monitoring with cooldown logic

### Adding a New Collector

1. Create `app/collectors/newcollector.py` inheriting from `BaseCollector`
2. Implement `collect()` returning `List[MetricValue]`
3. Implement `get_sensor_configs()` returning `List[SensorConfig]`
4. Register in `app/collectors/__init__.py`

## Version Management

**CRITICAL: Bump version with EVERY commit that changes code!**

When making any changes to the add-on, you MUST update the version in ALL 7 files:

1. `system-monitor-pro/config.yaml` → `version: "X.Y.Z"`
2. `system-monitor-pro/build.yaml` → `BUILD_VERSION: "X.Y.Z"`
3. `system-monitor-pro/app/__init__.py` → `__version__ = "X.Y.Z"`
4. `system-monitor-pro/app/main.py` → `logger.info("System Monitor Pro vX.Y.Z")`
5. `system-monitor-pro/app/device_registry.py` → `"sw_version": "X.Y.Z"`
6. `system-monitor-pro/CHANGELOG.md` → Add new `## [X.Y.Z]` section at top
7. `README.md` → Update version badge `version-X.Y.Z-blue`

**Version format:** Use semantic versioning (MAJOR.MINOR.PATCH)
- PATCH: Bug fixes, small changes
- MINOR: New features, non-breaking
- MAJOR: Breaking changes

## Development Commands

```bash
# Run locally (requires MQTT broker)
export MQTT_HOST=localhost
export MQTT_PORT=1883
cd system-monitor-pro
pip install -r requirements.txt
python app/main.py

# Build Docker image locally
docker build -t system-monitor-pro --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20 system-monitor-pro/
```

## Home Assistant Add-on Requirements

- `repository.yaml` at root (not .json)
- Each add-on in its own subdirectory with `config.yaml`
- Supported architectures: amd64, aarch64
- MQTT broker required (Mosquitto add-on)
