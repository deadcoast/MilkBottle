"""Top‑level package for **VENVmilker**.

Exposes version metadata and a *lazy* `get_cli()` accessor so that importing
`venvmilker` in third‑party code does **not** pull heavy Typer/Rich deps until
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
    __version__: str = version("milkbottle-venvmilker")
except PackageNotFoundError:  # pragma: no cover – not installed
    __version__ = "1.0.0"

# Enhanced module metadata for registry
__alias__ = "venvmilker"
__description__ = "Virtual environment creation and management tool"
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
        "venv_creation",
        "dependency_installation",
        "environment_activation",
        "snapshot_generation",
        "template_scaffolding",
        "python_version_management",
        "interactive_cli",
        "configuration_management",
    ]


def get_dependencies() -> List[str]:
    """Return list of module dependencies."""
    return [
        "virtualenv>=20.0.0",
        "Rich>=13.0.0",
        "Typer>=0.9.0",
        "python-slugify>=8.0.0",
    ]


def get_config_schema() -> Dict[str, Any]:
    """Return configuration schema for validation."""
    return {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": True},
            "python": {"type": "string", "default": "3.11"},
            "install": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["rich", "typer"],
            },
            "snapshot": {"type": "boolean", "default": True},
            "dry_run": {"type": "boolean", "default": False},
            "template": {"type": "string", "default": None},
            "interactive": {"type": "boolean", "default": True},
            "log_level": {"type": "string", "default": "info"},
        },
        "required": ["enabled"],
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate module configuration."""
    try:
        from .config import validate_config as validate

        return validate(config)
    except Exception:
        # Fallback to basic validation if config module is not available
        return _basic_config_validation(config)


def _basic_config_validation(config: Dict[str, Any]) -> bool:
    """Basic configuration validation fallback."""
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
            details = "Virtual environment management ready"
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
        # Check virtualenv
        try:
            import virtualenv
        except ImportError:
            missing_deps.append("virtualenv")

        # Check Rich
        try:
            import rich
        except ImportError:
            missing_deps.append("Rich")

        # Check Typer
        try:
            import typer
        except ImportError:
            missing_deps.append("Typer")

        # Check python-slugify
        try:
            import slugify
        except ImportError:
            missing_deps.append("python-slugify")

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
                "dependencies": [
                    "virtualenv",
                    "Rich",
                    "Typer",
                    "python-slugify",
                ],
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
            "python": "3.11",
            "install": ["rich", "typer"],
            "snapshot": True,
            "dry_run": False,
            "template": None,
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

        # Check if workflow module is available
        try:
            from .workflow import activate_environment, bootstrap_environment

            functionality_checks.append("workflow_functions")
        except ImportError:
            pass

        # Check if utils module is available
        try:
            from .utils import find_interpreter

            functionality_checks.append("utility_functions")
        except ImportError:
            pass

        # Check if template module is available
        try:
            from .template import apply_template

            functionality_checks.append("template_system")
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
    """Return the Typer application defined in ``venvmilker.cli``.

    The import is deferred until first call to keep top‑level import cost low.
    """

    cli_module: ModuleType = importlib.import_module(
        "milkbottle.modules.venvmilker.cli"
    )
    if hasattr(cli_module, "app"):
        return cli_module.app  # type: ignore[attr-defined]
    raise RuntimeError("venvmilker.cli does not define 'app'.")
