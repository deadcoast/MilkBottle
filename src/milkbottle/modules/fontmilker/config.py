"""Fontmilker configuration module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FontmilkerConfig:
    """Fontmilker configuration."""

    enabled: bool = True
    dry_run: bool = False
    verbose: bool = False
    output_dir: str = "fonts"
    extract_formats: List[str] = field(
        default_factory=lambda: ["ttf", "otf", "woff", "woff2"]
    )
    analyze_fonts: bool = True
    convert_fonts: bool = False
    optimize_fonts: bool = False
    validate_fonts: bool = True
    interactive: bool = True
    log_level: str = "info"

    # Font processing options
    supported_formats: List[str] = field(
        default_factory=lambda: ["ttf", "otf", "woff", "woff2"]
    )
    output_formats: List[str] = field(default_factory=lambda: ["woff2", "woff", "ttf"])
    optimization_level: int = 2
    subset_text: Optional[str] = None
    font_display: str = "swap"
    preload_fonts: bool = True

    def __post_init__(self):
        if self.extract_formats is None:
            self.extract_formats = ["ttf", "otf", "woff", "woff2"]

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "output_dir": self.output_dir,
            "extract_formats": self.extract_formats,
            "analyze_fonts": self.analyze_fonts,
            "convert_fonts": self.convert_fonts,
            "optimize_fonts": self.optimize_fonts,
            "validate_fonts": self.validate_fonts,
            "interactive": self.interactive,
            "log_level": self.log_level,
        }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    try:
        # Check required fields
        if "enabled" not in config:
            return False

        # Check boolean fields
        boolean_fields = [
            "enabled",
            "dry_run",
            "verbose",
            "analyze_fonts",
            "convert_fonts",
            "optimize_fonts",
            "validate_fonts",
            "interactive",
        ]
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                return False

        # Check string fields
        string_fields = ["output_dir", "log_level"]
        for field in string_fields:
            if field in config and not isinstance(config[field], str):
                return False

        # Check array fields
        if "extract_formats" in config:
            if not isinstance(config["extract_formats"], list):
                return False
            for fmt in config["extract_formats"]:
                if not isinstance(fmt, str):
                    return False

        return True

    except Exception:
        return False


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    config = FontmilkerConfig()
    return config.as_dict()
