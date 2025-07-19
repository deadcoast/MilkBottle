"""PDFmilker discovery module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from milkbottle.utils import hash_file

logger = logging.getLogger("pdfmilker.discovery")


def discover_pdfs(directory: Optional[str] = None) -> List[Path]:
    """
    Recursively discover all PDF files in the given directory.
    Args:
        directory (Optional[str]): Directory to search. Defaults to current working directory.
    Returns:
        List[Path]: List of PDF file paths found.
    """
    if directory is None:
        directory = str(Path.cwd())
    root = Path(directory)
    pdfs = [p for p in root.rglob("*.pdf") if p.is_file()]
    logger.info("Discovered %d PDF(s) in %s", len(pdfs), directory)
    return pdfs


def hash_pdf(pdf_path: Path) -> Optional[str]:
    """
    Compute the SHA256 hash of a PDF file.
    Args:
        pdf_path (Path): Path to the PDF file.
    Returns:
        Optional[str]: SHA256 hex digest, or None if error.
    """
    return hash_file(str(pdf_path))
