"""Advanced monitoring and logging system for MilkBottle.

This module provides comprehensive monitoring, performance tracking,
resource usage monitoring, and structured logging capabilities.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Monitoring constants
DEFAULT_METRICS_RETENTION = 3600  # 1 hour
DEFAULT_LOG_RETENTION_DAYS = 7
MAX_METRICS_HISTORY = 10000
MAX_LOG_ENTRIES = 10000


class StructuredLogger:
    """Structured logger with correlation ID support and JSON formatting."""

    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize structured logger.

        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.name = name
        self.log_file = log_file
        self.correlation_id = None
        self._log_entries = deque(maxlen=MAX_LOG_ENTRIES)

        # Setup file handler if log_file specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        else:
            self.file_handler = None

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking.

        Args:
            correlation_id: Unique correlation ID
        """
        self.correlation_id = correlation_id

    def _format_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Format log entry as structured data.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional log data

        Returns:
            Formatted log entry
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "correlation_id": self.correlation_id,
        }

        if kwargs:
            entry["data"] = kwargs

        return entry

    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry to file and memory.

        Args:
            entry: Log entry to write
        """
        # Add to memory
        self._log_entries.append(entry)

        # Write to file if configured
        if self.file_handler:
            log_message = json.dumps(entry)
            self.file_handler.emit(
                logging.LogRecord(
                    name=self.name,
                    level=getattr(logging, entry["level"].upper()),
                    pathname="",
                    lineno=0,
                    msg=log_message,
                    args=(),
                    exc_info=None,
                )
            )

    def info(self, message: str, **kwargs):
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional log data
        """
        entry = self._format_log_entry("info", message, **kwargs)
        self._write_log(entry)

    def warning(self, message: str, **kwargs):
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional log data
        """
        entry = self._format_log_entry("warning", message, **kwargs)
        self._write_log(entry)

    def error(self, message: str, **kwargs):
        """Log error message.

        Args:
            message: Log message
            **kwargs: Additional log data
        """
        entry = self._format_log_entry("error", message, **kwargs)
        self._write_log(entry)

    def debug(self, message: str, **kwargs):
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional log data
        """
        entry = self._format_log_entry("debug", message, **kwargs)
        self._write_log(entry)

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent log entries
        """
        return list(self._log_entries)[-limit:]

    def get_logs_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get logs by correlation ID.

        Args:
            correlation_id: Correlation ID to filter by

        Returns:
            List of log entries with matching correlation ID
        """
        return [
            entry
            for entry in self._log_entries
            if entry.get("correlation_id") == correlation_id
        ]


class PerformanceMetrics:
    """Performance metrics collection and analysis."""

    def __init__(self, retention_seconds: int = DEFAULT_METRICS_RETENTION):
        """Initialize performance metrics.

        Args:
            retention_seconds: Metrics retention time in seconds
        """
        self.retention_seconds = retention_seconds
        self.metrics = defaultdict(lambda: deque(maxlen=MAX_METRICS_HISTORY))
        self.lock = threading.Lock()

    def record_metric(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a performance metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        timestamp = time.time()
        metric_entry = {"timestamp": timestamp, "value": value, "tags": tags or {}}

        with self.lock:
            self.metrics[metric_name].append(metric_entry)
            self._cleanup_old_metrics()

    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = time.time() - self.retention_seconds

        for metric_name in list(self.metrics.keys()):
            # Remove old entries
            while (
                self.metrics[metric_name]
                and self.metrics[metric_name][0]["timestamp"] < cutoff_time
            ):
                self.metrics[metric_name].popleft()

            # Remove empty metrics
            if not self.metrics[metric_name]:
                del self.metrics[metric_name]

    def get_metric_stats(
        self, metric_name: str, window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get statistics for a metric.

        Args:
            metric_name: Name of the metric
            window_seconds: Time window for statistics (None for all time)

        Returns:
            Metric statistics
        """
        if metric_name not in self.metrics:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        with self.lock:
            entries = list(self.metrics[metric_name])

            if window_seconds:
                cutoff_time = time.time() - window_seconds
                entries = [e for e in entries if e["timestamp"] >= cutoff_time]

            if not entries:
                return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

            values = [e["value"] for e in entries]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
            }

    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all metrics.

        Returns:
            Dictionary of all metrics
        """
        with self.lock:
            return {name: list(entries) for name, entries in self.metrics.items()}


class ResourceMonitor:
    """System resource monitoring."""

    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process()
        self.start_time = time.time()

    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage.

        Returns:
            System resource information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {"percent": cpu_percent, "count": psutil.cpu_count()},
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            }
        except Exception as e:
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def get_process_resources(self) -> Dict[str, Any]:
        """Get current process resource usage.

        Returns:
            Process resource information
        """
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()

            return {
                "timestamp": datetime.now().isoformat(),
                "pid": self.process.pid,
                "cpu_percent": cpu_percent,
                "memory": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": self.process.memory_percent(),
                },
                "threads": self.process.num_threads(),
                "open_files": len(self.process.open_files()),
                "connections": len(self.process.net_connections()),
            }
        except Exception as e:
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def get_uptime(self) -> float:
        """Get process uptime in seconds.

        Returns:
            Process uptime
        """
        return time.time() - self.start_time


class MonitoringManager:
    """Central monitoring manager."""

    def __init__(self, log_file: Optional[str] = None):
        """Initialize monitoring manager.

        Args:
            log_file: Optional log file path
        """
        self.logger = StructuredLogger("milkbottle.monitoring", log_file)
        self.metrics = PerformanceMetrics()
        self.resource_monitor = ResourceMonitor()
        self.monitoring_enabled = True
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

    def start_monitoring(self, interval_seconds: int = 30):
        """Start background monitoring.

        Args:
            interval_seconds: Monitoring interval in seconds
        """
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval_seconds,), daemon=True
        )
        self._monitoring_thread.start()
        self.logger.info(
            "Started background monitoring", interval_seconds=interval_seconds
        )

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        self.logger.info("Stopped background monitoring")

    def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop.

        Args:
            interval_seconds: Monitoring interval
        """
        while not self._stop_monitoring.wait(interval_seconds):
            try:
                # Record system resources
                system_resources = self.resource_monitor.get_system_resources()
                self.metrics.record_metric(
                    "system.cpu_percent", system_resources["cpu"]["percent"]
                )
                self.metrics.record_metric(
                    "system.memory_percent", system_resources["memory"]["percent"]
                )
                self.metrics.record_metric(
                    "system.disk_percent", system_resources["disk"]["percent"]
                )

                # Record process resources
                process_resources = self.resource_monitor.get_process_resources()
                self.metrics.record_metric(
                    "process.cpu_percent", process_resources["cpu_percent"]
                )
                self.metrics.record_metric(
                    "process.memory_mb",
                    process_resources["memory"]["rss"] / 1024 / 1024,
                )
                self.metrics.record_metric(
                    "process.threads", process_resources["threads"]
                )

                # Log resource usage
                self.logger.debug(
                    "Resource monitoring",
                    system=system_resources,
                    process=process_resources,
                )

            except Exception as e:
                self.logger.error("Monitoring error", error=str(e))

    def record_operation(
        self, operation_name: str, duration: float, success: bool = True, **kwargs
    ):
        """Record operation metrics.

        Args:
            operation_name: Name of the operation
            duration: Operation duration in seconds
            success: Whether operation was successful
            **kwargs: Additional operation data
        """
        # Record timing metrics
        self.metrics.record_metric(f"operation.{operation_name}.duration", duration)
        self.metrics.record_metric(
            f"operation.{operation_name}.success_rate", 1.0 if success else 0.0
        )

        # Log operation
        log_level = "info" if success else "error"
        getattr(self.logger, log_level)(
            f"Operation completed: {operation_name}",
            duration=duration,
            success=success,
            **kwargs,
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status.

        Returns:
            Health status information
        """
        try:
            # Get resource usage
            system_resources = self.resource_monitor.get_system_resources()
            process_resources = self.resource_monitor.get_process_resources()

            # Check for issues
            issues = []
            warnings = []

            # CPU usage
            if system_resources["cpu"]["percent"] > 90:
                issues.append("High CPU usage")
            elif system_resources["cpu"]["percent"] > 70:
                warnings.append("Elevated CPU usage")

            # Memory usage
            if system_resources["memory"]["percent"] > 90:
                issues.append("High memory usage")
            elif system_resources["memory"]["percent"] > 80:
                warnings.append("Elevated memory usage")

            # Disk usage
            if system_resources["disk"]["percent"] > 90:
                issues.append("High disk usage")
            elif system_resources["disk"]["percent"] > 80:
                warnings.append("Elevated disk usage")

            return {
                "status": "healthy" if not issues else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": self.resource_monitor.get_uptime(),
                "system_resources": system_resources,
                "process_resources": process_resources,
                "issues": issues,
                "warnings": warnings,
            }

        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def print_status(self):
        """Print monitoring status."""
        health = self.get_health_status()

        # Health status panel
        status_color = {"healthy": "green", "unhealthy": "red", "error": "red"}.get(
            health["status"], "yellow"
        )

        health_panel = Panel(
            f"Status: [{status_color}]{health['status'].upper()}[/{status_color}]\n"
            f"Uptime: {health['uptime']:.1f}s\n"
            f"Issues: {len(health.get('issues', []))}\n"
            f"Warnings: {len(health.get('warnings', []))}",
            title="System Health",
            border_style=status_color,
        )

        console.print(health_panel)

        # Resource usage table
        if "system_resources" in health:
            resources = health["system_resources"]

            table = Table(title="Resource Usage")
            table.add_column("Resource", style="cyan")
            table.add_column("Usage", style="green")
            table.add_column("Status", style="yellow")

            # CPU
            cpu_percent = resources["cpu"]["percent"]
            cpu_status = (
                "High"
                if cpu_percent > 90
                else "Elevated" if cpu_percent > 70 else "Normal"
            )
            table.add_row("CPU", f"{cpu_percent:.1f}%", cpu_status)

            # Memory
            memory_percent = resources["memory"]["percent"]
            memory_status = (
                "High"
                if memory_percent > 90
                else "Elevated" if memory_percent > 80 else "Normal"
            )
            table.add_row("Memory", f"{memory_percent:.1f}%", memory_status)

            # Disk
            disk_percent = resources["disk"]["percent"]
            disk_status = (
                "High"
                if disk_percent > 90
                else "Elevated" if disk_percent > 80 else "Normal"
            )
            table.add_row("Disk", f"{disk_percent:.1f}%", disk_status)

            console.print(table)

        # Issues and warnings
        if health.get("issues"):
            console.print(
                Panel(
                    "\n".join(f"• {issue}" for issue in health["issues"]),
                    title="Issues",
                    border_style="red",
                )
            )

        if health.get("warnings"):
            console.print(
                Panel(
                    "\n".join(f"• {warning}" for warning in health["warnings"]),
                    title="Warnings",
                    border_style="yellow",
                )
            )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Metrics summary
        """
        summary = {}

        # Get stats for common metrics
        common_metrics = [
            "system.cpu_percent",
            "system.memory_percent",
            "system.disk_percent",
            "process.cpu_percent",
            "process.memory_mb",
        ]

        for metric in common_metrics:
            stats = self.metrics.get_metric_stats(
                metric, window_seconds=300
            )  # Last 5 minutes
            if stats["count"] > 0:
                summary[metric] = stats

        return summary


# Global monitoring manager instance
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager(log_file: Optional[str] = None) -> MonitoringManager:
    """Get global monitoring manager instance.

    Args:
        log_file: Optional log file path

    Returns:
        Monitoring manager instance
    """
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager(log_file)
    return _monitoring_manager


def record_operation(
    operation_name: str, duration: float, success: bool = True, **kwargs
):
    """Record operation metrics.

    Args:
        operation_name: Name of the operation
        duration: Operation duration in seconds
        success: Whether operation was successful
        **kwargs: Additional operation data
    """
    manager = get_monitoring_manager()
    manager.record_operation(operation_name, duration, success, **kwargs)


def get_health_status() -> Dict[str, Any]:
    """Get system health status.

    Returns:
        Health status information
    """
    return get_monitoring_manager().get_health_status()


def print_monitoring_status():
    """Print monitoring status."""
    get_monitoring_manager().print_status()


def start_monitoring(interval_seconds: int = 30):
    """Start background monitoring.

    Args:
        interval_seconds: Monitoring interval in seconds
    """
    get_monitoring_manager().start_monitoring(interval_seconds)


def stop_monitoring():
    """Stop background monitoring."""
    get_monitoring_manager().stop_monitoring()
