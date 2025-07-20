"""Monitoring Manager - Application and system monitoring."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import yaml
from rich.console import Console

from ..config import MilkBottleConfig


@dataclass
class SystemMetrics:
    """System performance metrics."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    load_average: List[float]
    uptime: float


@dataclass
class ApplicationMetrics:
    """Application performance metrics."""

    timestamp: str
    response_time: float
    request_count: int
    error_count: int
    active_connections: int
    memory_usage: float
    cpu_usage: float


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    metric: str
    threshold: float
    operator: str  # >, <, >=, <=, ==
    duration: int  # seconds
    severity: str  # info, warning, critical
    message: str
    enabled: bool = True


@dataclass
class Alert:
    """Alert information."""

    rule_name: str
    severity: str
    message: str
    timestamp: str
    value: float
    threshold: float
    acknowledged: bool = False


class MonitoringManager:
    """Application and system monitoring management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.monitoring")
        self.monitoring_active = False
        self.metrics_dir = Path.home() / ".milkbottle" / "monitoring"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.system_metrics: List[SystemMetrics] = []
        self.application_metrics: List[ApplicationMetrics] = []
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: List[Alert] = []

        # Load default alert rules
        self._load_default_alert_rules()

    async def start_monitoring(self, interval: int = 60) -> bool:
        """Start monitoring with specified interval."""
        try:
            self.logger.info(f"Starting monitoring with {interval}s interval")
            self.monitoring_active = True

            while self.monitoring_active:
                # Collect metrics
                await self._collect_system_metrics()
                await self._collect_application_metrics()

                # Check alerts
                await self._check_alerts()

                # Save metrics
                await self._save_metrics()

                # Wait for next interval
                await asyncio.sleep(interval)

            return True

        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
            return False

    async def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.logger.info("Stopping monitoring")
        self.monitoring_active = False

    async def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Get recent system metrics."""
        return self.system_metrics[-limit:] if self.system_metrics else []

    async def collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect current system metrics (public method for CLI)."""
        try:
            await self._collect_system_metrics()
            return self.system_metrics[-1] if self.system_metrics else None
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return None

    async def get_application_metrics(
        self, limit: int = 100
    ) -> List[ApplicationMetrics]:
        """Get recent application metrics."""
        return self.application_metrics[-limit:] if self.application_metrics else []

    async def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule."""
        try:
            self.alert_rules.append(rule)
            self.logger.info(f"Added alert rule: {rule.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add alert rule: {e}")
            return False

    async def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        try:
            self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
            self.logger.info(f"Removed alert rule: {rule_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove alert rule: {e}")
            return False

    async def get_active_alerts(self) -> List[Alert]:
        """Get active alerts."""
        return [a for a in self.active_alerts if not a.acknowledged]

    async def acknowledge_alert(self, rule_name: str) -> bool:
        """Acknowledge an alert."""
        try:
            for alert in self.active_alerts:
                if alert.rule_name == rule_name and not alert.acknowledged:
                    alert.acknowledged = True
                    self.logger.info(f"Acknowledged alert: {rule_name}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}")
            return False

    async def generate_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """Generate monitoring report."""
        try:
            if report_type == "summary":
                return await self._generate_summary_report()
            elif report_type == "detailed":
                return await self._generate_detailed_report()
            elif report_type == "alerts":
                return await self._generate_alerts_report()
            else:
                self.logger.error(f"Unknown report type: {report_type}")
                return {}

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return {}

    async def export_metrics(
        self,
        format: str = "json",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> bool:
        """Export metrics to file."""
        try:
            # Filter metrics by time range
            system_metrics = self._filter_metrics_by_time(
                self.system_metrics, start_time, end_time
            )
            app_metrics = self._filter_metrics_by_time(
                self.application_metrics, start_time, end_time
            )

            if format == "csv":
                await self._export_csv_metrics(system_metrics, app_metrics)

            elif format == "json":
                export_data = {
                    "system_metrics": [m.__dict__ for m in system_metrics],
                    "application_metrics": [m.__dict__ for m in app_metrics],
                    "export_time": self._get_timestamp(),
                }

                export_file = (
                    self.metrics_dir / f"metrics_export_{self._get_timestamp()}.json"
                )
                with open(export_file, "w") as f:
                    json.dump(export_data, f, indent=2)

            elif format == "yaml":
                export_data = {
                    "system_metrics": [m.__dict__ for m in system_metrics],
                    "application_metrics": [m.__dict__ for m in app_metrics],
                    "export_time": self._get_timestamp(),
                }

                export_file = (
                    self.metrics_dir / f"metrics_export_{self._get_timestamp()}.yaml"
                )
                with open(export_file, "w") as f:
                    yaml.dump(export_data, f, default_flow_style=False)

            self.logger.info(f"Exported metrics to {export_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent

            # Network I/O
            network_io = psutil.net_io_counters()
            network_data = {
                "bytes_sent": float(network_io.bytes_sent),
                "bytes_recv": float(network_io.bytes_recv),
                "packets_sent": float(network_io.packets_sent),
                "packets_recv": float(network_io.packets_recv),
            }

            # Load average
            load_average = list(psutil.getloadavg())

            # Uptime
            uptime = time.time() - psutil.boot_time()

            # Create metrics object
            metrics = SystemMetrics(
                timestamp=self._get_timestamp(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_data,
                load_average=load_average,
                uptime=uptime,
            )

            self.system_metrics.append(metrics)

            # Keep only last 1000 metrics
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    async def _collect_application_metrics(self) -> None:
        """Collect application performance metrics."""
        try:
            # This would typically come from application instrumentation
            # For now, use placeholder values
            metrics = ApplicationMetrics(
                timestamp=self._get_timestamp(),
                response_time=0.1,  # Placeholder
                request_count=0,  # Placeholder
                error_count=0,  # Placeholder
                active_connections=0,  # Placeholder
                memory_usage=psutil.Process().memory_percent(),
                cpu_usage=psutil.Process().cpu_percent(),
            )

            self.application_metrics.append(metrics)

            # Keep only last 1000 metrics
            if len(self.application_metrics) > 1000:
                self.application_metrics = self.application_metrics[-1000:]

        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {e}")

    async def _check_alerts(self) -> None:
        """Check alert rules and trigger alerts."""
        try:
            if not self.system_metrics or not self.application_metrics:
                return

            latest_system = self.system_metrics[-1]
            latest_app = self.application_metrics[-1]

            for rule in self.alert_rules:
                if not rule.enabled:
                    continue

                # Get metric value
                metric_value = self._get_metric_value(
                    rule.metric, latest_system, latest_app
                )
                if metric_value is None:
                    continue

                # Check threshold
                if self._check_threshold(metric_value, rule.threshold, rule.operator):
                    # Check if alert already exists
                    existing_alert = next(
                        (
                            a
                            for a in self.active_alerts
                            if a.rule_name == rule.name and not a.acknowledged
                        ),
                        None,
                    )

                    if not existing_alert:
                        # Create new alert
                        alert = Alert(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=rule.message,
                            timestamp=self._get_timestamp(),
                            value=metric_value,
                            threshold=rule.threshold,
                        )
                        self.active_alerts.append(alert)
                        self.logger.warning(
                            f"Alert triggered: {rule.name} - {rule.message}"
                        )

        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")

    def _get_metric_value(
        self,
        metric: str,
        system_metrics: SystemMetrics,
        app_metrics: ApplicationMetrics,
    ) -> Optional[float]:
        """Get metric value from metrics objects."""
        if metric == "cpu_percent":
            return system_metrics.cpu_percent
        elif metric == "memory_percent":
            return system_metrics.memory_percent
        elif metric == "disk_usage_percent":
            return system_metrics.disk_usage_percent
        elif metric == "response_time":
            return app_metrics.response_time
        elif metric == "error_count":
            return app_metrics.error_count
        elif metric == "active_connections":
            return app_metrics.active_connections
        else:
            return None

    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value meets threshold condition."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        else:
            return False

    async def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            metrics_file = self.metrics_dir / "metrics.json"

            metrics_data = {
                "system_metrics": [m.__dict__ for m in self.system_metrics[-100:]],
                "application_metrics": [
                    m.__dict__ for m in self.application_metrics[-100:]
                ],
                "last_updated": self._get_timestamp(),
            }

            with open(metrics_file, "w") as f:
                json.dump(metrics_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def _filter_metrics_by_time(
        self, metrics: List, start_time: Optional[str], end_time: Optional[str]
    ) -> List:
        """Filter metrics by time range."""
        if not start_time and not end_time:
            return metrics

        filtered_metrics = []
        for metric in metrics:
            if start_time and metric.timestamp < start_time:
                continue
            if end_time and metric.timestamp > end_time:
                continue
            filtered_metrics.append(metric)

        return filtered_metrics

    async def _export_csv_metrics(
        self, system_metrics: List[SystemMetrics], app_metrics: List[ApplicationMetrics]
    ) -> None:
        """Export metrics to CSV format."""
        import csv

        export_file = self.metrics_dir / f"metrics_export_{self._get_timestamp()}.csv"

        with open(export_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write system metrics
            writer.writerow(["System Metrics"])
            writer.writerow(["Timestamp", "CPU %", "Memory %", "Disk %", "Uptime"])
            for metric in system_metrics:
                writer.writerow(
                    [
                        metric.timestamp,
                        metric.cpu_percent,
                        metric.memory_percent,
                        metric.disk_usage_percent,
                        metric.uptime,
                    ]
                )

            writer.writerow([])  # Empty row

            # Write application metrics
            writer.writerow(["Application Metrics"])
            writer.writerow(
                ["Timestamp", "Response Time", "Request Count", "Error Count", "CPU %"]
            )
            for metric in app_metrics:
                writer.writerow(
                    [
                        metric.timestamp,
                        metric.response_time,
                        metric.request_count,
                        metric.error_count,
                        metric.cpu_usage,
                    ]
                )

    async def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary monitoring report."""
        if not self.system_metrics or not self.application_metrics:
            return {"error": "No metrics available"}

        latest_system = self.system_metrics[-1]
        latest_app = self.application_metrics[-1]

        return {
            "report_type": "summary",
            "timestamp": self._get_timestamp(),
            "system_health": {
                "cpu_usage": latest_system.cpu_percent,
                "memory_usage": latest_system.memory_percent,
                "disk_usage": latest_system.disk_usage_percent,
                "uptime": latest_system.uptime,
            },
            "application_health": {
                "response_time": latest_app.response_time,
                "request_count": latest_app.request_count,
                "error_count": latest_app.error_count,
                "active_connections": latest_app.active_connections,
            },
            "active_alerts": len([a for a in self.active_alerts if not a.acknowledged]),
        }

    async def _generate_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed monitoring report."""
        return {
            "report_type": "detailed",
            "timestamp": self._get_timestamp(),
            "system_metrics_count": len(self.system_metrics),
            "application_metrics_count": len(self.application_metrics),
            "alert_rules_count": len(self.alert_rules),
            "active_alerts_count": len(
                [a for a in self.active_alerts if not a.acknowledged]
            ),
            "recent_system_metrics": [m.__dict__ for m in self.system_metrics[-10:]],
            "recent_application_metrics": [
                m.__dict__ for m in self.application_metrics[-10:]
            ],
        }

    async def _generate_alerts_report(self) -> Dict[str, Any]:
        """Generate alerts report."""
        return {
            "report_type": "alerts",
            "timestamp": self._get_timestamp(),
            "alert_rules": [r.__dict__ for r in self.alert_rules],
            "active_alerts": [
                a.__dict__ for a in self.active_alerts if not a.acknowledged
            ],
            "acknowledged_alerts": [
                a.__dict__ for a in self.active_alerts if a.acknowledged
            ],
        }

    def _load_default_alert_rules(self) -> None:
        """Load default alert rules."""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                metric="cpu_percent",
                threshold=80.0,
                operator=">",
                duration=300,
                severity="warning",
                message="CPU usage is above 80%",
            ),
            AlertRule(
                name="High Memory Usage",
                metric="memory_percent",
                threshold=90.0,
                operator=">",
                duration=300,
                severity="critical",
                message="Memory usage is above 90%",
            ),
            AlertRule(
                name="High Disk Usage",
                metric="disk_usage_percent",
                threshold=85.0,
                operator=">",
                duration=300,
                severity="warning",
                message="Disk usage is above 85%",
            ),
            AlertRule(
                name="High Error Rate",
                metric="error_count",
                threshold=10,
                operator=">",
                duration=60,
                severity="critical",
                message="Error count is above 10",
            ),
        ]

        self.alert_rules.extend(default_rules)

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
