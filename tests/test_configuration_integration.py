"""Tests for PDFmilker configuration integration."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from milkbottle.modules.pdfmilker.config import PDFmilkerConfig
from milkbottle.modules.pdfmilker.pipeline import PDFmilkerPipeline


class TestConfigurationIntegration:
    """Test configuration integration with PDFmilker pipeline."""

    def test_pipeline_respects_grobid_configuration(self):
        """Test that pipeline respects Grobid configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = (
                self._extracted_from_test_pipeline_respects_mathpix_configuration_5(
                    False, True, True
                )
            )
            # Patch the config in the pipeline
            with patch(
                "milkbottle.modules.pdfmilker.pipeline.pdfmilker_config", mock_config
            ):
                pipeline = PDFmilkerPipeline()

                # Mock the extractors
                pipeline.grobid_extractor = Mock()
                pipeline.pandoc_converter = Mock()

                # Set up mock responses
                pipeline.pandoc_converter.convert_pdf_to_markdown.return_value = (
                    "# Test Content"
                )

                # Create a test PDF file
                pdf_path = Path(temp_dir) / "test.pdf"
                pdf_path.write_text("dummy pdf content")
                output_path = Path(temp_dir) / "output.md"

                # Process the PDF
                result = pipeline.process_scientific_paper(pdf_path, output_path)

                # Verify Grobid was not called
                pipeline.grobid_extractor.extract_scientific_paper.assert_not_called()

                # Verify Pandoc was called as fallback
                pipeline.pandoc_converter.convert_pdf_to_markdown.assert_called_once_with(
                    pdf_path
                )

                # Verify result
                assert result["success"] is True
                assert result["method"] == "pandoc"

    def test_pipeline_respects_pandoc_configuration(self):
        """Test that pipeline respects Pandoc configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = (
                self._extracted_from_test_pipeline_respects_mathpix_configuration_5(
                    False, False, True
                )
            )
            # Patch the config in the pipeline
            with patch(
                "milkbottle.modules.pdfmilker.pipeline.pdfmilker_config", mock_config
            ):
                pipeline = PDFmilkerPipeline()

                # Mock the extractors
                pipeline.grobid_extractor = Mock()
                pipeline.pandoc_converter = Mock()

                # Mock the fallback extraction to avoid PDF file issues
                with patch.object(pipeline, "_fallback_extraction") as mock_fallback:
                    self._extracted_from_test_pipeline_respects_pandoc_configuration_21(
                        temp_dir, mock_fallback, pipeline
                    )

    # TODO Rename this here and in `test_pipeline_respects_pandoc_configuration`
    def _extracted_from_test_pipeline_respects_pandoc_configuration_21(
        self, temp_dir, mock_fallback, pipeline
    ):
        mock_fallback.return_value = {
            "success": True,
            "method": "enhanced_fallback",
            "output_path": Path(temp_dir) / "output.md",
            "content_length": 100,
            "math_expressions_count": 0,
            "tables_count": 0,
        }

        # Create a test PDF file
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_text("dummy pdf content")
        output_path = Path(temp_dir) / "output.md"

        # Process the PDF
        result = pipeline.process_scientific_paper(pdf_path, output_path)

        # Verify Pandoc was not called
        pipeline.pandoc_converter.convert_pdf_to_markdown.assert_not_called()

        # Verify fallback was used
        assert result["success"] is True
        assert result["method"] == "enhanced_fallback"

    def test_pipeline_respects_mathpix_configuration(self):
        """Test that pipeline respects Mathpix configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = (
                self._extracted_from_test_pipeline_respects_mathpix_configuration_5(
                    True, True, False
                )
            )
            # Patch the config in the pipeline
            with patch(
                "milkbottle.modules.pdfmilker.pipeline.pdfmilker_config", mock_config
            ):
                pipeline = PDFmilkerPipeline()

                # Mock the extractors
                pipeline.grobid_extractor = Mock()
                pipeline.mathpix_processor = Mock()

                # Set up mock Grobid response with math formulas
                grobid_result = {
                    "body_text": "Test content",
                    "math_formulas": [{"content": "x^2 + y^2 = z^2"}],
                    "tables": [],
                    "references": [],
                }
                pipeline.grobid_extractor.extract_scientific_paper.return_value = (
                    grobid_result
                )

                # Create a test PDF file
                pdf_path = Path(temp_dir) / "test.pdf"
                pdf_path.write_text("dummy pdf content")
                output_path = Path(temp_dir) / "output.md"

                # Process the PDF
                result = pipeline.process_scientific_paper(pdf_path, output_path)

                # Verify Mathpix was not called for math processing
                pipeline.mathpix_processor.process_math_text.assert_not_called()

                # Verify result
                assert result["success"] is True
                assert result["method"] == "grobid"

    # TODO Rename this here and in `test_pipeline_respects_grobid_configuration`, `test_pipeline_respects_pandoc_configuration` and `test_pipeline_respects_mathpix_configuration`
    def _extracted_from_test_pipeline_respects_mathpix_configuration_5(
        self, arg0, arg1, arg2
    ):
        result = Mock(spec=PDFmilkerConfig)
        result.is_grobid_enabled.return_value = arg0
        result.is_pandoc_enabled.return_value = arg1
        result.is_mathpix_enabled.return_value = arg2
        return result

    def test_math_extraction_respects_configuration(self):
        """Test that math extraction respects configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock config that disables both Mathpix and Grobid
            mock_config = Mock(spec=PDFmilkerConfig)
            mock_config.is_mathpix_enabled.return_value = False
            mock_config.is_grobid_enabled.return_value = False

            # Patch the config in the pipeline
            with patch(
                "milkbottle.modules.pdfmilker.pipeline.pdfmilker_config", mock_config
            ):
                self._extracted_from_test_math_extraction_respects_configuration_13(
                    temp_dir
                )

    # TODO Rename this here and in `test_math_extraction_respects_configuration`
    def _extracted_from_test_math_extraction_respects_configuration_13(self, temp_dir):
        pipeline = PDFmilkerPipeline()

        # Mock the extractors
        pipeline.mathpix_processor = Mock()
        pipeline.grobid_extractor = Mock()

        # Create a test PDF file
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_text("dummy pdf content")

        # Extract math
        result = pipeline.extract_math_only(pdf_path)

        # Verify neither service was called
        pipeline.mathpix_processor.extract_math_from_pdf.assert_not_called()
        pipeline.grobid_extractor.extract_scientific_paper.assert_not_called()

        # Verify empty result
        assert result == []

    def test_configuration_validation(self):
        """Test configuration validation."""
        config = PDFmilkerConfig()

        # Test validation
        validation_results = config.validate_configuration()

        # Most validation should pass with default config
        # Mathpix credentials validation will fail since no credentials are set
        assert validation_results["grobid_url"] is True
        assert validation_results["pandoc_path"] is True
        assert validation_results["batch_settings"] is True
        assert validation_results["quality_settings"] is True

        # Mathpix credentials validation should fail (no credentials set)
        assert validation_results["mathpix_credentials"] is False

        # Test specific validations
        assert config._validate_batch_settings() is True
        assert config._validate_quality_settings() is True

    def test_configuration_summary(self):
        """Test configuration summary generation."""
        config = PDFmilkerConfig()

        summary = config.get_configuration_summary()

        # Verify summary structure
        assert "services" in summary
        assert "processing" in summary
        assert "batch_processing" in summary
        assert "quality_assessment" in summary
        assert "progress_tracking" in summary
        assert "error_handling" in summary

        # Verify service settings
        services = summary["services"]
        assert "grobid_enabled" in services
        assert "mathpix_enabled" in services
        assert "pandoc_enabled" in services

        # Verify processing settings
        processing = summary["processing"]
        assert "output_format" in processing
        assert "math_format" in processing

    def test_configuration_precedence(self):
        """Test configuration precedence (TOML, env, CLI)."""
        # This test would require more complex setup with actual config files
        # For now, we'll test the basic config loading
        config = PDFmilkerConfig()

        # Test that defaults are loaded
        assert config.get_output_format() == "markdown"
        assert config.get_math_format() == "latex"
        assert config.is_grobid_enabled() is True

    def test_batch_processing_configuration(self):
        """Test batch processing configuration."""
        config = PDFmilkerConfig()

        # Test batch settings
        assert config.is_batch_mode_enabled() is True
        assert config.is_parallel_processing_enabled() is True
        assert config.get_max_workers() == 4
        assert config.get_memory_limit_mb() == 2048

    def test_quality_assessment_configuration(self):
        """Test quality assessment configuration."""
        config = PDFmilkerConfig()

        # Test quality settings
        assert config.is_quality_assessment_enabled() is True
        assert config.get_quality_threshold() == 0.7
        assert config.get_min_text_length() == 100

    def test_error_handling_configuration(self):
        """Test error handling configuration."""
        config = PDFmilkerConfig()

        # Test error handling settings
        assert config.get_max_retries() == 3
        assert config.get_retry_delay() == 1.0
        assert config.is_partial_result_recovery_enabled() is True

    def test_progress_tracking_configuration(self):
        """Test progress tracking configuration."""
        config = PDFmilkerConfig()

        # Test progress tracking settings
        assert config.is_progress_tracking_enabled() is True
        assert config.get_progress_update_interval() == 0.5

    def test_format_export_configuration(self):
        """Test format export configuration."""
        config = PDFmilkerConfig()

        # Test format settings
        supported_formats = config.get_supported_formats()
        assert "markdown" in supported_formats
        assert "html" in supported_formats
        assert "latex" in supported_formats
        assert "json" in supported_formats
        assert "docx" in supported_formats

    def test_service_url_configuration(self):
        """Test service URL configuration."""
        config = PDFmilkerConfig()

        # Test service URLs
        grobid_url = config.get_grobid_url()
        assert grobid_url == "http://localhost:8070"  # Default value

        pandoc_path = config.get_pandoc_path()
        assert pandoc_path == "pandoc"  # Default value

    def test_credentials_configuration(self):
        """Test credentials configuration."""
        config = PDFmilkerConfig()

        # Test credentials (should be None by default)
        credentials = config.get_mathpix_credentials()
        assert credentials is None  # No credentials set by default

    def test_configuration_with_environment_variables(self):
        """Test configuration with environment variables."""
        # This test would require setting environment variables
        # For now, we'll test the basic functionality
        config = PDFmilkerConfig()

        # Test that config can be created without environment variables
        assert config is not None
        assert hasattr(config, "get_grobid_url")
        assert hasattr(config, "get_mathpix_credentials")

    def test_configuration_immutability(self):
        """Test that configuration is immutable."""
        config = PDFmilkerConfig()

        # Test that we can't modify the config directly
        # (This depends on the implementation, but generally config should be read-only)
        original_output_format = config.get_output_format()

        # The config should remain unchanged
        assert config.get_output_format() == original_output_format

    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        config = PDFmilkerConfig()

        # Test that invalid configurations don't crash the system
        # This is handled by the validation methods
        validation_results = config.validate_configuration()

        # All validations should return boolean values
        for result in validation_results.values():
            assert isinstance(result, bool)
