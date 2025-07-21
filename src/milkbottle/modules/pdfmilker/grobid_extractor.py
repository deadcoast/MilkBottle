"""PDFmilker Grobid integration for proper scientific paper extraction."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

try:
    from grobid_client import GrobidClient

    GROBID_AVAILABLE = True
except ImportError:
    GROBID_AVAILABLE = False
    logging.warning("Grobid client not available")

logger = logging.getLogger("pdfmilker.grobid")


class GrobidExtractor:
    """Scientific paper extractor using Grobid."""

    def __init__(self, grobid_url: str = "http://localhost:8070"):
        self.grobid_url = grobid_url
        self.client = None
        if GROBID_AVAILABLE:
            try:
                self.client = GrobidClient(grobid_url)
                logger.info(f"Connected to Grobid at {grobid_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Grobid: {e}")

    def extract_scientific_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract scientific paper content using Grobid.
        Args:
            pdf_path (Path): Path to the PDF file.
        Returns:
            Dict[str, Any]: Structured content including text, math, tables, references.
        """
        if not self.client:
            logger.error("Grobid client not available")
            return self._fallback_extraction(pdf_path)

        try:
            # Process PDF with Grobid
            result = self.client.process_pdf(
                str(pdf_path),
                "processFulltextDocument",
                generateIDs=1,
                consolidateHeader=1,
                consolidateCitations=1,
                includeRawCitations=1,
                includeRawAffiliations=1,
                teiCoordinates=1,
            )

            if result and result.status_code == 200:
                return self._parse_grobid_result(result.text)
            logger.warning(
                f"Grobid processing failed: {result.status_code if result else 'No response'}"
            )
            return self._fallback_extraction(pdf_path)

        except Exception as e:
            logger.error(f"Grobid extraction failed: {e}")
            return self._fallback_extraction(pdf_path)

    def _parse_grobid_result(self, tei_xml: str) -> Dict[str, Any]:
        """
        Parse Grobid TEI XML result into structured content.
        Args:
            tei_xml (str): TEI XML from Grobid.
        Returns:
            Dict[str, Any]: Structured content.
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(tei_xml, "xml")

            # Extract title
            title = ""
            if title_elem := soup.find("title"):
                title = title_elem.get_text(strip=True)

            # Extract abstract
            abstract = ""
            if abstract_elem := soup.find("abstract"):
                abstract = abstract_elem.get_text(strip=True)

            # Extract body text
            body_text = ""
            if body_elem := soup.find("body"):
                body_text = body_elem.get_text(strip=True)

            math_formulas = [
                {
                    "type": formula.get("type", "inline"),
                    "content": formula.get_text(strip=True),
                    "id": formula.get("xml:id", ""),
                }
                for formula in soup.find_all("formula")
            ]
            # Extract tables
            tables = []
            for table in soup.find_all("table"):
                table_data = self._extract_table_data(table)
                tables.append(table_data)

            # Extract references
            references = []
            for ref in soup.find_all("biblStruct"):
                ref_data = self._extract_reference_data(ref)
                references.append(ref_data)

            return {
                "title": title,
                "abstract": abstract,
                "body_text": body_text,
                "math_formulas": math_formulas,
                "tables": tables,
                "references": references,
                "raw_tei": tei_xml,
            }

        except Exception as e:
            logger.error(f"Failed to parse Grobid result: {e}")
            return {
                "title": "",
                "abstract": "",
                "body_text": "",
                "math_formulas": [],
                "tables": [],
                "references": [],
                "raw_tei": tei_xml,
            }

    def _extract_table_data(self, table_elem) -> Dict[str, Any]:
        """Extract table data from TEI XML."""
        try:
            rows = []
            for row in table_elem.find_all("row"):
                cells = [cell.get_text(strip=True) for cell in row.find_all("cell")]
                rows.append(cells)

            return {
                "rows": rows,
                "headers": rows[0] if rows else [],
                "data": rows[1:] if len(rows) > 1 else [],
            }
        except Exception as e:
            logger.warning(f"Failed to extract table data: {e}")
            return {"rows": [], "headers": [], "data": []}

    def _extract_reference_data(self, ref_elem) -> Dict[str, Any]:
        """Extract reference data from TEI XML."""
        try:
            title = ""
            authors = []

            if title_elem := ref_elem.find("title"):
                title = title_elem.get_text(strip=True)

            for author in ref_elem.find_all("author"):
                if author_text := author.get_text(strip=True):
                    authors.append(author_text)

            return {
                "title": title,
                "authors": authors,
                "raw": ref_elem.get_text(strip=True),
            }
        except Exception as e:
            logger.warning(f"Failed to extract reference data: {e}")
            return {"title": "", "authors": [], "raw": ""}

    def _fallback_extraction(self, pdf_path: Path) -> Dict[str, Any]:
        """Fallback to basic extraction if Grobid is not available."""
        logger.warning("Using fallback extraction - Grobid not available")
        return {
            "title": "",
            "abstract": "",
            "body_text": "",
            "math_formulas": [],
            "tables": [],
            "references": [],
            "raw_tei": "",
        }


# Global instance
grobid_extractor = GrobidExtractor()
