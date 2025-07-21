import logging
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger("pdfmilker.transform")


def pdf_to_markdown(text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Transform extracted PDF text and metadata into Markdown with YAML front-matter.
    Args:
        text (str): Extracted text from the PDF.
        metadata (Optional[Dict[str, Any]]): PDF metadata.
    Returns:
        str: Markdown string with YAML front-matter.
    """
    md_lines = []
    if metadata:
        try:
            yaml_front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
            md_lines.extend(("---", yaml_front.strip(), "---\n"))
        except Exception as e:
            logger.error(f"Failed to generate YAML front-matter: {e}")
    # Simple heading hierarchy: treat lines starting with numbers or ALL CAPS as headings
    for line in text.splitlines():
        if line.strip().isupper() and len(line.strip()) > 3:
            md_lines.append(f"# {line.strip()}")
        elif line.strip().startswith(
            ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")
        ):
            md_lines.append(f"## {line.strip()}")
        else:
            md_lines.append(line)
    logger.info("Transformed PDF text and metadata to Markdown.")
    return "\n".join(md_lines)
