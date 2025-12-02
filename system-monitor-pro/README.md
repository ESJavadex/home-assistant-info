# System Monitor Pro for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/ESJavadex/home-assistant-info?style=flat-square)](https://github.com/ESJavadex/home-assistant-info/releases)
[![License](https://img.shields.io/github/license/ESJavadex/home-assistant-info?style=flat-square)](LICENSE)
[![Home Assistant Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg?style=flat-square)](https://www.home-assistant.io/addons/)
[![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg?style=flat-square)](https://www.home-assistant.io/)
[![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg?style=flat-square)](https://www.home-assistant.io/)

<p align="center">
  <img src="images/logo.png" alt="System Monitor Pro Logo" width="200"/>
</p>

**Comprehensive system monitoring add-on for Home Assistant** that creates 30+ sensors for CPU, memory, disk, network, and security metrics. Optimized for Raspberry Pi with dedicated sensors for thermal throttling and power issues.

---

## Table of Contents

- [Features](#features)
- [Sensors Overview](#sensors-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dashboard Examples](#dashboard-examples)
- [Alerts & Automations](#alerts--automations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Category | Metrics |
|----------|---------|
| **CPU** | Usage (total + per-core), temperature, frequency |
| **Memory** | Total, used, available, percentage, swap |
| **Disk** | Usage, free space, total (per filesystem) |
| **Network** | Bytes sent/received, packets, errors, IP addresses |
| **Security** | Open ports, active connections, listening services |
| **System** | Uptime, load average, process count, OS info |
| **Raspberry Pi** | Throttling, under-voltage, temp limit, core voltage |

### Key Highlights

- **MQTT Discovery** - Sensors automatically appear in Home Assistant
- **Multi-Architecture** - Works on x86-64 and ARM64 (Raspberry Pi 4/5)
- **Low Resource Usage** - Configurable update interval (default 60s)
- **Threshold Alerts** - Get notified when metrics exceed limits
- **Raspberry Pi Optimized** - Dedicated sensors for Pi-specific issues

---

## Sensors Overview

### Hardware Metrics

| Sensor | Unit | Description |
|--------|------|-------------|
| CPU Usage | % | Total CPU utilization |
| CPU Core X Usage | % | Per-core utilization |
| CPU Temperature | °C | Processor temperature |
| CPU Frequency | MHz | Current clock speed |
| Memory Usage | % | RAM utilization |
| Memory Available | GB | Available RAM |
| Disk Usage | % | Filesystem utilization |
| Disk Free | GB | Available disk space |

### Network & Security

| Sensor | Description |
|--------|-------------|
| Network Bytes Sent/Received | Total data transferred |
| IP Address | Primary IP with all interfaces in attributes |
| Open Ports | Count with port details in attributes |
| Active Connections | Established connection count |

### Raspberry Pi (Auto-detected)

| Sensor | Type | Description |
|--------|------|-------------|
| RPi Throttled | Binary | Currently thermal throttling |
| RPi Under Voltage | Binary | Power supply issue detected |
| RPi Temperature Limited | Binary | Soft temp limit active |
| RPi Core Voltage | V | Core voltage reading |
| RPi GPU Temperature | °C | VideoCore temperature |

---

## Installation

### Prerequisites

1. **Home Assistant OS** or **Supervised** installation
2. **Mosquitto MQTT broker** add-on installed and running
3. **MQTT integration** configured in Home Assistant

### Method 1: Add Repository (Recommended)

1. Navigate to **Settings** → **Add-ons** → **Add-on Store**
2. Click the **⋮** menu (top right) → **Repositories**
3. Add this repository URL:
   ```
   https://github.com/ESJavadex/home-assistant-info
   ```
4. Find **System Monitor Pro** in the add-on store
5. Click **Install** → **Start**

### Method 2: Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ESJavadex/home-assistant-info.git
   ```
2. Copy the `system-monitor-pro` folder to your Home Assistant `addons` directory
3. Reload add-ons in Home Assistant
4. Install and start the add-on

---

## Configuration

### Default Configuration

```yaml
update_interval: 60
cpu_threshold: 90
memory_threshold: 85
disk_threshold: 85
temp_threshold: 80
enable_security_monitoring: true
enable_rpi_monitoring: true
enable_alerts: true
alert_cooldown: 300
monitored_disks: []
mqtt_topic_prefix: system_monitor_pro
```

### Configuration Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `update_interval` | 60 | 10-3600 | Seconds between metric updates |
| `cpu_threshold` | 90 | 50-100 | CPU % to trigger alert |
| `memory_threshold` | 85 | 50-100 | Memory % to trigger alert |
| `disk_threshold` | 85 | 50-100 | Disk % to trigger alert |
| `temp_threshold` | 80 | 50-100 | Temperature °C to trigger alert |
| `enable_security_monitoring` | true | - | Monitor open ports and connections |
| `enable_rpi_monitoring` | true | - | Enable Raspberry Pi sensors |
| `enable_alerts` | true | - | Enable threshold-based alerts |
| `alert_cooldown` | 300 | 60-3600 | Seconds between repeated alerts |
| `monitored_disks` | [] | - | Mount points to monitor (empty = all) |
| `mqtt_topic_prefix` | system_monitor_pro | - | MQTT topic prefix |

### Example: Monitor Specific Disks

```yaml
monitored_disks:
  - /
  - /media/storage
  - /mnt/backup
```

---

## Usage

After starting the add-on, sensors automatically appear in Home Assistant via MQTT Discovery. You can find them under:

- **Settings** → **Devices & Services** → **MQTT** → **System Monitor**

Or search for entities starting with `sensor.system_monitor_`.

### Entity Naming Convention

```
sensor.system_monitor_{hostname}_{metric}
```

Examples:
- `sensor.system_monitor_homeassistant_cpu_usage`
- `sensor.system_monitor_homeassistant_memory_usage`
- `sensor.system_monitor_homeassistant_disk_root_usage`

---

## Dashboard Examples

### Simple Entities Card

```yaml
type: entities
title: System Monitor
entities:
  - entity: sensor.system_monitor_homeassistant_cpu_usage
    name: CPU
  - entity: sensor.system_monitor_homeassistant_memory_usage
    name: Memory
  - entity: sensor.system_monitor_homeassistant_disk_root_usage
    name: Disk
  - entity: sensor.system_monitor_homeassistant_cpu_temperature
    name: Temperature
  - entity: sensor.system_monitor_homeassistant_uptime
    name: Uptime
```

### Gauge Cards

```yaml
type: horizontal-stack
cards:
  - type: gauge
    entity: sensor.system_monitor_homeassistant_cpu_usage
    name: CPU
    severity:
      green: 0
      yellow: 60
      red: 85
  - type: gauge
    entity: sensor.system_monitor_homeassistant_memory_usage
    name: Memory
    severity:
      green: 0
      yellow: 60
      red: 85
  - type: gauge
    entity: sensor.system_monitor_homeassistant_disk_root_usage
    name: Disk
    severity:
      green: 0
      yellow: 70
      red: 85
```

### Raspberry Pi Status Card

```yaml
type: entities
title: Raspberry Pi Health
entities:
  - entity: binary_sensor.system_monitor_homeassistant_rpi_under_voltage
    name: Under Voltage
  - entity: binary_sensor.system_monitor_homeassistant_rpi_throttled
    name: Throttled
  - entity: sensor.system_monitor_homeassistant_rpi_core_voltage
    name: Core Voltage
  - entity: sensor.system_monitor_homeassistant_rpi_gpu_temperature
    name: GPU Temp
```

---

## Alerts & Automations

### MQTT Alert Events

When thresholds are exceeded, alerts are published to:
```
system_monitor_pro/alerts
```

Payload format:
```json
{
  "sensor": "cpu_usage",
  "name": "CPU Usage",
  "value": 95.2,
  "threshold": 90
}
```

### Example Automation: Mobile Notification

```yaml
automation:
  - alias: "System Monitor - Critical Alert"
    trigger:
      - platform: mqtt
        topic: "system_monitor_pro/alerts"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "System Alert"
          message: "{{ trigger.payload_json.name }}: {{ trigger.payload_json.value }}%"
          data:
            priority: high
            channel: system_alerts
```

### Example Automation: Telegram Notification

```yaml
automation:
  - alias: "System Monitor - Telegram Alert"
    trigger:
      - platform: mqtt
        topic: "system_monitor_pro/alerts"
    condition:
      - condition: template
        value_template: "{{ trigger.payload_json.value | float > 90 }}"
    action:
      - service: telegram_bot.send_message
        data:
          message: |
            ⚠️ *System Alert*
            {{ trigger.payload_json.name }}: {{ trigger.payload_json.value }}
            Threshold: {{ trigger.payload_json.threshold }}
```

### Example Automation: Disk Space Warning

```yaml
automation:
  - alias: "Disk Space Low Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.system_monitor_homeassistant_disk_root_usage
        above: 80
    action:
      - service: persistent_notification.create
        data:
          title: "Disk Space Warning"
          message: "Root disk usage is {{ states('sensor.system_monitor_homeassistant_disk_root_usage') }}%"
```

---

## Troubleshooting

### Sensors Not Appearing

1. **Check MQTT broker is running**
   ```
   Settings → Add-ons → Mosquitto broker → Logs
   ```

2. **Verify MQTT integration**
   ```
   Settings → Devices & Services → MQTT
   ```

3. **Check add-on logs**
   ```
   Settings → Add-ons → System Monitor Pro → Logs
   ```

4. **Verify MQTT messages** (using MQTT Explorer or similar):
   ```
   Topic: homeassistant/sensor/system_monitor_*/config
   ```

### Missing Temperature Sensor

Temperature sensors require hardware support. Some systems (especially VMs) don't expose temperature via standard interfaces.

### Raspberry Pi Sensors Missing

- Ensure you're running on actual Raspberry Pi hardware
- The `vcgencmd` tool must be available
- Set `enable_rpi_monitoring: true` in configuration
- Check add-on has access to `/dev/vcio` device

### High CPU Usage

If the add-on uses too much CPU:
1. Increase `update_interval` (e.g., 120 or 300 seconds)
2. Disable `enable_security_monitoring` if not needed
3. Limit `monitored_disks` to specific mount points

### Connection Errors

```
Failed to connect to MQTT broker
```

1. Verify Mosquitto broker is running
2. Check MQTT credentials in Mosquitto add-on config
3. Ensure no firewall blocking port 1883

---

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────┐
│              System Monitor Pro              │
├─────────────────────────────────────────────┤
│  main.py          - Orchestration loop      │
│  mqtt_publisher   - MQTT Discovery & state  │
│  alert_manager    - Threshold monitoring    │
│  device_registry  - HA device entity        │
├─────────────────────────────────────────────┤
│  Collectors:                                │
│  ├── cpu.py      - CPU metrics             │
│  ├── memory.py   - RAM metrics             │
│  ├── disk.py     - Filesystem metrics      │
│  ├── network.py  - Network stats           │
│  ├── security.py - Ports & connections     │
│  ├── system.py   - Uptime, load, OS info   │
│  └── rpi.py      - Raspberry Pi specific   │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│           MQTT Broker (Mosquitto)           │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│       Home Assistant (MQTT Discovery)       │
└─────────────────────────────────────────────┘
```

### Technologies Used

- **Python 3.12** - Application runtime
- **psutil** - Cross-platform system metrics
- **paho-mqtt** - MQTT client library
- **Alpine Linux** - Container base image
- **Home Assistant Add-on SDK** - Integration framework

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ESJavadex/home-assistant-info.git
cd home-assistant-info/system-monitor-pro

# Install dependencies
pip install -r requirements.txt

# Run locally (requires MQTT broker)
export MQTT_HOST=localhost
export MQTT_PORT=1883
python app/main.py
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) - The best home automation platform
- [psutil](https://github.com/giampaolo/psutil) - Cross-platform system monitoring library
- [Eclipse Paho](https://www.eclipse.org/paho/) - MQTT client library

---

<p align="center">
  Made with ❤️ for the Home Assistant community
</p>
