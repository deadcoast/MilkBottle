"""Performance monitoring system for MilkBottle."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger("milkbottle.performance_monitor")


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""

    timestamp: float
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_available: float = 0.0
    disk_io_read: float = 0.0
    disk_io_write: float = 0.0
    network_io_sent: float = 0.0
    network_io_recv: float = 0.0
    response_time: float = 0.0
    throughput: float = 0.0
    active_threads: int = 0
    active_processes: int = 0


@dataclass
class FunctionProfile:
    """Function profiling data."""

    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_called: float = 0.0


class PerformanceMonitor:
    """System performance monitoring and profiling."""

    def __init__(self, max_history: int = 1000, monitoring_interval: float = 1.0):
        """Initialize performance monitor.

        Args:
            max_history: Maximum number of metrics to keep in history
            monitoring_interval: Interval between monitoring samples in seconds
        """
        self.max_history = max_history
        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Metrics storage
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=max_history)
        self.function_profiles: Dict[str, FunctionProfile] = {}

        # Performance thresholds
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "response_time_warning": 1.0,
            "response_time_critical": 5.0,
        }

        # Event callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            "cpu_warning": [],
            "cpu_critical": [],
            "memory_warning": [],
            "memory_critical": [],
            "response_time_warning": [],
            "response_time_critical": [],
        }

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.monitoring:
            logger.warning("Performance monitoring already started")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self.monitoring:
            logger.warning("Performance monitoring not running")
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system metrics.

        Returns:
            Current performance metrics
        """
        if not PSUTIL_AVAILABLE:
            return PerformanceMetrics(timestamp=time.time())

        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1) if psutil else 0.0

            # Memory usage
            memory = psutil.virtual_memory() if psutil else None
            memory_usage = memory.percent if memory else 0.0
            memory_available = memory.available / (1024**3) if memory else 0.0  # GB

            # Disk I/O
            disk_io = psutil.disk_io_counters() if psutil else None
            disk_io_read = disk_io.read_bytes / (1024**2) if disk_io else 0  # MB
            disk_io_write = disk_io.write_bytes / (1024**2) if disk_io else 0  # MB

            # Network I/O
            network_io = psutil.net_io_counters() if psutil else None
            network_io_sent = (
                network_io.bytes_sent / (1024**2) if network_io else 0
            )  # MB
            network_io_recv = (
                network_io.bytes_recv / (1024**2) if network_io else 0
            )  # MB

            # Process info
            active_threads = threading.active_count()
            active_processes = len(psutil.pids()) if psutil else 0

            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                memory_available=memory_available,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_io_sent=network_io_sent,
                network_io_recv=network_io_recv,
                active_threads=active_threads,
                active_processes=active_processes,
            )

            # Check thresholds and trigger callbacks
            self._check_thresholds(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return PerformanceMetrics(timestamp=time.time())

    def get_average_metrics(self, window: Optional[int] = None) -> PerformanceMetrics:
        """Get average metrics over a time window.

        Args:
            window: Number of recent metrics to average (None for all)

        Returns:
            Average performance metrics
        """
        if not self.metrics_history:
            return PerformanceMetrics(timestamp=time.time())

        # Get metrics to average
        if window is None:
            metrics_to_average = list(self.metrics_history)
        else:
            metrics_to_average = list(self.metrics_history)[-window:]

        if not metrics_to_average:
            return PerformanceMetrics(timestamp=time.time())

        # Calculate averages
        avg_metrics = PerformanceMetrics(timestamp=time.time())
        count = len(metrics_to_average)

        avg_metrics.cpu_usage = sum(m.cpu_usage for m in metrics_to_average) / count
        avg_metrics.memory_usage = (
            sum(m.memory_usage for m in metrics_to_average) / count
        )
        avg_metrics.memory_available = (
            sum(m.memory_available for m in metrics_to_average) / count
        )
        avg_metrics.disk_io_read = (
            sum(m.disk_io_read for m in metrics_to_average) / count
        )
        avg_metrics.disk_io_write = (
            sum(m.disk_io_write for m in metrics_to_average) / count
        )
        avg_metrics.network_io_sent = (
            sum(m.network_io_sent for m in metrics_to_average) / count
        )
        avg_metrics.network_io_recv = (
            sum(m.network_io_recv for m in metrics_to_average) / count
        )
        avg_metrics.response_time = (
            sum(m.response_time for m in metrics_to_average) / count
        )
        avg_metrics.throughput = sum(m.throughput for m in metrics_to_average) / count
        avg_metrics.active_threads = int(
            sum(m.active_threads for m in metrics_to_average) / count
        )
        avg_metrics.active_processes = int(
            sum(m.active_processes for m in metrics_to_average) / count
        )

        return avg_metrics

    def get_function_profile(self, function_name: str) -> Optional[FunctionProfile]:
        """Get profiling data for a function.

        Args:
            function_name: Name of the function

        Returns:
            Function profile or None if not found
        """
        return self.function_profiles.get(function_name)

    def get_all_function_profiles(self) -> Dict[str, FunctionProfile]:
        """Get all function profiles.

        Returns:
            Dictionary of all function profiles
        """
        return self.function_profiles.copy()

    def clear_function_profiles(self) -> None:
        """Clear all function profiles."""
        self.function_profiles.clear()
        logger.info("Function profiles cleared")

    def set_threshold(self, threshold_name: str, value: float) -> None:
        """Set a performance threshold.

        Args:
            threshold_name: Name of the threshold
            value: Threshold value
        """
        if threshold_name in self.thresholds:
            self.thresholds[threshold_name] = value
            logger.info(f"Set threshold {threshold_name} to {value}")
        else:
            logger.warning(f"Unknown threshold: {threshold_name}")

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for performance events.

        Args:
            event: Event name (e.g., 'cpu_warning', 'memory_critical')
            callback: Callback function
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.info(f"Added callback for event: {event}")
        else:
            logger.warning(f"Unknown event: {event}")

    def remove_callback(self, event: str, callback: Callable) -> None:
        """Remove a callback for performance events.

        Args:
            event: Event name
            callback: Callback function to remove
        """
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
            logger.info(f"Removed callback for event: {event}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report.

        Returns:
            Performance report dictionary
        """
        current_metrics = self.get_current_metrics()
        avg_metrics = self.get_average_metrics()

        # Calculate performance trends
        if len(self.metrics_history) >= 2:
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 samples
            cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
            memory_trend = self._calculate_trend(
                [m.memory_usage for m in recent_metrics]
            )
        else:
            cpu_trend = "stable"
            memory_trend = "stable"

        # Function profiling summary
        function_summary = {}
        for name, profile in self.function_profiles.items():
            function_summary[name] = {
                "call_count": profile.call_count,
                "avg_time": profile.avg_time,
                "min_time": profile.min_time,
                "max_time": profile.max_time,
                "last_called": profile.last_called,
            }

        return {
            "current_metrics": {
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "memory_available_gb": current_metrics.memory_available,
                "active_threads": current_metrics.active_threads,
                "active_processes": current_metrics.active_processes,
            },
            "average_metrics": {
                "cpu_usage": avg_metrics.cpu_usage,
                "memory_usage": avg_metrics.memory_usage,
                "response_time": avg_metrics.response_time,
            },
            "trends": {"cpu_trend": cpu_trend, "memory_trend": memory_trend},
            "function_profiles": function_summary,
            "thresholds": self.thresholds,
            "monitoring_active": self.monitoring,
            "metrics_count": len(self.metrics_history),
        }

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check metrics against thresholds and trigger callbacks."""
        # CPU thresholds
        if metrics.cpu_usage >= self.thresholds["cpu_critical"]:
            self._trigger_callbacks("cpu_critical", metrics)
        elif metrics.cpu_usage >= self.thresholds["cpu_warning"]:
            self._trigger_callbacks("cpu_warning", metrics)

        # Memory thresholds
        if metrics.memory_usage >= self.thresholds["memory_critical"]:
            self._trigger_callbacks("memory_critical", metrics)
        elif metrics.memory_usage >= self.thresholds["memory_warning"]:
            self._trigger_callbacks("memory_warning", metrics)

        # Response time thresholds
        if metrics.response_time >= self.thresholds["response_time_critical"]:
            self._trigger_callbacks("response_time_critical", metrics)
        elif metrics.response_time >= self.thresholds["response_time_warning"]:
            self._trigger_callbacks("response_time_warning", metrics)

    def _trigger_callbacks(self, event: str, metrics: PerformanceMetrics) -> None:
        """Trigger callbacks for an event."""
        for callback in self.callbacks[event]:
            try:
                callback(event, metrics)
            except Exception as e:
                logger.error(f"Error in callback for event {event}: {e}")

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a list of values."""
        if len(values) < 2:
            return "stable"

        # Simple trend calculation
        first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
        second_half = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)

        diff = second_half - first_half
        if abs(diff) < 0.1:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

    def _record_function_call(self, function_name: str, execution_time: float) -> None:
        """Record a function call for profiling."""
        if function_name not in self.function_profiles:
            self.function_profiles[function_name] = FunctionProfile(
                function_name=function_name
            )

        profile = self.function_profiles[function_name]
        profile.call_count += 1
        profile.total_time += execution_time
        profile.avg_time = profile.total_time / profile.call_count
        profile.min_time = min(profile.min_time, execution_time)
        profile.max_time = max(profile.max_time, execution_time)
        profile.last_called = time.time()


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance.

    Args:
        func: Function to monitor

    Returns:
        Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record function call
            monitor = PerformanceMonitor()
            monitor._record_function_call(func.__name__, execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.3f}s: {e}"
            )
            raise

    return wrapper


def async_performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor async function performance.

    Args:
        func: Async function to monitor

    Returns:
        Decorated async function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record function call
            monitor = PerformanceMonitor()
            monitor._record_function_call(func.__name__, execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Async function {func.__name__} failed after {execution_time:.3f}s: {e}"
            )
            raise

    return wrapper
