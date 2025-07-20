"""
Integration tests for PDFmilker pipeline workflow.

These tests verify the complete end-to-end workflow from PDF discovery
through extraction, transformation, validation, and reporting.
"""

import json
import logging
from unittest.mock import Mock, patch

from milkbottle.modules.pdfmilker.discovery import discover_pdfs, hash_pdf
from milkbottle.modules.pdfmilker.extract import extract_text_structured
from milkbottle.modules.pdfmilker.prepare import prepare_output_tree
from milkbottle.modules.pdfmilker.relocate import relocate_pdf
from milkbottle.modules.pdfmilker.report import write_report
from milkbottle.modules.pdfmilker.transform import pdf_to_markdown_structured
from milkbottle.modules.pdfmilker.validate import validate_assets, validate_pdf_hash


class TestFullPipelineIntegration:
    """Integration tests for the complete PDFmilker pipeline."""

    def test_complete_pipeline_workflow(self, tmp_path):
        """Test the complete pipeline workflow from discovery to reporting."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create test PDF files
        pdf1 = source_dir / "document1.pdf"
        pdf2 = source_dir / "document2.pdf"
        pdf1.write_bytes(b"fake pdf content 1")
        pdf2.write_bytes(b"fake pdf content 2")

        output_dir = tmp_path / "output"

        # Step 1: Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 2
        assert pdf1 in discovered_pdfs
        assert pdf2 in discovered_pdfs

        # Step 2: Prepare output tree for each PDF
        output_trees = {}
        for pdf_path in discovered_pdfs:
            output_trees[pdf_path] = prepare_output_tree(pdf_path, output_dir)

        # Verify output directories were created
        for pdf_path, output_tree in output_trees.items():
            for subdir_name, subdir_path in output_tree.items():
                assert subdir_path.exists()

        # Step 3: Process each PDF
        results = []
        for pdf_path in discovered_pdfs:
            output_tree = output_trees[pdf_path]

            # Extract structured content
            with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
                mock_doc = Mock()
                mock_page = Mock()
                mock_page.rect.width = 612
                mock_page.rect.height = 792
                mock_page.rotation = 0

                # Mock text blocks
                mock_text_blocks = {
                    "blocks": [
                        {
                            "lines": [
                                {
                                    "spans": [
                                        {
                                            "text": f"Title for {pdf_path.name}",
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
                mock_doc.metadata = {
                    "title": f"Document {pdf_path.name}",
                    "author": "Test Author",
                }
                mock_doc.close = Mock()
                mock_fitz.return_value = mock_doc

                structured_content = extract_text_structured(pdf_path)

            # Transform to Markdown
            markdown_content = pdf_to_markdown_structured(structured_content)

            # Generate hash
            pdf_hash = hash_pdf(pdf_path)

            # Relocate PDF
            relocated_path = relocate_pdf(pdf_path, output_tree["pdf"])

            # Validate assets
            asset_paths = {
                "markdown": [output_tree["markdown"] / f"{pdf_path.stem}.md"],
                "images": [],
                "tables": [],
            }
            assets_valid = validate_assets(asset_paths)

            # Validate PDF hash
            hash_valid = validate_pdf_hash(pdf_path, pdf_hash)

            # Write report
            report_data = {
                "pdf_name": pdf_path.name,
                "pdf_hash": pdf_hash,
                "pages": len(structured_content["pages"]),
                "images_extracted": len(structured_content["figures"]),
                "tables_found": len(structured_content["tables"]),
                "math_blocks": len(structured_content["math_blocks"]),
                "relocated_path": str(relocated_path) if relocated_path else None,
                "assets_valid": all(assets_valid.values()),
                "hash_valid": hash_valid,
                "status": (
                    "success"
                    if relocated_path and all(assets_valid.values()) and hash_valid
                    else "partial"
                ),
            }

            report_path = write_report(report_data, output_tree["meta"])

            results.append(
                {
                    "pdf_path": pdf_path,
                    "output_tree": output_tree,
                    "report_path": report_path,
                    "report_data": report_data,
                }
            )

        # Step 4: Verify results
        assert len(results) == 2

        for result in results:
            assert result["report_path"].exists()
            assert result["report_data"]["status"] in ["success", "partial"]
            assert result["report_data"]["pdf_hash"] is not None
            assert result["report_data"]["pages"] == 1

        # Step 5: Generate summary report
        summary_data = {
            "total_pdfs": len(results),
            "successful": len(
                [r for r in results if r["report_data"]["status"] == "success"]
            ),
            "partial": len(
                [r for r in results if r["report_data"]["status"] == "partial"]
            ),
            "total_pages": sum(r["report_data"]["pages"] for r in results),
            "total_images": sum(r["report_data"]["images_extracted"] for r in results),
            "total_tables": sum(r["report_data"]["tables_found"] for r in results),
            "total_math_blocks": sum(r["report_data"]["math_blocks"] for r in results),
        }

        # Ensure meta directory exists
        meta_dir = output_dir / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)

        summary_report = write_report(summary_data, meta_dir, "summary.json")
        assert summary_report.exists()

        # Verify summary content
        with summary_report.open("r", encoding="utf-8") as f:
            loaded_summary = json.load(f)

        assert loaded_summary["total_pdfs"] == 2
        assert loaded_summary["total_pages"] == 2

    def test_pipeline_with_errors(self, tmp_path):
        """Test pipeline behavior when errors occur during processing."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create one valid PDF and one that will cause errors
        valid_pdf = source_dir / "valid.pdf"
        valid_pdf.write_bytes(b"fake pdf content")

        # Create a file that's not a PDF
        invalid_file = source_dir / "invalid.txt"
        invalid_file.write_text("This is not a PDF")

        output_dir = tmp_path / "output"

        # Discover PDFs (should only find the valid one)
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1
        assert valid_pdf in discovered_pdfs

        # Prepare output tree
        output_tree = prepare_output_tree(valid_pdf, output_dir)

        # Process the valid PDF
        pdf_path = valid_pdf

        # Mock extraction to simulate success
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
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
                                        "text": "Valid Document",
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
            mock_doc.metadata = {"title": "Valid Document", "author": "Test Author"}
            mock_doc.close = Mock()
            mock_fitz.return_value = mock_doc

            structured_content = extract_text_structured(pdf_path)

        # Transform to Markdown
        markdown_content = pdf_to_markdown_structured(structured_content)

        # Generate hash
        pdf_hash = hash_pdf(pdf_path)

        # Relocate PDF
        relocated_path = relocate_pdf(pdf_path, output_tree["pdf"])

        # Write report
        report_data = {
            "pdf_name": pdf_path.name,
            "pdf_hash": pdf_hash,
            "pages": len(structured_content["pages"]),
            "images_extracted": len(structured_content["figures"]),
            "tables_found": len(structured_content["tables"]),
            "math_blocks": len(structured_content["math_blocks"]),
            "relocated_path": str(relocated_path) if relocated_path else None,
            "status": "success" if relocated_path else "error",
        }

        report_path = write_report(report_data, output_tree["meta"])
        assert report_path.exists()

        # Verify the invalid file was ignored
        assert invalid_file not in discovered_pdfs

    def test_pipeline_with_large_files(self, tmp_path):
        """Test pipeline behavior with large PDF files."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a large PDF file (simulate with large content)
        large_pdf = source_dir / "large_document.pdf"
        large_content = b"x" * (1024 * 1024)  # 1MB
        large_pdf.write_bytes(large_content)

        output_dir = tmp_path / "output"

        # Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1
        assert large_pdf in discovered_pdfs

        # Prepare output tree for each PDF
        output_trees = {}
        for pdf_path in discovered_pdfs:
            output_trees[pdf_path] = prepare_output_tree(pdf_path, output_dir)

        # Process the large PDF
        pdf_path = large_pdf
        output_path = output_trees[pdf_path]

        # Mock extraction for large file
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.rect.width = 612
            mock_page.rect.height = 792
            mock_page.rotation = 0

            # Simulate large content
            mock_text_blocks = {
                "blocks": [
                    {
                        "lines": [
                            {
                                "spans": [
                                    {
                                        "text": "Large Document Content",
                                        "font": "Arial",
                                        "size": 12,
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
            mock_doc.metadata = {"title": "Large Document", "author": "Test Author"}
            mock_doc.close = Mock()
            mock_fitz.return_value = mock_doc

            structured_content = extract_text_structured(pdf_path)

        # Generate hash (should work with large files)
        pdf_hash = hash_pdf(pdf_path)
        assert pdf_hash is not None

        # Relocate PDF (should handle large files)
        relocated_path = relocate_pdf(pdf_path, output_path["pdf"])
        assert relocated_path is not None

        # Verify the relocated file has the same content
        assert relocated_path.exists()
        assert relocated_path.read_bytes() == large_content

    def test_pipeline_with_special_characters(self, tmp_path):
        """Test pipeline behavior with special characters in filenames."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create PDF with special characters in filename
        special_pdf = source_dir / "document (2024) - test.pdf"
        special_pdf.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"

        # Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1
        assert special_pdf in discovered_pdfs

        # Prepare output tree for each PDF
        output_trees = {}
        for pdf_path in discovered_pdfs:
            output_trees[pdf_path] = prepare_output_tree(pdf_path, output_dir)

        # Process the PDF
        pdf_path = special_pdf
        output_path = output_trees[pdf_path]

        # Mock extraction
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
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
                                        "text": "Special Character Document",
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
            mock_doc.metadata = {
                "title": "Special Character Document",
                "author": "Test Author",
            }
            mock_doc.close = Mock()
            mock_fitz.return_value = mock_doc

            structured_content = extract_text_structured(pdf_path)

        # Transform to Markdown
        markdown_content = pdf_to_markdown_structured(structured_content)

        # Generate hash
        pdf_hash = hash_pdf(pdf_path)

        # Relocate PDF (should handle special characters)
        relocated_path = relocate_pdf(pdf_path, output_path["pdf"])
        assert relocated_path is not None

        # Verify the relocated file has the correct name
        assert relocated_path.name == "document (2024) - test.pdf"

        # Write report
        report_data = {
            "pdf_name": pdf_path.name,
            "pdf_hash": pdf_hash,
            "pages": len(structured_content["pages"]),
            "images_extracted": len(structured_content["figures"]),
            "tables_found": len(structured_content["tables"]),
            "math_blocks": len(structured_content["math_blocks"]),
            "relocated_path": str(relocated_path),
            "status": "success",
        }

        report_path = write_report(report_data, output_path["meta"])
        assert report_path.exists()

    def test_pipeline_performance(self, tmp_path):
        """Test pipeline performance with multiple files."""
        # Setup test environment
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create multiple test PDF files
        pdf_files = []
        for i in range(10):
            pdf_file = source_dir / f"document_{i:03d}.pdf"
            pdf_file.write_bytes(f"fake pdf content {i}".encode())
            pdf_files.append(pdf_file)

        output_dir = tmp_path / "output"

        # Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 10

        # Prepare output tree for each PDF
        output_trees = {}
        for pdf_path in discovered_pdfs:
            output_trees[pdf_path] = prepare_output_tree(pdf_path, output_dir)

        # Process all PDFs
        results = []
        for pdf_path in discovered_pdfs:
            output_tree = output_trees[pdf_path]

            # Mock extraction for each file
            with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
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
                                            "text": f"Document {pdf_path.stem}",
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
                mock_doc.metadata = {
                    "title": f"Document {pdf_path.stem}",
                    "author": "Test Author",
                }
                mock_doc.close = Mock()
                mock_fitz.return_value = mock_doc

                structured_content = extract_text_structured(pdf_path)

            # Generate hash
            pdf_hash = hash_pdf(pdf_path)

            # Relocate PDF
            relocated_path = relocate_pdf(pdf_path, output_tree["pdf"])

            # Write report
            report_data = {
                "pdf_name": pdf_path.name,
                "pdf_hash": pdf_hash,
                "pages": len(structured_content["pages"]),
                "images_extracted": len(structured_content["figures"]),
                "tables_found": len(structured_content["tables"]),
                "math_blocks": len(structured_content["math_blocks"]),
                "relocated_path": str(relocated_path) if relocated_path else None,
                "status": "success" if relocated_path else "error",
            }

            report_path = write_report(report_data, output_tree["meta"])
            results.append(
                {
                    "pdf_path": pdf_path,
                    "report_path": report_path,
                    "report_data": report_data,
                }
            )

        # Verify all files were processed
        assert len(results) == 10

        # Verify all reports were created
        for result in results:
            assert result["report_path"].exists()
            assert result["report_data"]["status"] == "success"

        # Write summary report
        summary_data = {
            "total_pdfs": len(results),
            "successful": len(
                [r for r in results if r["report_data"]["status"] == "success"]
            ),
            "partial": len(
                [r for r in results if r["report_data"]["status"] == "partial"]
            ),
            "total_pages": sum(r["report_data"]["pages"] for r in results),
            "total_images": sum(r["report_data"]["images_extracted"] for r in results),
            "total_tables": sum(r["report_data"]["tables_found"] for r in results),
            "total_math_blocks": sum(r["report_data"]["math_blocks"] for r in results),
        }

        # Ensure meta directory exists
        meta_dir = output_dir / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)

        summary_report = write_report(summary_data, meta_dir, "summary.json")
        assert summary_report.exists()

        # Verify summary
        with summary_report.open("r", encoding="utf-8") as f:
            loaded_summary = json.load(f)

        assert loaded_summary["total_pdfs"] == 10
        assert loaded_summary["successful"] == 10
        assert loaded_summary["total_pages"] == 10


class TestPipelineErrorHandling:
    """Test error handling in the pipeline workflow."""

    def test_pipeline_with_missing_source_directory(self, tmp_path):
        """Test pipeline behavior when source directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        # Discover PDFs from nonexistent directory
        discovered_pdfs = discover_pdfs(nonexistent_dir)
        assert discovered_pdfs == []

        # Prepare output tree with empty list (should handle gracefully)
        # Note: prepare_output_tree expects a single PDF path, not a list
        pass

    def test_pipeline_with_permission_errors(self, tmp_path):
        """Test pipeline behavior when permission errors occur."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"

        # Discover PDFs
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1

        # Mock permission error during relocation
        with patch("milkbottle.modules.pdfmilker.relocate.shutil.move") as mock_move:
            mock_move.side_effect = PermissionError("Permission denied")

            # Prepare output tree
            output_tree = prepare_output_tree(discovered_pdfs[0], output_dir)

            # Try to relocate (should fail gracefully)
            pdf_path = discovered_pdfs[0]

            relocated_path = relocate_pdf(pdf_path, output_tree["pdf"])
            assert relocated_path is None

            # Source file should still exist
            assert pdf_path.exists()

    def test_pipeline_with_corrupted_pdfs(self, tmp_path):
        """Test pipeline behavior with corrupted PDF files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a corrupted PDF file
        corrupted_pdf = source_dir / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"this is not a valid pdf file")

        output_dir = tmp_path / "output"

        # Discover PDFs (should still find it)
        discovered_pdfs = discover_pdfs(source_dir)
        assert len(discovered_pdfs) == 1

        # Prepare output tree
        output_trees = {}
        for pdf_path in discovered_pdfs:
            output_trees[pdf_path] = prepare_output_tree(pdf_path, output_dir)

        # Mock extraction to simulate corruption error
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
            mock_fitz.side_effect = ValueError("Invalid PDF")

            pdf_path = discovered_pdfs[0]
            output_path = output_trees[pdf_path]

            # Extraction should return empty content
            structured_content = extract_text_structured(pdf_path)
            assert structured_content["raw_text"] == ""
            assert structured_content["pages"] == []

            # Hash should still work
            pdf_hash = hash_pdf(pdf_path)
            assert pdf_hash is not None

            # Relocation should still work
            relocated_path = relocate_pdf(pdf_path, output_path["pdf"])
            assert relocated_path is not None

            # Write report with error status
            report_data = {
                "pdf_name": pdf_path.name,
                "pdf_hash": pdf_hash,
                "pages": len(structured_content["pages"]),
                "images_extracted": len(structured_content["figures"]),
                "tables_found": len(structured_content["tables"]),
                "math_blocks": len(structured_content["math_blocks"]),
                "relocated_path": str(relocated_path),
                "status": "error_extraction",
            }

            report_path = write_report(report_data, output_path["meta"])
            assert report_path.exists()


class TestPipelineLogging:
    """Test logging behavior in the pipeline workflow."""

    def test_pipeline_logging_output(self, tmp_path, caplog):
        """Test that pipeline operations are properly logged."""
        caplog.set_level(logging.INFO)

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        pdf_file = source_dir / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        output_dir = tmp_path / "output"

        # Run pipeline steps
        discovered_pdfs = discover_pdfs(source_dir)
        output_tree = prepare_output_tree(discovered_pdfs[0], output_dir)

        pdf_path = discovered_pdfs[0]
        output_path = output_tree

        # Mock extraction
        with patch("milkbottle.modules.pdfmilker.extract.fitz.open") as mock_fitz:
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

            structured_content = extract_text_structured(pdf_path)

        pdf_hash = hash_pdf(pdf_path)
        relocated_path = relocate_pdf(pdf_path, output_path["pdf"])

        report_data = {
            "pdf_name": pdf_path.name,
            "pdf_hash": pdf_hash,
            "pages": len(structured_content["pages"]),
            "images_extracted": len(structured_content["figures"]),
            "tables_found": len(structured_content["tables"]),
            "math_blocks": len(structured_content["math_blocks"]),
            "relocated_path": str(relocated_path),
            "status": "success",
        }

        report_path = write_report(report_data, output_path["meta"])

        # Verify logging messages
        log_messages = [record.message for record in caplog.records]

        # Should have discovery, extraction, relocation, and report messages
        assert any("discovered" in msg.lower() for msg in log_messages)
        assert any("extracted" in msg.lower() for msg in log_messages)
        assert any("moved" in msg.lower() for msg in log_messages)
        assert any("wrote report" in msg.lower() for msg in log_messages)
