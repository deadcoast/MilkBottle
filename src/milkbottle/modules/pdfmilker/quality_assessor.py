"""Quality assessment system for PDFmilker.

This module provides comprehensive quality assessment capabilities for extracted
PDF content, including confidence scoring, quality metrics, and validation checks.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class QualityMetrics:
    """Quality metrics for extracted content."""

    overall_score: float = 0.0
    text_completeness: float = 0.0
    text_quality: float = 0.0
    math_accuracy: float = 0.0
    table_structure: float = 0.0
    image_quality: float = 0.0
    citation_accuracy: float = 0.0
    formatting_quality: float = 0.0
    confidence_level: str = "low"
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ContentValidation:
    """Content validation results."""

    is_valid: bool = False
    missing_sections: List[str] = field(default_factory=list)
    empty_sections: List[str] = field(default_factory=list)
    malformed_content: List[str] = field(default_factory=list)
    validation_score: float = 0.0


class QualityAssessor:
    """Comprehensive quality assessment for extracted PDF content."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the quality assessor.

        Args:
            config: Configuration dictionary for quality assessment
        """
        self.config = config or {}
        self.min_text_length = self.config.get("min_text_length", 100)
        self.quality_threshold = self.config.get("quality_threshold", 0.7)
        self.math_confidence_threshold = self.config.get(
            "math_confidence_threshold", 0.8
        )
        self.table_confidence_threshold = self.config.get(
            "table_confidence_threshold", 0.7
        )

    def assess_extraction_quality(
        self, original_pdf: Path, extracted_content: Dict[str, Any]
    ) -> QualityMetrics:
        """Assess the quality of extracted content.

        Args:
            original_pdf: Path to original PDF file
            extracted_content: Extracted content dictionary

        Returns:
            QualityMetrics object with assessment results
        """
        try:
            metrics = QualityMetrics()

            # Assess different aspects of quality
            metrics.text_completeness = self._assess_text_completeness(
                extracted_content
            )
            metrics.text_quality = self._assess_text_quality(extracted_content)
            metrics.math_accuracy = self._assess_math_accuracy(extracted_content)
            metrics.table_structure = self._assess_table_structure(extracted_content)
            metrics.image_quality = self._assess_image_quality(extracted_content)
            metrics.citation_accuracy = self._assess_citation_accuracy(
                extracted_content
            )
            metrics.formatting_quality = self._assess_formatting_quality(
                extracted_content
            )

            # Calculate overall score
            metrics.overall_score = self._calculate_overall_score(metrics)

            # Determine confidence level
            metrics.confidence_level = self._determine_confidence_level(
                metrics.overall_score
            )

            # Generate issues, warnings, and suggestions
            self._generate_assessment_feedback(metrics, extracted_content)

            logger.info(
                f"Quality assessment completed. Overall score: {metrics.overall_score:.2f}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return QualityMetrics(
                overall_score=0.0,
                confidence_level="error",
                issues=[f"Assessment failed: {str(e)}"],
            )

    def validate_content_structure(self, content: Dict[str, Any]) -> ContentValidation:
        """Validate the structure and completeness of extracted content.

        Args:
            content: Extracted content dictionary

        Returns:
            ContentValidation object with validation results
        """
        validation = ContentValidation()

        # Check for required sections
        required_sections = ["title", "body_text"]
        optional_sections = [
            "abstract",
            "math_formulas",
            "tables",
            "references",
            "images",
        ]

        all_sections = required_sections + optional_sections

        for section in all_sections:
            if section not in content:
                if section in required_sections:
                    validation.missing_sections.append(section)
                continue

            section_content = content[section]

            # Check if section is empty
            if self._is_section_empty(section_content):
                validation.empty_sections.append(section)

            # Check for malformed content
            if self._is_content_malformed(section_content, section):
                validation.malformed_content.append(section)

        # Calculate validation score
        validation.validation_score = self._calculate_validation_score(
            validation, len(all_sections)
        )
        validation.is_valid = validation.validation_score >= self.quality_threshold

        return validation

    def get_quality_report(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Generate a comprehensive quality report.

        Args:
            metrics: Quality metrics object

        Returns:
            Dictionary containing quality report
        """
        return {
            "summary": {
                "overall_score": metrics.overall_score,
                "confidence_level": metrics.confidence_level,
                "assessment_timestamp": self._get_timestamp(),
            },
            "detailed_metrics": {
                "text_completeness": metrics.text_completeness,
                "text_quality": metrics.text_quality,
                "math_accuracy": metrics.math_accuracy,
                "table_structure": metrics.table_structure,
                "image_quality": metrics.image_quality,
                "citation_accuracy": metrics.citation_accuracy,
                "formatting_quality": metrics.formatting_quality,
            },
            "issues": metrics.issues,
            "warnings": metrics.warnings,
            "suggestions": metrics.suggestions,
            "recommendations": self._generate_recommendations(metrics),
        }

    def _assess_text_completeness(self, content: Dict[str, Any]) -> float:
        """Assess the completeness of extracted text.

        Args:
            content: Extracted content

        Returns:
            Completeness score (0.0 to 1.0)
        """
        score = 0.0
        total_checks = 0

        # Check title presence
        if content.get("title"):
            title_length = len(content["title"].strip())
            if title_length > 0:
                score += 1.0
                if title_length > 10:
                    score += 0.5
            total_checks += 1.5

        # Check abstract presence
        if content.get("abstract"):
            abstract_length = len(content["abstract"].strip())
            if abstract_length > 0:
                score += 1.0
                if abstract_length > 50:
                    score += 0.5
            total_checks += 1.5

        # Check body text completeness
        if content.get("body_text"):
            body_length = len(content["body_text"].strip())
            if body_length > 0:
                score += 1.0
                if body_length > self.min_text_length:
                    score += 1.0
                if body_length > 1000:
                    score += 0.5
            total_checks += 2.5

        # Check for section headers
        body_text = content.get("body_text", "")
        section_headers = len(re.findall(r"^#{1,6}\s+", body_text, re.MULTILINE))
        if section_headers > 0:
            score += min(section_headers * 0.2, 1.0)
            total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_text_quality(self, content: Dict[str, Any]) -> float:
        """Assess the quality of extracted text.

        Args:
            content: Extracted content

        Returns:
            Text quality score (0.0 to 1.0)
        """
        score = 0.0
        total_checks = 0

        body_text = content.get("body_text", "")
        if not body_text:
            return 0.0

        # Check for proper sentence structure
        sentences = re.split(r"[.!?]+", body_text)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if valid_sentences:
            score += min(len(valid_sentences) / max(len(sentences), 1), 1.0)
        total_checks += 1.0

        if paragraphs := [p.strip() for p in body_text.split("\n\n") if p.strip()]:
            score += min(len(paragraphs) / 5, 1.0)  # Expect at least 5 paragraphs
        total_checks += 1.0

        # Check for proper capitalization
        words = body_text.split()
        capitalized_words = sum(bool(word and word[0].isupper()) for word in words)
        if words:
            capitalization_ratio = capitalized_words / len(words)
            score += min(capitalization_ratio, 1.0)
        total_checks += 1.0

        # Check for common OCR artifacts
        ocr_artifacts = len(re.findall(r"[|{}[\]\\]", body_text))
        if len(body_text) > 0:
            artifact_ratio = ocr_artifacts / len(body_text)
            score += max(0, 1.0 - artifact_ratio * 10)  # Penalize artifacts
        total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_math_accuracy(self, content: Dict[str, Any]) -> float:
        """Assess the accuracy of mathematical content.

        Args:
            content: Extracted content

        Returns:
            Math accuracy score (0.0 to 1.0)
        """
        math_formulas = content.get("math_formulas", [])
        if not math_formulas:
            return 0.0

        score = 0.0
        total_checks = 0

        for formula in math_formulas:
            formula_score = 0.0
            formula_checks = 0

            # Check for LaTeX content
            if formula.get("latex"):
                latex_content = formula["latex"]
                formula_score += 1.0

                # Check for balanced braces
                if latex_content.count("{") == latex_content.count("}"):
                    formula_score += 0.5

                # Check for common LaTeX patterns
                if re.search(r"\\[a-zA-Z]+", latex_content):
                    formula_score += 0.5

                formula_checks += 2.0

            # Check for confidence score
            if formula.get("confidence"):
                confidence = float(formula["confidence"])
                formula_score += min(confidence, 1.0)
                formula_checks += 1.0

            # Check for formula number
            if formula.get("number"):
                formula_score += 0.5
                formula_checks += 0.5

            if formula_checks > 0:
                score += formula_score / formula_checks
                total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_table_structure(self, content: Dict[str, Any]) -> float:
        """Assess the structure quality of extracted tables.

        Args:
            content: Extracted content

        Returns:
            Table structure score (0.0 to 1.0)
        """
        tables = content.get("tables", [])
        if not tables:
            return 0.0

        score = 0.0
        total_checks = 0

        for table in tables:
            table_score = 0.0
            table_checks = 0

            if isinstance(table, dict):
                if "rows" in table and table["rows"]:
                    table_score += 1.0
                    table_checks += 1.0

                if "headers" in table:
                    table_score += 0.5
                    table_checks += 0.5

                if "markdown" in table:
                    table_score += 0.5
                    table_checks += 0.5

                if table.get("confidence"):
                    confidence = float(table["confidence"])
                    table_score += min(confidence, 1.0)
                    table_checks += 1.0

            if table_checks > 0:
                score += table_score / table_checks
                total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_image_quality(self, content: Dict[str, Any]) -> float:
        """Assess the quality of extracted images.

        Args:
            content: Extracted content

        Returns:
            Image quality score (0.0 to 1.0)
        """
        images = content.get("images", [])
        if not images:
            return 0.0

        score = 0.0
        total_checks = 0

        for image in images:
            image_score = 0.0
            image_checks = 0

            # Check for image data
            if isinstance(image, dict):
                if image.get("path") or image.get("data"):
                    image_score += 1.0
                    image_checks += 1.0

                # Check for caption
                if image.get("caption"):
                    image_score += 0.5
                    image_checks += 0.5

                # Check for confidence score
                if image.get("confidence"):
                    confidence = float(image["confidence"])
                    image_score += min(confidence, 1.0)
                    image_checks += 1.0

            if image_checks > 0:
                score += image_score / image_checks
                total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_citation_accuracy(self, content: Dict[str, Any]) -> float:
        """Assess the accuracy of extracted citations.

        Args:
            content: Extracted content

        Returns:
            Citation accuracy score (0.0 to 1.0)
        """
        references = content.get("references", [])
        if not references:
            return 0.0

        score = 0.0
        total_checks = 0

        for ref in references:
            ref_score = 0.0
            ref_checks = 0

            # Check for reference content
            if ref and str(ref).strip() != "":
                ref_score += 1.0
                ref_checks += 1.0

                # Check for author pattern
                if re.search(r"[A-Z][a-z]+\s+[A-Z]", str(ref)):
                    ref_score += 0.5
                    ref_checks += 0.5

                # Check for year pattern
                if re.search(r"\b(19|20)\d{2}\b", str(ref)):
                    ref_score += 0.5
                    ref_checks += 0.5

            if ref_checks > 0:
                score += ref_score / ref_checks
                total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _assess_formatting_quality(self, content: Dict[str, Any]) -> float:
        """Assess the overall formatting quality.

        Args:
            content: Extracted content

        Returns:
            Formatting quality score (0.0 to 1.0)
        """
        score = 0.0
        total_checks = 0

        # Check for consistent formatting
        body_text = content.get("body_text", "")
        if body_text:
            # Check for proper line breaks
            lines = body_text.split("\n")
            if non_empty_lines := [line.strip() for line in lines if line.strip()]:
                score += min(len(non_empty_lines) / max(len(lines), 1), 1.0)
            total_checks += 1.0

            # Check for proper spacing
            double_spaces = body_text.count("  ")
            if len(body_text) > 0:
                spacing_ratio = double_spaces / len(body_text)
                score += max(0, 1.0 - spacing_ratio * 5)  # Penalize excessive spacing
            total_checks += 1.0

        # Check for section organization
        sections = [
            "title",
            "abstract",
            "body_text",
            "math_formulas",
            "tables",
            "references",
        ]
        present_sections = sum(bool(content.get(section)) for section in sections)
        score += min(present_sections / len(sections), 1.0)
        total_checks += 1.0

        return score / total_checks if total_checks > 0 else 0.0

    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score from individual metrics.

        Args:
            metrics: Quality metrics object

        Returns:
            Overall score (0.0 to 1.0)
        """
        weights = {
            "text_completeness": 0.25,
            "text_quality": 0.20,
            "math_accuracy": 0.15,
            "table_structure": 0.10,
            "image_quality": 0.10,
            "citation_accuracy": 0.10,
            "formatting_quality": 0.10,
        }

        score = 0.0
        total_weight = 0.0

        for metric_name, weight in weights.items():
            metric_value = getattr(metrics, metric_name, 0.0)
            score += metric_value * weight
            total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def _determine_confidence_level(self, score: float) -> str:
        """Determine confidence level based on quality score.

        Args:
            score: Quality score (0.0 to 1.0)

        Returns:
            Confidence level string
        """
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "high"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "moderate"
        elif score >= 0.3:
            return "low"
        else:
            return "poor"

    def _generate_assessment_feedback(
        self, metrics: QualityMetrics, content: Dict[str, Any]
    ) -> None:
        """Generate feedback based on assessment results.

        Args:
            metrics: Quality metrics object
            content: Extracted content
        """
        # Generate issues for low scores
        if metrics.text_completeness < 0.5:
            metrics.issues.append("Text extraction appears incomplete")

        if metrics.text_quality < 0.5:
            metrics.issues.append("Text quality is poor, may contain OCR artifacts")

        if metrics.math_accuracy < 0.5:
            metrics.issues.append("Mathematical formulas may be incorrectly extracted")

        if metrics.table_structure < 0.5:
            metrics.issues.append("Table structure may be malformed")

        # Generate warnings for moderate scores
        if 0.5 <= metrics.text_completeness < 0.7:
            metrics.warnings.append("Text completeness could be improved")

        if 0.5 <= metrics.text_quality < 0.7:
            metrics.warnings.append("Text quality could be improved")

        # Generate suggestions for improvement
        if not content.get("abstract"):
            metrics.suggestions.append(
                "Consider extracting abstract for better completeness"
            )

        if not content.get("references"):
            metrics.suggestions.append(
                "Consider extracting references for academic papers"
            )

        if not content.get("math_formulas"):
            metrics.suggestions.append(
                "Consider enabling math extraction for scientific papers"
            )

    def _is_section_empty(self, section_content: Any) -> bool:
        """Check if a section is empty.

        Args:
            section_content: Content of a section

        Returns:
            True if section is empty
        """
        if not section_content:
            return True

        if isinstance(section_content, str):
            return len(section_content.strip()) == 0

        if isinstance(section_content, list):
            return len(section_content) == 0

        if isinstance(section_content, dict):
            return len(section_content) == 0

        return False

    def _is_content_malformed(self, content: Any, section_name: str) -> bool:
        """Check if content is malformed.

        Args:
            content: Content to check
            section_name: Name of the section

        Returns:
            True if content is malformed
        """
        if section_name == "math_formulas":
            if isinstance(content, list):
                for formula in content:
                    if not isinstance(formula, dict) or not formula.get("latex"):
                        return True

        elif section_name == "tables":
            if isinstance(content, list):
                for table in content:
                    if not isinstance(table, dict) or not table.get("rows"):
                        return True

        elif section_name == "references":
            if isinstance(content, list):
                for ref in content:
                    if not ref or len(str(ref).strip()) < 10:
                        return True

        return False

    def _calculate_validation_score(
        self, validation: ContentValidation, total_sections: int
    ) -> float:
        """Calculate validation score.

        Args:
            validation: Content validation object
            total_sections: Total number of sections

        Returns:
            Validation score (0.0 to 1.0)
        """
        if total_sections == 0:
            return 0.0

        # Penalize missing and empty sections
        penalty = (
            len(validation.missing_sections) + len(validation.empty_sections)
        ) / total_sections

        # Penalize malformed content
        malformed_penalty = len(validation.malformed_content) / total_sections

        return max(0.0, 1.0 - penalty - malformed_penalty)

    def _generate_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """Generate improvement recommendations.

        Args:
            metrics: Quality metrics object

        Returns:
            List of recommendations
        """
        recommendations = []

        if metrics.overall_score < 0.7:
            recommendations.append("Consider using enhanced extraction methods")

        if metrics.text_completeness < 0.7:
            recommendations.append(
                "Enable full-text extraction for better completeness"
            )

        if metrics.math_accuracy < 0.7:
            recommendations.append(
                "Enable Mathpix integration for better math extraction"
            )

        if metrics.table_structure < 0.7:
            recommendations.append(
                "Enable advanced table extraction for better structure"
            )

        if metrics.citation_accuracy < 0.7:
            recommendations.append(
                "Enable Grobid integration for better citation extraction"
            )

        return recommendations

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().isoformat()


# Global quality assessor instance
quality_assessor = QualityAssessor()
