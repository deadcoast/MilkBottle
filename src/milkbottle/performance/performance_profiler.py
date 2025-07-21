"""Performance profiling system for MilkBottle."""

from __future__ import annotations

import cProfile
import logging
import pstats
import time
import tracemalloc
from dataclasses import dataclass, field
from functools import wraps
from io import StringIO
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("milkbottle.performance_profiler")


@dataclass
class ProfileResult:
    """Result of performance profiling."""

    function_name: str
    total_time: float
    call_count: int
    avg_time: float
    min_time: float
    max_time: float
    memory_usage: Optional[float] = None
    memory_peak: Optional[float] = None
    cpu_percent: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfilingStats:
    """Profiling statistics."""

    total_functions: int = 0
    total_time: float = 0.0
    total_calls: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class PerformanceProfiler:
    """Advanced performance profiling system."""

    def __init__(
        self, enable_memory_profiling: bool = True, enable_cpu_profiling: bool = True
    ):
        """Initialize performance profiler.

        Args:
            enable_memory_profiling: Whether to enable memory profiling
            enable_cpu_profiling: Whether to enable CPU profiling
        """
        self.enable_memory_profiling = enable_memory_profiling
        self.enable_cpu_profiling = enable_cpu_profiling
        self.profile_history: List[ProfileResult] = []
        self.active_profiles: Dict[str, Any] = {}

        # Initialize tracemalloc if memory profiling is enabled
        if self.enable_memory_profiling:
            tracemalloc.start()

        logger.info("Performance profiler initialized")

    def profile_function(self, func: Callable, *args, **kwargs) -> ProfileResult:
        """Profile a function execution.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Profile result
        """
        function_name = func.__name__
        start_time = time.time()

        # Memory profiling
        memory_start = None
        memory_end = None
        if self.enable_memory_profiling:
            memory_start = tracemalloc.get_traced_memory()

        # CPU profiling
        profiler = None
        if self.enable_cpu_profiling:
            profiler = cProfile.Profile()
            profiler.enable()

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Stop CPU profiling
            if profiler:
                profiler.disable()

            # Get memory usage
            if self.enable_memory_profiling:
                memory_end = tracemalloc.get_traced_memory()

            # Calculate timing
            end_time = time.time()
            execution_time = end_time - start_time

            # Create profile result
            profile_result = ProfileResult(
                function_name=function_name,
                total_time=execution_time,
                call_count=1,
                avg_time=execution_time,
                min_time=execution_time,
                max_time=execution_time,
                memory_usage=(
                    memory_end[0] - memory_start[0]
                    if memory_start and memory_end
                    else None
                ),
                memory_peak=(
                    memory_end[1] - memory_start[1]
                    if memory_start and memory_end
                    else None
                ),
            )

            # Add CPU profiling details
            if profiler:
                self._extracted_from_profile_function_65(
                    profiler, profile_result, execution_time
                )
            # Store in history
            self.profile_history.append(profile_result)

            logger.info(f"Profiled {function_name}: {execution_time:.3f}s")
            return profile_result

        except Exception as e:
            logger.error(f"Profiling failed for {function_name}: {e}")
            return ProfileResult(
                function_name=function_name,
                total_time=0.0,
                call_count=0,
                avg_time=0.0,
                min_time=0.0,
                max_time=0.0,
                details={"error": str(e)},
            )

    # TODO Rename this here and in `profile_function`
    def _extracted_from_profile_function_65(
        self, profiler, profile_result, execution_time
    ):
        stats = pstats.Stats(profiler)
        self._extracted_from_stop_profile_5(stats, profile_result)
        # Calculate CPU percentage (approximate)
        profile_result.cpu_percent = (execution_time / time.time()) * 100

    def start_profile(self, name: str) -> None:
        """Start a named profile session.

        Args:
            name: Profile session name
        """
        if name in self.active_profiles:
            logger.warning(f"Profile session '{name}' already exists")
            return

        profile_data = {
            "start_time": time.time(),
            "memory_start": (
                tracemalloc.get_traced_memory()
                if self.enable_memory_profiling
                else None
            ),
            "profiler": cProfile.Profile() if self.enable_cpu_profiling else None,
        }

        if profile_data["profiler"]:
            profile_data["profiler"].enable()

        self.active_profiles[name] = profile_data
        logger.info(f"Started profile session: {name}")

    def stop_profile(self, name: str) -> Optional[ProfileResult]:
        """Stop a named profile session.

        Args:
            name: Profile session name

        Returns:
            Profile result or None if session not found
        """
        if name not in self.active_profiles:
            logger.warning(f"Profile session '{name}' not found")
            return None

        profile_data = self.active_profiles[name]
        end_time = time.time()

        # Stop CPU profiling
        if profile_data["profiler"]:
            profile_data["profiler"].disable()

        # Get memory usage
        memory_end = None
        if self.enable_memory_profiling and profile_data["memory_start"]:
            memory_end = tracemalloc.get_traced_memory()

        # Calculate timing
        execution_time = end_time - profile_data["start_time"]

        # Create profile result
        profile_result = ProfileResult(
            function_name=name,
            total_time=execution_time,
            call_count=1,
            avg_time=execution_time,
            min_time=execution_time,
            max_time=execution_time,
            memory_usage=(
                memory_end[0] - profile_data["memory_start"][0] if memory_end else None
            ),
            memory_peak=(
                memory_end[1] - profile_data["memory_start"][1] if memory_end else None
            ),
        )

        # Add CPU profiling details
        if profile_data["profiler"]:
            stats = pstats.Stats(profile_data["profiler"])
            self._extracted_from_stop_profile_5(stats, profile_result)
        # Store in history and remove from active
        self.profile_history.append(profile_result)
        del self.active_profiles[name]

        logger.info(f"Stopped profile session {name}: {execution_time:.3f}s")
        return profile_result

    # TODO Rename this here and in `_extracted_from_profile_function_65` and `stop_profile`
    def _extracted_from_stop_profile_5(self, stats, profile_result):
        stats.sort_stats("cumulative")
        output = StringIO()
        stats.print_stats(10)
        profile_result.details["cpu_profile"] = "CPU profiling completed"

    def get_profile_history(self) -> List[ProfileResult]:
        """Get profiling history.

        Returns:
            List of profile results
        """
        return self.profile_history.copy()

    def get_function_profile(self, function_name: str) -> Optional[ProfileResult]:
        """Get profile for a specific function.

        Args:
            function_name: Name of the function

        Returns:
            Profile result or None if not found
        """
        return next(
            (
                profile
                for profile in reversed(self.profile_history)
                if profile.function_name == function_name
            ),
            None,
        )

    def get_slowest_functions(self, limit: int = 10) -> List[ProfileResult]:
        """Get the slowest functions by average time.

        Args:
            limit: Maximum number of functions to return

        Returns:
            List of slowest functions
        """
        # Group by function name and calculate averages
        function_stats: Dict[str, List[ProfileResult]] = {}

        for profile in self.profile_history:
            if profile.function_name not in function_stats:
                function_stats[profile.function_name] = []
            function_stats[profile.function_name].append(profile)

        # Calculate average times
        avg_profiles = []
        for func_name, profiles in function_stats.items():
            total_time = sum(p.total_time for p in profiles)
            call_count = sum(p.call_count for p in profiles)
            avg_time = total_time / call_count if call_count > 0 else 0

            avg_profile = ProfileResult(
                function_name=func_name,
                total_time=total_time,
                call_count=call_count,
                avg_time=avg_time,
                min_time=min(p.min_time for p in profiles),
                max_time=max(p.max_time for p in profiles),
            )
            avg_profiles.append(avg_profile)

        # Sort by average time and return top N
        avg_profiles.sort(key=lambda x: x.avg_time, reverse=True)
        return avg_profiles[:limit]

    def get_memory_intensive_functions(self, limit: int = 10) -> List[ProfileResult]:
        """Get the most memory-intensive functions.

        Args:
            limit: Maximum number of functions to return

        Returns:
            List of memory-intensive functions
        """
        memory_profiles = [
            p for p in self.profile_history if p.memory_usage is not None
        ]
        memory_profiles.sort(key=lambda x: x.memory_usage or 0, reverse=True)
        return memory_profiles[:limit]

    def clear_history(self) -> None:
        """Clear profiling history."""
        self.profile_history.clear()
        logger.info("Profiling history cleared")

    def get_profiling_report(self) -> Dict[str, Any]:
        """Get comprehensive profiling report.

        Returns:
            Profiling report dictionary
        """
        if not self.profile_history:
            return {"message": "No profiling data available"}

        # Calculate overall statistics
        total_functions = len({p.function_name for p in self.profile_history})
        total_time = sum(p.total_time for p in self.profile_history)
        total_calls = sum(p.call_count for p in self.profile_history)

        # Memory statistics
        memory_profiles = [
            p for p in self.profile_history if p.memory_usage is not None
        ]
        total_memory = sum(p.memory_usage or 0 for p in memory_profiles)
        avg_memory = total_memory / len(memory_profiles) if memory_profiles else 0

        # Get top functions
        slowest_functions = self.get_slowest_functions(5)
        memory_intensive = self.get_memory_intensive_functions(5)

        return {
            "overall_stats": {
                "total_functions": total_functions,
                "total_time": total_time,
                "total_calls": total_calls,
                "avg_time_per_call": total_time / total_calls if total_calls > 0 else 0,
                "total_memory_usage": total_memory,
                "avg_memory_per_call": avg_memory,
            },
            "slowest_functions": [
                {
                    "name": p.function_name,
                    "avg_time": p.avg_time,
                    "total_time": p.total_time,
                    "call_count": p.call_count,
                }
                for p in slowest_functions
            ],
            "memory_intensive_functions": [
                {
                    "name": p.function_name,
                    "memory_usage": p.memory_usage,
                    "memory_peak": p.memory_peak,
                    "call_count": p.call_count,
                }
                for p in memory_intensive
            ],
            "active_profiles": list(self.active_profiles.keys()),
            "profile_count": len(self.profile_history),
        }

    def optimize_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Profile and provide optimization suggestions for a function.

        Args:
            func: Function to optimize
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Optimization suggestions
        """
        profile_result = self.profile_function(func, *args, **kwargs)

        suggestions = []

        # Time-based suggestions
        if profile_result.avg_time > 1.0:
            suggestions.extend(
                (
                    "Consider caching results for expensive operations",
                    "Look for opportunities to parallelize work",
                    "Profile individual operations within the function",
                )
            )
        if profile_result.avg_time > 0.1:
            suggestions.extend(
                (
                    "Consider using more efficient algorithms",
                    "Check for unnecessary computations",
                )
            )
        # Memory-based suggestions
        if (
            profile_result.memory_usage
            and profile_result.memory_usage > 100 * 1024 * 1024
        ):  # 100MB
            suggestions.extend(
                (
                    "Consider streaming large data instead of loading all at once",
                    "Look for memory leaks or inefficient data structures",
                    "Consider using generators for large datasets",
                )
            )
        # CPU-based suggestions
        if profile_result.cpu_percent and profile_result.cpu_percent > 80:
            suggestions.extend(
                (
                    "Consider using multiprocessing for CPU-intensive tasks",
                    "Look for opportunities to use vectorized operations",
                )
            )
        return {
            "profile_result": {
                "function_name": profile_result.function_name,
                "execution_time": profile_result.total_time,
                "memory_usage": profile_result.memory_usage,
                "cpu_percent": profile_result.cpu_percent,
            },
            "suggestions": suggestions,
            "performance_rating": self._calculate_performance_rating(profile_result),
        }

    def _calculate_performance_rating(self, profile: ProfileResult) -> str:
        """Calculate a performance rating for a profile result.

        Args:
            profile: Profile result

        Returns:
            Performance rating (excellent, good, fair, poor)
        """
        score = 0

        # Time score
        if profile.avg_time < 0.01:
            score += 3
        elif profile.avg_time < 0.1:
            score += 2
        elif profile.avg_time < 1.0:
            score += 1

        # Memory score
        if profile.memory_usage:
            if profile.memory_usage < 1024 * 1024:  # 1MB
                score += 3
            elif profile.memory_usage < 10 * 1024 * 1024:  # 10MB
                score += 2
            elif profile.memory_usage < 100 * 1024 * 1024:  # 100MB
                score += 1

        # CPU score
        if profile.cpu_percent:
            if profile.cpu_percent < 20:
                score += 3
            elif profile.cpu_percent < 50:
                score += 2
            elif profile.cpu_percent < 80:
                score += 1

        if score >= 8:
            return "excellent"
        elif score >= 6:
            return "good"
        elif score >= 4:
            return "fair"
        else:
            return "poor"


def profile_function(func: Callable) -> Callable:
    """Decorator to profile function performance.

    Args:
        func: Function to profile

    Returns:
        Decorated function
    """
    profiler = PerformanceProfiler()

    @wraps(func)
    def wrapper(*args, **kwargs):
        return profiler.profile_function(func, *args, **kwargs)

    return wrapper


def profile_memory(func: Callable) -> Callable:
    """Decorator to profile function memory usage.

    Args:
        func: Function to profile

    Returns:
        Decorated function
    """
    profiler = PerformanceProfiler(
        enable_memory_profiling=True, enable_cpu_profiling=False
    )

    @wraps(func)
    def wrapper(*args, **kwargs):
        return profiler.profile_function(func, *args, **kwargs)

    return wrapper
