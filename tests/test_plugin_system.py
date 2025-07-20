"""Tests for the enhanced plugin system."""

from pathlib import Path

import pytest

from milkbottle.config import MilkBottleConfig
from milkbottle.plugin_system.core import (
    PluginInfo,
    PluginManager,
    PluginMetadata,
    get_plugin_manager,
)


class TestPluginSystem:
    """Test the enhanced plugin system."""

    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            email="test@example.com",
            license="MIT",
        )

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test plugin"
        assert metadata.author == "Test Author"
        assert metadata.email == "test@example.com"
        assert metadata.license == "MIT"

    def test_plugin_info_creation(self):
        """Test creating plugin info."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            email="test@example.com",
            license="MIT",
        )

        plugin_info = PluginInfo(
            metadata=metadata, path=Path("/tmp/test_plugin"), status="discovered"
        )

        assert plugin_info.metadata.name == "test_plugin"
        assert plugin_info.status == "discovered"
        assert plugin_info.is_healthy() is False  # Default health status is unknown

    def test_plugin_manager_creation(self):
        """Test creating plugin manager."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        assert manager is not None
        assert len(manager.plugins) == 0
        assert len(manager.loaded_plugins) == 0

    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns a singleton."""
        config = MilkBottleConfig()
        manager1 = get_plugin_manager(config)
        manager2 = get_plugin_manager(config)

        assert manager1 is manager2

    def test_plugin_metadata_validation(self):
        """Test plugin metadata validation."""
        # Test valid metadata
        valid_metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            email="test@example.com",
            license="MIT",
        )

        # This should not raise an exception
        assert valid_metadata.name == "test_plugin"

        # Test invalid metadata (empty name)
        with pytest.raises(ValueError, match="Plugin name cannot be empty"):
            PluginMetadata(
                name="",
                version="1.0.0",
                description="A test plugin",
                author="Test Author",
                email="test@example.com",
                license="MIT",
            )

        # Test invalid metadata (empty version)
        with pytest.raises(ValueError, match="Plugin version cannot be empty"):
            PluginMetadata(
                name="test_plugin",
                version="",
                description="A test plugin",
                author="Test Author",
                email="test@example.com",
                license="MIT",
            )

    def test_plugin_info_methods(self):
        """Test plugin info methods."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            email="test@example.com",
            license="MIT",
        )

        plugin_info = PluginInfo(
            metadata=metadata,
            path=Path("/tmp/test_plugin"),
            status="enabled",
            health_status={"status": "healthy"},
        )

        assert plugin_info.is_healthy() is True
        assert plugin_info.is_enabled() is True
        assert plugin_info.get_performance_score() == 0.0  # Default value

    def test_plugin_manager_statistics(self):
        """Test plugin manager statistics."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        # Add some test plugins
        metadata1 = PluginMetadata(
            name="plugin1",
            version="1.0.0",
            description="Plugin 1",
            author="Author 1",
            email="author1@example.com",
            license="MIT",
        )

        metadata2 = PluginMetadata(
            name="plugin2",
            version="2.0.0",
            description="Plugin 2",
            author="Author 2",
            email="author2@example.com",
            license="MIT",
        )

        plugin_info1 = PluginInfo(
            metadata=metadata1,
            path=Path("/tmp/plugin1"),
            status="enabled",
            health_status={"status": "healthy"},
            rating=4.5,
        )

        plugin_info2 = PluginInfo(
            metadata=metadata2,
            path=Path("/tmp/plugin2"),
            status="enabled",
            health_status={"status": "unhealthy"},
            rating=3.0,
            error_count=2,
        )

        manager.plugins["plugin1"] = plugin_info1
        manager.plugins["plugin2"] = plugin_info2

        stats = manager.get_plugin_statistics()

        assert stats["total_plugins"] == 2
        assert stats["loaded_plugins"] == 0
        assert stats["healthy_plugins"] == 1
        assert stats["unhealthy_plugins"] == 1
        assert stats["average_rating"] == 3.75
        assert stats["total_downloads"] == 0
        assert stats["total_errors"] == 2
        assert stats["total_errors"] == 2
