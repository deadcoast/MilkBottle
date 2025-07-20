"""Performance Optimization System for MilkBottle."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil
from rich.console import Console

logger = logging.getLogger("milkbottle.performance")


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_io: Dict[str, float] = field(default_factory=dict)
    network_io: Dict[str, float] = field(default_factory=dict)
    response_time: float = 0.0
    throughput: float = 0.0
    timestamp: float = field(default_factory=time.time)


class CacheManager:
    """Intelligent caching system."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = {}
        self.logger = logging.getLogger("milkbottle.cache")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                # Update access count
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                return self.cache[key]
            else:
                # Expired, remove from cache
                self._remove_from_cache(key)
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if len(self.cache) >= self.max_size:
            # Remove least recently used entry
            self._evict_lru()

        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_counts[key] = 0

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        self.access_counts.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
            "memory_usage": self._estimate_memory_usage(),
        }

    def _remove_from_cache(self, key: str) -> None:
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            if key in self.access_counts:
                del self.access_counts[key]

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find least recently used key
        lru_key = min(self.access_counts.keys(), key=lambda k: self.access_counts[k])
        self._remove_from_cache(lru_key)

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_accesses = sum(self.access_counts.values())
        if total_accesses == 0:
            return 0.0
        return total_accesses / (total_accesses + len(self.cache))

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        # Rough estimation
        return len(self.cache) * 1024  # 1KB per entry


class PerformanceMonitor:
    """System performance monitoring."""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.performance")
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

    async def start_monitoring(self, interval: int = 60) -> bool:
        """Start performance monitoring."""
        try:
            if self.monitoring:
                self.logger.warning("Monitoring already started")
                return True

            self.monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
            self.logger.info("Performance monitoring started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitor_task
        self.logger.info("Performance monitoring stopped")

    async def _monitor_loop(self, interval: int) -> None:
        """Monitoring loop."""
        while self.monitoring:
            try:
                metrics = await self.collect_system_metrics()
                self.record_metrics(metrics)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_metrics = {
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0,
            }

            # Network I/O
            network_io = psutil.net_io_counters()
            network_metrics = {
                "bytes_sent": network_io.bytes_sent if network_io else 0,
                "bytes_recv": network_io.bytes_recv if network_io else 0,
                "packets_sent": network_io.packets_sent if network_io else 0,
                "packets_recv": network_io.packets_recv if network_io else 0,
            }

            return PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_io=disk_metrics,
                network_io=network_metrics,
                timestamp=time.time(),
            )

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics()

    def record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics."""
        self.metrics.append(metrics)

        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

    def get_average_metrics(self, minutes: int = 5) -> PerformanceMetrics:
        """Get average performance metrics for the last N minutes."""
        if not self.metrics:
            return PerformanceMetrics()

        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return PerformanceMetrics()

        avg_metrics = PerformanceMetrics()
        count = len(recent_metrics)

        avg_metrics.cpu_usage = sum(m.cpu_usage for m in recent_metrics) / count
        avg_metrics.memory_usage = sum(m.memory_usage for m in recent_metrics) / count
        avg_metrics.response_time = sum(m.response_time for m in recent_metrics) / count
        avg_metrics.throughput = sum(m.throughput for m in recent_metrics) / count

        return avg_metrics

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.metrics:
            return {"error": "No metrics available"}

        latest = self.metrics[-1]
        avg_5min = self.get_average_metrics(5)
        avg_1hour = self.get_average_metrics(60)

        return {
            "current": {
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage,
                "response_time": latest.response_time,
                "throughput": latest.throughput,
            },
            "average_5min": {
                "cpu_usage": avg_5min.cpu_usage,
                "memory_usage": avg_5min.memory_usage,
                "response_time": avg_5min.response_time,
                "throughput": avg_5min.throughput,
            },
            "average_1hour": {
                "cpu_usage": avg_1hour.cpu_usage,
                "memory_usage": avg_1hour.memory_usage,
                "response_time": avg_1hour.response_time,
                "throughput": avg_1hour.throughput,
            },
            "total_metrics": len(self.metrics),
        }


class ResourceOptimizer:
    """Resource optimization and management."""

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.resource_optimizer")

    async def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        try:
            # Get current memory usage
            memory = psutil.virtual_memory()

            # Force garbage collection
            import gc

            gc.collect()

            # Get memory after optimization
            memory_after = psutil.virtual_memory()

            freed_memory = memory.used - memory_after.used

            return {
                "success": True,
                "freed_memory_mb": freed_memory / (1024 * 1024),
                "memory_usage_before": memory.percent,
                "memory_usage_after": memory_after.percent,
            }

        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_disk_usage(self, path: Path) -> Dict[str, Any]:
        """Optimize disk usage for a specific path."""
        try:
            path = Path(path)
            if not path.exists():
                return {"success": False, "error": "Path does not exist"}

            # Calculate disk usage before
            usage_before = self._get_directory_size(path)

            # Remove temporary files
            temp_files_removed = await self._remove_temp_files(path)

            # Calculate disk usage after
            usage_after = self._get_directory_size(path)

            freed_space = usage_before - usage_after

            return {
                "success": True,
                "freed_space_mb": freed_space / (1024 * 1024),
                "temp_files_removed": temp_files_removed,
                "usage_before_mb": usage_before / (1024 * 1024),
                "usage_after_mb": usage_after / (1024 * 1024),
            }

        except Exception as e:
            self.logger.error(f"Disk optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _remove_temp_files(self, path: Path) -> int:
        """Remove temporary files from directory."""
        temp_extensions = {".tmp", ".temp", ".cache", ".log"}
        removed_count = 0

        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in temp_extensions:
                try:
                    file_path.unlink()
                    removed_count += 1
                except Exception as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")

        return removed_count

    def _get_directory_size(self, path: Path) -> int:
        """Get directory size in bytes."""
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    pass
        return total_size


class ParallelProcessor:
    """Parallel processing utilities."""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (psutil.cpu_count() or 1) + 4)
        self.logger = logging.getLogger("milkbottle.parallel_processor")

    async def process_parallel(
        self, items: List[Any], processor: Callable[[Any], Any], chunk_size: int = 100
    ) -> List[Any]:
        """Process items in parallel."""
        try:
            results = []

            # Process in chunks to avoid overwhelming the system
            for i in range(0, len(items), chunk_size):
                chunk = items[i : i + chunk_size]

                # Create tasks for the chunk
                tasks = [
                    asyncio.create_task(self._process_item(item, processor))
                    for item in chunk
                ]

                # Wait for all tasks in the chunk to complete
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Filter out exceptions
                valid_results = [
                    r for r in chunk_results if not isinstance(r, Exception)
                ]
                results.extend(valid_results)

                # Log any exceptions
                exceptions = [r for r in chunk_results if isinstance(r, Exception)]
                for exc in exceptions:
                    self.logger.error(f"Processing error: {exc}")

            return results

        except Exception as e:
            self.logger.error(f"Parallel processing failed: {e}")
            return []

    async def _process_item(self, item: Any, processor: Callable[[Any], Any]) -> Any:
        """Process a single item."""
        try:
            if asyncio.iscoroutinefunction(processor):
                return await processor(item)
            else:
                # Run CPU-bound functions in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, processor, item)
        except Exception as e:
            self.logger.error(f"Error processing item: {e}")
            raise


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent

        try:
            result = await func(*args, **kwargs)

            end_time = time.time()
            end_cpu = psutil.cpu_percent()
            end_memory = psutil.virtual_memory().percent

            # Record metrics
            metrics = PerformanceMetrics(
                cpu_usage=(start_cpu + end_cpu) / 2,
                memory_usage=(start_memory + end_memory) / 2,
                response_time=end_time - start_time,
            )

            # Log performance data
            logger.info(
                f"Function {func.__name__} completed in {metrics.response_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Function {func.__name__} failed: {e}")
            raise

    return wrapper


# Global instances
cache_manager = CacheManager()
performance_monitor_instance = PerformanceMonitor()
resource_optimizer = ResourceOptimizer()
parallel_processor = ParallelProcessor()
