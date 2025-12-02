# System Monitor Pro

Comprehensive system monitoring add-on for Home Assistant that exposes CPU, memory, disk, network, and security metrics as sensors.

## Features

- **CPU Monitoring**: Usage (total and per-core), temperature, frequency
- **Memory Monitoring**: Total, used, available RAM, swap usage
- **Disk Monitoring**: Usage, free space for all mounted filesystems
- **Network Monitoring**: Bytes sent/received, packets, errors, IP addresses
- **Security Monitoring**: Open ports, active connections, listening services
- **System Info**: Uptime, load average, OS version, process count
- **Raspberry Pi Support**: Thermal throttling, under-voltage warnings, core voltage

## Requirements

- Home Assistant OS or Supervised installation
- Mosquitto MQTT broker add-on (or any MQTT broker)
- MQTT integration configured in Home Assistant

## Installation

1. Install the Mosquitto MQTT broker add-on if you haven't already
2. Configure the MQTT integration in Home Assistant
3. Add this add-on repository to your Home Assistant
4. Install the System Monitor Pro add-on
5. Start the add-on

Sensors will automatically appear in Home Assistant via MQTT Discovery.

## Configuration

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `update_interval` | 60 | Seconds between metric updates (10-3600) |
| `cpu_threshold` | 90 | CPU usage % to trigger alert (50-100) |
| `memory_threshold` | 85 | Memory usage % to trigger alert (50-100) |
| `disk_threshold` | 85 | Disk usage % to trigger alert (50-100) |
| `temp_threshold` | 80 | Temperature (°C) to trigger alert (50-100) |
| `enable_security_monitoring` | true | Monitor open ports and connections |
| `enable_rpi_monitoring` | true | Enable Raspberry Pi specific sensors |
| `enable_alerts` | true | Enable threshold-based alerts |
| `alert_cooldown` | 300 | Seconds between repeated alerts (60-3600) |
| `monitored_disks` | [] | List of mount points to monitor (empty = all) |
| `mqtt_topic_prefix` | system_monitor_pro | MQTT topic prefix |

### Example Configuration

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
monitored_disks:
  - /
  - /media/storage
mqtt_topic_prefix: system_monitor_pro
```

## Sensors Created

### CPU Sensors

| Sensor | Type | Unit | Description |
|--------|------|------|-------------|
| CPU Usage | measurement | % | Total CPU utilization |
| CPU Core X Usage | measurement | % | Per-core utilization |
| CPU Temperature | measurement | °C | Processor temperature |
| CPU Frequency | measurement | MHz | Current clock speed |

### Memory Sensors

| Sensor | Type | Unit | Description |
|--------|------|------|-------------|
| Memory Usage | measurement | % | RAM utilization |
| Memory Total | measurement | GB | Total installed RAM |
| Memory Used | measurement | GB | Currently used RAM |
| Memory Available | measurement | GB | Available RAM |
| Swap Usage | measurement | % | Swap utilization |
| Swap Used | measurement | GB | Used swap space |

### Disk Sensors (per filesystem)

| Sensor | Type | Unit | Description |
|--------|------|------|-------------|
| Disk Usage {mount} | measurement | % | Filesystem utilization |
| Disk Free {mount} | measurement | GB | Available space |
| Disk Total {mount} | measurement | GB | Total capacity |

### Network Sensors

| Sensor | Type | Unit | Description |
|--------|------|------|-------------|
| Network Bytes Sent | total_increasing | GB | Total transmitted |
| Network Bytes Received | total_increasing | GB | Total received |
| Network Packets Sent | total_increasing | - | Packets transmitted |
| Network Packets Received | total_increasing | - | Packets received |
| Network Errors | total_increasing | - | Total network errors |
| Network Drops | total_increasing | - | Total dropped packets |
| IP Address | text | - | Primary IP (attributes contain all) |

### Security Sensors

| Sensor | Type | Description |
|--------|------|-------------|
| Open Ports | measurement | Number of listening ports |
| Active Connections | measurement | Established connections |
| Total Connections | measurement | All connections |
| Listening Sockets | measurement | LISTEN state sockets |

### System Sensors

| Sensor | Type | Unit | Description |
|--------|------|------|-------------|
| System Uptime | total_increasing | s | Time since boot |
| Process Count | measurement | - | Running processes |
| Load Average 1m | measurement | - | 1-minute load average |
| Load Average 5m | measurement | - | 5-minute load average |
| Load Average 15m | measurement | - | 15-minute load average |
| System Info | text | - | OS version (attributes contain details) |

### Raspberry Pi Sensors (when detected)

| Sensor | Type | Description |
|--------|------|-------------|
| RPi Throttled | binary | Currently thermal throttling |
| RPi Under Voltage | binary | Power supply issue |
| RPi Temperature Limited | binary | Soft temp limit active |
| RPi Frequency Capped | binary | Frequency capped |
| RPi Core Voltage | measurement | Core voltage (V) |
| RPi GPU Temperature | measurement | GPU temperature (°C) |
| RPi Throttle Status | text | Raw throttle hex value |

## Alerts

When `enable_alerts` is true, the add-on publishes alert events to `system_monitor_pro/alerts` when:

- CPU usage exceeds threshold
- Memory usage exceeds threshold
- Any disk usage exceeds threshold
- Temperature exceeds threshold
- Raspberry Pi under-voltage detected
- Raspberry Pi thermal throttling active
- Raspberry Pi temperature limited

You can create automations to respond to these alerts:

```yaml
automation:
  - alias: "System Monitor Alert Notification"
    trigger:
      - platform: mqtt
        topic: "system_monitor_pro/alerts"
    action:
      - service: notify.mobile_app
        data:
          title: "System Alert"
          message: "{{ trigger.payload_json.name }}: {{ trigger.payload_json.value }}"
```

## Dashboard Example

Create a dashboard card using the sensors:

```yaml
type: entities
title: System Monitor
entities:
  - entity: sensor.system_monitor_cpu_usage
  - entity: sensor.system_monitor_memory_usage
  - entity: sensor.system_monitor_disk_root_usage
  - entity: sensor.system_monitor_cpu_temperature
  - entity: sensor.system_monitor_system_uptime
```

## Troubleshooting

### Sensors not appearing

1. Verify MQTT broker is running and accessible
2. Check add-on logs for connection errors
3. Verify MQTT integration is configured in Home Assistant
4. Check MQTT topic prefix matches expected topics

### Missing temperature sensor

Temperature sensors require hardware support. Not all systems expose temperature via standard interfaces.

### Raspberry Pi sensors missing

- Ensure the device is a Raspberry Pi
- `vcgencmd` must be available (provided via `/dev/vcio` device mount)
- Set `enable_rpi_monitoring: true`

### High resource usage

- Increase `update_interval` for less frequent updates
- Disable `enable_security_monitoring` if not needed
- Limit `monitored_disks` to specific mount points

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/ESJavadex/home-assistant-info).
