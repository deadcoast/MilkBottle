"""Tests for {{ plugin_name }}."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from {{ plugin_name }} import {{ class_name }}
from {{ plugin_name }}.cli import cli

class Test{{ class_name }}:
    """Test {{ class_name }}."""

    def test_plugin_creation(self):
        """Test creating the plugin."""
        plugin = {{ class_name }}()
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = {{ class_name }}()
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True

    def test_health_check(self):
        """Test health check."""
        plugin = {{ class_name }}()
        health = plugin.health_check()
        assert "status" in health
        assert "version" in health

class TestCLI:
    """Test CLI interface."""

    def test_status_command(self):
        """Test status command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_config_command(self):
        """Test config command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
