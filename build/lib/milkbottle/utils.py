import hashlib
import logging
from typing import Optional

from rich.box import MINIMAL_DOUBLE_HEAD
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text
from slugify import slugify as _slugify

logger = logging.getLogger("milkbottle.utils")


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
    except Exception as e:
        logger.error(f"Failed to slugify '{value}': {e}")
        return value


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
    except Exception as e:
        logger.error(f"Failed to hash file '{path}': {e}")
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
    panel = Panel(
        subtitle_text,
        title=border_text,
        width=width,
        border_style=style,
        box=MINIMAL_DOUBLE_HEAD,
        padding=(1, 2),
    )
    return panel


def print_menu_border() -> None:
    """
    Print the MilkBottle main menu border to the console using Rich.
    """
    console = get_console()
    panel = render_menu_border()
    console.print(panel)
