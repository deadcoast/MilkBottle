"""Test the example Hello World plugin."""

import sys
from pathlib import Path

import pytest

# Add the examples directory to the path
examples_path = (
    Path(__file__).parent.parent / "examples" / "plugins" / "hello_world_plugin"
)
sys.path.insert(0, str(examples_path.parent.parent))

from hello_world_plugin import (
    HelloWorldPlugin,
    get_metadata,
    get_plugin_interface,
    health_check,
    validate_config,
)


class TestHelloWorldPlugin:
    """Test the Hello World plugin."""

    def test_plugin_creation(self):
        """Test creating the plugin."""
        plugin = HelloWorldPlugin()
        assert plugin is not None
        assert not plugin.initialized

    def test_plugin_metadata(self):
        """Test plugin metadata."""
        metadata = get_metadata()
        assert metadata.name == "hello_world_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A simple Hello World plugin for MilkBottle"
        assert metadata.author == "MilkBottle Development Team"
        assert metadata.email == "dev@milkbottle.dev"
        assert metadata.license == "MIT"
        assert metadata.capabilities == ["greeting", "example"]
        assert metadata.tags == ["example", "hello", "world"]

    def test_plugin_interface(self):
        """Test getting plugin interface."""
        plugin = get_plugin_interface()
        assert isinstance(plugin, HelloWorldPlugin)

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        assert validate_config({"greeting": "Hi there!"}) is True

        # Invalid config (not a dict)
        assert validate_config("not a dict") is False

    def test_health_check(self):
        """Test health check."""
        health = health_check()
        assert "status" in health
        assert "details" in health
        assert "version" in health
        assert health["version"] == "1.0.0"

    def test_say_hello(self):
        """Test the say_hello method."""
        plugin = HelloWorldPlugin()

        # Test with name
        greeting = plugin.say_hello("Alice")
        assert greeting == "Hello, Alice!"

        # Test without name (before initialization)
        greeting = plugin.say_hello()
        assert greeting == "Hello, World!"

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = HelloWorldPlugin()

        # Initialize the plugin
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True
        assert plugin.config is not None

        # Test say_hello after initialization
        greeting = plugin.say_hello()
        assert greeting == "Hello, World!"

    @pytest.mark.asyncio
    async def test_plugin_shutdown(self):
        """Test plugin shutdown."""
        plugin = HelloWorldPlugin()

        # Initialize first
        await plugin.initialize()
        assert plugin.initialized is True

        # Shutdown
        await plugin.shutdown()
        assert plugin.initialized is False

    def test_plugin_capabilities(self):
        """Test plugin capabilities."""
        plugin = HelloWorldPlugin()
        capabilities = plugin.get_capabilities()
        assert "greeting" in capabilities
        assert "example" in capabilities

    def test_plugin_dependencies(self):
        """Test plugin dependencies."""
        plugin = HelloWorldPlugin()
        dependencies = plugin.get_dependencies()
        assert dependencies == []  # No dependencies for this simple plugin

    def test_config_schema(self):
        """Test configuration schema."""
        plugin = HelloWorldPlugin()
        schema = plugin.get_config_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "greeting" in schema["properties"]
        assert "repeat_count" in schema["properties"]

    def test_performance_metrics(self):
        """Test performance metrics."""
        plugin = HelloWorldPlugin()
        metrics = plugin.get_performance_metrics()

        assert "score" in metrics
        assert "response_time" in metrics
        assert "memory_usage" in metrics
        assert metrics["score"] == 1.0

    def test_error_log(self):
        """Test error log."""
        plugin = HelloWorldPlugin()
        errors = plugin.get_error_log()
        assert isinstance(errors, list)
