"""Integration tests for Phase 5 components."""

import asyncio
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from milkbottle.cli import cli
from milkbottle.performance.optimizer import (
    cache_manager,
    performance_monitor_instance,
    resource_optimizer,
)
from milkbottle.plugin_sdk import PluginSDK


class TestPhase5Integration:
    """Test Phase 5 system integration."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MilkBottle - Modular CLI Toolbox" in result.output
        assert "deployment" in result.output
        assert "marketplace" in result.output
        assert "performance" in result.output
        assert "sdk" in result.output

    def test_sdk_help(self, runner):
        """Test SDK help command."""
        result = runner.invoke(cli, ["sdk", "--help"])
        assert result.exit_code == 0
        assert "Plugin SDK commands" in result.output
        assert "create" in result.output
        assert "validate" in result.output
        assert "test" in result.output
        assert "package" in result.output
        assert "templates" in result.output

    def test_performance_help(self, runner):
        """Test performance help command."""
        result = runner.invoke(cli, ["performance", "--help"])
        assert result.exit_code == 0
        assert "Performance optimization commands" in result.output
        assert "start-monitoring" in result.output
        assert "stop-monitoring" in result.output
        assert "metrics" in result.output
        assert "report" in result.output
        assert "optimize-memory" in result.output
        assert "optimize-disk" in result.output
        assert "cache-stats" in result.output
        assert "clear-cache" in result.output

    def test_deployment_help(self, runner):
        """Test deployment help command."""
        result = runner.invoke(cli, ["deployment", "--help"])
        assert result.exit_code == 0
        assert "Deployment management commands" in result.output
        assert "deploy" in result.output
        assert "rollback" in result.output
        assert "scaling" in result.output
        assert "monitoring" in result.output
        assert "security" in result.output
        assert "backup" in result.output
        assert "cicd" in result.output
        assert "docker" in result.output

    def test_marketplace_help(self, runner):
        """Test marketplace help command."""
        result = runner.invoke(cli, ["marketplace", "--help"])
        assert result.exit_code == 0
        assert "Plugin marketplace commands" in result.output
        assert "search" in result.output
        assert "install" in result.output
        assert "info" in result.output
        assert "rate" in result.output
        assert "reviews" in result.output
        assert "popular" in result.output
        assert "recent" in result.output
        assert "category" in result.output
        assert "analytics" in result.output
        assert "security-scan" in result.output
        assert "validate" in result.output

    def test_status_command(self, runner):
        """Test status command."""
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "MilkBottle System Status" in result.output
        assert "Deployment System" in result.output
        assert "Plugin Marketplace" in result.output
        assert "Plugin SDK" in result.output
        assert "Performance System" in result.output
        assert "Cache System" in result.output

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "MilkBottle v" in result.output

    def test_sdk_templates_command(self, runner):
        """Test SDK templates command."""
        result = runner.invoke(cli, ["sdk", "templates"])
        assert result.exit_code == 0
        assert "Available Plugin Templates" in result.output
        assert "basic" in result.output
        assert "cli" in result.output
        assert "web" in result.output
        assert "api" in result.output

    def test_performance_cache_stats_command(self, runner):
        """Test performance cache stats command."""
        result = runner.invoke(cli, ["performance", "cache-stats"])
        assert result.exit_code == 0
        assert "Cache Statistics" in result.output
        assert "Cache Size" in result.output
        assert "Max Size" in result.output
        assert "Hit Rate" in result.output
        assert "Memory Usage" in result.output

    def test_performance_clear_cache_command(self, runner):
        """Test performance clear cache command."""
        result = runner.invoke(cli, ["performance", "clear-cache"])
        assert result.exit_code == 0
        assert "Cache cleared" in result.output

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration."""
        # Start monitoring
        await performance_monitor_instance.start_monitoring(interval=1)

        # Get metrics
        metrics = await performance_monitor_instance.collect_system_metrics()
        assert metrics is not None
        assert hasattr(metrics, "cpu_usage")
        assert hasattr(metrics, "memory_usage")
        assert hasattr(metrics, "disk_io")
        assert hasattr(metrics, "response_time")

        # Stop monitoring
        await performance_monitor_instance.stop_monitoring()

    @pytest.mark.asyncio
    async def test_cache_manager_integration(self):
        """Test cache manager integration."""
        # Set cache value
        cache_manager.set("test_key", "test_value")

        # Get cache value
        value = cache_manager.get("test_key")
        assert value == "test_value"

        # Get stats
        stats = cache_manager.get_stats()
        assert stats["size"] == 1
        assert stats["hit_rate"] > 0

        # Clear cache
        cache_manager.clear()
        stats = cache_manager.get_stats()
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_resource_optimizer_integration(self):
        """Test resource optimizer integration."""
        # Optimize memory
        result = await resource_optimizer.optimize_memory()
        assert result is not None
        assert "success" in result

        # Test disk optimization with temp directory
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await resource_optimizer.optimize_disk_usage(Path(temp_dir))
            assert result is not None
            assert "success" in result

    def test_plugin_sdk_integration(self):
        """Test plugin SDK integration."""
        sdk = PluginSDK()

        # List templates
        templates = sdk.list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Get template info
        template_info = sdk.get_template_info("basic")
        assert template_info is not None
        assert "name" in template_info
        assert "description" in template_info

    def test_cli_with_config(self, runner, temp_dir):
        """Test CLI with configuration file."""
        # Create a test config file
        config_file = temp_dir / "test_config.toml"
        config_file.write_text(
            """
[plugin_system]
plugin_dir = "/tmp/plugins"
enable_marketplace = true

[performance]
cache_size = 500
monitoring_interval = 30
        """
        )

        result = runner.invoke(cli, ["--config", str(config_file), "status"])
        assert result.exit_code == 0

    def test_cli_verbose_mode(self, runner):
        """Test CLI verbose mode."""
        result = runner.invoke(cli, ["--verbose", "status"])
        assert result.exit_code == 0

    def test_cli_debug_mode(self, runner):
        """Test CLI debug mode."""
        result = runner.invoke(cli, ["--debug", "status"])
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_performance_report_integration(self):
        """Test performance report integration."""
        # Start monitoring briefly
        await performance_monitor_instance.start_monitoring(interval=1)
        await asyncio.sleep(2)  # Collect some data
        await performance_monitor_instance.stop_monitoring()

        # Get report
        report = performance_monitor_instance.get_performance_report()
        assert report is not None
        assert "current" in report
        assert "average_5min" in report
        assert "average_1hour" in report

    def test_all_commands_exist(self, runner):
        """Test that all expected commands exist."""
        # Test all main command groups
        commands = [
            "deployment",
            "marketplace",
            "performance",
            "sdk",
            "status",
            "version",
        ]

        for command in commands:
            result = runner.invoke(cli, [command, "--help"])
            assert result.exit_code == 0, f"Command {command} failed"

    def test_error_handling(self, runner):
        """Test error handling in CLI."""
        # Test invalid command
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0

        # Test invalid option
        result = runner.invoke(cli, ["--invalid-option"])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
