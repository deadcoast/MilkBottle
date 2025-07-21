"""Memory optimization system for MilkBottle."""

from __future__ import annotations

import contextlib
import gc
import logging
import sys
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Dict, List
from weakref import WeakSet

logger = logging.getLogger("milkbottle.memory_optimizer")


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    allocated_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    memory_percent: float = 0.0
    gc_objects: int = 0
    gc_collections: int = 0


@dataclass
class MemoryLeak:
    """Memory leak information."""

    file_path: str
    line_number: int
    size_mb: float
    count: int
    traceback: List[str]


class MemoryOptimizer:
    """Advanced memory optimization and leak detection system."""

    def __init__(
        self, enable_tracemalloc: bool = True, leak_threshold_mb: float = 10.0
    ):
        """Initialize memory optimizer.

        Args:
            enable_tracemalloc: Whether to enable tracemalloc for leak detection
            leak_threshold_mb: Memory leak threshold in MB
        """
        self.enable_tracemalloc = enable_tracemalloc
        self.leak_threshold_mb = leak_threshold_mb
        self.memory_history: List[MemoryStats] = []
        self.leak_snapshots: List[tracemalloc.Snapshot] = []
        self.optimization_history: List[Dict[str, Any]] = []

        # Initialize tracemalloc if enabled
        if self.enable_tracemalloc:
            tracemalloc.start()

        # Track large objects
        self.large_objects: WeakSet[Any] = WeakSet()
        self.large_object_threshold = 1024 * 1024  # 1MB

        logger.info("Memory optimizer initialized")

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics.

        Returns:
            Current memory statistics
        """
        try:
            # Get tracemalloc statistics
            if self.enable_tracemalloc:
                current, peak = tracemalloc.get_traced_memory()
                current_mb = current / (1024 * 1024)
                peak_mb = peak / (1024 * 1024)
            else:
                current_mb = 0.0
                peak_mb = 0.0

            # Get garbage collection statistics
            gc_stats = gc.get_stats()
            total_collections = sum(stat["collections"] for stat in gc_stats)

            # Get system memory info
            try:
                import psutil

                memory = psutil.virtual_memory()
                available_mb = memory.available / (1024 * 1024)
                memory_percent = memory.percent
            except ImportError:
                available_mb = 0.0
                memory_percent = 0.0

            stats = MemoryStats(
                current_memory_mb=current_mb,
                peak_memory_mb=peak_mb,
                allocated_memory_mb=current_mb,
                available_memory_mb=available_mb,
                memory_percent=memory_percent,
                gc_objects=len(gc.get_objects()),
                gc_collections=total_collections,
            )

            # Store in history
            self.memory_history.append(stats)

            return stats

        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats()

    def optimize(self) -> Dict[str, Any]:
        """Run comprehensive memory optimization.

        Returns:
            Optimization results
        """
        before_stats = self.get_memory_stats()

        # Garbage collection optimization
        gc_result = self._optimize_garbage_collection()
        optimizations = {"garbage_collection": gc_result}
        # Memory leak detection
        leak_result = self._detect_memory_leaks()
        optimizations["memory_leaks"] = leak_result

        # Large object cleanup
        large_object_result = self._cleanup_large_objects()
        optimizations["large_objects"] = large_object_result

        # Reference cycle detection
        cycle_result = self._detect_reference_cycles()
        optimizations["reference_cycles"] = cycle_result

        # Memory fragmentation analysis
        fragmentation_result = self._analyze_fragmentation()
        optimizations["fragmentation"] = fragmentation_result

        after_stats = self.get_memory_stats()

        # Calculate improvement
        memory_freed = before_stats.current_memory_mb - after_stats.current_memory_mb
        improvement_percent = (
            (memory_freed / before_stats.current_memory_mb * 100)
            if before_stats.current_memory_mb > 0
            else 0
        )

        optimizations["summary"] = {
            "memory_freed_mb": memory_freed,
            "improvement_percent": improvement_percent,
            "before_memory_mb": before_stats.current_memory_mb,
            "after_memory_mb": after_stats.current_memory_mb,
        }

        # Store optimization in history
        self.optimization_history.append(
            {"timestamp": time.time(), "results": optimizations}
        )

        logger.info(
            f"Memory optimization completed: {memory_freed:.2f}MB freed ({improvement_percent:.1f}% improvement)"
        )
        return optimizations

    def _optimize_garbage_collection(self) -> Dict[str, Any]:
        """Optimize garbage collection."""
        try:
            # Get GC statistics before
            before_stats = gc.get_stats()
            before_objects = len(gc.get_objects())

            # Force garbage collection
            collected = gc.collect()

            # Get GC statistics after
            after_stats = gc.get_stats()
            after_objects = len(gc.get_objects())

            # Calculate improvements
            objects_freed = before_objects - after_objects
            collections_performed = sum(
                stat["collections"] for stat in after_stats
            ) - sum(stat["collections"] for stat in before_stats)

            return {
                "success": True,
                "objects_freed": objects_freed,
                "collections_performed": collections_performed,
                "gc_collected": collected,
                "before_objects": before_objects,
                "after_objects": after_objects,
            }

        except Exception as e:
            logger.error(f"Garbage collection optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _detect_memory_leaks(self) -> Dict[str, Any]:
        """Detect potential memory leaks."""
        if not self.enable_tracemalloc:
            return {"success": False, "error": "Tracemalloc not enabled"}

        try:
            return self._extracted_from__detect_memory_leaks_8()
        except Exception as e:
            logger.error(f"Memory leak detection failed: {e}")
            return {"success": False, "error": str(e)}

    # TODO Rename this here and in `_detect_memory_leaks`
    def _extracted_from__detect_memory_leaks_8(self):
        # Take current snapshot
        current_snapshot = tracemalloc.take_snapshot()

        if not self.leak_snapshots:
            # First snapshot, just store it
            self.leak_snapshots.append(current_snapshot)
            return {
                "success": True,
                "message": "Initial snapshot taken",
                "leaks_detected": 0,
            }

        # Compare with previous snapshot
        previous_snapshot = self.leak_snapshots[-1]
        top_stats = current_snapshot.compare_to(previous_snapshot, "lineno")

        # Filter potential leaks
        leaks = []
        for stat in top_stats:
            if (
                stat.size_diff > self.leak_threshold_mb * 1024 * 1024
            ):  # Convert to bytes
                leak = MemoryLeak(
                    file_path=stat.traceback.format()[-1].split(":")[0],
                    line_number=int(stat.traceback.format()[-1].split(":")[1]),
                    size_mb=stat.size_diff / (1024 * 1024),
                    count=stat.count_diff,
                    traceback=stat.traceback.format(),
                )
                leaks.append(leak)

        # Store current snapshot
        self.leak_snapshots.append(current_snapshot)

        return {
            "success": True,
            "leaks_detected": len(leaks),
            "leaks": [
                {
                    "file": leak.file_path,
                    "line": leak.line_number,
                    "size_mb": leak.size_mb,
                    "count": leak.count,
                }
                for leak in leaks
            ],
        }

    def _cleanup_large_objects(self) -> Dict[str, Any]:
        """Clean up large objects."""
        try:
            # Find large objects
            large_objects = []
            for obj in gc.get_objects():
                try:
                    size = sys.getsizeof(obj)
                    if size > self.large_object_threshold:
                        large_objects.append(
                            {
                                "type": type(obj).__name__,
                                "size_mb": size / (1024 * 1024),
                                "id": id(obj),
                            }
                        )
                except (TypeError, ValueError):
                    continue

            # Sort by size
            large_objects.sort(key=lambda x: x["size_mb"], reverse=True)

            return {
                "success": True,
                "large_objects_found": len(large_objects),
                "total_size_mb": sum(obj["size_mb"] for obj in large_objects),
                "largest_objects": large_objects[:10],  # Top 10 largest
            }

        except Exception as e:
            logger.error(f"Large object cleanup failed: {e}")
            return {"success": False, "error": str(e)}

    def _detect_reference_cycles(self) -> Dict[str, Any]:
        """Detect reference cycles."""
        try:
            # Count objects before collection
            before_count = len(gc.get_objects())

            # Force collection to detect cycles
            collected = gc.collect()

            # Count objects after collection
            after_count = len(gc.get_objects())

            cycles_freed = before_count - after_count

            return {
                "success": True,
                "cycles_freed": cycles_freed,
                "objects_freed": collected,
                "before_count": before_count,
                "after_count": after_count,
            }

        except Exception as e:
            logger.error(f"Reference cycle detection failed: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_fragmentation(self) -> Dict[str, Any]:
        """Analyze memory fragmentation."""
        try:
            # Get memory statistics
            stats = self.get_memory_stats()

            # Calculate fragmentation metrics
            fragmentation_score = 0.0
            if stats.available_memory_mb > 0:
                # Simple fragmentation calculation
                fragmentation_score = (
                    (stats.peak_memory_mb - stats.current_memory_mb)
                    / stats.peak_memory_mb
                    * 100
                )

            return {
                "success": True,
                "fragmentation_score": fragmentation_score,
                "current_memory_mb": stats.current_memory_mb,
                "peak_memory_mb": stats.peak_memory_mb,
                "available_memory_mb": stats.available_memory_mb,
                "memory_percent": stats.memory_percent,
            }

        except Exception as e:
            logger.error(f"Memory fragmentation analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def track_large_object(self, obj: Any) -> None:
        """Track a large object for potential cleanup.

        Args:
            obj: Object to track
        """
        with contextlib.suppress(TypeError, ValueError):
            size = sys.getsizeof(obj)
            if size > self.large_object_threshold:
                self.large_objects.add(obj)
                logger.debug(
                    f"Tracking large object: {type(obj).__name__} ({size / (1024 * 1024):.2f}MB)"
                )

    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report.

        Returns:
            Memory report dictionary
        """
        current_stats = self.get_memory_stats()

        # Calculate trends
        if len(self.memory_history) >= 2:
            recent_stats = self.memory_history[-10:]  # Last 10 samples
            memory_trend = "stable"
            if len(recent_stats) >= 2:
                first_avg = sum(
                    s.current_memory_mb for s in recent_stats[: len(recent_stats) // 2]
                ) / (len(recent_stats) // 2)
                second_avg = sum(
                    s.current_memory_mb for s in recent_stats[len(recent_stats) // 2 :]
                ) / (len(recent_stats) - len(recent_stats) // 2)
                if second_avg > first_avg * 1.1:
                    memory_trend = "increasing"
                elif second_avg < first_avg * 0.9:
                    memory_trend = "decreasing"
        else:
            memory_trend = "unknown"

        # Get recent optimizations
        recent_optimizations = (
            self.optimization_history[-5:] if self.optimization_history else []
        )

        return {
            "current_stats": {
                "current_memory_mb": current_stats.current_memory_mb,
                "peak_memory_mb": current_stats.peak_memory_mb,
                "available_memory_mb": current_stats.available_memory_mb,
                "memory_percent": current_stats.memory_percent,
                "gc_objects": current_stats.gc_objects,
                "gc_collections": current_stats.gc_collections,
            },
            "trends": {
                "memory_trend": memory_trend,
                "history_count": len(self.memory_history),
            },
            "optimization_history": {
                "total_optimizations": len(self.optimization_history),
                "recent_optimizations": [
                    {
                        "timestamp": opt["timestamp"],
                        "memory_freed_mb": opt["results"]["summary"]["memory_freed_mb"],
                        "improvement_percent": opt["results"]["summary"][
                            "improvement_percent"
                        ],
                    }
                    for opt in recent_optimizations
                ],
            },
            "leak_detection": {
                "enabled": self.enable_tracemalloc,
                "snapshots_count": len(self.leak_snapshots),
                "leak_threshold_mb": self.leak_threshold_mb,
            },
        }

    def clear_history(self) -> None:
        """Clear memory history."""
        self.memory_history.clear()
        self.leak_snapshots.clear()
        self.optimization_history.clear()
        logger.info("Memory history cleared")

    def set_leak_threshold(self, threshold_mb: float) -> None:
        """Set memory leak detection threshold.

        Args:
            threshold_mb: Threshold in MB
        """
        self.leak_threshold_mb = threshold_mb
        logger.info(f"Memory leak threshold set to {threshold_mb}MB")

    def get_large_objects(self) -> List[Dict[str, Any]]:
        """Get list of currently tracked large objects.

        Returns:
            List of large object information
        """
        large_objects = []
        for obj in self.large_objects:
            try:
                size = sys.getsizeof(obj)
                large_objects.append(
                    {
                        "type": type(obj).__name__,
                        "size_mb": size / (1024 * 1024),
                        "id": id(obj),
                    }
                )
            except (TypeError, ValueError):
                continue

        return large_objects
