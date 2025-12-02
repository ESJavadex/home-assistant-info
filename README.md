# Home Assistant Info Add-ons

[![Home Assistant Add-ons](https://img.shields.io/badge/Home%20Assistant-Add--ons-blue.svg?style=flat-square)](https://www.home-assistant.io/addons/)
[![License](https://img.shields.io/github/license/ESJavadex/home-assistant-info?style=flat-square)](LICENSE)

Custom Home Assistant add-ons for system monitoring and information.

## Installation

1. Navigate to **Settings** → **Add-ons** → **Add-on Store**
2. Click the **⋮** menu (top right) → **Repositories**
3. Add this repository URL:
   ```
   https://github.com/ESJavadex/home-assistant-info
   ```
4. Click **Add** → **Close**
5. Refresh the page - add-ons will appear in the store

## Available Add-ons

### System Monitor Pro

[![Version](https://img.shields.io/badge/version-0.0.2-blue.svg?style=flat-square)](system-monitor-pro/)
[![amd64](https://img.shields.io/badge/amd64-yes-green.svg?style=flat-square)](system-monitor-pro/)
[![aarch64](https://img.shields.io/badge/aarch64-yes-green.svg?style=flat-square)](system-monitor-pro/)

Comprehensive system monitoring add-on that creates 30+ sensors via MQTT Discovery:

- **CPU**: Usage (total + per-core), temperature, frequency
- **Memory**: Total, used, available, swap
- **Disk**: Usage for all mounted filesystems
- **Network**: Bytes sent/received, IP addresses, errors
- **Security**: Open ports, active connections
- **System**: Uptime, load average, process count
- **Raspberry Pi**: Throttling, under-voltage, core voltage

[📖 Documentation](system-monitor-pro/DOCS.md) | [📝 Changelog](system-monitor-pro/CHANGELOG.md)

---

## Support

- [🐛 Report a bug](https://github.com/ESJavadex/home-assistant-info/issues)
- [💡 Request a feature](https://github.com/ESJavadex/home-assistant-info/issues)

## License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for the Home Assistant community
</p>
