"""VENVmilker exception hierarchy – production‑ready.

All exceptions raised by this module ultimately derive from
``VenvMilkerError``, which itself derives from MilkBottle’s shared
``MilkBottleError`` if available, or a lightweight fallback when VENVmilker
is used standalone.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fallback‑aware base error
# ---------------------------------------------------------------------------
try:
    from milkbottle.errors import MilkBottleError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – stand‑alone usage

    class MilkBottleError(Exception):
        """Standalone replacement when MilkBottle isn’t installed."""


# ---------------------------------------------------------------------------
# VENVmilker‑specific hierarchy
# ---------------------------------------------------------------------------
class VenvMilkerError(MilkBottleError):
    """Base class for all VENVmilker exceptions."""


class DetectError(VenvMilkerError):
    """Raised when the project root or Python interpreter cannot be found."""


class CreateError(VenvMilkerError):
    """Raised when creating the virtual environment fails."""


class InstallError(VenvMilkerError):
    """Raised when installing starter packages inside the venv fails."""


class SnapshotError(VenvMilkerError):
    """Raised when generating *requirements.lock* fails."""


class TemplateError(VenvMilkerError):
    """Raised when scaffolding a project template fails."""


class ActivateError(VenvMilkerError):
    """Raised when spawning an activated subshell fails."""


__all__ = [
    "VenvMilkerError",
    "DetectError",
    "CreateError",
    "InstallError",
    "SnapshotError",
    "TemplateError",
    "ActivateError",
]
