import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pdfmilker.relocate")


def relocate_pdf(
    src_pdf: Path, dest_dir: Path, overwrite: bool = False, dry_run: bool = False
) -> Optional[Path]:
    """
    Move the source PDF to the target /pdf directory.
    Args:
        src_pdf (Path): Path to the source PDF file.
        dest_dir (Path): Target directory (should be the /pdf subfolder).
        overwrite (bool): Overwrite if file exists.
        dry_run (bool): If True, do not actually move the file.
    Returns:
        Optional[Path]: Path to the relocated PDF, or None if error.
    """
    dest_pdf = dest_dir / src_pdf.name
    try:
        if dry_run:
            logger.info(f"[DRY RUN] Would move {src_pdf} to {dest_pdf}")
            return dest_pdf
        if dest_pdf.exists():
            if overwrite:
                dest_pdf.unlink()
                logger.info(f"Overwriting existing file: {dest_pdf}")
            else:
                logger.warning(
                    f"File already exists and overwrite is False: {dest_pdf}"
                )
                return None
        shutil.move(str(src_pdf), str(dest_pdf))
        logger.info(f"Moved {src_pdf} to {dest_pdf}")
        return dest_pdf
    except Exception as e:
        logger.error(f"Failed to relocate {src_pdf} to {dest_pdf}: {e}")
        return None
