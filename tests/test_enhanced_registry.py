"""Tests for the enhanced MilkBottle registry system."""

from unittest.mock import Mock, patch

import pytest

from milkbottle.registry import (
    BottleRegistry,
    get_registry,
    health_check,
    print_status,
    validate_config,
)


class TestBottleRegistry:
    """Test the BottleRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = BottleRegistry()

    def teardown_method(self):
        """Clean up after each test."""
        # Clear the registry cache to prevent test interference
        self.registry._bottles = {}
        self.registry._health_cache = {}
        self.registry._config_cache = {}
        self.registry._discovery_time = None

    def test_init(self):
        """Test registry initialization."""
        assert self.registry._bottles == {}
        assert self.registry._health_cache == {}
        assert self.registry._config_cache == {}
        assert self.registry._discovery_time is None

    @patch("milkbottle.registry.importlib.metadata.entry_points")
    def test_discover_bottles_empty(self, mock_entry_points):
        """Test discovering bottles when none exist."""
        # Mock entry points to return empty list
        mock_entry_points.return_value.select.return_value = []

        # Mock the discovery methods to return empty results
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(
                self.registry, "_discover_local_bottles", return_value={}
            ):
                # Clear any existing cache
                self.registry._bottles = {}
                self.registry._discovery_time = None

                bottles = self.registry.discover_bottles(force_refresh=True)
                assert bottles == {}

    @patch("milkbottle.registry.importlib.metadata.entry_points")
    def test_discover_bottles_with_mock_module(self, mock_entry_points):
        """Test discovering bottles with a mock module."""
        # Mock entry points to return empty list
        mock_entry_points.return_value.select.return_value = []

        # Create a mock module with standard interface
        mock_module = Mock()
        mock_module.get_metadata.return_value = {
            "name": "test_bottle",
            "version": "1.0.0",
            "description": "Test bottle",
            "author": "Test Author",
            "email": "test@example.com",
            "capabilities": ["test_capability"],
            "dependencies": ["test_dep"],
            "config_schema": {"type": "object"},
        }
        mock_module.get_cli.return_value = Mock()

        # Mock the discovery methods directly
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "version": "1.0.0",
                        "description": "Test bottle",
                        "author": "Test Author",
                        "email": "test@example.com",
                        "capabilities": ["test_capability"],
                        "dependencies": ["test_dep"],
                        "config_schema": {"type": "object"},
                        "has_standard_interface": True,
                        "has_cli": True,
                        "module": mock_module,
                        "cli_loader": lambda: mock_module.get_cli(),
                        "discovery_time": "2025-07-19T04:04:35.097350",
                        "source": "local",
                    }
                }

                # Clear any existing cache
                self.registry._bottles = {}
                self.registry._discovery_time = None

                bottles = self.registry.discover_bottles(force_refresh=True)

                assert "test_bottle" in bottles
                bottle_info = bottles["test_bottle"]
                assert bottle_info["name"] == "test_bottle"
                assert bottle_info["version"] == "1.0.0"
                assert bottle_info["has_standard_interface"] is True
                assert bottle_info["has_cli"] is True

    @patch("milkbottle.registry.importlib.metadata.entry_points")
    def test_discover_bottles_with_basic_module(self, mock_entry_points):
        """Test discovering bottles with a basic module (no standard interface)."""
        # Mock entry points to return empty list
        mock_entry_points.return_value.select.return_value = []

        # Create a mock module without standard interface
        mock_module = Mock()
        mock_module.__alias__ = "basic_bottle"
        mock_module.__version__ = "0.1.0"
        mock_module.__description__ = "Basic bottle"
        mock_module.get_cli.return_value = Mock()

        # Mock the discovery methods directly
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "basic_bottle": {
                        "name": "basic_bottle",
                        "version": "0.1.0",
                        "description": "Basic bottle",
                        "author": "Unknown",
                        "email": "",
                        "capabilities": [],
                        "dependencies": [],
                        "config_schema": {},
                        "has_standard_interface": False,
                        "has_cli": True,
                        "module": mock_module,
                        "cli_loader": lambda: mock_module.get_cli(),
                        "discovery_time": "2025-07-19T04:04:35.097350",
                        "source": "local",
                    }
                }

                # Clear any existing cache
                self.registry._bottles = {}
                self.registry._discovery_time = None

                bottles = self.registry.discover_bottles(force_refresh=True)

                assert "basic_bottle" in bottles
                bottle_info = bottles["basic_bottle"]
                assert bottle_info["name"] == "basic_bottle"
                assert bottle_info["version"] == "0.1.0"
                assert bottle_info["has_standard_interface"] is False
                assert bottle_info["has_cli"] is True

    def test_get_bottle_success(self):
        """Test successfully getting a bottle."""
        mock_cli = Mock()
        mock_module = Mock()
        mock_module.get_cli.return_value = mock_cli

        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_cli": True,
                        "cli_loader": lambda: mock_cli,
                    }
                }

                result = self.registry.get_bottle("test_bottle")
                assert result == mock_cli

    def test_get_bottle_not_found(self):
        """Test getting a bottle that doesn't exist."""
        # Mock the discovery methods to return empty results
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(
                self.registry, "_discover_local_bottles", return_value={}
            ):
                result = self.registry.get_bottle("nonexistent")
                assert result is None

    def test_get_bottle_no_cli(self):
        """Test getting a bottle without CLI interface."""
        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {"name": "test_bottle", "has_cli": False}
                }

                result = self.registry.get_bottle("test_bottle")
                assert result is None

    def test_health_check_all_bottles(self):
        """Test health check for all bottles."""
        mock_module = Mock()
        mock_module.health_check.return_value = {
            "status": "healthy",
            "details": "All good",
        }
        mock_module.get_dependencies.return_value = []

        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "has_cli": True,
                        "module": mock_module,
                        "cli_loader": lambda: Mock(),
                    }
                }

                result = self.registry.health_check()

                assert "timestamp" in result
                assert "overall_status" in result
                assert "bottles" in result
                assert "test_bottle" in result["bottles"]
                assert result["overall_status"] == "healthy"

    def test_health_check_specific_bottle(self):
        """Test health check for a specific bottle."""
        mock_module = Mock()
        mock_module.health_check.return_value = {
            "status": "healthy",
            "details": "All good",
        }
        mock_module.get_dependencies.return_value = []

        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "has_cli": True,
                        "module": mock_module,
                        "cli_loader": lambda: Mock(),
                    }
                }

                result = self.registry.health_check("test_bottle")

                assert "timestamp" in result
                assert "overall_status" in result
                assert "bottles" in result
                assert "test_bottle" in result["bottles"]
                assert result["bottles"]["test_bottle"]["status"] == "healthy"

    def test_health_check_bottle_not_found(self):
        """Test health check for a bottle that doesn't exist."""
        # Mock the discovery methods to return empty results
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(
                self.registry, "_discover_local_bottles", return_value={}
            ):
                result = self.registry.health_check("nonexistent")

                assert result["bottles"]["nonexistent"]["status"] == "critical"
                assert "Bottle not found" in result["bottles"]["nonexistent"]["details"]

    def test_validate_config_success(self):
        """Test successful configuration validation."""
        mock_module = Mock()
        mock_module.validate_config.return_value = True

        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "module": mock_module,
                    }
                }

                is_valid, errors = self.registry.validate_config(
                    "test_bottle", {"enabled": True}
                )

                assert is_valid is True
                assert errors == []

    def test_validate_config_failure(self):
        """Test failed configuration validation."""
        mock_module = Mock()
        mock_module.validate_config.return_value = False

        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "module": mock_module,
                    }
                }

                is_valid, errors = self.registry.validate_config(
                    "test_bottle", {"invalid": "config"}
                )

                assert is_valid is False
                assert "Configuration validation failed" in errors

    def test_validate_config_bottle_not_found(self):
        """Test configuration validation for bottle that doesn't exist."""
        # Mock the discovery methods to return empty results
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(
                self.registry, "_discover_local_bottles", return_value={}
            ):
                is_valid, errors = self.registry.validate_config("nonexistent", {})

                assert is_valid is False
                assert "Bottle 'nonexistent' not found" in errors

    def test_validate_config_no_standard_interface(self):
        """Test configuration validation for bottle without standard interface."""
        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": False,
                    }
                }

                is_valid, errors = self.registry.validate_config("test_bottle", {})

                assert is_valid is False
                assert "Bottle does not implement standard interface" in errors

    def test_list_bottles(self):
        """Test listing bottles."""
        # Mock the discovery methods to return our test bottle
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "version": "1.0.0",
                        "description": "Test bottle",
                        "author": "Test Author",
                        "capabilities": ["test_cap"],
                        "dependencies": ["test_dep"],
                        "has_standard_interface": True,
                        "has_cli": True,
                        "is_valid": True,
                        "source": "local",
                    }
                }

                bottles = self.registry.list_bottles()

                assert len(bottles) == 1
                bottle = bottles[0]
                assert bottle["name"] == "test_bottle"
                assert bottle["version"] == "1.0.0"
                assert bottle["description"] == "Test bottle"

    def test_get_capabilities(self):
        """Test getting capabilities for all bottles."""
        # Mock the discovery methods to return our test bottles
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "capabilities": ["cap1", "cap2"],
                    },
                    "basic_bottle": {
                        "name": "basic_bottle",
                        "has_standard_interface": False,
                        "capabilities": [],
                    },
                }

                capabilities = self.registry.get_capabilities()

                assert "test_bottle" in capabilities
                assert capabilities["test_bottle"] == ["cap1", "cap2"]
                assert "basic_bottle" not in capabilities

    def test_get_dependencies(self):
        """Test getting dependencies for all bottles."""
        # Mock the discovery methods to return our test bottles
        with patch.object(
            self.registry, "_discover_entrypoint_bottles", return_value={}
        ):
            with patch.object(self.registry, "_discover_local_bottles") as mock_local:
                mock_local.return_value = {
                    "test_bottle": {
                        "name": "test_bottle",
                        "has_standard_interface": True,
                        "dependencies": ["dep1", "dep2"],
                    },
                    "basic_bottle": {
                        "name": "basic_bottle",
                        "has_standard_interface": False,
                        "dependencies": [],
                    },
                }

                dependencies = self.registry.get_dependencies()

                assert "test_bottle" in dependencies
                assert dependencies["test_bottle"] == ["dep1", "dep2"]
                assert "basic_bottle" not in dependencies

    def test_print_status(self):
        """Test printing status."""
        self.registry._bottles = {
            "test_bottle": {
                "name": "test_bottle",
                "version": "1.0.0",
                "description": "Test bottle",
                "has_standard_interface": True,
                "has_cli": True,
                "is_valid": True,
            }
        }

        # This should not raise an exception
        self.registry.print_status()


class TestRegistryFunctions:
    """Test the registry functions."""

    def test_get_registry(self):
        """Test getting the registry instance."""
        registry_instance = get_registry()
        assert isinstance(registry_instance, BottleRegistry)

    def test_health_check_function(self):
        """Test the health_check function."""
        result = health_check()
        assert "timestamp" in result
        assert "overall_status" in result
        assert "bottles" in result

    def test_health_check_function_with_alias(self):
        """Test the health_check function with specific alias."""
        result = health_check("nonexistent")
        assert "timestamp" in result
        assert "overall_status" in result
        assert "bottles" in result

    def test_validate_config_function(self):
        """Test the validate_config function."""
        is_valid, errors = validate_config("nonexistent", {})
        assert is_valid is False
        assert "Bottle 'nonexistent' not found" in errors

    def test_print_status_function(self):
        """Test the print_status function."""
        # This should not raise an exception
        print_status()


class TestRegistryIntegration:
    """Test registry integration with real modules."""

    def test_registry_with_real_modules(self):
        """Test registry with real modules (if available)."""
        registry_instance = get_registry()
        bottles = registry_instance.discover_bottles(force_refresh=True)

        # Should discover at least some modules
        assert isinstance(bottles, dict)

        # Check that discovered bottles have required fields
        for bottle_name, bottle_info in bottles.items():
            assert "name" in bottle_info
            assert "version" in bottle_info
            assert "description" in bottle_info
            assert "has_standard_interface" in bottle_info
            assert "has_cli" in bottle_info

    def test_health_check_integration(self):
        """Test health check integration with real modules."""
        registry_instance = get_registry()
        result = registry_instance.health_check()

        assert "timestamp" in result
        assert "overall_status" in result
        assert "bottles" in result

        # Check that health check provides meaningful information
        assert result["overall_status"] in ["healthy", "warning", "critical"]

    def test_config_validation_integration(self):
        """Test configuration validation integration."""
        registry_instance = get_registry()
        bottles = registry_instance.discover_bottles(force_refresh=True)

        # Test validation for each bottle with standard interface
        for bottle_name, bottle_info in bottles.items():
            if bottle_info.get("has_standard_interface"):
                is_valid, errors = registry_instance.validate_config(
                    bottle_name, {"enabled": True}
                )
                assert isinstance(is_valid, bool)
                assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__])
