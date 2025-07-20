"""Tests for Phase 4 features: Interactive Preview System and Configuration Wizards."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from milkbottle.preview_system import (
    InteractivePreview,
    PreviewConfig,
    PreviewResult,
    get_preview_system,
    preview_file,
)
from milkbottle.wizards import (
    ConfigurationWizard,
    FontMilkerWizard,
    PDFmilkerWizard,
    VenvMilkerWizard,
    run_wizard,
)


class TestPreviewConfig:
    """Test PreviewConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PreviewConfig()

        assert config.max_preview_size == 1000
        assert config.show_metadata is True
        assert config.show_structure is True
        assert config.show_quality_metrics is True
        assert config.auto_refresh is False
        assert config.refresh_interval == 2.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PreviewConfig(
            max_preview_size=500,
            show_metadata=False,
            auto_refresh=True,
            refresh_interval=5.0,
        )

        assert config.max_preview_size == 500
        assert config.show_metadata is False
        assert config.auto_refresh is True
        assert config.refresh_interval == 5.0


class TestPreviewResult:
    """Test PreviewResult dataclass."""

    def test_preview_result_creation(self):
        """Test creating a PreviewResult instance."""
        result = PreviewResult(
            content="Test content",
            metadata={"test": "data"},
            structure={"pages": 1},
            quality_metrics={"score": 0.8},
            file_size=1024,
            extraction_time=1.5,
            confidence_score=0.9,
            warnings=["Test warning"],
            errors=[],
        )

        assert result.content == "Test content"
        assert result.metadata["test"] == "data"
        assert result.structure["pages"] == 1
        assert result.quality_metrics["score"] == 0.8
        assert result.file_size == 1024
        assert result.extraction_time == 1.5
        assert result.confidence_score == 0.9
        assert result.warnings == ["Test warning"]
        assert result.errors == []


class TestInteractivePreview:
    """Test InteractivePreview class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.preview = InteractivePreview()
        self.test_pdf_path = Path("test.pdf")

    def test_init(self):
        """Test InteractivePreview initialization."""
        assert self.preview.config is not None
        assert isinstance(self.preview.config, PreviewConfig)
        assert self.preview.preview_cache == {}
        assert self.preview.live_display is None

    def test_create_pdf_preview_with_title_and_abstract(self):
        """Test PDF preview creation with title and abstract."""
        structured_content = {
            "title": "Test Document",
            "abstract": "This is a test abstract that should be truncated if too long.",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
            "tables": [{"data": "table1"}],
            "images": [{"path": "image1.jpg"}],
            "math_formulas": [{"latex": "x^2"}],
        }

        preview = self.preview._create_pdf_preview(structured_content)

        assert "Title: Test Document" in preview
        assert "Abstract: This is a test abstract" in preview
        assert "Page 1: Page 1 content" in preview
        assert "Page 2: Page 2 content" in preview
        assert "Tables: 1 found" in preview
        assert "Images: 1 found" in preview
        assert "Math Formulas: 1 found" in preview

    def test_create_pdf_preview_without_title_abstract(self):
        """Test PDF preview creation without title and abstract."""
        structured_content = {
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}]
        }

        preview = self.preview._create_pdf_preview(structured_content)

        assert "Title:" not in preview
        assert "Abstract:" not in preview
        assert "Page 1: Page 1 content" in preview
        assert "Page 2: Page 2 content" in preview

    def test_analyze_content_structure(self):
        """Test content structure analysis."""
        structured_content = {
            "pages": [{"text": "page1"}, {"text": "page2"}],
            "title": "Test Title",
            "abstract": "Test Abstract",
            "tables": [{"data": "table1"}],
            "images": [{"path": "image1.jpg"}],
            "math_formulas": [{"latex": "x^2"}],
            "references": ["ref1", "ref2"],
        }

        structure = self.preview._analyze_content_structure(structured_content)

        assert structure["total_pages"] == 2
        assert structure["has_title"] is True
        assert structure["has_abstract"] is True
        assert structure["has_tables"] is True
        assert structure["has_images"] is True
        assert structure["has_math"] is True
        assert structure["has_references"] is True

    @patch("milkbottle.modules.pdfmilker.extract.extract_text_structured")
    @patch("milkbottle.modules.pdfmilker.quality_assessor.QualityAssessor")
    def test_preview_pdf_extraction_success(self, mock_quality_assessor, mock_extract):
        """Test successful PDF preview extraction."""
        # Mock the extraction result
        mock_extract.return_value = {
            "title": "Test Document",
            "pages": [{"text": "Page content"}],
            "tables": [],
            "images": [],
        }

        # Mock the quality assessor
        mock_assessor_instance = Mock()
        mock_assessor_instance.assess_extraction_quality.return_value = {
            "overall_confidence": 0.8,
            "text_quality": 0.9,
        }
        mock_quality_assessor.return_value = mock_assessor_instance

        # Mock file stats
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value = Mock(st_size=1024)

            result = self.preview.preview_pdf_extraction(self.test_pdf_path)

        assert isinstance(result, PreviewResult)
        assert result.content is not None
        assert result.metadata["filename"] == "test.pdf"
        assert result.metadata["file_size"] == 1024
        assert result.confidence_score == 0.8
        assert result.errors == []

    @patch("milkbottle.modules.pdfmilker.extract.extract_text_structured")
    def test_preview_pdf_extraction_failure(self, mock_extract):
        """Test PDF preview extraction failure."""
        mock_extract.side_effect = Exception("Extraction failed")

        result = self.preview.preview_pdf_extraction(self.test_pdf_path)

        assert isinstance(result, PreviewResult)
        assert result.content == "Error during extraction"
        assert result.errors == ["Extraction failed"]
        assert result.confidence_score == 0.0

    def test_preview_cache(self):
        """Test preview caching functionality."""
        # Add a result to cache
        test_result = PreviewResult(
            content="test",
            metadata={},
            structure={},
            quality_metrics={},
            file_size=0,
            extraction_time=0.0,
            confidence_score=0.0,
            warnings=[],
            errors=[],
        )

        self.preview.preview_cache["test.pdf"] = test_result

        assert "test.pdf" in self.preview.preview_cache
        assert self.preview.preview_cache["test.pdf"] == test_result


class TestConfigurationWizard:
    """Test ConfigurationWizard base class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.wizard = ConfigurationWizard()

    def test_init(self):
        """Test ConfigurationWizard initialization."""
        assert self.wizard.config == {}
        assert self.wizard.current_step == 0
        assert self.wizard.total_steps == 0

    def test_display_progress(self):
        """Test progress display."""
        self.wizard.current_step = 2
        self.wizard.total_steps = 4

        # This should not raise an exception
        self.wizard.display_progress()

    def test_save_config(self):
        """Test configuration saving."""
        self.wizard.config = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            self.wizard.save_config(config_path)

            # Verify the file was created and contains the config
            assert config_path.exists()
            with open(config_path, "r") as f:
                saved_config = json.load(f)

            assert saved_config == {"test": "value"}
        finally:
            config_path.unlink(missing_ok=True)

    def test_run_not_implemented(self):
        """Test that run method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.wizard.run()


class TestPDFmilkerWizard:
    """Test PDFmilkerWizard class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.wizard = PDFmilkerWizard()

    def test_init(self):
        """Test PDFmilkerWizard initialization."""
        assert self.wizard.total_steps == 6
        assert self.wizard.config == {}

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_basic_settings(self, mock_confirm, mock_prompt):
        """Test basic settings configuration."""
        mock_prompt.return_value = "test_output"
        mock_confirm.side_effect = [True, False]  # verbose=True, dry_run=False

        self.wizard._configure_basic_settings()

        assert self.wizard.config["output_dir"] == "test_output"
        assert self.wizard.config["verbose"] is True
        assert self.wizard.config["dry_run"] is False

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_output_settings(self, mock_confirm, mock_prompt):
        """Test output settings configuration."""
        mock_prompt.return_value = "1,2"  # Select txt and json
        mock_confirm.side_effect = [
            True,
            True,
        ]  # include_images=True, include_tables=True

        self.wizard._configure_output_settings()

        assert self.wizard.config["formats"] == ["txt", "json"]
        assert self.wizard.config["include_images"] is True
        assert self.wizard.config["include_tables"] is True

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_services(self, mock_confirm, mock_prompt):
        """Test service configuration."""
        mock_confirm.side_effect = [True, False]  # use_grobid=True, use_mathpix=False
        mock_prompt.return_value = "http://localhost:8070"

        self.wizard._configure_services()

        assert self.wizard.config["services"]["grobid"]["enabled"] is True
        assert (
            self.wizard.config["services"]["grobid"]["url"] == "http://localhost:8070"
        )
        assert self.wizard.config["services"]["mathpix"]["enabled"] is False

    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        self.wizard.config = {
            "output_dir": "test_output",
            "services": {"grobid": {"enabled": False}, "mathpix": {"enabled": False}},
        }

        assert self.wizard._validate_configuration() is True

    def test_validate_configuration_failure(self):
        """Test failed configuration validation."""
        self.wizard.config = {
            "services": {
                "grobid": {"enabled": True},  # Missing URL
                "mathpix": {"enabled": True},  # Missing credentials
            }
        }

        assert self.wizard._validate_configuration() is False


class TestVenvMilkerWizard:
    """Test VenvMilkerWizard class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.wizard = VenvMilkerWizard()

    def test_init(self):
        """Test VenvMilkerWizard initialization."""
        assert self.wizard.total_steps == 4
        assert self.wizard.config == {}

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_python(self, mock_confirm, mock_prompt):
        """Test Python configuration."""
        mock_prompt.return_value = "3.12"
        mock_confirm.return_value = True  # use_system_python=True

        self.wizard._configure_python()

        assert self.wizard.config["python"] == "3.12"
        assert self.wizard.config["python_path"] is None

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_packages(self, mock_confirm, mock_prompt):
        """Test package configuration."""
        mock_prompt.return_value = "rich,typer,pytest"
        mock_confirm.side_effect = [True, False]  # snapshot=True, upgrade=False

        self.wizard._configure_packages()

        assert self.wizard.config["install"] == ["rich", "typer", "pytest"]
        assert self.wizard.config["snapshot"] is True
        assert self.wizard.config["upgrade"] is False


class TestFontMilkerWizard:
    """Test FontMilkerWizard class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.wizard = FontMilkerWizard()

    def test_init(self):
        """Test FontMilkerWizard initialization."""
        assert self.wizard.total_steps == 3
        assert self.wizard.config == {}

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_extraction(self, mock_confirm, mock_prompt):
        """Test extraction configuration."""
        mock_prompt.side_effect = ["fonts_output", "1,2"]  # output_dir, format_choice

        self.wizard._configure_extraction()

        assert self.wizard.config["output_dir"] == "fonts_output"
        assert self.wizard.config["extract_formats"] == ["ttf", "otf"]

    @patch("milkbottle.wizards.Prompt.ask")
    @patch("milkbottle.wizards.Confirm.ask")
    def test_configure_analysis(self, mock_confirm, mock_prompt):
        """Test analysis configuration."""
        mock_confirm.side_effect = [
            True,
            True,
        ]  # enable_analysis=True, generate_reports=True
        mock_prompt.return_value = "detailed"

        self.wizard._configure_analysis()

        assert self.wizard.config["analyze_fonts"] is True
        assert self.wizard.config["analysis_depth"] == "detailed"
        assert self.wizard.config["generate_reports"] is True


class TestWizardFunctions:
    """Test wizard utility functions."""

    def test_run_wizard_valid_type(self):
        """Test running a valid wizard type."""
        with patch("milkbottle.wizards.PDFmilkerWizard") as mock_wizard_class:
            mock_wizard = Mock()
            mock_wizard.run.return_value = {"test": "config"}
            mock_wizard_class.return_value = mock_wizard

            config = run_wizard("pdfmilker")

            assert config == {"test": "config"}
            mock_wizard.run.assert_called_once()

    def test_run_wizard_invalid_type(self):
        """Test running an invalid wizard type."""
        with pytest.raises(ValueError, match="Unknown wizard type: invalid"):
            run_wizard("invalid")


class TestPreviewFunctions:
    """Test preview utility functions."""

    def test_get_preview_system(self):
        """Test getting the global preview system."""
        # Clear any existing instance
        import milkbottle.preview_system

        milkbottle.preview_system._preview_system = None

        preview_system = get_preview_system()

        assert isinstance(preview_system, InteractivePreview)

        # Test that subsequent calls return the same instance
        preview_system2 = get_preview_system()
        assert preview_system is preview_system2

    @patch("milkbottle.preview_system.get_preview_system")
    def test_preview_file(self, mock_get_preview):
        """Test preview_file function."""
        mock_preview_system = Mock()
        mock_preview_system.interactive_preview_workflow.return_value = True
        mock_get_preview.return_value = mock_preview_system

        test_path = Path("test.pdf")
        result = preview_file(test_path)

        assert result is True
        mock_preview_system.interactive_preview_workflow.assert_called_once_with(
            test_path
        )


class TestIntegration:
    """Integration tests for Phase 4 features."""

    def test_preview_system_integration(self):
        """Test preview system integration with existing modules."""
        preview_system = InteractivePreview()

        # Test that the preview system can be created without errors
        assert preview_system is not None
        assert hasattr(preview_system, "preview_pdf_extraction")
        assert hasattr(preview_system, "interactive_preview_workflow")

    def test_wizard_integration(self):
        """Test wizard integration."""
        # Test that all wizards can be created
        pdf_wizard = PDFmilkerWizard()
        venv_wizard = VenvMilkerWizard()
        font_wizard = FontMilkerWizard()

        assert pdf_wizard is not None
        assert venv_wizard is not None
        assert font_wizard is not None

        assert pdf_wizard.total_steps == 6
        assert venv_wizard.total_steps == 4
        assert font_wizard.total_steps == 3

    def test_configuration_persistence(self):
        """Test configuration persistence."""
        wizard = PDFmilkerWizard()
        wizard.config = {"test": "value", "nested": {"key": "value"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            wizard.save_config(config_path)

            # Verify the file was created and contains the config
            assert config_path.exists()
            with open(config_path, "r") as f:
                saved_config = json.load(f)

            assert saved_config == {"test": "value", "nested": {"key": "value"}}
        finally:
            config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])
