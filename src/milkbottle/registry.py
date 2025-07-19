"""MilkBottle registry module."""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

logger = logging.getLogger("milkbottle.registry")

MODULES_PATH = Path(__file__).parent / "modules"
ENTRY_POINT_GROUP = "milkbottle.bottles"


def discover_entrypoint_bottles() -> List[Dict[str, Any]]:
    """
    Discover bottles registered via entry points.
    Returns a list of dicts with alias, description, version, and loader.
    """
    bottles = []
    try:
        for entry_point in importlib.metadata.entry_points().select(
            group=ENTRY_POINT_GROUP
        ):
            try:
                module = importlib.import_module(entry_point.module)
                alias = getattr(module, "__alias__", entry_point.name)
                description = getattr(
                    module, "__description__", "No description provided."
                )
                version = getattr(module, "__version__", "0.0.0")
                bottles.append(
                    {
                        "alias": alias,
                        "description": description,
                        "version": version,
                        "loader": lambda: getattr(module, "get_cli")(),
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to load entry-point bottle '%s': %s", entry_point.name, e
                )
    except Exception as e:
        logger.error("Error discovering entry-point bottles: %s", e)
    return bottles


def discover_local_bottles() -> List[Dict[str, Any]]:
    """
    Discover bottles in the local modules directory.
    Returns a list of dicts with alias, description, version, and loader.
    """
    bottles = []
    if not MODULES_PATH.exists():
        return bottles
    for item in MODULES_PATH.iterdir():
        if item.is_dir() and (item / "cli.py").exists():
            try:
                module_name = f"milkbottle.modules.{item.name}"
                module = importlib.import_module(module_name)
                alias = getattr(module, "__alias__", item.name)
                description = getattr(
                    module, "__description__", "No description provided."
                )
                version = getattr(module, "__version__", "0.0.0")
                bottles.append(
                    {
                        "alias": alias,
                        "description": description,
                        "version": version,
                        "loader": lambda: getattr(module, "get_cli")(),
                    }
                )
            except Exception as e:
                logger.error("Failed to load local bottle '%s': %s", item.name, e)
    return bottles


def list_bottles() -> List[Dict[str, Any]]:
    """
    List all discovered bottles (entry-point and local).
    Returns a list of dicts with alias, description, and version.
    """
    bottles = discover_entrypoint_bottles() + discover_local_bottles()
    # Remove duplicates by alias (entry-points take precedence)
    seen = set()
    unique_bottles = []
    for b in bottles:
        if b["alias"].lower() not in seen:
            unique_bottles.append(b)
            seen.add(b["alias"].lower())
    return [
        {"alias": b["alias"], "description": b["description"], "version": b["version"]}
        for b in unique_bottles
    ]


def get_bottle(alias: str) -> Optional[typer.Typer]:
    """
    Retrieve the Typer app for a given bottle alias (case-insensitive).
    Returns the Typer app or None if not found.
    """
    bottles = discover_entrypoint_bottles() + discover_local_bottles()
    for b in bottles:
        if b["alias"].lower() == alias.lower():
            try:
                return b["loader"]()
            except Exception as e:
                logger.error("Failed to load CLI for bottle '%s': %s", alias, e)
                return None
    logger.warning("Bottle '%s' not found.", alias)
    return None
