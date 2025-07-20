"""Enhanced MilkBottle registry module with standardized interface support.

This module provides comprehensive bottle discovery, validation, health monitoring,
and configuration management for the MilkBottle system.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

logger = logging.getLogger("milkbottle.registry")

MODULES_PATH = Path(__file__).parent / "modules"
ENTRY_POINT_GROUP = "milkbottle.bottles"
console = Console()

# Configuration constants
DEFAULT_CACHE_TIMEOUT = 300  # 5 minutes
DEFAULT_HEALTH_CHECK_TIMEOUT = 30  # 30 seconds


class BottleRegistry:
    """Enhanced bottle registry with standardized interface support."""

    def __init__(self, cache_timeout: int = DEFAULT_CACHE_TIMEOUT):
        """Initialize the bottle registry.

        Args:
            cache_timeout: Cache timeout in seconds (default: 300)
        """
        self._bottles: Dict[str, Dict[str, Any]] = {}
        self._health_cache: Dict[str, Dict[str, Any]] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._discovery_time: Optional[datetime] = None
        self._cache_timeout = cache_timeout

    def discover_bottles(
        self, force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Discover all bottles with enhanced metadata and validation.

        Args:
            force_refresh: Force refresh of discovery cache

        Returns:
            Dictionary of discovered bottles with enhanced metadata
        """
        if not force_refresh and self._bottles and self._discovery_time:
            # Return cached results if not stale
            age = datetime.now() - self._discovery_time
            if age.total_seconds() < self._cache_timeout:
                return self._bottles

        self._bottles = {}

        # Discover entry-point bottles
        entry_point_bottles = self._discover_entrypoint_bottles()
        self._bottles.update(entry_point_bottles)

        # Discover local bottles
        local_bottles = self._discover_local_bottles()
        self._bottles.update(local_bottles)

        # Validate and enhance bottles
        self._validate_and_enhance_bottles()

        self._discovery_time = datetime.now()
        return self._bottles

    def _discover_entrypoint_bottles(self) -> Dict[str, Dict[str, Any]]:
        """Discover bottles registered via entry points with enhanced metadata."""
        bottles = {}
        try:
            for entry_point in importlib.metadata.entry_points().select(
                group=ENTRY_POINT_GROUP
            ):
                try:
                    bottle_info = self._load_bottle_with_metadata(
                        entry_point.module, entry_point.name
                    )
                    if bottle_info:
                        bottles[entry_point.name] = bottle_info
                except Exception as e:
                    logger.error(
                        "Failed to load entry-point bottle '%s': %s",
                        entry_point.name,
                        e,
                    )
        except Exception as e:
            logger.error("Error discovering entry-point bottles: %s", e)
        return bottles

    def _discover_local_bottles(self) -> Dict[str, Dict[str, Any]]:
        """Discover bottles in the local modules directory with enhanced metadata."""
        bottles = {}
        if not MODULES_PATH.exists():
            return bottles

        for item in MODULES_PATH.iterdir():
            if item.is_dir() and (item / "cli.py").exists():
                try:
                    module_name = f"milkbottle.modules.{item.name}"
                    bottle_info = self._load_bottle_with_metadata(
                        module_name, item.name
                    )
                    if bottle_info:
                        bottles[item.name] = bottle_info
                except Exception as e:
                    logger.error("Failed to load local bottle '%s': %s", item.name, e)
        return bottles

    def _load_bottle_with_metadata(
        self, module_name: str, bottle_name: str
    ) -> Optional[Dict[str, Any]]:
        """Load a bottle with comprehensive metadata and validation."""
        try:
            module = importlib.import_module(module_name)

            # Basic bottle info
            bottle_info = {
                "name": bottle_name,
                "module_name": module_name,
                "module": module,
                "discovery_time": datetime.now().isoformat(),
                "source": "entry_point" if "entry_point" in module_name else "local",
            }

            # Enhanced metadata if available
            if hasattr(module, "get_metadata"):
                try:
                    metadata = module.get_metadata()
                    bottle_info.update(metadata)
                    bottle_info["has_standard_interface"] = True
                except Exception as e:
                    logger.warning("Failed to get metadata for %s: %s", bottle_name, e)
                    bottle_info["has_standard_interface"] = False
            else:
                # Fallback to basic metadata
                bottle_info.update(
                    {
                        "name": getattr(module, "__alias__", bottle_name),
                        "version": getattr(module, "__version__", "0.0.0"),
                        "description": getattr(
                            module, "__description__", "No description provided."
                        ),
                        "author": getattr(module, "__author__", "Unknown"),
                        "email": getattr(module, "__email__", ""),
                        "capabilities": [],
                        "dependencies": [],
                        "config_schema": {},
                        "has_standard_interface": False,
                    }
                )

            # CLI loader
            if hasattr(module, "get_cli"):
                bottle_info["cli_loader"] = lambda m=module: getattr(m, "get_cli")()
                bottle_info["has_cli"] = True
            else:
                bottle_info["has_cli"] = False
                logger.warning("Bottle %s has no CLI interface", bottle_name)

            return bottle_info

        except Exception as e:
            logger.error("Failed to load bottle %s: %s", bottle_name, e)
            return None

    def _validate_and_enhance_bottles(self):
        """Validate and enhance discovered bottles."""
        for bottle_name, bottle_info in self._bottles.items():
            try:
                # Validate configuration if standard interface is available
                if bottle_info.get("has_standard_interface"):
                    if hasattr(bottle_info["module"], "validate_config"):
                        # Test with default configuration
                        default_config = {"enabled": True}
                        try:
                            is_valid = bottle_info["module"].validate_config(
                                default_config
                            )
                            bottle_info["config_validation"] = is_valid
                        except Exception as e:
                            logger.warning(
                                "Config validation failed for %s: %s", bottle_name, e
                            )
                            bottle_info["config_validation"] = False

                # Check for required attributes
                bottle_info["is_valid"] = (
                    bottle_info.get("has_cli", False)
                    and bottle_info.get("name")
                    and bottle_info.get("version")
                )

            except Exception as e:
                logger.error("Failed to validate bottle %s: %s", bottle_name, e)
                bottle_info["is_valid"] = False

    def get_bottle(self, alias: str) -> Optional[typer.Typer]:
        """
        Retrieve the Typer app for a given bottle alias (case-insensitive).

        Args:
            alias: Bottle alias to retrieve

        Returns:
            Typer app or None if not found
        """
        bottles = self.discover_bottles()

        for bottle_name, bottle_info in bottles.items():
            if bottle_info.get("name", "").lower() == alias.lower():
                if bottle_info.get("has_cli"):
                    try:
                        return bottle_info["cli_loader"]()
                    except Exception as e:
                        logger.error("Failed to load CLI for bottle '%s': %s", alias, e)
                        return None
                else:
                    logger.warning("Bottle '%s' has no CLI interface", alias)
                    return None

        logger.warning("Bottle '%s' not found.", alias)
        return None

    def get_bottle_metadata(self, alias: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive metadata for a bottle.

        Args:
            alias: Bottle alias

        Returns:
            Bottle metadata or None if not found
        """
        bottles = self.discover_bottles()

        for bottle_name, bottle_info in bottles.items():
            if bottle_info.get("name", "").lower() == alias.lower():
                return bottle_info

        return None

    def health_check(self, alias: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform health check for bottles.

        Args:
            alias: Specific bottle alias to check, or None for all bottles

        Returns:
            Health check results
        """
        bottles = self.discover_bottles()
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "bottles": {},
        }

        if alias:
            # Check specific bottle
            bottle_info = self.get_bottle_metadata(alias)
            if bottle_info:
                results["bottles"][alias] = self._check_bottle_health(bottle_info)
            else:
                results["bottles"][alias] = {
                    "status": "critical",
                    "details": "Bottle not found",
                }
        else:
            # Check all bottles
            for bottle_name, bottle_info in bottles.items():
                results["bottles"][bottle_name] = self._check_bottle_health(bottle_info)

        # Determine overall status
        bottle_statuses = [info["status"] for info in results["bottles"].values()]
        if any(status == "critical" for status in bottle_statuses):
            results["overall_status"] = "critical"
        elif any(status == "warning" for status in bottle_statuses):
            results["overall_status"] = "warning"

        return results

    def _check_bottle_health(self, bottle_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a specific bottle."""
        try:
            # Basic health check
            health_info = {
                "status": "healthy",
                "details": "Bottle is functioning normally",
                "checks": {},
            }

            # Check if bottle has standard interface
            if bottle_info.get("has_standard_interface"):
                module = bottle_info["module"]

                # Use bottle's own health check if available
                if hasattr(module, "health_check"):
                    try:
                        # Add timeout handling for health checks
                        import threading

                        health_result = None
                        health_error = None

                        def run_health_check():
                            nonlocal health_result, health_error
                            try:
                                health_result = module.health_check()
                            except Exception as e:
                                health_error = e

                        # Run health check with timeout
                        thread = threading.Thread(target=run_health_check)
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout=DEFAULT_HEALTH_CHECK_TIMEOUT)

                        if thread.is_alive():
                            health_info["checks"]["bottle_health"] = {
                                "status": "critical",
                                "details": f"Health check timed out after {DEFAULT_HEALTH_CHECK_TIMEOUT} seconds",
                            }
                        elif health_error:
                            health_info["checks"]["bottle_health"] = {
                                "status": "critical",
                                "details": f"Health check failed: {health_error}",
                            }
                        elif health_result:
                            health_info.update(health_result)

                    except Exception as e:
                        health_info["checks"]["bottle_health"] = {
                            "status": "critical",
                            "details": f"Health check failed: {e}",
                        }
                else:
                    health_info["checks"]["bottle_health"] = {
                        "status": "warning",
                        "details": "No health check available",
                    }

                # Check dependencies if available
                if hasattr(module, "get_dependencies"):
                    try:
                        deps_status = self._check_dependencies(
                            module.get_dependencies()
                        )
                        health_info["checks"]["dependencies"] = deps_status
                    except Exception as e:
                        health_info["checks"]["dependencies"] = {
                            "status": "warning",
                            "details": f"Dependency check failed: {e}",
                        }
            else:
                health_info["checks"]["standard_interface"] = {
                    "status": "warning",
                    "details": "Bottle does not implement standard interface",
                }

            # Check CLI availability
            if bottle_info.get("has_cli"):
                try:
                    cli = bottle_info["cli_loader"]()
                    if cli is not None:
                        health_info["checks"]["cli"] = {
                            "status": "healthy",
                            "details": "CLI interface available",
                        }
                    else:
                        health_info["checks"]["cli"] = {
                            "status": "critical",
                            "details": "CLI interface failed to load",
                        }
                except Exception as e:
                    health_info["checks"]["cli"] = {
                        "status": "critical",
                        "details": f"CLI interface error: {e}",
                    }
            else:
                health_info["checks"]["cli"] = {
                    "status": "critical",
                    "details": "No CLI interface available",
                }

            # Determine overall status
            check_statuses = [
                check["status"] for check in health_info["checks"].values()
            ]
            if any(status == "critical" for status in check_statuses):
                health_info["status"] = "critical"
                health_info["details"] = "Critical issues detected"
            elif any(status == "warning" for status in check_statuses):
                health_info["status"] = "warning"
                health_info["details"] = "Some warnings detected"

            return health_info

        except Exception as e:
            return {
                "status": "critical",
                "details": f"Health check failed: {e}",
                "checks": {},
            }

    def _check_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """Check if dependencies are available."""
        try:
            missing_deps = []
            version_issues = []

            for dep in dependencies:
                # Parse dependency string (e.g., "package>=1.0.0")
                if ">=" in dep:
                    package_name, version_req = dep.split(">=", 1)
                    package_name = package_name.strip()
                    version_req = version_req.strip()
                elif "==" in dep:
                    package_name, version_req = dep.split("==", 1)
                    package_name = package_name.strip()
                    version_req = version_req.strip()
                else:
                    package_name = dep.strip()
                    version_req = None

                try:
                    module = importlib.import_module(package_name)
                    if version_req:
                        # Basic version check (could be enhanced with packaging library)
                        if hasattr(module, "__version__"):
                            module_version = module.__version__
                            # Simple version comparison (could be improved)
                            if module_version < version_req:
                                version_issues.append(
                                    f"{package_name} {module_version} < {version_req}"
                                )
                except ImportError:
                    missing_deps.append(package_name)
                except Exception:
                    missing_deps.append(package_name)

            if missing_deps:
                return {
                    "status": "critical",
                    "details": f"Missing dependencies: {', '.join(missing_deps)}",
                    "missing": missing_deps,
                }
            elif version_issues:
                return {
                    "status": "warning",
                    "details": f"Version issues: {', '.join(version_issues)}",
                    "version_issues": version_issues,
                }
            else:
                return {
                    "status": "healthy",
                    "details": "All dependencies available",
                    "dependencies": dependencies,
                }

        except Exception as e:
            return {
                "status": "warning",
                "details": f"Dependency check failed: {e}",
            }

    def validate_config(
        self, alias: str, config: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate configuration for a bottle.

        Args:
            alias: Bottle alias
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        bottle_info = self.get_bottle_metadata(alias)
        if not bottle_info:
            return False, [f"Bottle '{alias}' not found"]

        if not bottle_info.get("has_standard_interface"):
            return False, ["Bottle does not implement standard interface"]

        try:
            module = bottle_info["module"]
            if hasattr(module, "validate_config"):
                is_valid = module.validate_config(config)
                if is_valid:
                    return True, []
                else:
                    return False, ["Configuration validation failed"]
            else:
                return False, ["Bottle does not support configuration validation"]
        except Exception as e:
            return False, [f"Configuration validation error: {e}"]

    def list_bottles(self) -> List[Dict[str, Any]]:
        """
        List all discovered bottles with enhanced information.

        Returns:
            List of bottle information dictionaries
        """
        bottles = self.discover_bottles()
        return [
            {
                "name": info.get("name", bottle_name),
                "version": info.get("version", "0.0.0"),
                "description": info.get("description", "No description provided."),
                "author": info.get("author", "Unknown"),
                "capabilities": info.get("capabilities", []),
                "dependencies": info.get("dependencies", []),
                "has_standard_interface": info.get("has_standard_interface", False),
                "has_cli": info.get("has_cli", False),
                "is_valid": info.get("is_valid", False),
                "source": info.get("source", "unknown"),
            }
            for bottle_name, info in bottles.items()
        ]

    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get capabilities for all bottles.

        Returns:
            Dictionary mapping bottle names to their capabilities
        """
        bottles = self.discover_bottles()
        capabilities = {}

        for bottle_name, bottle_info in bottles.items():
            if bottle_info.get("has_standard_interface"):
                capabilities[bottle_name] = bottle_info.get("capabilities", [])

        return capabilities

    def get_dependencies(self) -> Dict[str, List[str]]:
        """
        Get dependencies for all bottles.

        Returns:
            Dictionary mapping bottle names to their dependencies
        """
        bottles = self.discover_bottles()
        dependencies = {}

        for bottle_name, bottle_info in bottles.items():
            if bottle_info.get("has_standard_interface"):
                dependencies[bottle_name] = bottle_info.get("dependencies", [])

        return dependencies

    def print_status(self):
        """Print comprehensive status of all bottles."""
        bottles = self.list_bottles()

        # Create status table
        table = Table(title="MilkBottle Registry Status")
        table.add_column("Bottle", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Interface", style="blue")
        table.add_column("CLI", style="magenta")
        table.add_column("Capabilities", style="white")

        for bottle in bottles:
            status = "✅ Valid" if bottle["is_valid"] else "❌ Invalid"
            interface = "✅ Standard" if bottle["has_standard_interface"] else "⚠️ Basic"
            cli = "✅ Available" if bottle["has_cli"] else "❌ Missing"
            capabilities = f"{len(bottle['capabilities'])} capabilities"

            table.add_row(
                bottle["name"], bottle["version"], status, interface, cli, capabilities
            )

        console.print(table)

        # Print summary
        total_bottles = len(bottles)
        valid_bottles = sum(1 for b in bottles if b["is_valid"])
        standard_interfaces = sum(1 for b in bottles if b["has_standard_interface"])

        console.print(
            f"\n[bold]Summary:[/bold] {valid_bottles}/{total_bottles} bottles valid, {standard_interfaces} with standard interface"
        )


# Global registry instance
_registry = BottleRegistry()


# Backward compatibility functions
def discover_entrypoint_bottles() -> List[Dict[str, Any]]:
    """Backward compatibility: Discover bottles registered via entry points."""
    bottles = _registry.discover_bottles()
    return [
        {
            "alias": info.get("name", name),
            "description": info.get("description", "No description provided."),
            "version": info.get("version", "0.0.0"),
            "loader": info.get("cli_loader", lambda: None),
        }
        for name, info in bottles.items()
        if info.get("source") == "entry_point"
    ]


def discover_local_bottles() -> List[Dict[str, Any]]:
    """Backward compatibility: Discover bottles in the local modules directory."""
    bottles = _registry.discover_bottles()
    return [
        {
            "alias": info.get("name", name),
            "description": info.get("description", "No description provided."),
            "version": info.get("version", "0.0.0"),
            "loader": info.get("cli_loader", lambda: None),
        }
        for name, info in bottles.items()
        if info.get("source") == "local"
    ]


def list_bottles() -> List[Dict[str, Any]]:
    """Backward compatibility: List all discovered bottles."""
    return _registry.list_bottles()


def get_bottle(alias: str) -> Optional[typer.Typer]:
    """Backward compatibility: Retrieve the Typer app for a given bottle alias."""
    return _registry.get_bottle(alias)


# Enhanced functions
def get_registry() -> BottleRegistry:
    """Get the global registry instance."""
    return _registry


def perform_health_check(alias: Optional[str] = None) -> Dict[str, Any]:
    """Perform health check for bottles."""
    return _registry.health_check(alias)


def validate_bottle_config(
    alias: str, config: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate configuration for a bottle."""
    return _registry.validate_config(alias, config)


def print_registry_status():
    """Print comprehensive status of all bottles."""
    _registry.print_status()
