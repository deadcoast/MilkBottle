"""Advanced Analytics System for MilkBottle.

This module provides machine learning-based quality assessment and advanced analytics
for content extraction and processing, including text quality analysis, content
classification, and predictive insights.
"""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for content analysis."""

    readability_score: float
    coherence_score: float
    completeness_score: float
    accuracy_score: float
    relevance_score: float
    overall_score: float
    confidence: float
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ContentClassification:
    """Content classification results."""

    document_type: str
    subject_area: str
    complexity_level: str
    target_audience: str
    language: str
    confidence: float
    tags: List[str] = field(default_factory=list)


@dataclass
class PredictiveInsights:
    """Predictive insights for content."""

    processing_time_prediction: float
    quality_improvement_potential: float
    recommended_formats: List[str]
    optimization_suggestions: List[str]
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class AnalyticsResult:
    """Complete analytics result."""

    quality_metrics: QualityMetrics
    classification: ContentClassification
    insights: PredictiveInsights
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


class AdvancedAnalytics:
    """Advanced analytics system with ML-based quality assessment."""

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the advanced analytics system."""
        self.model_path = model_path or Path("models/analytics_model.pkl")
        self.models = {}
        self.feature_extractors = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        """Initialize ML models and feature extractors."""
        try:
            # Initialize feature extractors
            self.feature_extractors = {
                "text_features": self._extract_text_features,
                "structural_features": self._extract_structural_features,
                "semantic_features": self._extract_semantic_features,
                "statistical_features": self._extract_statistical_features,
            }

            # Load pre-trained models if available
            if self.model_path.exists():
                self._load_models()
            else:
                self._initialize_default_models()

        except Exception as e:
            logger.warning(f"Could not initialize advanced models: {e}")
            self._initialize_fallback_models()

    def _load_models(self) -> None:
        """Load pre-trained models from file."""
        try:
            with open(self.model_path, "rb") as f:
                self.models = pickle.load(f)
            console.print(
                f"[green]Loaded analytics models from {self.model_path}[/green]"
            )
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """Initialize default rule-based models."""
        self.models = {
            "quality_assessor": self._rule_based_quality_assessment,
            "classifier": self._rule_based_classification,
            "predictor": self._rule_based_prediction,
        }
        console.print("[yellow]Using rule-based analytics models[/yellow]")

    def _initialize_fallback_models(self) -> None:
        """Initialize fallback models when ML is not available."""
        self.models = {
            "quality_assessor": self._basic_quality_assessment,
            "classifier": self._basic_classification,
            "predictor": self._basic_prediction,
        }
        console.print("[red]Using basic analytics models[/red]")

    def analyze_content(self, content_data: Dict[str, Any]) -> AnalyticsResult:
        """Perform comprehensive content analysis."""
        console.print("\n[bold underline]Advanced Content Analysis[/bold underline]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Extract features
            task1 = progress.add_task("Extracting features...", total=None)
            features = self._extract_all_features(content_data)
            progress.update(task1, completed=True)

            # Assess quality
            task2 = progress.add_task("Assessing quality...", total=None)
            quality_metrics = self._assess_quality(features, content_data)
            progress.update(task2, completed=True)

            # Classify content
            task3 = progress.add_task("Classifying content...", total=None)
            classification = self._classify_content(features, content_data)
            progress.update(task3, completed=True)

            # Generate insights
            task4 = progress.add_task("Generating insights...", total=None)
            insights = self._generate_insights(
                features, quality_metrics, classification
            )
            progress.update(task4, completed=True)

        return AnalyticsResult(
            quality_metrics=quality_metrics,
            classification=classification,
            insights=insights,
            metadata={"features": features},
        )

    def _extract_all_features(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all features from content data."""
        features = {}

        for feature_type, extractor in self.feature_extractors.items():
            try:
                features[feature_type] = extractor(content_data)
            except Exception as e:
                logger.warning(f"Failed to extract {feature_type}: {e}")
                features[feature_type] = {}

        return features

    def _extract_text_features(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text-based features."""
        features = {}

        pages = content_data.get("pages", [])
        all_text = "".join(page.get("text", "") + " " for page in pages)
        if all_text.strip():
            # Basic text statistics
            words = all_text.split()
            sentences = all_text.split(".")

            features.update(
                {
                    "word_count": len(words),
                    "sentence_count": len([s for s in sentences if s.strip()]),
                    "avg_sentence_length": len(words)
                    / max(len([s for s in sentences if s.strip()]), 1),
                    "avg_word_length": (
                        np.mean([len(word) for word in words]) if words else 0
                    ),
                    "unique_words": len(set(words)),
                    "vocabulary_richness": len(set(words)) / max(len(words), 1),
                    "text_length": len(all_text),
                }
            )

        return features

    def _extract_structural_features(
        self, content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract structural features."""
        features = {}

        features.update(
            {
                "has_title": bool(content_data.get("title")),
                "has_abstract": bool(content_data.get("abstract")),
                "page_count": len(content_data.get("pages", [])),
                "table_count": len(content_data.get("tables", [])),
                "image_count": len(content_data.get("images", [])),
                "math_formula_count": len(content_data.get("math_formulas", [])),
                "citation_count": len(content_data.get("citations", [])),
                "has_toc": bool(content_data.get("table_of_contents")),
                "has_bibliography": bool(content_data.get("bibliography")),
            }
        )

        return features

    def _extract_semantic_features(
        self, content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract semantic features."""
        features = {}

        # Simple keyword analysis
        title = content_data.get("title", "").lower()
        abstract = content_data.get("abstract", "").lower()

        # Academic indicators
        academic_keywords = [
            "research",
            "study",
            "analysis",
            "method",
            "results",
            "conclusion",
        ]
        technical_keywords = [
            "algorithm",
            "system",
            "model",
            "framework",
            "implementation",
        ]
        business_keywords = [
            "strategy",
            "market",
            "business",
            "management",
            "organization",
        ]

        features.update(
            {
                "academic_score": sum(
                    word in title or word in abstract for word in academic_keywords
                ),
                "technical_score": sum(
                    word in title or word in abstract for word in technical_keywords
                ),
                "business_score": sum(
                    word in title or word in abstract for word in business_keywords
                ),
                "has_abstract": bool(abstract),
                "title_length": len(title.split()),
            }
        )

        return features

    def _extract_statistical_features(
        self, content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract statistical features."""
        features = {}

        # Content distribution
        pages = content_data.get("pages", [])
        if pages:
            page_lengths = [len(page.get("text", "")) for page in pages]
            features.update(
                {
                    "avg_page_length": np.mean(page_lengths),
                    "page_length_std": np.std(page_lengths),
                    "page_length_variance": np.var(page_lengths),
                    "max_page_length": max(page_lengths),
                    "min_page_length": min(page_lengths),
                }
            )

        # Metadata statistics
        features.update(
            {
                "metadata_completeness": len([k for k, v in content_data.items() if v])
                / max(len(content_data), 1),
                "file_size": content_data.get("metadata", {}).get("file_size", 0),
                "extraction_time": content_data.get("metadata", {}).get(
                    "extraction_time", 0
                ),
            }
        )

        return features

    def _assess_quality(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> QualityMetrics:
        """Assess content quality using ML or rule-based methods."""
        if "quality_assessor" in self.models:
            return self.models["quality_assessor"](features, content_data)
        else:
            return self._basic_quality_assessment(features, content_data)

    def _rule_based_quality_assessment(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> QualityMetrics:
        """Rule-based quality assessment."""
        text_features = features.get("text_features", {})
        structural_features = features.get("structural_features", {})

        # Readability score
        avg_sentence_length = text_features.get("avg_sentence_length", 0)
        avg_word_length = text_features.get("avg_word_length", 0)
        readability_score = max(
            0, min(1, 1 - (avg_sentence_length - 15) / 30 - (avg_word_length - 5) / 10)
        )

        # Coherence score
        vocabulary_richness = text_features.get("vocabulary_richness", 0)
        coherence_score = min(1, vocabulary_richness * 2)

        # Completeness score
        has_title = structural_features.get("has_title", False)
        has_abstract = structural_features.get("has_abstract", False)
        page_count = structural_features.get("page_count", 0)
        completeness_score = (has_title + has_abstract + min(page_count / 10, 1)) / 3

        # Accuracy score (based on structural completeness)
        accuracy_score = structural_features.get("metadata_completeness", 0)

        # Relevance score
        relevance_score = 0.8  # Default high relevance

        # Overall score
        overall_score = (
            readability_score
            + coherence_score
            + completeness_score
            + accuracy_score
            + relevance_score
        ) / 5

        # Confidence
        confidence = min(1, overall_score * 1.2)

        # Recommendations
        recommendations = []
        if readability_score < 0.7:
            recommendations.append("Consider simplifying sentence structure")
        if coherence_score < 0.6:
            recommendations.append("Improve vocabulary diversity")
        if completeness_score < 0.8:
            recommendations.append("Add missing structural elements")

        # Warnings
        warnings = []
        if page_count < 2:
            warnings.append("Very short document")
        if avg_sentence_length > 25:
            warnings.append("Complex sentence structure detected")

        return QualityMetrics(
            readability_score=readability_score,
            coherence_score=coherence_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            overall_score=overall_score,
            confidence=confidence,
            recommendations=recommendations,
            warnings=warnings,
        )

    def _basic_quality_assessment(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> QualityMetrics:
        """Basic quality assessment fallback."""
        return QualityMetrics(
            readability_score=0.7,
            coherence_score=0.7,
            completeness_score=0.7,
            accuracy_score=0.7,
            relevance_score=0.7,
            overall_score=0.7,
            confidence=0.5,
            recommendations=["Enable advanced analytics for detailed assessment"],
            warnings=[],
        )

    def _classify_content(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> ContentClassification:
        """Classify content using ML or rule-based methods."""
        if "classifier" in self.models:
            return self.models["classifier"](features, content_data)
        else:
            return self._basic_classification(features, content_data)

    def _rule_based_classification(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> ContentClassification:
        """Rule-based content classification."""
        semantic_features = features.get("semantic_features", {})
        structural_features = features.get("structural_features", {})
        text_features = features.get("text_features", {})

        # Document type classification
        academic_score = semantic_features.get("academic_score", 0)
        technical_score = semantic_features.get("technical_score", 0)
        business_score = semantic_features.get("business_score", 0)

        if academic_score > max(technical_score, business_score):
            document_type = "Academic Paper"
        elif technical_score > business_score:
            document_type = "Technical Document"
        elif business_score > 0:
            document_type = "Business Document"
        else:
            document_type = "General Document"

        # Subject area
        if academic_score > 0:
            subject_area = "Academic/Research"
        elif technical_score > 0:
            subject_area = "Technology/Engineering"
        elif business_score > 0:
            subject_area = "Business/Management"
        else:
            subject_area = "General"

        # Complexity level
        avg_sentence_length = text_features.get("avg_sentence_length", 0)
        vocabulary_richness = text_features.get("vocabulary_richness", 0)

        if avg_sentence_length > 20 or vocabulary_richness > 0.8:
            complexity_level = "Advanced"
        elif avg_sentence_length > 15 or vocabulary_richness > 0.6:
            complexity_level = "Intermediate"
        else:
            complexity_level = "Basic"

        # Target audience
        if complexity_level == "Advanced":
            target_audience = "Experts/Researchers"
        elif complexity_level == "Intermediate":
            target_audience = "Professionals"
        else:
            target_audience = "General Public"

        # Language detection (simplified)
        language = "English"  # Default assumption

        # Tags
        tags = []
        if structural_features.get("has_abstract"):
            tags.append("has-abstract")
        if structural_features.get("table_count", 0) > 0:
            tags.append("contains-tables")
        if structural_features.get("image_count", 0) > 0:
            tags.append("contains-images")
        if structural_features.get("math_formula_count", 0) > 0:
            tags.append("contains-math")

        confidence = 0.8  # High confidence for rule-based classification

        return ContentClassification(
            document_type=document_type,
            subject_area=subject_area,
            complexity_level=complexity_level,
            target_audience=target_audience,
            language=language,
            confidence=confidence,
            tags=tags,
        )

    def _basic_classification(
        self, features: Dict[str, Any], content_data: Dict[str, Any]
    ) -> ContentClassification:
        """Basic classification fallback."""
        return ContentClassification(
            document_type="Unknown",
            subject_area="General",
            complexity_level="Unknown",
            target_audience="General",
            language="Unknown",
            confidence=0.3,
            tags=[],
        )

    def _generate_insights(
        self,
        features: Dict[str, Any],
        quality_metrics: QualityMetrics,
        classification: ContentClassification,
    ) -> PredictiveInsights:
        """Generate predictive insights."""
        if "predictor" in self.models:
            return self.models["predictor"](features, quality_metrics, classification)
        else:
            return self._basic_prediction(features, quality_metrics, classification)

    def _rule_based_prediction(
        self,
        features: Dict[str, Any],
        quality_metrics: QualityMetrics,
        classification: ContentClassification,
    ) -> PredictiveInsights:
        """Rule-based prediction generation."""
        text_features = features.get("text_features", {})
        structural_features = features.get("structural_features", {})

        # Processing time prediction
        word_count = text_features.get("word_count", 0)
        page_count = structural_features.get("page_count", 0)
        table_count = structural_features.get("table_count", 0)
        image_count = structural_features.get("image_count", 0)

        base_time = word_count * 0.001  # Base processing time
        table_time = table_count * 2.0  # Table processing overhead
        image_time = image_count * 1.5  # Image processing overhead
        processing_time_prediction = base_time + table_time + image_time

        # Quality improvement potential
        current_score = quality_metrics.overall_score
        improvement_potential = max(0, 1.0 - current_score)

        # Recommended formats
        recommended_formats = []
        if classification.document_type == "Academic Paper":
            recommended_formats.extend(["pdf", "latex", "markdown"])
        elif classification.document_type == "Technical Document":
            recommended_formats.extend(["html", "markdown", "pdf"])
        elif classification.document_type == "Business Document":
            recommended_formats.extend(["docx", "pdf", "html"])
        else:
            recommended_formats.extend(["txt", "json", "markdown"])

        # Optimization suggestions
        optimization_suggestions = []
        if quality_metrics.readability_score < 0.7:
            optimization_suggestions.append(
                "Simplify sentence structure for better readability"
            )
        if quality_metrics.completeness_score < 0.8:
            optimization_suggestions.append("Add missing structural elements")
        if structural_features.get("table_count", 0) > 5:
            optimization_suggestions.append("Consider breaking down large tables")

        # Risk factors
        risk_factors = []
        if page_count > 50:
            risk_factors.append(
                "Large document may require significant processing time"
            )
        if image_count > 20:
            risk_factors.append("High image count may impact export performance")
        if quality_metrics.overall_score < 0.6:
            risk_factors.append("Low quality content may affect export results")

        return PredictiveInsights(
            processing_time_prediction=processing_time_prediction,
            quality_improvement_potential=improvement_potential,
            recommended_formats=recommended_formats,
            optimization_suggestions=optimization_suggestions,
            risk_factors=risk_factors,
        )

    def _basic_prediction(
        self,
        features: Dict[str, Any],
        quality_metrics: QualityMetrics,
        classification: ContentClassification,
    ) -> PredictiveInsights:
        """Basic prediction fallback."""
        return PredictiveInsights(
            processing_time_prediction=1.0,
            quality_improvement_potential=0.3,
            recommended_formats=["txt", "json"],
            optimization_suggestions=[
                "Enable advanced analytics for detailed insights"
            ],
            risk_factors=[],
        )

    def display_analytics_results(self, result: AnalyticsResult) -> None:
        """Display analytics results in a user-friendly format."""
        console.print("\n[bold underline]Advanced Analytics Results[/bold underline]")

        # Quality Metrics
        quality_panel = Panel(
            f"Overall Score: [bold green]{result.quality_metrics.overall_score:.2f}[/bold green]\n"
            f"Confidence: [bold blue]{result.quality_metrics.confidence:.2f}[/bold blue]\n\n"
            f"Readability: {result.quality_metrics.readability_score:.2f}\n"
            f"Coherence: {result.quality_metrics.coherence_score:.2f}\n"
            f"Completeness: {result.quality_metrics.completeness_score:.2f}\n"
            f"Accuracy: {result.quality_metrics.accuracy_score:.2f}\n"
            f"Relevance: {result.quality_metrics.relevance_score:.2f}",
            title="[bold]Quality Assessment[/bold]",
            border_style="green",
        )
        console.print(quality_panel)

        # Content Classification
        classification_panel = Panel(
            f"Document Type: [bold]{result.classification.document_type}[/bold]\n"
            f"Subject Area: {result.classification.subject_area}\n"
            f"Complexity Level: {result.classification.complexity_level}\n"
            f"Target Audience: {result.classification.target_audience}\n"
            f"Language: {result.classification.language}\n"
            f"Confidence: {result.classification.confidence:.2f}\n\n"
            f"Tags: {', '.join(result.classification.tags) if result.classification.tags else 'None'}",
            title="[bold]Content Classification[/bold]",
            border_style="blue",
        )
        console.print(classification_panel)

        # Predictive Insights
        insights_panel = Panel(
            f"Processing Time: [bold yellow]{result.insights.processing_time_prediction:.2f}s[/bold yellow]\n"
            f"Improvement Potential: {result.insights.quality_improvement_potential:.2f}\n\n"
            f"Recommended Formats: {', '.join(result.insights.recommended_formats)}\n\n"
            f"Optimization Suggestions:\n"
            + "\n".join(
                f"• {suggestion}"
                for suggestion in result.insights.optimization_suggestions
            )
            + (
                "\n\nRisk Factors:\n"
                + "\n".join(f"⚠️ {risk}" for risk in result.insights.risk_factors)
                if result.insights.risk_factors
                else ""
            ),
            title="[bold]Predictive Insights[/bold]",
            border_style="yellow",
        )
        console.print(insights_panel)

        # Recommendations and Warnings
        if result.quality_metrics.recommendations or result.quality_metrics.warnings:
            console.print("\n[bold]Recommendations & Warnings[/bold]")

        if result.quality_metrics.recommendations:
            console.print("\n[bold green]Recommendations:[/bold green]")
            for rec in result.quality_metrics.recommendations:
                console.print(f"• {rec}")

        if result.quality_metrics.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in result.quality_metrics.warnings:
                console.print(f"⚠️ {warning}")


def get_advanced_analytics(model_path: Optional[Path] = None) -> AdvancedAnalytics:
    """Get the global advanced analytics instance."""
    return AdvancedAnalytics(model_path)


def analyze_content_advanced(
    content_data: Dict[str, Any], model_path: Optional[Path] = None
) -> AnalyticsResult:
    """Perform advanced content analysis."""
    analytics = get_advanced_analytics(model_path)
    return analytics.analyze_content(content_data)


if __name__ == "__main__":
    # Example usage
    sample_content = {
        "title": "Advanced Analytics in Content Processing",
        "abstract": "This paper presents a comprehensive analysis of advanced analytics techniques for content processing and quality assessment.",
        "pages": [
            {
                "text": "Introduction to advanced analytics and its applications in content processing."
            },
            {"text": "Methodology and implementation details of the analytics system."},
            {"text": "Results and evaluation of the proposed approach."},
        ],
        "tables": [{"data": "sample table"}],
        "images": [{"path": "sample.jpg"}],
        "metadata": {"file_size": 1024000, "extraction_time": 2.5},
    }

    result = analyze_content_advanced(sample_content)
    analytics = get_advanced_analytics()
    analytics.display_analytics_results(result)
