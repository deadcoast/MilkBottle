"""Unit tests for PDFmilker discovery module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from milkbottle.modules.pdfmilker.discovery import discover_pdfs, hash_pdf


class TestDiscoverPDFs:
    """Test cases for discover_pdfs function."""

    def test_discover_pdfs_with_directory(self, tmp_path):
        """Test discovering PDFs in a specific directory."""
        # Create test directory structure
        test_dir = tmp_path / "test_pdfs"
        test_dir.mkdir()

        # Create some PDF files
        pdf1 = test_dir / "document1.pdf"
        pdf2 = test_dir / "document2.pdf"
        txt_file = test_dir / "readme.txt"

        pdf1.write_text("fake pdf content")
        pdf2.write_text("fake pdf content")
        txt_file.write_text("text content")

        # Test discovery
        result = discover_pdfs(str(test_dir))

        assert len(result) == 2
        assert pdf1 in result
        assert pdf2 in result
        assert txt_file not in result

    def test_discover_pdfs_with_nested_directories(self, tmp_path):
        """Test discovering PDFs in nested directory structure."""
        # Create nested directory structure
        root_dir = tmp_path / "root"
        sub_dir = root_dir / "subdir"
        deep_dir = sub_dir / "deep"

        root_dir.mkdir()
        sub_dir.mkdir()
        deep_dir.mkdir()

        # Create PDFs at different levels
        pdf1 = root_dir / "root.pdf"
        pdf2 = sub_dir / "sub.pdf"
        pdf3 = deep_dir / "deep.pdf"

        pdf1.write_text("fake pdf content")
        pdf2.write_text("fake pdf content")
        pdf3.write_text("fake pdf content")

        # Test discovery
        result = discover_pdfs(str(root_dir))

        assert len(result) == 3
        assert pdf1 in result
        assert pdf2 in result
        assert pdf3 in result

    def test_discover_pdfs_empty_directory(self, tmp_path):
        """Test discovering PDFs in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = discover_pdfs(str(empty_dir))

        assert len(result) == 0

    def test_discover_pdfs_no_pdfs_only_other_files(self, tmp_path):
        """Test discovering PDFs when only other file types exist."""
        test_dir = tmp_path / "no_pdfs"
        test_dir.mkdir()

        # Create non-PDF files
        txt_file = test_dir / "readme.txt"
        doc_file = test_dir / "document.doc"
        py_file = test_dir / "script.py"

        txt_file.write_text("text content")
        doc_file.write_text("doc content")
        py_file.write_text("python code")

        result = discover_pdfs(str(test_dir))

        assert len(result) == 0

    def test_discover_pdfs_default_directory(self, tmp_path):
        """Test discovering PDFs using default directory (current working directory)."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            # Create a PDF in the mocked current directory
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_text("fake pdf content")

            result = discover_pdfs()

            assert len(result) == 1
            assert pdf_file in result

    def test_discover_pdfs_case_sensitivity(self, tmp_path):
        """Test that PDF discovery is case-sensitive."""
        test_dir = tmp_path / "case_test"
        test_dir.mkdir()

        # Create files with different case extensions
        pdf_lower = test_dir / "lower.pdf"
        pdf_upper = test_dir / "upper.PDF"
        pdf_mixed = test_dir / "mixed.Pdf"

        pdf_lower.write_text("fake pdf content")
        pdf_upper.write_text("fake pdf content")
        pdf_mixed.write_text("fake pdf content")

        result = discover_pdfs(str(test_dir))

        # Should only find .pdf files (lowercase extension)
        assert len(result) == 1
        assert pdf_lower in result
        assert pdf_upper not in result
        assert pdf_mixed not in result

    def test_discover_pdfs_nonexistent_directory(self):
        """Test discovering PDFs in non-existent directory."""
        # The function should return an empty list for nonexistent directories
        result = discover_pdfs("/nonexistent/directory/path")
        assert result == []

    def test_discover_pdfs_permission_error(self, tmp_path):
        """Test discovering PDFs when permission is denied."""
        test_dir = tmp_path / "permission_test"
        test_dir.mkdir()

        # Mock rglob to raise PermissionError
        with patch(
            "pathlib.Path.rglob", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(PermissionError):
                discover_pdfs(str(test_dir))


class TestHashPDF:
    """Test cases for hash_pdf function."""

    def test_hash_pdf_valid_file(self, tmp_path):
        """Test hash computation for a valid PDF file."""
        # Create a test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_content = b"fake pdf content for hashing"
        pdf_file.write_bytes(pdf_content)

        # Mock the hash_file function to return a known hash
        expected_hash = "a1b2c3d4e5f6"
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file",
            return_value=expected_hash,
        ):
            result = hash_pdf(pdf_file)

            assert result == expected_hash

    def test_hash_pdf_nonexistent_file(self):
        """Test hash computation for non-existent file."""
        nonexistent_file = Path("/nonexistent/file.pdf")

        # Mock hash_file to return None for non-existent file
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file", return_value=None
        ):
            result = hash_pdf(nonexistent_file)

            assert result is None

    def test_hash_pdf_empty_file(self, tmp_path):
        """Test hash computation for empty PDF file."""
        empty_pdf = tmp_path / "empty.pdf"
        empty_pdf.write_bytes(b"")

        # Mock hash_file to return hash for empty file
        expected_hash = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file",
            return_value=expected_hash,
        ):
            result = hash_pdf(empty_pdf)

            assert result == expected_hash

    def test_hash_pdf_large_file(self, tmp_path):
        """Test hash computation for large PDF file."""
        large_pdf = tmp_path / "large.pdf"
        # Create a large file (1MB)
        large_content = b"x" * (1024 * 1024)
        large_pdf.write_bytes(large_content)

        # Mock hash_file to return hash for large file
        expected_hash = "large_file_hash_123"
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file",
            return_value=expected_hash,
        ):
            result = hash_pdf(large_pdf)

            assert result == expected_hash

    def test_hash_pdf_hash_file_error(self, tmp_path):
        """Test hash computation when hash_file raises an exception."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        # Mock hash_file to raise an exception
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file",
            side_effect=OSError("File read error"),
        ):
            with pytest.raises(OSError):
                hash_pdf(pdf_file)

    def test_hash_pdf_unicode_filename(self, tmp_path):
        """Test hash computation for PDF with Unicode filename."""
        unicode_pdf = tmp_path / "测试文档.pdf"
        unicode_pdf.write_text("fake pdf content")

        # Mock hash_file to return hash
        expected_hash = "unicode_file_hash_456"
        with patch(
            "milkbottle.modules.pdfmilker.discovery.hash_file",
            return_value=expected_hash,
        ):
            result = hash_pdf(unicode_pdf)

            assert result == expected_hash


class TestDiscoveryIntegration:
    """Integration tests for discovery module."""

    def test_discover_and_hash_workflow(self, tmp_path):
        """Test the complete workflow of discovering PDFs and computing hashes."""
        # Create test directory with PDFs
        test_dir = tmp_path / "workflow_test"
        test_dir.mkdir()

        pdf1 = test_dir / "doc1.pdf"
        pdf2 = test_dir / "doc2.pdf"

        pdf1.write_text("content1")
        pdf2.write_text("content2")

        # Discover PDFs
        discovered_pdfs = discover_pdfs(str(test_dir))
        assert len(discovered_pdfs) == 2

        # Compute hashes for discovered PDFs
        with patch("milkbottle.modules.pdfmilker.discovery.hash_file") as mock_hash:
            mock_hash.side_effect = ["hash1", "hash2"]

            hashes = [hash_pdf(pdf) for pdf in discovered_pdfs]

            assert hashes == ["hash1", "hash2"]
            assert mock_hash.call_count == 2

    def test_discovery_with_special_characters(self, tmp_path):
        """Test discovery with special characters in filenames."""
        test_dir = tmp_path / "special_chars"
        test_dir.mkdir()

        # Create PDFs with special characters
        special_pdfs = [
            test_dir / "file with spaces.pdf",
            test_dir / "file-with-dashes.pdf",
            test_dir / "file_with_underscores.pdf",
            test_dir / "file123.pdf",
        ]

        for pdf in special_pdfs:
            pdf.write_text("fake content")

        result = discover_pdfs(str(test_dir))

        assert len(result) == 4
        for pdf in special_pdfs:
            assert pdf in result
            assert pdf in result
