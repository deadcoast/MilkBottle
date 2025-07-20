"""PDFmilker utils module."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("pdfmilker.utils")


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
