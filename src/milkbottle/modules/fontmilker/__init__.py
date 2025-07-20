"""Top‑level package for **Fontmilker**.

Font extraction and management tool for MilkBottle.
Exposes version metadata and a *lazy* `get_cli()` accessor so that importing
`fontmilker` in third‑party code does **not** pull heavy Typer/Rich deps until
absolutely necessary.

Enhanced with standardized interface for MilkBottle integration.
"""

from __future__ import annotations

import importlib
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType
from typing import Any, Dict, List

__all__ = ["__version__", "get_cli", "get_metadata", "validate_config", "health_check"]

# ------------------------------------------------------------
# Version metadata
# ------------------------------------------------------------
try:
    __version__: str = version("milkbottle-fontmilker")
except PackageNotFoundError:  # pragma: no cover – not installed
    __version__ = "1.0.0"

# Enhanced module metadata for registry
__alias__ = "fontmilker"
__description__ = "Font extraction and management tool"
__author__ = "MilkBottle Team"
__email__ = "team@milkbottle.dev"

# ------------------------------------------------------------
# Standardized Interface Implementation
# ------------------------------------------------------------


def get_metadata() -> Dict[str, Any]:
    """Get comprehensive module metadata."""
    return {
        "name": __alias__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "email": __email__,
        "capabilities": get_capabilities(),
        "dependencies": get_dependencies(),
        "config_schema": get_config_schema(),
    }


def get_capabilities() -> List[str]:
    """Return list of module capabilities."""
    return [
        "font_extraction",
        "font_analysis",
        "font_conversion",
        "font_metadata",
        "font_optimization",
        "font_validation",
        "interactive_cli",
        "configuration_management",
    ]


def get_dependencies() -> List[str]:
    """Return list of module dependencies."""
    return [
        "fonttools>=4.40.0",
        "Rich>=13.0.0",
        "Click>=8.0.0",
        "Pillow>=10.0.0",
        "reportlab>=4.0.0",
    ]


def get_config_schema() -> Dict[str, Any]:
    """Return configuration schema for validation."""
    return {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": True},
            "dry_run": {"type": "boolean", "default": False},
            "verbose": {"type": "boolean", "default": False},
            "output_dir": {"type": "string", "default": "fonts"},
            "extract_formats": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["ttf", "otf", "woff", "woff2"],
            },
            "analyze_fonts": {"type": "boolean", "default": True},
            "convert_fonts": {"type": "boolean", "default": False},
            "optimize_fonts": {"type": "boolean", "default": False},
            "validate_fonts": {"type": "boolean", "default": True},
            "interactive": {"type": "boolean", "default": True},
            "log_level": {"type": "string", "default": "info"},
        },
        "required": ["enabled"],
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate module configuration."""
    return _basic_config_validation(config)


def _basic_config_validation(config: Dict[str, Any]) -> bool:
    """Basic configuration validation."""
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


def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    try:
        # Check dependencies
        deps_status = _check_dependencies()

        # Check configuration
        config_status = _check_configuration()

        # Check functionality
        func_status = _check_functionality()

        # Determine overall status
        if all(
            status["status"] == "healthy"
            for status in [deps_status, config_status, func_status]
        ):
            overall_status = "healthy"
            details = "Font extraction and management ready"
        elif any(
            status["status"] == "critical"
            for status in [deps_status, config_status, func_status]
        ):
            overall_status = "critical"
            details = "Critical issues detected"
        else:
            overall_status = "warning"
            details = "Some warnings detected"

        return {
            "status": overall_status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "version": __version__,
            "checks": {
                "dependencies": deps_status,
                "configuration": config_status,
                "functionality": func_status,
            },
        }
    except Exception as e:
        return {
            "status": "critical",
            "details": f"Health check failed: {e}",
            "timestamp": datetime.now().isoformat(),
            "version": __version__,
        }


def _check_dependencies() -> Dict[str, Any]:
    """Check module dependencies."""
    try:
        missing_deps = []
        version_issues = []

        # Check fonttools
        try:
            import fonttools
        except ImportError:
            missing_deps.append("fonttools")

        # Check Rich
        try:
            import rich
        except ImportError:
            missing_deps.append("Rich")

        # Check Click
        try:
            import click
        except ImportError:
            missing_deps.append("Click")

        # Check Pillow
        try:
            from PIL import Image, ImageFont
        except ImportError:
            missing_deps.append("Pillow")

        # Check reportlab
        try:
            import reportlab
        except ImportError:
            missing_deps.append("reportlab")

        if missing_deps:
            return {
                "status": "critical",
                "details": f"Missing dependencies: {', '.join(missing_deps)}",
                "missing": missing_deps,
            }

        if version_issues:
            return {
                "status": "warning",
                "details": f"Version issues: {', '.join(version_issues)}",
                "version_issues": version_issues,
            }

        return {
            "status": "healthy",
            "details": "All dependencies available",
            "dependencies": ["fonttools", "Rich", "Click", "Pillow", "reportlab"],
        }

    except Exception as e:
        return {"status": "critical", "details": f"Dependency check failed: {e}"}


def _check_configuration() -> Dict[str, Any]:
    """Check module configuration."""
    try:
        # Test with default configuration
        default_config = {
            "enabled": True,
            "dry_run": False,
            "verbose": False,
            "output_dir": "fonts",
            "extract_formats": ["ttf", "otf"],
            "analyze_fonts": True,
            "convert_fonts": False,
            "optimize_fonts": False,
            "validate_fonts": True,
            "interactive": True,
            "log_level": "info",
        }

        if validate_config(default_config):
            return {"status": "healthy", "details": "Configuration validation working"}
        else:
            return {"status": "critical", "details": "Configuration validation failed"}

    except Exception as e:
        return {"status": "critical", "details": f"Configuration check failed: {e}"}


def _check_functionality() -> Dict[str, Any]:
    """Check module functionality."""
    try:
        # Test core functionality
        functionality_checks = []

        # Check if CLI can be loaded
        try:
            cli = get_cli()
            if cli is not None:
                functionality_checks.append("CLI loading")
        except Exception:
            pass

        # Check if font extractor is available
        try:
            from .font_extractor import FontExtractor

            functionality_checks.append("font_extraction")
        except ImportError:
            pass

        # Check if font analyzer is available
        try:
            from .font_analyzer import FontAnalyzer

            functionality_checks.append("font_analysis")
        except ImportError:
            pass

        # Check if font converter is available
        try:
            from .font_converter import FontConverter

            functionality_checks.append("font_conversion")
        except ImportError:
            pass

        if len(functionality_checks) >= 2:
            return {
                "status": "healthy",
                "details": f"Core functionality available: {', '.join(functionality_checks)}",
                "available_features": functionality_checks,
            }
        elif len(functionality_checks) >= 1:
            return {
                "status": "warning",
                "details": f"Limited functionality: {', '.join(functionality_checks)}",
                "available_features": functionality_checks,
            }
        else:
            return {"status": "critical", "details": "No core functionality available"}

    except Exception as e:
        return {"status": "critical", "details": f"Functionality check failed: {e}"}


# ------------------------------------------------------------
# Lazy CLI accessor
# ------------------------------------------------------------


def get_cli() -> Any:  # type: ignore[valid-type, name-defined, attr-defined]
    """Return the Typer application defined in ``fontmilker.cli``.

    The import is deferred until first call to keep top‑level import cost low.
    """

    cli_module: ModuleType = importlib.import_module(
        "milkbottle.modules.fontmilker.cli"
    )
    if hasattr(cli_module, "app"):
        return cli_module.app  # type: ignore[attr-defined]
    raise RuntimeError("fontmilker.cli does not define 'app'.")
