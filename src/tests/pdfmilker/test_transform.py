"""Unit tests for PDFmilker transform module."""

from unittest.mock import patch

from milkbottle.modules.pdfmilker.transform import (
    _is_display_math,
    _is_math_line,
    _table_to_markdown,
    pdf_to_markdown,
    pdf_to_markdown_structured,
)


class TestPdfToMarkdownStructured:
    """Test cases for pdf_to_markdown_structured function."""

    def test_pdf_to_markdown_structured_basic(self):
        """Test basic structured transformation without metadata."""
        structured_content = {
            "pages": [
                {
                    "page_num": 1,
                    "text_blocks": [
                        {
                            "text": "Sample Title",
                            "type": "title",
                            "bbox": [10, 10, 100, 50],
                        },
                        {
                            "text": "Sample content",
                            "type": "body",
                            "bbox": [10, 60, 100, 100],
                        },
                    ],
                }
            ],
            "tables": [],
            "math_blocks": [],
            "figures": [],
            "references": [],
            "raw_text": "Sample Title\nSample content",
        }

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_structured_content.return_value = (
                "# Sample Title\n\nSample content"
            )

            result = pdf_to_markdown_structured(structured_content)

        assert "# Sample Title" in result
        assert "Sample content" in result
        mock_formatter.format_structured_content.assert_called_once_with(
            structured_content
        )

    def test_pdf_to_markdown_structured_with_metadata(self):
        """Test structured transformation with metadata."""
        structured_content = {
            "pages": [],
            "tables": [],
            "math_blocks": [],
            "figures": [],
            "references": [],
            "raw_text": "",
        }

        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "subject": "Test Subject",
        }

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_structured_content.return_value = "Content"

            result = pdf_to_markdown_structured(structured_content, metadata)

        # Check for YAML front-matter
        assert result.startswith("---")
        assert result.endswith("Content")
        assert "title: Test Document" in result
        assert "author: Test Author" in result
        assert "subject: Test Subject" in result

    def test_pdf_to_markdown_structured_yaml_error(self):
        """Test structured transformation when YAML generation fails."""
        structured_content = {
            "pages": [],
            "tables": [],
            "math_blocks": [],
            "figures": [],
            "references": [],
            "raw_text": "",
        }

        # Create metadata that will cause YAML error
        metadata = {"invalid_key": object()}  # Object not serializable

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_structured_content.return_value = "Content"

            result = pdf_to_markdown_structured(structured_content, metadata)

        # Should still return content even if YAML fails
        assert "Content" in result
        assert not result.startswith("---")

    def test_pdf_to_markdown_structured_complex_content(self):
        """Test structured transformation with complex content."""
        structured_content = {
            "pages": [
                {
                    "page_num": 1,
                    "text_blocks": [
                        {
                            "text": "Research Paper Title",
                            "type": "title",
                            "bbox": [10, 10, 100, 50],
                        },
                        {
                            "text": "Abstract: This is the abstract",
                            "type": "abstract",
                            "bbox": [10, 60, 100, 100],
                        },
                        {
                            "text": "x = y + z",
                            "type": "math",
                            "bbox": [10, 110, 100, 150],
                        },
                    ],
                    "tables": [
                        {
                            "data": [["Header1", "Header2"], ["Data1", "Data2"]],
                            "bbox": [10, 160, 200, 200],
                        }
                    ],
                }
            ],
            "tables": [
                {
                    "data": [["Header1", "Header2"], ["Data1", "Data2"]],
                    "bbox": [10, 160, 200, 200],
                }
            ],
            "math_blocks": [
                {
                    "text": "x = y + z",
                    "type": "inline",
                    "page": 1,
                    "bbox": [10, 110, 100, 150],
                }
            ],
            "figures": [
                {
                    "caption": "Fig. 1: Sample figure",
                    "page": 1,
                    "bbox": [10, 210, 100, 250],
                }
            ],
            "references": [{"text": "[1] Author, Title, Journal, 2024", "page": 1}],
            "raw_text": "Research Paper Title\nAbstract: This is the abstract\nx = y + z",
        }

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_structured_content.return_value = "# Research Paper Title\n\nAbstract: This is the abstract\n\n$x = y + z$\n\n| Header1 | Header2 |\n|---------|---------|\n| Data1 | Data2 |\n\n![Fig. 1: Sample figure](images/figure1.png)\n\n## References\n\n[1] Author, Title, Journal, 2024"

            result = pdf_to_markdown_structured(structured_content)

        assert "# Research Paper Title" in result
        assert "Abstract: This is the abstract" in result
        assert "$x = y + z$" in result
        assert "| Header1 | Header2 |" in result
        assert "![Fig. 1: Sample figure]" in result
        assert "[1] Author, Title, Journal, 2024" in result


class TestPdfToMarkdown:
    """Test cases for pdf_to_markdown function."""

    def test_pdf_to_markdown_basic(self):
        """Test basic text transformation without metadata."""
        text = "Sample text content"

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_text.return_value = "Sample text content"

            result = pdf_to_markdown(text)

        assert result == "Sample text content"
        mock_formatter.format_text.assert_called_once_with(text)

    def test_pdf_to_markdown_with_metadata(self):
        """Test text transformation with metadata."""
        text = "Sample text content"
        metadata = {"title": "Test Document", "author": "Test Author"}

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_text.return_value = "Sample text content"

            result = pdf_to_markdown(text, metadata)

        # Check for YAML front-matter
        assert result.startswith("---")
        assert result.endswith("Sample text content")
        assert "title: Test Document" in result
        assert "author: Test Author" in result

    def test_pdf_to_markdown_yaml_error(self):
        """Test text transformation when YAML generation fails."""
        text = "Sample text content"
        metadata = {"invalid_key": object()}  # Object not serializable

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_text.return_value = "Sample text content"

            result = pdf_to_markdown(text, metadata)

        # Should still return content even if YAML fails
        assert result == "Sample text content"

    def test_pdf_to_markdown_complex_text(self):
        """Test text transformation with complex content."""
        text = """Title: Research Paper

Abstract: This is the abstract content.

Introduction
This is the introduction text.

x = y + z

Table 1: Sample Data
| Column1 | Column2 |
|---------|---------|
| Data1   | Data2   |

Fig. 1: Sample Figure

References
[1] Author, Title, Journal, 2024"""

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_text.return_value = """# Title: Research Paper

## Abstract
This is the abstract content.

## Introduction
This is the introduction text.

$x = y + z$

### Table 1: Sample Data
| Column1 | Column2 |
|---------|---------|
| Data1   | Data2   |

![Fig. 1: Sample Figure](images/figure1.png)

## References
[1] Author, Title, Journal, 2024"""

            result = pdf_to_markdown(text)

        assert "# Title: Research Paper" in result
        assert "## Abstract" in result
        assert "## Introduction" in result
        assert "$x = y + z$" in result
        assert "### Table 1: Sample Data" in result
        assert "![Fig. 1: Sample Figure]" in result
        assert "## References" in result


class TestTableToMarkdown:
    """Test cases for _table_to_markdown function."""

    def test_table_to_markdown_basic(self):
        """Test basic table conversion."""
        table = {
            "data": [
                ["Header1", "Header2", "Header3"],
                ["Data1", "Data2", "Data3"],
                ["Data4", "Data5", "Data6"],
            ],
            "rows": 3,
            "cols": 3,
        }

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter._table_to_markdown.return_value = [
                "| Header1 | Header2 | Header3 |",
                "|---------|---------|---------|",
                "| Data1 | Data2 | Data3 |",
                "| Data4 | Data5 | Data6 |",
            ]

            result = _table_to_markdown(table)

        assert len(result) == 4
        assert "| Header1 | Header2 | Header3 |" in result
        assert "|---------|---------|---------|" in result
        assert "| Data1 | Data2 | Data3 |" in result
        assert "| Data4 | Data5 | Data6 |" in result

    def test_table_to_markdown_empty_table(self):
        """Test table conversion with empty table."""
        table = {"data": [], "rows": 0, "cols": 0}

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter._table_to_markdown.return_value = []

            result = _table_to_markdown(table)

        assert result == []

    def test_table_to_markdown_single_row(self):
        """Test table conversion with single row."""
        table = {"data": [["Header1", "Header2"]], "rows": 1, "cols": 2}

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter._table_to_markdown.return_value = [
                "| Header1 | Header2 |",
                "|---------|---------|",
            ]

            result = _table_to_markdown(table)

        assert len(result) == 2
        assert "| Header1 | Header2 |" in result
        assert "|---------|---------|" in result

    def test_table_to_markdown_with_empty_cells(self):
        """Test table conversion with empty cells."""
        table = {
            "data": [["Header1", "", "Header3"], ["Data1", "", "Data3"]],
            "rows": 2,
            "cols": 3,
        }

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter._table_to_markdown.return_value = [
                "| Header1 | | Header3 |",
                "|---------|---------|---------|",
                "| Data1 | | Data3 |",
            ]

            result = _table_to_markdown(table)

        assert len(result) == 3
        assert "| Header1 | | Header3 |" in result
        assert "| Data1 | | Data3 |" in result


class TestIsMathLine:
    """Test cases for _is_math_line function."""

    def test_is_math_line_simple_math(self):
        """Test detection of simple mathematical content."""
        text = "x = y + z"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_math_line(text)

        assert result is True
        mock_math.is_mathematical_content.assert_called_once_with(text)

    def test_is_math_line_complex_math(self):
        """Test detection of complex mathematical content."""
        text = "\\sum_{i=1}^{n} x_i = \\frac{a + b}{c}"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_math_line(text)

        assert result is True

    def test_is_math_line_not_math(self):
        """Test detection of non-mathematical content."""
        text = "This is regular text content"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = False

            result = _is_math_line(text)

        assert result is False

    def test_is_math_line_empty(self):
        """Test detection with empty text."""
        text = ""

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = False

            result = _is_math_line(text)

        assert result is False

    def test_is_math_line_with_numbers(self):
        """Test detection with text containing numbers."""
        text = "The value is 42 and the result is 3.14"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = False

            result = _is_math_line(text)

        assert result is False


class TestIsDisplayMath:
    """Test cases for _is_display_math function."""

    def test_is_display_math_begin_end(self):
        """Test detection of display math with begin/end."""
        text = "\\begin{equation} x = y + z \\end{equation}"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is True

    def test_is_display_math_brackets(self):
        """Test detection of display math with brackets."""
        text = "\\[ x = y + z \\]"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is True

    def test_is_display_math_displaystyle(self):
        """Test detection of display math with displaystyle."""
        text = "\\displaystyle x = y + z"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is True

    def test_is_display_math_frac(self):
        """Test detection of display math with fraction."""
        text = "\\frac{a + b}{c}"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is True

    def test_is_display_math_sum(self):
        """Test detection of display math with sum."""
        text = "\\sum_{i=1}^{n} x_i"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is True

    def test_is_display_math_inline(self):
        """Test detection of inline math (should not be display)."""
        text = "x = y + z"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = True

            result = _is_display_math(text)

        assert result is False

    def test_is_display_math_not_math(self):
        """Test detection with non-mathematical content."""
        text = "This is regular text"

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = False

            result = _is_display_math(text)

        assert result is False

    def test_is_display_math_empty(self):
        """Test detection with empty text."""
        text = ""

        with patch(
            "milkbottle.modules.pdfmilker.transform.math_processor"
        ) as mock_math:
            mock_math.is_mathematical_content.return_value = False

            result = _is_display_math(text)

        assert result is False


class TestTransformIntegration:
    """Integration tests for transform module."""

    def test_full_transform_workflow(self):
        """Test the complete transformation workflow."""
        # Create complex structured content
        structured_content = {
            "pages": [
                {
                    "page_num": 1,
                    "text_blocks": [
                        {
                            "text": "Research Paper on Machine Learning",
                            "type": "title",
                            "bbox": [10, 10, 100, 50],
                        },
                        {
                            "text": "Abstract: This paper presents a novel approach to machine learning.",
                            "type": "abstract",
                            "bbox": [10, 60, 100, 100],
                        },
                        {
                            "text": "\\sum_{i=1}^{n} x_i = \\frac{a + b}{c}",
                            "type": "math",
                            "bbox": [10, 110, 100, 150],
                        },
                    ],
                    "tables": [
                        {
                            "data": [
                                ["Algorithm", "Accuracy", "Time"],
                                ["SVM", "0.95", "1.2s"],
                                ["Random Forest", "0.92", "0.8s"],
                            ],
                            "bbox": [10, 160, 200, 250],
                        }
                    ],
                }
            ],
            "tables": [
                {
                    "data": [
                        ["Algorithm", "Accuracy", "Time"],
                        ["SVM", "0.95", "1.2s"],
                        ["Random Forest", "0.92", "0.8s"],
                    ],
                    "bbox": [10, 160, 200, 250],
                }
            ],
            "math_blocks": [
                {
                    "text": "\\sum_{i=1}^{n} x_i = \\frac{a + b}{c}",
                    "type": "display",
                    "page": 1,
                    "bbox": [10, 110, 100, 150],
                }
            ],
            "figures": [
                {
                    "caption": "Fig. 1: Performance comparison",
                    "page": 1,
                    "bbox": [10, 260, 100, 300],
                }
            ],
            "references": [
                {
                    "text": "[1] Smith, J. et al. Machine Learning Advances, 2024",
                    "page": 1,
                }
            ],
            "raw_text": "Research Paper on Machine Learning\nAbstract: This paper presents a novel approach to machine learning.\n\\sum_{i=1}^{n} x_i = \\frac{a + b}{c}",
        }

        metadata = {
            "title": "Research Paper on Machine Learning",
            "author": "John Smith",
            "subject": "Machine Learning",
            "keywords": ["machine learning", "algorithms", "optimization"],
        }

        # Mock the markdown formatter
        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_structured_content.return_value = """# Research Paper on Machine Learning

## Abstract
This paper presents a novel approach to machine learning.

$$
\\sum_{i=1}^{n} x_i = \\frac{a + b}{c}
$$

| Algorithm | Accuracy | Time |
|-----------|----------|------|
| SVM | 0.95 | 1.2s |
| Random Forest | 0.92 | 0.8s |

![Fig. 1: Performance comparison](images/figure1.png)

## References
[1] Smith, J. et al. Machine Learning Advances, 2024"""

            result = pdf_to_markdown_structured(structured_content, metadata)

        # Verify YAML front-matter
        assert result.startswith("---")
        assert "title: Research Paper on Machine Learning" in result
        assert "author: John Smith" in result
        assert "subject: Machine Learning" in result
        assert "keywords:" in result

        # Verify content
        assert "# Research Paper on Machine Learning" in result
        assert "## Abstract" in result
        assert "$$" in result  # Display math
        assert "| Algorithm | Accuracy | Time |" in result
        assert "![Fig. 1: Performance comparison]" in result
        assert "## References" in result
        assert "[1] Smith, J. et al. Machine Learning Advances, 2024" in result

    def test_simple_text_transform_workflow(self):
        """Test the simple text transformation workflow."""
        text = """Title: Simple Document

This is a simple document with some content.

x = y + z

Table: Sample Data
| A | B |
|---|---|
| 1 | 2 |

References
[1] Author, Title, 2024"""

        metadata = {"title": "Simple Document", "author": "Test Author"}

        with patch(
            "milkbottle.modules.pdfmilker.transform.markdown_formatter"
        ) as mock_formatter:
            mock_formatter.format_text.return_value = """# Title: Simple Document

This is a simple document with some content.

$x = y + z$

## Table: Sample Data
| A | B |
|---|---|
| 1 | 2 |

## References
[1] Author, Title, 2024"""

            result = pdf_to_markdown(text, metadata)

        # Verify YAML front-matter
        assert result.startswith("---")
        assert "title: Simple Document" in result
        assert "author: Test Author" in result

        # Verify content
        assert "# Title: Simple Document" in result
        assert "This is a simple document with some content" in result
        assert "$x = y + z$" in result
        assert "## Table: Sample Data" in result
        assert "| A | B |" in result
        assert "## References" in result
        assert "[1] Author, Title, 2024" in result
