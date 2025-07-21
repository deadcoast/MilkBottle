"""PDFmilker enhanced image processing with figure detection and caption extraction."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

from .errors import PDFMilkerError

logger = logging.getLogger("pdfmilker.image_processor")


class Figure:
    """Represents a figure with its metadata and content."""

    def __init__(self, page_number: int, bbox: Tuple[float, float, float, float]):
        self.page_number = page_number
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.image_path: Optional[Path] = None
        self.caption: Optional[str] = None
        self.figure_number: Optional[str] = None
        self.confidence: float = 0.0
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.file_size: Optional[int] = None
        self.format: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert figure to dictionary representation."""
        return {
            "page_number": self.page_number,
            "bbox": self.bbox,
            "image_path": str(self.image_path) if self.image_path else None,
            "caption": self.caption,
            "figure_number": self.figure_number,
            "confidence": self.confidence,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "format": self.format,
        }


class ImageProcessor:
    """Enhanced image processor with figure detection and caption extraction."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("extracted_images")
        self.min_image_size = 100  # Minimum width/height in pixels
        self.max_image_size = 5000  # Maximum width/height in pixels
        self.supported_formats = ["png", "jpg", "jpeg", "tiff", "bmp"]
        self.caption_patterns = [
            r"Figure\s+(\d+)[:\.]\s*(.+)",
            r"Fig\.\s+(\d+)[:\.]\s*(.+)",
            r"(\d+)\.\s*(.+)",  # Numbered captions
            r"([A-Z][^.!?]*[.!?])",  # Sentence starting with capital letter
        ]

    def extract_figures_with_captions(self, pdf_path: Path) -> List[Figure]:
        """
        Extract figures with captions from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of Figure objects with metadata
        """
        try:
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            figures = []
            doc = fitz.Document(str(pdf_path))

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract images from page
                page_figures = self._extract_images_from_page(page, page_num, pdf_path)
                figures.extend(page_figures)

                # Extract captions from page text
                captions = self._extract_captions_from_page(page, page_num)

                # Match figures with captions
                self._match_figures_with_captions(page_figures, captions)

            doc.close()

            # Post-process figures
            self._post_process_figures(figures)

            logger.info(f"Extracted {len(figures)} figures from {pdf_path.name}")
            return figures

        except Exception as e:
            logger.error(f"Failed to extract figures from {pdf_path}: {e}")
            raise PDFMilkerError(f"Image extraction failed: {e}") from e

    def _extract_images_from_page(
        self, page: fitz.Page, page_num: int, pdf_path: Path
    ) -> List[Figure]:
        """Extract images from a single page."""
        figures = []

        try:
            # Get image list from page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Get image rectangle
                    img_rect = page.get_image_bbox(img)

                    if img_rect is None:
                        continue

                    # Check if image is large enough
                    if (
                        img_rect.width < self.min_image_size
                        or img_rect.height < self.min_image_size
                    ):
                        continue

                    # Create figure object
                    figure = Figure(
                        page_num, (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
                    )

                    # Extract and save image
                    self._extract_and_save_image(
                        page, img, figure, pdf_path, page_num, img_index
                    )

                    figures.append(figure)

                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} from page {page_num}: {e}"
                    )
                    continue

            return figures

        except Exception as e:
            logger.error(f"Failed to extract images from page {page_num}: {e}")
            return []

    def _extract_and_save_image(
        self,
        page: fitz.Page,
        img: Any,
        figure: Figure,
        pdf_path: Path,
        page_num: int,
        img_index: int,
    ) -> None:
        """Extract and save image to file."""
        try:
            # Get image data
            img_data = page.extract_image(img)

            if img_data is None:
                return

            # Determine image format
            img_format = img_data.get("ext", "png").lower()
            if img_format not in self.supported_formats:
                img_format = "png"

            # Create filename
            base_name = pdf_path.stem
            filename = f"{base_name}_page{page_num+1}_img{img_index+1}.{img_format}"
            image_path = self.output_dir / filename

            # Save image
            with open(image_path, "wb") as f:
                f.write(img_data["image"])

            # Get image metadata
            figure.image_path = image_path
            figure.format = img_format
            figure.file_size = image_path.stat().st_size

            # Get image dimensions
            try:
                with Image.open(image_path) as pil_image:
                    figure.width, figure.height = pil_image.size
            except Exception as e:
                logger.warning(f"Failed to get image dimensions: {e}")

            # Calculate confidence based on image quality
            figure.confidence = self._calculate_image_confidence(figure)

        except Exception as e:
            logger.error(f"Failed to save image: {e}")

    def _extract_captions_from_page(
        self, page: fitz.Page, page_num: int
    ) -> List[Dict[str, Any]]:
        """Extract potential captions from page text."""
        captions = []

        try:
            # Get text blocks with their positions
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    text = block.get("text", "").strip()
                    bbox = block.get("bbox", (0, 0, 0, 0))

                    if text and len(text) > 10:  # Minimum caption length
                        if caption_info := self._identify_caption(text, bbox):
                            caption_info["page_number"] = page_num
                            captions.append(caption_info)

            return captions

        except Exception as e:
            logger.error(f"Failed to extract captions from page {page_num}: {e}")
            return []

    def _identify_caption(
        self, text: str, bbox: Tuple[float, float, float, float]
    ) -> Optional[Dict[str, Any]]:
        """Identify if text is a caption and extract figure number."""
        for pattern in self.caption_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                if len(match.groups()) == 2:
                    figure_num = match[1]
                    caption_text = match[2].strip()
                else:
                    figure_num = None
                    caption_text = text.strip()

                return {
                    "text": caption_text,
                    "figure_number": figure_num,
                    "bbox": bbox,
                    "confidence": 0.8,
                }

        # Check for potential captions (shorter text, likely near images)
        if 10 <= len(text) <= 200 and text[0].isupper():
            return {
                "text": text,
                "figure_number": None,
                "bbox": bbox,
                "confidence": 0.4,
            }

        return None

    def _match_figures_with_captions(
        self, figures: List[Figure], captions: List[Dict[str, Any]]
    ) -> None:
        """Match figures with their captions based on proximity."""
        for figure in figures:
            best_caption = None
            best_distance = float("inf")

            for caption in captions:
                if caption["page_number"] != figure.page_number:
                    continue

                # Calculate distance between figure and caption
                distance = self._calculate_distance(figure.bbox, caption["bbox"])

                if (
                    distance < best_distance and distance < 200
                ):  # Max 200 points distance
                    best_distance = distance
                    best_caption = caption

            if best_caption:
                figure.caption = best_caption["text"]
                figure.figure_number = best_caption["figure_number"]
                figure.confidence = min(
                    figure.confidence + 0.2, 1.0
                )  # Boost confidence

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

    def _calculate_image_confidence(self, figure: Figure) -> float:
        """Calculate confidence score for image quality."""
        confidence = 0.5  # Base confidence

        # Size-based confidence
        if figure.width and figure.height:
            if figure.width >= 300 and figure.height >= 300:
                confidence += 0.2
            elif figure.width >= 100 and figure.height >= 100:
                confidence += 0.1

        # Format-based confidence
        if figure.format in ["png", "tiff"]:
            confidence += 0.1
        elif figure.format in ["jpg", "jpeg"]:
            confidence += 0.05

        # File size confidence (not too small, not too large)
        if figure.file_size:
            if 1000 <= figure.file_size <= 10000000:  # 1KB to 10MB
                confidence += 0.1
            elif figure.file_size < 1000:
                confidence -= 0.1

        return min(confidence, 1.0)

    def _post_process_figures(self, figures: List[Figure]) -> None:
        """Post-process extracted figures."""
        # Sort figures by page number and position
        figures.sort(key=lambda f: (f.page_number, f.bbox[1], f.bbox[0]))

        # Assign figure numbers if missing
        figure_counter = 1
        for figure in figures:
            if not figure.figure_number:
                figure.figure_number = str(figure_counter)
                figure_counter += 1

    def assess_image_quality(self, figure: Figure) -> Dict[str, Any]:
        """Assess the quality of an extracted image."""
        quality_metrics = {
            "resolution_score": 0.0,
            "format_score": 0.0,
            "size_score": 0.0,
            "overall_quality": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Resolution assessment
        if figure.width and figure.height:
            total_pixels = figure.width * figure.height
            if total_pixels >= 1000000:  # 1MP
                quality_metrics["resolution_score"] = 1.0
            elif total_pixels >= 100000:  # 100KP
                quality_metrics["resolution_score"] = 0.8
            elif total_pixels >= 10000:  # 10KP
                quality_metrics["resolution_score"] = 0.6
            else:
                quality_metrics["resolution_score"] = 0.3
                quality_metrics["issues"].append("Low resolution image")
        else:
            quality_metrics["issues"].append("Unable to determine image dimensions")

        # Format assessment
        if figure.format:
            if figure.format in ["png", "tiff"]:
                quality_metrics["format_score"] = 1.0
            elif figure.format in ["jpg", "jpeg"]:
                quality_metrics["format_score"] = 0.8
            else:
                quality_metrics["format_score"] = 0.5
                quality_metrics["issues"].append(f"Unsupported format: {figure.format}")

        # File size assessment
        if figure.file_size:
            if 10000 <= figure.file_size <= 5000000:  # 10KB to 5MB
                quality_metrics["size_score"] = 1.0
            elif figure.file_size < 10000:
                quality_metrics["size_score"] = 0.3
                quality_metrics["issues"].append("Very small file size")
            else:
                quality_metrics["size_score"] = 0.7
                quality_metrics["recommendations"].append(
                    "Consider compression for large file"
                )

        # Overall quality calculation
        quality_metrics["overall_quality"] = (
            quality_metrics["resolution_score"] * 0.4
            + quality_metrics["format_score"] * 0.3
            + quality_metrics["size_score"] * 0.3
        )

        # Add recommendations based on quality
        if quality_metrics["overall_quality"] < 0.6:
            quality_metrics["recommendations"].append(
                "Consider manual review of image quality"
            )

        return quality_metrics

    def get_image_statistics(self, figures: List[Figure]) -> Dict[str, Any]:
        """Get statistics about extracted images."""
        if not figures:
            return {"total_figures": 0}

        stats = {
            "total_figures": len(figures),
            "pages_with_figures": len({f.page_number for f in figures}),
            "total_file_size": sum(f.file_size or 0 for f in figures),
            "formats": {},
            "quality_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
            },
            "captions_extracted": sum(bool(f.caption) for f in figures),
            "figure_numbers_assigned": sum(bool(f.figure_number) for f in figures),
        }

        # Format distribution
        for figure in figures:
            if figure.format:
                stats["formats"][figure.format] = (
                    stats["formats"].get(figure.format, 0) + 1
                )

        # Quality distribution
        for figure in figures:
            quality = self.assess_image_quality(figure)
            overall_quality = quality["overall_quality"]

            if overall_quality >= 0.8:
                stats["quality_distribution"]["excellent"] += 1
            elif overall_quality >= 0.6:
                stats["quality_distribution"]["good"] += 1
            elif overall_quality >= 0.4:
                stats["quality_distribution"]["fair"] += 1
            else:
                stats["quality_distribution"]["poor"] += 1

        return stats


# Global image processor instance
image_processor = ImageProcessor()
