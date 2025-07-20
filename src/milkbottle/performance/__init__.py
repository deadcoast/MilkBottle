"""MilkBottle Performance Optimization System.

This module provides comprehensive performance optimization features including:
- Intelligent caching system
- Performance monitoring and metrics
- Parallel processing capabilities
- Resource optimization
- Performance profiling
- Memory optimization
- I/O optimization
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache_manager import CacheManager
from .io_optimizer import IOOptimizer
from .memory_optimizer import MemoryOptimizer
from .parallel_processor import ParallelProcessor
from .performance_monitor import PerformanceMonitor
from .performance_profiler import PerformanceProfiler
from .resource_optimizer import ResourceOptimizer

logger = logging.getLogger("milkbottle.performance")


class PerformanceOptimizer:
    """Main performance optimization system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the performance optimization system."""
        self.config = config or {}
        self.cache_manager = CacheManager(
            max_size=self.config.get("cache_max_size", 1000),
            ttl=self.config.get("cache_ttl", 3600),
        )
        self.performance_monitor = PerformanceMonitor()
        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.get("max_workers", 4)
        )
        self.resource_optimizer = ResourceOptimizer()
        self.performance_profiler = PerformanceProfiler()
        self.memory_optimizer = MemoryOptimizer()
        self.io_optimizer = IOOptimizer()

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.performance_monitor.start_monitoring()
        logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.performance_monitor.stop_monitoring()
        logger.info("Performance monitoring stopped")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "cache_stats": self.cache_manager.get_stats(),
            "performance_metrics": self.performance_monitor.get_average_metrics(),
            "resource_usage": self.resource_optimizer.get_resource_usage(),
            "memory_stats": self.memory_optimizer.get_memory_stats(),
            "io_stats": self.io_optimizer.get_io_stats(),
            "parallel_stats": self.parallel_processor.get_stats(),
        }

    def optimize_system(self) -> Dict[str, Any]:
        """Run comprehensive system optimization."""
        # Memory optimization
        memory_optimization = self.memory_optimizer.optimize()
        optimizations = {"memory": memory_optimization}
        # I/O optimization
        io_optimization = self.io_optimizer.optimize()
        optimizations["io"] = io_optimization

        # Resource optimization
        resource_optimization = self.resource_optimizer.optimize()
        optimizations["resource"] = resource_optimization

        # Cache optimization
        cache_optimization = self.cache_manager.optimize()
        optimizations["cache"] = cache_optimization

        logger.info("System optimization completed")
        return optimizations

    def profile_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Profile a function execution."""
        return self.performance_profiler.profile_function(func, *args, **kwargs)

    def clear_cache(self) -> None:
        """Clear all caches."""
        self.cache_manager.clear()
        logger.info("All caches cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_manager.get_stats()

    def parallel_execute(self, func, items: List[Any], **kwargs) -> List[Any]:
        """Execute function in parallel on items."""
        return self.parallel_processor.execute(func, items, **kwargs)

    def optimize_memory(self) -> Dict[str, Any]:
        """Run memory optimization."""
        return self.memory_optimizer.optimize()

    def optimize_io(self) -> Dict[str, Any]:
        """Run I/O optimization."""
        return self.io_optimizer.optimize()


# Global performance optimizer instance
_optimizer: Optional[PerformanceOptimizer] = None


def get_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def start_monitoring() -> None:
    """Start performance monitoring."""
    get_optimizer().start_monitoring()


def stop_monitoring() -> None:
    """Stop performance monitoring."""
    get_optimizer().stop_monitoring()


def get_performance_report() -> Dict[str, Any]:
    """Get performance report."""
    return get_optimizer().get_performance_report()


def optimize_system() -> Dict[str, Any]:
    """Run system optimization."""
    return get_optimizer().optimize_system()


def profile_function(func, *args, **kwargs) -> Dict[str, Any]:
    """Profile a function."""
    return get_optimizer().profile_function(func, *args, **kwargs)


def clear_cache() -> None:
    """Clear all caches."""
    get_optimizer().clear_cache()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return get_optimizer().get_cache_stats()


def parallel_execute(func, items: List[Any], **kwargs) -> List[Any]:
    """Execute function in parallel."""
    return get_optimizer().parallel_execute(func, items, **kwargs)


def optimize_memory() -> Dict[str, Any]:
    """Run memory optimization."""
    return get_optimizer().optimize_memory()


def optimize_io() -> Dict[str, Any]:
    """Run I/O optimization."""
    return get_optimizer().optimize_io()


# Performance decorators
def performance_monitor(func):
    """Decorator to monitor function performance."""
    from .performance_monitor import performance_monitor as monitor_decorator

    return monitor_decorator(func)


def cache_result(ttl: int = 3600):
    """Decorator to cache function results."""
    from .cache_manager import cache_result as cache_decorator

    return cache_decorator(ttl)


def parallel_processing(max_workers: int = 4):
    """Decorator to enable parallel processing."""
    from .parallel_processor import parallel_processing as parallel_decorator

    return parallel_decorator(max_workers)


__all__ = [
    "PerformanceOptimizer",
    "get_optimizer",
    "start_monitoring",
    "stop_monitoring",
    "get_performance_report",
    "optimize_system",
    "profile_function",
    "clear_cache",
    "get_cache_stats",
    "parallel_execute",
    "optimize_memory",
    "optimize_io",
    "performance_monitor",
    "cache_result",
    "parallel_processing",
]
