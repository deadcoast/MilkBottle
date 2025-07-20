"""Plugin discovery system for MilkBottle.

This module provides advanced plugin discovery capabilities including
local file system scanning, remote marketplace integration, and
caching for performance optimization.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import PluginInfo, PluginMetadata


class PluginDiscovery:
    """Advanced plugin discovery system."""

    def __init__(self, config: Any):
        """Initialize plugin discovery.

        Args:
            config: MilkBottle configuration
        """
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.plugin_discovery")
        self._cache: Dict[str, PluginInfo] = {}
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

    async def discover_all_plugins(
        self, force_refresh: bool = False
    ) -> List[PluginInfo]:
        """Discover all available plugins from all sources.

        Args:
            force_refresh: Force refresh of cached results

        Returns:
            List of discovered plugins
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            self.logger.debug("Using cached plugin discovery results")
            return list(self._cache.values())

        discovered_plugins = []

        # Discover local plugins
        local_plugins = await self.discover_local_plugins()
        discovered_plugins.extend(local_plugins)

        # Discover remote plugins
        if self.config.enable_marketplace:
            remote_plugins = await self.discover_remote_plugins()
            discovered_plugins.extend(remote_plugins)

        # Update cache
        self._update_cache(discovered_plugins)

        return discovered_plugins

    async def discover_local_plugins(
        self, plugin_dir: Optional[Path] = None
    ) -> List[PluginInfo]:
        """Discover plugins from local file system.

        Args:
            plugin_dir: Optional specific plugin directory

        Returns:
            List of discovered local plugins
        """
        plugin_dir = plugin_dir or Path(self.config.plugin_dir).expanduser()
        plugins = []

        if not plugin_dir.exists():
            self.logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return plugins

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Discovering local plugins...", total=None)

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

            progress.update(task, completed=True)

        self.logger.info(f"Discovered {len(plugins)} local plugins")
        return plugins

    async def discover_remote_plugins(self) -> List[PluginInfo]:
        """Discover plugins from remote marketplace.

        Returns:
            List of discovered remote plugins
        """
        plugins = []

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Discovering remote plugins...", total=None)

                async with aiohttp.ClientSession() as session:
                    async with session.get(self.config.marketplace_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            for plugin_data in data.get("plugins", []):
                                plugin_info = self._create_remote_plugin_info(
                                    plugin_data
                                )
                                plugins.append(plugin_info)
                        else:
                            self.logger.error(
                                f"Failed to fetch marketplace data: {response.status}"
                            )

                progress.update(task, completed=True)

        except Exception as e:
            self.logger.error(f"Failed to discover remote plugins: {e}")

        self.logger.info(f"Discovered {len(plugins)} remote plugins")
        return plugins

    async def _load_plugin_info(self, plugin_path: Path) -> Optional[PluginInfo]:
        """Load plugin information from path.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin information or None if failed
        """
        try:
            # Try to load plugin.yaml first
            manifest_path = plugin_path / "plugin.yaml"
            if manifest_path.exists():
                return await self._load_from_manifest(manifest_path, plugin_path)

            # Try to load from __init__.py
            init_path = plugin_path / "__init__.py"
            return (
                await self._load_from_init(plugin_path) if init_path.exists() else None
            )
        except Exception as e:
            self.logger.error(f"Failed to load plugin info from {plugin_path}: {e}")
            return None

    async def _load_from_manifest(
        self, manifest_path: Path, plugin_path: Path
    ) -> Optional[PluginInfo]:
        """Load plugin info from manifest file.

        Args:
            manifest_path: Path to manifest file
            plugin_path: Path to plugin directory

        Returns:
            Plugin information or None if failed
        """
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            metadata = PluginMetadata(
                name=data.get("name", plugin_path.name),
                version=data.get("version", "0.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                email=data.get("email", ""),
                license=data.get("license", "MIT"),
                dependencies=data.get("dependencies", []),
                capabilities=data.get("capabilities", []),
                tags=data.get("tags", []),
                repository=data.get("repository"),
                documentation=data.get("documentation"),
                homepage=data.get("homepage"),
                min_milkbottle_version=data.get("min_milkbottle_version"),
                max_milkbottle_version=data.get("max_milkbottle_version"),
                python_version=data.get("python_version"),
                keywords=data.get("keywords", []),
                classifiers=data.get("classifiers", []),
            )

            return PluginInfo(metadata=metadata, path=plugin_path, status="discovered")

        except Exception as e:
            self.logger.error(f"Failed to load manifest from {manifest_path}: {e}")
            return None

    async def _load_from_init(self, plugin_path: Path) -> Optional[PluginInfo]:
        """Load plugin info from __init__.py file.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin information or None if failed
        """
        try:
            import importlib.util
            import sys

            # Load module
            spec = importlib.util.spec_from_file_location(
                plugin_path.name, plugin_path / "__init__.py"
            )
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create module spec for {plugin_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_path.name] = module
            spec.loader.exec_module(module)

            # Extract metadata
            metadata = PluginMetadata(
                name=getattr(module, "__name__", plugin_path.name),
                version=getattr(module, "__version__", "0.0.0"),
                description=getattr(module, "__description__", ""),
                author=getattr(module, "__author__", ""),
                email=getattr(module, "__email__", ""),
                license=getattr(module, "__license__", "MIT"),
                dependencies=getattr(module, "__dependencies__", []),
                capabilities=getattr(module, "__capabilities__", []),
                tags=getattr(module, "__tags__", []),
            )

            return PluginInfo(metadata=metadata, path=plugin_path, status="discovered")

        except Exception as e:
            self.logger.error(f"Failed to load from __init__.py: {e}")
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

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid.

        Returns:
            True if cache is valid, False otherwise
        """
        if not self._cache_timestamp:
            return False

        import time

        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _update_cache(self, plugins: List[PluginInfo]) -> None:
        """Update discovery cache.

        Args:
            plugins: List of plugins to cache
        """
        import time

        self._cache.clear()
        for plugin in plugins:
            self._cache[plugin.metadata.name] = plugin

        self._cache_timestamp = time.time()

    def clear_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache.clear()
        self._cache_timestamp = None

    def get_cached_plugins(self) -> List[PluginInfo]:
        """Get cached plugins.

        Returns:
            List of cached plugins
        """
        return list(self._cache.values())

    def search_plugins(
        self, query: str, search_fields: Optional[List[str]] = None
    ) -> List[PluginInfo]:
        """Search plugins by query.

        Args:
            query: Search query
            search_fields: Fields to search in (name, description, tags, etc.)

        Returns:
            List of matching plugins
        """
        if search_fields is None:
            search_fields = ["name", "description", "tags", "capabilities"]

        query_lower = query.lower()
        matching_plugins = []

        for plugin in self._cache.values():
            for field in search_fields:
                if field == "name" and query_lower in plugin.metadata.name.lower():
                    matching_plugins.append(plugin)
                    break
                elif (
                    field == "description"
                    and query_lower in plugin.metadata.description.lower()
                ):
                    matching_plugins.append(plugin)
                    break
                elif field == "tags" and any(
                    query_lower in tag.lower() for tag in plugin.metadata.tags
                ):
                    matching_plugins.append(plugin)
                    break
                elif field == "capabilities" and any(
                    query_lower in cap.lower() for cap in plugin.metadata.capabilities
                ):
                    matching_plugins.append(plugin)
                    break

        return matching_plugins
