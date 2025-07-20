"""PDFmilker transform module - Enhanced for scientific papers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import yaml

from .markdown_formatter import markdown_formatter
from .math_processor import math_processor

logger = logging.getLogger("pdfmilker.transform")


def pdf_to_markdown_structured(
    structured_content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Transform structured PDF content into enhanced Markdown with scientific paper support.
    Uses enhanced math processor and markdown formatter for high accuracy.
    Args:
        structured_content (Dict[str, Any]): Structured content from extract_text_structured.
        metadata (Optional[Dict[str, Any]]): PDF metadata.
    Returns:
        str: Enhanced Markdown string with proper formatting.
    """
    md_lines = []

    # YAML front-matter
    if metadata:
        try:
            yaml_front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
            md_lines.extend(("---", yaml_front.strip(), "---\n"))
        except Exception as e:
            logger.error("Failed to generate YAML front-matter: %s", e)

    # Use the enhanced markdown formatter for structured content
    formatted_content = markdown_formatter.format_structured_content(structured_content)
    md_lines.append(formatted_content)

    logger.info("Transformed structured PDF content to enhanced Markdown.")
    return "\n".join(md_lines)


def pdf_to_markdown(text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Transform extracted PDF text and metadata into Markdown with YAML front-matter.
    Enhanced version with better scientific paper support using new processors.
    Args:
        text (str): Extracted text from the PDF.
        metadata (Optional[Dict[str, Any]]): PDF metadata.
    Returns:
        str: Markdown string with YAML front-matter.
    """
    md_lines = []

    # YAML front-matter
    if metadata:
        try:
            yaml_front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
            md_lines.extend(("---", yaml_front.strip(), "---\n"))
        except Exception as e:
            logger.error("Failed to generate YAML front-matter: %s", e)

    # Use the enhanced markdown formatter for better formatting
    formatted_text = markdown_formatter.format_text(text)
    md_lines.append(formatted_text)

    logger.info("Transformed PDF text and metadata to enhanced Markdown.")
    return "\n".join(md_lines)


def _table_to_markdown(table: Dict[str, Any]) -> List[str]:
    """Convert table data to Markdown table format."""
    return markdown_formatter._table_to_markdown(table)


def _is_math_line(text: str) -> bool:
    """Detect if a line contains mathematical content."""
    return math_processor.is_mathematical_content(text)


def _is_display_math(text: str) -> bool:
    """Detect if math should be displayed as a block."""
    # Simple heuristic: if line contains complex math, treat as display
    if math_processor.is_mathematical_content(text):
        # Check for display math indicators
        display_indicators = [
            r"^\\begin\{",
            r"\\end\{.*\}$",
            r"^\\\[",
            r"\\\]$",
            r"^\\displaystyle",
            r"^\\frac\{",
            r"^\\sum_",
            r"^\\int_",
            r"^\\prod_",
        ]
        import re

        return any(re.search(pattern, text) for pattern in display_indicators)
    return False
