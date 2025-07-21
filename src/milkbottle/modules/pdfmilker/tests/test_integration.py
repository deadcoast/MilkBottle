"""Integration tests for PDFmilker enhanced features."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from milkbottle.modules.pdfmilker.batch_processor import BatchProcessor, ProgressTracker
from milkbottle.modules.pdfmilker.format_exporter import FormatExporter
from milkbottle.modules.pdfmilker.pipeline import PDFmilkerPipeline
from milkbottle.modules.pdfmilker.quality_assessor import QualityAssessor


class TestPDFmilkerIntegration:
    """Integration tests for PDFmilker enhanced features."""

    def test_full_pipeline_integration(self):
        """Test complete pipeline integration with all enhanced features."""
        # Create a mock PDF file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = Path(f.name)

        # Create output directory
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Initialize pipeline
            pipeline = PDFmilkerPipeline()

            # Mock the scientific paper processing to return test data
            test_content = {
                "title": "Test Scientific Paper",
                "abstract": "This is a test abstract for a scientific paper.",
                "body_text": "This is the main content of the scientific paper with sufficient length to meet quality assessment requirements.",
                "math_formulas": [
                    {"content": "\\frac{a}{b}", "confidence": 0.9},
                    {"content": "\\sum_{i=1}^{n} x_i", "confidence": 0.8},
                ],
                "tables": [{"rows": [["Header1", "Header2"], ["Data1", "Data2"]]}],
                "references": [
                    {"raw": "Author, A. (2020). Test Paper. Journal of Testing."},
                    {"raw": "Author, B. (2021). Another Test. Proceedings of Testing."},
                ],
            }

            with patch.object(pipeline, "process_scientific_paper") as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "output_path": output_dir / "temp.md",
                    "method": "grobid",
                    "content_length": len(str(test_content)),
                }

                # Process PDF
                result = pipeline.process_pdf(pdf_path, output_dir, "markdown")

                assert result["success"] is True
                assert "output_file" in result
                assert "extracted_content" in result
                assert "export_result" in result

                # Verify export result
                export_result = result["export_result"]
                assert export_result["success"] is True
                assert export_result["format"] == "markdown"

        finally:
            # Cleanup
            if pdf_path.exists():
                pdf_path.unlink()
            if output_dir.exists():
                import shutil

                shutil.rmtree(output_dir)

    def test_quality_assessment_integration(self):
        """Test quality assessment integration with pipeline."""
        # Create test content
        test_content = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "body_text": "x" * 200,  # Sufficient length
            "math_formulas": [{"content": "\\frac{a}{b}", "confidence": 0.9}],
            "tables": [{"rows": [["A", "B"], ["1", "2"]]}],
            "references": [{"raw": "Author, A. (2020). Test."}],
        }

        # Test quality assessment
        assessor = QualityAssessor()
        pdf_path = Path("test.pdf")

        report = assessor.assess_extraction_quality(pdf_path, test_content)

        assert report.pdf_path == pdf_path
        assert report.extracted_content == test_content
        assert report.metrics.overall_confidence > 0
        assert report.metrics.get_quality_level() in [
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Very Poor",
        ]

    def test_format_export_integration(self):
        """Test format export integration with different formats."""
        exporter = FormatExporter()
        test_content = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "body_text": "Test content",
            "math_formulas": [{"content": "x^2 + y^2 = z^2"}],
            "tables": [{"rows": [["A", "B"], ["1", "2"]]}],
            "references": [{"raw": "Test Reference"}],
        }

        # Test multiple formats
        formats_to_test = ["markdown", "html", "json"]

        for format_type in formats_to_test:
            with tempfile.NamedTemporaryFile(
                suffix=f".{format_type}", delete=False
            ) as f:
                output_path = Path(f.name)

            try:
                result = exporter.export_to_format(
                    test_content, format_type, output_path
                )

                assert result["success"] is True
                assert result["format"] == format_type
                assert result["output_path"] == output_path
                assert result["content_length"] > 0

                # Verify file was created and has content
                assert output_path.exists()
                file_content = output_path.read_text(encoding="utf-8")
                assert file_content != ""

                # Format-specific checks
                if format_type == "markdown":
                    assert "# Test Document" in file_content
                elif format_type == "html":
                    assert "<!DOCTYPE html>" in file_content
                elif format_type == "json":
                    json_data = json.loads(file_content)
                    assert "metadata" in json_data
                    assert "content" in json_data

            finally:
                output_path.unlink(missing_ok=True)

    def test_batch_processing_integration(self):
        """Test batch processing integration."""
        # Create test PDF files
        test_files = []
        for _ in range(3):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                test_files.append(Path(f.name))

        output_dir = Path(tempfile.mkdtemp())

        try:
            # Initialize batch processor
            processor = BatchProcessor(max_workers=2, enable_parallel=False)

            # Mock the pipeline processing
            with patch.object(processor, "pipeline") as mock_pipeline:
                mock_pipeline.process_pdf.return_value = {
                    "success": True,
                    "output_file": output_dir / "test.md",
                    "extracted_content": {"title": "Test"},
                    "export_result": {"success": True},
                }

                # Process batch
                result = processor.process_batch(test_files, output_dir, dry_run=False)

                assert result.total_files == 3
                assert result.success_count == 3
                assert result.failure_count == 0
                assert result.success_rate == 100.0
                assert result.processing_time > 0

        finally:
            # Cleanup
            for file_path in test_files:
                if file_path.exists():
                    file_path.unlink()
            if output_dir.exists():
                import shutil

                shutil.rmtree(output_dir)

    def test_error_recovery_integration(self):
        """Test error recovery integration."""
        # Create test PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = Path(f.name)

        output_dir = Path(tempfile.mkdtemp())

        try:
            pipeline = PDFmilkerPipeline()

            # Mock primary processing to fail
            with patch.object(pipeline, "process_scientific_paper") as mock_primary:
                mock_primary.side_effect = Exception("Primary processing failed")

                # Mock fallback processing to succeed
                with patch.object(pipeline, "_fallback_extraction") as mock_fallback:
                    mock_fallback.return_value = {
                        "success": True,
                        "output_path": output_dir / "temp.md",
                        "content_length": 100,
                    }

                    # Test fallback processing
                    result = pipeline.process_pdf_fallback(
                        pdf_path, output_dir, "markdown"
                    )

                    assert result["success"] is True
                    assert "output_file" in result
                    assert "extracted_content" in result

        finally:
            # Cleanup
            if pdf_path.exists():
                pdf_path.unlink()
            if output_dir.exists():
                import shutil

                shutil.rmtree(output_dir)

    def test_memory_management_integration(self):
        """Test memory management integration."""
        processor = BatchProcessor(memory_limit_mb=1024)

        # Test memory usage tracking
        memory_usage = processor.get_memory_usage()

        assert isinstance(memory_usage, dict)
        # Should have either error status or memory info
        assert "error" in memory_usage or "current_mb" in memory_usage

        # Test cancellation
        assert processor._cancelled is False
        processor.cancel()
        assert processor._cancelled is True

    def test_progress_tracking_integration(self):
        """Test progress tracking integration."""
        console = Console()
        tracker = ProgressTracker(5, console)

        # Test progress tracking lifecycle
        assert tracker.total_files == 5
        assert tracker.current_file == 0

        # Mock progress object
        mock_progress = Mock()
        tracker.progress = mock_progress

        # Test start
        tracker.start()
        mock_progress.start.assert_called_once()
        assert tracker.main_task is not None

        # Test next file
        tracker.next_file("test.pdf")
        assert tracker.current_file == 1

        # Test update progress
        tracker.update_file_progress(0.5, "Processing")
        mock_progress.update.assert_called()

        # Test stop
        tracker.stop()
        mock_progress.stop.assert_called_once()

    def test_quality_metrics_integration(self):
        """Test quality metrics integration."""
        # Test quality metrics calculation
        from milkbottle.modules.pdfmilker.quality_assessor import QualityMetrics

        metrics = QualityMetrics()
        metrics.text_completeness = 0.9
        metrics.math_accuracy = 0.8
        metrics.table_structure = 0.7
        metrics.image_quality = 0.6
        metrics.citation_completeness = 0.5

        confidence = metrics.calculate_overall_confidence()

        assert confidence > 0
        assert confidence <= 1.0
        assert metrics.overall_confidence == confidence

        # Test quality level
        quality_level = metrics.get_quality_level()
        assert quality_level in ["Excellent", "Good", "Fair", "Poor", "Very Poor"]

        # Test issues and warnings
        metrics.add_issue("Test issue")
        metrics.add_warning("Test warning")

        assert len(metrics.issues) == 1
        assert len(metrics.warnings) == 1
        assert "Test issue" in metrics.issues
        assert "Test warning" in metrics.warnings

    def test_table_conversion_integration(self):
        """Test table conversion across different formats."""
        exporter = FormatExporter()
        test_table = {
            "rows": [
                ["Name", "Age", "City"],
                ["John", "25", "New York"],
                ["Jane", "30", "Los Angeles"],
            ]
        }

        # Test markdown conversion
        md_table = exporter._convert_table_to_markdown(test_table)
        assert "| Name | Age | City |" in md_table
        assert "| John | 25 | New York |" in md_table

        # Test HTML conversion
        html_table = exporter._convert_table_to_html(test_table)
        assert "<table>" in html_table
        assert "<th>Name</th>" in html_table
        assert "<td>John</td>" in html_table

        # Test LaTeX conversion
        latex_table = exporter._convert_table_to_latex(test_table)
        assert "\\begin{table}" in latex_table
        assert "\\end{table}" in latex_table
        assert "Name & Age & City" in latex_table

    def test_math_processing_integration(self):
        """Test mathematical content processing integration."""
        assessor = QualityAssessor()

        # Test valid LaTeX formulas
        valid_formulas = [
            "\\frac{a}{b}",
            "\\sum_{i=1}^{n} x_i",
            "\\int_{0}^{1} f(x) dx",
            "\\sqrt{x^2 + y^2}",
        ]

        for formula in valid_formulas:
            assert assessor._is_valid_latex_formula(formula)

        # Test invalid formulas
        invalid_formulas = [
            "plain text",
            "x^2 + y^2",  # No LaTeX commands
            "simple equation",
        ]

        for formula in invalid_formulas:
            assert not assessor._is_valid_latex_formula(formula)

    def test_citation_processing_integration(self):
        """Test citation processing integration."""
        assessor = QualityAssessor()

        # Test valid citations
        valid_citations = [
            "Smith, J. (2020). Test paper. Journal of Testing.",
            "Doe, A. et al. (2019). Another test. Proceedings of Testing.",
            "Author, B. (2021). Title. Journal of Science.",
        ]

        for citation in valid_citations:
            assert assessor._is_valid_citation(citation)

        # Test invalid citations
        invalid_citations = ["random text", "just some words", "no author or year"]

        for citation in invalid_citations:
            assert not assessor._is_valid_citation(citation)


if __name__ == "__main__":
    pytest.main([__file__])
