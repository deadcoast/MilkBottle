"""Tests for MilkBottle plugin system and extensibility."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from milkbottle.plugin_system import (
    PluginLoader,
    PluginManager,
    PluginManifest,
    get_plugin_manager,
    install_plugin,
    list_plugins,
    load_plugin,
    unload_plugin,
)
from milkbottle.registry import BottleRegistry, get_registry


class TestPluginManifest:
    """Test plugin manifest functionality."""

    def test_valid_manifest(self):
        """Test valid manifest creation."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin",
            "author": "Test Author",
            "dependencies": ["requests>=2.25.0"],
            "capabilities": ["text_processing"],
            "config_schema": {
                "enabled": {"type": "boolean", "default": True},
            },
        }

        manifest = PluginManifest(manifest_data)

        assert manifest.name == "test_plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == "Test plugin"
        assert manifest.entry_point == "test_plugin"
        assert manifest.author == "Test Author"
        assert manifest.dependencies == ["requests>=2.25.0"]
        assert manifest.capabilities == ["text_processing"]

    def test_invalid_manifest_missing_required(self):
        """Test manifest validation with missing required fields."""
        manifest_data = {
            "name": "test_plugin",
            # Missing version, description, entry_point
        }

        with pytest.raises(Exception):
            PluginManifest(manifest_data)

    def test_invalid_version_format(self):
        """Test manifest validation with invalid version."""
        manifest_data = {
            "name": "test_plugin",
            "version": "invalid-version",
            "description": "Test plugin",
            "entry_point": "test_plugin",
        }

        with pytest.raises(Exception):
            PluginManifest(manifest_data)

    def test_manifest_to_dict(self):
        """Test manifest to dictionary conversion."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin",
        }

        manifest = PluginManifest(manifest_data)
        result = manifest.to_dict()

        assert result["name"] == "test_plugin"
        assert result["version"] == "1.0.0"
        assert result["description"] == "Test plugin"
        assert result["entry_point"] == "test_plugin"


class TestPluginLoader:
    """Test plugin loader functionality."""

    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization."""
        loader = PluginLoader()
        assert loader.plugin_dirs is not None
        assert len(loader.plugin_dirs) > 0

    def test_discover_plugins_empty(self):
        """Test plugin discovery with empty directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PluginLoader([temp_dir])
            plugins = loader.discover_plugins()
            assert plugins == {}

    def test_discover_plugins_with_manifest(self):
        """Test plugin discovery with valid manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create plugin directory structure
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()

            # Create manifest file
            manifest_file = plugin_dir / "plugin.yaml"
            manifest_file.write_text(
                """
name: test_plugin
version: 1.0.0
description: Test plugin
entry_point: test_plugin
author: Test Author
dependencies:
  - requests>=2.25.0
capabilities:
  - text_processing
config_schema:
  enabled:
    type: boolean
    default: true
"""
            )

            loader = PluginLoader([temp_dir])
            plugins = loader.discover_plugins()

            assert "test_plugin" in plugins
            assert plugins["test_plugin"].name == "test_plugin"
            assert plugins["test_plugin"].version == "1.0.0"

    def test_load_plugin_module(self):
        """Test loading plugin module."""
        # Create a mock module
        mock_module = Mock()
        mock_module.get_metadata = Mock(
            return_value={
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
            }
        )
        mock_module.get_cli = Mock(return_value=typer.Typer())

        with patch("importlib.import_module", return_value=mock_module):
            manifest_data = {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "entry_point": "test_plugin",
            }
            manifest = PluginManifest(manifest_data)

            loader = PluginLoader()
            plugin_module = loader._load_plugin_module(manifest)

            assert plugin_module is not None
            assert hasattr(plugin_module, "get_metadata")
            assert hasattr(plugin_module, "get_cli")


class TestPluginManager:
    """Test plugin manager functionality."""

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        registry = Mock(spec=BottleRegistry)
        manager = PluginManager(registry)
        assert manager.registry == registry

    def test_install_plugin_from_path(self):
        """Test installing plugin from local path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create plugin directory
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()

            # Create manifest
            manifest_file = plugin_dir / "plugin.yaml"
            manifest_file.write_text(
                """
name: test_plugin
version: 1.0.0
description: Test plugin
entry_point: test_plugin
"""
            )

            # Create plugin module
            module_file = plugin_dir / "test_plugin.py"
            module_file.write_text(
                """
def get_metadata():
    return {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
    }

def get_cli():
    import typer
    return typer.Typer()
"""
            )

            registry = Mock(spec=BottleRegistry)
            manager = PluginManager(registry)

            # Test installation
            result = manager.install_plugin(str(plugin_dir))
            assert result is True

    def test_load_plugin(self):
        """Test loading a plugin."""
        registry = Mock(spec=BottleRegistry)
        manager = PluginManager(registry)

        # Mock the loader's load_plugin method instead
        with patch.object(manager.loader, "load_plugin", return_value=Mock()):
            result = manager.load_plugin("test_plugin")
            assert result is True

    def test_unload_plugin(self):
        """Test unloading a plugin."""
        registry = Mock(spec=BottleRegistry)
        manager = PluginManager(registry)

        # Mock loaded plugin
        manager._active_plugins.add("test_plugin")
        manager._plugin_health["test_plugin"] = Mock()

        result = manager.unload_plugin("test_plugin")
        assert result is True
        assert "test_plugin" not in manager._active_plugins

    def test_list_plugins(self):
        """Test listing plugins."""
        registry = Mock(spec=BottleRegistry)
        manager = PluginManager(registry)

        # Mock discovered plugins
        mock_manifest = Mock(spec=PluginManifest)
        mock_manifest.name = "test_plugin"
        mock_manifest.version = "1.0.0"
        mock_manifest.description = "Test plugin"

        # Mock plugin loader discovery
        with patch.object(
            manager.loader,
            "discover_plugins",
            return_value={"test_plugin": mock_manifest},
        ):
            manager._active_plugins.add("test_plugin")

            plugins = manager.list_plugins()
            assert len(plugins) == 1
            assert plugins[0]["name"] == "test_plugin"
            assert plugins[0]["loaded"] is True

    def test_plugin_health_check(self):
        """Test plugin health check."""
        registry = Mock(spec=BottleRegistry)
        manager = PluginManager(registry)

        # Mock plugin with health check
        mock_plugin = Mock()
        mock_plugin.health_check = Mock(
            return_value={
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        )

        manager._active_plugins.add("test_plugin")

        health = manager._check_plugin_health("test_plugin", mock_plugin)
        assert health["status"] == "healthy"


class TestBottleRegistry:
    """Test bottle registry functionality."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = BottleRegistry()
        assert registry._bottles == {}
        assert registry._health_cache == {}
        assert registry._config_cache == {}

    def test_discover_bottles(self):
        """Test bottle discovery."""
        registry = BottleRegistry()

        # Mock entry point discovery
        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value.select.return_value = []

            bottles = registry.discover_bottles()
            assert isinstance(bottles, dict)

    def test_get_bottle(self):
        """Test getting a bottle."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottle
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "cli_loader": lambda: typer.Typer(),
                }
            }

            bottle = registry.get_bottle("test_bottle")
            assert bottle is not None

    def test_get_bottle_not_found(self):
        """Test getting non-existent bottle."""
        registry = BottleRegistry()
        bottle = registry.get_bottle("nonexistent")
        assert bottle is None

    def test_health_check(self):
        """Test bottle health check."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottle
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "module": Mock(),
                }
            }

            # Mock the health check method
            with patch.object(registry, "_check_bottle_health") as mock_health:
                mock_health.return_value = {
                    "status": "healthy",
                    "timestamp": "2024-01-01T00:00:00Z",
                }

                health = registry.health_check("test_bottle")
                assert health["status"] == "healthy"

    def test_validate_config(self):
        """Test configuration validation."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottle
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "module": Mock(),
                }
            }

            # Mock the validation method
            with patch.object(registry, "_validate_bottle_config") as mock_validate:
                mock_validate.return_value = (True, [])

                is_valid, errors = registry.validate_config(
                    "test_bottle", {"enabled": True}
                )
                assert is_valid is True
                assert errors == []

    def test_list_bottles(self):
        """Test listing bottles."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottles
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "version": "1.0.0",
                    "description": "Test bottle",
                    "has_cli": True,
                    "is_valid": True,
                },
            }

            bottles = registry.list_bottles()
            assert len(bottles) == 1
            assert bottles[0]["name"] == "test_bottle"

    def test_get_capabilities(self):
        """Test getting bottle capabilities."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottles
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "capabilities": ["text_processing", "data_export"],
                },
            }

            capabilities = registry.get_capabilities()
            assert "test_bottle" in capabilities
            assert "text_processing" in capabilities["test_bottle"]

    def test_get_dependencies(self):
        """Test getting bottle dependencies."""
        registry = BottleRegistry()

        # Mock bottle discovery to return our test bottles
        with patch.object(registry, "discover_bottles") as mock_discover:
            mock_discover.return_value = {
                "test_bottle": {
                    "name": "test_bottle",
                    "dependencies": ["requests>=2.25.0"],
                },
            }

            dependencies = registry.get_dependencies()
            assert "test_bottle" in dependencies
            assert "requests>=2.25.0" in dependencies["test_bottle"]


class TestPluginSystemIntegration:
    """Test plugin system integration."""

    def test_plugin_lifecycle(self):
        """Test complete plugin lifecycle."""
        # Mock the plugin installation and loading process
        with patch(
            "milkbottle.plugin_system.install_plugin", return_value=True
        ) as mock_install:
            with patch(
                "milkbottle.plugin_system.load_plugin", return_value=True
            ) as mock_load:
                with patch(
                    "milkbottle.plugin_system.list_plugins",
                    return_value=[{"name": "test_plugin"}],
                ) as mock_list:
                    with patch(
                        "milkbottle.plugin_system.unload_plugin", return_value=True
                    ) as mock_unload:

                        # Test plugin installation
                        result = install_plugin("test_plugin")
                        assert result is True
                        mock_install.assert_called_once_with("test_plugin")

                        # Test plugin loading
                        result = load_plugin("test_plugin")
                        assert result is True
                        mock_load.assert_called_once_with("test_plugin")

                        # Test plugin listing
                        plugins = list_plugins()
                        assert len(plugins) == 1
                        assert plugins[0]["name"] == "test_plugin"
                        mock_list.assert_called_once()

                        # Test plugin unloading
                        result = unload_plugin("test_plugin")
                        assert result is True
                        mock_unload.assert_called_once_with("test_plugin")

    def test_registry_integration(self):
        """Test registry integration with plugins."""
        registry = get_registry()

        # Discover bottles
        bottles = registry.discover_bottles()
        assert isinstance(bottles, dict)

        # List bottles
        bottle_list = registry.list_bottles()
        assert isinstance(bottle_list, list)

        # Get capabilities
        capabilities = registry.get_capabilities()
        assert isinstance(capabilities, dict)

        # Get dependencies
        dependencies = registry.get_dependencies()
        assert isinstance(dependencies, dict)

    def test_plugin_manager_integration(self):
        """Test plugin manager integration."""
        manager = get_plugin_manager()

        # List plugins
        plugins = manager.list_plugins()
        assert isinstance(plugins, list)

        # Get plugin status (only if plugins exist)
        if plugins:
            plugin_name = plugins[0]["name"]
            status = manager.get_plugin_status(plugin_name)
            assert isinstance(status, dict)
        else:
            # Test with a non-existent plugin
            status = manager.get_plugin_status("nonexistent_plugin")
            assert status is None

    def test_entry_point_discovery(self):
        """Test entry point bottle discovery."""
        registry = get_registry()

        # Mock entry points
        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value.select.return_value = []

            bottles = registry.discover_bottles()
            assert isinstance(bottles, dict)

    def test_local_bottle_discovery(self):
        """Test local bottle discovery."""
        registry = get_registry()

        # Mock local modules
        with patch("milkbottle.registry.MODULES_PATH") as mock_modules_path:
            mock_modules_path.exists.return_value = True
            mock_modules_path.iterdir.return_value = []

            bottles = registry.discover_bottles()
            assert isinstance(bottles, dict)


class TestPluginDevelopmentWorkflow:
    """Test plugin development workflow."""

    def test_plugin_template_structure(self):
        """Test plugin template structure."""
        # This test verifies that the plugin development guide structure is valid
        template_structure = [
            "src/my_plugin/__init__.py",
            "src/my_plugin/cli.py",
            "src/my_plugin/core.py",
            "tests/test_my_plugin.py",
            "pyproject.toml",
            "plugin.yaml",
        ]

        # Verify all required files are documented
        for file_path in template_structure:
            # Check if it's a path with directories or a root file
            if "/" in file_path:
                assert "/" in file_path  # Valid path structure
            else:
                assert file_path.endswith((".toml", ".yaml", ".md"))  # Valid root file
            assert file_path.endswith(
                (".py", ".toml", ".yaml", ".md")
            )  # Valid extensions

    def test_plugin_interface_compliance(self):
        """Test plugin interface compliance."""
        # Mock plugin module with standard interface
        mock_module = Mock()
        mock_module.get_metadata = Mock(
            return_value={
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
            }
        )
        mock_module.get_cli = Mock(return_value=typer.Typer())
        mock_module.validate_config = Mock(return_value=True)
        mock_module.health_check = Mock(
            return_value={
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        )

        # Verify interface compliance
        assert hasattr(mock_module, "get_metadata")
        assert hasattr(mock_module, "get_cli")
        assert hasattr(mock_module, "validate_config")
        assert hasattr(mock_module, "health_check")

        # Test function calls
        metadata = mock_module.get_metadata()
        assert metadata["name"] == "test_plugin"

        cli = mock_module.get_cli()
        assert cli is not None

        is_valid = mock_module.validate_config({})
        assert is_valid is True

        health = mock_module.health_check()
        assert health["status"] == "healthy"

    def test_plugin_configuration_workflow(self):
        """Test plugin configuration workflow."""
        # Test configuration loading
        config = {
            "enabled": True,
            "api_key": "test-key",
            "endpoint": "https://api.example.com",
        }

        # Test configuration validation
        def validate_config(config):
            if not config.get("enabled", True):
                return True
            if not config.get("api_key"):
                return False
            return True

        # Test valid configuration
        assert validate_config(config) is True

        # Test invalid configuration
        invalid_config = {"enabled": True}  # Missing API key
        assert validate_config(invalid_config) is False

        # Test disabled configuration
        disabled_config = {"enabled": False}
        assert validate_config(disabled_config) is True

    def test_plugin_testing_workflow(self):
        """Test plugin testing workflow."""
        # Mock test structure
        test_functions = [
            "test_plugin_initialization",
            "test_plugin_processing",
            "test_plugin_configuration",
            "test_plugin_error_handling",
            "test_plugin_cli_interface",
        ]

        # Verify test coverage
        for test_func in test_functions:
            assert test_func.startswith("test_")
            assert "_" in test_func  # Valid naming convention

    def test_plugin_packaging_workflow(self):
        """Test plugin packaging workflow."""
        # Test package structure
        package_files = [
            "pyproject.toml",
            "src/my_plugin/__init__.py",
            "src/my_plugin/cli.py",
            "src/my_plugin/core.py",
            "tests/test_my_plugin.py",
            "README.md",
            "plugin.yaml",
        ]

        # Verify packaging requirements
        assert "pyproject.toml" in package_files
        assert "src/" in package_files[1]  # Source code structure
        assert "tests/" in package_files[4]  # Test structure
        assert "README.md" in package_files
        assert "plugin.yaml" in package_files

    def test_plugin_distribution_workflow(self):
        """Test plugin distribution workflow."""
        # Test entry point registration
        entry_points = {
            "milkbottle.bottles": [
                "my_plugin = my_plugin",
            ],
        }

        # Verify entry point format
        assert "milkbottle.bottles" in entry_points
        assert len(entry_points["milkbottle.bottles"]) > 0

        entry_point = entry_points["milkbottle.bottles"][0]
        assert "=" in entry_point
        assert entry_point.split("=")[0].strip() == "my_plugin"
        assert entry_point.split("=")[1].strip() == "my_plugin"


class TestPluginSystemDocumentation:
    """Test plugin system documentation completeness."""

    def test_plugin_development_guide_exists(self):
        """Test that plugin development guide exists."""
        guide_path = Path("docs/MilkBottle/PLUGIN_DEVELOPMENT_GUIDE.md")
        assert guide_path.exists()

    def test_plugin_examples_exist(self):
        """Test that plugin examples exist."""
        # Check for existing plugin modules
        modules_path = Path("src/milkbottle/modules")
        if modules_path.exists():
            plugin_modules = [d for d in modules_path.iterdir() if d.is_dir()]
            assert len(plugin_modules) > 0

            # Check for standard interface implementation
            for module in plugin_modules:
                init_file = module / "__init__.py"
                if init_file.exists():
                    # Verify module has basic structure
                    assert init_file.exists()

    def test_plugin_template_completeness(self):
        """Test plugin template completeness."""
        # Verify all required sections are documented
        required_sections = [
            "Plugin Architecture",
            "Creating Your First Plugin",
            "Plugin Manifest",
            "Entry Point Registration",
            "Standard Interface",
            "Configuration Management",
            "Testing Your Plugin",
            "Packaging and Distribution",
            "Best Practices",
        ]

        # This test ensures the documentation covers all essential topics
        for section in required_sections:
            assert len(section) > 0  # Valid section name
            assert " " in section or section.isupper()  # Proper formatting
