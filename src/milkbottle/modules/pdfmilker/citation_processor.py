"""PDFmilker citation processing with extraction and formatting."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from .errors import PDFMilkerError

logger = logging.getLogger("pdfmilker.citation_processor")


class Citation:
    """Represents a citation with its metadata and content."""

    def __init__(self, text: str, citation_type: str = "unknown"):
        self.text = text
        self.citation_type = citation_type  # in_text, footnote, bibliography
        self.authors: List[str] = []
        self.title: Optional[str] = None
        self.year: Optional[str] = None
        self.journal: Optional[str] = None
        self.doi: Optional[str] = None
        self.url: Optional[str] = None
        self.page_number: Optional[int] = None
        self.confidence: float = 0.0
        self.raw_text: str = text
        self.context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary representation."""
        return {
            "text": self.text,
            "citation_type": self.citation_type,
            "authors": self.authors,
            "title": self.title,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
            "page_number": self.page_number,
            "confidence": self.confidence,
            "raw_text": self.raw_text,
            "context": self.context,
        }

    def to_bibtex(self) -> str:
        """Convert citation to BibTeX format."""
        if not self.authors or not self.title:
            return f"@misc{{{self._generate_key()},\n  title = {{{self.raw_text}}}\n}}"

        bibtex = f"@article{{{self._generate_key()},\n"
        bibtex += f"  author = {{{' and '.join(self.authors)}}},\n"
        bibtex += f"  title = {{{self.title}}},\n"

        if self.year:
            bibtex += f"  year = {{{self.year}}},\n"

        if self.journal:
            bibtex += f"  journal = {{{self.journal}}},\n"

        if self.doi:
            bibtex += f"  doi = {{{self.doi}}},\n"

        if self.url:
            bibtex += f"  url = {{{self.url}}},\n"

        bibtex = bibtex.rstrip(",\n") + "\n}"
        return bibtex

    def _generate_key(self) -> str:
        """Generate a unique key for the citation."""
        if self.authors and self.year:
            author = self.authors[0].split()[-1] if self.authors[0] else "Unknown"
            return f"{author}{self.year}"
        elif self.authors:
            author = self.authors[0].split()[-1] if self.authors[0] else "Unknown"
            return f"{author}Unknown"
        else:
            return "UnknownAuthorUnknown"


class Bibliography:
    """Represents a bibliography section."""

    def __init__(self):
        self.citations: List[Citation] = []
        self.title: Optional[str] = None
        self.page_number: Optional[int] = None
        self.confidence: float = 0.0

    def add_citation(self, citation: Citation) -> None:
        """Add a citation to the bibliography."""
        self.citations.append(citation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert bibliography to dictionary representation."""
        return {
            "title": self.title,
            "page_number": self.page_number,
            "confidence": self.confidence,
            "citations": [c.to_dict() for c in self.citations],
            "citation_count": len(self.citations),
        }

    def to_bibtex(self) -> str:
        """Convert bibliography to BibTeX format."""
        bibtex = ""
        for citation in self.citations:
            bibtex += citation.to_bibtex() + "\n\n"
        return bibtex.strip()

    def to_markdown(self) -> str:
        """Convert bibliography to Markdown format."""
        if not self.citations:
            return ""

        markdown = "# References\n\n"

        for i, citation in enumerate(self.citations, 1):
            markdown += f"{i}. "

            if citation.authors:
                markdown += f"{', '.join(citation.authors)}. "

            if citation.title:
                markdown += f"**{citation.title}**. "

            if citation.journal:
                markdown += f"*{citation.journal}*. "

            if citation.year:
                markdown += f"{citation.year}. "

            if citation.doi:
                markdown += f"DOI: {citation.doi}. "

            markdown += "\n\n"

        return markdown


class CitationProcessor:
    """Advanced citation processor with extraction and formatting."""

    def __init__(self):
        self.citation_patterns = {
            "in_text": [
                r"\(([^)]+)\)",  # (Author, Year)
                r"\[([^\]]+)\]",  # [Author, Year]
                r"([A-Z][a-z]+ et al\.?,?\s+\d{4})",  # Author et al., Year
                r"([A-Z][a-z]+ and [A-Z][a-z]+,?\s+\d{4})",  # Author and Author, Year
            ],
            "footnote": [
                r"^\d+\.\s*(.+)",  # Numbered footnotes
                r"^[a-z]\.\s*(.+)",  # Lettered footnotes
            ],
            "bibliography": [
                r"^[A-Z][a-z\s]+,\s*[A-Z]\.\s*\d{4}",  # Author, A. Year
                r"^[A-Z][a-z\s]+ et al\.\s*\d{4}",  # Author et al. Year
            ],
        }

        self.author_patterns = [
            r"([A-Z][a-z]+ [A-Z][a-z]+)",  # First Last
            r"([A-Z][a-z]+, [A-Z])",  # Last, First
        ]

        self.year_patterns = [
            r"\b(19|20)\d{2}\b",  # 19xx or 20xx
        ]

        self.doi_patterns = [
            r"10\.\d{4,}/[-._;()/:\w]+",
        ]

        self.url_patterns = [
            r"https?://[^\s]+",
        ]

    def extract_citations(self, pdf_path: Path) -> Bibliography:
        """
        Extract citations from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Bibliography object with extracted citations
        """
        try:
            bibliography = Bibliography()
            doc = fitz.Document(str(pdf_path))

            # Extract citations from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract in-text citations
                in_text_citations = self._extract_in_text_citations(page, page_num)
                bibliography.citations.extend(in_text_citations)

                # Extract footnotes
                footnote_citations = self._extract_footnotes(page, page_num)
                bibliography.citations.extend(footnote_citations)

                # Check for bibliography section
                if self._is_bibliography_page(page):
                    bibliography.page_number = page_num
                    bibliography.title = "References"
                    bibliography.confidence = 0.9

            doc.close()

            # Extract bibliography entries
            if bibliography.page_number is not None:
                doc = fitz.Document(str(pdf_path))
                page = doc.load_page(bibliography.page_number)
                bib_citations = self._extract_bibliography_entries(page)
                bibliography.citations.extend(bib_citations)
                doc.close()

            # Process and enhance citations
            self._process_citations(bibliography.citations)

            # Remove duplicates
            bibliography.citations = self._remove_duplicate_citations(
                bibliography.citations
            )

            logger.info(
                f"Extracted {len(bibliography.citations)} citations from {pdf_path.name}"
            )
            return bibliography

        except Exception as e:
            logger.error(f"Failed to extract citations from {pdf_path}: {e}")
            raise PDFMilkerError(f"Citation extraction failed: {e}") from e

    def _extract_in_text_citations(
        self, page: fitz.Page, page_num: int
    ) -> List[Citation]:
        """Extract in-text citations from page."""
        citations = []

        try:
            # Get text blocks
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    text = block.get("text", "").strip()

                    if text:
                        # Find citation patterns
                        for pattern in self.citation_patterns["in_text"]:
                            matches = re.finditer(pattern, text)
                            for match in matches:
                                citation_text = (
                                    match.group(1) if match.groups() else match.group(0)
                                )

                                citation = Citation(citation_text, "in_text")
                                citation.page_number = page_num
                                citation.context = (
                                    text[:100] + "..." if len(text) > 100 else text
                                )

                                citations.append(citation)

            return citations

        except Exception as e:
            logger.error(
                f"Failed to extract in-text citations from page {page_num}: {e}"
            )
            return []

    def _extract_footnotes(self, page: fitz.Page, page_num: int) -> List[Citation]:
        """Extract footnotes from page."""
        citations = []

        try:
            # Get text blocks
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    text = block.get("text", "").strip()

                    if text:
                        # Find footnote patterns
                        for pattern in self.citation_patterns["footnote"]:
                            matches = re.finditer(pattern, text, re.MULTILINE)
                            for match in matches:
                                citation_text = (
                                    match.group(1) if match.groups() else match.group(0)
                                )

                                citation = Citation(citation_text, "footnote")
                                citation.page_number = page_num
                                citation.context = (
                                    text[:100] + "..." if len(text) > 100 else text
                                )

                                citations.append(citation)

            return citations

        except Exception as e:
            logger.error(f"Failed to extract footnotes from page {page_num}: {e}")
            return []

    def _is_bibliography_page(self, page: fitz.Page) -> bool:
        """Check if page contains bibliography section."""
        try:
            text = page.get_text().lower()

            bibliography_keywords = [
                "references",
                "bibliography",
                "works cited",
                "literature cited",
                "sources",
                "citations",
                "further reading",
            ]

            for keyword in bibliography_keywords:
                if keyword in text:
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check bibliography page: {e}")
            return False

    def _extract_bibliography_entries(self, page: fitz.Page) -> List[Citation]:
        """Extract bibliography entries from page."""
        citations = []

        try:
            # Get text blocks
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    text = block.get("text", "").strip()

                    if text and len(text) > 20:  # Minimum length for bibliography entry
                        # Check if this looks like a bibliography entry
                        if self._looks_like_bibliography_entry(text):
                            citation = Citation(text, "bibliography")
                            citations.append(citation)

            return citations

        except Exception as e:
            logger.error(f"Failed to extract bibliography entries: {e}")
            return []

    def _looks_like_bibliography_entry(self, text: str) -> bool:
        """Determine if text looks like a bibliography entry."""
        # Check for author patterns
        author_found = False
        for pattern in self.author_patterns:
            if re.search(pattern, text):
                author_found = True
                break

        # Check for year
        year_found = bool(re.search(r"\b(19|20)\d{2}\b", text))

        # Check for title indicators
        title_indicators = ['"', "'", "**", "*", "_"]
        title_found = any(indicator in text for indicator in title_indicators)

        # Must have author and year, or title
        return author_found and (year_found or title_found)

    def _process_citations(self, citations: List[Citation]) -> None:
        """Process and enhance extracted citations."""
        for citation in citations:
            self._extract_citation_metadata(citation)
            citation.confidence = self._calculate_citation_confidence(citation)

    def _extract_citation_metadata(self, citation: Citation) -> None:
        """Extract metadata from citation text."""
        text = citation.text

        # Extract authors
        for pattern in self.author_patterns:
            authors = re.findall(pattern, text)
            if authors:
                citation.authors = [author.strip() for author in authors]
                break

        # Extract year
        for pattern in self.year_patterns:
            years = re.findall(pattern, text)
            if years:
                citation.year = years[0]
                break

        # Extract DOI
        for pattern in self.doi_patterns:
            dois = re.findall(pattern, text)
            if dois:
                citation.doi = dois[0]
                break

        # Extract URL
        for pattern in self.url_patterns:
            urls = re.findall(pattern, text)
            if urls:
                citation.url = urls[0]
                break

        # Extract title (simplified)
        # Look for text between quotes or in italics
        title_patterns = [
            r'"([^"]+)"',  # Double quotes
            r"'([^']+)'",  # Single quotes
            r"\*\*([^*]+)\*\*",  # Bold markdown
            r"\*([^*]+)\*",  # Italic markdown
        ]

        for pattern in title_patterns:
            titles = re.findall(pattern, text)
            if titles:
                citation.title = titles[0].strip()
                break

        # Extract journal (simplified)
        # Look for italicized text that might be journal names
        journal_patterns = [
            r"\*([^*]+)\*",  # Italic markdown
            r"_([^_]+)_",  # Underline markdown
        ]

        for pattern in journal_patterns:
            journals = re.findall(pattern, text)
            if journals:
                # Filter out likely titles
                for journal in journals:
                    if len(journal) > 3 and not journal.lower().startswith(
                        ("the ", "a ", "an ")
                    ):
                        citation.journal = journal.strip()
                        break

    def _calculate_citation_confidence(self, citation: Citation) -> float:
        """Calculate confidence score for citation extraction."""
        confidence = 0.3  # Base confidence

        # Author confidence
        if citation.authors:
            confidence += 0.2

        # Year confidence
        if citation.year:
            confidence += 0.2

        # Title confidence
        if citation.title:
            confidence += 0.15

        # Journal confidence
        if citation.journal:
            confidence += 0.1

        # DOI confidence
        if citation.doi:
            confidence += 0.1

        # Citation type confidence
        if citation.citation_type == "bibliography":
            confidence += 0.1
        elif citation.citation_type == "in_text":
            confidence += 0.05

        return min(confidence, 1.0)

    def _remove_duplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Remove duplicate citations based on text similarity."""
        unique_citations = []
        seen_texts = set()

        for citation in citations:
            # Normalize text for comparison
            normalized_text = re.sub(r"\s+", " ", citation.text.lower().strip())

            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_citations.append(citation)

        return unique_citations

    def format_citations(
        self, bibliography: Bibliography, format_type: str = "markdown"
    ) -> str:
        """Format citations in specified format."""
        if format_type == "bibtex":
            return bibliography.to_bibtex()
        elif format_type == "markdown":
            return bibliography.to_markdown()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def get_citation_statistics(self, bibliography: Bibliography) -> Dict[str, Any]:
        """Get statistics about extracted citations."""
        if not bibliography.citations:
            return {"total_citations": 0}

        stats = {
            "total_citations": len(bibliography.citations),
            "citation_types": {},
            "pages_with_citations": len(
                set(
                    c.page_number
                    for c in bibliography.citations
                    if c.page_number is not None
                )
            ),
            "citations_with_authors": sum(
                1 for c in bibliography.citations if c.authors
            ),
            "citations_with_years": sum(1 for c in bibliography.citations if c.year),
            "citations_with_titles": sum(1 for c in bibliography.citations if c.title),
            "citations_with_dois": sum(1 for c in bibliography.citations if c.doi),
            "average_confidence": sum(c.confidence for c in bibliography.citations)
            / len(bibliography.citations),
        }

        # Citation type distribution
        for citation in bibliography.citations:
            citation_type = citation.citation_type
            stats["citation_types"][citation_type] = (
                stats["citation_types"].get(citation_type, 0) + 1
            )

        return stats


# Global citation processor instance
citation_processor = CitationProcessor()
