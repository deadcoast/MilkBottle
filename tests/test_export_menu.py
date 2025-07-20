"""Tests for Export Options Menu functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from milkbottle.export_menu import (
    ExportFormat,
    ExportOptionsMenu,
    ExportPreview,
    export_content_interactive,
    get_export_menu,
)


class TestExportFormat:
    """Test ExportFormat dataclass."""

    def test_export_format_creation(self):
        """Test creating an ExportFormat instance."""
        format_info = ExportFormat(
            name="Test Format",
            extension=".test",
            description="Test format for testing",
            supported_features=["text", "tables"],
            config_options={"option1": True, "option2": "value"},
            preview_supported=True,
        )

        assert format_info.name == "Test Format"
        assert format_info.extension == ".test"
        assert format_info.description == "Test format for testing"
        assert format_info.supported_features == ["text", "tables"]
        assert format_info.config_options == {"option1": True, "option2": "value"}
        assert format_info.preview_supported is True

    def test_export_format_defaults(self):
        """Test ExportFormat with default values."""
        format_info = ExportFormat(
            name="Test Format",
            extension=".test",
            description="Test format",
            supported_features=["text"],
            config_options={},
        )

        assert format_info.preview_supported is True


class TestExportPreview:
    """Test ExportPreview dataclass."""

    def test_export_preview_creation(self):
        """Test creating an ExportPreview instance."""
        preview = ExportPreview(
            format_name="Test Format",
            content="Test content",
            metadata={"test": "data"},
            file_size=1024,
            quality_score=0.8,
            warnings=["Test warning"],
            errors=[],
        )

        assert preview.format_name == "Test Format"
        assert preview.content == "Test content"
        assert preview.metadata["test"] == "data"
        assert preview.file_size == 1024
        assert preview.quality_score == 0.8
        assert preview.warnings == ["Test warning"]
        assert preview.errors == []


class TestExportOptionsMenu:
    """Test ExportOptionsMenu class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.export_menu = ExportOptionsMenu()

    def test_init(self):
        """Test ExportOptionsMenu initialization."""
        assert self.export_menu.available_formats is not None
        assert len(self.export_menu.available_formats) > 0
        assert self.export_menu.selected_formats == []
        assert self.export_menu.export_config == {}

    def test_initialize_formats(self):
        """Test format initialization."""
        formats = self.export_menu._initialize_formats()

        # Check that expected formats are present
        assert "txt" in formats
        assert "json" in formats
        assert "markdown" in formats
        assert "html" in formats
        assert "latex" in formats

        # Check format structure
        txt_format = formats["txt"]
        assert isinstance(txt_format, ExportFormat)
        assert txt_format.name == "Plain Text"
        assert txt_format.extension == ".txt"
        assert "text" in txt_format.supported_features

    @patch("milkbottle.export_menu.Prompt.ask")
    def test_show_format_selection_all(self, mock_prompt):
        """Test format selection with 'all' option."""
        mock_prompt.return_value = "all"

        content_data = {"title": "Test Document"}
        selected = self.export_menu.show_format_selection(content_data)

        assert selected == list(self.export_menu.available_formats.keys())

    @patch("milkbottle.export_menu.Prompt.ask")
    def test_show_format_selection_specific(self, mock_prompt):
        """Test format selection with specific choices."""
        mock_prompt.return_value = "1,2"

        content_data = {"title": "Test Document"}
        selected = self.export_menu.show_format_selection(content_data)

        format_ids = list(self.export_menu.available_formats.keys())
        expected = [format_ids[0], format_ids[1]]
        assert selected == expected

    @patch("milkbottle.export_menu.Prompt.ask")
    def test_show_format_selection_invalid(self, mock_prompt):
        """Test format selection with invalid input."""
        mock_prompt.return_value = "invalid"

        content_data = {"title": "Test Document"}
        selected = self.export_menu.show_format_selection(content_data)

        # Should default to txt, json
        assert selected == ["txt", "json"]

    def test_generate_txt_preview(self):
        """Test TXT preview generation."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }

        preview = self.export_menu._generate_txt_preview(content_data)

        assert "Title: Test Document" in preview
        assert "Abstract: Test abstract" in preview
        assert "Page 1 content" in preview
        assert "Page 2 content" in preview

    def test_generate_json_preview(self):
        """Test JSON preview generation."""
        content_data = {
            "title": "Test Document",
            "pages": [{"text": "content"}],
            "tables": [{"data": "table"}],
            "images": [{"path": "image.jpg"}],
        }

        preview = self.export_menu._generate_json_preview(content_data)

        # Should be valid JSON
        parsed = json.loads(preview)
        assert parsed["title"] == "Test Document"
        assert parsed["pages_count"] == 1
        assert parsed["tables_count"] == 1
        assert parsed["images_count"] == 1

    def test_generate_markdown_preview(self):
        """Test Markdown preview generation."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }

        preview = self.export_menu._generate_markdown_preview(content_data)

        assert "# Test Document" in preview
        assert "**Abstract:**" in preview
        assert "## Page 1" in preview
        assert "## Page 2" in preview

    def test_generate_html_preview(self):
        """Test HTML preview generation."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }

        preview = self.export_menu._generate_html_preview(content_data)

        assert "<!DOCTYPE html>" in preview
        assert "<title>Document Preview</title>" in preview
        assert "<h1>Test Document</h1>" in preview
        assert "<h2>Page 1</h2>" in preview

    def test_generate_latex_preview(self):
        """Test LaTeX preview generation."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }

        preview = self.export_menu._generate_latex_preview(content_data)

        assert "\\documentclass{article}" in preview
        assert "\\title{Test Document}" in preview
        assert "\\begin{abstract}" in preview
        assert "\\section*{Page 1}" in preview

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "tables": [{"data": "table"}],
            "images": [{"path": "image.jpg"}],
            "math_formulas": [{"latex": "x^2"}],
        }

        score = self.export_menu._calculate_quality_score("json", content_data)

        # Should be between 0 and 1
        assert 0 <= score <= 1
        # Should be higher for rich content
        assert score > 0.5

    def test_calculate_quality_score_minimal(self):
        """Test quality score calculation with minimal content."""
        content_data = {"pages": [{"text": "content"}]}

        score = self.export_menu._calculate_quality_score("txt", content_data)

        # Should be base score for minimal content
        assert score == 0.5

    @patch("milkbottle.export_menu.Prompt.ask")
    @patch("milkbottle.export_menu.Confirm.ask")
    def test_configure_export_options(self, mock_confirm, mock_prompt):
        """Test export options configuration."""
        self.export_menu.selected_formats = ["txt", "json"]
        mock_prompt.return_value = "utf-8"
        # Provide enough responses for all boolean options in txt and json formats
        mock_confirm.side_effect = [
            True,
            False,
            True,
            True,
            True,
        ]  # All boolean options

        config = self.export_menu.configure_export_options()

        assert "txt" in config
        assert "json" in config
        assert config["txt"]["encoding"] == "utf-8"
        assert config["txt"]["line_breaks"] is True
        assert config["txt"]["preserve_formatting"] is False

    def test_export_to_txt(self):
        """Test TXT export."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }
        config = {
            "encoding": "utf-8",
            "line_breaks": True,
            "preserve_formatting": False,
        }

        content = self.export_menu._export_to_txt(content_data, config)

        assert "Test Document" in content
        assert "ABSTRACT" in content
        assert "Page 1 content" in content
        assert "Page 2 content" in content

    def test_export_to_json(self):
        """Test JSON export."""
        content_data = {
            "title": "Test Document",
            "pages": [{"text": "content"}],
            "tables": [{"data": "table"}],
        }
        config = {"indent": 2, "include_metadata": True, "include_images": True}

        content = self.export_menu._export_to_json(content_data, config)

        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed["title"] == "Test Document"
        assert len(parsed["pages"]) == 1
        assert len(parsed["tables"]) == 1

    def test_export_to_markdown(self):
        """Test Markdown export."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }
        config = {
            "include_toc": True,
            "preserve_formatting": True,
            "image_format": "markdown",
        }

        content = self.export_menu._export_to_markdown(content_data, config)

        assert "# Test Document" in content
        assert "## Abstract" in content
        assert "## Page 1" in content
        assert "## Page 2" in content

    def test_export_to_html(self):
        """Test HTML export."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }
        config = {"include_css": True, "responsive": True, "include_metadata": True}

        content = self.export_menu._export_to_html(content_data, config)

        assert "<!DOCTYPE html>" in content
        assert "<title>Test Document</title>" in content
        assert "<h1>Test Document</h1>" in content
        assert "<style>" in content  # CSS included

    def test_export_to_latex(self):
        """Test LaTeX export."""
        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
        }
        config = {
            "document_class": "article",
            "include_bibliography": True,
            "math_mode": True,
        }

        content = self.export_menu._export_to_latex(content_data, config)

        assert "\\documentclass{article}" in content
        assert "\\title{Test Document}" in content
        assert "\\begin{abstract}" in content
        assert "\\section*{Page 1}" in content

    def test_execute_export(self):
        """Test export execution."""
        self.export_menu.selected_formats = ["txt", "json"]
        self.export_menu.export_config = {
            "txt": {
                "encoding": "utf-8",
                "line_breaks": True,
                "preserve_formatting": False,
            },
            "json": {"indent": 2, "include_metadata": True, "include_images": True},
        }

        content_data = {"title": "Test Document", "pages": [{"text": "content"}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            results = self.export_menu.execute_export(content_data, output_dir)

            assert "txt" in results
            assert "json" in results
            assert not results["txt"].startswith("Error:")
            assert not results["json"].startswith("Error:")

            # Check that files were created
            txt_file = Path(results["txt"])
            json_file = Path(results["json"])
            assert txt_file.exists()
            assert json_file.exists()


class TestExportFunctions:
    """Test export utility functions."""

    def test_get_export_menu(self):
        """Test getting the export menu instance."""
        export_menu = get_export_menu()

        assert isinstance(export_menu, ExportOptionsMenu)
        assert export_menu.available_formats is not None

    @patch("milkbottle.export_menu.ExportOptionsMenu.show_format_selection")
    @patch("milkbottle.export_menu.ExportOptionsMenu.show_format_previews")
    @patch("milkbottle.export_menu.ExportOptionsMenu.configure_export_options")
    @patch("milkbottle.export_menu.ExportOptionsMenu.execute_export")
    def test_export_content_interactive(
        self, mock_execute, mock_config, mock_previews, mock_selection
    ):
        """Test interactive export function."""
        mock_selection.return_value = ["txt", "json"]
        mock_previews.return_value = {}
        mock_config.return_value = {"txt": {}, "json": {}}
        mock_execute.return_value = {"txt": "test.txt", "json": "test.json"}

        content_data = {"title": "Test Document"}
        output_dir = Path("test_output")

        results = export_content_interactive(content_data, output_dir)

        assert results == {"txt": "test.txt", "json": "test.json"}
        mock_selection.assert_called_once_with(content_data)
        mock_previews.assert_called_once_with(content_data)
        mock_config.assert_called_once()
        mock_execute.assert_called_once_with(content_data, output_dir)


class TestIntegration:
    """Integration tests for export menu."""

    def test_export_menu_integration(self):
        """Test export menu integration."""
        export_menu = ExportOptionsMenu()

        # Test that the export menu can be created without errors
        assert export_menu is not None
        assert hasattr(export_menu, "show_format_selection")
        assert hasattr(export_menu, "show_format_previews")
        assert hasattr(export_menu, "configure_export_options")
        assert hasattr(export_menu, "execute_export")

    def test_format_preview_integration(self):
        """Test format preview integration."""
        export_menu = ExportOptionsMenu()

        content_data = {
            "title": "Test Document",
            "abstract": "Test abstract",
            "pages": [{"text": "Page 1 content"}, {"text": "Page 2 content"}],
            "tables": [{"data": "table"}],
            "images": [{"path": "image.jpg"}],
        }

        # Test preview generation for all formats
        for format_id in ["txt", "json", "markdown", "html", "latex"]:
            preview = export_menu._generate_format_preview(format_id, content_data)
            assert isinstance(preview, ExportPreview)
            assert preview.format_name is not None
            assert preview.content is not None
            assert 0 <= preview.quality_score <= 1

    def test_export_integration(self):
        """Test export integration."""
        export_menu = ExportOptionsMenu()

        content_data = {"title": "Test Document", "pages": [{"text": "content"}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Test export for txt format
            result = export_menu._export_to_format("txt", content_data, output_dir)
            assert result.exists()

            # Check file content
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
                assert "Test Document" in content

    def test_configuration_persistence(self):
        """Test configuration persistence."""
        export_menu = ExportOptionsMenu()
        export_menu.selected_formats = ["txt", "json"]

        # Configure options
        export_menu.export_config = {
            "txt": {"encoding": "utf-8", "line_breaks": True},
            "json": {"indent": 4, "include_metadata": True},
        }

        # Verify configuration
        assert export_menu.export_config["txt"]["encoding"] == "utf-8"
        assert export_menu.export_config["json"]["indent"] == 4


if __name__ == "__main__":
    pytest.main([__file__])
