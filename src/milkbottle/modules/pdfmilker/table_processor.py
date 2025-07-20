"""PDFmilker advanced table processing with complex structure handling."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import pandas as pd

from .errors import PDFMilkerError

logger = logging.getLogger("pdfmilker.table_processor")


class TableStructure:
    """Represents a table with its structure and metadata."""

    def __init__(self, page_number: int, bbox: Tuple[float, float, float, float]):
        self.page_number = page_number
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.rows: List[List[str]] = []
        self.headers: List[str] = []
        self.table_number: Optional[str] = None
        self.caption: Optional[str] = None
        self.confidence: float = 0.0
        self.structure_type: str = "simple"  # simple, complex, merged_cells
        self.column_count: int = 0
        self.row_count: int = 0
        self.has_headers: bool = False
        self.merged_cells: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert table to dictionary representation."""
        return {
            "page_number": self.page_number,
            "bbox": self.bbox,
            "rows": self.rows,
            "headers": self.headers,
            "table_number": self.table_number,
            "caption": self.caption,
            "confidence": self.confidence,
            "structure_type": self.structure_type,
            "column_count": self.column_count,
            "row_count": self.row_count,
            "has_headers": self.has_headers,
            "merged_cells": self.merged_cells,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Convert table to pandas DataFrame."""
        if not self.rows:
            return pd.DataFrame()

        if self.has_headers and self.headers:
            return pd.DataFrame(self.rows, columns=self.headers)
        else:
            return pd.DataFrame(self.rows)


class TableProcessor:
    """Advanced table processor with complex structure handling."""

    def __init__(self):
        self.min_table_size = 3  # Minimum rows/columns to be considered a table
        self.max_table_size = 100  # Maximum rows/columns
        self.table_patterns = [
            r"Table\s+(\d+)[:\.]\s*(.+)",
            r"Tab\.\s+(\d+)[:\.]\s*(.+)",
            r"(\d+)\.\s*(.+)",  # Numbered tables
        ]
        self.header_patterns = [
            r"^[A-Z][a-z\s]+$",  # Title case headers
            r"^[A-Z\s]+$",  # All caps headers
            r"^[a-z\s]+$",  # All lowercase headers
        ]

    def extract_tables_with_structure(self, pdf_path: Path) -> List[TableStructure]:
        """
        Extract tables with advanced structure analysis.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TableStructure objects
        """
        try:
            tables = []
            doc = fitz.Document(str(pdf_path))

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract tables from page
                page_tables = self._extract_tables_from_page(page, page_num)
                tables.extend(page_tables)

                # Extract table captions
                captions = self._extract_table_captions(page, page_num)

                # Match tables with captions
                self._match_tables_with_captions(page_tables, captions)

            doc.close()

            # Post-process tables
            self._post_process_tables(tables)

            logger.info(f"Extracted {len(tables)} tables from {pdf_path.name}")
            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables from {pdf_path}: {e}")
            raise PDFMilkerError(f"Table extraction failed: {e}") from e

    def _extract_tables_from_page(
        self, page: fitz.Page, page_num: int
    ) -> List[TableStructure]:
        """Extract tables from a single page."""
        tables = []

        try:
            # Get text blocks with their positions
            text_dict = page.get_text("dict")

            # Group text blocks into potential table regions
            table_regions = self._identify_table_regions(text_dict)

            for region in table_regions:
                table = self._process_table_region(region, page_num)
                if table and self._validate_table(table):
                    tables.append(table)

            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables from page {page_num}: {e}")
            return []

    def _identify_table_regions(
        self, text_dict: Dict[str, Any]
    ) -> List[List[Dict[str, Any]]]:
        """Identify regions that might contain tables."""
        blocks = text_dict.get("blocks", [])

        # Group blocks by vertical alignment
        aligned_blocks = self._group_aligned_blocks(blocks)

        return [
            aligned_group
            for aligned_group in aligned_blocks
            if len(aligned_group) >= self.min_table_size
            and self._looks_like_table(aligned_group)
        ]

    def _group_aligned_blocks(
        self, blocks: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group text blocks that are vertically aligned."""
        text_blocks = [b for b in blocks if b.get("type") == 0]  # Text blocks only

        if not text_blocks:
            return []

        # Sort by y-coordinate
        text_blocks.sort(key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])

        groups = []
        current_group = []

        for block in text_blocks:
            bbox = block.get("bbox", [0, 0, 0, 0])

            if not current_group:
                current_group = [block]
            else:
                # Check if this block is close to the current group
                last_bbox = current_group[-1].get("bbox", [0, 0, 0, 0])
                y_distance = abs(bbox[1] - last_bbox[1])

                if y_distance < 50:  # Within 50 points
                    current_group.append(block)
                else:
                    if len(current_group) >= 2:
                        groups.append(current_group)
                    current_group = [block]

        if len(current_group) >= 2:
            groups.append(current_group)

        return groups

    def _looks_like_table(self, blocks: List[Dict[str, Any]]) -> bool:
        """Determine if a group of blocks looks like a table."""
        if len(blocks) < 2:
            return False

        # Check for consistent column structure
        column_positions = self._analyze_column_positions(blocks)

        if len(column_positions) < 2:
            return False

        # Check for tabular data patterns
        tabular_score = 0

        for block in blocks:
            text = block.get("text", "").strip()

            # Check for tabular separators
            if re.search(r"[\t|,;]", text):
                tabular_score += 1

            # Check for numeric data
            if re.search(r"\d+", text):
                tabular_score += 1

            # Check for consistent spacing
            if len(text.split()) >= 2:
                tabular_score += 1

        return tabular_score >= len(blocks) * 0.5

    def _analyze_column_positions(self, blocks: List[Dict[str, Any]]) -> List[float]:
        """Analyze column positions in text blocks."""
        positions = set()

        for block in blocks:
            text = block.get("text", "").strip()
            bbox = block.get("bbox", [0, 0, 0, 0])

            if words := text.split():
                # Use the x-position of the block as a column marker
                positions.add(bbox[0])

        return sorted(list(positions))

    def _process_table_region(
        self, blocks: List[Dict[str, Any]], page_num: int
    ) -> Optional[TableStructure]:
        """Process a region of blocks into a table structure."""
        try:
            # Sort blocks by position
            blocks.sort(
                key=lambda b: (
                    b.get("bbox", [0, 0, 0, 0])[1],
                    b.get("bbox", [0, 0, 0, 0])[0],
                )
            )

            # Calculate table bounding box
            bbox = self._calculate_table_bbox(blocks)

            # Create table structure
            table = TableStructure(page_num, bbox)

            # Extract rows from blocks
            rows = self._extract_rows_from_blocks(blocks)
            table.rows = rows

            # Analyze table structure
            self._analyze_table_structure(table)

            return table

        except Exception as e:
            logger.error(f"Failed to process table region: {e}")
            return None

    def _calculate_table_bbox(
        self, blocks: List[Dict[str, Any]]
    ) -> Tuple[float, float, float, float]:
        """Calculate bounding box for table region."""
        if not blocks:
            return (0, 0, 0, 0)

        x0 = min(b.get("bbox", [0, 0, 0, 0])[0] for b in blocks)
        y0 = min(b.get("bbox", [0, 0, 0, 0])[1] for b in blocks)
        x1 = max(b.get("bbox", [0, 0, 0, 0])[2] for b in blocks)
        y1 = max(b.get("bbox", [0, 0, 0, 0])[3] for b in blocks)

        return (x0, y0, x1, y1)

    def _extract_rows_from_blocks(
        self, blocks: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """Extract rows from text blocks."""
        rows = []

        for block in blocks:
            if text := block.get("text", "").strip():
                # Split text into columns
                columns = self._split_into_columns(text)
                rows.append(columns)

        return rows

    def _split_into_columns(self, text: str) -> List[str]:
        """Split text into columns based on spacing and separators."""
        # Try different splitting strategies

        # 1. Check for tabular separators
        if "\t" in text:
            return [col.strip() for col in text.split("\t")]

        # 2. Check for pipe separators
        if "|" in text:
            return [col.strip() for col in text.split("|")]

        # 3. Check for multiple spaces (likely column separator)
        if re.search(r"\s{3,}", text):
            return [col.strip() for col in re.split(r"\s{3,}", text)]

        # 4. Split by commas (if it looks like CSV)
        if text.count(",") >= 2:
            return [col.strip() for col in text.split(",")]

        # 5. Default: split by single spaces
        return [col.strip() for col in text.split()]

    def _analyze_table_structure(self, table: TableStructure) -> None:
        """Analyze and classify table structure."""
        if not table.rows:
            return

        table.row_count = len(table.rows)
        table.column_count = max(len(row) for row in table.rows) if table.rows else 0

        # Check for headers
        if table.row_count > 0:
            first_row = table.rows[0]
            if self._looks_like_headers(first_row):
                table.has_headers = True
                table.headers = first_row
                table.rows = table.rows[1:]  # Remove header row from data
                table.row_count -= 1

        # Analyze structure type
        if self._has_merged_cells(table):
            table.structure_type = "merged_cells"
        elif table.column_count > 5:
            table.structure_type = "complex"
        else:
            table.structure_type = "simple"

        # Calculate confidence
        table.confidence = self._calculate_table_confidence(table)

    def _looks_like_headers(self, row: List[str]) -> bool:
        """Determine if a row looks like table headers."""
        if not row:
            return False

        header_score = 0

        for cell in row:
            cell_text = cell.strip()

            # Check header patterns
            for pattern in self.header_patterns:
                if re.match(pattern, cell_text):
                    header_score += 1
                    break

            # Check for common header words
            header_words = [
                "name",
                "type",
                "value",
                "date",
                "time",
                "id",
                "code",
                "description",
            ]
            if any(word in cell_text.lower() for word in header_words):
                header_score += 1

        return header_score >= len(row) * 0.5

    def _has_merged_cells(self, table: TableStructure) -> bool:
        """Check if table has merged cells."""
        if not table.rows:
            return False

        # Check for inconsistent column counts
        column_counts = [len(row) for row in table.rows]
        return len(set(column_counts)) > 1

    def _calculate_table_confidence(self, table: TableStructure) -> float:
        """Calculate confidence score for table extraction."""
        confidence = 0.5  # Base confidence

        # Size-based confidence
        if table.row_count >= 3 and table.column_count >= 2:
            confidence += 0.2

        # Structure-based confidence
        if table.has_headers:
            confidence += 0.1

        if table.structure_type == "simple":
            confidence += 0.1
        elif table.structure_type == "complex":
            confidence += 0.05

        # Consistency-based confidence
        if table.rows:
            column_counts = [len(row) for row in table.rows]
            if len(set(column_counts)) == 1:  # All rows have same column count
                confidence += 0.1

        return min(confidence, 1.0)

    def _extract_table_captions(
        self, page: fitz.Page, page_num: int
    ) -> List[Dict[str, Any]]:
        """Extract potential table captions from page text."""
        captions = []

        try:
            # Get text blocks
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    text = block.get("text", "").strip()
                    bbox = block.get("bbox", (0, 0, 0, 0))

                    if text and len(text) > 10:
                        if caption_info := self._identify_table_caption(text, bbox):
                            caption_info["page_number"] = page_num
                            captions.append(caption_info)

            return captions

        except Exception as e:
            logger.error(f"Failed to extract table captions from page {page_num}: {e}")
            return []

    def _identify_table_caption(
        self, text: str, bbox: Tuple[float, float, float, float]
    ) -> Optional[Dict[str, Any]]:
        """Identify if text is a table caption."""
        for pattern in self.table_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                if len(match.groups()) == 2:
                    table_num = match.group(1)
                    caption_text = match.group(2).strip()
                else:
                    table_num = None
                    caption_text = text.strip()

                return {
                    "text": caption_text,
                    "table_number": table_num,
                    "bbox": bbox,
                    "confidence": 0.8,
                }

        return None

    def _match_tables_with_captions(
        self, tables: List[TableStructure], captions: List[Dict[str, Any]]
    ) -> None:
        """Match tables with their captions based on proximity."""
        for table in tables:
            best_caption = None
            best_distance = float("inf")

            for caption in captions:
                if caption["page_number"] != table.page_number:
                    continue

                # Calculate distance between table and caption
                distance = self._calculate_distance(table.bbox, caption["bbox"])

                if (
                    distance < best_distance and distance < 200
                ):  # Max 200 points distance
                    best_distance = distance
                    best_caption = caption

            if best_caption:
                table.caption = best_caption["text"]
                table.table_number = best_caption["table_number"]
                table.confidence = min(table.confidence + 0.2, 1.0)

    def _calculate_distance(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float],
    ) -> float:
        """Calculate distance between two bounding boxes."""
        # Use center points
        center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
        center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)

        return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5

    def _validate_table(self, table: TableStructure) -> bool:
        """Validate if extracted structure is actually a table."""
        if not table.rows:
            return False

        if table.row_count < self.min_table_size:
            return False

        if table.column_count < 2:
            return False

        return (
            table.row_count <= self.max_table_size
            and table.column_count <= self.max_table_size
        )

    def _post_process_tables(self, tables: List[TableStructure]) -> None:
        """Post-process extracted tables."""
        # Sort tables by page number and position
        tables.sort(key=lambda t: (t.page_number, t.bbox[1], t.bbox[0]))

        # Assign table numbers if missing
        table_counter = 1
        for table in tables:
            if not table.table_number:
                table.table_number = str(table_counter)
                table_counter += 1

    def export_table_to_csv(self, table: TableStructure, output_path: Path) -> bool:
        """Export table to CSV format."""
        try:
            df = table.to_dataframe()
            df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"Failed to export table to CSV: {e}")
            return False

    def export_table_to_excel(self, table: TableStructure, output_path: Path) -> bool:
        """Export table to Excel format."""
        try:
            df = table.to_dataframe()
            df.to_excel(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"Failed to export table to Excel: {e}")
            return False

    def get_table_statistics(self, tables: List[TableStructure]) -> Dict[str, Any]:
        """Get statistics about extracted tables."""
        if not tables:
            return {"total_tables": 0}

        stats = {
            "total_tables": len(tables),
            "pages_with_tables": len({t.page_number for t in tables}),
            "structure_types": {},
            "size_distribution": {"small": 0, "medium": 0, "large": 0},
            "captions_extracted": sum(bool(t.caption) for t in tables),
            "table_numbers_assigned": sum(bool(t.table_number) for t in tables),
            "tables_with_headers": sum(bool(t.has_headers) for t in tables),
            "average_confidence": sum(t.confidence for t in tables) / len(tables),
        }

        # Structure type distribution
        for table in tables:
            structure_type = table.structure_type
            stats["structure_types"][structure_type] = (
                stats["structure_types"].get(structure_type, 0) + 1
            )

        # Size distribution
        for table in tables:
            total_cells = table.row_count * table.column_count
            if total_cells <= 20:
                stats["size_distribution"]["small"] += 1
            elif total_cells <= 100:
                stats["size_distribution"]["medium"] += 1
            else:
                stats["size_distribution"]["large"] += 1

        return stats


# Global table processor instance
table_processor = TableProcessor()
