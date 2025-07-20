"""Structured logging for PDFmilker with JSONL format.

This module provides structured logging capabilities for PDFmilker operations,
writing logs to `/meta/<slug>.log` in JSONL format for machine parsing and analysis.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("pdfmilker.structured_logger")


class PDFmilkerStructuredLogger:
    """Structured logger for PDFmilker operations with JSONL output."""

    def __init__(self, meta_dir: Path, slug: str):
        """Initialize the structured logger.

        Args:
            meta_dir: Meta directory path
            slug: Slug identifier for the PDF
        """
        self.meta_dir = meta_dir
        self.slug = slug
        self.log_file = meta_dir / f"{slug}.log"

        # Ensure meta directory exists
        self.meta_dir.mkdir(parents=True, exist_ok=True)

        # Initialize correlation ID for this processing session
        self.correlation_id = f"{slug}_{int(time.time())}"

    def _write_log_entry(self, level: str, message: str, **kwargs: Any) -> None:
        """Write a structured log entry to the JSONL file.

        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            **kwargs: Additional structured data
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": "pdfmilker",
            "slug": self.slug,
            "correlation_id": self.correlation_id,
            "message": message,
        }

        # Add additional data if provided
        if kwargs:
            log_entry["data"] = kwargs

        # Write to JSONL file
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Fallback to standard logging if file write fails
            logger.error(f"Failed to write structured log entry: {e}")

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional structured data
        """
        self._write_log_entry("info", message, **kwargs)
        logger.info(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional structured data
        """
        self._write_log_entry("warning", message, **kwargs)
        logger.warning(message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.

        Args:
            message: Log message
            **kwargs: Additional structured data
        """
        self._write_log_entry("error", message, **kwargs)
        logger.error(message)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional structured data
        """
        self._write_log_entry("debug", message, **kwargs)
        logger.debug(message)

    def log_pipeline_step(self, step: str, status: str, **kwargs: Any) -> None:
        """Log a pipeline step with structured data.

        Args:
            step: Pipeline step name (discover, prepare, extract, transform, validate, relocate, report)
            status: Step status (started, completed, failed, skipped)
            **kwargs: Additional step-specific data
        """
        step_data = {"step": step, "status": status, **kwargs}
        self._write_log_entry("info", f"Pipeline step: {step} - {status}", **step_data)

    def log_extraction_result(self, result: Dict[str, Any]) -> None:
        """Log extraction result with structured data.

        Args:
            result: Extraction result dictionary
        """
        extraction_data = {
            "extraction_method": result.get("extraction_method", "unknown"),
            "content_length": result.get("content_length", 0),
            "success": result.get("success", False),
            "processing_time": result.get("processing_time", 0),
        }

        # Add additional result data
        if "metadata" in result:
            extraction_data["metadata"] = result["metadata"]

        if "quality_report" in result:
            extraction_data["quality_score"] = result["quality_report"].get(
                "overall_quality", 0
            )

        self._write_log_entry("info", "Extraction completed", **extraction_data)

    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context information.

        Args:
            error: Exception that occurred
            context: Context information about the error
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
        }
        self._write_log_entry("error", f"Error occurred: {error}", **error_data)

    def log_batch_summary(
        self,
        total_files: int,
        successful: int,
        failed: int,
        skipped: int,
        processing_time: float,
    ) -> None:
        """Log batch processing summary.

        Args:
            total_files: Total number of files processed
            successful: Number of successful extractions
            failed: Number of failed extractions
            skipped: Number of skipped files
            processing_time: Total processing time in seconds
        """
        summary_data = {
            "total_files": total_files,
            "successful_files": successful,
            "failed_files": failed,
            "skipped_files": skipped,
            "processing_time": processing_time,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
        }
        self._write_log_entry("info", "Batch processing completed", **summary_data)

    def get_recent_logs(self, limit: int = 100) -> list[Dict[str, Any]]:
        """Get recent log entries from the JSONL file.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent log entries
        """
        if not self.log_file.exists():
            return []

        try:
            with self.log_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                return [
                    json.loads(line.strip()) for line in recent_lines if line.strip()
                ]
        except Exception as e:
            logger.error(f"Failed to read recent logs: {e}")
            return []

    def get_logs_by_correlation_id(self, correlation_id: str) -> list[Dict[str, Any]]:
        """Get logs by correlation ID.

        Args:
            correlation_id: Correlation ID to filter by

        Returns:
            List of log entries with matching correlation ID
        """
        all_logs = self.get_recent_logs(
            limit=1000
        )  # Get more logs for correlation search
        return [log for log in all_logs if log.get("correlation_id") == correlation_id]


def create_structured_logger(meta_dir: Path, slug: str) -> PDFmilkerStructuredLogger:
    """Create a structured logger for PDFmilker operations.

    Args:
        meta_dir: Meta directory path
        slug: Slug identifier for the PDF

    Returns:
        PDFmilkerStructuredLogger instance
    """
    return PDFmilkerStructuredLogger(meta_dir, slug)
