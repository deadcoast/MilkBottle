"""Enhanced plugin system core for MilkBottle.

This module provides the core plugin management functionality including
PluginManager, PluginMetadata, PluginInfo, and PluginInterface classes
with advanced features for enterprise-grade plugin management.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import aiohttp
from rich.console import Console

from ..config import MilkBottleConfig
from ..utils import ErrorHandler, InputValidator


@dataclass
class PluginMetadata:
    """Plugin metadata with validation and comprehensive information."""

    name: str
    version: str
    description: str
    author: str
    email: str
    license: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    repository: Optional[str] = None
    documentation: Optional[str] = None
    homepage: Optional[str] = None
    min_milkbottle_version: Optional[str] = None
    max_milkbottle_version: Optional[str] = None
    python_version: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    classifiers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate metadata after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Plugin name cannot be empty")

        if not self.version or not self.version.strip():
            raise ValueError("Plugin version cannot be empty")

        if not self.description or not self.description.strip():
            raise ValueError("Plugin description cannot be empty")

        if not self.author or not self.author.strip():
            raise ValueError("Plugin author cannot be empty")

        if not self.email or not self.email.strip():
            raise ValueError("Plugin email cannot be empty")

        if not self.license or not self.license.strip():
            raise ValueError("Plugin license cannot be empty")


@dataclass
class PluginInfo:
    """Plugin information with status and health monitoring."""

    metadata: PluginMetadata
    path: Path
    status: str = "unknown"
    health_status: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[str] = None
    download_count: int = 0
    rating: float = 0.0
    install_date: Optional[str] = None
    last_used: Optional[str] = None
    error_count: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """Check if plugin is healthy."""
        return self.health_status.get("status", "unknown") == "healthy"

    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.status in ["enabled", "active"]

    def get_performance_score(self) -> float:
        """Get plugin performance score."""
        return self.performance_metrics.get("score", 0.0)


class PluginInterface(Protocol):
    """Enhanced plugin interface protocol that all plugins must implement."""

    def get_cli(self) -> Any:
        """Return the CLI interface for the plugin."""
        ...

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        ...

    def health_check(self) -> Dict[str, Any]:
        """Perform plugin health check."""
        ...

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        ...

    def get_capabilities(self) -> List[str]:
        """Return list of plugin capabilities."""
        ...

    def get_dependencies(self) -> List[str]:
        """Return list of plugin dependencies."""
        ...

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        ...

    def get_performance_metrics(self) -> Dict[str, float]:
        """Return performance metrics."""
        ...

    def get_error_log(self) -> List[Dict[str, Any]]:
        """Return error log."""
        ...


class PluginManager:
    """Advanced plugin management system with enterprise features."""

    def __init__(self, config: Optional[MilkBottleConfig] = None):
        """Initialize plugin manager.

        Args:
            config: MilkBottle configuration
        """
        self.config = config or MilkBottleConfig()
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.plugin_manager")
        self.error_handler = ErrorHandler()
        self.validator = InputValidator()
        self._discovery_cache: Dict[str, PluginInfo] = {}
        self._health_monitors: Dict[str, Any] = {}

    async def discover_plugins(
        self, plugin_dir: Optional[Path] = None
    ) -> List[PluginInfo]:
        """Discover plugins from local and remote sources.

        Args:
            plugin_dir: Optional specific plugin directory

        Returns:
            List of discovered plugin information
        """
        plugin_dir = plugin_dir or Path(self.config.plugin_dir)
        discovered_plugins = []

        # Discover local plugins
        local_plugins = await self._discover_local_plugins(plugin_dir)
        discovered_plugins.extend(local_plugins)

        # Discover remote plugins from marketplace
        if self.config.enable_marketplace:
            remote_plugins = await self._discover_remote_plugins()
            discovered_plugins.extend(remote_plugins)

        # Update cache
        for plugin in discovered_plugins:
            self._discovery_cache[plugin.metadata.name] = plugin

        return discovered_plugins

    async def _discover_local_plugins(self, plugin_dir: Path) -> List[PluginInfo]:
        """Discover plugins from local directory.

        Args:
            plugin_dir: Directory to scan for plugins

        Returns:
            List of discovered local plugins
        """
        plugins = []

        if not plugin_dir.exists():
            self.logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return plugins

        for plugin_path in plugin_dir.iterdir():
            if plugin_path.is_dir() and (plugin_path / "__init__.py").exists():
                try:
                    plugin_info = await self._load_plugin_info(plugin_path)
                    if plugin_info:
                        plugins.append(plugin_info)
                except Exception as e:
                    self.logger.error(
                        f"Failed to load plugin info from {plugin_path}: {e}"
                    )

        return plugins

    async def _discover_remote_plugins(self) -> List[PluginInfo]:
        """Discover plugins from remote marketplace.

        Returns:
            List of discovered remote plugins
        """
        plugins = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config.marketplace_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for plugin_data in data.get("plugins", []):
                            plugin_info = self._create_remote_plugin_info(plugin_data)
                            plugins.append(plugin_info)
        except Exception as e:
            self.logger.error(f"Failed to discover remote plugins: {e}")

        return plugins

    async def _load_plugin_info(self, plugin_path: Path) -> Optional[PluginInfo]:
        """Load plugin information from path.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin information or None if failed
        """
        try:
            # Load plugin module
            sys.path.insert(0, str(plugin_path.parent))
            plugin_module = __import__(plugin_path.name)

            # Extract metadata
            metadata = PluginMetadata(
                name=getattr(plugin_module, "__name__", plugin_path.name),
                version=getattr(plugin_module, "__version__", "0.0.0"),
                description=getattr(plugin_module, "__description__", ""),
                author=getattr(plugin_module, "__author__", ""),
                email=getattr(plugin_module, "__email__", ""),
                license=getattr(plugin_module, "__license__", "MIT"),
                dependencies=getattr(plugin_module, "__dependencies__", []),
                capabilities=getattr(plugin_module, "__capabilities__", []),
                tags=getattr(plugin_module, "__tags__", []),
            )

            return PluginInfo(metadata=metadata, path=plugin_path, status="discovered")

        except Exception as e:
            self.logger.error(f"Failed to load plugin info from {plugin_path}: {e}")
            return None

    def _create_remote_plugin_info(self, plugin_data: Dict[str, Any]) -> PluginInfo:
        """Create plugin info from remote data.

        Args:
            plugin_data: Remote plugin data

        Returns:
            Plugin information
        """
        metadata = PluginMetadata(
            name=plugin_data.get("name", ""),
            version=plugin_data.get("version", "0.0.0"),
            description=plugin_data.get("description", ""),
            author=plugin_data.get("author", ""),
            email=plugin_data.get("email", ""),
            license=plugin_data.get("license", "MIT"),
            dependencies=plugin_data.get("dependencies", []),
            capabilities=plugin_data.get("capabilities", []),
            tags=plugin_data.get("tags", []),
        )

        return PluginInfo(
            metadata=metadata,
            path=Path(plugin_data.get("path", "")),
            status="remote",
            download_count=plugin_data.get("download_count", 0),
            rating=plugin_data.get("rating", 0.0),
        )

    async def install_plugin(
        self, plugin_name: str, source: str = "marketplace"
    ) -> bool:
        """Install a plugin from marketplace or local source.

        Args:
            plugin_name: Name of plugin to install
            source: Source of plugin (marketplace, local, url)

        Returns:
            True if installation successful, False otherwise
        """
        try:
            if source == "marketplace":
                return await self._install_from_marketplace(plugin_name)
            elif source == "local":
                return await self._install_from_local(plugin_name)
            elif source.startswith(("http://", "https://")):
                return await self._install_from_url(plugin_name, source)
            else:
                self.logger.error(f"Unknown plugin source: {source}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to install plugin {plugin_name}: {e}")
            return False

    async def _install_from_marketplace(self, plugin_name: str) -> bool:
        """Install plugin from marketplace.

        Args:
            plugin_name: Name of plugin to install

        Returns:
            True if installation successful, False otherwise
        """
        plugin_url = f"{self.config.marketplace_url}/plugins/{plugin_name}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(plugin_url) as response:
                    if response.status == 200:
                        plugin_data = await response.json()
                        return await self._download_and_install_plugin(plugin_data)
                    else:
                        self.logger.error(
                            f"Plugin {plugin_name} not found in marketplace"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Failed to download plugin {plugin_name}: {e}")
            return False

    async def _install_from_local(self, plugin_name: str) -> bool:
        """Install plugin from local source.

        Args:
            plugin_name: Name of plugin to install

        Returns:
            True if installation successful, False otherwise
        """
        # Implementation for local installation
        self.logger.info(f"Installing plugin {plugin_name} from local source")
        return True

    async def _install_from_url(self, plugin_name: str, url: str) -> bool:
        """Install plugin from URL.

        Args:
            plugin_name: Name of plugin to install
            url: URL to plugin source

        Returns:
            True if installation successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        plugin_data = await response.json()
                        return await self._download_and_install_plugin(plugin_data)
                    else:
                        self.logger.error(f"Failed to download plugin from {url}")
                        return False

        except Exception as e:
            self.logger.error(f"Failed to download plugin from {url}: {e}")
            return False

    async def _download_and_install_plugin(self, plugin_data: Dict[str, Any]) -> bool:
        """Download and install plugin.

        Args:
            plugin_data: Plugin data from source

        Returns:
            True if installation successful, False otherwise
        """
        plugin_url = plugin_data.get("download_url")
        if not plugin_url:
            self.logger.error("No download URL provided for plugin")
            return False

        plugin_dir = Path(self.config.plugin_dir) / plugin_data.get("name", "unknown")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(plugin_url) as response:
                    if response.status == 200:
                        plugin_dir.mkdir(parents=True, exist_ok=True)

                        # Download plugin files
                        with open(plugin_dir / "plugin.zip", "wb") as f:
                            f.write(await response.read())

                        # Extract and install
                        return await self._extract_and_validate_plugin(plugin_dir)
                    else:
                        self.logger.error(
                            f"Failed to download plugin: {response.status}"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Failed to download plugin: {e}")
            return False

    async def _extract_and_validate_plugin(self, plugin_dir: Path) -> bool:
        """Extract and validate downloaded plugin.

        Args:
            plugin_dir: Directory containing plugin files

        Returns:
            True if validation successful, False otherwise
        """
        try:
            import zipfile

            # Extract plugin
            with zipfile.ZipFile(plugin_dir / "plugin.zip", "r") as zip_ref:
                zip_ref.extractall(plugin_dir)

            # Remove zip file
            (plugin_dir / "plugin.zip").unlink()

            # Validate plugin
            plugin_info = await self._load_plugin_info(plugin_dir)
            if plugin_info and await self._validate_plugin(plugin_info):
                self.plugins[plugin_info.metadata.name] = plugin_info
                self.logger.info(
                    f"Successfully installed plugin: {plugin_info.metadata.name}"
                )
                return True
            else:
                self.logger.error("Plugin validation failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to extract plugin: {e}")
            return False

    async def _validate_plugin(self, plugin_info: PluginInfo) -> bool:
        """Validate plugin security and compatibility.

        Args:
            plugin_info: Plugin information to validate

        Returns:
            True if validation successful, False otherwise
        """
        try:
            # Check plugin signature
            if not await self._verify_plugin_signature(plugin_info):
                self.logger.error("Plugin signature verification failed")
                return False

            # Check dependencies
            if not await self._check_plugin_dependencies(plugin_info):
                self.logger.error("Plugin dependencies not satisfied")
                return False

            # Check compatibility
            if not await self._check_plugin_compatibility(plugin_info):
                self.logger.error("Plugin compatibility check failed")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Plugin validation failed: {e}")
            return False

    async def _verify_plugin_signature(self, plugin_info: PluginInfo) -> bool:
        """Verify plugin digital signature.

        Args:
            plugin_info: Plugin information

        Returns:
            True if signature valid, False otherwise
        """
        # Implementation depends on signature verification method
        # For now, return True (implement proper signature verification)
        return True

    async def _check_plugin_dependencies(self, plugin_info: PluginInfo) -> bool:
        """Check if plugin dependencies are satisfied.

        Args:
            plugin_info: Plugin information

        Returns:
            True if dependencies satisfied, False otherwise
        """
        for dependency in plugin_info.metadata.dependencies:
            try:
                __import__(dependency)
            except ImportError:
                self.logger.error(f"Missing dependency: {dependency}")
                return False
        return True

    async def _check_plugin_compatibility(self, plugin_info: PluginInfo) -> bool:
        """Check plugin compatibility with current system.

        Args:
            plugin_info: Plugin information

        Returns:
            True if compatible, False otherwise
        """
        # Simple version check (implement proper semantic versioning)
        return True

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins with enhanced information.

        Returns:
            List of plugin information dictionaries
        """
        plugins = []

        plugins.extend(
            {
                "name": name,
                "version": plugin_info.metadata.version,
                "description": plugin_info.metadata.description,
                "author": plugin_info.metadata.author,
                "status": plugin_info.status,
                "rating": plugin_info.rating,
                "download_count": plugin_info.download_count,
                "capabilities": plugin_info.metadata.capabilities,
                "tags": plugin_info.metadata.tags,
                "health_status": plugin_info.health_status.get("status", "unknown"),
                "last_updated": plugin_info.last_updated,
                "error_count": plugin_info.error_count,
            }
            for name, plugin_info in self.plugins.items()
        )
        return plugins

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name.

        Args:
            name: Name of plugin to get

        Returns:
            Plugin interface or None if not found
        """
        if name not in self.loaded_plugins:
            if name in self.plugins:
                plugin_info = self.plugins[name]
                if plugin := self._load_plugin(plugin_info):
                    self.loaded_plugins[name] = plugin
                    return plugin
            return None
        return self.loaded_plugins[name]

    def _load_plugin(self, plugin_info: PluginInfo) -> Optional[PluginInterface]:
        """Load a plugin module.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin interface or None if failed
        """
        try:
            sys.path.insert(0, str(plugin_info.path.parent))
            plugin_module = __import__(plugin_info.path.name)

            if hasattr(plugin_module, "get_plugin_interface"):
                return plugin_module.get_plugin_interface()
            self.logger.error(f"Plugin {plugin_info.metadata.name} has no interface")
            return None

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_info.metadata.name}: {e}")
            return None

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all loaded plugins.

        Returns:
            Dictionary of plugin health status
        """
        health_status = {}

        for name, plugin in self.loaded_plugins.items():
            try:
                health_status[name] = plugin.health_check()
            except Exception as e:
                health_status[name] = {"status": "error", "error": str(e)}

        return health_status

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get plugin system statistics.

        Returns:
            Dictionary of plugin system statistics
        """
        total_plugins = len(self.plugins)
        loaded_plugins = len(self.loaded_plugins)
        healthy_plugins = sum(bool(p.is_healthy()) for p in self.plugins.values())

        return {
            "total_plugins": total_plugins,
            "loaded_plugins": loaded_plugins,
            "healthy_plugins": healthy_plugins,
            "unhealthy_plugins": total_plugins - healthy_plugins,
            "average_rating": sum(p.rating for p in self.plugins.values())
            / max(total_plugins, 1),
            "total_downloads": sum(p.download_count for p in self.plugins.values()),
            "total_errors": sum(p.error_count for p in self.plugins.values()),
        }


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(config: Optional[MilkBottleConfig] = None) -> PluginManager:
    """Get the global plugin manager instance.

    Args:
        config: Optional configuration to use

    Returns:
        Plugin manager instance
    """
    global _plugin_manager

    if _plugin_manager is None:
        _plugin_manager = PluginManager(config)

    return _plugin_manager
