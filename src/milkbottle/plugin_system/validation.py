"""Plugin validation system for MilkBottle.

This module provides comprehensive plugin validation including
security checks, dependency verification, and compatibility testing.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, Optional

from packaging import version

from .core import PluginInfo, PluginMetadata


class PluginValidator:
    """Plugin validation system."""

    def __init__(self, config: Any):
        """Initialize plugin validator.

        Args:
            config: MilkBottle configuration
        """
        self.config = config
        self.logger = logging.getLogger("milkbottle.plugin_validator")

    async def validate_plugin(self, plugin_info: PluginInfo) -> Dict[str, Any]:
        """Validate a plugin comprehensively.

        Args:
            plugin_info: Plugin information to validate

        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "security_issues": [],
            "compatibility_issues": [],
        }

        # Validate metadata
        metadata_results = self._validate_metadata(plugin_info.metadata)
        results["valid"] &= metadata_results["valid"]
        results["errors"].extend(metadata_results["errors"])
        results["warnings"].extend(metadata_results["warnings"])

        # Validate dependencies
        dependency_results = await self._validate_dependencies(plugin_info.metadata)
        results["valid"] &= dependency_results["valid"]
        results["errors"].extend(dependency_results["errors"])
        results["warnings"].extend(dependency_results["warnings"])

        # Validate compatibility
        compatibility_results = self._validate_compatibility(plugin_info.metadata)
        results["valid"] &= compatibility_results["valid"]
        results["errors"].extend(compatibility_results["errors"])
        results["warnings"].extend(compatibility_results["warnings"])
        results["compatibility_issues"].extend(compatibility_results["issues"])

        # Validate security
        security_results = await self._validate_security(plugin_info)
        results["valid"] &= security_results["valid"]
        results["errors"].extend(security_results["errors"])
        results["warnings"].extend(security_results["warnings"])
        results["security_issues"].extend(security_results["issues"])

        return results

    def _validate_metadata(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """Validate plugin metadata.

        Args:
            metadata: Plugin metadata to validate

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": []}

        # Check required fields
        if not metadata.name or not metadata.name.strip():
            results["errors"].append("Plugin name is required")
            results["valid"] = False

        if not metadata.version or not metadata.version.strip():
            results["errors"].append("Plugin version is required")
            results["valid"] = False

        if not metadata.description or not metadata.description.strip():
            results["errors"].append("Plugin description is required")
            results["valid"] = False

        if not metadata.author or not metadata.author.strip():
            results["errors"].append("Plugin author is required")
            results["valid"] = False

        if not metadata.email or not metadata.email.strip():
            results["errors"].append("Plugin email is required")
            results["valid"] = False

        if not metadata.license or not metadata.license.strip():
            results["errors"].append("Plugin license is required")
            results["valid"] = False

        # Validate version format
        try:
            version.parse(metadata.version)
        except version.InvalidVersion:
            results["errors"].append(f"Invalid version format: {metadata.version}")
            results["valid"] = False

        # Check for common issues
        if len(metadata.description) < 10:
            results["warnings"].append("Plugin description is very short")

        if not metadata.capabilities:
            results["warnings"].append("No capabilities specified")

        if not metadata.tags:
            results["warnings"].append("No tags specified")

        return results

    async def _validate_dependencies(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """Validate plugin dependencies.

        Args:
            metadata: Plugin metadata to validate

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": []}

        for dependency in metadata.dependencies:
            try:
                __import__(dependency)
            except ImportError:
                results["errors"].append(f"Missing dependency: {dependency}")
                results["valid"] = False

        return results

    def _validate_compatibility(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """Validate plugin compatibility.

        Args:
            metadata: Plugin metadata to validate

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "issues": []}

        # Check MilkBottle version compatibility
        if metadata.min_milkbottle_version:
            try:
                min_version = version.parse(metadata.min_milkbottle_version)
                current_version = version.parse(self.config.version)
                if current_version < min_version:
                    results["errors"].append(
                        f"Plugin requires MilkBottle {metadata.min_milkbottle_version} or higher"
                    )
                    results["valid"] = False
                    results["issues"].append("version_incompatibility")
            except version.InvalidVersion:
                results["warnings"].append(
                    f"Invalid min_milkbottle_version: {metadata.min_milkbottle_version}"
                )

        if metadata.max_milkbottle_version:
            try:
                max_version = version.parse(metadata.max_milkbottle_version)
                current_version = version.parse(self.config.version)
                if current_version > max_version:
                    results["warnings"].append(
                        f"Plugin tested up to MilkBottle {metadata.max_milkbottle_version}"
                    )
                    results["issues"].append("version_untested")
            except version.InvalidVersion:
                results["warnings"].append(
                    f"Invalid max_milkbottle_version: {metadata.max_milkbottle_version}"
                )

        # Check Python version compatibility
        if metadata.python_version:
            try:
                required_version = version.parse(metadata.python_version)
                current_python = version.parse(
                    f"{sys.version_info.major}.{sys.version_info.minor}"
                )
                if current_python < required_version:
                    results["errors"].append(
                        f"Plugin requires Python {metadata.python_version} or higher"
                    )
                    results["valid"] = False
                    results["issues"].append("python_version_incompatibility")
            except version.InvalidVersion:
                results["warnings"].append(
                    f"Invalid python_version: {metadata.python_version}"
                )

        return results

    async def _validate_security(self, plugin_info: PluginInfo) -> Dict[str, Any]:
        """Validate plugin security.

        Args:
            plugin_info: Plugin information to validate

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "issues": []}

        # Check for potentially dangerous imports
        dangerous_imports = [
            "subprocess",
            "os",
            "sys",
            "eval",
            "exec",
            "globals",
            "locals",
        ]

        try:
            # Scan plugin files for dangerous imports
            plugin_path = plugin_info.path
            for py_file in plugin_path.rglob("*.py"):
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    for dangerous_import in dangerous_imports:
                        if (
                            f"import {dangerous_import}" in content
                            or f"from {dangerous_import}" in content
                        ):
                            results["warnings"].append(
                                f"Potentially dangerous import '{dangerous_import}' found in {py_file.name}"
                            )
                            results["issues"].append("dangerous_import")

        except Exception as e:
            results["warnings"].append(f"Could not perform security scan: {e}")

        return results

    def validate_config(
        self, plugin_info: PluginInfo, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate plugin configuration.

        Args:
            plugin_info: Plugin information
            config: Configuration to validate

        Returns:
            Validation results
        """
        results = {"valid": True, "errors": [], "warnings": []}

        # Get plugin interface to validate config
        try:
            plugin = self._load_plugin(plugin_info)
            if (
                plugin
                and hasattr(plugin, "validate_config")
                and not plugin.validate_config(config)
            ):
                results["errors"].append("Configuration validation failed")
                results["valid"] = False
        except Exception as e:
            results["warnings"].append(f"Could not validate configuration: {e}")

        return results

    def _load_plugin(self, plugin_info: PluginInfo) -> Optional[Any]:
        """Load plugin for validation.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin instance or None if failed
        """
        try:
            import importlib.util
            import sys

            plugin_path = plugin_info.path
            spec = importlib.util.spec_from_file_location(
                plugin_info.metadata.name, plugin_path / "__init__.py"
            )
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_info.metadata.name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "get_plugin_interface"):
                return module.get_plugin_interface()

            return None

        except Exception as e:
            self.logger.error(f"Failed to load plugin for validation: {e}")
            return None
