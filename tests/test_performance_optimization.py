"""Tests for MilkBottle Performance Optimization System."""

import tempfile
import time
from pathlib import Path

import pytest

from milkbottle.performance import (
    PerformanceOptimizer,
    cache_result,
    clear_cache,
    get_cache_stats,
    get_performance_report,
    optimize_io,
    optimize_memory,
    optimize_system,
    parallel_execute,
    parallel_processing,
    performance_monitor,
    start_monitoring,
    stop_monitoring,
)
from milkbottle.performance.cache_manager import CacheManager
from milkbottle.performance.io_optimizer import IOOptimizer
from milkbottle.performance.memory_optimizer import MemoryOptimizer
from milkbottle.performance.parallel_processor import ParallelProcessor
from milkbottle.performance.performance_monitor import PerformanceMonitor
from milkbottle.performance.performance_profiler import PerformanceProfiler
from milkbottle.performance.resource_optimizer import ResourceOptimizer


class TestCacheManager:
    """Test cache manager functionality."""

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(max_size=100, ttl=1800)
        assert cache.max_size == 100
        assert cache.ttl == 1800
        assert len(cache.cache) == 0

    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        cache = CacheManager()

        # Set value
        cache.set("test_key", "test_value")
        assert len(cache.cache) == 1

        # Get value
        result = cache.get("test_key")
        assert result == "test_value"

        # Get non-existent key
        result = cache.get("non_existent", "default")
        assert result == "default"

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = CacheManager(ttl=1)  # Short TTL

        # Set value
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.5)  # Wait longer than TTL
        assert cache.get("test_key") is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = CacheManager(max_size=2)

        self._extracted_from_test_cache_clear_6(cache)
        # Add third item, should evict first
        cache.set("key3", "value3")
        assert len(cache.cache) == 2
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = CacheManager()
        self._extracted_from_test_cache_clear_6(cache)
        cache.clear()
        assert len(cache.cache) == 0

    # TODO Rename this here and in `test_cache_lru_eviction` and `test_cache_clear`
    def _extracted_from_test_cache_clear_6(self, cache):
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.cache) == 2

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheManager()

        # Add some data
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["entries"] == 1
        assert 0 < stats["hit_rate"] < 1

    def test_cache_optimize(self):
        """Test cache optimization."""
        cache = CacheManager()
        cache.set("key1", "value1")

        result = cache.optimize()
        assert "expired_cleaned" in result
        assert "avg_access_count" in result


class TestPerformanceMonitor:
    """Test performance monitor functionality."""

    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()
        assert not monitor.monitoring
        assert len(monitor.metrics_history) == 0

    def test_get_current_metrics(self):
        """Test getting current metrics."""
        monitor = PerformanceMonitor()
        metrics = monitor.get_current_metrics()

        assert hasattr(metrics, "timestamp")
        assert hasattr(metrics, "cpu_usage")
        assert hasattr(metrics, "memory_usage")

    def test_get_average_metrics(self):
        """Test getting average metrics."""
        monitor = PerformanceMonitor()

        # Add some metrics
        for _ in range(5):
            monitor.metrics_history.append(monitor.get_current_metrics())

        avg_metrics = monitor.get_average_metrics()
        assert avg_metrics is not None

    def test_function_profiling(self):
        """Test function profiling."""
        monitor = PerformanceMonitor()

        # Record a function call
        monitor._record_function_call("test_function", 0.1)

        profile = monitor.get_function_profile("test_function")
        assert profile is not None
        assert profile.function_name == "test_function"
        assert profile.call_count == 1

    def test_performance_report(self):
        """Test performance report generation."""
        monitor = PerformanceMonitor()

        # Add some data
        monitor._record_function_call("test_function", 0.1)

        report = monitor.get_performance_report()
        assert "current_metrics" in report
        assert "function_profiles" in report


class TestParallelProcessor:
    """Test parallel processor functionality."""

    def test_parallel_processor_initialization(self):
        """Test parallel processor initialization."""
        processor = ParallelProcessor(max_workers=4)
        assert processor.max_workers == 4
        assert not processor.use_processes

    def test_parallel_execution(self):
        """Test parallel execution."""
        processor = ParallelProcessor(max_workers=2)

        def test_function(x):
            return x * 2

        items = [1, 2, 3, 4, 5]
        results = processor.execute(test_function, items)

        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]

    def test_parallel_execution_with_errors(self):
        """Test parallel execution with errors."""
        processor = ParallelProcessor(max_workers=2)

        def test_function(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2

        items = [1, 2, 3, 4, 5]
        results = processor.execute(test_function, items)

        # Should handle errors gracefully
        assert len(results) == 5
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] is None  # Error case
        assert results[3] == 8
        assert results[4] == 10

    def test_get_stats(self):
        """Test getting processing statistics."""
        processor = ParallelProcessor()

        def test_function(x):
            return x * 2

        processor.execute(test_function, [1, 2, 3])

        stats = processor.get_stats()
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 3
        assert stats["success_rate"] == 1.0

    def test_worker_optimization(self):
        """Test worker optimization."""
        processor = ParallelProcessor()

        result = processor.optimize_workers(sample_size=10)
        assert "test_results" in result
        assert "optimal_workers" in result


class TestResourceOptimizer:
    """Test resource optimizer functionality."""

    def test_resource_optimizer_initialization(self):
        """Test resource optimizer initialization."""
        optimizer = ResourceOptimizer()
        assert optimizer.optimization_threshold == 0.1
        assert len(optimizer.optimization_history) == 0

    def test_get_resource_usage(self):
        """Test getting resource usage."""
        optimizer = ResourceOptimizer()
        usage = optimizer.get_resource_usage()

        assert hasattr(usage, "cpu_percent")
        assert hasattr(usage, "memory_percent")
        assert hasattr(usage, "disk_usage_percent")

    def test_optimize(self):
        """Test resource optimization."""
        optimizer = ResourceOptimizer()
        result = optimizer.optimize()

        assert "memory" in result
        assert "cpu" in result
        assert "disk" in result
        assert "network" in result

    def test_set_resource_limit(self):
        """Test setting resource limits."""
        optimizer = ResourceOptimizer()
        optimizer.set_resource_limit("max_memory_percent", 90.0)
        assert optimizer.limits["max_memory_percent"] == 90.0

    def test_get_optimization_report(self):
        """Test getting optimization report."""
        optimizer = ResourceOptimizer()
        optimizer.optimize()  # Run optimization first

        report = optimizer.get_optimization_report()
        assert "current_usage" in report
        assert "limits" in report
        assert "optimization_history" in report


class TestPerformanceProfiler:
    """Test performance profiler functionality."""

    def test_performance_profiler_initialization(self):
        """Test performance profiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.enable_memory_profiling
        assert profiler.enable_cpu_profiling

    def test_profile_function(self):
        """Test function profiling."""
        profiler = PerformanceProfiler()

        def test_function():
            time.sleep(0.01)
            return "test"

        result = profiler.profile_function(test_function)

        assert result.function_name == "test_function"
        assert result.total_time > 0
        assert result.call_count == 1

    def test_start_stop_profile(self):
        """Test start and stop profiling."""
        profiler = PerformanceProfiler()

        profiler.start_profile("test_session")
        assert "test_session" in profiler.active_profiles

        result = profiler.stop_profile("test_session")
        assert result is not None
        assert result.function_name == "test_session"

    def test_get_slowest_functions(self):
        """Test getting slowest functions."""
        profiler = PerformanceProfiler()

        # Add some profiles by calling profile_function
        def fast_function():
            time.sleep(0.01)
            return "fast"

        def slow_function():
            time.sleep(0.1)
            return "slow"

        profiler.profile_function(fast_function)
        profiler.profile_function(slow_function)

        slowest = profiler.get_slowest_functions(limit=1)
        assert len(slowest) == 1
        assert slowest[0].function_name == "slow_function"

    def test_optimize_function(self):
        """Test function optimization."""
        profiler = PerformanceProfiler()

        def test_function():
            time.sleep(0.1)
            return "test"

        result = profiler.optimize_function(test_function)

        assert "profile_result" in result
        assert "suggestions" in result
        assert "performance_rating" in result


class TestMemoryOptimizer:
    """Test memory optimizer functionality."""

    def test_memory_optimizer_initialization(self):
        """Test memory optimizer initialization."""
        optimizer = MemoryOptimizer()
        assert optimizer.enable_tracemalloc
        assert optimizer.leak_threshold_mb == 10.0

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        optimizer = MemoryOptimizer()
        stats = optimizer.get_memory_stats()

        assert hasattr(stats, "current_memory_mb")
        assert hasattr(stats, "peak_memory_mb")
        assert hasattr(stats, "gc_objects")

    def test_optimize(self):
        """Test memory optimization."""
        optimizer = MemoryOptimizer()
        result = optimizer.optimize()

        assert "garbage_collection" in result
        assert "memory_leaks" in result
        assert "large_objects" in result
        assert "summary" in result

    def test_track_large_object(self):
        """Test tracking large objects."""
        optimizer = MemoryOptimizer()

        # Create a large object
        large_list = [0] * 1000000  # ~8MB
        optimizer.track_large_object(large_list)

        large_objects = optimizer.get_large_objects()
        assert len(large_objects) > 0

    def test_get_memory_report(self):
        """Test getting memory report."""
        optimizer = MemoryOptimizer()
        optimizer.optimize()  # Run optimization first

        report = optimizer.get_memory_report()
        assert "current_stats" in report
        assert "trends" in report
        assert "optimization_history" in report


class TestIOOptimizer:
    """Test I/O optimizer functionality."""

    def test_io_optimizer_initialization(self):
        """Test I/O optimizer initialization."""
        optimizer = IOOptimizer()
        assert optimizer.buffer_size == 8192
        assert optimizer.max_concurrent_operations == 10

    def test_get_io_stats(self):
        """Test getting I/O statistics."""
        optimizer = IOOptimizer()
        stats = optimizer.get_io_stats()

        assert hasattr(stats, "read_bytes")
        assert hasattr(stats, "write_bytes")
        assert hasattr(stats, "read_operations")

    def test_record_file_operations(self):
        """Test recording file operations."""
        optimizer = self._extracted_from_test_optimize_3()
        stats = optimizer.get_io_stats()
        assert stats.read_bytes == 1024
        assert stats.write_bytes == 512
        assert stats.read_operations == 1
        assert stats.write_operations == 1

    def test_optimize(self):
        """Test I/O optimization."""
        optimizer = self._extracted_from_test_optimize_3()
        result = optimizer.optimize()

        assert "file_io" in result
        assert "network_io" in result
        assert "buffers" in result
        assert "caching" in result

    # TODO Rename this here and in `test_record_file_operations` and `test_optimize`
    def _extracted_from_test_optimize_3(self):
        result = IOOptimizer()
        result.record_file_read("test.txt", 1024, 0.1)
        result.record_file_write("test.txt", 512, 0.05)
        return result

    def test_get_io_report(self):
        """Test getting I/O report."""
        optimizer = IOOptimizer()

        # Record some operations first
        optimizer.record_file_read("test.txt", 1024, 0.1)

        report = optimizer.get_io_report()
        assert "io_stats" in report
        assert "file_io" in report
        assert "settings" in report

    @pytest.mark.asyncio
    async def test_async_file_operations(self):
        """Test async file operations."""
        optimizer = IOOptimizer()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = f.name
            f.write(b"test content")

        try:
            # Test async read
            content = await optimizer.async_read_file(test_file)
            assert content == b"test content"

            # Test async write
            await optimizer.async_write_file(test_file, b"new content")

            # Verify write
            content = await optimizer.async_read_file(test_file)
            assert content == b"new content"

        finally:
            Path(test_file).unlink()


class TestPerformanceOptimizer:
    """Test main performance optimizer."""

    def test_performance_optimizer_initialization(self):
        """Test performance optimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert optimizer.cache_manager is not None
        assert optimizer.performance_monitor is not None
        assert optimizer.parallel_processor is not None

    def test_get_performance_report(self):
        """Test getting performance report."""
        optimizer = PerformanceOptimizer()
        report = optimizer.get_performance_report()

        assert "cache_stats" in report
        assert "performance_metrics" in report
        assert "resource_usage" in report

    def test_optimize_system(self):
        """Test system optimization."""
        optimizer = PerformanceOptimizer()
        result = optimizer.optimize_system()

        assert "memory" in result
        assert "io" in result
        assert "resource" in result
        assert "cache" in result

    def test_parallel_execute(self):
        """Test parallel execution."""
        optimizer = PerformanceOptimizer()

        def test_function(x):
            return x * 2

        results = optimizer.parallel_execute(test_function, [1, 2, 3])
        assert results == [2, 4, 6]


class TestPerformanceDecorators:
    """Test performance decorators."""

    def test_performance_monitor_decorator(self):
        """Test performance monitor decorator."""

        @performance_monitor
        def test_function():
            time.sleep(0.01)
            return "test"

        result = test_function()
        assert result == "test"

    def test_cache_result_decorator(self):
        """Test cache result decorator."""
        call_count = 0

        @cache_result(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should be cached)
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_parallel_processing_decorator(self):
        """Test parallel processing decorator."""

        @parallel_processing(max_workers=2)
        def test_function(items):
            return [x * 2 for x in items]

        results = test_function([1, 2, 3, 4, 5])
        assert results == [2, 4, 6, 8, 10]


class TestGlobalFunctions:
    """Test global performance functions."""

    def test_start_stop_monitoring(self):
        """Test start and stop monitoring."""
        start_monitoring()
        time.sleep(0.1)  # Let monitoring run briefly
        stop_monitoring()

    def test_get_performance_report(self):
        """Test getting performance report."""
        report = get_performance_report()
        assert isinstance(report, dict)

    def test_optimize_system(self):
        """Test system optimization."""
        result = optimize_system()
        assert isinstance(result, dict)

    def test_clear_cache(self):
        """Test clearing cache."""
        clear_cache()  # Should not raise any errors

    def test_get_cache_stats(self):
        """Test getting cache stats."""
        stats = get_cache_stats()
        assert isinstance(stats, dict)

    def test_parallel_execute(self):
        """Test parallel execution."""

        def test_function(x):
            return x * 2

        results = parallel_execute(test_function, [1, 2, 3])
        assert results == [2, 4, 6]

    def test_optimize_memory(self):
        """Test memory optimization."""
        result = optimize_memory()
        assert isinstance(result, dict)

    def test_optimize_io(self):
        """Test I/O optimization."""
        result = optimize_io()
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__])
