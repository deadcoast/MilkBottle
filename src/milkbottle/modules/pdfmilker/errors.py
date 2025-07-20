"""PDFmilker exception hierarchy – production‑ready.

All exceptions raised by this module ultimately derive from
``PDFMilkerError``, which itself derives from MilkBottle's shared
``MilkBottleError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from milkbottle.errors import MilkBottleError
else:
    try:
        from milkbottle.errors import MilkBottleError
    except ImportError:
        # Fallback for standalone usage
        class MilkBottleError(Exception):  # type: ignore
            """Base exception for all MilkBottle errors."""


# ---------------------------------------------------------------------------
# PDFmilker-specific errors
# ---------------------------------------------------------------------------
class PDFMilkerError(MilkBottleError):
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
