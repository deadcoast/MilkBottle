"""Batch processing system for PDFmilker with parallel processing and progress tracking.

This module provides a robust batch processing system that can handle large numbers
of PDF files with parallel processing, progress tracking, memory management, and
error recovery capabilities.
"""

from __future__ import annotations

import gc
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class BatchResult:
    """Result of a batch processing operation."""

    total_files: int
    successful_files: int
    failed_files: int
    skipped_files: int
    processing_time: float
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    warnings: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessingConfig:
    """Configuration for batch processing."""

    max_workers: int = 4
    memory_limit_mb: int = 2048  # 2GB default
    timeout_seconds: int = 300  # 5 minutes per file
    retry_attempts: int = 2
    skip_existing: bool = True
    output_format: str = "markdown"
    quality_assessment: bool = True
    extract_images: bool = False
    extract_tables: bool = True
    extract_citations: bool = True


class BatchProcessor:
    """Advanced batch processor for PDF files with parallel processing and progress tracking."""

    def __init__(self, config: ProcessingConfig):
        """Initialize the batch processor.

        Args:
            config: Processing configuration
        """
        self.config = config
        self.progress_callback: Optional[Callable] = None
        self.cancellation_event = threading.Event()

    def process_batch(
        self,
        pdf_files: List[Path],
        output_dir: Path,
        progress_callback: Optional[Callable] = None,
    ) -> BatchResult:
        """Process a batch of PDF files with parallel processing and progress tracking.

        Args:
            pdf_files: List of PDF file paths to process
            output_dir: Output directory for processed files
            progress_callback: Optional callback for progress updates

        Returns:
            BatchResult with processing statistics and results
        """
        start_time = time.time()
        self.progress_callback = progress_callback
        self.cancellation_event.clear()

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filter files based on configuration
        files_to_process = self._filter_files(pdf_files, output_dir)

        if not files_to_process:
            return BatchResult(
                total_files=len(pdf_files),
                successful_files=0,
                failed_files=0,
                skipped_files=len(pdf_files),
                processing_time=time.time() - start_time,
            )

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            # Create main task
            main_task = progress.add_task(
                f"Processing {len(files_to_process)} PDF files...",
                total=len(files_to_process),
            )

            # Process files in parallel
            results = self._process_files_parallel(
                files_to_process, output_dir, progress, main_task
            )

            # Update progress
            progress.update(main_task, completed=len(files_to_process))

        processing_time = time.time() - start_time

        # Compile results
        batch_result = BatchResult(
            total_files=len(pdf_files),
            successful_files=len(
                [r for r in results.values() if r.get("success", False)]
            ),
            failed_files=len(
                [r for r in results.values() if not r.get("success", False)]
            ),
            skipped_files=len(pdf_files) - len(files_to_process),
            processing_time=processing_time,
            results={str(k): v for k, v in results.items()},
        )

        # Extract errors and warnings
        for file_path, result in results.items():
            if not result.get("success", False):
                batch_result.errors[str(file_path)] = result.get(
                    "error", "Unknown error"
                )
            if result.get("warning"):
                batch_result.warnings[str(file_path)] = result["warning"]

        return batch_result

    def _filter_files(self, pdf_files: List[Path], output_dir: Path) -> List[Path]:
        """Filter files based on configuration and existing outputs.

        Args:
            pdf_files: List of PDF files to filter
            output_dir: Output directory to check for existing files

        Returns:
            Filtered list of files to process
        """
        files_to_process = []

        for pdf_file in pdf_files:
            if not pdf_file.exists():
                logger.warning(f"PDF file not found: {pdf_file}")
                continue

            if not pdf_file.suffix.lower() == ".pdf":
                logger.warning(f"Not a PDF file: {pdf_file}")
                continue

            # Check if output already exists
            if self.config.skip_existing:
                output_file = self._get_output_path(pdf_file, output_dir)
                if output_file.exists():
                    logger.info(f"Skipping {pdf_file.name} - output already exists")
                    continue

            files_to_process.append(pdf_file)

        return files_to_process

    def _process_files_parallel(
        self, files: List[Path], output_dir: Path, progress: Progress, main_task: Any
    ) -> Dict[Path, Dict[str, Any]]:
        """Process files in parallel using ThreadPoolExecutor.

        Args:
            files: List of files to process
            output_dir: Output directory
            progress: Rich progress object
            main_task: Main progress task

        Returns:
            Dictionary of results for each file
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self._process_single_file, file_path, output_dir
                ): file_path
                for file_path in files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                if self.cancellation_event.is_set():
                    break

                file_path = future_to_file[future]

                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    results[file_path] = result

                    # Update progress
                    progress.advance(main_task)

                    # Update description with current file
                    progress.update(
                        main_task, description=f"Processing {file_path.name}..."
                    )

                    # Call progress callback if provided
                    if self.progress_callback:
                        self.progress_callback(file_path, result)

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results[file_path] = {
                        "success": False,
                        "error": str(e),
                        "processing_time": 0,
                    }
                    progress.advance(main_task)

        return results

    def _process_single_file(self, pdf_file: Path, output_dir: Path) -> Dict[str, Any]:
        """Process a single PDF file.

        Args:
            pdf_file: Path to PDF file
            output_dir: Output directory

        Returns:
            Processing result dictionary
        """
        start_time = time.time()

        try:
            # Import here to avoid circular imports
            from .pipeline import PDFmilkerPipeline

            # Create pipeline and process
            pipeline = PDFmilkerPipeline()
            result = pipeline.process_pdf(
                pdf_file, output_dir, self.config.output_format
            )

            processing_time = time.time() - start_time

            return {
                "success": True,
                "output_file": result.get("output_file"),
                "processing_time": processing_time,
                "file_size": pdf_file.stat().st_size,
                "extracted_content": result.get("extracted_content", {}),
                "quality_score": result.get("quality_score", 0.0),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to process {pdf_file}: {e}")

            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "file_size": pdf_file.stat().st_size if pdf_file.exists() else 0,
            }
        finally:
            # Force garbage collection to manage memory
            gc.collect()

    def _get_output_path(self, pdf_file: Path, output_dir: Path) -> Path:
        """Get the output path for a PDF file.

        Args:
            pdf_file: Input PDF file path
            output_dir: Output directory

        Returns:
            Output file path
        """
        stem = pdf_file.stem
        if self.config.output_format == "markdown":
            return output_dir / f"{stem}.md"
        elif self.config.output_format == "html":
            return output_dir / f"{stem}.html"
        elif self.config.output_format == "json":
            return output_dir / f"{stem}.json"
        else:
            return output_dir / f"{stem}.{self.config.output_format}"

    def cancel(self):
        """Cancel the current batch processing operation."""
        self.cancellation_event.set()
        logger.info("Batch processing cancellation requested")


class ProgressTracker:
    """Progress tracking system for batch operations."""

    def __init__(self, total_files: int):
        """Initialize the progress tracker.

        Args:
            total_files: Total number of files to process
        """
        self.total_files = total_files
        self.current_file = 0
        self.current_operation = ""
        self.start_time = time.time()
        self.file_times: List[float] = []

    def update_progress(
        self, file_progress: float, operation: str, file_name: str = ""
    ):
        """Update progress information.

        Args:
            file_progress: Progress within current file (0.0 to 1.0)
            operation: Current operation being performed
            file_name: Name of current file being processed
        """
        self.current_operation = operation

        if file_progress >= 1.0:
            self.current_file += 1
            self.file_times.append(time.time() - self.start_time)

        # Calculate ETA
        if self.file_times:
            avg_time_per_file = sum(self.file_times) / len(self.file_times)
            remaining_files = self.total_files - self.current_file
            eta_seconds = remaining_files * avg_time_per_file
        else:
            eta_seconds = 0

        # Log progress
        logger.info(
            f"Progress: {self.current_file}/{self.total_files} files "
            f"({self.current_file/self.total_files*100:.1f}%) - "
            f"Current: {file_name} - {operation} - ETA: {eta_seconds:.0f}s"
        )

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information.

        Returns:
            Dictionary with progress information
        """
        elapsed_time = time.time() - self.start_time

        return {
            "current_file": self.current_file,
            "total_files": self.total_files,
            "progress_percentage": (self.current_file / self.total_files) * 100,
            "current_operation": self.current_operation,
            "elapsed_time": elapsed_time,
            "eta_seconds": self._calculate_eta(),
            "files_per_second": (
                self.current_file / elapsed_time if elapsed_time > 0 else 0
            ),
        }

    def _calculate_eta(self) -> float:
        """Calculate estimated time to completion.

        Returns:
            Estimated time in seconds
        """
        if not self.file_times:
            return 0

        avg_time_per_file = sum(self.file_times) / len(self.file_times)
        remaining_files = self.total_files - self.current_file
        return remaining_files * avg_time_per_file
