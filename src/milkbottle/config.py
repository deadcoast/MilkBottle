"""MilkBottle configuration loader – production‑ready
===================================================

Responsible for merging multiple layers of settings:
1. Hard‑coded defaults (inside this file)
2. `milkbottle.toml` found in project root or ancestors
3. CLI overrides passed by `milk_bottle.py`

The resulting `MilkBottleConfig` dataclass is consumed by the main CLI.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "log_level": "info",
    "dry_run": False,
    "config_file": None,
    "bottles": {},
    "global": {
        "interactive": True,
        "color": True,
        "verbose": False,
    },
    "venvmilker": {
        "python": "3.11",
        "install": ["rich", "typer"],
        "snapshot": True,
        "dry_run": False,
        "template": None,
    },
    "pdfmilker": {
        "output_dir": "extracted",
        "formats": ["txt", "json"],
        "dry_run": False,
        "verbose": False,
    },
    "plugin_system": {
        "plugin_dir": "~/.milkbottle/plugins",
        "enable_marketplace": True,
        "marketplace_url": "https://marketplace.milkbottle.dev/api/v1",
        "auto_update": False,
        "security_scan": True,
        "performance_monitoring": True,
    },
}

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MilkBottleConfig:
    """Immutable configuration object for a MilkBottle session."""

    log_level: str = DEFAULTS["log_level"]
    dry_run: bool = DEFAULTS["dry_run"]
    config_file: Optional[str] = DEFAULTS["config_file"]
    bottles: Dict[str, Any] = field(default_factory=dict)
    global_settings: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULTS["global"])
    )
    venvmilker_config: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULTS["venvmilker"])
    )
    pdfmilker_config: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULTS["pdfmilker"])
    )
    plugin_system_config: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULTS["plugin_system"])
    )
    version: str = "5.0.0"

    def as_dict(self) -> Dict[str, Any]:
        """Return config as plain dict (for JSON serialization)."""
        return {
            "log_level": self.log_level,
            "dry_run": self.dry_run,
            "config_file": self.config_file,
            "bottles": self.bottles,
            "global": self.global_settings,
            "venvmilker": self.venvmilker_config,
            "pdfmilker": self.pdfmilker_config,
            "plugin_system": self.plugin_system_config,
            "version": self.version,
        }

    def get_bottle_config(self, bottle_name: str) -> Dict[str, Any]:
        """Get configuration for a specific bottle."""
        if bottle_name == "venvmilker":
            return self.venvmilker_config
        elif bottle_name == "pdfmilker":
            return self.pdfmilker_config
        return self.bottles.get(bottle_name, {})

    @property
    def plugin_dir(self) -> str:
        """Get plugin directory path."""
        return self.plugin_system_config.get("plugin_dir", "~/.milkbottle/plugins")

    @property
    def enable_marketplace(self) -> bool:
        """Check if marketplace is enabled."""
        return self.plugin_system_config.get("enable_marketplace", True)

    @property
    def marketplace_url(self) -> str:
        """Get marketplace URL."""
        return self.plugin_system_config.get(
            "marketplace_url", "https://marketplace.milkbottle.dev/api/v1"
        )

    def is_dry_run(self) -> bool:
        """Check if dry run mode is enabled."""
        return self.dry_run


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _load_toml(start_dir: Path) -> dict[str, Any]:
    """Search *start_dir* and parents for `milkbottle.toml`."""
    for parent in [start_dir, *start_dir.parents]:
        candidate = parent / "milkbottle.toml"
        if candidate.is_file():
            try:
                with candidate.open("rb") as fh:
                    return tomllib.load(fh)
            except (OSError, ValueError, tomllib.TOMLDecodeError):
                # If TOML parsing fails, return empty dict
                return {}
    return {}


def _deep_update(
    target: MutableMapping[str, Any], src: MutableMapping[str, Any]
) -> None:
    """Recursively merge *src* into *target* (in‑place)."""
    for key, value in src.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, MutableMapping)
        ):
            _deep_update(target[key], value)  # type: ignore[arg-type]
        else:
            target[key] = value


def _load_config_file(config_path: Optional[str]) -> dict[str, Any]:
    """Load configuration from a specific file path."""
    if not config_path:
        return {}

    config_file = Path(config_path)
    if not config_file.is_file():
        return {}

    try:
        with config_file.open("rb") as fh:
            return tomllib.load(fh)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_config(
    project_root: Path,
    cli_overrides: dict[str, Any],
    config_file_path: Optional[str] = None,
) -> MilkBottleConfig:
    """Return a merged `MilkBottleConfig`.

    Precedence (lowest→highest): defaults < TOML < config file < CLI overrides.
    """
    data: dict[str, Any] = {**DEFAULTS}

    # Load TOML from project directory
    toml_data = _load_toml(project_root)
    _deep_update(data, toml_data)

    # Load specific config file if provided
    if config_file_path:
        config_data = _load_config_file(config_file_path)
        _deep_update(data, config_data)

    # Apply CLI overrides last
    _deep_update(data, cli_overrides)

    return MilkBottleConfig(
        log_level=str(data.get("log_level", DEFAULTS["log_level"])),
        dry_run=bool(data.get("dry_run", DEFAULTS["dry_run"])),
        config_file=config_file_path,
        bottles=dict(data.get("bottles", {})),
        global_settings=dict(data.get("global", DEFAULTS["global"])),
        venvmilker_config=dict(data.get("venvmilker", DEFAULTS["venvmilker"])),
        pdfmilker_config=dict(data.get("pdfmilker", DEFAULTS["pdfmilker"])),
    )


def get_config(
    project_root: Optional[Path] = None,
    config_file: Optional[str] = None,
    dry_run: bool = False,
    log_level: Optional[str] = None,
) -> MilkBottleConfig:
    """Convenience function to build config from common parameters."""
    if project_root is None:
        project_root = Path.cwd()

    cli_overrides = {}
    if dry_run:
        cli_overrides["dry_run"] = True
    if log_level:
        cli_overrides["log_level"] = log_level

    return build_config(project_root, cli_overrides, config_file)
