import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

logger = logging.getLogger("pdfmilker.extract")


def extract_text(pdf_path: Path) -> Optional[str]:
    """
    Extract all text from a PDF file using PyMuPDF.
    Args:
        pdf_path (Path): Path to the PDF file.
    Returns:
        Optional[str]: Extracted text, or None if error.
    """
    try:
        doc = fitz.open(str(pdf_path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        logger.info(f"Extracted text from {pdf_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return None


def extract_images(pdf_path: Path, output_dir: Path) -> List[Path]:
    """
    Extract all images from a PDF file and save them to output_dir.
    Args:
        pdf_path (Path): Path to the PDF file.
        output_dir (Path): Directory to save images.
    Returns:
        List[Path]: List of saved image file paths.
    """
    saved_images = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, 1):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n >= 5:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_path = output_dir / f"page{page_num}_img{img_index+1}.png"
                pix.save(str(img_path))
                saved_images.append(img_path)
                pix = None
        doc.close()
        logger.info(f"Extracted {len(saved_images)} images from {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to extract images from {pdf_path}: {e}")
    return saved_images


def extract_metadata(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file using PyMuPDF.
    Args:
        pdf_path (Path): Path to the PDF file.
    Returns:
        Dict[str, Any]: Metadata dictionary.
    """
    metadata = {}
    try:
        doc = fitz.open(str(pdf_path))
        metadata = dict(doc.metadata)
        doc.close()
        logger.info(f"Extracted metadata from {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to extract metadata from {pdf_path}: {e}")
    return metadata
