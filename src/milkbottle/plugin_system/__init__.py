"""Enhanced plugin system for MilkBottle with advanced features and management.

This package provides comprehensive plugin discovery, loading, validation,
and management capabilities for extending MilkBottle functionality with
enterprise-grade features including marketplace integration, performance
optimization, and production deployment capabilities.
"""

from __future__ import annotations

__version__ = "5.0.0"
__author__ = "MilkBottle Development Team"
__description__ = "Enhanced plugin system for MilkBottle"

from .core import (
    PluginInfo,
    PluginInterface,
    PluginManager,
    PluginMetadata,
    get_plugin_manager,
)
from .discovery import PluginDiscovery
from .health import PluginHealthMonitor
from .marketplace import PluginMarketplace
from .validation import PluginValidator

__all__ = [
    "PluginInterface",
    "PluginManager",
    "PluginMetadata",
    "PluginInfo",
    "PluginDiscovery",
    "PluginValidator",
    "PluginMarketplace",
    "PluginHealthMonitor",
    "get_plugin_manager",
]
