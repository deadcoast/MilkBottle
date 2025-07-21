"""Advanced plugin system for MilkBottle with dynamic loading and management.

This module provides comprehensive plugin discovery, loading, validation,
and management capabilities for extending MilkBottle functionality.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse
from urllib.request import urlopen

import yaml
from packaging import version
from rich.console import Console
from rich.table import Table

from .errors import PluginError, ValidationError
from .registry import BottleRegistry

logger = logging.getLogger("milkbottle.plugin_system")
console = Console()

# Plugin system constants
PLUGIN_MANIFEST_FILE = "plugin.yaml"
PLUGIN_ENTRY_POINT = "plugin_main"
DEFAULT_PLUGIN_DIRS = ["~/.milkbottle/plugins", "./plugins", "./local_plugins"]
SUPPORTED_PLUGIN_FORMATS = [".zip", ".tar.gz", ".whl"]


class PluginManifest:
    """Plugin manifest with validation and metadata management."""

    def __init__(self, manifest_data: Dict[str, Any]):
        """Initialize plugin manifest.

        Args:
            manifest_data: Plugin manifest data
        """
        self.data = manifest_data
        self._validate_manifest()

    def _validate_manifest(self):
        """Validate plugin manifest structure."""
        required_fields = ["name", "version", "description", "entry_point"]
        for field in required_fields:
            if field not in self.data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate version format
        try:
            version.parse(self.data["version"])
        except version.InvalidVersion as e:
            raise ValidationError(f"Invalid version format: {self.data['version']}") from e

        # Validate entry point
        if not isinstance(self.data["entry_point"], str):
            raise ValidationError("Entry point must be a string")

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.data["name"]

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.data["version"]

    @property
    def description(self) -> str:
        """Get plugin description."""
        return self.data["description"]

    @property
    def entry_point(self) -> str:
        """Get plugin entry point."""
        return self.data["entry_point"]

    @property
    def author(self) -> str:
        """Get plugin author."""
        return self.data.get("author", "Unknown")

    @property
    def dependencies(self) -> List[str]:
        """Get plugin dependencies."""
        return self.data.get("dependencies", [])

    @property
    def capabilities(self) -> List[str]:
        """Get plugin capabilities."""
        return self.data.get("capabilities", [])

    @property
    def config_schema(self) -> Dict[str, Any]:
        """Get plugin configuration schema."""
        return self.data.get("config_schema", {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return self.data.copy()


class PluginLoader:
    """Plugin loader with support for multiple formats and sources."""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """Initialize plugin loader.

        Args:
            plugin_dirs: List of plugin directories to search
        """
        self.plugin_dirs = plugin_dirs or DEFAULT_PLUGIN_DIRS
        self._loaded_plugins: Dict[str, Any] = {}
        self._plugin_metadata: Dict[str, PluginManifest] = {}

    def discover_plugins(self) -> Dict[str, PluginManifest]:
        """Discover all available plugins.

        Returns:
            Dictionary of plugin names to manifests
        """
        plugins = {}

        for plugin_dir in self.plugin_dirs:
            expanded_dir = Path(plugin_dir).expanduser()
            if expanded_dir.exists():
                plugins |= self._scan_plugin_directory(expanded_dir)

        return plugins

    def _scan_plugin_directory(self, plugin_dir: Path) -> Dict[str, PluginManifest]:
        """Scan a plugin directory for plugins.

        Args:
            plugin_dir: Directory to scan

        Returns:
            Dictionary of discovered plugins
        """
        plugins = {}

        for item in plugin_dir.iterdir():
            if item.is_dir():
                # Directory-based plugin
                manifest_path = item / PLUGIN_MANIFEST_FILE
                if manifest_path.exists():
                    try:
                        manifest = self._load_manifest(manifest_path)
                        plugins[manifest.name] = manifest
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {item}: {e}")

            elif item.is_file() and item.suffix in SUPPORTED_PLUGIN_FORMATS:
                # Archive-based plugin
                try:
                    manifest = self._load_archive_plugin(item)
                    plugins[manifest.name] = manifest
                except Exception as e:
                    logger.error(f"Failed to load archive plugin {item}: {e}")

        return plugins

    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        """Load plugin manifest from file.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Plugin manifest
        """
        with open(manifest_path, "r", encoding="utf-8") as f:
            if manifest_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        return PluginManifest(data)

    def _load_archive_plugin(self, archive_path: Path) -> PluginManifest:
        """Load plugin from archive file.

        Args:
            archive_path: Path to plugin archive

        Returns:
            Plugin manifest
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if archive_path.suffix != ".zip":
                # Handle other archive formats
                raise PluginError(f"Unsupported archive format: {archive_path.suffix}")

            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(temp_path)
            # Look for manifest in extracted files
            manifest_path = temp_path / PLUGIN_MANIFEST_FILE
            if not manifest_path.exists():
                # Try subdirectories
                for subdir in temp_path.iterdir():
                    if subdir.is_dir():
                        manifest_path = subdir / PLUGIN_MANIFEST_FILE
                        if manifest_path.exists():
                            break

            if not manifest_path.exists():
                raise PluginError(f"No manifest found in archive: {archive_path}")

            return self._load_manifest(manifest_path)

    def load_plugin(self, plugin_name: str, plugin_dir: Optional[str] = None) -> Any:
        """Load a specific plugin.

        Args:
            plugin_name: Name of plugin to load
            plugin_dir: Optional specific plugin directory

        Returns:
            Loaded plugin module
        """
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]

        # Find plugin manifest
        manifest = self._find_plugin_manifest(plugin_name, plugin_dir)
        if not manifest:
            raise PluginError(f"Plugin not found: {plugin_name}")

        # Load plugin module
        plugin_module = self._load_plugin_module(manifest)
        self._loaded_plugins[plugin_name] = plugin_module
        self._plugin_metadata[plugin_name] = manifest

        logger.info(f"Successfully loaded plugin: {plugin_name} v{manifest.version}")
        return plugin_module

    def _find_plugin_manifest(
        self, plugin_name: str, plugin_dir: Optional[str] = None
    ) -> Optional[PluginManifest]:
        """Find plugin manifest by name.

        Args:
            plugin_name: Name of plugin to find
            plugin_dir: Optional specific plugin directory

        Returns:
            Plugin manifest if found
        """
        if plugin_dir:
            expanded_dir = Path(plugin_dir).expanduser()
            if expanded_dir.exists():
                plugins = self._scan_plugin_directory(expanded_dir)
                return plugins.get(plugin_name)

        # Search all plugin directories
        all_plugins = self.discover_plugins()
        return all_plugins.get(plugin_name)

    def _load_plugin_module(self, manifest: PluginManifest) -> Any:
        """Load plugin module from manifest.

        Args:
            manifest: Plugin manifest

        Returns:
            Loaded plugin module
        """
        try:
            # Import the plugin module
            module = importlib.import_module(manifest.entry_point)

            # Validate plugin interface
            if not hasattr(module, "get_metadata"):
                raise PluginError(
                    f"Plugin {manifest.name} missing get_metadata() method"
                )

            if not hasattr(module, "get_cli"):
                raise PluginError(f"Plugin {manifest.name} missing get_cli() method")

            return module

        except ImportError as e:
            raise PluginError(f"Failed to import plugin {manifest.name}: {e}") from e

    def get_loaded_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins.

        Returns:
            Dictionary of loaded plugins
        """
        return self._loaded_plugins.copy()

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get plugin metadata.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin manifest if found
        """
        return self._plugin_metadata.get(plugin_name)

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if plugin was unloaded
        """
        if plugin_name in self._loaded_plugins:
            del self._loaded_plugins[plugin_name]
            del self._plugin_metadata[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        return False


class PluginManager:
    """Advanced plugin manager with lifecycle management and validation."""

    def __init__(self, registry: Optional[BottleRegistry] = None):
        """Initialize plugin manager.

        Args:
            registry: Optional bottle registry instance
        """
        self.registry = registry or BottleRegistry()
        self.loader = PluginLoader()
        self._active_plugins: Set[str] = set()
        self._plugin_health: Dict[str, Dict[str, Any]] = {}

    def install_plugin(self, plugin_source: str) -> bool:
        """Install a plugin from source.

        Args:
            plugin_source: Plugin source (URL, path, or package name)

        Returns:
            True if installation successful
        """
        try:
            if plugin_source.startswith(("http://", "https://")):
                return self._install_from_url(plugin_source)
            elif Path(plugin_source).exists():
                return self._install_from_path(plugin_source)
            else:
                return self._install_from_package(plugin_source)

        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_source}: {e}")
            return False

    def _install_from_url(self, url: str) -> bool:
        """Install plugin from URL.

        Args:
            url: Plugin download URL

        Returns:
            True if installation successful
        """
        plugin_dir = Path("~/.milkbottle/plugins").expanduser()
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Download plugin
        with urlopen(url) as response:
            filename = urlparse(url).path.split("/")[-1]
            plugin_path = plugin_dir / filename

            with open(plugin_path, "wb") as f:
                f.write(response.read())

        logger.info(f"Downloaded plugin to {plugin_path}")
        return True

    def _install_from_path(self, path: str) -> bool:
        """Install plugin from local path.

        Args:
            path: Local plugin path

        Returns:
            True if installation successful
        """
        plugin_dir = Path("~/.milkbottle/plugins").expanduser()
        plugin_dir.mkdir(parents=True, exist_ok=True)

        source_path = Path(path)
        if source_path.is_file():
            # Copy file
            import shutil

            shutil.copy2(source_path, plugin_dir / source_path.name)
        elif source_path.is_dir():
            # Copy directory
            import shutil

            target_path = plugin_dir / source_path.name
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)

        logger.info(f"Installed plugin from {path}")
        return True

    def _install_from_package(self, package_name: str) -> bool:
        """Install plugin from package.

        Args:
            package_name: Package name

        Returns:
            True if installation successful
        """
        try:
            import subprocess

            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
            )
            logger.info(f"Installed plugin package: {package_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install package {package_name}: {e}")
            return False

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin.

        Args:
            plugin_name: Name of plugin to load

        Returns:
            True if plugin loaded successfully
        """
        try:
            plugin_module = self.loader.load_plugin(plugin_name)

            # Register with registry
            if hasattr(plugin_module, "get_cli"):
                # Add to registry (this would need registry modification)
                self._active_plugins.add(plugin_name)

                # Perform health check
                health_status = self._check_plugin_health(plugin_name, plugin_module)
                self._plugin_health[plugin_name] = health_status

            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False

    def _check_plugin_health(
        self, plugin_name: str, plugin_module: Any
    ) -> Dict[str, Any]:
        """Check plugin health status.

        Args:
            plugin_name: Name of plugin
            plugin_module: Plugin module

        Returns:
            Health status dictionary
        """
        health_status = {
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
        }

        try:
            # Check if plugin has required methods
            required_methods = ["get_metadata", "get_cli"]
            for method in required_methods:
                if not hasattr(plugin_module, method):
                    health_status["errors"].append(f"Missing method: {method}")

            # Check configuration validation
            if hasattr(plugin_module, "validate_config"):
                try:
                    test_config = {"enabled": True}
                    is_valid = plugin_module.validate_config(test_config)
                    if not is_valid:
                        health_status["warnings"].append(
                            "Configuration validation failed"
                        )
                except Exception as e:
                    health_status["errors"].append(f"Config validation error: {e}")

            # Determine overall status
            if health_status["errors"]:
                health_status["status"] = "error"
            elif health_status["warnings"]:
                health_status["status"] = "warning"
            else:
                health_status["status"] = "healthy"

        except Exception as e:
            health_status["status"] = "error"
            health_status["errors"].append(f"Health check failed: {e}")

        return health_status

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if plugin unloaded successfully
        """
        if plugin_name in self._active_plugins:
            self._active_plugins.remove(plugin_name)
            self.loader.unload_plugin(plugin_name)

            if plugin_name in self._plugin_health:
                del self._plugin_health[plugin_name]

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        return False

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins.

        Returns:
            List of plugin information
        """
        plugins = []
        discovered_plugins = self.loader.discover_plugins()

        for name, manifest in discovered_plugins.items():
            plugin_info = {
                "name": name,
                "version": manifest.version,
                "description": manifest.description,
                "author": manifest.author,
                "status": "loaded" if name in self._active_plugins else "available",
                "health": self._plugin_health.get(name, {"status": "unknown"}),
            }
            plugins.append(plugin_info)

        return plugins

    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed plugin status.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin status information
        """
        if plugin_name not in self._active_plugins:
            return None

        manifest = self.loader.get_plugin_metadata(plugin_name)
        health = self._plugin_health.get(plugin_name, {})

        return {
            "name": plugin_name,
            "manifest": manifest.to_dict() if manifest else None,
            "health": health,
            "loaded_at": datetime.now().isoformat(),
        }

    def print_plugin_status(self):
        """Print plugin status table."""
        plugins = self.list_plugins()

        table = Table(title="MilkBottle Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Health", style="red")
        table.add_column("Description", style="white")

        for plugin in plugins:
            health_status = plugin["health"].get("status", "unknown")
            health_color = {
                "healthy": "green",
                "warning": "yellow",
                "error": "red",
                "unknown": "dim",
            }.get(health_status, "dim")

            table.add_row(
                plugin["name"],
                plugin["version"],
                plugin["status"],
                f"[{health_color}]{health_status}[/{health_color}]",
                (
                    plugin["description"][:50] + "..."
                    if len(plugin["description"]) > 50
                    else plugin["description"]
                ),
            )

        console.print(table)


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance.

    Returns:
        Plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def install_plugin(plugin_source: str) -> bool:
    """Install a plugin.

    Args:
        plugin_source: Plugin source

    Returns:
        True if installation successful
    """
    return get_plugin_manager().install_plugin(plugin_source)


def load_plugin(plugin_name: str) -> bool:
    """Load a plugin.

    Args:
        plugin_name: Name of plugin to load

    Returns:
        True if plugin loaded successfully
    """
    return get_plugin_manager().load_plugin(plugin_name)


def unload_plugin(plugin_name: str) -> bool:
    """Unload a plugin.

    Args:
        plugin_name: Name of plugin to unload

    Returns:
        True if plugin unloaded successfully
    """
    return get_plugin_manager().unload_plugin(plugin_name)


def list_plugins() -> List[Dict[str, Any]]:
    """List all available plugins.

    Returns:
        List of plugin information
    """
    return get_plugin_manager().list_plugins()


def print_plugin_status():
    """Print plugin status table."""
    get_plugin_manager().print_plugin_status()
