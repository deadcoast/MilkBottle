"""VENVmilker configuration loader – production‑ready
===================================================

Responsible for merging three layers of settings:
1. Hard‑coded defaults (inside this file)
2. `venvmilker.toml` found in project root or ancestors
3. CLI overrides passed by `cli.py`

The resulting `VenvConfig` dataclass is consumed by `workflow.py`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "python": "3.11",
    "install": ["rich", "typer"],
    "snapshot": True,
    "dry_run": False,
    "template": None,  # e.g., "snakemake"
}

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class VenvConfig:
    """Immutable configuration object for a VENVmilker session."""

    python: str = DEFAULTS["python"]
    install: List[str] = field(default_factory=lambda: list(DEFAULTS["install"]))
    snapshot: bool = DEFAULTS["snapshot"]
    dry_run: bool = DEFAULTS["dry_run"]
    template: Optional[str] = DEFAULTS["template"]

    def as_dict(self) -> Dict[str, Any]:  # noqa: D401 – simple helper
        """Return config as plain dict (for JSON serialization)."""
        return {
            "python": self.python,
            "install": self.install,
            "snapshot": self.snapshot,
            "dry_run": self.dry_run,
            "template": self.template,
        }

    # Convenience alias for workflow
    to_json = as_dict


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _load_toml(start_dir: Path) -> dict[str, Any]:
    """Search *start_dir* and parents for `venvmilker.toml`."""
    for parent in [start_dir, *start_dir.parents]:
        candidate = parent / "venvmilker.toml"
        if candidate.is_file():
            with candidate.open("rb") as fh:
                return tomllib.load(fh)
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


# ---------------------------------------------------------------------------
# Configuration Validation
# ---------------------------------------------------------------------------


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate VENVmilker configuration.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check required fields
        if "enabled" not in config:
            return False

        # Check boolean fields
        boolean_fields = ["enabled", "snapshot", "dry_run", "interactive"]
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                return False

        # Check string fields
        string_fields = ["python", "template", "log_level"]
        for field in string_fields:
            if field in config and not isinstance(config[field], str):
                return False

        # Check array fields
        if "install" in config:
            if not isinstance(config["install"], list):
                return False
            for package in config["install"]:
                if not isinstance(package, str):
                    return False

        # Validate Python version format
        if "python" in config:
            python_version = config["python"]
            if not isinstance(python_version, str):
                return False
            # Basic Python version validation (e.g., "3.11", "3.12")
            if not python_version.startswith("3."):
                return False
            try:
                version_parts = python_version.split(".")
                if len(version_parts) != 2:
                    return False
                major, minor = version_parts
                if not (major == "3" and minor.isdigit() and 7 <= int(minor) <= 12):
                    return False
            except (ValueError, IndexError):
                return False

        return True

    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_config(project_root: Path, cli_overrides: dict[str, Any]) -> VenvConfig:
    """Return a merged `VenvConfig`.

    Precedence (lowest→highest): defaults < TOML < CLI overrides.
    """
    data: dict[str, Any] = {**DEFAULTS}

    toml_data = _load_toml(project_root)
    _deep_update(data, toml_data)
    _deep_update(data, cli_overrides)

    # Normalise types
    install_value = data.get("install")
    if isinstance(install_value, str):
        data["install"] = install_value.split()
    elif install_value is None:
        data["install"] = DEFAULTS["install"]

    return VenvConfig(
        python=str(data["python"]),
        install=list(data["install"]),
        snapshot=bool(data["snapshot"]),
        dry_run=bool(data["dry_run"]),
        template=str(data["template"]) if data["template"] else None,
    )
