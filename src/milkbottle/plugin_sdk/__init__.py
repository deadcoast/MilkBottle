"""MilkBottle Plugin SDK - Development tools for plugin creators.

This package provides comprehensive tools for creating, validating, testing,
and packaging MilkBottle plugins with enterprise-grade features.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .generator import PluginGenerator
from .packaging import PluginPackager
from .templates import PluginTemplate
from .testing import PluginTester
from .validator import PluginValidator

logger = logging.getLogger("milkbottle.plugin_sdk")


class PluginSDK:
    """Plugin development SDK for MilkBottle."""

    def __init__(self, sdk_path: Optional[Path] = None):
        """Initialize the Plugin SDK.

        Args:
            sdk_path: Optional custom SDK path
        """
        self.sdk_path = sdk_path or Path(__file__).parent
        self.template_manager = PluginTemplate(self.sdk_path)
        self.generator = PluginGenerator()
        self.validator = PluginValidator()
        self.tester = PluginTester()
        self.packager = PluginPackager()

        logger.info("MilkBottle Plugin SDK initialized")

    def create_plugin(
        self,
        name: str,
        template: str = "basic",
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> bool:
        """Create a new plugin from template.

        Args:
            name: Plugin name
            template: Template to use (basic, cli, web, etc.)
            output_dir: Output directory (defaults to current directory)
            **kwargs: Additional template parameters

        Returns:
            True if creation successful, False otherwise
        """
        try:
            output_dir = output_dir or Path.cwd() / name

            # Generate plugin structure
            success = self.generator.generate_plugin(
                name=name,
                template=template,
                output_dir=output_dir,
                template_manager=self.template_manager,
                **kwargs,
            )

            if success:
                logger.info(f"Successfully created plugin: {name}")
                return True
            else:
                logger.error(f"Failed to create plugin: {name}")
                return False

        except Exception as e:
            logger.error(f"Error creating plugin {name}: {e}")
            return False

    def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate a plugin for compliance.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Validation results
        """
        return self.validator.validate_plugin(plugin_path)

    def test_plugin(self, plugin_path: Path, test_type: str = "all") -> Dict[str, Any]:
        """Run tests for a plugin.

        Args:
            plugin_path: Path to plugin directory
            test_type: Type of tests to run (unit, integration, all)

        Returns:
            Test results
        """
        return self.tester.test_plugin(plugin_path, test_type)

    def package_plugin(
        self, plugin_path: Path, output_path: Optional[Path] = None, format: str = "zip"
    ) -> bool:
        """Package a plugin for distribution.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for package
            format: Package format (zip, tar.gz, wheel)

        Returns:
            True if packaging successful, False otherwise
        """
        return self.packager.package_plugin(plugin_path, output_path, format)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List available plugin templates.

        Returns:
            List of available templates with descriptions
        """
        return self.template_manager.list_templates()

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template.

        Args:
            template_name: Name of template

        Returns:
            Template information or None if not found
        """
        return self.template_manager.get_template_info(template_name)

    def create_template(
        self, template_name: str, template_path: Path, description: str = ""
    ) -> bool:
        """Create a new plugin template.

        Args:
            template_name: Name of the template
            template_path: Path to template files
            description: Template description

        Returns:
            True if creation successful, False otherwise
        """
        return self.template_manager.create_template(
            template_name, template_path, description
        )

    def build_plugin(self, plugin_path: Path, build_type: str = "development") -> bool:
        """Build a plugin for development or production.

        Args:
            plugin_path: Path to plugin directory
            build_type: Build type (development, production)

        Returns:
            True if build successful, False otherwise
        """
        try:
            # Validate plugin
            validation_results = self.validate_plugin(plugin_path)
            if not validation_results.get("valid", False):
                logger.error("Plugin validation failed")
                return False

            # Run tests
            test_results = self.test_plugin(plugin_path)
            if not test_results.get("success", False):
                logger.error("Plugin tests failed")
                return False

            # Package plugin
            if build_type == "production":
                return self.package_plugin(plugin_path)

            return True

        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False

    def get_plugin_info(self, plugin_path: Path) -> Dict[str, Any]:
        """Get comprehensive information about a plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin information
        """
        info = {
            "path": str(plugin_path),
            "exists": plugin_path.exists(),
            "validation": {},
            "tests": {},
            "metadata": {},
        }

        if plugin_path.exists():
            # Get validation results
            info["validation"] = self.validate_plugin(plugin_path)

            # Get test results
            info["tests"] = self.test_plugin(plugin_path)

            # Get metadata
            try:
                from milkbottle.plugin_system.core import PluginMetadata

                # This would require loading the plugin to get metadata
                info["metadata"] = {"status": "loaded"}
            except Exception as e:
                info["metadata"] = {"error": str(e)}

        return info


# Global SDK instance
_sdk_instance: Optional[PluginSDK] = None


def get_sdk() -> PluginSDK:
    """Get the global Plugin SDK instance.

    Returns:
        Plugin SDK instance
    """
    global _sdk_instance

    if _sdk_instance is None:
        _sdk_instance = PluginSDK()

    return _sdk_instance


# Convenience functions
def create_plugin(
    name: str, template: str = "basic", output_dir: Optional[Path] = None, **kwargs
) -> bool:
    """Create a new plugin.

    Args:
        name: Plugin name
        template: Template to use
        output_dir: Output directory
        **kwargs: Additional parameters

    Returns:
        True if creation successful, False otherwise
    """
    return get_sdk().create_plugin(name, template, output_dir, **kwargs)


def validate_plugin(plugin_path: Path) -> Dict[str, Any]:
    """Validate a plugin.

    Args:
        plugin_path: Path to plugin directory

    Returns:
        Validation results
    """
    return get_sdk().validate_plugin(plugin_path)


def test_plugin(plugin_path: Path, test_type: str = "all") -> Dict[str, Any]:
    """Test a plugin.

    Args:
        plugin_path: Path to plugin directory
        test_type: Type of tests to run

    Returns:
        Test results
    """
    return get_sdk().test_plugin(plugin_path, test_type)


def package_plugin(
    plugin_path: Path, output_path: Optional[Path] = None, format: str = "zip"
) -> bool:
    """Package a plugin.

    Args:
        plugin_path: Path to plugin directory
        output_path: Output path for package
        format: Package format

    Returns:
        True if packaging successful, False otherwise
    """
    return get_sdk().package_plugin(plugin_path, output_path, format)


def list_templates() -> List[Dict[str, Any]]:
    """List available templates.

    Returns:
        List of available templates
    """
    return get_sdk().list_templates()


def build_plugin(plugin_path: Path, build_type: str = "development") -> bool:
    """Build a plugin.

    Args:
        plugin_path: Path to plugin directory
        build_type: Build type

    Returns:
        True if build successful, False otherwise
    """
    return get_sdk().build_plugin(plugin_path, build_type)


__all__ = [
    "PluginSDK",
    "get_sdk",
    "create_plugin",
    "validate_plugin",
    "test_plugin",
    "package_plugin",
    "list_templates",
    "build_plugin",
]
