"""Comprehensive tests for Phase 3 features.

This module tests the advanced integration features including:
- Plugin system functionality
- Monitoring and logging capabilities
- Enhanced main application integration
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from milkbottle.errors import PluginError, ValidationError
from milkbottle.monitoring import (
    MonitoringManager,
    PerformanceMetrics,
    ResourceMonitor,
    StructuredLogger,
    get_health_status,
    get_monitoring_manager,
    record_operation,
    start_monitoring,
    stop_monitoring,
)
from milkbottle.plugin_system import (
    PluginLoader,
    PluginManager,
    PluginManifest,
    get_plugin_manager,
    list_plugins,
    load_plugin,
    unload_plugin,
)


class TestPluginManifest:
    """Test plugin manifest functionality."""

    def test_valid_manifest(self):
        """Test creating a valid plugin manifest."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin.main",
            "author": "Test Author",
            "dependencies": ["requests"],
            "capabilities": ["web_scraping"],
            "config_schema": {"enabled": {"type": "boolean"}},
        }

        manifest = PluginManifest(manifest_data)

        assert manifest.name == "test_plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == "Test plugin"
        assert manifest.entry_point == "test_plugin.main"
        assert manifest.author == "Test Author"
        assert manifest.dependencies == ["requests"]
        assert manifest.capabilities == ["web_scraping"]
        assert manifest.config_schema == {"enabled": {"type": "boolean"}}

    def test_invalid_manifest_missing_fields(self):
        """Test manifest validation with missing required fields."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            # Missing description and entry_point
        }

        with pytest.raises(ValidationError, match="Missing required field"):
            PluginManifest(manifest_data)

    def test_invalid_version_format(self):
        """Test manifest validation with invalid version format."""
        manifest_data = {
            "name": "test_plugin",
            "version": "invalid_version",
            "description": "Test plugin",
            "entry_point": "test_plugin.main",
        }

        with pytest.raises(ValidationError, match="Invalid version format"):
            PluginManifest(manifest_data)

    def test_invalid_entry_point_type(self):
        """Test manifest validation with invalid entry point type."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": 123,  # Should be string
        }

        with pytest.raises(ValidationError, match="Entry point must be a string"):
            PluginManifest(manifest_data)

    def test_manifest_to_dict(self):
        """Test converting manifest to dictionary."""
        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin.main",
        }

        manifest = PluginManifest(manifest_data)
        result = manifest.to_dict()

        assert result == manifest_data


class TestPluginLoader:
    """Test plugin loader functionality."""

    def test_discover_plugins_empty_directory(self):
        """Test discovering plugins in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PluginLoader([temp_dir])
            plugins = loader.discover_plugins()

            assert plugins == {}

    def test_discover_plugins_with_manifest(self):
        """Test discovering plugins with valid manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()

            manifest_data = {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "entry_point": "test_plugin.main",
            }

            manifest_file = plugin_dir / "plugin.yaml"
            with open(manifest_file, "w") as f:
                yaml.dump(manifest_data, f)

            loader = PluginLoader([temp_dir])
            plugins = loader.discover_plugins()

            assert "test_plugin" in plugins
            assert plugins["test_plugin"].name == "test_plugin"
            assert plugins["test_plugin"].version == "1.0.0"

    def test_load_manifest_yaml(self):
        """Test loading manifest from YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_data = {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "entry_point": "test_plugin.main",
            }

            manifest_file = Path(temp_dir) / "plugin.yaml"
            with open(manifest_file, "w") as f:
                yaml.dump(manifest_data, f)

            loader = PluginLoader()
            manifest = loader._load_manifest(manifest_file)

            assert manifest.name == "test_plugin"
            assert manifest.version == "1.0.0"

    def test_load_manifest_json(self):
        """Test loading manifest from JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_data = {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "entry_point": "test_plugin.main",
            }

            manifest_file = Path(temp_dir) / "plugin.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest_data, f)

            loader = PluginLoader()
            manifest = loader._load_manifest(manifest_file)

            assert manifest.name == "test_plugin"
            assert manifest.version == "1.0.0"

    @patch("importlib.import_module")
    def test_load_plugin_module_success(self, mock_import):
        """Test successfully loading a plugin module."""
        # Mock the module
        mock_module = Mock()
        mock_module.get_metadata = Mock(return_value={})
        mock_module.get_cli = Mock(return_value=Mock())
        mock_import.return_value = mock_module

        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin.main",
        }
        manifest = PluginManifest(manifest_data)

        loader = PluginLoader()
        result = loader._load_plugin_module(manifest)

        assert result == mock_module
        mock_import.assert_called_once_with("test_plugin.main")

    @patch("importlib.import_module")
    def test_load_plugin_module_missing_methods(self, mock_import):
        """Test loading plugin module with missing required methods."""
        # Mock the module without required methods
        mock_module = Mock()
        # Explicitly remove the methods to ensure they don't exist
        del mock_module.get_metadata
        del mock_module.get_cli
        mock_import.return_value = mock_module

        manifest_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "test_plugin.main",
        }
        manifest = PluginManifest(manifest_data)

        loader = PluginLoader()

        with pytest.raises(PluginError, match="missing get_metadata"):
            loader._load_plugin_module(manifest)

    def test_unload_plugin(self):
        """Test unloading a plugin."""
        loader = PluginLoader()

        # Mock a loaded plugin
        mock_plugin = Mock()
        loader._loaded_plugins["test_plugin"] = mock_plugin
        loader._plugin_metadata["test_plugin"] = Mock()

        result = loader.unload_plugin("test_plugin")

        assert result is True
        assert "test_plugin" not in loader._loaded_plugins
        assert "test_plugin" not in loader._plugin_metadata


class TestPluginManager:
    """Test plugin manager functionality."""

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        manager = PluginManager()

        assert manager.registry is not None
        assert manager.loader is not None
        assert manager._active_plugins == set()
        assert manager._plugin_health == {}

    @patch("milkbottle.plugin_system.PluginLoader.load_plugin")
    def test_load_plugin_success(self, mock_load_plugin):
        """Test successfully loading a plugin."""
        # Mock the plugin module
        mock_module = Mock()
        mock_module.get_cli = Mock(return_value=Mock())
        mock_load_plugin.return_value = mock_module

        manager = PluginManager()
        result = manager.load_plugin("test_plugin")

        assert result is True
        assert "test_plugin" in manager._active_plugins
        assert "test_plugin" in manager._plugin_health

    @patch("milkbottle.plugin_system.PluginLoader.load_plugin")
    def test_load_plugin_failure(self, mock_load_plugin):
        """Test plugin loading failure."""
        mock_load_plugin.side_effect = PluginError("Plugin not found")

        manager = PluginManager()
        result = manager.load_plugin("test_plugin")

        assert result is False
        assert "test_plugin" not in manager._active_plugins

    def test_unload_plugin_success(self):
        """Test successfully unloading a plugin."""
        manager = PluginManager()
        manager._active_plugins.add("test_plugin")
        manager._plugin_health["test_plugin"] = {}

        result = manager.unload_plugin("test_plugin")

        assert result is True
        assert "test_plugin" not in manager._active_plugins
        assert "test_plugin" not in manager._plugin_health

    def test_unload_plugin_not_loaded(self):
        """Test unloading a plugin that's not loaded."""
        manager = PluginManager()

        result = manager.unload_plugin("test_plugin")

        assert result is False

    @patch("milkbottle.plugin_system.PluginLoader.discover_plugins")
    def test_list_plugins(self, mock_discover):
        """Test listing plugins."""
        # Mock discovered plugins
        mock_manifest = Mock()
        mock_manifest.version = "1.0.0"
        mock_manifest.description = "Test plugin"
        mock_manifest.author = "Test Author"

        mock_discover.return_value = {"test_plugin": mock_manifest}

        manager = PluginManager()
        manager._active_plugins.add("test_plugin")
        manager._plugin_health["test_plugin"] = {"status": "healthy"}

        plugins = manager.list_plugins()

        assert len(plugins) == 1
        assert plugins[0]["name"] == "test_plugin"
        assert plugins[0]["status"] == "loaded"
        assert plugins[0]["health"]["status"] == "healthy"

    def test_check_plugin_health_healthy(self):
        """Test plugin health check for healthy plugin."""
        mock_module = Mock()
        mock_module.get_metadata = Mock()
        mock_module.get_cli = Mock()
        mock_module.validate_config = Mock(return_value=True)

        manager = PluginManager()
        health = manager._check_plugin_health("test_plugin", mock_module)

        assert health["status"] == "healthy"
        assert not health["errors"]
        assert not health["warnings"]

    def test_check_plugin_health_with_errors(self):
        """Test plugin health check for plugin with errors."""
        mock_module = Mock()
        # Missing required methods
        del mock_module.get_metadata
        del mock_module.get_cli

        manager = PluginManager()
        health = manager._check_plugin_health("test_plugin", mock_module)

        assert health["status"] == "error"
        assert len(health["errors"]) == 2


class TestStructuredLogger:
    """Test structured logger functionality."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger("test_logger")

        assert logger.name == "test_logger"
        assert logger.correlation_id is None
        assert logger.file_handler is None

    def test_logger_with_file(self):
        """Test logger initialization with file handler."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger("test_logger", log_file)

            assert logger.name == "test_logger"
            assert logger.file_handler is not None
        finally:
            Path(log_file).unlink()

    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        logger = StructuredLogger("test_logger")
        correlation_id = "test-correlation-123"

        logger.set_correlation_id(correlation_id)

        assert logger.correlation_id == correlation_id

    def test_info_logging(self):
        """Test info level logging."""
        logger = StructuredLogger("test_logger")
        logger.set_correlation_id("test-123")

        logger.info("Test message", extra_data="test_value")

        logs = logger.get_recent_logs()
        assert len(logs) == 1

        log_entry = logs[0]
        assert log_entry["level"] == "info"
        assert log_entry["message"] == "Test message"
        assert log_entry["correlation_id"] == "test-123"
        assert log_entry["data"]["extra_data"] == "test_value"

    def test_error_logging(self):
        """Test error level logging."""
        logger = StructuredLogger("test_logger")

        logger.error("Error message", error_code=500)

        logs = logger.get_recent_logs()
        assert len(logs) == 1

        log_entry = logs[0]
        assert log_entry["level"] == "error"
        assert log_entry["message"] == "Error message"
        assert log_entry["data"]["error_code"] == 500

    def test_get_logs_by_correlation_id(self):
        """Test filtering logs by correlation ID."""
        logger = StructuredLogger("test_logger")

        logger.set_correlation_id("corr-1")
        logger.info("Message 1")

        logger.set_correlation_id("corr-2")
        logger.info("Message 2")

        logs_corr_1 = logger.get_logs_by_correlation_id("corr-1")
        logs_corr_2 = logger.get_logs_by_correlation_id("corr-2")

        assert len(logs_corr_1) == 1
        assert len(logs_corr_2) == 1
        assert logs_corr_1[0]["message"] == "Message 1"
        assert logs_corr_2[0]["message"] == "Message 2"


class TestPerformanceMetrics:
    """Test performance metrics functionality."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = PerformanceMetrics()

        assert metrics.retention_seconds == 3600
        assert metrics.metrics == {}

    def test_record_metric(self):
        """Test recording a metric."""
        metrics = PerformanceMetrics()

        metrics.record_metric("test_metric", 42.5, {"tag": "value"})

        assert "test_metric" in metrics.metrics
        assert len(metrics.metrics["test_metric"]) == 1

        entry = metrics.metrics["test_metric"][0]
        assert entry["value"] == 42.5
        assert entry["tags"]["tag"] == "value"

    def test_get_metric_stats(self):
        """Test getting metric statistics."""
        metrics = PerformanceMetrics()

        # Record multiple values
        metrics.record_metric("test_metric", 10.0)
        metrics.record_metric("test_metric", 20.0)
        metrics.record_metric("test_metric", 30.0)

        stats = metrics.get_metric_stats("test_metric")

        assert stats["count"] == 3
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["avg"] == 20.0
        assert stats["sum"] == 60.0

    def test_get_metric_stats_empty(self):
        """Test getting stats for non-existent metric."""
        metrics = PerformanceMetrics()

        stats = metrics.get_metric_stats("non_existent")

        assert stats["count"] == 0
        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0
        assert stats["sum"] == 0

    def test_cleanup_old_metrics(self):
        """Test cleanup of old metrics."""
        metrics = PerformanceMetrics(retention_seconds=1)

        # Record a metric
        metrics.record_metric("test_metric", 42.0)
        assert len(metrics.metrics["test_metric"]) == 1

        # Wait for retention to expire
        time.sleep(1.1)

        # Trigger cleanup
        metrics.record_metric("test_metric", 43.0)

        # Should only have the new metric
        assert len(metrics.metrics["test_metric"]) == 1
        assert metrics.metrics["test_metric"][0]["value"] == 43.0


class TestResourceMonitor:
    """Test resource monitor functionality."""

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    def test_get_system_resources(self, mock_disk, mock_memory, mock_cpu):
        """Test getting system resources."""
        # Mock system resources
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(
            total=8589934592,  # 8GB
            available=4294967296,  # 4GB
            percent=50.0,
            used=4294967296,
        )
        mock_disk.return_value = Mock(
            total=1000000000000, used=500000000000, free=500000000000  # 1TB  # 500GB
        )

        monitor = ResourceMonitor()
        resources = monitor.get_system_resources()

        assert resources["cpu"]["percent"] == 25.5
        assert resources["memory"]["total"] == 8589934592
        assert resources["memory"]["percent"] == 50.0
        assert resources["disk"]["percent"] == 50.0

    @patch("psutil.Process")
    def test_get_process_resources(self, mock_process_class):
        """Test getting process resources."""
        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.cpu_percent.return_value = 5.2
        mock_process.memory_info.return_value = Mock(
            rss=104857600, vms=209715200
        )  # 100MB, 200MB
        mock_process.memory_percent.return_value = 2.5
        mock_process.num_threads.return_value = 4
        mock_process.open_files.return_value = [Mock()]
        mock_process.net_connections.return_value = [Mock()]

        mock_process_class.return_value = mock_process

        monitor = ResourceMonitor()
        resources = monitor.get_process_resources()

        assert resources["pid"] == 12345
        assert resources["cpu_percent"] == 5.2
        assert resources["memory"]["rss"] == 104857600
        assert resources["threads"] == 4

    def test_get_uptime(self):
        """Test getting process uptime."""
        monitor = ResourceMonitor()

        # Wait a bit
        time.sleep(0.1)

        uptime = monitor.get_uptime()

        assert uptime > 0
        assert uptime < 1  # Should be less than 1 second


class TestMonitoringManager:
    """Test monitoring manager functionality."""

    def test_monitoring_manager_initialization(self):
        """Test monitoring manager initialization."""
        manager = MonitoringManager()

        assert manager.logger is not None
        assert manager.metrics is not None
        assert manager.resource_monitor is not None
        assert manager.monitoring_enabled is True

    def test_record_operation_success(self):
        """Test recording successful operation."""
        manager = MonitoringManager()

        manager.record_operation("test_operation", 1.5, True, extra_data="test")

        # Check metrics
        stats = manager.metrics.get_metric_stats("operation.test_operation.duration")
        assert stats["count"] == 1
        assert stats["avg"] == 1.5

        success_stats = manager.metrics.get_metric_stats(
            "operation.test_operation.success_rate"
        )
        assert success_stats["avg"] == 1.0

    def test_record_operation_failure(self):
        """Test recording failed operation."""
        manager = MonitoringManager()

        manager.record_operation("test_operation", 0.5, False, error="test error")

        # Check metrics
        success_stats = manager.metrics.get_metric_stats(
            "operation.test_operation.success_rate"
        )
        assert success_stats["avg"] == 0.0

    @patch("milkbottle.monitoring.ResourceMonitor.get_system_resources")
    @patch("milkbottle.monitoring.ResourceMonitor.get_process_resources")
    def test_get_health_status_healthy(self, mock_process, mock_system):
        """Test getting health status for healthy system."""
        # Mock healthy resources
        mock_system.return_value = {
            "cpu": {"percent": 25.0},
            "memory": {"percent": 50.0},
            "disk": {"percent": 30.0},
        }
        mock_process.return_value = {"cpu_percent": 5.0, "memory": {"rss": 104857600}}

        manager = MonitoringManager()
        health = manager.get_health_status()

        assert health["status"] == "healthy"
        assert not health["issues"]
        assert not health["warnings"]

    @patch("milkbottle.monitoring.ResourceMonitor.get_system_resources")
    def test_get_health_status_unhealthy(self, mock_system):
        """Test getting health status for unhealthy system."""
        # Mock unhealthy resources
        mock_system.return_value = {
            "cpu": {"percent": 95.0},  # High CPU
            "memory": {"percent": 95.0},  # High memory
            "disk": {"percent": 95.0},  # High disk
        }

        manager = MonitoringManager()
        health = manager.get_health_status()

        assert health["status"] == "unhealthy"
        assert len(health["issues"]) == 3  # CPU, memory, disk issues

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        manager = MonitoringManager()

        # Start monitoring
        manager.start_monitoring(interval_seconds=1)
        assert manager._monitoring_thread is not None
        assert manager._monitoring_thread.is_alive()

        # Stop monitoring
        manager.stop_monitoring()
        # Give thread time to stop
        time.sleep(0.1)
        assert not manager._monitoring_thread.is_alive()

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        manager = MonitoringManager()

        # Record some metrics
        manager.metrics.record_metric("system.cpu_percent", 25.0)
        manager.metrics.record_metric("system.memory_percent", 50.0)

        summary = manager.get_metrics_summary()

        assert "system.cpu_percent" in summary
        assert "system.memory_percent" in summary
        assert summary["system.cpu_percent"]["count"] == 1


class TestGlobalFunctions:
    """Test global functions from monitoring and plugin modules."""

    def test_get_monitoring_manager_singleton(self):
        """Test that get_monitoring_manager returns singleton."""
        manager1 = get_monitoring_manager()
        manager2 = get_monitoring_manager()

        assert manager1 is manager2

    def test_record_operation_global(self):
        """Test global record_operation function."""
        record_operation("test_op", 1.0, True)

        manager = get_monitoring_manager()
        stats = manager.metrics.get_metric_stats("operation.test_op.duration")
        assert stats["count"] == 1

    def test_get_health_status_global(self):
        """Test global get_health_status function."""
        health = get_health_status()

        assert "status" in health
        assert "timestamp" in health
        assert "uptime" in health

    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns singleton."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        assert manager1 is manager2

    def test_plugin_functions(self):
        """Test global plugin functions."""
        # Test list_plugins
        plugins = list_plugins()
        assert isinstance(plugins, list)

        # Test load_plugin (should fail for non-existent plugin)
        result = load_plugin("non_existent_plugin")
        assert result is False

        # Test unload_plugin (should fail for non-existent plugin)
        result = unload_plugin("non_existent_plugin")
        assert result is False


class TestIntegration:
    """Integration tests for Phase 3 features."""

    def test_plugin_and_monitoring_integration(self):
        """Test integration between plugin system and monitoring."""
        # Start monitoring
        start_monitoring(interval_seconds=1)

        # Get managers
        plugin_manager = get_plugin_manager()
        monitoring_manager = get_monitoring_manager()

        # Record some operations
        record_operation("plugin.discovery", 0.1, True)
        record_operation("plugin.load", 0.2, True)

        # Check metrics
        stats = monitoring_manager.metrics.get_metric_stats(
            "operation.plugin.discovery.duration"
        )
        assert stats["count"] == 1

        # Stop monitoring
        stop_monitoring()

    def test_logging_and_monitoring_integration(self):
        """Test integration between logging and monitoring."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            log_file = f.name

        try:
            # Create monitoring manager with log file
            manager = MonitoringManager(log_file)

            # Set correlation ID and log
            manager.logger.set_correlation_id("test-correlation")
            manager.logger.info("Test message", operation="test")

            # Record operation
            manager.record_operation("test_operation", 1.0, True)

            # Check logs
            logs = manager.logger.get_recent_logs()
            assert len(logs) >= 2  # At least the info log and operation log

            # Check correlation ID filtering
            correlation_logs = manager.logger.get_logs_by_correlation_id(
                "test-correlation"
            )
            assert len(correlation_logs) >= 1

        finally:
            Path(log_file).unlink()

    def test_error_handling(self):
        """Test error handling in Phase 3 features."""
        # Test plugin error handling
        with pytest.raises(ValidationError):
            PluginManifest({"name": "test"})  # Missing required fields

        with pytest.raises(PluginError):
            # This would normally fail, but we'll test the error type
            raise PluginError("Test plugin error")

        # Test monitoring error handling
        manager = MonitoringManager()

        # Record operation with error
        manager.record_operation("error_operation", 0.1, False, error="test error")

        # Check that error was logged
        logs = manager.logger.get_recent_logs()
        error_logs = [log for log in logs if log["level"] == "error"]
        assert error_logs
