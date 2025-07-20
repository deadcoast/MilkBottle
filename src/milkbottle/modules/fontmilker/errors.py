"""Fontmilker exception hierarchy."""

from __future__ import annotations

from typing import Optional


class FontmilkerError(Exception):
    """Base exception for Fontmilker errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(FontmilkerError):
    """Configuration-related errors."""

    pass


class ValidationError(FontmilkerError):
    """Validation-related errors."""

    pass


class ExtractionError(FontmilkerError):
    """Font extraction errors."""

    pass


class AnalysisError(FontmilkerError):
    """Font analysis errors."""

    pass


class ConversionError(FontmilkerError):
    """Font conversion errors."""

    pass


class OptimizationError(FontmilkerError):
    """Font optimization errors."""

    pass


__all__ = [
    "FontmilkerError",
    "ConfigurationError",
    "ValidationError",
    "ExtractionError",
    "AnalysisError",
    "ConversionError",
    "OptimizationError",
]
