"""Unit tests for PDFmilker report module."""

import json
from unittest.mock import Mock, patch

from milkbottle.modules.pdfmilker.report import print_report, write_report


class TestWriteReport:
    """Test cases for write_report function."""

    def test_write_report_success(self, tmp_path):
        """Test successful report writing."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {
            "pdf_name": "test.pdf",
            "pages": 5,
            "images_extracted": 3,
            "tables_found": 2,
            "math_blocks": 1,
            "status": "success",
        }

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result == meta_dir / "report.json"
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data

    def test_write_report_custom_filename(self, tmp_path):
        """Test report writing with custom filename."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {"pdf_name": "test.pdf", "status": "success"}

        result = write_report(report_data, meta_dir, "custom_report.json")

        # Verify result
        assert result == meta_dir / "custom_report.json"
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data

    def test_write_report_complex_data(self, tmp_path):
        """Test report writing with complex nested data."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {
            "pdf_name": "research_paper.pdf",
            "metadata": {
                "title": "Research Paper",
                "author": "John Smith",
                "year": 2024,
            },
            "extraction_results": {
                "pages": 10,
                "images": [
                    {"page": 1, "filename": "figure1.png"},
                    {"page": 3, "filename": "figure2.png"},
                ],
                "tables": [
                    {"page": 2, "rows": 5, "cols": 3},
                    {"page": 4, "rows": 3, "cols": 2},
                ],
                "math_blocks": [
                    {"page": 1, "type": "inline", "content": "x = y + z"},
                    {"page": 5, "type": "display", "content": "\\sum_{i=1}^{n} x_i"},
                ],
            },
            "processing_time": 45.2,
            "status": "success",
            "errors": [],
        }

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data
        assert loaded_data["extraction_results"]["pages"] == 10
        assert len(loaded_data["extraction_results"]["images"]) == 2
        assert len(loaded_data["extraction_results"]["tables"]) == 2
        assert len(loaded_data["extraction_results"]["math_blocks"]) == 2

    def test_write_report_empty_data(self, tmp_path):
        """Test report writing with empty data."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {}

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == {}

    def test_write_report_unicode_content(self, tmp_path):
        """Test report writing with Unicode content."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {
            "pdf_name": "测试文档.pdf",
            "title": "研究论文标题",
            "author": "张三",
            "status": "success",
        }

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data
        assert loaded_data["pdf_name"] == "测试文档.pdf"
        assert loaded_data["title"] == "研究论文标题"
        assert loaded_data["author"] == "张三"

    def test_write_report_nonexistent_directory(self, tmp_path):
        """Test report writing to nonexistent directory."""
        meta_dir = tmp_path / "nonexistent" / "meta"

        report_data = {"pdf_name": "test.pdf", "status": "success"}

        result = write_report(report_data, meta_dir)

        # Verify result is returned even if directory doesn't exist
        assert result == meta_dir / "report.json"

        # Directory should not exist since the function doesn't create it
        assert not meta_dir.exists()

    def test_write_report_permission_error(self, tmp_path):
        """Test report writing when permission is denied."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {"pdf_name": "test.pdf", "status": "success"}

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = write_report(report_data, meta_dir)

        # Should still return the path even if writing fails
        assert result == meta_dir / "report.json"

    def test_write_report_disk_full_error(self, tmp_path):
        """Test report writing when disk is full."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {"pdf_name": "test.pdf", "status": "success"}

        # Mock open to raise OSError (disk full)
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            result = write_report(report_data, meta_dir)

        # Should still return the path even if writing fails
        assert result == meta_dir / "report.json"

    def test_write_report_large_data(self, tmp_path):
        """Test report writing with large data."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        # Create large report data
        large_text = "x" * 10000
        report_data = {
            "pdf_name": "large_document.pdf",
            "content": large_text,
            "pages": 100,
            "images_extracted": 50,
            "tables_found": 25,
            "math_blocks": 30,
            "status": "success",
        }

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result.exists()

        # Verify file size is reasonable
        file_size = result.stat().st_size
        assert file_size > 0

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data
        assert loaded_data["content"] == large_text

    def test_write_report_special_characters(self, tmp_path):
        """Test report writing with special characters in data."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {
            "pdf_name": "document (2024).pdf",
            "title": "Research Paper: A Novel Approach",
            "description": "This paper presents a novel approach to solving complex problems.",
            "keywords": ["machine learning", "AI", "optimization"],
            "status": "success",
        }

        result = write_report(report_data, meta_dir)

        # Verify result
        assert result.exists()

        # Verify content
        with result.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data
        assert loaded_data["pdf_name"] == "document (2024).pdf"
        assert loaded_data["title"] == "Research Paper: A Novel Approach"


class TestPrintReport:
    """Test cases for print_report function."""

    def test_print_report_basic(self):
        """Test basic report printing."""
        report_data = {
            "pdf_name": "test.pdf",
            "pages": 5,
            "images_extracted": 3,
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify console and table were created
                mock_console_class.assert_called_once()
                mock_table_class.assert_called_once_with(
                    title="PDFmilker Extraction Report", show_lines=True
                )

                # Verify table columns were added
                assert mock_table.add_column.call_count == 2

                # Verify table rows were added
                assert mock_table.add_row.call_count == 4

                # Verify table was printed
                mock_console.print.assert_called_once_with(mock_table)

    def test_print_report_complex_data(self):
        """Test report printing with complex data."""
        report_data = {
            "pdf_name": "research_paper.pdf",
            "metadata": {"title": "Research Paper", "author": "John Smith"},
            "extraction_results": {"pages": 10, "images": 5, "tables": 3},
            "processing_time": 45.2,
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table rows were added for each key-value pair
                assert mock_table.add_row.call_count == 5

    def test_print_report_empty_data(self):
        """Test report printing with empty data."""
        report_data = {}

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table was created but no rows added
                mock_table_class.assert_called_once()
                assert mock_table.add_row.call_count == 0
                mock_console.print.assert_called_once_with(mock_table)

    def test_print_report_unicode_content(self):
        """Test report printing with Unicode content."""
        report_data = {
            "pdf_name": "测试文档.pdf",
            "title": "研究论文标题",
            "author": "张三",
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table rows were added
                assert mock_table.add_row.call_count == 4
                mock_console.print.assert_called_once_with(mock_table)

    def test_print_report_nested_objects(self):
        """Test report printing with nested objects."""
        report_data = {
            "pdf_name": "test.pdf",
            "metadata": {"title": "Test Document", "author": "Test Author"},
            "results": {"pages": 5, "images": 3},
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table rows were added (nested objects will be converted to strings)
                assert mock_table.add_row.call_count == 4
                mock_console.print.assert_called_once_with(mock_table)

    def test_print_report_large_data(self):
        """Test report printing with large data."""
        # Create large report data
        report_data = {
            "pdf_name": "large_document.pdf",
            "content": "x" * 1000,  # Large content
            "pages": 100,
            "images_extracted": 50,
            "tables_found": 25,
            "math_blocks": 30,
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table rows were added
                assert mock_table.add_row.call_count == 7
                mock_console.print.assert_called_once_with(mock_table)

    def test_print_report_special_characters(self):
        """Test report printing with special characters."""
        report_data = {
            "pdf_name": "document (2024).pdf",
            "title": "Research Paper: A Novel Approach",
            "description": "This paper presents a novel approach to solving complex problems.",
            "status": "success",
        }

        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table rows were added
                assert mock_table.add_row.call_count == 4
                mock_console.print.assert_called_once_with(mock_table)


class TestReportIntegration:
    """Integration tests for report module."""

    def test_full_report_workflow(self, tmp_path):
        """Test the complete report workflow."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        # Create comprehensive report data
        report_data = {
            "pdf_name": "research_paper.pdf",
            "metadata": {
                "title": "Research Paper on Machine Learning",
                "author": "John Smith",
                "year": 2024,
                "subject": "Machine Learning",
            },
            "extraction_results": {
                "pages": 15,
                "images_extracted": 8,
                "tables_found": 5,
                "math_blocks": 12,
                "figures": 6,
                "references": 25,
            },
            "processing_time": 67.3,
            "file_size": "2.5 MB",
            "status": "success",
            "errors": [],
            "warnings": ["Low resolution image on page 3"],
        }

        # Write report
        report_path = write_report(report_data, meta_dir)
        assert report_path.exists()

        # Verify written content
        with report_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data

        # Test printing report
        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table was created and printed
                mock_table_class.assert_called_once()
                mock_console.print.assert_called_once_with(mock_table)

    def test_report_with_errors(self, tmp_path):
        """Test report workflow with errors."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        report_data = {
            "pdf_name": "corrupted.pdf",
            "status": "error",
            "errors": [
                "Failed to extract text from page 3",
                "Image extraction failed for page 5",
                "Table detection failed",
            ],
            "pages_processed": 2,
            "processing_time": 12.5,
        }

        # Write report
        report_path = write_report(report_data, meta_dir)
        assert report_path.exists()

        # Verify written content
        with report_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == report_data
        assert loaded_data["status"] == "error"
        assert len(loaded_data["errors"]) == 3

        # Test printing report
        with patch("milkbottle.modules.pdfmilker.report.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with patch("milkbottle.modules.pdfmilker.report.Table") as mock_table_class:
                mock_table = Mock()
                mock_table_class.return_value = mock_table

                print_report(report_data)

                # Verify table was created and printed
                mock_table_class.assert_called_once()
                mock_console.print.assert_called_once_with(mock_table)

    def test_multiple_reports(self, tmp_path):
        """Test creating multiple reports."""
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()

        # Create multiple reports
        reports = []
        for i in range(3):
            report_data = {
                "pdf_name": f"document{i}.pdf",
                "pages": 5 + i,
                "status": "success",
                "processing_time": 10.0 + i,
            }

            report_path = write_report(report_data, meta_dir, f"report{i}.json")
            reports.append(report_path)

        # Verify all reports exist
        for report_path in reports:
            assert report_path.exists()

            with report_path.open("r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            assert loaded_data["status"] == "success"

        # Verify different filenames
        assert len(set(r.name for r in reports)) == 3
