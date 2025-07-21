"""
PDFmilker text extraction module - Enhanced for scientific papers.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from .math_processor import math_processor

logger = logging.getLogger("pdfmilker.extract")


def extract_text_structured(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract structured text from a PDF file with enhanced scientific paper support.
    Args:
        pdf_path (Path): Path to the PDF file.
    Returns:
        Dict[str, Any]: Structured content including text, tables, math, and layout info.
    """
    try:
        doc = fitz.open(str(pdf_path))  # type: ignore[attr-defined]

        structured_content = {
            "pages": [],
            "tables": [],
            "math_blocks": [],
            "figures": [],
            "references": [],
            "sections": [],
            "raw_text": "",
        }

        for page_num, page in enumerate(doc, 1):
            # Get text blocks with positioning information
            text_blocks = page.get_text("dict")
            page_content = {
                "page_num": page_num,
                "text_blocks": [],
                "tables": [],
                "math_blocks": [],
                "figures": [],
                "layout": {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation,
                },
            }
            # Process text blocks for structure
            for block in text_blocks.get("blocks", []):
                if "lines" in block:  # Text block
                    block_text = ""
                    block_fonts = set()
                    block_sizes = set()

                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                            block_fonts.add(span["font"])
                            block_sizes.add(span["size"])
                        block_text += line_text + "\n"

                    # Analyze block for structure
                    block_info = {
                        "text": block_text.strip(),
                        "bbox": block["bbox"],
                        "fonts": list(block_fonts),
                        "sizes": list(block_sizes),
                        "type": _classify_text_block(
                            block_text, block_fonts, block_sizes
                        ),
                    }

                    page_content["text_blocks"].append(block_info)
                    structured_content["raw_text"] += block_text + "\n"

                    # FIXED: Use math processor for consistent math detection
                    if math_processor.is_mathematical_content(block_text):
                        math_block = {
                            "text": block_text.strip(),
                            "page": page_num,
                            "bbox": block["bbox"],
                            "type": (
                                "inline" if len(block_text.split()) < 5 else "display"
                            ),
                        }
                        page_content["math_blocks"].append(math_block)
                        structured_content["math_blocks"].append(math_block)

                    # Detect figure captions
                    if _is_figure_caption(block_text):
                        figure_info = {
                            "caption": block_text.strip(),
                            "page": page_num,
                            "bbox": block["bbox"],
                        }
                        page_content["figures"].append(figure_info)
                        structured_content["figures"].append(figure_info)

                    # Detect references
                    if _is_reference_section(block_text):
                        structured_content["references"].append(
                            {"text": block_text.strip(), "page": page_num}
                        )

            # Extract tables using PyMuPDF's table detection
            tables = _extract_tables_from_page(page)
            page_content["tables"].extend(tables)
            structured_content["tables"].extend(tables)

            structured_content["pages"].append(page_content)

        doc.close()
        logger.info("Extracted structured content from %s", pdf_path)
        return structured_content

    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to extract structured text from %s: %s", pdf_path, e)
        return {
            "raw_text": "",
            "pages": [],
            "tables": [],
            "math_blocks": [],
            "figures": [],
            "references": [],
            "sections": [],
        }


def extract_text(pdf_path: Path) -> Optional[str]:
    """
    Extract all text from a PDF file using PyMuPDF (legacy function).
    Args:
        pdf_path (Path): Path to the PDF file.
    Returns:
        Optional[str]: Extracted text, or None if error.
    """
    try:
        doc = fitz.open(str(pdf_path))  # type: ignore[attr-defined]
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        logger.info("Extracted text from %s", pdf_path)
        return text
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to extract text from %s: %s", pdf_path, e)
        return None


def extract_images(pdf_path: Path, output_dir: Path) -> List[Path]:
    """
    Extract all images from a PDF file and save them to output_dir.
    Enhanced to handle both embedded images and rendered content.
    Args:
        pdf_path (Path): Path to the PDF file.
        output_dir (Path): Directory to save images.
    Returns:
        List[Path]: List of saved image file paths.
    """
    saved_images = []
    try:
        doc = fitz.open(str(pdf_path))  # type: ignore[attr-defined]

        for page_num, page in enumerate(doc, 1):
            # Extract embedded images
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

            # Extract rendered content as images (for complex layouts)
            # This helps capture tables, charts, and complex formatting
            mat = fitz.Matrix(2, 2)  # Higher resolution
            pix = page.get_pixmap(matrix=mat)
            rendered_path = output_dir / f"page{page_num}_rendered.png"
            pix.save(str(rendered_path))
            saved_images.append(rendered_path)

        doc.close()
        logger.info("Extracted %d images from %s", len(saved_images), pdf_path)
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to extract images from %s: %s", pdf_path, e)
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
        doc = fitz.open(str(pdf_path))  # type: ignore[attr-defined]
        metadata = dict(doc.metadata)
        doc.close()
        logger.info("Extracted metadata from %s", pdf_path)
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to extract metadata from %s: %s", pdf_path, e)
    return metadata


def _classify_text_block(text: str, fonts: set, sizes: set) -> str:
    """Classify text block based on content and formatting."""
    text = text.strip()

    # Title detection
    if len(text) < 100 and any(size > 12 for size in sizes):
        return "title"

    # Heading detection
    if text.isupper() and len(text) > 3 and len(text) < 100:
        return "heading"

    # Abstract detection
    if text.lower().startswith(("abstract", "summary")):
        return "abstract"

    # Reference detection
    if re.match(r"^\[\d+\]", text):
        return "reference"

    # Figure caption detection
    if re.match(r"^fig\.?\s*\d+", text.lower()):
        return "figure_caption"

    # Table caption detection
    if re.match(r"^table\s*\d+", text.lower()):
        return "table_caption"

    # FIXED: Use math processor for consistent math detection
    return "math" if math_processor.is_mathematical_content(text) else "body"


# REMOVED: _is_math_content and _contains_real_math functions - now using math processor


def _is_figure_caption(text: str) -> bool:
    """Detect figure captions."""
    patterns = [
        r"^fig\.?\s*\d+",
        r"^figure\s*\d+",
        r"^fig\.?\s*\d+[.:]",
        r"^figure\s*\d+[.:]",
    ]
    return any(re.match(pattern, text.lower()) for pattern in patterns)


def _is_reference_section(text: str) -> bool:
    """Detect reference section content."""
    patterns = [r"^\[\d+\]", r"^references?", r"^bibliography", r"^cited\s+references"]
    return any(re.match(pattern, text.lower()) for pattern in patterns)


def _extract_tables_from_page(page) -> List[Dict[str, Any]]:
    """Extract tables from a page using PyMuPDF."""
    tables = []
    try:
        # Use PyMuPDF's table detection
        table_dict = page.find_tables()

        for table in table_dict:
            table_data = [
                [cell.strip() if cell else "" for cell in row]
                for row in table.extract()
            ]
            tables.append(
                {
                    "data": table_data,
                    "bbox": table.bbox,
                    "rows": len(table_data),
                    "cols": len(table_data[0]) if table_data else 0,
                }
            )
    except Exception as e:
        logger.warning("Table extraction failed: %s", e)

    return tables
