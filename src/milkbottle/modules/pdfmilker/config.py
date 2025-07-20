"""PDFmilker configuration management."""

import os
from typing import Any, Dict, Optional

from milkbottle.config import get_config


class PDFmilkerConfig:
    """Configuration for PDFmilker services."""

    def __init__(self):
        self.core_config = get_config()
        self.pdfmilker_config = self.core_config.get_bottle_config("pdfmilker")

    def get_grobid_url(self) -> Optional[str]:
        """Get Grobid server URL."""
        return (
            self.pdfmilker_config.get("grobid_url")
            or os.getenv("GROBID_URL")
            or "http://localhost:8070"
        )

    def get_mathpix_credentials(self) -> Optional[Dict[str, str]]:
        """Get Mathpix API credentials."""
        app_id = self.pdfmilker_config.get("mathpix_app_id") or os.getenv(
            "MATHPIX_APP_ID"
        )
        app_key = self.pdfmilker_config.get("mathpix_app_key") or os.getenv(
            "MATHPIX_APP_KEY"
        )

        return {"app_id": app_id, "app_key": app_key} if app_id and app_key else None

    def get_pandoc_path(self) -> Optional[str]:
        """Get Pandoc executable path."""
        return (
            self.pdfmilker_config.get("pandoc_path")
            or os.getenv("PANDOC_PATH")
            or "pandoc"
        )

    def is_grobid_enabled(self) -> bool:
        """Check if Grobid is enabled."""
        return self.pdfmilker_config.get("enable_grobid", True)

    def is_mathpix_enabled(self) -> bool:
        """Check if Mathpix is enabled."""
        return self.pdfmilker_config.get("enable_mathpix", True)

    def is_pandoc_enabled(self) -> bool:
        """Check if Pandoc is enabled."""
        return self.pdfmilker_config.get("enable_pandoc", True)

    def get_enhanced_fallback(self) -> bool:
        """Check if enhanced fallback is enabled."""
        return self.pdfmilker_config.get("enhanced_fallback", True)

    def get_output_format(self) -> str:
        """Get output format preference."""
        return self.pdfmilker_config.get("output_format", "markdown")

    def get_math_format(self) -> str:
        """Get math formatting preference."""
        return self.pdfmilker_config.get("math_format", "latex")

    # New batch processing configuration methods
    def is_batch_mode_enabled(self) -> bool:
        """Check if batch mode is enabled."""
        return self.pdfmilker_config.get("batch_mode", True)

    def is_parallel_processing_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        return self.pdfmilker_config.get("parallel_processing", True)

    def get_max_workers(self) -> int:
        """Get maximum number of parallel workers."""
        return self.pdfmilker_config.get("max_workers", 4)

    def get_memory_limit_mb(self) -> int:
        """Get memory limit in MB."""
        return self.pdfmilker_config.get("memory_limit_mb", 2048)

    # New quality assessment configuration methods
    def is_quality_assessment_enabled(self) -> bool:
        """Check if quality assessment is enabled."""
        return self.pdfmilker_config.get("enable_quality_assessment", True)

    def get_quality_threshold(self) -> float:
        """Get quality threshold for warnings."""
        return self.pdfmilker_config.get("quality_threshold", 0.7)

    def get_min_text_length(self) -> int:
        """Get minimum text length for quality assessment."""
        return self.pdfmilker_config.get("min_text_length", 100)

    # New format export configuration methods
    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats."""
        return self.pdfmilker_config.get(
            "supported_formats", ["markdown", "html", "latex", "json", "docx"]
        )

    def get_default_template_path(self) -> Optional[str]:
        """Get default template path for exports."""
        return self.pdfmilker_config.get("default_template_path")

    # New progress tracking configuration methods
    def is_progress_tracking_enabled(self) -> bool:
        """Check if progress tracking is enabled."""
        return self.pdfmilker_config.get("show_progress", True)

    def get_progress_update_interval(self) -> float:
        """Get progress update interval in seconds."""
        return self.pdfmilker_config.get("progress_update_interval", 0.5)

    # New error handling configuration methods
    def get_max_retries(self) -> int:
        """Get maximum number of retries for failed operations."""
        return self.pdfmilker_config.get("max_retries", 3)

    def get_retry_delay(self) -> float:
        """Get delay between retries in seconds."""
        return self.pdfmilker_config.get("retry_delay", 1.0)

    def is_partial_result_recovery_enabled(self) -> bool:
        """Check if partial result recovery is enabled."""
        return self.pdfmilker_config.get("partial_result_recovery", True)

    # Configuration validation methods
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate all configuration settings."""
        return {
            "grobid_url": self._validate_grobid_url(),
            "mathpix_credentials": self._validate_mathpix_credentials(),
            "pandoc_path": self._validate_pandoc_path(),
            "batch_settings": self._validate_batch_settings(),
            "quality_settings": self._validate_quality_settings(),
        }

    def _validate_grobid_url(self) -> bool:
        """Validate Grobid URL configuration."""
        if not self.is_grobid_enabled():
            return True  # Not required if disabled

        grobid_url = self.get_grobid_url()
        return grobid_url is not None and grobid_url.startswith(("http://", "https://"))

    def _validate_mathpix_credentials(self) -> bool:
        """Validate Mathpix credentials configuration."""
        if not self.is_mathpix_enabled():
            return True  # Not required if disabled

        credentials = self.get_mathpix_credentials()
        return (
            credentials is not None
            and "app_id" in credentials
            and "app_key" in credentials
        )

    def _validate_pandoc_path(self) -> bool:
        """Validate Pandoc path configuration."""
        if not self.is_pandoc_enabled():
            return True  # Not required if disabled

        pandoc_path = self.get_pandoc_path()
        return pandoc_path is not None and len(pandoc_path) > 0

    def _validate_batch_settings(self) -> bool:
        """Validate batch processing settings."""
        max_workers = self.get_max_workers()
        memory_limit = self.get_memory_limit_mb()

        return 1 <= max_workers <= 16 and 512 <= memory_limit <= 8192

    def _validate_quality_settings(self) -> bool:
        """Validate quality assessment settings."""
        quality_threshold = self.get_quality_threshold()
        min_text_length = self.get_min_text_length()

        return 0.0 <= quality_threshold <= 1.0 and min_text_length > 0

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of all configuration settings."""
        return {
            "services": {
                "grobid_enabled": self.is_grobid_enabled(),
                "grobid_url": self.get_grobid_url(),
                "mathpix_enabled": self.is_mathpix_enabled(),
                "pandoc_enabled": self.is_pandoc_enabled(),
                "pandoc_path": self.get_pandoc_path(),
            },
            "processing": {
                "enhanced_fallback": self.get_enhanced_fallback(),
                "output_format": self.get_output_format(),
                "math_format": self.get_math_format(),
            },
            "batch_processing": {
                "batch_mode": self.is_batch_mode_enabled(),
                "parallel_processing": self.is_parallel_processing_enabled(),
                "max_workers": self.get_max_workers(),
                "memory_limit_mb": self.get_memory_limit_mb(),
            },
            "quality_assessment": {
                "enabled": self.is_quality_assessment_enabled(),
                "quality_threshold": self.get_quality_threshold(),
                "min_text_length": self.get_min_text_length(),
            },
            "progress_tracking": {
                "enabled": self.is_progress_tracking_enabled(),
                "update_interval": self.get_progress_update_interval(),
            },
            "error_handling": {
                "max_retries": self.get_max_retries(),
                "retry_delay": self.get_retry_delay(),
                "partial_result_recovery": self.is_partial_result_recovery_enabled(),
            },
        }


# Global config instance
pdfmilker_config = PDFmilkerConfig()
