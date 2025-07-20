"""Integration tests for the plugin system."""

from pathlib import Path

import pytest

from milkbottle.config import MilkBottleConfig
from milkbottle.plugin_system.core import (
    PluginInfo,
    PluginManager,
    PluginMetadata,
    get_plugin_manager,
)


class TestPluginSystemIntegration:
    """Integration tests for the plugin system."""

    def test_plugin_manager_integration(self):
        """Test plugin manager integration."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        # Test basic functionality
        assert manager is not None
        assert len(manager.plugins) == 0

        # Test statistics
        stats = manager.get_plugin_statistics()
        assert stats["total_plugins"] == 0
        assert stats["loaded_plugins"] == 0
        assert stats["healthy_plugins"] == 0

    def test_plugin_metadata_validation_integration(self):
        """Test plugin metadata validation integration."""
        # Test valid metadata
        valid_metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin for integration testing",
            author="Test Author",
            email="test@example.com",
            license="MIT",
            dependencies=["rich"],
            capabilities=["test"],
            tags=["test", "integration"],
        )

        assert valid_metadata.name == "test_plugin"
        assert valid_metadata.version == "1.0.0"
        assert "rich" in valid_metadata.dependencies
        assert "test" in valid_metadata.capabilities

    def test_plugin_info_integration(self):
        """Test plugin info integration."""
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
            rating=4.5,
            download_count=100,
        )

        assert plugin_info.is_healthy() is True
        assert plugin_info.is_enabled() is True
        assert plugin_info.rating == 4.5
        assert plugin_info.download_count == 100

    def test_singleton_pattern_integration(self):
        """Test that plugin manager singleton pattern works."""
        config = MilkBottleConfig()

        # Get manager instances
        manager1 = get_plugin_manager(config)
        manager2 = get_plugin_manager(config)
        manager3 = get_plugin_manager()  # Should use existing instance

        # All should be the same instance
        assert manager1 is manager2
        assert manager1 is manager3

    def test_plugin_manager_with_plugins(self):
        """Test plugin manager with multiple plugins."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        # Create test plugins
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

        # Add plugins to manager
        manager.plugins["plugin1"] = plugin_info1
        manager.plugins["plugin2"] = plugin_info2

        # Test listing plugins
        plugins = manager.list_plugins()
        assert len(plugins) == 2

        # Find specific plugins
        plugin1_data = next((p for p in plugins if p["name"] == "plugin1"), None)
        plugin2_data = next((p for p in plugins if p["name"] == "plugin2"), None)

        assert plugin1_data is not None
        assert plugin2_data is not None
        assert plugin1_data["version"] == "1.0.0"
        assert plugin2_data["version"] == "2.0.0"
        assert plugin1_data["rating"] == 4.5
        assert plugin2_data["rating"] == 3.0

    def test_plugin_statistics_integration(self):
        """Test plugin statistics integration."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        # Add plugins with different states
        metadata1 = PluginMetadata(
            name="healthy_plugin",
            version="1.0.0",
            description="Healthy plugin",
            author="Author",
            email="author@example.com",
            license="MIT",
        )

        metadata2 = PluginMetadata(
            name="unhealthy_plugin",
            version="1.0.0",
            description="Unhealthy plugin",
            author="Author",
            email="author@example.com",
            license="MIT",
        )

        healthy_plugin = PluginInfo(
            metadata=metadata1,
            path=Path("/tmp/healthy"),
            status="enabled",
            health_status={"status": "healthy"},
            rating=5.0,
            download_count=1000,
        )

        unhealthy_plugin = PluginInfo(
            metadata=metadata2,
            path=Path("/tmp/unhealthy"),
            status="enabled",
            health_status={"status": "unhealthy"},
            rating=2.0,
            download_count=500,
            error_count=5,
        )

        manager.plugins["healthy_plugin"] = healthy_plugin
        manager.plugins["unhealthy_plugin"] = unhealthy_plugin

        # Test statistics
        stats = manager.get_plugin_statistics()

        assert stats["total_plugins"] == 2
        assert stats["healthy_plugins"] == 1
        assert stats["unhealthy_plugins"] == 1
        assert stats["average_rating"] == 3.5  # (5.0 + 2.0) / 2
        assert stats["total_downloads"] == 1500  # 1000 + 500
        assert stats["total_errors"] == 5

    @pytest.mark.asyncio
    async def test_async_health_check_integration(self):
        """Test async health check integration."""
        config = MilkBottleConfig()
        manager = PluginManager(config)

        # Test health check with no plugins
        health_status = await manager.health_check_all()
        assert health_status == {}

        # Add a mock plugin (we can't easily test with real plugins in integration test)
        # This test verifies the async method exists and works
        assert hasattr(manager, "health_check_all")
        assert callable(manager.health_check_all)

    def test_config_integration(self):
        """Test configuration integration."""
        config = MilkBottleConfig()

        # Test plugin system configuration
        assert hasattr(config, "plugin_dir")
        assert hasattr(config, "enable_marketplace")
        assert hasattr(config, "marketplace_url")

        # Test default values
        assert config.plugin_dir == "~/.milkbottle/plugins"
        assert config.enable_marketplace is True
        assert "marketplace.milkbottle.dev" in config.marketplace_url
