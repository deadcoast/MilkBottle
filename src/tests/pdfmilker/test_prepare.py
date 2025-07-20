"""Unit tests for PDFmilker prepare module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from milkbottle.modules.pdfmilker.prepare import prepare_output_tree


class TestPrepareOutputTree:
    """Test cases for prepare_output_tree function."""

    def test_prepare_output_tree_basic(self, tmp_path):
        """Test basic output tree creation."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = tmp_path / "output"

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            result = prepare_output_tree(pdf_path, outdir)

        # Check that all required directories were created
        expected_base = outdir / "document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

        # Verify directories actually exist
        for path in result.values():
            assert path.exists()
            assert path.is_dir()

    def test_prepare_output_tree_with_special_characters(self, tmp_path):
        """Test output tree creation with special characters in filename."""
        pdf_path = Path("/path/to/My Document (2024).pdf")
        outdir = tmp_path / "output"

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify",
            return_value="my-document-2024",
        ):
            result = prepare_output_tree(pdf_path, outdir)

        expected_base = outdir / "my-document-2024"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_with_unicode_filename(self, tmp_path):
        """Test output tree creation with Unicode characters in filename."""
        pdf_path = Path("/path/to/测试文档.pdf")
        outdir = tmp_path / "output"

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify",
            return_value="ce-shi-wen-dang",
        ):
            result = prepare_output_tree(pdf_path, outdir)

        expected_base = outdir / "ce-shi-wen-dang"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_with_long_filename(self, tmp_path):
        """Test output tree creation with very long filename."""
        long_name = "a" * 200  # Very long filename
        pdf_path = Path(f"/path/to/{long_name}.pdf")
        outdir = tmp_path / "output"

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify",
            return_value="very-long-slug",
        ):
            result = prepare_output_tree(pdf_path, outdir)

        expected_base = outdir / "very-long-slug"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_with_tilde_expansion(self, tmp_path):
        """Test output tree creation with tilde in path (home directory expansion)."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = Path("~/test_output")

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            with patch(
                "pathlib.Path.expanduser", return_value=tmp_path / "test_output"
            ):
                result = prepare_output_tree(pdf_path, outdir)

        expected_base = tmp_path / "test_output" / "document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_with_relative_paths(self, tmp_path):
        """Test output tree creation with relative paths."""
        pdf_path = Path("relative/path/document.pdf")
        outdir = Path("relative/output")

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            with patch(
                "pathlib.Path.resolve", return_value=tmp_path / "absolute" / "output"
            ):
                result = prepare_output_tree(pdf_path, outdir)

        expected_base = tmp_path / "absolute" / "output" / "document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_existing_directories(self, tmp_path):
        """Test output tree creation when directories already exist."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = tmp_path / "output"

        # Pre-create some directories
        base_dir = outdir / "document"
        base_dir.mkdir(parents=True)
        (base_dir / "markdown").mkdir()
        (base_dir / "images").mkdir()

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            result = prepare_output_tree(pdf_path, outdir)

        # Should still work and return the correct paths
        expected_base = outdir / "document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

        # All directories should exist
        for path in result.values():
            assert path.exists()
            assert path.is_dir()

    def test_prepare_output_tree_nested_output_directory(self, tmp_path):
        """Test output tree creation in nested output directory."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = tmp_path / "output" / "nested" / "deep"

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            result = prepare_output_tree(pdf_path, outdir)

        expected_base = outdir / "document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

        # Verify the nested structure was created
        assert outdir.exists()
        assert expected_base.exists()

    def test_prepare_output_tree_permission_error(self, tmp_path):
        """Test output tree creation when permission is denied."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = tmp_path / "output"

        # Mock mkdir to raise PermissionError
        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            with patch(
                "pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")
            ):
                with pytest.raises(PermissionError):
                    prepare_output_tree(pdf_path, outdir)

    def test_prepare_output_tree_disk_full_error(self, tmp_path):
        """Test output tree creation when disk is full."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = tmp_path / "output"

        # Mock mkdir to raise OSError (disk full)
        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            with patch(
                "pathlib.Path.mkdir", side_effect=OSError("No space left on device")
            ):
                with pytest.raises(OSError):
                    prepare_output_tree(pdf_path, outdir)

    def test_prepare_output_tree_invalid_output_path(self, tmp_path):
        """Test output tree creation with invalid output path."""
        pdf_path = Path("/path/to/document.pdf")
        outdir = Path("/invalid/path/that/does/not/exist")

        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify", return_value="document"
        ):
            with pytest.raises(Exception):  # Should raise some exception
                prepare_output_tree(pdf_path, outdir)

    def test_prepare_output_tree_empty_filename(self, tmp_path):
        """Test output tree creation with empty filename."""
        pdf_path = Path("/path/to/.pdf")  # Empty stem
        outdir = tmp_path / "output"

        with patch("milkbottle.modules.pdfmilker.prepare.slugify", return_value=""):
            result = prepare_output_tree(pdf_path, outdir)

        expected_base = outdir / ""
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"

    def test_prepare_output_tree_slugify_integration(self, tmp_path):
        """Test that slugify is called correctly with the PDF stem."""
        pdf_path = Path("/path/to/My Test Document.pdf")
        outdir = tmp_path / "output"

        with patch("milkbottle.modules.pdfmilker.prepare.slugify") as mock_slugify:
            mock_slugify.return_value = "my-test-document"
            result = prepare_output_tree(pdf_path, outdir)

        # Verify slugify was called with the correct stem
        mock_slugify.assert_called_once_with("My Test Document")

        # Verify the result uses the slugified name
        expected_base = outdir / "my-test-document"
        assert result["markdown"] == expected_base / "markdown"
        assert result["images"] == expected_base / "images"
        assert result["pdf"] == expected_base / "pdf"
        assert result["meta"] == expected_base / "meta"


class TestPrepareIntegration:
    """Integration tests for prepare module."""

    def test_prepare_output_tree_full_workflow(self, tmp_path):
        """Test the complete workflow of preparing output tree."""
        # Create a realistic PDF path
        pdf_path = Path("/home/user/documents/Research Paper (2024).pdf")
        outdir = tmp_path / "extracted_pdfs"

        # Mock slugify to return a realistic slug
        with patch(
            "milkbottle.modules.pdfmilker.prepare.slugify",
            return_value="research-paper-2024",
        ):
            result = prepare_output_tree(pdf_path, outdir)

        # Verify the complete directory structure
        base_dir = outdir / "research-paper-2024"
        expected_structure = {
            "markdown": base_dir / "markdown",
            "images": base_dir / "images",
            "pdf": base_dir / "pdf",
            "meta": base_dir / "meta",
        }

        assert result == expected_structure

        # Verify all directories exist and are empty
        for name, path in result.items():
            assert path.exists()
            assert path.is_dir()
            assert not any(path.iterdir())  # Should be empty

    def test_prepare_output_tree_multiple_pdfs(self, tmp_path):
        """Test preparing output trees for multiple PDFs."""
        pdf_paths = [
            Path("/path/to/doc1.pdf"),
            Path("/path/to/doc2.pdf"),
            Path("/path/to/doc3.pdf"),
        ]
        outdir = tmp_path / "output"

        results = []
        with patch("milkbottle.modules.pdfmilker.prepare.slugify") as mock_slugify:
            mock_slugify.side_effect = ["doc1", "doc2", "doc3"]

            for pdf_path in pdf_paths:
                result = prepare_output_tree(pdf_path, outdir)
                results.append(result)

        # Verify each PDF got its own directory structure
        assert len(results) == 3

        for i, result in enumerate(results):
            expected_base = outdir / f"doc{i+1}"
            assert result["markdown"] == expected_base / "markdown"
            assert result["images"] == expected_base / "images"
            assert result["pdf"] == expected_base / "pdf"
            assert result["meta"] == expected_base / "meta"
            assert result["meta"] == expected_base / "meta"
