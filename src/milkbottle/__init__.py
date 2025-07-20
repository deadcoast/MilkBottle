"""MilkBottle - Enhanced Modular CLI Toolbox with Health Monitoring & Plugin System.

A comprehensive CLI toolbox that provides modular tools (bottles) for various tasks
with integrated health monitoring, plugin system, and advanced features.
"""

__version__ = "1.0.0"
__author__ = "MilkBottle Team"
__description__ = "Enhanced Modular CLI Toolbox with Health Monitoring & Plugin System"

from .config import MilkBottleConfig, build_config, get_config
from .errors import MilkBottleError

# Main exports
from .registry import get_bottle, get_registry, list_bottles, perform_health_check

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_registry",
    "list_bottles",
    "get_bottle",
    "perform_health_check",
    "get_config",
    "build_config",
    "MilkBottleConfig",
    "MilkBottleError",
]
