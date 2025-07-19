"""PDFmilker validate module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from milkbottle.utils import hash_file

logger = logging.getLogger("pdfmilker.validate")


def validate_assets(asset_paths: Dict[str, List[Path]]) -> Dict[str, bool]:
    """
    Validate the existence of expected output files for a PDF bundle.
    Args:
        asset_paths (Dict[str, List[Path]]): Mapping of asset type to list of file paths.
    Returns:
        Dict[str, bool]: Mapping of asset type to validation result (True if all exist).
    """
    results = {}
    for asset_type, paths in asset_paths.items():
        results[asset_type] = all(p.exists() for p in paths)
        logger.info("Validation for %s: %s", asset_type, results[asset_type])
    return results


def validate_pdf_hash(pdf_path: Path, expected_hash: str) -> bool:
    """
    Validate that the hash of a PDF matches the expected value.
    Args:
        pdf_path (Path): Path to the PDF file.
        expected_hash (str): Expected SHA256 hash.
    Returns:
        bool: True if hash matches, False otherwise.
    """
    actual_hash = hash_file(str(pdf_path))
    match = actual_hash == expected_hash
    logger.info("Hash validation for %s: %s", pdf_path, match)
    return match
