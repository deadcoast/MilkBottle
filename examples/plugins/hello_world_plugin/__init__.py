"""Hello World Plugin for MilkBottle.

This is an example plugin that demonstrates how to implement
the PluginInterface for MilkBottle Phase 5.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "1.0.0"
__name__ = "hello_world_plugin"
__description__ = "A simple Hello World plugin for MilkBottle"
__author__ = "MilkBottle Development Team"
__email__ = "dev@milkbottle.dev"
__license__ = "MIT"
__dependencies__ = []
__capabilities__ = ["greeting", "example"]
__tags__ = ["example", "hello", "world"]


class HelloWorldPlugin(PluginInterface):
    """Hello World plugin implementation."""

    def __init__(self):
        """Initialize the plugin."""
        self.logger = logging.getLogger("milkbottle.plugin.hello_world")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False

    def get_cli(self) -> Any:
        """Return the CLI interface."""
        from .cli import cli

        return cli

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name=__name__,
            version=__version__,
            description=__description__,
            author=__author__,
            email=__email__,
            license=__license__,
            dependencies=__dependencies__,
            capabilities=__capabilities__,
            tags=__tags__,
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        try:
            # Simple validation - just check if config is a dict
            return isinstance(config, dict)
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform plugin health check."""
        try:
            return {
                "status": "healthy" if self.initialized else "initializing",
                "details": "Hello World plugin is functioning normally",
                "version": __version__,
                "dependencies_ok": self._check_dependencies(),
                "config_valid": self.config is not None,
            }
        except Exception as e:
            return {
                "status": "critical",
                "details": f"Health check failed: {e}",
                "version": __version__,
            }

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        try:
            self.logger.info(f"Initializing plugin {__name__}")

            # Initialize plugin resources
            await self._initialize_resources()

            # Load configuration
            await self._load_configuration()

            # Validate configuration
            if not self.validate_config(self.config or {}):
                self.logger.error("Plugin configuration validation failed")
                return False

            self.initialized = True
            self.logger.info(f"Plugin {__name__} initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {__name__}: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        try:
            self.logger.info(f"Shutting down plugin {__name__}")

            # Cleanup resources
            await self._cleanup_resources()

            self.initialized = False
            self.logger.info(f"Plugin {__name__} shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during plugin shutdown {__name__}: {e}")

    def get_capabilities(self) -> List[str]:
        """Return list of plugin capabilities."""
        return __capabilities__

    def get_dependencies(self) -> List[str]:
        """Return list of plugin dependencies."""
        return __dependencies__

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "type": "object",
            "properties": {
                "greeting": {
                    "type": "string",
                    "description": "Custom greeting message",
                    "default": "Hello, World!",
                },
                "repeat_count": {
                    "type": "integer",
                    "description": "Number of times to repeat the greeting",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": [],
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Return performance metrics."""
        return {"score": 1.0, "response_time": 0.001, "memory_usage": 0.1}

    def get_error_log(self) -> List[Dict[str, Any]]:
        """Return error log."""
        return []

    async def _initialize_resources(self) -> None:
        """Initialize plugin resources."""
        # No special resources needed for this simple plugin
        pass

    async def _load_configuration(self) -> None:
        """Load plugin configuration."""
        # Default configuration
        self.config = {"greeting": "Hello, World!", "repeat_count": 1}

    async def _cleanup_resources(self) -> None:
        """Cleanup plugin resources."""
        # No cleanup needed for this simple plugin
        pass

    def _check_dependencies(self) -> bool:
        """Check if all dependencies are available."""
        for dependency in __dependencies__:
            try:
                __import__(dependency)
            except ImportError:
                return False
        return True

    def say_hello(self, name: Optional[str] = None) -> str:
        """Say hello to someone.

        Args:
            name: Name to greet (optional)

        Returns:
            Greeting message
        """
        if name:
            return f"Hello, {name}!"
        else:
            return (
                self.config.get("greeting", "Hello, World!")
                if self.config
                else "Hello, World!"
            )


# Plugin instance
plugin_instance = HelloWorldPlugin()


# Required exports
def get_plugin_interface() -> PluginInterface:
    """Get plugin interface."""
    return plugin_instance


def get_cli():
    """Get plugin CLI interface."""
    return plugin_instance.get_cli()


def get_metadata():
    """Get plugin metadata."""
    return plugin_instance.get_metadata()


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate plugin configuration."""
    return plugin_instance.validate_config(config)


def health_check() -> Dict[str, Any]:
    """Perform plugin health check."""
    return plugin_instance.health_check()
