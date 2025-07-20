"""PDFmilker extraction pipeline - Using proper libraries for scientific papers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Removed circular import - BatchProcessor will be instantiated when needed
from .errors import PDFMilkerError
from .format_exporter import FormatExporter
from .grobid_extractor import grobid_extractor
from .image_processor import image_processor
from .mathpix_processor import mathpix_processor
from .pandoc_converter import pandoc_converter
from .quality_assessor import quality_assessor
from .table_processor import table_processor

logger = logging.getLogger("pdfmilker.pipeline")


class PDFmilkerPipeline:
    """Enhanced PDF extraction pipeline using proper libraries."""

    def __init__(self):
        self.grobid_extractor = grobid_extractor
        self.mathpix_processor = mathpix_processor
        self.pandoc_converter = pandoc_converter
        self.format_exporter = FormatExporter()
        self.quality_assessor = quality_assessor
        self.image_processor = image_processor
        self.table_processor = table_processor
        # Initialize batch processor lazily to avoid circular imports
        self._batch_processor = None

    @property
    def batch_processor(self):
        """Get batch processor instance, creating it if needed."""
        if self._batch_processor is None:
            from .batch_processor import BatchProcessor

            self._batch_processor = BatchProcessor()
        return self._batch_processor

    def process_pdf(
        self, pdf_path: Path, output_dir: Path, format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Process a single PDF file with enhanced features.

        Args:
            pdf_path: Path to input PDF file
            output_dir: Directory for output files
            format_type: Output format (markdown, html, latex, json, docx)

        Returns:
            Dict containing processing results and metadata
        """
        try:
            logger.info("Processing PDF: %s", pdf_path)

            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Process the PDF using scientific paper extraction
            result = self.process_scientific_paper(pdf_path, output_dir / "temp.md")

            # Load the extracted content
            if result.get("success"):
                extracted_content = self._load_extracted_content(result["output_path"])

                # Add metadata
                extracted_content.update(
                    {
                        "pdf_path": str(pdf_path),
                        "extraction_method": result.get("method", "unknown"),
                        "content_length": result.get("content_length", 0),
                    }
                )

                # Export to requested format
                output_file = output_dir / f"{pdf_path.stem}.{format_type}"
                export_result = self.format_exporter.export_to_format(
                    extracted_content, format_type, output_file
                )

                # Clean up temporary file
                if result["output_path"].exists():
                    result["output_path"].unlink()

                return {
                    "success": True,
                    "output_file": output_file,
                    "extracted_content": extracted_content,
                    "export_result": export_result,
                }
            else:
                raise PDFMilkerError("PDF processing failed")

        except Exception as e:
            logger.error("PDF processing failed: %s", e)
            raise PDFMilkerError(f"Failed to process PDF: {e}") from e

    def process_pdf_fallback(
        self, pdf_path: Path, output_dir: Path, format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Fallback PDF processing when primary method fails.

        Args:
            pdf_path: Path to input PDF file
            output_dir: Directory for output files
            format_type: Output format

        Returns:
            Dict containing processing results and metadata
        """
        try:
            logger.info("Using fallback processing for: %s", pdf_path)

            # Use basic extraction as fallback
            result = self._fallback_extraction(pdf_path, output_dir / "temp.md")

            if result.get("success"):
                extracted_content = self._load_extracted_content(result["output_path"])

                # Add metadata
                extracted_content.update(
                    {
                        "pdf_path": str(pdf_path),
                        "extraction_method": "fallback",
                        "content_length": result.get("content_length", 0),
                    }
                )

                # Export to requested format
                output_file = output_dir / f"{pdf_path.stem}_fallback.{format_type}"
                export_result = self.format_exporter.export_to_format(
                    extracted_content, format_type, output_file
                )

                # Clean up temporary file
                if result["output_path"].exists():
                    result["output_path"].unlink()

                return {
                    "success": True,
                    "output_file": output_file,
                    "extracted_content": extracted_content,
                    "export_result": export_result,
                }
            else:
                raise PDFMilkerError("Fallback processing failed")

        except Exception as e:
            logger.error("Fallback processing failed: %s", e)
            raise PDFMilkerError(f"Fallback processing failed: {e}") from e

    def _load_extracted_content(self, markdown_path: Path) -> Dict[str, Any]:
        """Load extracted content from markdown file."""
        try:
            content = markdown_path.read_text(encoding="utf-8")

            # Parse the markdown content into structured format
            return self._parse_markdown_content(content)

        except Exception as e:
            logger.error("Failed to load extracted content: %s", e)
            return {"body_text": "", "title": "", "abstract": ""}

    def _parse_markdown_content(self, content: str) -> Dict[str, Any]:
        """Parse markdown content into structured format."""
        lines = content.split("\n")
        result = {
            "title": "",
            "abstract": "",
            "body_text": "",
            "math_formulas": [],
            "tables": [],
            "references": [],
        }

        current_section = "body_text"
        section_content = []

        for line in lines:
            line = line.strip()

            if line.startswith("# "):
                if not result["title"]:
                    result["title"] = line[2:]
                current_section = "body_text"
                section_content = []
            elif line.startswith("## Abstract"):
                current_section = "abstract"
                section_content = []
            elif line.startswith("## Content"):
                current_section = "body_text"
                section_content = []
            elif line.startswith("## Mathematical Formulas"):
                current_section = "math_formulas"
                section_content = []
            elif line.startswith("## Tables"):
                current_section = "tables"
                section_content = []
            elif line.startswith("## References"):
                current_section = "references"
                section_content = []
            elif line.startswith("$$") and line.endswith("$$"):
                # Math formula
                formula_content = line[2:-2]
                result["math_formulas"].append(
                    {"content": formula_content, "type": "latex"}
                )
            elif line.startswith("- ") and current_section == "references":
                # Reference
                result["references"].append({"raw": line[2:], "type": "bibliography"})
            elif line:
                section_content.append(line)

            # Update current section content
            if current_section in ["abstract", "body_text"]:
                result[current_section] = "\n".join(section_content)

        return result

    def process_scientific_paper(
        self, pdf_path: Path, output_path: Path
    ) -> Dict[str, Any]:
        """
        Process scientific paper using proper libraries.
        Args:
            pdf_path (Path): Path to input PDF.
            output_path (Path): Path for output Markdown.
        Returns:
            Dict[str, Any]: Processing results and metadata.
        """
        try:
            logger.info("Processing scientific paper: %s", pdf_path)

            # Step 1: Extract using Grobid (best for scientific papers)
            grobid_result = self.grobid_extractor.extract_scientific_paper(pdf_path)

            if grobid_result and grobid_result.get("body_text"):
                logger.info("Using Grobid extraction results")
                return self._process_grobid_result(grobid_result, output_path)

            # Step 2: Fallback to Pandoc for basic conversion
            logger.info("Grobid extraction failed, trying Pandoc")
            pandoc_result = self.pandoc_converter.convert_pdf_to_markdown(pdf_path)

            if pandoc_result:
                logger.info("Using Pandoc conversion results")
                return self._process_pandoc_result(pandoc_result, output_path)

            # Step 3: Final fallback to basic extraction
            logger.warning("Both Grobid and Pandoc failed, using basic extraction")
            return self._fallback_extraction(pdf_path, output_path)

        except Exception as e:
            logger.error("Pipeline processing failed: %s", e)
            raise PDFMilkerError(f"Failed to process PDF: {e}") from e

    def _process_grobid_result(
        self, grobid_result: Dict[str, Any], output_path: Path
    ) -> Dict[str, Any]:
        """Process Grobid extraction results."""
        try:
            # Combine all text content
            content_parts = []

            # Add title
            if grobid_result.get("title"):
                content_parts.append(f"# {grobid_result['title']}\n")

            # Add abstract
            if grobid_result.get("abstract"):
                content_parts.append(f"## Abstract\n\n{grobid_result['abstract']}\n")

            # Add body text
            if grobid_result.get("body_text"):
                content_parts.append(f"## Content\n\n{grobid_result['body_text']}\n")

            # Process mathematical formulas
            if grobid_result.get("math_formulas"):
                content_parts.append("## Mathematical Formulas\n")
                for formula in grobid_result["math_formulas"]:
                    latex_content = formula.get("content", "")
                    if latex_content:
                        # Use Mathpix for math processing if available
                        processed_math = self.mathpix_processor.process_math_text(
                            latex_content
                        )
                        content_parts.append(f"$${processed_math}$$\n")

            # Process tables
            if grobid_result.get("tables"):
                content_parts.append("## Tables\n")
                for table in grobid_result["tables"]:
                    table_md = self._convert_table_to_markdown(table)
                    content_parts.append(table_md + "\n")

            # Process references
            if grobid_result.get("references"):
                content_parts.append("## References\n")
                for ref in grobid_result["references"]:
                    ref_text = ref.get("raw", "")
                    if ref_text:
                        content_parts.append(f"- {ref_text}\n")

            # Combine all content
            final_content = "\n".join(content_parts)

            # Write to output file
            output_path.write_text(final_content, encoding="utf-8")

            return {
                "success": True,
                "method": "grobid",
                "output_path": output_path,
                "content_length": len(final_content),
                "math_formulas_count": len(grobid_result.get("math_formulas", [])),
                "tables_count": len(grobid_result.get("tables", [])),
                "references_count": len(grobid_result.get("references", [])),
            }

        except Exception as e:
            logger.error("Failed to process Grobid result: %s", e)
            raise PDFMilkerError(f"Failed to process Grobid result: {e}") from e

    def _process_pandoc_result(
        self, pandoc_result: str, output_path: Path
    ) -> Dict[str, Any]:
        """Process Pandoc conversion results."""
        try:
            # Write Pandoc result directly
            output_path.write_text(pandoc_result, encoding="utf-8")

            return {
                "success": True,
                "method": "pandoc",
                "output_path": output_path,
                "content_length": len(pandoc_result),
            }

        except Exception as e:
            logger.error("Failed to process Pandoc result: %s", e)
            raise PDFMilkerError(f"Failed to process Pandoc result: {e}") from e

    def _fallback_extraction(self, pdf_path: Path, output_path: Path) -> Dict[str, Any]:
        """Enhanced fallback extraction with better math processing."""
        try:
            # Use basic PyMuPDF extraction as last resort
            import fitz

            doc = fitz.open(str(pdf_path))
            content_parts = []
            math_expressions = []
            table_count = 0

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract text with better formatting
                text = page.get_text("text")
                if text.strip():
                    # Process mathematical content
                    processed_text = self._enhance_math_content(text)
                    content_parts.append(processed_text)

                    # Extract math expressions
                    page_math = self._extract_math_from_text(text)
                    math_expressions.extend(page_math)

                # Try to extract tables
                tables = page.get_text("dict")
                if "blocks" in tables:
                    for block in tables["blocks"]:
                        if block.get("type") == 1:  # Table
                            table_md = self._extract_table_from_block(block)
                            if table_md:
                                content_parts.append(table_md)
                                table_count += 1

            doc.close()

            # Combine all content with proper structure
            final_content = self._structure_fallback_content(
                content_parts, math_expressions
            )
            output_path.write_text(final_content, encoding="utf-8")

            return {
                "success": True,
                "method": "enhanced_fallback",
                "output_path": output_path,
                "content_length": len(final_content),
                "math_expressions_count": len(math_expressions),
                "tables_count": table_count,
            }

        except Exception as e:
            logger.error("Enhanced fallback extraction failed: %s", e)
            raise PDFMilkerError(f"All extraction methods failed: {e}") from e

    def _enhance_math_content(self, text: str) -> str:
        """Enhance mathematical content in text with proper Markdown formatting."""
        import re

        processed_text = text

        # Simple, safe math patterns without complex regex
        replacements = [
            # Big O notation
            ("O(n log2 n)", "$O(n \\log_2 n)$"),
            ("O(n log n)", "$O(n \\log n)$"),
            ("O(n)", "$O(n)$"),
            # Greek letters
            ("alpha", "$\\alpha$"),
            ("beta", "$\\beta$"),
            ("gamma", "$\\gamma$"),
            ("delta", "$\\delta$"),
            ("theta", "$\\theta$"),
            ("lambda", "$\\lambda$"),
            ("pi", "$\\pi$"),
            ("sigma", "$\\sigma$"),
            ("phi", "$\\phi$"),
            ("omega", "$\\omega$"),
            # Mathematical symbols
            ("infty", "$\\infty$"),
            ("infinity", "$\\infty$"),
            ("leq", "$\\leq$"),
            ("geq", "$\\geq$"),
            ("neq", "$\\neq$"),
            ("approx", "$\\approx$"),
            ("sum", "$\\sum$"),
            ("int", "$\\int$"),
            ("prod", "$\\prod$"),
            ("partial", "$\\partial$"),
            ("nabla", "$\\nabla$"),
            # Fractions (simple cases)
            ("1/2", "$\\frac{1}{2}$"),
            ("1/3", "$\\frac{1}{3}$"),
            ("1/4", "$\\frac{1}{4}$"),
            ("2/3", "$\\frac{2}{3}$"),
            ("3/4", "$\\frac{3}{4}$"),
        ]

        # Apply simple replacements
        for old, new in replacements:
            processed_text = processed_text.replace(old, new)

        # Handle inline math expressions (already formatted)
        processed_text = re.sub(r"\$([^$]+)\$", r"$\1$", processed_text)

        # Handle display math blocks
        processed_text = re.sub(r"\\\[([^\]]+)\\\]", r"$$\1$$", processed_text)

        return processed_text

    def _extract_math_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract mathematical expressions from text."""
        import re

        math_expressions = []

        # Find mathematical patterns
        patterns = [
            r"\$([^$]+)\$",  # Inline math
            r"\$\$([^$]+)\$\$",  # Display math
            r"\\\[([^\]]+)\\\]",  # Display math brackets
            r"\bO\([^)]+\)",  # Big O notation
            r"\b[αβγδεζηθικλμνξπρστυφχψω]\b",  # Greek letters
            r"\b(infty|leq|geq|neq|approx|sum|int|prod|partial|nabla)\b",  # Math symbols
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                math_expressions.append(
                    {
                        "content": match.group(0),
                        "type": "inline" if "$" in match.group(0) else "symbol",
                        "position": match.start(),
                    }
                )

        return math_expressions

    def _extract_table_from_block(self, block: Dict[str, Any]) -> Optional[str]:
        """Extract table from PyMuPDF block."""
        try:
            if "lines" not in block:
                return None

            table_data = []
            for line in block["lines"]:
                row = []
                for span in line.get("spans", []):
                    row.append(span.get("text", "").strip())
                if row:
                    table_data.append(row)

            if len(table_data) < 2:
                return None

            return self._convert_table_to_markdown({"rows": table_data})

        except Exception as e:
            logger.debug("Failed to extract table: %s", e)
            return None

    def _structure_fallback_content(
        self, content_parts: List[str], math_expressions: List[Dict[str, Any]]
    ) -> str:
        """Structure the fallback content with proper Markdown formatting."""
        structured_parts = []

        # Add header
        structured_parts.append("# Extracted Scientific Paper\n")

        # Add math summary if found
        if math_expressions:
            structured_parts.append("## Mathematical Expressions Found\n")
            for expr in math_expressions[:10]:  # Limit to first 10
                structured_parts.append(f"- `{expr['content']}`")
            structured_parts.append("")

        # Add main content
        structured_parts.append("## Content\n")
        structured_parts.extend(content_parts)

        return "\n".join(structured_parts)

    def _convert_table_to_markdown(self, table: Dict[str, Any]) -> str:
        """Convert table data to Markdown format."""
        try:
            rows = table.get("rows", [])
            if not rows:
                return ""

            # Create header
            headers = table.get("headers", rows[0] if rows else [])
            markdown_lines = []

            # Add header row
            markdown_lines.append("| " + " | ".join(headers) + " |")
            markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

            # Add data rows
            data_rows = table.get("data", rows[1:] if len(rows) > 1 else [])
            for row in data_rows:
                markdown_lines.append("| " + " | ".join(row) + " |")

            return "\n".join(markdown_lines)

        except Exception as e:
            logger.warning("Failed to convert table to Markdown: %s", e)
            return ""

    def extract_math_only(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract only mathematical content from PDF.
        Args:
            pdf_path (Path): Path to PDF file.
        Returns:
            List[Dict[str, Any]]: List of mathematical expressions.
        """
        try:
            # Try Mathpix first for math extraction
            math_expressions = self.mathpix_processor.extract_math_from_pdf(pdf_path)

            if math_expressions:
                logger.info(
                    "Extracted %d math expressions using Mathpix", len(math_expressions)
                )
                return math_expressions

            # Fallback to Grobid for math extraction
            grobid_result = self.grobid_extractor.extract_scientific_paper(pdf_path)
            if grobid_result and grobid_result.get("math_formulas"):
                logger.info(
                    "Extracted %d math expressions using Grobid",
                    len(grobid_result["math_formulas"]),
                )
                return grobid_result["math_formulas"]

            logger.warning("No mathematical content found")
            return []

        except Exception as e:
            logger.error("Math extraction failed: %s", e)
            return []


# Global instance
pipeline = PDFmilkerPipeline()
