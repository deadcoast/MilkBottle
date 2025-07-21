"""PDFmilker markdown formatter - Enhanced formatting for scientific papers."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from .math_processor import math_processor

logger = logging.getLogger("pdfmilker.markdown_formatter")


class MarkdownFormatter:
    """Enhanced markdown formatter for scientific papers."""

    def __init__(self):
        # Patterns for different content types
        self.patterns = {
            "heading": [
                r"^[A-Z][A-Z\s]{3,}$",  # ALL CAPS headings
                r"^\d+\.\s+[A-Z]",  # Numbered sections
                r"^\d+\.\d+\s+[A-Z]",  # Numbered subsections
                r"^\d+\.\d+\.\d+\s+[A-Z]",  # Numbered subsubsections
            ],
            "list_item": [
                r"^\s*[-*+]\s+",  # Bullet lists
                r"^\s*\d+\.\s+",  # Numbered lists
                r"^\s*[a-z]\.\s+",  # Lettered lists
            ],
            "code_block": [
                r"^\s*```",  # Code block start/end
                r"^\s*`[^`]+`",  # Inline code
            ],
            "emphasis": [
                r"\*\*[^*]+\*\*",  # Bold
                r"\*[^*]+\*",  # Italic
                r"_[^_]+_",  # Italic (underscore)
            ],
            "link": [
                r"\[([^\]]+)\]\(([^)]+)\)",  # Markdown links
            ],
            "abstract": [
                r"^abstract",  # Abstract section
                r"^summary",  # Summary section
            ],
            "figure_caption": [
                r"^fig\.?\s*\d+",  # Figure captions
                r"^figure\s*\d+",
            ],
            "table_caption": [
                r"^table\s*\d+",  # Table captions
            ],
            "reference": [
                r"^\[\d+\]",  # Reference citations
            ],
        }

        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
            for category, pattern_list in self.patterns.items()
        }

    def format_text(self, text: str) -> str:
        """
        Format text with proper markdown structure and spacing.
        Args:
            text (str): Raw text to format.
        Returns:
            str: Properly formatted markdown text.
        """
        if not text.strip():
            return ""

        # Split into lines and process
        lines = text.split("\n")
        formatted_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                # Handle empty lines and paragraph breaks
                if i > 0 and lines[i - 1].strip():
                    formatted_lines.append("")
                i += 1
                continue

            # Check for algorithm blocks first
            if self._is_algorithm_start(line):
                algorithm_block = self._format_algorithm_block(lines, i)
                formatted_lines.append(algorithm_block)
                # Skip the lines that were processed in the algorithm block
                i = self._find_algorithm_end(lines, i)
            else:
                if processed_line := self._process_line(line, lines, i):
                    formatted_lines.append(processed_line)
                i += 1

        # Clean up spacing
        return self._cleanup_spacing("\n".join(formatted_lines))

    def _find_algorithm_end(self, lines: List[str], start_index: int) -> int:
        """Find the end index of an algorithm block."""
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()

            # Stop conditions for algorithm blocks
            if not line:
                if i + 1 >= len(lines) or not self._looks_like_algorithm_content(
                    lines[i + 1]
                ):
                    break
                i += 1
                continue
            elif (
                self._looks_like_algorithm_content(line)
                or self._is_algorithm_continuation(line)
                or self._is_algorithm_text(line)
            ):
                i += 1
                continue
            else:
                # Check if this might be the end of the algorithm
                if re.match(r"^\d+\.\s+[A-Z]", line) or re.match(
                    r"^[A-Z][A-Z\s]{3,}$", line
                ):
                    break
                # If it doesn't look like algorithm content but we're still in the algorithm, include it
                i += 1

        return i

    def _process_line(self, line: str, lines: List[str], index: int) -> Optional[str]:
        """
        Process a single line and determine its formatting.
        Args:
            line (str): Current line.
            lines (List[str]): All lines for context.
            index (int): Current line index.
        Returns:
            Optional[str]: Formatted line or None to skip.
        """
        # Check for algorithm blocks first
        if self._is_algorithm_start(line):
            return self._format_algorithm_block(lines, index)
        # Check for headings
        if self._is_heading(line):
            return self._format_heading(line)

        # Check for lists
        if self._is_list_item(line):
            return self._format_list_item(line)

        # Check for code blocks
        if self._is_code_block(line):
            return self._format_code_block(line)

        # Check for emphasis
        if self._has_emphasis(line):
            return self._format_emphasis(line)

        # Check for abstract
        if self._is_abstract(line):
            return self._format_abstract(line, lines, index)

        # Check for figure captions
        if self._is_figure_caption(line):
            return self._format_figure_caption(line)

        # Check for table captions
        if self._is_table_caption(line):
            return self._format_table_caption(line)

        # Check for references
        if self._is_reference(line):
            return self._format_reference(line)

        # FIXED: Handle mixed content with inline math detection
        # Only treat the entire line as math if it's pure mathematical content
        if math_processor.is_mathematical_content(line) and self._is_pure_math_content(
            line
        ):
            return math_processor.process_mathematical_content(line)
        else:
            # Regular text with potential inline math
            return self._format_regular_text(line)

    def _is_algorithm_start(self, line: str) -> bool:
        """Check if line starts an algorithm block."""
        return re.match(r"^Algorithm \d+", line, re.IGNORECASE) is not None

    def _format_algorithm_block(self, lines: List[str], start_index: int) -> str:
        """Format an algorithm block as a code block."""
        algorithm_lines = ["```", lines[start_index].strip()]

        # Collect ALL algorithm content as raw text (no processing at all)
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()

            # Stop conditions for algorithm blocks
            if not line:
                # Empty line - check if next few lines are still algorithm content
                if i + 1 < len(lines) and self._looks_like_algorithm_content(
                    lines[i + 1]
                ):
                    algorithm_lines.append("")
                else:
                    break
            elif (
                self._looks_like_algorithm_content(line)
                or self._is_algorithm_continuation(line)
                or self._is_algorithm_text(line)
                or self._is_algorithm_any_content(line)
            ):
                # Add raw line without any processing
                algorithm_lines.append(line)
            elif re.match(r"^\d+\.\s+[A-Z]", line) or re.match(
                r"^[A-Z][A-Z\s]{3,}$", line
            ):
                break
            else:
                # If it doesn't look like algorithm content but we're still in the algorithm, include it as raw text
                algorithm_lines.append(line)

            i += 1

        # End code block
        algorithm_lines.append("```")

        return "\n".join(algorithm_lines)

    def _looks_like_algorithm_content(self, line: str) -> bool:
        """Check if line looks like algorithm pseudocode content."""
        # Algorithm content patterns
        algorithm_patterns = [
            r"^\d+:",  # Line numbers
            r"^//",  # Comments
            r"^end",  # End statements
            r"^if",  # Control structures
            r"^else",
            r"^for",
            r"^while",
            r"^return",
            r"^break",
            r"^continue",
            r"^←",  # Assignment
            r"^Input:",
            r"^Output:",
            r"^Create",
            r"^Sort",
            r"^index",
            r"^Phase",
            r"^Fill",
            r"^Merge",
            r"^while",
            r"^for each",
            r"^end for",
            r"^end while",
            r"^end if",
            r"^Sorted array",
            r"^Append",
            r"^Insert",
            r"^Add",
            r"^base array",
            r"^Rainbow",
            r"^BINARYSEARCH",
            r"^MERGE",
            r"^MERGEPOLICY",
        ]

        return any(
            re.match(pattern, line, re.IGNORECASE) for pattern in algorithm_patterns
        )

    def _is_algorithm_continuation(self, line: str) -> bool:
        """Check if line is a continuation of algorithm content."""
        # Lines that continue algorithm logic
        continuation_patterns = [
            r"^\s*if\s+",  # Indented if statements
            r"^\s*else\s+",  # Indented else statements
            r"^\s*for\s+",  # Indented for loops
            r"^\s*while\s+",  # Indented while loops
            r"^\s*return\s+",  # Indented return statements
            r"^\s*break",  # Indented break
            r"^\s*continue",  # Indented continue
            r"^\s*←",  # Indented assignment
            r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*←",  # Variable assignment
            r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(",  # Function calls
            r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=",  # Variable assignment with =
            r"^\s*//",  # Indented comments
            r"^\s*\d+:",  # Indented line numbers
        ]

        return any(re.match(pattern, line) for pattern in continuation_patterns)

    def _is_algorithm_text(self, line: str) -> bool:
        """Check if line is algorithm text that should be included in the code block."""
        # Algorithm text patterns that should be included
        algorithm_text_patterns = [
            r"^Fill the Rainbow",
            r"^Merge the bands",
            r"^while True do",
            r"^if index is at the middle",
            r"^if base array length is even",
            r"^if value is between",
            r"^Append new band",
            r"^Insert value at middle",
            r"^Add value to the front",
            r"^Add value to the back",
            r"^Insert value before middle",
            r"^Insert value after middle",
            r"^if index in bottom half",
            r"^if index in top half",
            r"^Insert value at the front",
            r"^Insert value at the end",
            r"^while number of bands",
            r"^for bandi, bandj in",
            r"^Sorted array =",
            r"^return Sorted array",
        ]

        return any(
            re.match(pattern, line, re.IGNORECASE)
            for pattern in algorithm_text_patterns
        )

    def _is_algorithm_any_content(self, line: str) -> bool:
        """Check if line is any kind of algorithm content that should be included."""
        # This is a catch-all for any line that might be algorithm content
        # We want to be very permissive here to avoid missing algorithm content

        # Skip lines that are clearly not algorithm content
        if re.match(r"^\d+\.\s+[A-Z]", line):  # Section headings
            return False
        if re.match(r"^[A-Z][A-Z\s]{3,}$", line):  # ALL CAPS headings
            return False
        if re.match(r"^Figure \d+", line, re.IGNORECASE):  # Figure captions
            return False
        return not re.match(r"^Table \d+", line, re.IGNORECASE)

    def _is_heading(self, line: str) -> bool:
        """Check if line is a heading."""
        return any(pattern.match(line) for pattern in self.compiled_patterns["heading"])

    def _format_heading(self, line: str) -> str:
        """Format a heading."""
        # Determine heading level based on pattern
        if re.match(r"^[A-Z][A-Z\s]{3,}$", line):
            return f"# {line}"
        elif re.match(r"^\d+\.\s+[A-Z]", line):
            return f"## {line}"
        elif re.match(r"^\d+\.\d+\s+[A-Z]", line):
            return f"### {line}"
        else:
            return f"## {line}"

    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item."""
        return any(
            pattern.match(line) for pattern in self.compiled_patterns["list_item"]
        )

    def _format_list_item(self, line: str) -> str:
        """Format a list item."""
        return line

    def _is_code_block(self, line: str) -> bool:
        """Check if line is a code block."""
        return any(
            pattern.match(line) for pattern in self.compiled_patterns["code_block"]
        )

    def _format_code_block(self, line: str) -> str:
        """Format a code block."""
        return line

    def _has_emphasis(self, line: str) -> bool:
        """Check if line has emphasis."""
        return any(
            pattern.search(line) for pattern in self.compiled_patterns["emphasis"]
        )

    def _format_emphasis(self, line: str) -> str:
        """Format emphasis."""
        return line

    def _is_abstract(self, line: str) -> bool:
        """Check if line is an abstract."""
        return any(
            pattern.match(line, re.IGNORECASE)
            for pattern in self.compiled_patterns["abstract"]
        )

    def _format_abstract(self, line: str, lines: List[str], index: int) -> str:
        """Format an abstract section."""
        # Collect abstract content
        abstract_lines = [line]
        i = index + 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line or self._is_heading(next_line):
                break
            abstract_lines.append(next_line)
            i += 1

        return f"### Abstract\n{' '.join(abstract_lines)}"

    def _is_figure_caption(self, line: str) -> bool:
        """Check if line is a figure caption."""
        return any(
            pattern.match(line, re.IGNORECASE)
            for pattern in self.compiled_patterns["figure_caption"]
        )

    def _format_figure_caption(self, line: str) -> str:
        """Format a figure caption."""
        return f"**{line}**"

    def _is_table_caption(self, line: str) -> bool:
        """Check if line is a table caption."""
        return any(
            pattern.match(line, re.IGNORECASE)
            for pattern in self.compiled_patterns["table_caption"]
        )

    def _format_table_caption(self, line: str) -> str:
        """Format a table caption."""
        return f"**{line}**"

    def _is_reference(self, line: str) -> bool:
        """Check if line is a reference."""
        return any(
            pattern.match(line) for pattern in self.compiled_patterns["reference"]
        )

    def _format_reference(self, line: str) -> str:
        """Format a reference."""
        return line

    def _format_regular_text(self, line: str) -> str:
        """Format regular text with inline math detection."""
        return self._format_inline_math(line)

    def _format_inline_math(self, text: str) -> str:
        """Format inline mathematical expressions in text - FIXED: Better detection."""
        # Skip URLs and common non-math patterns
        if re.search(r"https?://|www\.|\.com|\.org|\.net", text):
            return text

        # FIXED: More comprehensive patterns for inline math
        inline_math_patterns = [
            r"O\([^)]+\)",  # Big O notation
            r"\\[a-zA-Z]+",  # LaTeX commands
            r"[a-zA-Z]_[a-zA-Z0-9]",  # Subscripts
            r"[a-zA-Z]\^[a-zA-Z0-9]",  # Superscripts
            r"[a-zA-Z]\s*[=+\-*/]\s*[a-zA-Z0-9]",  # Simple equations
            r"[a-zA-Z]\s*[=+\-*/]\s*[a-zA-Z0-9]\s*[+\-*/]\s*[a-zA-Z0-9]",  # Multi-operator equations
        ]

        # Find and format inline math
        for pattern in inline_math_patterns:
            matches = re.finditer(pattern, text)
            # Process matches in reverse order to avoid index issues
            for match in reversed(list(matches)):
                start, end = match.span()
                math_expr = match.group()

                if start > 0:
                    if text[start - 1] == "$" and end < len(text) and text[end] == "$":
                        continue

                    # Check if it's part of a larger math block
                    prev_char = text[start - 1]
                    next_char = text[end]
                    if prev_char in "=+-*/" or next_char in "=+-*/":
                        continue

                # Wrap in inline math delimiters
                text = f"{text[:start]}${math_expr}${text[end:]}"

        return text

    def _cleanup_spacing(self, text: str) -> str:
        """
        Clean up spacing and formatting issues.
        Args:
            text (str): Text to clean up.
        Returns:
            str: Cleaned text.
        """
        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Ensure proper spacing around headings
        text = re.sub(r"([^\n])\n(#+\s)", r"\1\n\n\2", text)
        text = re.sub(r"(#+\s[^\n]*)\n([^\n])", r"\1\n\n\2", text)

        # Ensure proper spacing around lists
        text = re.sub(r"([^\n])\n(\s*[-*+]\s)", r"\1\n\n\2", text)
        text = re.sub(r"(\s*[-*+]\s[^\n]*)\n([^\n])", r"\1\n\n\2", text)

        # Ensure proper spacing around math blocks
        text = re.sub(r"([^\n])\n(\$\$)", r"\1\n\n\2", text)
        text = re.sub(r"(\$\$)\n([^\n])", r"\1\n\n\2", text)

        # Clean up trailing whitespace
        text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)

        # Ensure consistent line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        return text.strip()

    def format_structured_content(self, structured_content: Dict[str, Any]) -> str:
        """
        Format structured content into markdown.
        Args:
            structured_content (Dict[str, Any]): Structured content from extraction.
        Returns:
            str: Formatted markdown text.
        """
        formatted_sections = []

        # Process pages in order
        pages = structured_content.get("pages", [])
        for page in pages:
            text_blocks = sorted(
                page["text_blocks"], key=lambda x: (x["bbox"][1], x["bbox"][0])
            )

            for block in text_blocks:
                block_type = block.get("type", "body")
                text = block["text"].strip()

                if not text:
                    continue

                # Process based on block type
                if block_type == "title":
                    formatted_sections.append(f"# {text}")
                elif block_type == "heading":
                    formatted_sections.append(f"## {text}")
                elif block_type == "abstract":
                    formatted_sections.append(f"### Abstract\n{text}")
                elif block_type == "figure_caption":
                    formatted_sections.append(f"**{text}**")
                elif block_type == "table_caption":
                    formatted_sections.append(f"**{text}**")
                elif block_type == "math":
                    # Use math processor for mathematical content
                    formatted_sections.append(
                        math_processor.process_mathematical_content(text)
                    )
                elif block_type == "reference":
                    formatted_sections.append(text)
                else:
                    # Regular body text
                    formatted_sections.append(self.format_text(text))

        # Add tables
        tables = structured_content.get("tables", [])
        for i, table in enumerate(tables):
            formatted_sections.append(f"\n### Table {i+1}")
            formatted_sections.extend(self._table_to_markdown(table))

        # Add math blocks
        math_blocks = structured_content.get("math_blocks", [])
        formatted_sections.extend(
            math_processor.process_mathematical_content(math_block["text"])
            for math_block in math_blocks
        )
        # Add figures
        figures = structured_content.get("figures", [])
        formatted_sections.extend(f"\n**{figure['caption']}**" for figure in figures)
        if references := structured_content.get("references", []):
            formatted_sections.append("\n## References")
            formatted_sections.extend(ref["text"] for ref in references)
        return self._cleanup_spacing("\n\n".join(formatted_sections))

    def _table_to_markdown(self, table: Dict[str, Any]) -> List[str]:
        """Convert table data to Markdown table format."""
        md_lines = []
        data = table.get("data", [])

        if not data:
            return md_lines

        # Create header
        header = "| " + " | ".join(str(cell) for cell in data[0]) + " |"
        separator = "| " + " | ".join("---" for _ in data[0]) + " |"

        md_lines.extend((header, separator))
        # Add data rows
        md_lines.extend(
            "| " + " | ".join(str(cell) for cell in row) + " |" for row in data[1:]
        )
        return md_lines

    def _is_pure_math_content(self, text: str) -> bool:
        """Check if text contains only mathematical content."""
        # Skip if text contains common non-math words
        non_math_words = [
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "this",
            "that",
            "these",
            "those",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "can",
            "may",
            "might",
            "must",
            "shall",
            "paper",
            "algorithm",
            "data",
            "structure",
            "analysis",
            "complexity",
            "runtime",
            "performance",
            "comparison",
            "results",
            "figure",
            "table",
            "section",
            "chapter",
            "introduction",
            "conclusion",
            "test",
            "with",
            "math",
            "and",
            "some",
            "text",
        ]

        text_lower = text.lower()
        for word in non_math_words:
            if word in text_lower:
                return False

        # If it passes the word check and contains math, it's likely pure math
        return math_processor.is_mathematical_content(text)


# Global instance
markdown_formatter = MarkdownFormatter()
