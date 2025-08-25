"""Health monitoring and status reporting for Kicktipp Bot."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os

logger = logging.getLogger(__name__)


class HealthStatus:
    """Tracks the health status of the bot."""

    def __init__(self):
        # Start with initial heartbeat
        self.last_heartbeat: Optional[datetime] = datetime.now()
        self.last_successful_run: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.total_runs: int = 0
        self.successful_runs: int = 0
        self.failed_runs: int = 0
        self.start_time: datetime = datetime.now()
        self.status: str = "starting"

    def heartbeat(self) -> None:
        """Update the heartbeat timestamp."""
        self.last_heartbeat = datetime.now()

    def mark_ready(self) -> None:
        """Mark the bot as ready and running."""
        self.status = "ready"
        self.heartbeat()

    def record_successful_run(self) -> None:
        """Record a successful bot execution."""
        self.last_successful_run = datetime.now()
        self.successful_runs += 1
        self.total_runs += 1
        self.status = "healthy"
        self.last_error = None

    def record_failed_run(self, error: str) -> None:
        """Record a failed bot execution."""
        self.failed_runs += 1
        self.total_runs += 1
        self.last_error = error
        self.status = "error"

    def get_status(self) -> Dict[str, Any]:
        """Get the current health status."""
        now = datetime.now()
        uptime = now - self.start_time

        # Determine if bot is healthy based on different criteria
        is_healthy = self._determine_health(now, uptime)

        return {
            "status": self.status,
            "healthy": is_healthy,
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
            "start_time": self.start_time.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_successful_run": self.last_successful_run.isoformat() if self.last_successful_run else None,
            "last_error": self.last_error,
            "stats": {
                "total_runs": self.total_runs,
                "successful_runs": self.successful_runs,
                "failed_runs": self.failed_runs,
                "success_rate": round(self.successful_runs / max(self.total_runs, 1) * 100, 2)
            }
        }

    def _determine_health(self, now: datetime, uptime: timedelta) -> bool:
        """Determine if the bot is healthy based on current state and uptime."""
        # During startup (first 5 minutes), be more lenient
        if uptime < timedelta(minutes=5):
            # During startup, consider healthy if:
            # 1. Status is not 'error' AND
            # 2. We have a recent heartbeat (within 2 minutes)
            recent_heartbeat = (
                self.last_heartbeat and
                (now - self.last_heartbeat) < timedelta(minutes=2)
            )
            return self.status != "error" and recent_heartbeat

        # After startup, use stricter criteria based on run interval
        # Import here to avoid circular imports
        from .config import Config

        # Get the run interval and add a 50% buffer
        run_interval_minutes = Config.RUN_EVERY_X_MINUTES or 60
        health_timeout_minutes = int(run_interval_minutes * 1.5)  # 50% buffer

        if self.last_heartbeat:
            time_since_heartbeat = now - self.last_heartbeat
            minutes_since_heartbeat = time_since_heartbeat.total_seconds() / 60
            is_healthy = minutes_since_heartbeat < health_timeout_minutes
            return is_healthy
        else:
            logger.warning("Health check: No heartbeat recorded yet")
            return False


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint."""

    def do_GET(self):
        """Handle GET requests for health status."""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/status':
            self.send_detailed_status()
        else:
            self.send_error(404, "Not Found")

    def send_health_response(self):
        """Send a simple health check response."""
        status = health_status.get_status()

        if status["healthy"]:
            self.send_response(200)
            response = {"status": "healthy",
                        "timestamp": datetime.now().isoformat()}
        else:
            self.send_response(503)
            response = {"status": "unhealthy",
                        "timestamp": datetime.now().isoformat()}

        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def send_detailed_status(self):
        """Send detailed status information."""
        status = health_status.get_status()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status, indent=2).encode())

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.debug(f"Health check request: {format % args}")


class HealthMonitor:
    """Manages health monitoring for the bot."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start_health_server(self) -> None:
        """Start the health check HTTP server."""
        try:
            self.server = HTTPServer(
                ('0.0.0.0', self.port), HealthCheckHandler)
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True,
                name="HealthCheckServer"
            )
            self.server_thread.start()
            logger.info(f"Health check server started on port {self.port}")
            logger.info(
                f"Health endpoints: http://localhost:{self.port}/health, http://localhost:{self.port}/status")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")

    def stop_health_server(self) -> None:
        """Stop the health check HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health check server stopped")

    def send_heartbeat_notification(self) -> None:
        """Send heartbeat notification to external monitoring."""
        heartbeat_url = os.getenv("HEARTBEAT_URL")
        if heartbeat_url:
            try:
                import requests
                response = requests.post(
                    heartbeat_url,
                    json={
                        "service": "kicktipp-bot",
                        "status": health_status.status,
                        "timestamp": datetime.now().isoformat(),
                        "uptime": health_status.get_status()["uptime_seconds"]
                    },
                    timeout=10
                )
                response.raise_for_status()
                logger.debug("Heartbeat notification sent successfully")
            except Exception as e:
                logger.warning(f"Failed to send heartbeat notification: {e}")


# Global health status instance
health_status = HealthStatus()
health_monitor = HealthMonitor(
    port=int(os.getenv("HEALTH_CHECK_PORT", "8080")))
