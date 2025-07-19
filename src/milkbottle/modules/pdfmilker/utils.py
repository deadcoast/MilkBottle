"""PDFmilker utils module."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("pdfmilker.utils")


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes as a human-readable string.
    Args:
        size_bytes (int): File size in bytes.
    Returns:
        str: Human-readable file size.
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def is_pdf_file(path: Path) -> bool:
    """
    Check if a file is a valid PDF by extension and magic number.
    Args:
        path (Path): Path to the file.
    Returns:
        bool: True if file is a PDF, False otherwise.
    """
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return False
    try:
        with path.open("rb") as f:
            header = f.read(5)
            return header == b"%PDF-"
    except Exception as e:
        logger.error("Failed to check PDF magic number for %s: %s", path, e)
        return False
