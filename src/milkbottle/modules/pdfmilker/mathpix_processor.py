"""PDFmilker Mathpix integration for mathematical content processing."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("pdfmilker.mathpix")


class MathpixProcessor:
    """Mathematical content processor using Mathpix API."""

    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.mathpix.com/v3"

        # Check if credentials are available
        if not self.app_id or not self.app_key:
            logger.warning(
                "Mathpix credentials not provided - using fallback processing"
            )
            self.available = False
        else:
            self.available = True

    def process_math_image(self, image_path: Path) -> Optional[str]:
        """
        Process mathematical content from image using Mathpix OCR.
        Args:
            image_path (Path): Path to image containing math.
        Returns:
            Optional[str]: LaTeX representation of the math, or None if failed.
        """
        if not self.available:
            return None

        try:
            headers = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "Content-type": "application/json",
            }

            data = {
                "src": f"data:image/png;base64,{self._image_to_base64(image_path)}",
                "formats": ["latex_simplified", "text"],
                "ocr_options": ["math", "text"],
            }

            response = requests.post(
                f"{self.base_url}/text", headers=headers, data=json.dumps(data)
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("latex_simplified", result.get("text", ""))
            else:
                logger.warning(f"Mathpix API failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Mathpix processing failed: {e}")
            return None

    def process_math_text(self, text: str) -> str:
        """
        Process mathematical text using Mathpix API.
        Args:
            text (str): Text containing mathematical expressions.
        Returns:
            str: Processed text with proper math formatting.
        """
        if not self.available:
            return self._fallback_math_processing(text)

        try:
            headers = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "Content-type": "application/json",
            }

            data = {
                "src": text,
                "formats": ["latex_simplified", "text"],
                "ocr_options": ["math", "text"],
            }

            response = requests.post(
                f"{self.base_url}/text", headers=headers, data=json.dumps(data)
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("latex_simplified", result.get("text", text))
            else:
                logger.warning(f"Mathpix API failed: {response.status_code}")
                return self._fallback_math_processing(text)

        except Exception as e:
            logger.error(f"Mathpix processing failed: {e}")
            return self._fallback_math_processing(text)

    def _image_to_base64(self, image_path: Path) -> str:
        """Convert image to base64 string."""
        import base64

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _fallback_math_processing(self, text: str) -> str:
        """Fallback math processing when Mathpix is not available."""
        # Simple but effective fallback
        import re

        # Basic LaTeX to Markdown conversions
        conversions = [
            (r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
            (r"\\sum", "∑"),
            (r"\\int", "∫"),
            (r"\\alpha", "α"),
            (r"\\beta", "β"),
            (r"\\gamma", "γ"),
            (r"\\delta", "δ"),
            (r"\\theta", "θ"),
            (r"\\lambda", "λ"),
            (r"\\pi", "π"),
            (r"\\sigma", "σ"),
            (r"\\phi", "φ"),
            (r"\\omega", "ω"),
            (r"\\infty", "∞"),
            (r"\\leq", "≤"),
            (r"\\geq", "≥"),
            (r"\\neq", "≠"),
        ]

        result = text
        for pattern, replacement in conversions:
            result = re.sub(pattern, replacement, result)

        return result

    def extract_math_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract mathematical content from PDF using Mathpix.
        Args:
            pdf_path (Path): Path to PDF file.
        Returns:
            List[Dict[str, Any]]: List of mathematical expressions found.
        """
        if not self.available:
            logger.warning("Mathpix not available - cannot extract math from PDF")
            return []

        try:
            headers = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "Content-type": "application/json",
            }

            data = {
                "src": f"data:application/pdf;base64,{self._pdf_to_base64(pdf_path)}",
                "formats": ["latex_simplified", "text"],
                "ocr_options": ["math", "text"],
                "math_inline_delimiters": ["$", "$"],
                "math_display_delimiters": ["$$", "$$"],
            }

            response = requests.post(
                f"{self.base_url}/pdf", headers=headers, data=json.dumps(data)
            )

            if response.status_code == 200:
                result = response.json()
                return self._parse_mathpix_pdf_result(result)
            else:
                logger.warning(f"Mathpix PDF processing failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Mathpix PDF extraction failed: {e}")
            return []

    def _pdf_to_base64(self, pdf_path: Path) -> str:
        """Convert PDF to base64 string."""
        import base64

        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode("utf-8")

    def _parse_mathpix_pdf_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Mathpix PDF processing result."""
        math_expressions = []

        try:
            # Extract math expressions from the result
            if "latex_simplified" in result:
                latex_content = result["latex_simplified"]
                # Parse the LaTeX content to extract individual expressions
                # This is a simplified parser - Mathpix provides more detailed structure
                expressions = self._extract_latex_expressions(latex_content)
                for i, expr in enumerate(expressions):
                    math_expressions.append(
                        {
                            "id": f"math_{i}",
                            "type": "inline" if "$" in expr else "display",
                            "content": expr,
                            "latex": expr,
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to parse Mathpix result: {e}")

        return math_expressions

    def _extract_latex_expressions(self, latex_content: str) -> List[str]:
        """Extract individual LaTeX expressions from content."""
        import re

        # Simple extraction of math expressions
        expressions = []

        # Find inline math
        inline_pattern = r"\$([^$]+)\$"
        expressions.extend(re.findall(inline_pattern, latex_content))

        # Find display math
        display_pattern = r"\$\$([^$]+)\$\$"
        expressions.extend(re.findall(display_pattern, latex_content))

        return expressions


# Global instance (requires credentials to be set)
mathpix_processor = MathpixProcessor()
