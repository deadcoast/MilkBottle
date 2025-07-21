"""Top‑level package for **PDFmilker**.

Exposes version metadata and a *lazy* `get_cli()` accessor so that importing
`pdfmilker` in third‑party code does **not** pull heavy Typer/Rich deps until
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
    __version__: str = version("milkbottle-pdfmilker")
except PackageNotFoundError:  # pragma: no cover – not installed
    __version__ = "1.0.0"

# Enhanced module metadata for registry
__alias__ = "pdfmilker"
__description__ = "Advanced PDF extraction and processing tool with quality assessment"
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
        "pdf_extraction",
        "batch_processing",
        "quality_assessment",
        "multi_format_export",
        "image_processing",
        "citation_processing",
        "table_processing",
        "error_recovery",
        "progress_tracking",
        "interactive_cli",
        "configuration_management",
    ]


def get_dependencies() -> List[str]:
    """Return list of module dependencies."""
    return [
        "PyMuPDF>=1.23.0",
        "Rich>=13.0.0",
        "Click>=8.0.0",
        "Pillow>=10.0.0",
        "python-docx>=0.8.11",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
    ]


def get_config_schema() -> Dict[str, Any]:
    """Return configuration schema for validation."""
    return {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": True},
            "dry_run": {"type": "boolean", "default": False},
            "verbose": {"type": "boolean", "default": False},
            "output_dir": {"type": "string", "default": "extracted"},
            "formats": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["markdown", "html", "json"],
            },
            "quality_assessment": {"type": "boolean", "default": True},
            "extract_images": {"type": "boolean", "default": False},
            "extract_tables": {"type": "boolean", "default": False},
            "extract_citations": {"type": "boolean", "default": False},
            "batch_processing": {"type": "boolean", "default": True},
            "parallel_workers": {
                "type": "integer",
                "minimum": 1,
                "maximum": 16,
                "default": 4,
            },
            "memory_limit": {"type": "string", "default": "2GB"},
            "progress_tracking": {"type": "boolean", "default": True},
            "error_recovery": {"type": "boolean", "default": True},
        },
        "required": ["enabled"],
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate module configuration."""
    try:
        from .config_validator import validate_config as validate

        return validate(config)
    except Exception:
        # Fallback to basic validation if config_validator is not available
        return _basic_config_validation(config)


def _basic_config_validation(config: Dict[str, Any]) -> bool:
    """Basic configuration validation fallback."""
    try:
        # Check required fields
        if "enabled" not in config:
            return False

        # Check boolean fields
        boolean_fields = [
            "enabled",
            "dry_run",
            "verbose",
            "quality_assessment",
            "extract_images",
            "extract_tables",
            "extract_citations",
            "batch_processing",
            "progress_tracking",
            "error_recovery",
        ]

        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                return False

        # Check string fields
        string_fields = ["output_dir", "memory_limit"]
        for field in string_fields:
            if field in config and not isinstance(config[field], str):
                return False

        # Check integer fields
        if "parallel_workers" in config:
            if not isinstance(config["parallel_workers"], int):
                return False
            if config["parallel_workers"] < 1 or config["parallel_workers"] > 16:
                return False

        # Check array fields
        if "formats" in config:
            if not isinstance(config["formats"], list):
                return False
            for fmt in config["formats"]:
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
            details = "All components functioning normally"
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
        # Check PyMuPDF
        try:
            import fitz

            if not hasattr(fitz, "Document"):
                missing_deps.append("PyMuPDF")
        except ImportError:
            missing_deps.append("PyMuPDF")

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
            from PIL import Image
        except ImportError:
            missing_deps.append("Pillow")

        if missing_deps:
            return {
                "status": "critical",
                "details": f"Missing dependencies: {', '.join(missing_deps)}",
                "missing": missing_deps,
            }

        version_issues = []

        return (
            {
                "status": "warning",
                "details": f"Version issues: {', '.join(version_issues)}",
                "version_issues": version_issues,
            }
            if version_issues
            else {
                "status": "healthy",
                "details": "All dependencies available",
                "dependencies": ["PyMuPDF", "Rich", "Click", "Pillow"],
            }
        )
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
            "output_dir": "extracted",
            "formats": ["markdown"],
            "quality_assessment": True,
            "extract_images": False,
            "extract_tables": False,
            "extract_citations": False,
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

        # Check if batch processor is available
        try:
            from .batch_processor import BatchProcessor

            functionality_checks.append("batch_processing")
        except ImportError:
            pass

        # Check if quality assessor is available
        try:
            from .quality_assessor import QualityAssessor

            functionality_checks.append("quality_assessment")
        except ImportError:
            pass

        # Check if format exporter is available
        try:
            from .format_exporter import FormatExporter

            functionality_checks.append("format_export")
        except ImportError:
            pass

        if len(functionality_checks) >= 3:
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
    """Return the Typer application defined in ``pdfmilker.cli``.

    The import is deferred until first call to keep top‑level import cost low.
    """

    cli_module: ModuleType = importlib.import_module("milkbottle.modules.pdfmilker.cli")
    if hasattr(cli_module, "app"):
        return cli_module.app  # type: ignore[attr-defined]
    raise RuntimeError("pdfmilker.cli does not define 'app'.")
