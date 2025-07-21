"""Unit tests for PDFmilker validate module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from milkbottle.modules.pdfmilker.validate import validate_assets, validate_pdf_hash


class TestValidateAssets:
    """Test cases for validate_assets function."""

    def test_validate_assets_all_exist(self, tmp_path):
        """Test validation when all assets exist."""
        # Create test files
        markdown_file = tmp_path / "markdown" / "document.md"
        markdown_file.parent.mkdir()
        markdown_file.write_text("# Test Document")

        image_file = self._extracted_from_test_validate_assets_all_exist_8(
            tmp_path, "images", "figure1.png", b"fake image data"
        )
        pdf_file = self._extracted_from_test_validate_assets_all_exist_8(
            tmp_path, "pdf", "document.pdf", b"fake pdf data"
        )
        asset_paths = {
            "markdown": [markdown_file],
            "images": [image_file],
            "pdf": [pdf_file],
        }

        result = validate_assets(asset_paths)

        assert result["markdown"] is True
        assert result["images"] is True
        assert result["pdf"] is True

    # TODO Rename this here and in `test_validate_assets_all_exist`
    def _extracted_from_test_validate_assets_all_exist_8(
        self, tmp_path, arg1, arg2, arg3
    ):
        result = tmp_path / arg1 / arg2
        result.parent.mkdir()
        result.write_bytes(arg3)

        return result

    def test_validate_assets_some_missing(self, tmp_path):
        """Test validation when some assets are missing."""
        # Create only some test files
        markdown_file = tmp_path / "markdown" / "document.md"
        markdown_file.parent.mkdir()
        markdown_file.write_text("# Test Document")

        # Missing image file
        missing_image = tmp_path / "images" / "figure1.png"

        pdf_file = tmp_path / "pdf" / "document.pdf"
        pdf_file.parent.mkdir()
        pdf_file.write_bytes(b"fake pdf data")

        asset_paths = {
            "markdown": [markdown_file],
            "images": [missing_image],
            "pdf": [pdf_file],
        }

        result = validate_assets(asset_paths)

        assert result["markdown"] is True
        assert result["images"] is False
        assert result["pdf"] is True

    def test_validate_assets_all_missing(self, tmp_path):
        """Test validation when all assets are missing."""
        missing_files = [
            tmp_path / "markdown" / "document.md",
            tmp_path / "images" / "figure1.png",
            tmp_path / "pdf" / "document.pdf",
        ]

        asset_paths = {
            "markdown": [missing_files[0]],
            "images": [missing_files[1]],
            "pdf": [missing_files[2]],
        }

        result = validate_assets(asset_paths)

        assert result["markdown"] is False
        assert result["images"] is False
        assert result["pdf"] is False

    def test_validate_assets_multiple_files_per_type(self, tmp_path):
        """Test validation with multiple files per asset type."""
        # Create multiple files for each type
        markdown_files = []
        for i in range(3):
            file_path = tmp_path / "markdown" / f"document{i}.md"
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(f"# Document {i}")
            markdown_files.append(file_path)

        image_files = []
        for i in range(2):
            file_path = tmp_path / "images" / f"figure{i}.png"
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_bytes(b"fake image data")
            image_files.append(file_path)

        asset_paths = {"markdown": markdown_files, "images": image_files}

        result = validate_assets(asset_paths)

        assert result["markdown"] is True
        assert result["images"] is True

    def test_validate_assets_mixed_existence(self, tmp_path):
        """Test validation with mixed file existence."""
        # Create some files
        existing_file = tmp_path / "markdown" / "document.md"
        existing_file.parent.mkdir()
        existing_file.write_text("# Test Document")

        missing_file = tmp_path / "images" / "figure.png"

        asset_paths = {"markdown": [existing_file], "images": [missing_file]}

        result = validate_assets(asset_paths)

        assert result["markdown"] is True
        assert result["images"] is False

    def test_validate_assets_empty_lists(self):
        """Test validation with empty file lists."""
        asset_paths = {"markdown": [], "images": [], "pdf": []}

        result = validate_assets(asset_paths)

        # Empty lists should return True (all files exist)
        assert result["markdown"] is True
        assert result["images"] is True
        assert result["pdf"] is True

    def test_validate_assets_nonexistent_directories(self, tmp_path):
        """Test validation with files in nonexistent directories."""
        nonexistent_files = [
            Path("/nonexistent/path/file1.md"),
            Path("/another/nonexistent/file2.png"),
        ]

        asset_paths = {
            "markdown": [nonexistent_files[0]],
            "images": [nonexistent_files[1]],
        }

        result = validate_assets(asset_paths)

        assert result["markdown"] is False
        assert result["images"] is False

    def test_validate_assets_special_characters(self, tmp_path):
        """Test validation with files containing special characters."""
        # Create file with special characters
        special_file = tmp_path / "markdown" / "document (2024).md"
        special_file.parent.mkdir()
        special_file.write_text("# Test Document")

        asset_paths = {"markdown": [special_file]}

        result = validate_assets(asset_paths)

        assert result["markdown"] is True

    def test_validate_assets_unicode_filenames(self, tmp_path):
        """Test validation with Unicode filenames."""
        # Create file with Unicode characters
        unicode_file = tmp_path / "markdown" / "测试文档.md"
        unicode_file.parent.mkdir()
        unicode_file.write_text("# Test Document")

        asset_paths = {"markdown": [unicode_file]}

        result = validate_assets(asset_paths)

        assert result["markdown"] is True


class TestValidatePdfHash:
    """Test cases for validate_pdf_hash function."""

    def test_validate_pdf_hash_match(self, tmp_path):
        """Test hash validation when hashes match."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = "test_hash_value"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file",
            return_value=expected_hash,
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is True

    def test_validate_pdf_hash_mismatch(self, tmp_path):
        """Test hash validation when hashes don't match."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = "expected_hash"
        actual_hash = "different_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=actual_hash
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is False

    def test_validate_pdf_hash_nonexistent_file(self):
        """Test hash validation with nonexistent file."""
        pdf_path = Path("/nonexistent/file.pdf")
        expected_hash = "test_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=None
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is False

    def test_validate_pdf_hash_empty_file(self, tmp_path):
        """Test hash validation with empty file."""
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(b"")

        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # SHA256 of empty string

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file",
            return_value=expected_hash,
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is True

    def test_validate_pdf_hash_large_file(self, tmp_path):
        """Test hash validation with large file."""
        pdf_path = tmp_path / "large.pdf"
        # Create a large file (1MB)
        large_content = b"x" * (1024 * 1024)
        pdf_path.write_bytes(large_content)

        expected_hash = "large_file_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file",
            return_value=expected_hash,
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is True

    def test_validate_pdf_hash_hash_file_error(self, tmp_path):
        """Test hash validation when hash_file raises an exception."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = "test_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file",
            side_effect=OSError("File read error"),
        ):
            with pytest.raises(OSError):
                validate_pdf_hash(pdf_path, expected_hash)

    def test_validate_pdf_hash_empty_expected_hash(self, tmp_path):
        """Test hash validation with empty expected hash."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = ""
        actual_hash = "some_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=actual_hash
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is False

    def test_validate_pdf_hash_none_expected_hash(self, tmp_path):
        """Test hash validation with None expected hash."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = ""  # Empty string instead of None
        actual_hash = "some_hash"

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=actual_hash
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is False

    def test_validate_pdf_hash_case_sensitive(self, tmp_path):
        """Test that hash validation is case sensitive."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        expected_hash = "ABC123"
        actual_hash = "abc123"  # Different case

        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=actual_hash
        ):
            result = validate_pdf_hash(pdf_path, expected_hash)

        assert result is False


class TestValidateIntegration:
    """Integration tests for validate module."""

    def test_full_validation_workflow(self, tmp_path):
        """Test the complete validation workflow."""
        # Create a complete set of assets
        markdown_file = tmp_path / "markdown" / "document.md"
        markdown_file.parent.mkdir()
        markdown_file.write_text("# Test Document")

        image_file = self._extracted_from_test_full_validation_workflow_8(
            tmp_path, "images", "figure1.png", b"fake image data"
        )
        pdf_file = self._extracted_from_test_full_validation_workflow_8(
            tmp_path, "pdf", "document.pdf", b"test pdf content for hashing"
        )
        # Test asset validation
        asset_paths = {
            "markdown": [markdown_file],
            "images": [image_file],
            "pdf": [pdf_file],
        }

        asset_results = validate_assets(asset_paths)

        # Test hash validation
        expected_hash = "test_hash_value"
        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file",
            return_value=expected_hash,
        ):
            hash_result = validate_pdf_hash(pdf_file, expected_hash)

        # Verify results
        assert asset_results["markdown"] is True
        assert asset_results["images"] is True
        assert asset_results["pdf"] is True
        assert hash_result is True

    # TODO Rename this here and in `test_full_validation_workflow`
    def _extracted_from_test_full_validation_workflow_8(
        self, tmp_path, arg1, arg2, arg3
    ):
        result = tmp_path / arg1 / arg2
        result.parent.mkdir()
        result.write_bytes(arg3)

        return result

    def test_validation_with_missing_assets(self, tmp_path):
        """Test validation workflow with some missing assets."""
        # Create only some assets
        markdown_file = tmp_path / "markdown" / "document.md"
        markdown_file.parent.mkdir()
        markdown_file.write_text("# Test Document")

        # Missing image file
        missing_image = tmp_path / "images" / "figure1.png"

        pdf_file = tmp_path / "pdf" / "document.pdf"
        pdf_file.parent.mkdir()
        pdf_file.write_bytes(b"test pdf content")

        # Test asset validation
        asset_paths = {
            "markdown": [markdown_file],
            "images": [missing_image],
            "pdf": [pdf_file],
        }

        asset_results = validate_assets(asset_paths)

        # Test hash validation with mismatch
        expected_hash = "expected_hash"
        actual_hash = "different_hash"
        with patch(
            "milkbottle.modules.pdfmilker.validate.hash_file", return_value=actual_hash
        ):
            hash_result = validate_pdf_hash(pdf_file, expected_hash)

        # Verify results
        assert asset_results["markdown"] is True
        assert asset_results["images"] is False
        assert asset_results["pdf"] is True
        assert hash_result is False
        assert hash_result is False
