# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-12-02

### Added

- Web dashboard: Network card showing IP address, bytes sent/received, packets, errors, drops
- Web dashboard: Connections card showing active connections, open ports, listening sockets
- Web dashboard: Raspberry Pi card (auto-shown if RPi detected) with GPU temp, voltage, throttle status
- Network interfaces list in dashboard
- Top listening ports list in dashboard

## [0.0.3] - 2024-12-02

### Added

- CLAUDE.md with repository guidance and version management instructions

### Fixed

- Fixed s6-envdir error by using correct bashio shebang

## [0.0.2] - 2024-12-02

### Changed

- Renamed repository to "Home Assistant Info Add-ons"

## [0.0.1] - 2024-12-02

### Added

- Initial release
- CPU monitoring (usage, temperature, frequency, per-core)
- Memory monitoring (total, used, available, swap)
- Disk monitoring (usage, free, total per filesystem)
- Network monitoring (bytes, packets, errors, IP addresses)
- Security monitoring (open ports, connections)
- System info (uptime, load average, OS version)
- Raspberry Pi specific sensors (throttling, voltage, GPU temp)
- MQTT Discovery for automatic sensor creation
- Configurable alert thresholds
- Multi-architecture support (amd64, aarch64)
