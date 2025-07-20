"""{{ plugin_name }} - {{ description }}"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{{ version }}"
__name__ = "{{ plugin_name }}"
__description__ = "{{ description }}"
__author__ = "{{ author }}"
__email__ = "{{ email }}"
__license__ = "{{ license }}"
__dependencies__ = {{ dependencies | tojson }}
__capabilities__ = {{ capabilities | tojson }}
__tags__ = {{ tags | tojson }}

class {{ class_name }}(PluginInterface):
    """{{ description }}"""

    def __init__(self):
        """Initialize the plugin."""
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False
        self.api_routes = {}

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
            tags=__tags__
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        required_fields = ["api_version", "base_path"]
        return all(field in config for field in required_fields)

    def health_check(self) -> Dict[str, Any]:
        """Perform plugin health check."""
        return {
            "status": "healthy" if self.initialized else "initializing",
            "details": "API plugin is functioning normally",
            "version": __version__,
            "api_routes": len(self.api_routes)
        }

    async def initialize(self) -> bool:
        """Initialize the plugin."""
        try:
            # Initialize API routes
            self.api_routes = {
                "/health": self.health_check,
                "/info": self.get_metadata
            }
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.api_routes.clear()
        self.initialized = False

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
                "api_version": {
                    "type": "string",
                    "description": "API version",
                    "default": "v1"
                },
                "base_path": {
                    "type": "string",
                    "description": "API base path",
                    "default": "/api"
                }
            },
            "required": ["api_version", "base_path"]
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Return performance metrics."""
        return {
            "score": 1.0,
            "response_time": 0.001,
            "memory_usage": 0.1
        }

    def get_error_log(self) -> List[Dict[str, Any]]:
        """Return error log."""
        return []

# Plugin instance
plugin_instance = {{ class_name }}()

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
