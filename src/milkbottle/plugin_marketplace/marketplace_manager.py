"""Marketplace Manager - Centralized plugin marketplace management."""

from __future__ import annotations

import contextlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
from rich.console import Console

from ..config import MilkBottleConfig
from ..utils import ErrorHandler, InputValidator


@dataclass
class PluginListing:
    """Plugin marketplace listing."""

    name: str
    version: str
    description: str
    author: str
    license: str
    repository: Optional[str] = None
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    download_url: Optional[str] = None
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    verified: bool = False
    featured: bool = False


@dataclass
class SearchFilters:
    """Search filters for marketplace."""

    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    min_rating: Optional[float] = None
    verified_only: bool = False
    featured_only: bool = False
    sort_by: str = "downloads"  # downloads, rating, updated, name
    sort_order: str = "desc"  # asc, desc


class MarketplaceManager:
    """Centralized plugin marketplace management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.marketplace")
        self.error_handler = ErrorHandler()
        self.validator = InputValidator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_dir = Path.home() / ".milkbottle" / "marketplace_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def search_plugins(
        self, query: str = "", filters: Optional[SearchFilters] = None
    ) -> List[PluginListing]:
        """Search for plugins in the marketplace."""
        try:
            self.logger.info(f"Searching plugins with query: {query}")

            # Get all plugins
            all_plugins = await self._fetch_plugin_listings()

            # Apply search filters
            filtered_plugins = self._apply_search_filters(all_plugins, query, filters)

            return self._sort_plugins(
                filtered_plugins,
                filters.sort_by if filters else "downloads",
                filters.sort_order if filters else "desc",
            )
        except Exception as e:
            self.logger.error(f"Failed to search plugins: {e}")
            return []

    async def get_plugin_details(self, plugin_name: str) -> Optional[PluginListing]:
        """Get detailed information about a specific plugin."""
        try:
            self.logger.info(f"Getting details for plugin: {plugin_name}")

            # Check cache first
            cache_file = self.cache_dir / f"{plugin_name}_details.json"
            if cache_file.exists():
                with contextlib.suppress(Exception):
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        return PluginListing(**data)
            # Fetch from marketplace
            plugin_url = urljoin(self.config.marketplace_url, f"plugins/{plugin_name}")

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(plugin_url) as response:
                if response.status == 200:
                    data = await response.json()
                    plugin = PluginListing(**data)

                    # Cache the result
                    with open(cache_file, "w") as f:
                        json.dump(data, f)

                    return plugin
                else:
                    self.logger.error(f"Plugin {plugin_name} not found")
                    return None

        except Exception as e:
            self.logger.error(f"Failed to get plugin details: {e}")
            return None

    async def install_plugin(
        self, plugin_name: str, version: Optional[str] = None
    ) -> bool:
        """Install a plugin from the marketplace."""
        try:
            self.logger.info(f"Installing plugin: {plugin_name}")

            # Get plugin details
            plugin = await self.get_plugin_details(plugin_name)
            if not plugin:
                self.logger.error(f"Plugin {plugin_name} not found")
                return False

            # Check if specific version is requested
            if version and plugin.version != version:
                self.logger.error(f"Version {version} not available for {plugin_name}")
                return False

            # Download plugin
            if not plugin.download_url:
                self.logger.error(f"No download URL for plugin {plugin_name}")
                return False

            download_success = await self._download_plugin(plugin)
            if not download_success:
                return False

            # Install plugin
            install_success = await self._install_downloaded_plugin(plugin)
            if not install_success:
                return False

            # Update download count
            await self._update_download_count(plugin_name)

            self.logger.info(f"Successfully installed plugin: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to install plugin {plugin_name}: {e}")
            return False

    async def update_plugin(self, plugin_name: str) -> bool:
        """Update an installed plugin."""
        try:
            self.logger.info(f"Updating plugin: {plugin_name}")

            # Get current version
            current_version = await self._get_installed_version(plugin_name)
            if not current_version:
                self.logger.error(f"Plugin {plugin_name} not installed")
                return False

            # Get latest version
            plugin = await self.get_plugin_details(plugin_name)
            if not plugin:
                self.logger.error(f"Plugin {plugin_name} not found in marketplace")
                return False

            # Check if update is needed
            if plugin.version == current_version:
                self.logger.info(f"Plugin {plugin_name} is already up to date")
                return True

            # Install new version
            return await self.install_plugin(plugin_name, plugin.version)

        except Exception as e:
            self.logger.error(f"Failed to update plugin {plugin_name}: {e}")
            return False

    async def rate_plugin(
        self, plugin_name: str, rating: float, review: Optional[str] = None
    ) -> bool:
        """Rate a plugin."""
        try:
            self.logger.info(f"Rating plugin {plugin_name} with {rating} stars")

            if not 1.0 <= rating <= 5.0:
                self.logger.error("Rating must be between 1.0 and 5.0")
                return False

            # Submit rating to marketplace
            rating_data = {
                "plugin_name": plugin_name,
                "rating": rating,
                "review": review,
                "user_id": self._get_user_id(),
            }

            rating_url = urljoin(
                self.config.marketplace_url, f"plugins/{plugin_name}/rate"
            )

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(rating_url, json=rating_data) as response:
                if response.status == 200:
                    self.logger.info(f"Successfully rated plugin {plugin_name}")
                    return True
                else:
                    self.logger.error(f"Failed to submit rating: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to rate plugin: {e}")
            return False

    async def list_featured_plugins(self) -> List[PluginListing]:
        """List featured plugins."""
        try:
            self.logger.info("Getting featured plugins")

            all_plugins = await self._fetch_plugin_listings()
            return [p for p in all_plugins if p.featured]
        except Exception as e:
            self.logger.error(f"Failed to get featured plugins: {e}")
            return []

    async def list_popular_plugins(self, limit: int = 10) -> List[PluginListing]:
        """List popular plugins by download count."""
        try:
            self.logger.info(f"Getting top {limit} popular plugins")

            all_plugins = await self._fetch_plugin_listings()
            popular_plugins = sorted(
                all_plugins, key=lambda p: p.download_count, reverse=True
            )

            return popular_plugins[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get popular plugins: {e}")
            return []

    async def list_recent_plugins(self, limit: int = 10) -> List[PluginListing]:
        """List recently updated plugins."""
        try:
            self.logger.info(f"Getting {limit} recently updated plugins")

            all_plugins = await self._fetch_plugin_listings()
            recent_plugins = sorted(
                all_plugins, key=lambda p: p.last_updated or "", reverse=True
            )

            return recent_plugins[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get recent plugins: {e}")
            return []

    async def _fetch_plugin_listings(self) -> List[PluginListing]:
        """Fetch all plugin listings from marketplace."""
        try:
            # Check cache first
            cache_file = self.cache_dir / "plugin_listings.json"
            if cache_file.exists():
                with contextlib.suppress(Exception):
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        return [PluginListing(**plugin_data) for plugin_data in data]
            # Fetch from marketplace
            listings_url = urljoin(self.config.marketplace_url, "plugins")

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(listings_url) as response:
                if response.status == 200:
                    data = await response.json()
                    plugins = [
                        PluginListing(**plugin_data)
                        for plugin_data in data.get("plugins", [])
                    ]

                    # Cache the result
                    with open(cache_file, "w") as f:
                        json.dump([p.__dict__ for p in plugins], f)

                    return plugins
                else:
                    self.logger.error(
                        f"Failed to fetch plugin listings: {response.status}"
                    )
                    return []

        except Exception as e:
            self.logger.error(f"Failed to fetch plugin listings: {e}")
            return []

    def _apply_search_filters(
        self, plugins: List[PluginListing], query: str, filters: Optional[SearchFilters]
    ) -> List[PluginListing]:
        """Apply search filters to plugin list."""
        filtered_plugins = plugins

        # Apply text search
        if query:
            query_lower = query.lower()
            filtered_plugins = [
                p
                for p in filtered_plugins
                if (
                    query_lower in p.name.lower()
                    or query_lower in p.description.lower()
                    or any(query_lower in tag.lower() for tag in p.tags)
                )
            ]

        if not filters:
            return filtered_plugins

        # Apply category filter
        if filters.category:
            filtered_plugins = [
                p for p in filtered_plugins if filters.category in p.tags
            ]

        # Apply tag filters
        if filters.tags:
            filtered_plugins = [
                p
                for p in filtered_plugins
                if all(tag in p.tags for tag in filters.tags)
            ]

        # Apply author filter
        if filters.author:
            filtered_plugins = [
                p
                for p in filtered_plugins
                if filters.author.lower() in p.author.lower()
            ]

        # Apply rating filter
        if filters.min_rating:
            filtered_plugins = [
                p for p in filtered_plugins if p.rating >= filters.min_rating
            ]

        # Apply verified filter
        if filters.verified_only:
            filtered_plugins = [p for p in filtered_plugins if p.verified]

        # Apply featured filter
        if filters.featured_only:
            filtered_plugins = [p for p in filtered_plugins if p.featured]

        return filtered_plugins

    def _sort_plugins(
        self, plugins: List[PluginListing], sort_by: str, sort_order: str
    ) -> List[PluginListing]:
        """Sort plugins by specified criteria."""
        reverse = sort_order.lower() == "desc"

        if sort_by == "downloads":
            return sorted(plugins, key=lambda p: p.download_count, reverse=reverse)
        elif sort_by == "rating":
            return sorted(plugins, key=lambda p: p.rating, reverse=reverse)
        elif sort_by == "updated":
            return sorted(plugins, key=lambda p: p.last_updated or "", reverse=reverse)
        elif sort_by == "name":
            return sorted(plugins, key=lambda p: p.name.lower(), reverse=reverse)
        else:
            return plugins

    async def _download_plugin(self, plugin: PluginListing) -> bool:
        """Download plugin from marketplace."""
        try:
            if not plugin.download_url:
                return False

            download_dir = self.cache_dir / "downloads"
            download_dir.mkdir(exist_ok=True)

            plugin_file = download_dir / f"{plugin.name}-{plugin.version}.zip"

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(plugin.download_url) as response:
                if response.status == 200:
                    with open(plugin_file, "wb") as f:
                        f.write(await response.read())

                    if await self._verify_plugin_download(plugin_file, plugin):
                        return True
                    plugin_file.unlink(missing_ok=True)
                else:
                    self.logger.error(f"Failed to download plugin: {response.status}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to download plugin: {e}")
            return False

    async def _verify_plugin_download(
        self, plugin_file: Path, plugin: PluginListing
    ) -> bool:
        """Verify downloaded plugin file."""
        try:
            # Check file size
            return plugin_file.stat().st_size != 0
        except Exception as e:
            self.logger.error(f"Failed to verify plugin download: {e}")
            return False

    async def _install_downloaded_plugin(self, plugin: PluginListing) -> bool:
        """Install downloaded plugin."""
        try:
            download_dir = self.cache_dir / "downloads"
            plugin_file = download_dir / f"{plugin.name}-{plugin.version}.zip"

            if not plugin_file.exists():
                return False

            # Extract plugin
            import zipfile

            plugin_dir = Path(self.config.plugin_dir) / plugin.name

            with zipfile.ZipFile(plugin_file, "r") as zip_ref:
                zip_ref.extractall(plugin_dir)

            # Verify installation
            if (plugin_dir / "__init__.py").exists():
                self.logger.info(f"Successfully installed plugin to {plugin_dir}")
                return True
            else:
                self.logger.error("Plugin installation verification failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to install downloaded plugin: {e}")
            return False

    async def _update_download_count(self, plugin_name: str) -> None:
        """Update download count for a plugin."""
        try:
            update_url = urljoin(
                self.config.marketplace_url, f"plugins/{plugin_name}/download"
            )

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(update_url) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Failed to update download count: {response.status}"
                    )

        except Exception as e:
            self.logger.warning(f"Failed to update download count: {e}")

    async def _get_installed_version(self, plugin_name: str) -> Optional[str]:
        """Get installed version of a plugin."""
        try:
            plugin_dir = Path(self.config.plugin_dir) / plugin_name
            init_file = plugin_dir / "__init__.py"

            if init_file.exists():
                # Try to extract version from __init__.py
                with open(init_file, "r") as f:
                    content = f.read()
                    for line in content.split("\n"):
                        if line.startswith("__version__"):
                            return line.split("=")[1].strip().strip("\"'")

            return None

        except Exception as e:
            self.logger.error(f"Failed to get installed version: {e}")
            return None

    def _get_user_id(self) -> str:
        """Get user ID for marketplace interactions."""
        # This would typically come from user authentication
        # For now, use a simple identifier
        return f"user_{os.getuid()}" if hasattr(os, "getuid") else "anonymous"

    def clear_cache(self) -> None:
        """Clear marketplace cache."""
        try:
            import shutil

            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Marketplace cache cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
