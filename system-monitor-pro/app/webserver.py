"""
Web dashboard server for System Monitor Pro.

Provides a real-time web interface for monitoring system metrics.
Uses aiohttp for async HTTP serving compatible with the main asyncio loop.
"""

import logging
from typing import TYPE_CHECKING, Optional
from aiohttp import web

if TYPE_CHECKING:
    from collectors import CollectorRegistry

logger = logging.getLogger(__name__)


class WebServer:
    """Async web server for the monitoring dashboard."""

    def __init__(self, collectors: "CollectorRegistry", port: int = 8099):
        self.collectors = collectors
        self.port = port
        self.app = web.Application()
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._setup_routes()

    def _setup_routes(self):
        """Configure routes for the web application."""
        # Main routes
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_get("/api/metrics", self._handle_metrics)
        self.app.router.add_get("/api/health", self._handle_health)
        # Handle trailing slashes for ingress compatibility
        self.app.router.add_get("/api/metrics/", self._handle_metrics)
        self.app.router.add_get("/api/health/", self._handle_health)

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serve the main dashboard HTML."""
        html = self._get_dashboard_html()
        return web.Response(text=html, content_type="text/html")

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """Return current metrics as JSON."""
        try:
            metrics = await self.collectors.collect_all()
            # Convert metrics to a dictionary format
            data = {}
            for metric in metrics:
                data[metric.sensor_id] = {
                    "value": metric.value,
                    "attributes": metric.attributes
                }
            return web.json_response(data)
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "healthy"})

    async def start(self):
        """Start the web server."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await self._site.start()
        logger.info(f"Web dashboard started on port {self.port}")

    async def stop(self):
        """Stop the web server."""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Web dashboard stopped")

    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Monitor Pro</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --accent: #e94560;
            --accent-secondary: #0ea5e9;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-card));
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .header h1 {{
            font-size: 2rem;
            background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .status {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            color: var(--text-secondary);
        }}

        .header .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }}

        .card {{
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .card-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}

        .icon-cpu {{ background: linear-gradient(135deg, #667eea, #764ba2); }}
        .icon-memory {{ background: linear-gradient(135deg, #f093fb, #f5576c); }}
        .icon-disk {{ background: linear-gradient(135deg, #4facfe, #00f2fe); }}
        .icon-network {{ background: linear-gradient(135deg, #43e97b, #38f9d7); }}
        .icon-system {{ background: linear-gradient(135deg, #fa709a, #fee140); }}
        .icon-security {{ background: linear-gradient(135deg, #8b5cf6, #a855f7); }}
        .icon-rpi {{ background: linear-gradient(135deg, #c51a4a, #ff6b9d); }}

        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-ok {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .status-warning {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
        .status-danger {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}

        .hidden {{ display: none !important; }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1;
        }}

        .metric-unit {{
            font-size: 1rem;
            color: var(--text-secondary);
            margin-left: 5px;
        }}

        .metric-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 5px;
        }}

        .progress-bar {{
            width: 100%;
            height: 8px;
            background: var(--bg-primary);
            border-radius: 4px;
            margin-top: 15px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease, background 0.3s;
        }}

        .progress-low {{ background: linear-gradient(90deg, #10b981, #34d399); }}
        .progress-medium {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
        .progress-high {{ background: linear-gradient(90deg, #ef4444, #f87171); }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }}

        .stat-item {{
            background: var(--bg-primary);
            padding: 12px;
            border-radius: 10px;
        }}

        .stat-value {{
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .stat-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .chart-container {{
            height: 120px;
            margin-top: 15px;
            position: relative;
        }}

        .chart {{
            width: 100%;
            height: 100%;
        }}

        .cores-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            gap: 8px;
            margin-top: 15px;
        }}

        .core-item {{
            background: var(--bg-primary);
            padding: 8px;
            border-radius: 8px;
            text-align: center;
        }}

        .core-value {{
            font-size: 1rem;
            font-weight: 600;
        }}

        .core-label {{
            font-size: 0.7rem;
            color: var(--text-secondary);
        }}

        .disk-list {{
            margin-top: 15px;
        }}

        .disk-item {{
            background: var(--bg-primary);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
        }}

        .disk-item:last-child {{
            margin-bottom: 0;
        }}

        .disk-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .disk-name {{
            font-weight: 600;
        }}

        .disk-usage {{
            color: var(--accent);
        }}

        .disk-details {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .system-info {{
            margin-top: 15px;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}

        .info-row:last-child {{
            border-bottom: none;
        }}

        .info-label {{
            color: var(--text-secondary);
        }}

        .info-value {{
            font-weight: 500;
        }}

        .uptime {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent-secondary);
        }}

        .refresh-info {{
            text-align: center;
            margin-top: 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .header h1 {{
                font-size: 1.5rem;
            }}
            .metric-value {{
                font-size: 2rem;
            }}
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>System Monitor Pro</h1>
        <div class="status">
            <span class="status-dot"></span>
            <span id="last-update">Connecting...</span>
        </div>
    </div>

    <div class="grid">
        <!-- CPU Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-cpu">&#x1F4BB;</div>
                    <span>CPU</span>
                </div>
            </div>
            <div class="metric-value">
                <span id="cpu-usage">--</span>
                <span class="metric-unit">%</span>
            </div>
            <div class="metric-label">Total Usage</div>
            <div class="progress-bar">
                <div class="progress-fill progress-low" id="cpu-progress" style="width: 0%"></div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="cpu-freq">--</div>
                    <div class="stat-label">Frequency (MHz)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="cpu-temp">--</div>
                    <div class="stat-label">Temperature</div>
                </div>
            </div>
            <div class="cores-grid" id="cores-container"></div>
        </div>

        <!-- Memory Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-memory">&#x1F9E0;</div>
                    <span>Memory</span>
                </div>
            </div>
            <div class="metric-value">
                <span id="memory-usage">--</span>
                <span class="metric-unit">%</span>
            </div>
            <div class="metric-label">Used</div>
            <div class="progress-bar">
                <div class="progress-fill progress-low" id="memory-progress" style="width: 0%"></div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="memory-used">--</div>
                    <div class="stat-label">Used (GB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="memory-total">--</div>
                    <div class="stat-label">Total (GB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="memory-available">--</div>
                    <div class="stat-label">Available (GB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="swap-usage">--</div>
                    <div class="stat-label">Swap (%)</div>
                </div>
            </div>
        </div>

        <!-- Disk Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-disk">&#x1F4BE;</div>
                    <span>Storage</span>
                </div>
            </div>
            <div class="disk-list" id="disk-container">
                <div class="stat-item">
                    <div class="stat-label">Loading disks...</div>
                </div>
            </div>
        </div>

        <!-- System Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-system">&#x2699;&#xFE0F;</div>
                    <span>System</span>
                </div>
            </div>
            <div class="metric-label">Uptime</div>
            <div class="uptime" id="uptime">--</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="load-1m">--</div>
                    <div class="stat-label">Load 1m</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="load-5m">--</div>
                    <div class="stat-label">Load 5m</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="load-15m">--</div>
                    <div class="stat-label">Load 15m</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="process-count">--</div>
                    <div class="stat-label">Processes</div>
                </div>
            </div>
            <div class="system-info" id="system-info"></div>
        </div>

        <!-- Network Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-network">&#x1F310;</div>
                    <span>Network</span>
                </div>
            </div>
            <div class="metric-value">
                <span id="network-ip">--</span>
            </div>
            <div class="metric-label">IP Address</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="net-sent">--</div>
                    <div class="stat-label">Sent (GB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="net-recv">--</div>
                    <div class="stat-label">Received (GB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="net-packets-sent">--</div>
                    <div class="stat-label">Packets Sent</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="net-packets-recv">--</div>
                    <div class="stat-label">Packets Recv</div>
                </div>
            </div>
            <div class="stats-grid" style="margin-top: 10px;">
                <div class="stat-item">
                    <div class="stat-value" id="net-errors">--</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="net-drops">--</div>
                    <div class="stat-label">Drops</div>
                </div>
            </div>
            <div class="system-info" id="interfaces-info"></div>
        </div>

        <!-- Security Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-security">&#x1F512;</div>
                    <span>Connections</span>
                </div>
            </div>
            <div class="metric-value">
                <span id="active-connections">--</span>
            </div>
            <div class="metric-label">Active Connections</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="open-ports">--</div>
                    <div class="stat-label">Open Ports</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-connections">--</div>
                    <div class="stat-label">Total Connections</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="listening-sockets">--</div>
                    <div class="stat-label">Listening</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="conn-time-wait">--</div>
                    <div class="stat-label">TIME_WAIT</div>
                </div>
            </div>
            <div class="system-info" id="ports-info"></div>
        </div>

        <!-- Raspberry Pi Card (hidden by default) -->
        <div class="card hidden" id="rpi-card">
            <div class="card-header">
                <div class="card-title">
                    <div class="card-icon icon-rpi">&#x1F353;</div>
                    <span>Raspberry Pi</span>
                </div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="rpi-gpu-temp">--</div>
                    <div class="stat-label">GPU Temp</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="rpi-voltage">--</div>
                    <div class="stat-label">Core Voltage</div>
                </div>
            </div>
            <div class="stats-grid" style="margin-top: 10px;">
                <div class="stat-item">
                    <span id="rpi-throttle-badge" class="status-badge status-ok">OK</span>
                    <div class="stat-label" style="margin-top: 5px;">Throttle</div>
                </div>
                <div class="stat-item">
                    <span id="rpi-voltage-badge" class="status-badge status-ok">OK</span>
                    <div class="stat-label" style="margin-top: 5px;">Voltage</div>
                </div>
                <div class="stat-item">
                    <span id="rpi-temp-badge" class="status-badge status-ok">OK</span>
                    <div class="stat-label" style="margin-top: 5px;">Temp Limit</div>
                </div>
                <div class="stat-item">
                    <span id="rpi-freq-badge" class="status-badge status-ok">OK</span>
                    <div class="stat-label" style="margin-top: 5px;">Freq Cap</div>
                </div>
            </div>
        </div>
    </div>

    <div class="refresh-info">
        Auto-refresh every 5 seconds
    </div>

    <script>
        // Use relative path for ingress compatibility
        function getBasePath() {{
            const path = window.location.pathname;
            // Remove trailing slash if present
            return path.endsWith('/') ? path.slice(0, -1) : path;
        }}

        function getProgressClass(value) {{
            if (value < 60) return 'progress-low';
            if (value < 85) return 'progress-medium';
            return 'progress-high';
        }}

        function formatUptime(seconds) {{
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);

            let parts = [];
            if (days > 0) parts.push(days + 'd');
            if (hours > 0) parts.push(hours + 'h');
            if (minutes > 0) parts.push(minutes + 'm');

            return parts.join(' ') || '< 1m';
        }}

        function formatNumber(num) {{
            if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B';
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toString();
        }}

        function updateDashboard(data) {{
            // CPU
            if (data.cpu_usage) {{
                const cpuVal = data.cpu_usage.value;
                document.getElementById('cpu-usage').textContent = cpuVal;
                const cpuProgress = document.getElementById('cpu-progress');
                cpuProgress.style.width = cpuVal + '%';
                cpuProgress.className = 'progress-fill ' + getProgressClass(cpuVal);
            }}

            if (data.cpu_frequency) {{
                document.getElementById('cpu-freq').textContent = data.cpu_frequency.value;
            }}

            if (data.cpu_temperature) {{
                document.getElementById('cpu-temp').textContent = data.cpu_temperature.value + '°C';
            }} else {{
                document.getElementById('cpu-temp').textContent = 'N/A';
            }}

            // CPU cores
            const coresContainer = document.getElementById('cores-container');
            let coresHtml = '';
            for (let i = 0; i < 32; i++) {{
                const coreKey = 'cpu_core_' + i + '_usage';
                if (data[coreKey]) {{
                    coresHtml += '<div class="core-item"><div class="core-value">' +
                        data[coreKey].value + '%</div><div class="core-label">Core ' + i + '</div></div>';
                }}
            }}
            coresContainer.innerHTML = coresHtml;

            // Memory
            if (data.memory_usage) {{
                const memVal = data.memory_usage.value;
                document.getElementById('memory-usage').textContent = memVal;
                const memProgress = document.getElementById('memory-progress');
                memProgress.style.width = memVal + '%';
                memProgress.className = 'progress-fill ' + getProgressClass(memVal);
            }}

            if (data.memory_used) document.getElementById('memory-used').textContent = data.memory_used.value;
            if (data.memory_total) document.getElementById('memory-total').textContent = data.memory_total.value;
            if (data.memory_available) document.getElementById('memory-available').textContent = data.memory_available.value;
            if (data.swap_usage) {{
                document.getElementById('swap-usage').textContent = data.swap_usage.value;
            }} else {{
                document.getElementById('swap-usage').textContent = 'N/A';
            }}

            // Disks
            const diskContainer = document.getElementById('disk-container');
            let diskHtml = '';
            const diskKeys = Object.keys(data).filter(k => k.startsWith('disk_') && k.endsWith('_usage'));

            for (const key of diskKeys) {{
                const diskId = key.replace('_usage', '');
                const usage = data[key].value;
                const freeKey = diskId + '_free';
                const totalKey = diskId + '_total';
                const free = data[freeKey] ? data[freeKey].value : '--';
                const total = data[totalKey] ? data[totalKey].value : '--';
                const name = diskId.replace('disk_', '/').replace(/_/g, '/');

                diskHtml += '<div class="disk-item">' +
                    '<div class="disk-header">' +
                        '<span class="disk-name">' + (name === '/root' ? '/' : name) + '</span>' +
                        '<span class="disk-usage">' + usage + '%</span>' +
                    '</div>' +
                    '<div class="progress-bar"><div class="progress-fill ' + getProgressClass(usage) +
                        '" style="width: ' + usage + '%"></div></div>' +
                    '<div class="disk-details">' +
                        '<span>Free: ' + free + ' GB</span>' +
                        '<span>Total: ' + total + ' GB</span>' +
                    '</div>' +
                '</div>';
            }}

            if (diskHtml) diskContainer.innerHTML = diskHtml;

            // System
            if (data.uptime) {{
                document.getElementById('uptime').textContent = formatUptime(data.uptime.value);
            }}

            if (data.load_1m) document.getElementById('load-1m').textContent = data.load_1m.value;
            if (data.load_5m) document.getElementById('load-5m').textContent = data.load_5m.value;
            if (data.load_15m) document.getElementById('load-15m').textContent = data.load_15m.value;
            if (data.process_count) document.getElementById('process-count').textContent = data.process_count.value;

            // System info
            if (data.system_info && data.system_info.attributes) {{
                const info = data.system_info.attributes;
                let infoHtml = '';
                if (info.os_version) infoHtml += '<div class="info-row"><span class="info-label">OS</span><span class="info-value">' + info.os_version + '</span></div>';
                if (info.kernel) infoHtml += '<div class="info-row"><span class="info-label">Kernel</span><span class="info-value">' + info.kernel + '</span></div>';
                if (info.architecture) infoHtml += '<div class="info-row"><span class="info-label">Arch</span><span class="info-value">' + info.architecture + '</span></div>';
                if (info.hostname) infoHtml += '<div class="info-row"><span class="info-label">Host</span><span class="info-value">' + info.hostname + '</span></div>';
                document.getElementById('system-info').innerHTML = infoHtml;
            }}

            // Network
            if (data.network_ip_address) {{
                document.getElementById('network-ip').textContent = data.network_ip_address.value;
                // Show interfaces
                if (data.network_ip_address.attributes && data.network_ip_address.attributes.interfaces) {{
                    const ifaces = data.network_ip_address.attributes.interfaces;
                    let ifaceHtml = '';
                    for (const [name, info] of Object.entries(ifaces)) {{
                        if (info.ipv4) {{
                            ifaceHtml += '<div class="info-row"><span class="info-label">' + name + '</span><span class="info-value">' + info.ipv4 + '</span></div>';
                        }}
                    }}
                    document.getElementById('interfaces-info').innerHTML = ifaceHtml;
                }}
            }}
            if (data.network_bytes_sent) document.getElementById('net-sent').textContent = data.network_bytes_sent.value;
            if (data.network_bytes_recv) document.getElementById('net-recv').textContent = data.network_bytes_recv.value;
            if (data.network_packets_sent) document.getElementById('net-packets-sent').textContent = formatNumber(data.network_packets_sent.value);
            if (data.network_packets_recv) document.getElementById('net-packets-recv').textContent = formatNumber(data.network_packets_recv.value);
            if (data.network_errors) document.getElementById('net-errors').textContent = data.network_errors.value;
            if (data.network_drops) document.getElementById('net-drops').textContent = data.network_drops.value;

            // Security / Connections
            if (data.active_connections) {{
                document.getElementById('active-connections').textContent = data.active_connections.value;
                // Show connection states
                if (data.active_connections.attributes) {{
                    const attrs = data.active_connections.attributes;
                    if (attrs.TIME_WAIT !== undefined) {{
                        document.getElementById('conn-time-wait').textContent = attrs.TIME_WAIT;
                    }}
                }}
            }}
            if (data.open_ports) {{
                document.getElementById('open-ports').textContent = data.open_ports.value;
                // Show top ports
                if (data.open_ports.attributes && data.open_ports.attributes.ports) {{
                    const ports = data.open_ports.attributes.ports.slice(0, 5);
                    let portsHtml = '';
                    for (const p of ports) {{
                        portsHtml += '<div class="info-row"><span class="info-label">:' + p.port + '</span><span class="info-value">' + p.service + '</span></div>';
                    }}
                    document.getElementById('ports-info').innerHTML = portsHtml;
                }}
            }}
            if (data.total_connections) document.getElementById('total-connections').textContent = data.total_connections.value;
            if (data.listening_sockets) document.getElementById('listening-sockets').textContent = data.listening_sockets.value;

            // Raspberry Pi
            if (data.rpi_gpu_temperature || data.rpi_core_voltage) {{
                document.getElementById('rpi-card').classList.remove('hidden');

                if (data.rpi_gpu_temperature) {{
                    document.getElementById('rpi-gpu-temp').textContent = data.rpi_gpu_temperature.value + '°C';
                }}
                if (data.rpi_core_voltage) {{
                    document.getElementById('rpi-voltage').textContent = data.rpi_core_voltage.value + 'V';
                }}

                // Status badges
                if (data.rpi_throttled) {{
                    const badge = document.getElementById('rpi-throttle-badge');
                    const isOn = data.rpi_throttled.value === 'on';
                    badge.textContent = isOn ? 'THROTTLED' : 'OK';
                    badge.className = 'status-badge ' + (isOn ? 'status-danger' : 'status-ok');
                }}
                if (data.rpi_under_voltage) {{
                    const badge = document.getElementById('rpi-voltage-badge');
                    const isOn = data.rpi_under_voltage.value === 'on';
                    badge.textContent = isOn ? 'LOW' : 'OK';
                    badge.className = 'status-badge ' + (isOn ? 'status-danger' : 'status-ok');
                }}
                if (data.rpi_temp_limited) {{
                    const badge = document.getElementById('rpi-temp-badge');
                    const isOn = data.rpi_temp_limited.value === 'on';
                    badge.textContent = isOn ? 'LIMITED' : 'OK';
                    badge.className = 'status-badge ' + (isOn ? 'status-warning' : 'status-ok');
                }}
                if (data.rpi_freq_capped) {{
                    const badge = document.getElementById('rpi-freq-badge');
                    const isOn = data.rpi_freq_capped.value === 'on';
                    badge.textContent = isOn ? 'CAPPED' : 'OK';
                    badge.className = 'status-badge ' + (isOn ? 'status-warning' : 'status-ok');
                }}
            }}

            // Update timestamp
            document.getElementById('last-update').textContent = 'Last update: ' + new Date().toLocaleTimeString();
        }}

        async function fetchMetrics() {{
            try {{
                const basePath = getBasePath();
                const response = await fetch(basePath + '/api/metrics');
                if (response.ok) {{
                    const data = await response.json();
                    updateDashboard(data);
                }} else {{
                    console.error('API returned:', response.status);
                    document.getElementById('last-update').textContent = 'Error: ' + response.status;
                }}
            }} catch (error) {{
                console.error('Failed to fetch metrics:', error);
                document.getElementById('last-update').textContent = 'Connection error';
            }}
        }}

        // Initial fetch and start interval
        fetchMetrics();
        setInterval(fetchMetrics, 5000);
    </script>
</body>
</html>'''
