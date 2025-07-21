"""PDFmilker Pandoc integration for LaTeX to Markdown conversion."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("pdfmilker.pandoc")


class PandocConverter:
    """LaTeX to Markdown converter using Pandoc."""

    def __init__(self):
        self.available = self._check_pandoc_availability()

    def _check_pandoc_availability(self) -> bool:
        """Check if Pandoc is available on the system."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Pandoc is available")
                return True
            else:
                logger.warning("Pandoc is not available")
                return False
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            logger.warning("Pandoc is not available")
            return False

    def convert_latex_to_markdown(self, latex_content: str) -> str:
        """
        Convert LaTeX content to Markdown using Pandoc.
        Args:
            latex_content (str): LaTeX content to convert.
        Returns:
            str: Markdown content.
        """
        if not self.available:
            logger.warning("Pandoc not available - using fallback conversion")
            return self._fallback_latex_conversion(latex_content)

        try:
            return self._extracted_from_convert_latex_to_markdown_(latex_content)
        except Exception as e:
            logger.error(f"Pandoc conversion failed: {e}")
            return self._fallback_latex_conversion(latex_content)

    # TODO Rename this here and in `convert_latex_to_markdown`
    def _extracted_from_convert_latex_to_markdown_(self, latex_content):
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as input_file:
            input_file.write(latex_content)
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
            return self._extracted_from_convert_pdf_to_markdown_47(output_path)
        logger.warning(f"Pandoc conversion failed: {result.stderr}")
        # Clean up output file
        Path(output_path).unlink(missing_ok=True)
        return self._fallback_latex_conversion(latex_content)

    def convert_pdf_to_markdown(self, pdf_path: Path) -> str:
        """
        Convert PDF to Markdown using Pandoc.
        Args:
            pdf_path (Path): Path to PDF file.
        Returns:
            str: Markdown content.
        """
        if not self.available:
            logger.warning("Pandoc not available - cannot convert PDF")
            return ""

        try:
            return self._extracted_from_convert_pdf_to_markdown_(pdf_path)
        except Exception as e:
            logger.error(f"Pandoc PDF conversion failed: {e}")
            return ""

    # TODO Rename this here and in `convert_pdf_to_markdown`
    def _extracted_from_convert_pdf_to_markdown_(self, pdf_path):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as output_file:
            output_path = output_file.name

        # Run Pandoc conversion
        cmd = [
            "pandoc",
            str(pdf_path),
            "-f",
            "pdf",
            "-t",
            "markdown",
            "-o",
            output_path,
            "--wrap=none",
            "--markdown-headings=atx",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            return self._extracted_from_convert_pdf_to_markdown_47(output_path)
        logger.warning(f"Pandoc PDF conversion failed: {result.stderr}")
        # Clean up output file
        Path(output_path).unlink(missing_ok=True)
        return ""

    # TODO Rename this here and in `convert_latex_to_markdown` and `convert_pdf_to_markdown`
    def _extracted_from_convert_pdf_to_markdown_47(self, output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        Path(output_path).unlink(missing_ok=True)
        return markdown_content

    def _fallback_latex_conversion(self, latex_content: str) -> str:
        """Fallback LaTeX to Markdown conversion when Pandoc is not available."""
        import re

        # Basic LaTeX to Markdown conversions
        conversions = [
            # Fractions
            (r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
            (r"\\dfrac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
            (r"\\tfrac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
            # Greek letters
            (r"\\alpha", "α"),
            (r"\\beta", "β"),
            (r"\\gamma", "γ"),
            (r"\\delta", "δ"),
            (r"\\epsilon", "ε"),
            (r"\\zeta", "ζ"),
            (r"\\eta", "η"),
            (r"\\theta", "θ"),
            (r"\\iota", "ι"),
            (r"\\kappa", "κ"),
            (r"\\lambda", "λ"),
            (r"\\mu", "μ"),
            (r"\\nu", "ν"),
            (r"\\xi", "ξ"),
            (r"\\pi", "π"),
            (r"\\rho", "ρ"),
            (r"\\sigma", "σ"),
            (r"\\tau", "τ"),
            (r"\\upsilon", "υ"),
            (r"\\phi", "φ"),
            (r"\\chi", "χ"),
            (r"\\psi", "ψ"),
            (r"\\omega", "ω"),
            # Mathematical symbols
            (r"\\sum", "∑"),
            (r"\\int", "∫"),
            (r"\\prod", "∏"),
            (r"\\infty", "∞"),
            (r"\\partial", "∂"),
            (r"\\nabla", "∇"),
            (r"\\leq", "≤"),
            (r"\\geq", "≥"),
            (r"\\neq", "≠"),
            (r"\\approx", "≈"),
            (r"\\equiv", "≡"),
            (r"\\propto", "∝"),
            (r"\\pm", "±"),
            (r"\\mp", "∓"),
            (r"\\times", "×"),
            (r"\\div", "÷"),
            (r"\\cdot", "·"),
            (r"\\circ", "∘"),
            (r"\\bullet", "•"),
            # Functions
            (r"\\sin", "sin"),
            (r"\\cos", "cos"),
            (r"\\tan", "tan"),
            (r"\\log", "log"),
            (r"\\ln", "ln"),
            (r"\\exp", "exp"),
            (r"\\sqrt", "√"),
            # Remove LaTeX environments
            (r"\\begin\{[^{}]*\}|\\end\{[^{}]*\}", ""),
            (r"\\\[|\\\]", ""),
        ]

        result = latex_content
        for pattern, replacement in conversions:
            result = re.sub(pattern, replacement, result)

        # Handle subscripts and superscripts
        result = re.sub(r"([a-zA-Z])_([a-zA-Z0-9])", r"\1<sub>\2</sub>", result)
        result = re.sub(r"([a-zA-Z])\^([a-zA-Z0-9])", r"\1<sup>\2</sup>", result)

        # Handle braced subscripts and superscripts
        result = re.sub(r"([a-zA-Z])_\{([^{}]*)\}", r"\1<sub>\2</sub>", result)
        result = re.sub(r"([a-zA-Z])\^\{([^{}]*)\}", r"\1<sup>\2</sup>", result)

        return result

    def convert_math_expression(self, math_expr: str) -> str:
        """
        Convert a single mathematical expression to Markdown.
        Args:
            math_expr (str): Mathematical expression in LaTeX.
        Returns:
            str: Markdown formatted mathematical expression.
        """
        if not self.available:
            return self._fallback_latex_conversion(math_expr)

        # Wrap in math delimiters for Pandoc
        wrapped_expr = f"$${math_expr}$$"
        converted = self.convert_latex_to_markdown(wrapped_expr)

        # Remove the wrapper and clean up
        converted = converted.replace("$$", "").strip()
        return converted


# Global instance
pandoc_converter = PandocConverter()
