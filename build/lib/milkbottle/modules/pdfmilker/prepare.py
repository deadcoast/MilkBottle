import logging
from pathlib import Path
from typing import Dict

from src.milkbottle.utils import slugify

logger = logging.getLogger("pdfmilker.prepare")


def prepare_output_tree(pdf_path: Path, outdir: Path) -> Dict[str, Path]:
    """
    Create a slugged output directory tree for a given PDF file.
    Subfolders: markdown/, images/, pdf/, meta/.
    Args:
        pdf_path (Path): Path to the source PDF file.
        outdir (Path): Root output directory.
    Returns:
        Dict[str, Path]: Mapping of subfolder names to their Path objects.
    """
    slug = slugify(pdf_path.stem)
    base = outdir.expanduser().resolve() / slug
    subdirs = {
        "markdown": base / "markdown",
        "images": base / "images",
        "pdf": base / "pdf",
        "meta": base / "meta",
    }
    try:
        for path in subdirs.values():
            path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output tree at {base}")
    except Exception as e:
        logger.error(f"Failed to create output tree for {pdf_path}: {e}")
        raise
    return subdirs
