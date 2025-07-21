"""Integration tests for Phase 2 enhancements."""

import pytest

from milkbottle import registry
from milkbottle.milk_bottle import (
    _show_system_status,
    _validate_bottle_configurations,
    show_main_menu,
)


class TestPhase2Integration:
    """Integration tests for Phase 2 enhancements."""

    def test_registry_discovery_integration(self):
        """Test that registry can discover all modules with enhanced metadata."""
        registry_instance = registry.get_registry()

        # Discover bottles
        bottles = registry_instance.discover_bottles(force_refresh=True)

        # Should find the modules we know exist
        expected_modules = ["pdfmilker", "venvmilker", "fontmilker"]
        found_modules = [name for name in bottles.keys() if name in expected_modules]

        # At least some modules should be found
        assert found_modules

        # Check that found modules have enhanced metadata
        for module_name in found_modules:
            bottle_info = bottles[module_name]

            # Required fields
            assert "name" in bottle_info
            assert "version" in bottle_info
            assert "description" in bottle_info
            assert "has_cli" in bottle_info
            assert "has_standard_interface" in bottle_info
            assert "discovery_time" in bottle_info
            assert "source" in bottle_info

            # Enhanced metadata fields
            assert "capabilities" in bottle_info
            assert "dependencies" in bottle_info
            assert "config_schema" in bottle_info
            assert "author" in bottle_info
            assert "email" in bottle_info

    def test_health_check_integration(self):
        """Test comprehensive health check integration."""
        registry_instance = registry.get_registry()

        # Perform health check for all bottles
        health_result = registry_instance.health_check()

        self._extracted_from_test_health_check_integration_19(
            "timestamp", health_result, "overall_status", "bottles"
        )
        # Check that overall status is valid
        assert health_result["overall_status"] in ["healthy", "warning", "critical"]

        # Check that bottles have health information
        if health_result["bottles"]:
            for bottle_name, health_info in health_result["bottles"].items():
                self._extracted_from_test_health_check_integration_19(
                    "status", health_info, "details", "timestamp"
                )
                assert "version" in health_info

                # Check that status is valid
                assert health_info["status"] in ["healthy", "warning", "critical"]

                # Check that checks are present
                if "checks" in health_info:
                    for check_name, check_info in health_info["checks"].items():
                        assert "status" in check_info
                        assert "details" in check_info

    # TODO Rename this here and in `test_health_check_integration`
    def _extracted_from_test_health_check_integration_19(self, arg0, arg1, arg2, arg3):
        assert arg0 in arg1
        assert arg2 in arg1
        assert arg3 in arg1

    def test_configuration_validation_integration(self):
        """Test configuration validation integration."""
        registry_instance = registry.get_registry()

        # Get bottles with standard interface
        bottles = registry_instance.list_bottles()
        if standard_bottles := [b for b in bottles if b["has_standard_interface"]]:
            # Test configuration validation for first standard bottle
            first_bottle = standard_bottles[0]
            bottle_name = first_bottle["name"]

            # Test valid configuration
            is_valid, errors = registry_instance.validate_config(
                bottle_name, {"enabled": True}
            )

            # Should be valid for basic config
            assert is_valid is True
            assert errors == []

            # Test invalid configuration
            is_valid, errors = registry_instance.validate_config(
                bottle_name, {"invalid_field": "invalid_value"}
            )

            # Should provide error messages
            assert isinstance(errors, list)

    def test_capabilities_and_dependencies_integration(self):
        """Test capabilities and dependencies integration."""
        registry_instance = registry.get_registry()

        # Get capabilities
        capabilities = registry_instance.get_capabilities()
        assert isinstance(capabilities, dict)

        # Get dependencies
        dependencies = registry_instance.get_dependencies()
        assert isinstance(dependencies, dict)

        # Check that capabilities and dependencies are consistent
        bottles = registry_instance.list_bottles()
        standard_bottles = [b for b in bottles if b["has_standard_interface"]]

        for bottle in standard_bottles:
            bottle_name = bottle["name"]

            # Check capabilities
            if bottle_name in capabilities:
                assert isinstance(capabilities[bottle_name], list)
                assert len(capabilities[bottle_name]) > 0

            # Check dependencies
            if bottle_name in dependencies:
                assert isinstance(dependencies[bottle_name], list)

    def test_backward_compatibility_integration(self):
        """Test that backward compatibility is maintained."""
        # Test original functions still work
        bottles = registry.list_bottles()
        assert isinstance(bottles, list)

        # Test that we can get bottle metadata
        if bottles:
            first_bottle = bottles[0]
            bottle_name = first_bottle["name"]

            # Test original get_bottle function
            bottle_cli = registry.get_bottle(bottle_name)
            # Should return None or a valid CLI object
            assert bottle_cli is None or hasattr(bottle_cli, "__call__")

    def test_enhanced_functions_integration(self):
        """Test that enhanced functions work correctly."""
        # Test get_registry
        registry_instance = registry.get_registry()
        assert registry_instance is not None

        # Test health_check function
        health_result = registry.health_check()
        assert "timestamp" in health_result
        assert "overall_status" in health_result

        if bottles := registry.list_bottles():
            first_bottle = bottles[0]
            bottle_name = first_bottle["name"]

            is_valid, errors = registry.validate_config(bottle_name, {"enabled": True})
            assert isinstance(is_valid, bool)
            assert isinstance(errors, list)

    def test_registry_status_display(self):
        """Test that registry status display works."""
        registry_instance = registry.get_registry()

        # This should not raise any exceptions
        try:
            registry_instance.print_status()
        except Exception as e:
            pytest.fail(f"print_status() raised an exception: {e}")

    def test_module_metadata_consistency(self):
        """Test that module metadata is consistent across different access methods."""
        registry_instance = registry.get_registry()

        # Get bottles through different methods
        bottles_discovery = registry_instance.discover_bottles()
        bottles_list = registry_instance.list_bottles()

        # Check that we get consistent information
        discovery_names = set(bottles_discovery.keys())
        list_names = {bottle["name"] for bottle in bottles_list}

        # Should have same bottles
        assert discovery_names == list_names

        # Check metadata consistency
        for bottle_name in discovery_names:
            discovery_info = bottles_discovery[bottle_name]
            list_info = next(b for b in bottles_list if b["name"] == bottle_name)

            # Check key fields are consistent
            assert discovery_info["name"] == list_info["name"]
            assert discovery_info["version"] == list_info["version"]
            assert discovery_info["description"] == list_info["description"]
            assert (
                discovery_info["has_standard_interface"]
                == list_info["has_standard_interface"]
            )
            assert discovery_info["has_cli"] == list_info["has_cli"]

    def test_error_handling_integration(self):
        """Test that error handling works correctly."""
        registry_instance = registry.get_registry()

        # Test with non-existent bottle
        bottle_cli = registry_instance.get_bottle("nonexistent_bottle")
        assert bottle_cli is None

        # Test health check for non-existent bottle
        health_result = registry_instance.health_check("nonexistent_bottle")
        assert "bottles" in health_result
        assert "nonexistent_bottle" in health_result["bottles"]
        assert health_result["bottles"]["nonexistent_bottle"]["status"] == "critical"

        # Test configuration validation for non-existent bottle
        is_valid, errors = registry_instance.validate_config("nonexistent_bottle", {})
        assert is_valid is False
        assert len(errors) > 0
        assert "not found" in errors[0]

    def test_caching_integration(self):
        """Test that caching works correctly."""
        registry_instance = registry.get_registry()

        # First discovery
        bottles1 = registry_instance.discover_bottles()
        discovery_time1 = registry_instance._discovery_time

        # Second discovery (should use cache)
        bottles2 = registry_instance.discover_bottles()
        discovery_time2 = registry_instance._discovery_time

        # Should be same time (cached)
        assert discovery_time1 == discovery_time2

        # Force refresh
        bottles3 = registry_instance.discover_bottles(force_refresh=True)
        discovery_time3 = registry_instance._discovery_time

        # Should be different time (refreshed)
        assert discovery_time3 is not None and discovery_time1 is not None
        assert discovery_time3 > discovery_time1

        # Results should be consistent
        assert set(bottles1.keys()) == set(bottles2.keys()) == set(bottles3.keys())


class TestMainApplicationIntegration:
    """Integration tests for main application enhancements."""

    def test_main_application_imports(self):
        """Test that main application imports work correctly."""
        # Test that enhanced functions are available
        from milkbottle.milk_bottle import _show_bottle_selection, _show_configuration

        # All functions should be callable
        assert callable(show_main_menu)
        assert callable(_show_system_status)
        assert callable(_validate_bottle_configurations)
        assert callable(_show_bottle_selection)
        assert callable(_show_configuration)

    def test_enhanced_cli_commands(self):
        """Test that enhanced CLI commands are available."""
        from milkbottle.milk_bottle import cli

        # Check that new commands are available
        # Click commands are stored in cli.commands as a dict
        commands = list(cli.commands.keys())  # type: ignore

        # Should have original commands
        assert "main" in commands
        assert "version" in commands
        assert "bottle" in commands

        # Should have new enhanced commands
        assert "status" in commands
        assert "validate" in commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
