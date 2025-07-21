"""Resource optimization system for MilkBottle."""

from __future__ import annotations

import contextlib
import gc
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger("milkbottle.resource_optimizer")


@dataclass
class ResourceUsage:
    """System resource usage information."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available_gb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_free_gb: float = 0.0
    network_io_sent_mb: float = 0.0
    network_io_recv_mb: float = 0.0
    open_files: int = 0
    active_connections: int = 0


@dataclass
class OptimizationResult:
    """Result of resource optimization."""

    optimization_type: str
    success: bool
    improvement: float
    details: str
    timestamp: float = field(default_factory=time.time)


class ResourceOptimizer:
    """System resource optimization and monitoring."""

    def __init__(self, optimization_threshold: float = 0.1):
        """Initialize resource optimizer.

        Args:
            optimization_threshold: Threshold for optimization improvements
        """
        self.optimization_threshold = optimization_threshold
        self.optimization_history: List[OptimizationResult] = []
        self.monitoring_active = False

        # Resource limits
        self.limits = {
            "max_memory_percent": 85.0,
            "max_cpu_percent": 90.0,
            "max_disk_percent": 90.0,
            "min_memory_available_gb": 1.0,
        }

        logger.info("Resource optimizer initialized")

    def get_resource_usage(self) -> ResourceUsage:
        """Get current system resource usage.

        Returns:
            Current resource usage information
        """
        if not PSUTIL_AVAILABLE:
            return ResourceUsage()

        try:
            return self._extracted_from_get_resource_usage_12()
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return ResourceUsage()

    # TODO Rename this here and in `get_resource_usage`
    def _extracted_from_get_resource_usage_12(self):
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1) if psutil else 0.0

        # Memory usage
        memory = psutil.virtual_memory() if psutil else None
        memory_percent = memory.percent if memory else 0.0
        memory_available_gb = memory.available / (1024**3) if memory else 0.0

        # Disk usage
        disk = psutil.disk_usage("/") if psutil else None
        disk_usage_percent = disk.percent if disk else 0.0
        disk_free_gb = disk.free / (1024**3) if disk else 0.0

        # Network I/O
        network = psutil.net_io_counters() if psutil else None
        network_io_sent_mb = network.bytes_sent / (1024**2) if network else 0.0
        network_io_recv_mb = network.bytes_recv / (1024**2) if network else 0.0

        # Process information
        process = psutil.Process() if psutil else None
        open_files = len(process.open_files()) if process else 0
        connections = len(process.connections()) if process else 0

        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb,
            open_files=open_files,
            active_connections=connections,
        )

    def optimize(self) -> Dict[str, Any]:
        """Run comprehensive resource optimization.

        Returns:
            Dictionary with optimization results
        """
        # Memory optimization
        memory_result = self._optimize_memory()
        optimizations = {"memory": memory_result}
        # CPU optimization
        cpu_result = self._optimize_cpu()
        optimizations["cpu"] = cpu_result

        # Disk optimization
        disk_result = self._optimize_disk()
        optimizations["disk"] = disk_result

        # Network optimization
        network_result = self._optimize_network()
        optimizations["network"] = network_result

        # File handle optimization
        file_result = self._optimize_file_handles()
        optimizations["file_handles"] = file_result

        # Garbage collection
        gc_result = self._optimize_garbage_collection()
        optimizations["garbage_collection"] = gc_result

        logger.info("Resource optimization completed")
        return optimizations

    def _optimize_memory(self) -> OptimizationResult:
        """Optimize memory usage."""
        try:
            before_usage = self.get_resource_usage()

            # Force garbage collection
            collected = gc.collect()

            # Clear Python cache
            import sys

            if hasattr(sys, "intern"):
                sys.intern.clear()

            after_usage = self.get_resource_usage()

            improvement = before_usage.memory_percent - after_usage.memory_percent

            result = OptimizationResult(
                optimization_type="memory",
                success=improvement > self.optimization_threshold,
                improvement=improvement,
                details=f"Garbage collection freed {collected} objects, memory usage reduced by {improvement:.2f}%",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return OptimizationResult(
                optimization_type="memory",
                success=False,
                improvement=0.0,
                details=f"Memory optimization failed: {e}",
            )

    def _optimize_cpu(self) -> OptimizationResult:
        """Optimize CPU usage."""
        try:
            before_usage = self.get_resource_usage()

            if PSUTIL_AVAILABLE and psutil:
                # Check for high CPU processes
                high_cpu_processes = []
                for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
                    with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                        if proc.info["cpu_percent"] > 50:
                            high_cpu_processes.append(proc.info)
            # Suggest CPU optimizations
            suggestions = []
            if before_usage.cpu_percent > self.limits["max_cpu_percent"]:
                suggestions.extend(
                    (
                        "Consider reducing parallel processing",
                        "Check for CPU-intensive operations",
                    )
                )
            improvement = 1.0 if suggestions else 0.0
            result = OptimizationResult(
                optimization_type="cpu",
                success=before_usage.cpu_percent < self.limits["max_cpu_percent"],
                improvement=improvement,
                details=f"CPU usage: {before_usage.cpu_percent:.1f}%. Suggestions: {'; '.join(suggestions)}",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            return OptimizationResult(
                optimization_type="cpu",
                success=False,
                improvement=0.0,
                details=f"CPU optimization failed: {e}",
            )

    def _optimize_disk(self) -> OptimizationResult:
        """Optimize disk usage."""
        try:
            before_usage = self.get_resource_usage()

            # Check disk space
            suggestions = []
            if before_usage.disk_usage_percent > self.limits["max_disk_percent"]:
                suggestions.extend(
                    (
                        "Consider cleaning temporary files",
                        "Check for large log files",
                        "Review cache directories",
                    )
                )
            # Check for temporary files
            temp_dirs = ["/tmp", "/var/tmp", str(Path.home() / ".cache")]
            temp_files = []

            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    with contextlib.suppress(PermissionError):
                        temp_files.extend(
                            str(file_path)
                            for file_path in temp_path.rglob("*")
                            if (
                                file_path.is_file()
                                and file_path.stat().st_size > 10 * 1024 * 1024
                            )
                        )
            improvement = 1.0 if suggestions else 0.0
            result = OptimizationResult(
                optimization_type="disk",
                success=before_usage.disk_usage_percent
                < self.limits["max_disk_percent"],
                improvement=improvement,
                details=f"Disk usage: {before_usage.disk_usage_percent:.1f}%. Suggestions: {'; '.join(suggestions)}",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Disk optimization failed: {e}")
            return OptimizationResult(
                optimization_type="disk",
                success=False,
                improvement=0.0,
                details=f"Disk optimization failed: {e}",
            )

    def _optimize_network(self) -> OptimizationResult:
        """Optimize network usage."""
        try:
            before_usage = self.get_resource_usage()

            # Network optimization suggestions
            suggestions = []
            if (
                before_usage.network_io_sent_mb > 100
                or before_usage.network_io_recv_mb > 100
            ):
                suggestions.extend(
                    (
                        "Consider implementing connection pooling",
                        "Check for unnecessary network requests",
                        "Implement request caching",
                    )
                )
            improvement = 1.0 if suggestions else 0.0
            result = OptimizationResult(
                optimization_type="network",
                success=not suggestions,
                improvement=improvement,
                details=f"Network I/O: {before_usage.network_io_sent_mb:.1f}MB sent, {before_usage.network_io_recv_mb:.1f}MB received. Suggestions: {'; '.join(suggestions)}",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Network optimization failed: {e}")
            return OptimizationResult(
                optimization_type="network",
                success=False,
                improvement=0.0,
                details=f"Network optimization failed: {e}",
            )

    def _optimize_file_handles(self) -> OptimizationResult:
        """Optimize file handle usage."""
        try:
            before_usage = self.get_resource_usage()

            suggestions = []
            if before_usage.open_files > 100:
                suggestions.extend(
                    (
                        "Consider using context managers for file operations",
                        "Implement file handle pooling",
                        "Check for unclosed file handles",
                    )
                )
            improvement = 1.0 if suggestions else 0.0
            result = OptimizationResult(
                optimization_type="file_handles",
                success=before_usage.open_files < 100,
                improvement=improvement,
                details=f"Open files: {before_usage.open_files}. Suggestions: {'; '.join(suggestions)}",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"File handle optimization failed: {e}")
            return OptimizationResult(
                optimization_type="file_handles",
                success=False,
                improvement=0.0,
                details=f"File handle optimization failed: {e}",
            )

    def _optimize_garbage_collection(self) -> OptimizationResult:
        """Optimize garbage collection."""
        try:
            # Get garbage collection statistics
            gc_stats = gc.get_stats()

            # Force garbage collection
            collected = gc.collect()

            # Get statistics after collection
            after_stats = gc.get_stats()

            improvement = collected if collected > 0 else 0.0

            # Calculate improvement based on stats comparison
            before_count = sum(stat.get("collections", 0) for stat in gc_stats)
            after_count = sum(stat.get("collections", 0) for stat in after_stats)
            stats_improvement = after_count - before_count

            result = OptimizationResult(
                optimization_type="garbage_collection",
                success=collected > 0,
                improvement=improvement,
                details=f"Garbage collection freed {collected} objects, stats improvement: {stats_improvement}",
            )

            self.optimization_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Garbage collection optimization failed: {e}")
            return OptimizationResult(
                optimization_type="garbage_collection",
                success=False,
                improvement=0.0,
                details=f"Garbage collection optimization failed: {e}",
            )

    def set_resource_limit(self, resource: str, limit: float) -> None:
        """Set a resource limit.

        Args:
            resource: Resource name (e.g., 'max_memory_percent')
            limit: Limit value
        """
        if resource in self.limits:
            self.limits[resource] = limit
            logger.info(f"Set {resource} limit to {limit}")
        else:
            logger.warning(f"Unknown resource limit: {resource}")

    def get_optimization_history(self) -> List[OptimizationResult]:
        """Get optimization history.

        Returns:
            List of optimization results
        """
        return self.optimization_history.copy()

    def clear_optimization_history(self) -> None:
        """Clear optimization history."""
        self.optimization_history.clear()
        logger.info("Optimization history cleared")

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report.

        Returns:
            Optimization report dictionary
        """
        current_usage = self.get_resource_usage()

        # Calculate optimization success rate
        successful_optimizations = sum(
            bool(opt.success) for opt in self.optimization_history
        )
        total_optimizations = len(self.optimization_history)
        success_rate = (
            successful_optimizations / total_optimizations
            if total_optimizations > 0
            else 0
        )

        # Get recent optimizations
        recent_optimizations = (
            self.optimization_history[-10:] if self.optimization_history else []
        )

        return {
            "current_usage": {
                "cpu_percent": current_usage.cpu_percent,
                "memory_percent": current_usage.memory_percent,
                "memory_available_gb": current_usage.memory_available_gb,
                "disk_usage_percent": current_usage.disk_usage_percent,
                "disk_free_gb": current_usage.disk_free_gb,
                "open_files": current_usage.open_files,
                "active_connections": current_usage.active_connections,
            },
            "limits": self.limits,
            "optimization_history": {
                "total_optimizations": total_optimizations,
                "successful_optimizations": successful_optimizations,
                "success_rate": success_rate,
                "recent_optimizations": [
                    {
                        "type": opt.optimization_type,
                        "success": opt.success,
                        "improvement": opt.improvement,
                        "details": opt.details,
                        "timestamp": opt.timestamp,
                    }
                    for opt in recent_optimizations
                ],
            },
        }
