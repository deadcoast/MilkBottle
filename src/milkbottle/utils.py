"""MilkBottle utils module."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

from rich.box import MINIMAL_DOUBLE_HEAD
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text
from slugify import slugify as _slugify

logger = logging.getLogger("milkbottle.utils")


class ErrorHandler:
    """Error handling utility for MilkBottle."""

    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger("milkbottle.error_handler")

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle an error with logging and context.

        Args:
            error: The exception to handle
            context: Additional context about the error
        """
        self.logger.error(f"Error in {context}: {error}")

    def validate_input(self, value: Any, expected_type: type, name: str = "") -> bool:
        """Validate input type.

        Args:
            value: Value to validate
            expected_type: Expected type
            name: Name of the value for error messages

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(value, expected_type):
            self.logger.error(
                f"Invalid type for {name}: expected {expected_type}, got {type(value)}"
            )
            return False
        return True


class InputValidator:
    """Input validation utility for MilkBottle."""

    def __init__(self):
        """Initialize input validator."""
        self.logger = logging.getLogger("milkbottle.input_validator")

    def validate_string(
        self, value: Any, min_length: int = 0, max_length: Optional[int] = None
    ) -> bool:
        """Validate string input.

        Args:
            value: Value to validate
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(value, str):
            return False

        if len(value) < min_length:
            return False

        if max_length and len(value) > max_length:
            return False

        return True

    def validate_path(self, path: Any) -> bool:
        """Validate path input.

        Args:
            path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            from pathlib import Path

            Path(path)
            return True
        except (TypeError, ValueError):
            return False

    def validate_url(self, url: Any) -> bool:
        """Validate URL input.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            from urllib.parse import urlparse

            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (TypeError, ValueError):
            return False


def get_console() -> Console:
    """
    Return a Rich Console instance for consistent CLI output.
    """
    return Console()


def slugify(value: str) -> str:
    """
    Slugify a string for safe folder or file names using python-slugify.
    Args:
        value (str): The string to slugify.
    Returns:
        str: The slugified string.
    """
    try:
        return _slugify(value)
    except (ValueError, TypeError) as e:
        logger.error("Failed to slugify '%s': %s", value, e)
        return value


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes as a human-readable string.
    Args:
        size_bytes (int): File size in bytes.
    Returns:
        str: Human-readable file size.
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def hash_file(path: str, chunk_size: int = 65536) -> Optional[str]:
    """
    Compute the SHA256 hash of a file.
    Args:
        path (str): Path to the file.
        chunk_size (int): Size of chunks to read.
    Returns:
        Optional[str]: Hex digest of the file, or None if error.
    """
    try:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError) as e:
        logger.error("Failed to hash file '%s': %s", path, e)
        return None


# --- Existing Rich menu border code ---
def render_menu_border(
    title: str = "MilkBottle Menu",
    subtitle: str = "The Fluid Code Toolbox",
    width: int = 60,
    style: str = "bold magenta",
) -> RenderableType:
    """
    Render an advanced ASCII/Unicode border for CLI menus using Rich.
    Args:
        title (str): The main title for the menu.
        subtitle (str): Subtitle or tagline.
        width (int): Width of the menu border.
        style (str): Rich style string for the border and text.
    Returns:
        RenderableType: A Rich renderable (Panel) with a custom border.
    """
    border_text = Text(title, style=style, justify="center")
    subtitle_text = Text(subtitle, style="dim", justify="center")
    return Panel(
        subtitle_text,
        title=border_text,
        width=width,
        border_style=style,
        box=MINIMAL_DOUBLE_HEAD,
        padding=(1, 2),
    )


def print_menu_border() -> None:
    """
    Print the MilkBottle main menu border to the console using Rich.
    """
    console = get_console()
    panel = render_menu_border()
    console.print(panel)
