"""PDFmilker exception hierarchy – production‑ready.

All exceptions raised by this module ultimately derive from
``PDFMilkerError``, which itself derives from MilkBottle’s shared
``MilkBottleError`` if available, or a lightweight fallback when PDFmilker
is used standalone.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Fallback‑aware base error
# ---------------------------------------------------------------------------
class PDFMilkerError(Exception):
    """
    Base exception for all PDFmilker errors.
    """


class ExtractionError(PDFMilkerError):
    """
    Raised when extraction of text, images, or metadata fails.
    """


class ValidationError(PDFMilkerError):
    """
    Raised when validation of assets or hashes fails.
    """


class RelocationError(PDFMilkerError):
    """
    Raised when relocation of the source PDF fails.
    """
