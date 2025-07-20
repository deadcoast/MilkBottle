"""PDFmilker enhanced error recovery with retry mechanisms and partial result recovery."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .errors import PDFMilkerError

logger = logging.getLogger("pdfmilker.error_recovery")

T = TypeVar("T")


class RecoveryStrategy:
    """Base class for error recovery strategies."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_count = 0
        self.last_error: Optional[Exception] = None

    def should_retry(self, error: Exception) -> bool:
        """Determine if operation should be retried."""
        return self.retry_count < self.max_retries

    def get_retry_delay(self) -> float:
        """Calculate delay before next retry."""
        return self.backoff_factor**self.retry_count

    def on_retry(self, error: Exception) -> None:
        """Handle retry attempt."""
        self.retry_count += 1
        self.last_error = error
        delay = self.get_retry_delay()
        logger.warning(
            f"Retry {self.retry_count}/{self.max_retries} after {delay:.2f}s due to: {error}"
        )
        time.sleep(delay)

    def reset(self) -> None:
        """Reset retry state."""
        self.retry_count = 0
        self.last_error = None


class NetworkRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for network-related errors."""

    def __init__(self, max_retries: int = 5, backoff_factor: float = 2.0):
        super().__init__(max_retries, backoff_factor)
        self.network_errors = [
            "ConnectionError",
            "TimeoutError",
            "socket.timeout",
            "requests.exceptions.RequestException",
            "urllib.error.URLError",
        ]

    def should_retry(self, error: Exception) -> bool:
        """Retry network errors with exponential backoff."""
        if self.retry_count >= self.max_retries:
            return False

        error_type = type(error).__name__
        return any(net_error in error_type for net_error in self.network_errors)


class FileRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for file-related errors."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        super().__init__(max_retries, backoff_factor)
        self.file_errors = [
            "FileNotFoundError",
            "PermissionError",
            "OSError",
            "IOError",
            "IsADirectoryError",
            "NotADirectoryError",
        ]

    def should_retry(self, error: Exception) -> bool:
        """Retry file errors with shorter backoff."""
        if self.retry_count >= self.max_retries:
            return False

        error_type = type(error).__name__
        return any(file_error in error_type for file_error in self.file_errors)


class PartialResult:
    """Represents a partial result from a failed operation."""

    def __init__(
        self, data: Any, success_ratio: float, error: Optional[Exception] = None
    ):
        self.data = data
        self.success_ratio = success_ratio  # 0.0 to 1.0
        self.error = error
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def is_usable(self, min_ratio: float = 0.5) -> bool:
        """Check if partial result is usable."""
        return self.success_ratio >= min_ratio

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data": self.data,
            "success_ratio": self.success_ratio,
            "error": str(self.error) if self.error else None,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "is_usable": self.is_usable(),
        }


class ErrorRecoveryManager:
    """Manages error recovery and partial result handling."""

    def __init__(self):
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {
            "network": NetworkRecoveryStrategy(),
            "file": FileRecoveryStrategy(),
            "default": RecoveryStrategy(),
        }
        self.partial_results: List[PartialResult] = []
        self.error_history: List[Dict[str, Any]] = []

    def execute_with_recovery(
        self,
        operation: Callable[[], T],
        strategy_name: str = "default",
        fallback_operation: Optional[Callable[[], T]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Union[T, PartialResult]:
        """
        Execute operation with error recovery.

        Args:
            operation: Main operation to execute
            strategy_name: Name of recovery strategy to use
            fallback_operation: Fallback operation if main fails
            context: Additional context for error handling

        Returns:
            Result of operation or partial result
        """
        strategy = self.recovery_strategies.get(
            strategy_name, self.recovery_strategies["default"]
        )
        strategy.reset()

        while True:
            try:
                result = operation()
                self._log_success(strategy_name, context)
                return result

            except Exception as error:
                self._log_error(error, strategy_name, context)

                if not strategy.should_retry(error):
                    # Try fallback operation
                    if fallback_operation:
                        try:
                            fallback_result = fallback_operation()
                            self._log_success(f"{strategy_name}_fallback", context)
                            return fallback_result
                        except Exception as fallback_error:
                            self._log_error(
                                fallback_error, f"{strategy_name}_fallback", context
                            )

                    if partial_result := self._create_partial_result(error, context):
                        self.partial_results.append(partial_result)
                        return partial_result

                    # Re-raise the error
                    raise error

                strategy.on_retry(error)

    def execute_batch_with_recovery(
        self,
        operations: List[Callable[[], T]],
        strategy_name: str = "default",
        continue_on_error: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Union[T, PartialResult]]:
        """
        Execute batch of operations with error recovery.

        Args:
            operations: List of operations to execute
            strategy_name: Name of recovery strategy to use
            continue_on_error: Whether to continue processing on errors
            context: Additional context for error handling

        Returns:
            List of results or partial results
        """
        results = []
        failed_operations = []

        for i, operation in enumerate(operations):
            try:
                result = self.execute_with_recovery(
                    operation, strategy_name, context=context
                )
                results.append(result)

            except Exception as error:
                logger.error(f"Operation {i} failed: {error}")
                failed_operations.append((i, error))

                if not continue_on_error:
                    raise error

        # Log batch summary
        self._log_batch_summary(len(operations), len(failed_operations), context)

        return results

    def _create_partial_result(
        self, error: Exception, context: Optional[Dict[str, Any]]
    ) -> Optional[PartialResult]:
        """Create partial result from error context."""
        # This is a simplified implementation
        # In practice, you would extract partial data from the error context
        if context and "partial_data" in context:
            partial_data = context["partial_data"]
            success_ratio = context.get("success_ratio", 0.0)
            return PartialResult(partial_data, success_ratio, error)

        return None

    def _log_error(
        self, error: Exception, strategy_name: str, context: Optional[Dict[str, Any]]
    ) -> None:
        """Log error information."""
        error_info = {
            "timestamp": time.time(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "strategy": strategy_name,
            "context": context or {},
        }
        self.error_history.append(error_info)

        logger.error(f"Error in {strategy_name}: {error}")

    def _log_success(
        self, strategy_name: str, context: Optional[Dict[str, Any]]
    ) -> None:
        """Log successful operation."""
        logger.info(f"Operation successful using {strategy_name}")

    def _log_batch_summary(
        self, total: int, failed: int, context: Optional[Dict[str, Any]]
    ) -> None:
        """Log batch processing summary."""
        success_rate = ((total - failed) / total) * 100 if total > 0 else 0
        logger.info(
            f"Batch processing complete: {total - failed}/{total} successful ({success_rate:.1f}%)"
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about errors encountered."""
        if not self.error_history:
            return {"total_errors": 0}

        stats = {
            "total_errors": len(self.error_history),
            "error_types": {},
            "strategies_used": {},
            "recent_errors": self.error_history[-10:],  # Last 10 errors
            "partial_results": len(self.partial_results),
        }

        # Error type distribution
        for error_info in self.error_history:
            error_type = error_info["error_type"]
            stats["error_types"][error_type] = (
                stats["error_types"].get(error_type, 0) + 1
            )

        # Strategy distribution
        for error_info in self.error_history:
            strategy = error_info["strategy"]
            stats["strategies_used"][strategy] = (
                stats["strategies_used"].get(strategy, 0) + 1
            )

        return stats

    def clear_history(self) -> None:
        """Clear error history and partial results."""
        self.error_history.clear()
        self.partial_results.clear()

    def get_recovery_suggestions(self, error: Exception) -> List[str]:
        """Get recovery suggestions for a specific error."""
        suggestions = []
        error_type = type(error).__name__

        if "Connection" in error_type or "Timeout" in error_type:
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Verify the service URL is correct",
                    "Try again in a few minutes",
                    "Check if the service is temporarily unavailable",
                ]
            )

        elif "FileNotFound" in error_type or "Permission" in error_type:
            suggestions.extend(
                [
                    "Verify the file path is correct",
                    "Check file permissions",
                    "Ensure the file exists",
                    "Try running with elevated permissions if needed",
                ]
            )

        elif "Memory" in error_type or "MemoryError" in error_type:
            suggestions.extend(
                [
                    "Close other applications to free memory",
                    "Try processing smaller files",
                    "Reduce batch size",
                    "Check available system memory",
                ]
            )

        else:
            suggestions.extend(
                (
                    "Try the operation again",
                    "Check the input parameters",
                    "Verify the configuration settings",
                )
            )
        return suggestions


class PDFProcessingRecovery:
    """Specialized recovery for PDF processing operations."""

    def __init__(self, recovery_manager: ErrorRecoveryManager):
        self.recovery_manager = recovery_manager

    def process_pdf_with_recovery(
        self,
        pdf_path: Path,
        processing_function: Callable[[Path], T],
        fallback_function: Optional[Callable[[Path], T]] = None,
    ) -> Union[T, PartialResult]:
        """
        Process PDF with specialized recovery strategies.

        Args:
            pdf_path: Path to PDF file
            processing_function: Main processing function
            fallback_function: Fallback processing function

        Returns:
            Processing result or partial result
        """

        def operation():
            return processing_function(pdf_path)

        def fallback():
            if fallback_function:
                return fallback_function(pdf_path)
            raise PDFMilkerError("No fallback function available")

        context = {
            "pdf_path": str(pdf_path),
            "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
        }

        return self.recovery_manager.execute_with_recovery(
            operation, "file", fallback, context
        )

    def batch_process_pdfs_with_recovery(
        self,
        pdf_paths: List[Path],
        processing_function: Callable[[Path], T],
        fallback_function: Optional[Callable[[Path], T]] = None,
        continue_on_error: bool = True,
    ) -> List[Union[T, PartialResult]]:
        """
        Process multiple PDFs with recovery strategies.

        Args:
            pdf_paths: List of PDF paths
            processing_function: Main processing function
            fallback_function: Fallback processing function
            continue_on_error: Whether to continue on individual failures

        Returns:
            List of processing results or partial results
        """
        operations = []

        for pdf_path in pdf_paths:

            def create_operation(pdf_path=pdf_path):
                return lambda: processing_function(pdf_path)

            operations.append(create_operation())

        context = {
            "batch_size": len(pdf_paths),
            "pdf_paths": [str(p) for p in pdf_paths],
        }

        return self.recovery_manager.execute_batch_with_recovery(
            operations, "file", continue_on_error, context
        )


# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()
pdf_processing_recovery = PDFProcessingRecovery(error_recovery_manager)
