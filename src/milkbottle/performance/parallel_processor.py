"""Parallel processing system for MilkBottle."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import wraps
from multiprocessing import cpu_count
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("milkbottle.parallel_processor")


@dataclass
class TaskResult:
    """Result of a parallel task."""

    task_id: str
    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class ProcessingStats:
    """Parallel processing statistics."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_time: float = 0.0
    avg_time_per_task: float = 0.0
    throughput: float = 0.0
    cpu_utilization: float = 0.0


class ParallelProcessor:
    """Advanced parallel processing system with thread and process pools."""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = False,
        chunk_size: int = 1,
    ):
        """Initialize parallel processor.

        Args:
            max_workers: Maximum number of workers (None for CPU count)
            use_processes: Whether to use process pool instead of thread pool
            chunk_size: Size of chunks for task distribution
        """
        self.max_workers = max_workers or cpu_count()
        self.use_processes = use_processes
        self.chunk_size = chunk_size

        # Create executor
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Statistics
        self.stats = ProcessingStats()
        self.task_history: List[TaskResult] = []

        logger.info(f"Initialized parallel processor with {self.max_workers} workers")

    def execute(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """Execute function in parallel on items.

        Args:
            func: Function to execute
            items: List of items to process
            **kwargs: Additional arguments for the function

        Returns:
            List of results
        """
        if not items:
            return []

        start_time = time.time()
        self.stats.total_tasks = len(items)

        try:
            # Submit tasks
            futures = []
            for i, item in enumerate(items):
                future = self.executor.submit(func, item, **kwargs)
                futures.append((i, future))

            # Collect results
            results = [None] * len(items)
            completed_count = 0

            for i, future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results[i] = result
                    completed_count += 1

                    # Record task result
                    task_result = TaskResult(
                        task_id=f"task_{i}",
                        result=result,
                        execution_time=time.time() - start_time,
                        success=True,
                    )
                    self.task_history.append(task_result)

                except Exception as e:
                    logger.error(f"Task {i} failed: {e}")
                    self.stats.failed_tasks += 1

                    task_result = TaskResult(
                        task_id=f"task_{i}",
                        result=None,
                        execution_time=time.time() - start_time,
                        success=False,
                        error=str(e),
                    )
                    self.task_history.append(task_result)

            # Update statistics
            total_time = time.time() - start_time
            self.stats.completed_tasks = completed_count
            self.stats.total_time = total_time
            self.stats.avg_time_per_task = total_time / len(items) if items else 0
            self.stats.throughput = len(items) / total_time if total_time > 0 else 0

            logger.info(
                f"Parallel execution completed: {completed_count}/{len(items)} tasks in {total_time:.3f}s"
            )
            return results

        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return []

    async def execute_async(
        self, func: Callable, items: List[Any], **kwargs
    ) -> List[Any]:
        """Execute function asynchronously in parallel.

        Args:
            func: Async function to execute
            items: List of items to process
            **kwargs: Additional arguments for the function

        Returns:
            List of results
        """
        if not items:
            return []

        start_time = time.time()
        self.stats.total_tasks = len(items)

        try:
            # Create tasks
            tasks = []
            for i, item in enumerate(items):
                task = asyncio.create_task(
                    self._execute_single_async(func, item, i, **kwargs)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            completed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Async task {i} failed: {result}")
                    self.stats.failed_tasks += 1
                    processed_results.append(None)

                    task_result = TaskResult(
                        task_id=f"async_task_{i}",
                        result=None,
                        execution_time=time.time() - start_time,
                        success=False,
                        error=str(result),
                    )
                else:
                    processed_results.append(result)
                    completed_count += 1

                    task_result = TaskResult(
                        task_id=f"async_task_{i}",
                        result=result,
                        execution_time=time.time() - start_time,
                        success=True,
                    )
                self.task_history.append(task_result)
            # Update statistics
            total_time = time.time() - start_time
            self.stats.completed_tasks = completed_count
            self.stats.total_time = total_time
            self.stats.avg_time_per_task = total_time / len(items) if items else 0
            self.stats.throughput = len(items) / total_time if total_time > 0 else 0

            logger.info(
                f"Async parallel execution completed: {completed_count}/{len(items)} tasks in {total_time:.3f}s"
            )
            return processed_results

        except Exception as e:
            logger.error(f"Async parallel execution failed: {e}")
            return []

    def execute_with_progress(
        self,
        func: Callable,
        items: List[Any],
        progress_callback: Optional[Callable] = None,
        **kwargs,
    ) -> List[Any]:
        """Execute function with progress tracking.

        Args:
            func: Function to execute
            items: List of items to process
            progress_callback: Optional callback for progress updates
            **kwargs: Additional arguments for the function

        Returns:
            List of results
        """
        if not items:
            return []

        start_time = time.time()
        self.stats.total_tasks = len(items)

        try:
            # Submit tasks
            futures = []
            for i, item in enumerate(items):
                future = self.executor.submit(func, item, **kwargs)
                futures.append((i, future))

            # Collect results with progress
            results = [None] * len(items)
            completed_count = 0

            for future in as_completed([f for _, f in futures]):
                try:
                    result = future.result(timeout=300)
                    # Find the index of this future
                    for i, f in futures:
                        if f == future:
                            results[i] = result
                            break
                    completed_count += 1

                    # Update progress
                    if progress_callback:
                        progress = (completed_count / len(items)) * 100
                        progress_callback(progress, completed_count, len(items))

                    # Record task result
                    task_result = TaskResult(
                        task_id=f"task_{i}",
                        result=result,
                        execution_time=time.time() - start_time,
                        success=True,
                    )
                    self.task_history.append(task_result)

                except Exception as e:
                    logger.error(f"Task {i} failed: {e}")
                    self.stats.failed_tasks += 1

                    task_result = TaskResult(
                        task_id=f"task_{i}",
                        result=None,
                        execution_time=time.time() - start_time,
                        success=False,
                        error=str(e),
                    )
                    self.task_history.append(task_result)

            # Update statistics
            total_time = time.time() - start_time
            self.stats.completed_tasks = completed_count
            self.stats.total_time = total_time
            self.stats.avg_time_per_task = total_time / len(items) if items else 0
            self.stats.throughput = len(items) / total_time if total_time > 0 else 0

            logger.info(
                f"Parallel execution with progress completed: {completed_count}/{len(items)} tasks in {total_time:.3f}s"
            )
            return results

        except Exception as e:
            logger.error(f"Parallel execution with progress failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        success_rate = 0
        if self.stats.total_tasks > 0:
            success_rate = self.stats.completed_tasks / self.stats.total_tasks

        return {
            "total_tasks": self.stats.total_tasks,
            "completed_tasks": self.stats.completed_tasks,
            "failed_tasks": self.stats.failed_tasks,
            "success_rate": success_rate,
            "total_time": self.stats.total_time,
            "avg_time_per_task": self.stats.avg_time_per_task,
            "throughput": self.stats.throughput,
            "max_workers": self.max_workers,
            "use_processes": self.use_processes,
            "chunk_size": self.chunk_size,
        }

    def optimize_workers(self, sample_size: int = 100) -> Dict[str, Any]:
        """Optimize number of workers based on performance.

        Args:
            sample_size: Number of sample tasks to test

        Returns:
            Optimization results
        """
        if sample_size <= 0:
            return {"error": "Invalid sample size"}

        # Test different worker counts
        worker_counts = [1, 2, 4, 8, 16, 32]
        if self.max_workers not in worker_counts:
            worker_counts.append(self.max_workers)

        results = {}

        for worker_count in worker_counts:
            if worker_count > cpu_count() * 2:
                continue  # Skip unrealistic worker counts

            # Create test executor
            if self.use_processes:
                test_executor = ProcessPoolExecutor(max_workers=worker_count)
            else:
                test_executor = ThreadPoolExecutor(max_workers=worker_count)

            # Test with sample tasks
            start_time = time.time()
            test_items = list(range(sample_size))

            try:
                futures = [
                    test_executor.submit(self._test_function, item)
                    for item in test_items
                ]
                for future in as_completed(futures):
                    future.result()

                total_time = time.time() - start_time
                throughput = sample_size / total_time if total_time > 0 else 0

                results[worker_count] = {
                    "time": total_time,
                    "throughput": throughput,
                    "efficiency": throughput / worker_count if worker_count > 0 else 0,
                }

            except Exception as e:
                logger.error(
                    f"Worker optimization test failed for {worker_count} workers: {e}"
                )
                results[worker_count] = {"error": str(e)}

            finally:
                test_executor.shutdown(wait=True)

        # Find optimal worker count
        optimal_workers = None
        best_efficiency = 0

        for worker_count, result in results.items():
            if "error" not in result and result["efficiency"] > best_efficiency:
                best_efficiency = result["efficiency"]
                optimal_workers = worker_count

        return {
            "test_results": results,
            "optimal_workers": optimal_workers,
            "best_efficiency": best_efficiency,
            "current_workers": self.max_workers,
            "recommendation": (
                f"Use {optimal_workers} workers"
                if optimal_workers
                else "Keep current configuration"
            ),
        }

    def shutdown(self) -> None:
        """Shutdown the parallel processor."""
        self.executor.shutdown(wait=True)
        logger.info("Parallel processor shutdown")

    async def _execute_single_async(
        self, func: Callable, item: Any, task_id: int, **kwargs
    ) -> Any:
        """Execute a single async task."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(item, **kwargs)
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, func, item, **kwargs)
        except Exception as e:
            logger.error(f"Async task {task_id} failed: {e}")
            raise

    def _test_function(self, item: Any) -> Any:
        """Test function for worker optimization."""
        # Simulate some work
        time.sleep(0.01)
        return item * 2


def parallel_processing(max_workers: Optional[int] = None, use_processes: bool = False):
    """Decorator to enable parallel processing.

    Args:
        max_workers: Maximum number of workers
        use_processes: Whether to use process pool

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        processor = ParallelProcessor(
            max_workers=max_workers, use_processes=use_processes
        )

        @wraps(func)
        def wrapper(items: List[Any], **kwargs):
            return processor.execute(func, items, **kwargs)

        return wrapper

    return decorator


def async_parallel_processing(max_workers: Optional[int] = None):
    """Decorator to enable async parallel processing.

    Args:
        max_workers: Maximum number of workers

    Returns:
        Decorated async function
    """

    def decorator(func: Callable) -> Callable:
        processor = ParallelProcessor(max_workers=max_workers, use_processes=False)

        @wraps(func)
        async def wrapper(items: List[Any], **kwargs):
            return await processor.execute_async(func, items, **kwargs)

        return wrapper

    return decorator
