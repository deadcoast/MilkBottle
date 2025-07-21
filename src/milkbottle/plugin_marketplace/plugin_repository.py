"""Plugin Repository - Centralized plugin storage and management."""

from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aiohttp
import yaml
from rich.console import Console

from ..config import MilkBottleConfig


@dataclass
class RepositoryConfig:
    """Repository configuration."""

    base_url: str = "https://marketplace.milkbottle.dev"
    api_version: str = "v1"
    cache_dir: str = "~/.milkbottle/marketplace_cache"
    cache_ttl: int = 3600  # seconds
    max_plugins_per_page: int = 50
    enable_offline_mode: bool = False
    verify_ssl: bool = True
    timeout: int = 30


@dataclass
class PluginVersion:
    """Plugin version information."""

    version: str
    release_date: str
    download_url: str
    checksum: str
    size: int
    changelog: str
    compatibility: Dict[str, str]
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RepositoryPlugin:
    """Plugin information from repository."""

    name: str
    description: str
    author: str
    license: str
    last_updated: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    documentation: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    versions: List[PluginVersion] = field(default_factory=list)
    latest_version: Optional[str] = None
    download_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    status: str = "active"  # active, deprecated, suspended


class PluginRepository:
    """Centralized plugin storage and management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.repo_config = RepositoryConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.repository")
        self.cache_dir = Path(self.repo_config.cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.plugins_cache: Dict[str, RepositoryPlugin] = {}
        self.cache_timestamp: Optional[datetime] = None

    async def search_plugins(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[RepositoryPlugin]:
        """Search for plugins in the repository."""
        try:
            self.logger.info(f"Searching plugins with query: {query}")

            # Ensure cache is up to date
            await self._update_cache_if_needed()

            # Filter plugins based on search criteria
            results = []

            for plugin in self.plugins_cache.values():
                # Check if plugin matches query
                if not self._matches_search_criteria(plugin, query, category, tags):
                    continue

                results.append(plugin)

                if len(results) >= limit:
                    break

            # Sort by relevance (download count, rating, etc.)
            results.sort(key=lambda p: (p.download_count, p.rating), reverse=True)

            self.logger.info(f"Found {len(results)} plugins matching query")
            return results

        except Exception as e:
            self.logger.error(f"Failed to search plugins: {e}")
            return []

    async def get_plugin(self, plugin_name: str) -> Optional[RepositoryPlugin]:
        """Get plugin information by name."""
        try:
            await self._update_cache_if_needed()
            return self.plugins_cache.get(plugin_name)

        except Exception as e:
            self.logger.error(f"Failed to get plugin {plugin_name}: {e}")
            return None

    async def get_popular_plugins(self, limit: int = 10) -> List[RepositoryPlugin]:
        """Get most popular plugins."""
        try:
            await self._update_cache_if_needed()

            plugins = list(self.plugins_cache.values())
            plugins.sort(key=lambda p: p.download_count, reverse=True)

            return plugins[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get popular plugins: {e}")
            return []

    async def get_recent_plugins(self, limit: int = 10) -> List[RepositoryPlugin]:
        """Get recently updated plugins."""
        try:
            await self._update_cache_if_needed()

            plugins = list(self.plugins_cache.values())
            plugins.sort(key=lambda p: p.last_updated, reverse=True)

            return plugins[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get recent plugins: {e}")
            return []

    async def get_plugins_by_category(
        self, category: str, limit: int = 20
    ) -> List[RepositoryPlugin]:
        """Get plugins by category."""
        try:
            await self._update_cache_if_needed()

            plugins = [
                plugin
                for plugin in self.plugins_cache.values()
                if category in plugin.categories
            ]

            plugins.sort(key=lambda p: p.download_count, reverse=True)
            return plugins[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get plugins by category: {e}")
            return []

    async def download_plugin(
        self,
        plugin_name: str,
        version: Optional[str] = None,
        target_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Download a plugin from the repository."""
        try:
            self.logger.info(f"Downloading plugin: {plugin_name}")

            # Get plugin information
            plugin = await self.get_plugin(plugin_name)
            if not plugin:
                self.logger.error(f"Plugin {plugin_name} not found")
                return None

            # Get version to download
            if not version:
                version = plugin.latest_version

            if not version:
                self.logger.error(f"No version specified for plugin {plugin_name}")
                return None

            version_info = next(
                (v for v in plugin.versions if v.version == version), None
            )
            if not version_info:
                self.logger.error(
                    f"Version {version} not found for plugin {plugin_name}"
                )
                return None

            # Set target directory
            if not target_dir:
                target_dir = Path.home() / ".milkbottle" / "plugins" / plugin_name

            target_dir.mkdir(parents=True, exist_ok=True)

            # Download plugin
            plugin_file = await self._download_file(
                version_info.download_url, target_dir
            )
            if not plugin_file:
                return None

            # Verify checksum
            if not await self._verify_checksum(plugin_file, version_info.checksum):
                self.logger.error(f"Checksum verification failed for {plugin_name}")
                plugin_file.unlink()
                return None

            # Extract plugin
            extracted_dir = await self._extract_plugin(plugin_file, target_dir)
            if not extracted_dir:
                return None

            # Clean up downloaded file
            plugin_file.unlink()

            self.logger.info(
                f"Successfully downloaded plugin {plugin_name} to {extracted_dir}"
            )
            return extracted_dir

        except Exception as e:
            self.logger.error(f"Failed to download plugin {plugin_name}: {e}")
            return None

    async def get_plugin_metadata(self, plugin_path: Path) -> Optional[Dict[str, Any]]:
        """Extract metadata from a plugin."""
        try:
            # Look for plugin.yaml or pyproject.toml
            metadata_files = [
                plugin_path / "plugin.yaml",
                plugin_path / "pyproject.toml",
                plugin_path / "setup.py",
            ]

            for metadata_file in metadata_files:
                if metadata_file.exists():
                    if metadata_file.suffix == ".yaml":
                        with open(metadata_file, "r") as f:
                            return yaml.safe_load(f)
                    elif metadata_file.suffix == ".toml":
                        import tomllib

                        with open(metadata_file, "rb") as f:
                            return tomllib.load(f)
                    elif metadata_file.name == "setup.py":
                        # Parse setup.py (simplified)
                        return await self._parse_setup_py(metadata_file)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get plugin metadata: {e}")
            return None

    async def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate a plugin for repository submission."""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "metadata": None,
            }

            # Check if plugin directory exists
            if not plugin_path.exists() or not plugin_path.is_dir():
                validation_result["valid"] = False
                validation_result["errors"].append("Plugin directory does not exist")
                return validation_result

            # Check for required files
            required_files = ["__init__.py", "cli.py"]
            for file_name in required_files:
                if not (plugin_path / file_name).exists():
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        f"Missing required file: {file_name}"
                    )

            # Get metadata
            metadata = await self.get_plugin_metadata(plugin_path)
            if metadata:
                validation_result["metadata"] = metadata

                # Validate metadata
                if not self._validate_metadata(metadata, validation_result):
                    validation_result["valid"] = False
            else:
                validation_result["valid"] = False
                validation_result["errors"].append("No metadata found")

            # Check for tests
            if not (plugin_path / "tests").exists():
                validation_result["warnings"].append("No tests directory found")

            # Check for documentation
            if not (plugin_path / "README.md").exists():
                validation_result["warnings"].append("No README.md found")

            return validation_result

        except Exception as e:
            self.logger.error(f"Failed to validate plugin: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": [],
                "metadata": None,
            }

    async def _update_cache_if_needed(self) -> None:
        """Update cache if it's expired or doesn't exist."""
        try:
            if self.repo_config.enable_offline_mode:
                return

            # Check if cache is expired
            if (
                self.cache_timestamp
                and datetime.now() - self.cache_timestamp
                < timedelta(seconds=self.repo_config.cache_ttl)
            ):
                return

            # Update cache
            await self._update_cache()

        except Exception as e:
            self.logger.error(f"Failed to update cache: {e}")

    async def _update_cache(self) -> None:
        """Update plugin cache from repository."""
        try:
            self.logger.info("Updating plugin cache")

            # Fetch plugins from repository API
            plugins = await self._fetch_plugins_from_api()

            # Update cache
            self.plugins_cache.clear()
            for plugin in plugins:
                self.plugins_cache[plugin.name] = plugin

            # Update timestamp
            self.cache_timestamp = datetime.now()

            # Save cache to file
            await self._save_cache()

            self.logger.info(f"Updated cache with {len(plugins)} plugins")

        except Exception as e:
            self.logger.error(f"Failed to update cache: {e}")

    async def _fetch_plugins_from_api(self) -> List[RepositoryPlugin]:
        """Fetch plugins from repository API."""
        try:
            # In a real implementation, this would fetch from the actual API
            # For demo purposes, return sample data
            return [
                RepositoryPlugin(
                    name="example-plugin",
                    description="An example plugin for MilkBottle",
                    author="Example Author",
                    license="MIT",
                    homepage="https://example.com/plugin",
                    repository="https://github.com/example/plugin",
                    tags=["example", "demo"],
                    categories=["utilities"],
                    latest_version="1.0.0",
                    download_count=100,
                    rating=4.5,
                    review_count=10,
                    last_updated="2024-01-01",
                    versions=[
                        PluginVersion(
                            version="1.0.0",
                            release_date="2024-01-01",
                            download_url="https://example.com/plugin-1.0.0.zip",
                            checksum="abc123",
                            size=1024,
                            changelog="Initial release",
                            compatibility={"milkbottle": ">=1.0.0"},
                            dependencies=["requests"],
                        )
                    ],
                )
            ]

        except Exception as e:
            self.logger.error(f"Failed to fetch plugins from API: {e}")
            return []

    async def _download_file(self, url: str, target_dir: Path) -> Optional[Path]:
        """Download a file from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Create temporary file
                        temp_file = (
                            target_dir
                            / f"temp_{hashlib.md5(url.encode()).hexdigest()}.zip"
                        )

                        # Download file
                        with open(temp_file, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                        return temp_file
                    else:
                        self.logger.error(f"Failed to download file: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            return None

    async def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum."""
        try:
            hash_md5 = hashlib.md5()
            async with aiofiles.open(file_path, "rb") as f:
                async for chunk in f:
                    hash_md5.update(chunk)

            actual_checksum = hash_md5.hexdigest()
            return actual_checksum == expected_checksum

        except Exception as e:
            self.logger.error(f"Failed to verify checksum: {e}")
            return False

    async def _extract_plugin(
        self, plugin_file: Path, target_dir: Path
    ) -> Optional[Path]:
        """Extract plugin archive."""
        try:
            with zipfile.ZipFile(plugin_file, "r") as zip_ref:
                zip_ref.extractall(target_dir)

            return next(
                (
                    item
                    for item in target_dir.iterdir()
                    if item.is_dir() and (item / "__init__.py").exists()
                ),
                target_dir,
            )
        except Exception as e:
            self.logger.error(f"Failed to extract plugin: {e}")
            return None

    async def _parse_setup_py(self, setup_file: Path) -> Dict[str, Any]:
        """Parse setup.py file (simplified)."""
        try:
            # This is a simplified parser
            # In production, you'd use a proper setup.py parser
            return {
                "name": "unknown",
                "version": "0.0.0",
                "description": "No description",
                "author": "Unknown",
                "license": "MIT",
            }
        except Exception as e:
            self.logger.error(f"Failed to parse setup.py: {e}")
            return {}

    def _validate_metadata(
        self, metadata: Dict[str, Any], validation_result: Dict[str, Any]
    ) -> bool:
        """Validate plugin metadata."""
        try:
            required_fields = ["name", "version", "description", "author"]

            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    validation_result["errors"].append(
                        f"Missing required field: {field}"
                    )
                    return False

            return True

        except Exception as e:
            validation_result["errors"].append(f"Metadata validation failed: {e}")
            return False

    def _matches_search_criteria(
        self,
        plugin: RepositoryPlugin,
        query: str,
        category: Optional[str],
        tags: Optional[List[str]],
    ) -> bool:
        """Check if plugin matches search criteria."""
        # Check query
        if (
            query.lower() not in plugin.name.lower()
            and query.lower() not in plugin.description.lower()
        ):
            return False

        # Check category
        if category and category not in plugin.categories:
            return False

        # Check tags
        return not tags or any(tag in plugin.tags for tag in tags)

    async def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            cache_file = self.cache_dir / "plugins_cache.json"

            cache_data = {
                "timestamp": (
                    self.cache_timestamp.isoformat() if self.cache_timestamp else None
                ),
                "plugins": {
                    name: plugin.__dict__ for name, plugin in self.plugins_cache.items()
                },
            }

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")

    async def _load_cache(self) -> None:
        """Load cache from file."""
        try:
            cache_file = self.cache_dir / "plugins_cache.json"

            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                # Load timestamp
                if cache_data.get("timestamp"):
                    self.cache_timestamp = datetime.fromisoformat(
                        cache_data["timestamp"]
                    )

                # Load plugins
                self.plugins_cache.clear()
                for name, plugin_data in cache_data.get("plugins", {}).items():
                    # Convert back to RepositoryPlugin object
                    # This is simplified - in production you'd have proper serialization
                    pass

        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}")
