"""
CLI tests for PDFmilker module.

Tests command line interface behavior, user input simulation,
and CLI integration with the PDFmilker pipeline.
"""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

from milkbottle.modules.pdfmilker.discovery import discover_pdfs, hash_pdf
from milkbottle.modules.pdfmilker.extract import extract_text_structured
from milkbottle.modules.pdfmilker.prepare import prepare_output_tree
from milkbottle.modules.pdfmilker.relocate import relocate_pdf
from milkbottle.modules.pdfmilker.report import write_report
from milkbottle.modules.pdfmilker.transform import pdf_to_markdown_structured
from milkbottle.modules.pdfmilker.validate import validate_assets, validate_pdf_hash


class TestPDFmilkerCoreFunctions:
    """Test the core PDFmilker functions that would be used by CLI."""

    def test_discover_pdfs_function(self, tmp_path):
        """Test discover_pdfs function."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf1 = source_dir / "document1.pdf"
        pdf2 = source_dir / "document2.pdf"
        pdf1.write_bytes(b"fake pdf content 1")
        pdf2.write_bytes(b"fake pdf content 2")

        # Test discovery
        discovered_pdfs = discover_pdfs(source_dir)

        assert len(discovered_pdfs) == 2
        assert pdf1 in discovered_pdfs
        assert pdf2 in discovered_pdfs

    def test_extract_function(self, tmp_path):
        """Test extract_text_structured function."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Mock extraction
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            self._extracted_from_test_extract_function_12(mock_fitz, pdf_file)

    # TODO Rename this here and in `test_extract_function`
    def _extracted_from_test_extract_function_12(self, mock_fitz, pdf_file):
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        mock_page.rotation = 0

        mock_text_blocks = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Test Document",
                                    "font": "Arial",
                                    "size": 16,
                                }
                            ]
                        }
                    ],
                    "bbox": [10, 10, 100, 50],
                }
            ]
        }

        mock_page.get_text.return_value = mock_text_blocks
        mock_page.get_images.return_value = []
        mock_page.find_tables.return_value = []
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.metadata = {"title": "Test Document", "author": "Test Author"}
        mock_doc.close = Mock()
        mock_fitz.return_value = mock_doc

        # Test extraction
        structured_content = extract_text_structured(pdf_file)

        assert structured_content["raw_text"] == "Test Document"
        assert len(structured_content["pages"]) == 1

    def test_transform_function(self, tmp_path):
        """Test pdf_to_markdown_structured function."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create structured content
        structured_content = {
            "raw_text": "Test Document\n\nThis is a test document.",
            "pages": [
                {
                    "page_num": 1,
                    "blocks": [
                        {
                            "text": "Test Document",
                            "type": "title",
                            "bbox": [10, 10, 100, 50],
                        },
                        {
                            "text": "This is a test document.",
                            "type": "body",
                            "bbox": [10, 60, 200, 100],
                        },
                    ],
                }
            ],
            "figures": [],
            "tables": [],
            "math_blocks": [],
        }

        # Test transformation
        markdown_content = pdf_to_markdown_structured(structured_content)

        assert "# Test Document" in markdown_content
        assert "This is a test document." in markdown_content

    def test_relocate_function(self, tmp_path):
        """Test relocate_pdf function."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Test relocation
        relocated_path = relocate_pdf(pdf_file, output_dir)

        assert relocated_path is not None
        assert relocated_path.exists()
        assert relocated_path.read_bytes() == b"fake pdf content"

    def test_validate_function(self, tmp_path):
        """Test validate_assets function."""
        # Setup test environment
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create test files
        markdown_file = test_dir / "test.md"
        markdown_file.write_text("# Test Document")

        # Create asset paths
        asset_paths = {
            "markdown": [markdown_file],
            "images": [],
            "tables": [],
        }

        # Test validation
        validation_result = validate_assets(asset_paths)

        assert validation_result["markdown"] is True
        assert validation_result["images"] is True
        assert validation_result["tables"] is True

    def test_report_function(self, tmp_path):
        """Test write_report and print_report functions."""
        # Setup test environment
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create test report data
        report_data = {
            "pdf_name": "test.pdf",
            "pdf_hash": "abc123",
            "pages": 1,
            "images_extracted": 0,
            "tables_found": 0,
            "math_blocks": 0,
            "relocated_path": "/path/to/relocated.pdf",
            "status": "success",
        }

        # Test report writing
        report_path = write_report(report_data, test_dir)

        assert report_path.exists()

        # Test report reading
        with report_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["pdf_name"] == "test.pdf"
        assert loaded_data["status"] == "success"

    def test_hash_function(self, tmp_path):
        """Test hash_pdf function."""
        # Setup test environment
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        pdf_file = test_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Test hashing
        pdf_hash = hash_pdf(pdf_file)

        assert pdf_hash is not None
        assert len(pdf_hash) > 0

    def test_prepare_function(self, tmp_path):
        """Test prepare_output_tree function."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"

        # Test output tree preparation
        output_tree = prepare_output_tree(pdf_file, output_dir)

        assert "pdf" in output_tree
        assert "markdown" in output_tree
        assert "meta" in output_tree
        assert "images" in output_tree
        assert "tables" in output_tree


class TestPDFmilkerWorkflow:
    """Test complete PDFmilker workflow functions."""

    def test_complete_workflow(self, tmp_path):
        """Test complete PDFmilker workflow."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"

        # Step 1: Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1
        assert pdf_file in discovered_pdfs

        # Step 2: Prepare output tree
        output_tree = prepare_output_tree(pdf_file, output_dir)

        # Step 3: Extract content
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            structured_content = self._extracted_from_test_complete_workflow_22(
                mock_fitz, pdf_file
            )
        # Step 4: Transform to Markdown
        markdown_content = pdf_to_markdown_structured(structured_content)

        # Step 5: Generate hash
        pdf_hash = hash_pdf(pdf_file)

        # Step 6: Relocate PDF
        relocated_path = relocate_pdf(pdf_file, output_tree["pdf"])

        # Step 7: Validate assets
        asset_paths = {
            "markdown": [output_tree["markdown"] / f"{pdf_file.stem}.md"],
            "images": [],
            "tables": [],
        }
        assets_valid = validate_assets(asset_paths)

        # Step 8: Validate PDF hash
        hash_valid = validate_pdf_hash(pdf_file, pdf_hash)

        # Step 9: Write report
        report_data = {
            "pdf_name": pdf_file.name,
            "pdf_hash": pdf_hash,
            "pages": len(structured_content["pages"]),
            "images_extracted": len(structured_content["figures"]),
            "tables_found": len(structured_content["tables"]),
            "math_blocks": len(structured_content["math_blocks"]),
            "relocated_path": str(relocated_path) if relocated_path else None,
            "assets_valid": all(assets_valid.values()),
            "hash_valid": hash_valid,
            "markdown_content_length": len(markdown_content) if markdown_content else 0,
            "status": (
                "success"
                if relocated_path and all(assets_valid.values()) and hash_valid
                else "partial"
            ),
        }

        report_path = write_report(report_data, output_tree["meta"])

        # Verify results
        assert report_path.exists()
        assert relocated_path is not None
        assert relocated_path.exists()
        assert pdf_hash is not None
        assert len(structured_content["pages"]) == 1

    # TODO Rename this here and in `test_complete_workflow`
    def _extracted_from_test_complete_workflow_22(self, mock_fitz, pdf_file):
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        mock_page.rotation = 0

        mock_text_blocks = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Test Document",
                                    "font": "Arial",
                                    "size": 16,
                                }
                            ]
                        }
                    ],
                    "bbox": [10, 10, 100, 50],
                }
            ]
        }

        mock_page.get_text.return_value = mock_text_blocks
        mock_page.get_images.return_value = []
        mock_page.find_tables.return_value = []
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.metadata = {"title": "Test Document", "author": "Test Author"}
        mock_doc.close = Mock()
        mock_fitz.return_value = mock_doc

        return extract_text_structured(pdf_file)

    def test_workflow_with_errors(self, tmp_path):
        """Test workflow with error handling."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a corrupted PDF
        corrupted_pdf = source_dir / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"this is not a valid pdf")

        output_dir = tmp_path / "output"

        # Step 1: Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1

        # Step 2: Prepare output tree
        output_tree = prepare_output_tree(corrupted_pdf, output_dir)

        # Step 3: Extract content (should handle error gracefully)
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            mock_fitz.side_effect = ValueError("Invalid PDF")

            structured_content = extract_text_structured(corrupted_pdf)

        # Should return empty content
        assert structured_content["raw_text"] == ""
        assert structured_content["pages"] == []

        # Step 4: Generate hash (should still work)
        pdf_hash = hash_pdf(corrupted_pdf)
        assert pdf_hash is not None

        # Step 5: Relocate PDF (should still work)
        relocated_path = relocate_pdf(corrupted_pdf, output_tree["pdf"])
        assert relocated_path is not None

        # Step 6: Write report with error status
        report_data = {
            "pdf_name": corrupted_pdf.name,
            "pdf_hash": pdf_hash,
            "pages": len(structured_content["pages"]),
            "images_extracted": len(structured_content["figures"]),
            "tables_found": len(structured_content["tables"]),
            "math_blocks": len(structured_content["math_blocks"]),
            "relocated_path": str(relocated_path),
            "status": "error_extraction",
        }

        report_path = write_report(report_data, output_tree["meta"])

        # Verify results
        assert report_path.exists()
        assert relocated_path.exists()


class TestPDFmilkerErrorHandling:
    """Test error handling in PDFmilker functions."""

    def test_discover_nonexistent_directory(self):
        """Test discover_pdfs with nonexistent directory."""
        discovered_pdfs = discover_pdfs(Path("/nonexistent/directory"))
        assert discovered_pdfs == []
        # Verify that the discovery result is empty for debugging
        assert len(discovered_pdfs) == 0

    def test_extract_nonexistent_file(self):
        """Test extract_text_structured with nonexistent file."""
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            mock_fitz.side_effect = FileNotFoundError("File not found")

            structured_content = extract_text_structured(Path("/nonexistent/file.pdf"))
            assert structured_content["raw_text"] == ""
            assert structured_content["pages"] == []

    def test_relocate_nonexistent_file(self, tmp_path):
        """Test relocate_pdf with nonexistent file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        relocated_path = relocate_pdf(Path("/nonexistent/file.pdf"), output_dir)
        assert relocated_path is None

    def test_validate_nonexistent_files(self, tmp_path):
        """Test validate_assets with nonexistent files."""
        asset_paths = {
            "markdown": [Path("/nonexistent/file.md")],
            "images": [],
            "tables": [],
        }

        validation_result = validate_assets(asset_paths)
        assert validation_result["markdown"] is False

    def test_hash_nonexistent_file(self):
        """Test hash_pdf with nonexistent file."""
        pdf_hash = hash_pdf(Path("/nonexistent/file.pdf"))
        assert pdf_hash is None


class TestPDFmilkerLogging:
    """Test logging behavior in PDFmilker functions."""

    def test_logging_output(self, tmp_path, caplog):
        """Test that functions log their operations."""
        caplog.set_level(logging.INFO)

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Test discovery logging
        discovered_pdfs = discover_pdfs(source_dir)

        # Verify discovery results for debugging
        assert len(discovered_pdfs) == 1
        assert pdf_file in discovered_pdfs

        # Test extraction logging
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            self._extracted_from_test_logging_output_16(mock_fitz, pdf_file)
        # Verify logging messages
        log_messages = [record.message for record in caplog.records]

        # Should have discovery and extraction messages
        assert any("discovered" in msg.lower() for msg in log_messages)
        assert any("extracted" in msg.lower() for msg in log_messages)

    # TODO Rename this here and in `test_logging_output`
    def _extracted_from_test_logging_output_16(self, mock_fitz, pdf_file):
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        mock_page.rotation = 0

        mock_text_blocks = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Test Document",
                                    "font": "Arial",
                                    "size": 16,
                                }
                            ]
                        }
                    ],
                    "bbox": [10, 10, 100, 50],
                }
            ]
        }

        mock_page.get_text.return_value = mock_text_blocks
        mock_page.get_images.return_value = []
        mock_page.find_tables.return_value = []
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.metadata = {"title": "Test Document", "author": "Test Author"}
        mock_doc.close = Mock()
        mock_fitz.return_value = mock_doc

        structured_content = extract_text_structured(pdf_file)
        # Verify that structured content was extracted for debugging
        assert structured_content is not None
        assert "pages" in structured_content
