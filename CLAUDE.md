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

**Important:** Bump version in ALL these files when making changes:
- `system-monitor-pro/config.yaml` (version field)
- `system-monitor-pro/build.yaml` (BUILD_VERSION arg)
- `system-monitor-pro/app/__init__.py` (__version__)
- `system-monitor-pro/app/main.py` (log message)
- `system-monitor-pro/app/device_registry.py` (sw_version)
- `system-monitor-pro/CHANGELOG.md` (add new entry)
- `README.md` (version badge)

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
