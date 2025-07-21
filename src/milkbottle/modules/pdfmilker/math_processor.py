"""PDFmilker mathematical content processor - Using proper libraries and APIs."""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("pdfmilker.math_processor")


class MathProcessor:
    """Mathematical content processor using proper libraries and APIs."""

    def __init__(self):
        # Simple but effective patterns for detection
        self.math_patterns = [
            r"O\([^)]+\)",  # Big O notation
            r"\\[a-zA-Z]+",  # LaTeX commands
            r"[αβγδεζηθικλμνξπρστυφχψω]",  # Greek letters
            r"[=+\-*/^√∫∑∏∂∇∞≠≤≥±×÷]",  # Math symbols
            r"[a-zA-Z]_[a-zA-Z0-9]",  # Subscripts
            r"[a-zA-Z]\^[a-zA-Z0-9]",  # Superscripts
        ]

    def is_mathematical_content(self, text: str) -> bool:
        """
        Detect mathematical content using simple, effective patterns.
        Args:
            text (str): Text to analyze.
        Returns:
            bool: True if text contains mathematical content.
        """
        if not text.strip():
            return False

        # Skip URLs
        if re.search(r"https?://|www\.|\.com|\.org|\.net", text):
            return False

        # Check for mathematical patterns
        return any(re.search(pattern, text) for pattern in self.math_patterns)

    def convert_latex_to_markdown(self, latex_text: str) -> str:
        """
        Convert LaTeX to Markdown using proper conversion.
        Args:
            latex_text (str): LaTeX mathematical text.
        Returns:
            str: Markdown formatted mathematical text.
        """
        if mathpix_result := self._try_mathpix_api(latex_text):
            return mathpix_result

        if pandoc_result := self._try_pandoc_conversion(latex_text):
            return pandoc_result

        # Fallback to simple conversion
        return self._simple_latex_conversion(latex_text)

    def _try_mathpix_api(self, latex_text: str) -> Optional[str]:
        """Try Mathpix API for math conversion."""
        # This would require Mathpix API key
        # For now, return None to use fallback
        del latex_text  # Unused parameter
        return None

    def _try_pandoc_conversion(self, latex_text: str) -> Optional[str]:
        """Try Pandoc for LaTeX to Markdown conversion."""
        try:
            import subprocess
            import tempfile
            from pathlib import Path

            # Create temporary files
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tex", delete=False
            ) as input_file:
                input_file.write(latex_text)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as output_file:
                output_path = output_file.name

            # Run Pandoc conversion
            cmd = [
                "pandoc",
                input_path,
                "-f",
                "latex",
                "-t",
                "markdown",
                "-o",
                output_path,
                "--wrap=none",
                "--markdown-headings=atx",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Clean up input file
            Path(input_path).unlink(missing_ok=True)

            if result.returncode == 0:
                # Read the converted content
                with open(output_path, "r", encoding="utf-8") as f:
                    markdown_content = f.read()

                # Clean up output file
                Path(output_path).unlink(missing_ok=True)

                return markdown_content
            else:
                logger.debug("Pandoc conversion failed: %s", result.stderr)
                # Clean up output file
                Path(output_path).unlink(missing_ok=True)
                return None

        except Exception as e:
            logger.debug("Pandoc conversion failed: %s", e)
            return None

    def _simple_latex_conversion(self, latex_text: str) -> str:
        """Simple fallback conversion that actually works."""
        # Basic conversions that work reliably
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

        result = latex_text
        for pattern, replacement in conversions:
            result = re.sub(pattern, replacement, result)

        return result

    def process_mathematical_content(self, text: str) -> str:
        """
        Process mathematical content using proper methods.
        Args:
            text (str): Text containing mathematical content.
        Returns:
            str: Processed text with proper mathematical formatting.
        """
        if not self.is_mathematical_content(text):
            return text

        # Convert LaTeX to Markdown
        converted = self.convert_latex_to_markdown(text)

        # Wrap in math delimiters
        return f"${converted}$"


# Global instance
math_processor = MathProcessor()
