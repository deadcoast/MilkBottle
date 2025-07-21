"""Tests for PDFmilker structured logging functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from milkbottle.modules.pdfmilker.structured_logger import (
    PDFmilkerStructuredLogger,
    create_structured_logger,
)


class TestPDFmilkerStructuredLogger:
    """Test structured logger functionality."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            assert logger.meta_dir == meta_dir
            assert logger.slug == slug
            assert logger.log_file == meta_dir / f"{slug}.log"
            assert meta_dir.exists()
            assert logger.correlation_id.startswith(slug)

    def test_info_logging(self):
        """Test info level logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.info("Test info message", extra_data="test_value")

            # Check that log file was created
            assert logger.log_file.exists()

            # Read and parse log entries
            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_info_logging_15(f, slug, logger)

    # TODO Rename this here and in `test_info_logging`
    def _extracted_from_test_info_logging_15(self, f, slug, logger):
        lines = f.readlines()
        assert len(lines) == 1

        log_entry = json.loads(lines[0])
        assert log_entry["level"] == "info"
        assert log_entry["message"] == "Test info message"
        assert log_entry["logger"] == "pdfmilker"
        assert log_entry["slug"] == slug
        assert log_entry["correlation_id"] == logger.correlation_id
        assert log_entry["data"]["extra_data"] == "test_value"

    def test_warning_logging(self):
        """Test warning level logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.warning("Test warning message")

            with logger.log_file.open("r", encoding="utf-8") as f:
                log_entry = json.loads(f.readline())
                assert log_entry["level"] == "warning"
                assert log_entry["message"] == "Test warning message"

    def test_error_logging(self):
        """Test error level logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.error("Test error message")

            with logger.log_file.open("r", encoding="utf-8") as f:
                log_entry = json.loads(f.readline())
                assert log_entry["level"] == "error"
                assert log_entry["message"] == "Test error message"

    def test_debug_logging(self):
        """Test debug level logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.debug("Test debug message")

            with logger.log_file.open("r", encoding="utf-8") as f:
                log_entry = json.loads(f.readline())
                assert log_entry["level"] == "debug"
                assert log_entry["message"] == "Test debug message"

    def test_pipeline_step_logging(self):
        """Test pipeline step logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.log_pipeline_step("extract", "started", pdf_path="/test/file.pdf")

            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_pipeline_step_logging_11(f)

    # TODO Rename this here and in `test_pipeline_step_logging`
    def _extracted_from_test_pipeline_step_logging_11(self, f):
        log_entry = json.loads(f.readline())
        assert log_entry["level"] == "info"
        assert "Pipeline step: extract - started" in log_entry["message"]
        assert log_entry["data"]["step"] == "extract"
        assert log_entry["data"]["status"] == "started"
        assert log_entry["data"]["pdf_path"] == "/test/file.pdf"

    def test_extraction_result_logging(self):
        """Test extraction result logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            result = {
                "extraction_method": "grobid",
                "content_length": 1500,
                "success": True,
                "processing_time": 2.5,
                "metadata": {"title": "Test Paper"},
                "quality_report": {"overall_quality": 0.85},
            }

            logger.log_extraction_result(result)

            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_extraction_result_logging_21(f)

    # TODO Rename this here and in `test_extraction_result_logging`
    def _extracted_from_test_extraction_result_logging_21(self, f):
        log_entry = json.loads(f.readline())
        assert log_entry["message"] == "Extraction completed"
        assert log_entry["data"]["extraction_method"] == "grobid"
        assert log_entry["data"]["content_length"] == 1500
        assert log_entry["data"]["success"] is True
        assert log_entry["data"]["processing_time"] == 2.5
        assert log_entry["data"]["metadata"]["title"] == "Test Paper"
        assert log_entry["data"]["quality_score"] == 0.85

    def test_error_with_context_logging(self):
        """Test error logging with context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            error = ValueError("Test error")
            context = {"pdf_path": "/test/file.pdf", "step": "extract"}

            logger.log_error_with_context(error, context)

            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_error_with_context_logging_15(f)

    # TODO Rename this here and in `test_error_with_context_logging`
    def _extracted_from_test_error_with_context_logging_15(self, f):
        log_entry = json.loads(f.readline())
        assert log_entry["level"] == "error"
        assert "Error occurred: Test error" in log_entry["message"]
        assert log_entry["data"]["error_type"] == "ValueError"
        assert log_entry["data"]["error_message"] == "Test error"
        assert log_entry["data"]["context"]["pdf_path"] == "/test/file.pdf"
        assert log_entry["data"]["context"]["step"] == "extract"

    def test_batch_summary_logging(self):
        """Test batch summary logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            logger.log_batch_summary(
                total_files=10, successful=8, failed=1, skipped=1, processing_time=15.5
            )

            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_batch_summary_logging_14(f)

    # TODO Rename this here and in `test_batch_summary_logging`
    def _extracted_from_test_batch_summary_logging_14(self, f):
        log_entry = json.loads(f.readline())
        assert log_entry["message"] == "Batch processing completed"
        assert log_entry["data"]["total_files"] == 10
        assert log_entry["data"]["successful_files"] == 8
        assert log_entry["data"]["failed_files"] == 1
        assert log_entry["data"]["skipped_files"] == 1
        assert log_entry["data"]["processing_time"] == 15.5
        assert log_entry["data"]["success_rate"] == 80.0

    def test_get_recent_logs(self):
        """Test getting recent logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            # Add multiple log entries
            logger.info("First message")
            logger.warning("Second message")
            logger.error("Third message")

            # Get recent logs
            recent_logs = logger.get_recent_logs(limit=2)

            assert len(recent_logs) == 2
            assert recent_logs[0]["message"] == "Second message"
            assert recent_logs[1]["message"] == "Third message"

    def test_get_logs_by_correlation_id(self):
        """Test getting logs by correlation ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            # Add log entries
            logger.info("Test message 1")
            logger.warning("Test message 2")

            # Get logs by correlation ID
            correlation_logs = logger.get_logs_by_correlation_id(logger.correlation_id)

            assert len(correlation_logs) == 2
            for log_entry in correlation_logs:
                assert log_entry["correlation_id"] == logger.correlation_id

    def test_log_file_creation_with_existing_meta_dir(self):
        """Test log file creation when meta directory already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            meta_dir.mkdir(parents=True, exist_ok=True)

            slug = "test-pdf"
            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            logger.info("Test message")

            assert logger.log_file.exists()
            assert logger.log_file.parent == meta_dir

    def test_log_file_append_mode(self):
        """Test that log file appends entries correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)

            # Add multiple entries
            logger.info("First entry")
            logger.warning("Second entry")
            logger.error("Third entry")

            # Check all entries are present
            with logger.log_file.open("r", encoding="utf-8") as f:
                self._extracted_from_test_log_file_append_mode_16(f)

    # TODO Rename this here and in `test_log_file_append_mode`
    def _extracted_from_test_log_file_append_mode_16(self, f):
        lines = f.readlines()
        assert len(lines) == 3

        entries = [json.loads(line) for line in lines]
        assert entries[0]["message"] == "First entry"
        assert entries[1]["message"] == "Second entry"
        assert entries[2]["message"] == "Third entry"

    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = PDFmilkerStructuredLogger(meta_dir, slug)
            logger.info("Test message")

            with logger.log_file.open("r", encoding="utf-8") as f:
                log_entry = json.loads(f.readline())
                timestamp = log_entry["timestamp"]

                # Verify ISO format
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique for different instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"

            logger1 = PDFmilkerStructuredLogger(meta_dir, "test1")
            logger2 = PDFmilkerStructuredLogger(meta_dir, "test2")

            assert logger1.correlation_id != logger2.correlation_id


class TestCreateStructuredLogger:
    """Test create_structured_logger factory function."""

    def test_create_structured_logger(self):
        """Test create_structured_logger function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = create_structured_logger(meta_dir, slug)

            assert isinstance(logger, PDFmilkerStructuredLogger)
            assert logger.meta_dir == meta_dir
            assert logger.slug == slug

    def test_create_structured_logger_with_logging(self):
        """Test create_structured_logger with actual logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = create_structured_logger(meta_dir, slug)
            logger.info("Test message")

            assert logger.log_file.exists()

            with logger.log_file.open("r", encoding="utf-8") as f:
                log_entry = json.loads(f.readline())
                assert log_entry["message"] == "Test message"
                assert log_entry["slug"] == slug


class TestStructuredLoggingIntegration:
    """Test structured logging integration with PDFmilker pipeline."""

    def test_pipeline_integration(self):
        """Test that structured logging integrates with pipeline."""
        # This test would require a mock PDF file and pipeline
        # For now, we'll test the basic integration points
        with tempfile.TemporaryDirectory() as temp_dir:
            meta_dir = Path(temp_dir) / "meta"
            slug = "test-pdf"

            logger = create_structured_logger(meta_dir, slug)

            # Simulate pipeline steps
            logger.log_pipeline_step("discover", "started", files_found=5)
            logger.log_pipeline_step("prepare", "started", output_dir=str(meta_dir))
            logger.log_pipeline_step("extract", "started", method="grobid")
            logger.log_pipeline_step(
                "extract", "completed", method="grobid", content_length=1500
            )
            logger.log_pipeline_step("transform", "started")
            logger.log_pipeline_step("transform", "completed", format="markdown")
            logger.log_pipeline_step("validate", "started")
            logger.log_pipeline_step("validate", "completed", validation_passed=True)
            logger.log_pipeline_step("relocate", "started")
            logger.log_pipeline_step("relocate", "completed", new_location="/output")
            logger.log_pipeline_step("report", "started")
            logger.log_pipeline_step("report", "completed", report_file="report.json")

            # Check all steps were logged
            with logger.log_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 12

                # Verify all pipeline steps are present
                steps = [json.loads(line)["data"]["step"] for line in lines]
                expected_steps = [
                    "discover",
                    "prepare",
                    "extract",
                    "extract",
                    "transform",
                    "transform",
                    "validate",
                    "validate",
                    "relocate",
                    "relocate",
                    "report",
                    "report",
                ]
                assert steps == expected_steps
