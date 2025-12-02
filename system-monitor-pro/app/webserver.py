"""
Web dashboard server for System Monitor Pro.

Provides a real-time web interface for monitoring system metrics.
Uses aiohttp for async HTTP serving compatible with the main asyncio loop.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from aiohttp import web

if TYPE_CHECKING:
    from collectors import CollectorRegistry

logger = logging.getLogger(__name__)

# Path to static files
STATIC_DIR = Path(__file__).parent / "static"


class WebServer:
    """Async web server for the monitoring dashboard."""

    def __init__(self, collectors: "CollectorRegistry", port: int = 8099):
        self.collectors = collectors
        self.port = port
        self.app = web.Application()
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._html_cache: Optional[str] = None
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
            data = {
                metric.sensor_id: {
                    "value": metric.value,
                    "attributes": metric.attributes
                }
                for metric in metrics
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
        """Load dashboard HTML from static file."""
        if self._html_cache is None:
            html_path = STATIC_DIR / "index.html"
            try:
                self._html_cache = html_path.read_text(encoding="utf-8")
                logger.debug(f"Loaded dashboard from {html_path}")
            except FileNotFoundError:
                logger.error(f"Dashboard HTML not found: {html_path}")
                self._html_cache = "<html><body><h1>Dashboard not found</h1></body></html>"
        return self._html_cache
