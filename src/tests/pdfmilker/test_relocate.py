"""Unit tests for PDFmilker relocate module."""

from unittest.mock import patch

from milkbottle.modules.pdfmilker.relocate import relocate_pdf


class TestRelocatePdf:
    """Test cases for relocate_pdf function."""

    def test_relocate_pdf_success(self, tmp_path):
        """Test successful PDF relocation."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result
        assert result is not None
        assert result == dest_dir / "document.pdf"
        assert result.exists()
        assert result.read_bytes() == b"test pdf content"

        # Verify source file is moved (no longer exists)
        assert not src_pdf.exists()

    def test_relocate_pdf_dry_run(self, tmp_path):
        """Test PDF relocation with dry run."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir, dry_run=True)

        # Verify result
        assert result is not None
        assert result == dest_dir / "document.pdf"

        # Verify source file still exists (not moved in dry run)
        assert src_pdf.exists()

        # Verify destination file doesn't exist (dry run)
        assert not result.exists()

    def test_relocate_pdf_overwrite_existing(self, tmp_path):
        """Test PDF relocation with overwrite of existing file."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"new pdf content")

        # Create destination directory with existing file
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)
        existing_pdf = dest_dir / "document.pdf"
        existing_pdf.write_bytes(b"old pdf content")

        result = relocate_pdf(src_pdf, dest_dir, overwrite=True)

        # Verify result
        assert result is not None
        assert result == dest_dir / "document.pdf"
        assert result.exists()
        assert result.read_bytes() == b"new pdf content"

        # Verify source file is moved
        assert not src_pdf.exists()

    def test_relocate_pdf_no_overwrite_existing(self, tmp_path):
        """Test PDF relocation without overwrite when file exists."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"new pdf content")

        # Create destination directory with existing file
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)
        existing_pdf = dest_dir / "document.pdf"
        existing_pdf.write_bytes(b"old pdf content")

        result = relocate_pdf(src_pdf, dest_dir, overwrite=False)

        # Verify result is None (no overwrite)
        assert result is None

        # Verify source file still exists
        assert src_pdf.exists()

        # Verify destination file unchanged
        assert existing_pdf.exists()
        assert existing_pdf.read_bytes() == b"old pdf content"

    def test_relocate_pdf_destination_directory_creation(self, tmp_path):
        """Test PDF relocation with destination directory creation."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Destination directory doesn't exist
        dest_dir = tmp_path / "dest" / "pdf"

        # The function doesn't create directories, so this should fail
        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result is None (error due to missing directory)
        assert result is None

    def test_relocate_pdf_nested_destination(self, tmp_path):
        """Test PDF relocation to nested destination directory."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create deeply nested destination
        dest_dir = tmp_path / "dest" / "nested" / "deep" / "pdf"

        # The function doesn't create directories, so this should fail
        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result is None (error due to missing directory)
        assert result is None

    def test_relocate_pdf_special_characters_filename(self, tmp_path):
        """Test PDF relocation with special characters in filename."""
        # Create source PDF with special characters
        src_pdf = tmp_path / "source" / "document (2024).pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result
        assert result is not None
        assert result == dest_dir / "document (2024).pdf"
        assert result.exists()

    def test_relocate_pdf_unicode_filename(self, tmp_path):
        """Test PDF relocation with Unicode characters in filename."""
        # Create source PDF with Unicode characters
        src_pdf = tmp_path / "source" / "测试文档.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result
        assert result is not None
        assert result == dest_dir / "测试文档.pdf"
        assert result.exists()

    def test_relocate_pdf_large_file(self, tmp_path):
        """Test PDF relocation with large file."""
        # Create large source PDF (1MB)
        src_pdf = tmp_path / "source" / "large.pdf"
        src_pdf.parent.mkdir()
        large_content = b"x" * (1024 * 1024)
        src_pdf.write_bytes(large_content)

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result
        assert result is not None
        assert result == dest_dir / "large.pdf"
        assert result.exists()
        assert result.read_bytes() == large_content

    def test_relocate_pdf_source_file_not_found(self, tmp_path):
        """Test PDF relocation with nonexistent source file."""
        # Source file doesn't exist
        src_pdf = tmp_path / "source" / "nonexistent.pdf"

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        result = relocate_pdf(src_pdf, dest_dir)

        # Verify result is None (error)
        assert result is None

    def test_relocate_pdf_permission_error(self, tmp_path):
        """Test PDF relocation when permission is denied."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # Mock shutil.move to raise PermissionError
        with patch(
            "milkbottle.modules.pdfmilker.relocate.shutil.move",
            side_effect=PermissionError("Permission denied"),
        ):
            result = relocate_pdf(src_pdf, dest_dir)

        # Verify result is None (error)
        assert result is None

        # Verify source file still exists
        assert src_pdf.exists()

    def test_relocate_pdf_disk_full_error(self, tmp_path):
        """Test PDF relocation when disk is full."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # Mock shutil.move to raise OSError (disk full)
        with patch(
            "milkbottle.modules.pdfmilker.relocate.shutil.move",
            side_effect=OSError("No space left on device"),
        ):
            result = relocate_pdf(src_pdf, dest_dir)

        # Verify result is None (error)
        assert result is None

        # Verify source file still exists
        assert src_pdf.exists()

    def test_relocate_pdf_dry_run_with_overwrite(self, tmp_path):
        """Test dry run with overwrite flag."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"new pdf content")

        # Create destination directory with existing file
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)
        existing_pdf = dest_dir / "document.pdf"
        existing_pdf.write_bytes(b"old pdf content")

        result = relocate_pdf(src_pdf, dest_dir, overwrite=True, dry_run=True)

        # Verify result
        assert result is not None
        assert result == dest_dir / "document.pdf"

        # Verify source file still exists (dry run)
        assert src_pdf.exists()

        # Verify destination file unchanged (dry run)
        assert existing_pdf.exists()
        assert existing_pdf.read_bytes() == b"old pdf content"

    def test_relocate_pdf_dry_run_no_overwrite_existing(self, tmp_path):
        """Test dry run without overwrite when file exists."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"new pdf content")

        # Create destination directory with existing file
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)
        existing_pdf = dest_dir / "document.pdf"
        existing_pdf.write_bytes(b"old pdf content")

        result = relocate_pdf(src_pdf, dest_dir, overwrite=False, dry_run=True)

        # Verify result is the destination path (dry run always returns the path)
        assert result == dest_dir / "document.pdf"

        # Verify source file still exists
        assert src_pdf.exists()

        # Verify destination file unchanged
        assert existing_pdf.exists()
        assert existing_pdf.read_bytes() == b"old pdf content"

    def test_relocate_pdf_multiple_files_same_name(self, tmp_path):
        """Test relocating multiple PDFs with the same name."""
        # Create multiple source PDFs with same name in different directories
        src_pdf1 = tmp_path / "source1" / "document.pdf"
        src_pdf1.parent.mkdir()
        src_pdf1.write_bytes(b"content 1")

        src_pdf2 = tmp_path / "source2" / "document.pdf"
        src_pdf2.parent.mkdir()
        src_pdf2.write_bytes(b"content 2")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # Relocate first PDF
        result1 = relocate_pdf(src_pdf1, dest_dir)
        assert result1 is not None
        assert result1.exists()
        assert result1.read_bytes() == b"content 1"

        # Relocate second PDF (should overwrite)
        result2 = relocate_pdf(src_pdf2, dest_dir, overwrite=True)
        assert result2 is not None
        assert result2.exists()
        assert result2.read_bytes() == b"content 2"

        # Verify only one file exists in destination
        assert len(list(dest_dir.glob("*.pdf"))) == 1


class TestRelocateIntegration:
    """Integration tests for relocate module."""

    def test_full_relocation_workflow(self, tmp_path):
        """Test the complete relocation workflow."""
        # Create source directory with multiple PDFs
        src_dir = tmp_path / "source"
        src_dir.mkdir()

        pdf1 = src_dir / "document1.pdf"
        pdf1.write_bytes(b"content 1")

        pdf2 = src_dir / "document2.pdf"
        pdf2.write_bytes(b"content 2")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # Relocate both PDFs
        result1 = relocate_pdf(pdf1, dest_dir)
        result2 = relocate_pdf(pdf2, dest_dir)

        # Verify results
        assert result1 is not None
        assert result2 is not None
        assert result1.exists()
        assert result2.exists()
        assert result1.read_bytes() == b"content 1"
        assert result2.read_bytes() == b"content 2"

        # Verify source files are moved
        assert not pdf1.exists()
        assert not pdf2.exists()

        # Verify destination contains both files
        dest_files = list(dest_dir.glob("*.pdf"))
        assert len(dest_files) == 2
        assert any(f.name == "document1.pdf" for f in dest_files)
        assert any(f.name == "document2.pdf" for f in dest_files)

    def test_relocation_with_validation(self, tmp_path):
        """Test relocation with file validation."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        original_content = b"test pdf content for validation"
        src_pdf.write_bytes(original_content)

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # Relocate PDF
        result = relocate_pdf(src_pdf, dest_dir)

        # Verify relocation
        assert result is not None
        assert result.exists()

        # Verify content integrity
        assert result.read_bytes() == original_content

        # Verify file size
        assert result.stat().st_size == len(original_content)

        # Verify source is moved
        assert not src_pdf.exists()

    def test_relocation_error_recovery(self, tmp_path):
        """Test relocation error recovery."""
        # Create source PDF
        src_pdf = tmp_path / "source" / "document.pdf"
        src_pdf.parent.mkdir()
        src_pdf.write_bytes(b"test pdf content")

        # Create destination directory
        dest_dir = tmp_path / "dest" / "pdf"
        dest_dir.mkdir(parents=True)

        # First attempt fails due to permission error
        with patch(
            "milkbottle.modules.pdfmilker.relocate.shutil.move",
            side_effect=PermissionError("Permission denied"),
        ):
            result1 = relocate_pdf(src_pdf, dest_dir)
            assert result1 is None
            assert src_pdf.exists()  # Source still exists

        # Second attempt succeeds
        result2 = relocate_pdf(src_pdf, dest_dir)
        assert result2 is not None
        assert result2.exists()
        assert not src_pdf.exists()  # Source is moved
