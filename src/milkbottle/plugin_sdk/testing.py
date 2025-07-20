"""Plugin testing framework for MilkBottle Plugin SDK.

This module provides comprehensive testing capabilities for plugins including
unit tests, integration tests, and performance tests.
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger("milkbottle.plugin_sdk.testing")


class PluginTester:
    """Plugin testing system."""

    def __init__(self):
        """Initialize the plugin tester."""
        self.console = Console()

    def test_plugin(self, plugin_path: Path, test_type: str = "all") -> Dict[str, Any]:
        """Run tests for a plugin.

        Args:
            plugin_path: Path to plugin directory
            test_type: Type of tests to run (unit, integration, all)

        Returns:
            Test results
        """
        results = {
            "success": False,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "coverage": 0.0,
            "duration": 0.0,
            "errors": [],
            "warnings": [],
            "details": {},
        }

        try:
            start_time = time.time()

            # Run different types of tests
            if test_type in ["all", "unit"]:
                unit_results = self._run_unit_tests(plugin_path)
                self._extracted_from_test_plugin_30(unit_results, results, "unit")
            if test_type in ["all", "integration"]:
                integration_results = self._run_integration_tests(plugin_path)
                self._extracted_from_test_plugin_30(
                    integration_results, results, "integration"
                )
            if test_type in ["all", "performance"]:
                performance_results = self._run_performance_tests(plugin_path)
                results["details"]["performance"] = performance_results

            # Calculate coverage
            if test_type in ["all", "coverage"]:
                coverage_results = self._run_coverage_tests(plugin_path)
                results["coverage"] = coverage_results.get("coverage", 0.0)
                results["details"]["coverage"] = coverage_results

            # Calculate duration
            results["duration"] = time.time() - start_time

            # Determine overall success
            results["success"] = (
                results["tests_failed"] == 0
                and results["tests_run"] > 0
                and results["coverage"] >= 80.0  # 80% coverage threshold
            )

        except Exception as e:
            logger.error(f"Testing failed: {e}")
            results["errors"].append(f"Testing failed: {e}")

        return results

    # TODO Rename this here and in `test_plugin`
    def _extracted_from_test_plugin_30(self, arg0, results, arg2):
        results["details"][arg2] = arg0
        results["tests_run"] += arg0.get("tests_run", 0)
        results["tests_passed"] += arg0.get("tests_passed", 0)
        results["tests_failed"] += arg0.get("tests_failed", 0)
        results["tests_skipped"] += arg0.get("tests_skipped", 0)

    def _run_unit_tests(self, plugin_path: Path) -> Dict[str, Any]:
        """Run unit tests for the plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Unit test results
        """
        results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "errors": [],
            "output": "",
        }

        try:
            # Find test files
            if not (test_files := list(plugin_path.rglob("test_*.py"))):
                results["errors"].append("No test files found")
                return results

            # Run pytest
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Running unit tests...", total=None)

                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--tb=short",
                    "--quiet",
                    "--json-report",
                    "--json-report-file=none",
                    *[str(f) for f in test_files],
                ]

                # Run tests
                process = subprocess.run(
                    cmd,
                    cwd=plugin_path,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                progress.update(task, description="Unit tests complete")

            # Parse results
            results["output"] = process.stdout + process.stderr
            results["return_code"] = process.returncode

            # Parse pytest output for test counts
            if process.stdout:
                lines = process.stdout.splitlines()
                for line in lines:
                    if "passed" in line and "failed" in line:
                        # Extract test counts from pytest output
                        import re

                        passed_match = re.search(r"(\d+) passed", line)
                        failed_match = re.search(r"(\d+) failed", line)
                        skipped_match = re.search(r"(\d+) skipped", line)

                        if passed_match:
                            results["tests_passed"] = int(passed_match.group(1))
                        if failed_match:
                            results["tests_failed"] = int(failed_match.group(1))
                        if skipped_match:
                            results["tests_skipped"] = int(skipped_match.group(1))

                        results["tests_run"] = (
                            results["tests_passed"]
                            + results["tests_failed"]
                            + results["tests_skipped"]
                        )
                        break

            if process.returncode != 0:
                results["errors"].append(
                    f"Unit tests failed with return code {process.returncode}"
                )

        except subprocess.TimeoutExpired:
            results["errors"].append("Unit tests timed out")
        except Exception as e:
            results["errors"].append(f"Unit test execution failed: {e}")

        return results

    def _run_integration_tests(self, plugin_path: Path) -> Dict[str, Any]:
        """Run integration tests for the plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Integration test results
        """
        results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "errors": [],
            "output": "",
        }

        try:
            # Find integration test files
            integration_test_files = list(
                plugin_path.rglob("*integration*.py")
            ) or list(plugin_path.rglob("test_integration*.py"))

            if not integration_test_files:
                results["warnings"] = ["No integration test files found"]
                return results

            # Run integration tests
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Running integration tests...", total=None)

                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--tb=short",
                    "--quiet",
                    "--json-report",
                    "--json-report-file=none",
                    *[str(f) for f in integration_test_files],
                ]

                # Run tests
                process = subprocess.run(
                    cmd,
                    cwd=plugin_path,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minute timeout for integration tests
                )

                progress.update(task, description="Integration tests complete")

            # Parse results (similar to unit tests)
            results["output"] = process.stdout + process.stderr
            results["return_code"] = process.returncode

            if process.stdout:
                lines = process.stdout.splitlines()
                for line in lines:
                    if "passed" in line and "failed" in line:
                        import re

                        passed_match = re.search(r"(\d+) passed", line)
                        failed_match = re.search(r"(\d+) failed", line)
                        skipped_match = re.search(r"(\d+) skipped", line)

                        if passed_match:
                            results["tests_passed"] = int(passed_match.group(1))
                        if failed_match:
                            results["tests_failed"] = int(failed_match.group(1))
                        if skipped_match:
                            results["tests_skipped"] = int(skipped_match.group(1))

                        results["tests_run"] = (
                            results["tests_passed"]
                            + results["tests_failed"]
                            + results["tests_skipped"]
                        )
                        break

            if process.returncode != 0:
                results["errors"].append(
                    f"Integration tests failed with return code {process.returncode}"
                )

        except subprocess.TimeoutExpired:
            results["errors"].append("Integration tests timed out")
        except Exception as e:
            results["errors"].append(f"Integration test execution failed: {e}")

        return results

    def _run_performance_tests(self, plugin_path: Path) -> Dict[str, Any]:
        """Run performance tests for the plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Performance test results
        """
        results = {"benchmarks": {}, "errors": [], "warnings": []}

        try:
            # Find performance test files
            perf_test_files = list(plugin_path.rglob("*perf*.py")) or list(
                plugin_path.rglob("test_performance*.py")
            )

            if not perf_test_files:
                results["warnings"].append("No performance test files found")
                return results

            # Run performance tests
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Running performance tests...", total=None)

                for perf_file in perf_test_files:
                    try:
                        # Run individual performance test file
                        process = subprocess.run(
                            [sys.executable, str(perf_file)],
                            cwd=plugin_path,
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )

                        # Parse performance results
                        if process.stdout:
                            # Extract benchmark results from output
                            import re

                            benchmark_pattern = r"(\w+):\s*([\d.]+)\s*(\w+)"
                            matches = re.findall(benchmark_pattern, process.stdout)

                            for match in matches:
                                metric_name, value, unit = match
                                results["benchmarks"][metric_name] = {
                                    "value": float(value),
                                    "unit": unit,
                                }

                        if process.returncode != 0:
                            results["errors"].append(
                                f"Performance test failed: {perf_file.name}"
                            )

                    except subprocess.TimeoutExpired:
                        results["errors"].append(
                            f"Performance test timed out: {perf_file.name}"
                        )
                    except Exception as e:
                        results["errors"].append(
                            f"Performance test failed: {perf_file.name} - {e}"
                        )

                progress.update(task, description="Performance tests complete")

        except Exception as e:
            results["errors"].append(f"Performance test execution failed: {e}")

        return results

    def _run_coverage_tests(self, plugin_path: Path) -> Dict[str, Any]:
        """Run coverage tests for the plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Coverage test results
        """
        results = {
            "coverage": 0.0,
            "lines_covered": 0,
            "lines_total": 0,
            "errors": [],
            "output": "",
        }

        try:
            # Check if coverage is available
            if importlib.util.find_spec("coverage") is None:
                results["errors"].append("Coverage package not available")
                return results

            # Run coverage
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Running coverage tests...", total=None)

                cmd = [
                    sys.executable,
                    "-m",
                    "coverage",
                    "run",
                    "--source=.",
                    "-m",
                    "pytest",
                ]

                # Find test files
                if test_files := list(plugin_path.rglob("test_*.py")):
                    cmd.extend([str(f) for f in test_files])

                # Run coverage
                process = subprocess.run(
                    cmd, cwd=plugin_path, capture_output=True, text=True, timeout=300
                )

                # Generate coverage report
                report_process = subprocess.run(
                    [sys.executable, "-m", "coverage", "report"],
                    cwd=plugin_path,
                    capture_output=True,
                    text=True,
                )

                progress.update(task, description="Coverage tests complete")

            # Parse coverage results
            results["output"] = report_process.stdout + report_process.stderr

            if report_process.stdout:
                lines = report_process.stdout.splitlines()
                for line in lines:
                    if "TOTAL" in line:
                        # Extract coverage percentage
                        import re

                        if coverage_match := re.search(r"(\d+)%", line):
                            results["coverage"] = float(coverage_match.group(1))

                        # Extract line counts
                        if line_match := re.search(r"(\d+)\s+(\d+)", line):
                            results["lines_covered"] = int(line_match.group(1))
                            results["lines_total"] = int(line_match.group(2))
                        break

            if process.returncode != 0:
                results["errors"].append(
                    f"Coverage tests failed with return code {process.returncode}"
                )

        except subprocess.TimeoutExpired:
            results["errors"].append("Coverage tests timed out")
        except Exception as e:
            results["errors"].append(f"Coverage test execution failed: {e}")

        return results

    def create_test_template(self, plugin_path: Path, test_type: str = "unit") -> bool:
        """Create test template for the plugin.

        Args:
            plugin_path: Path to plugin directory
            test_type: Type of test template to create

        Returns:
            True if creation successful, False otherwise
        """
        try:
            tests_dir = plugin_path / "tests"
            tests_dir.mkdir(exist_ok=True)

            if test_type == "unit":
                return self._create_unit_test_template(plugin_path, tests_dir)
            elif test_type == "integration":
                return self._create_integration_test_template(plugin_path, tests_dir)
            elif test_type == "performance":
                return self._create_performance_test_template(plugin_path, tests_dir)
            else:
                self.console.print(f"[red]Unknown test type: {test_type}[/red]")
                return False

        except Exception as e:
            logger.error(f"Failed to create test template: {e}")
            return False

    def _create_unit_test_template(self, plugin_path: Path, tests_dir: Path) -> bool:
        """Create unit test template.

        Args:
            plugin_path: Path to plugin directory
            tests_dir: Tests directory

        Returns:
            True if creation successful, False otherwise
        """
        try:
            # Get plugin name from path
            plugin_name = plugin_path.name

            # Create test file
            test_file = tests_dir / f"test_{plugin_name}.py"

            test_content = f'''"""Unit tests for {plugin_name} plugin."""

import pytest
from pathlib import Path

from {plugin_name} import get_plugin_interface, get_cli, get_metadata

class Test{plugin_name.title()}:
    """Test {plugin_name} plugin."""

    def test_plugin_creation(self):
        """Test creating the plugin."""
        plugin = get_plugin_interface()
        assert plugin is not None

    def test_plugin_metadata(self):
        """Test plugin metadata."""
        metadata = get_metadata()
        assert metadata is not None
        assert hasattr(metadata, 'name')
        assert hasattr(metadata, 'version')
        assert hasattr(metadata, 'description')

    def test_cli_interface(self):
        """Test CLI interface."""
        cli = get_cli()
        assert cli is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = get_plugin_interface()
        success = await plugin.initialize()
        assert success is True

    def test_health_check(self):
        """Test health check."""
        plugin = get_plugin_interface()
        health = plugin.health_check()
        assert "status" in health
        assert "version" in health

    def test_config_validation(self):
        """Test configuration validation."""
        plugin = get_plugin_interface()
        # Test with valid config
        valid_config = {{}}
        assert plugin.validate_config(valid_config) is True

    def test_capabilities(self):
        """Test plugin capabilities."""
        plugin = get_plugin_interface()
        capabilities = plugin.get_capabilities()
        assert isinstance(capabilities, list)

    def test_dependencies(self):
        """Test plugin dependencies."""
        plugin = get_plugin_interface()
        dependencies = plugin.get_dependencies()
        assert isinstance(dependencies, list)

    def test_config_schema(self):
        """Test configuration schema."""
        plugin = get_plugin_interface()
        schema = plugin.get_config_schema()
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"
'''

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            self.console.print(
                f"[green]Created unit test template: {test_file}[/green]"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create unit test template: {e}")
            return False

    def _create_integration_test_template(
        self, plugin_path: Path, tests_dir: Path
    ) -> bool:
        """Create integration test template.

        Args:
            plugin_path: Path to plugin directory
            tests_dir: Tests directory

        Returns:
            True if creation successful, False otherwise
        """
        try:
            plugin_name = plugin_path.name
            test_file = tests_dir / f"test_{plugin_name}_integration.py"

            test_content = f'''"""Integration tests for {plugin_name} plugin."""

import pytest
from pathlib import Path

from {plugin_name} import get_plugin_interface

class Test{plugin_name.title()}Integration:
    """Integration tests for {plugin_name} plugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin fixture."""
        plugin = get_plugin_interface()
        return plugin

    @pytest.mark.asyncio
    async def test_full_plugin_lifecycle(self):
        """Test complete plugin lifecycle."""
        plugin = get_plugin_interface()
        
        # Initialize
        success = await plugin.initialize()
        assert success is True
        
        # Health check
        health = plugin.health_check()
        assert health["status"] == "healthy"
        
        # Shutdown
        await plugin.shutdown()

    def test_cli_integration(self):
        """Test CLI integration."""
        from {plugin_name}.cli import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Test help
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        
        # Test status command if available
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_config_integration(self):
        """Test configuration integration."""
        plugin = get_plugin_interface()
        
        # Test with various configs
        test_configs = [
            {{}},
            {{"test": "value"}},
            {{"nested": {{"key": "value"}}}}
        ]
        
        for config in test_configs:
            assert plugin.validate_config(config) is True
'''

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            self.console.print(
                f"[green]Created integration test template: {test_file}[/green]"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create integration test template: {e}")
            return False

    def _create_performance_test_template(
        self, plugin_path: Path, tests_dir: Path
    ) -> bool:
        """Create performance test template.

        Args:
            plugin_path: Path to plugin directory
            tests_dir: Tests directory

        Returns:
            True if creation successful, False otherwise
        """
        try:
            plugin_name = plugin_path.name
            test_file = tests_dir / f"test_{plugin_name}_performance.py"

            test_content = f'''"""Performance tests for {plugin_name} plugin."""

import time
import pytest
from pathlib import Path

from {plugin_name} import get_plugin_interface

class Test{plugin_name.title()}Performance:
    """Performance tests for {plugin_name} plugin."""

    def test_initialization_performance(self):
        """Test plugin initialization performance."""
        start_time = time.time()
        
        plugin = get_plugin_interface()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should initialize quickly (< 1 second)
        assert duration < 1.0, f"Initialization took {{duration:.3f}}s, expected < 1.0s"
        print(f"Initialization time: {{duration:.3f}}s")

    def test_health_check_performance(self):
        """Test health check performance."""
        plugin = get_plugin_interface()
        
        start_time = time.time()
        health = plugin.health_check()
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should be very fast (< 100ms)
        assert duration < 0.1, f"Health check took {{duration:.3f}}s, expected < 0.1s"
        print(f"Health check time: {{duration:.3f}}s")

    def test_config_validation_performance(self):
        """Test configuration validation performance."""
        plugin = get_plugin_interface()
        
        # Test with large config
        large_config = {{}}
        for i in range(1000):
            large_config[f"key_{{i}}"] = f"value_{{i}}"
        
        start_time = time.time()
        result = plugin.validate_config(large_config)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should handle large configs efficiently (< 500ms)
        assert duration < 0.5, f"Config validation took {{duration:.3f}}s, expected < 0.5s"
        print(f"Config validation time: {{duration:.3f}}s")

    def test_memory_usage(self):
        """Test memory usage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple plugin instances
        plugins = []
        for i in range(10):
            plugin = get_plugin_interface()
            plugins.append(plugin)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not use excessive memory (< 50MB increase for 10 instances)
        assert memory_increase < 50, f"Memory increase: {{memory_increase:.1f}}MB, expected < 50MB"
        print(f"Memory usage increase: {{memory_increase:.1f}}MB")
'''

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            self.console.print(
                f"[green]Created performance test template: {test_file}[/green]"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create performance test template: {e}")
            return False

    def print_test_report(self, results: Dict[str, Any]) -> None:
        """Print test report.

        Args:
            results: Test results
        """
        # Overall status
        status_color = "green" if results["success"] else "red"
        self.console.print(
            f"\n[bold {status_color}]Test Status: {'PASS' if results['success'] else 'FAIL'}[/bold {status_color}]"
        )

        # Summary
        self.console.print(f"Tests Run: {results['tests_run']}")
        self.console.print(f"Tests Passed: {results['tests_passed']}")
        self.console.print(f"Tests Failed: {results['tests_failed']}")
        self.console.print(f"Tests Skipped: {results['tests_skipped']}")
        self.console.print(f"Coverage: {results['coverage']:.1f}%")
        self.console.print(f"Duration: {results['duration']:.2f}s")

        # Errors
        if results["errors"]:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                self.console.print(f"  ❌ {error}")

        # Warnings
        if results["warnings"]:
            self.console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in results["warnings"]:
                self.console.print(f"  ⚠️  {warning}")

        # Detailed results
        if results["details"]:
            self._extracted_from_print_test_report_35(results)

    # TODO Rename this here and in `print_test_report`
    def _extracted_from_print_test_report_35(self, results):
        self.console.print("\n[bold blue]Detailed Results:[/bold blue]")

        table = Table()
        table.add_column("Test Type", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Tests", style="green")
        table.add_column("Coverage", style="yellow")

        for test_type, test_results in results["details"].items():
            if isinstance(test_results, dict):
                tests_run = test_results.get("tests_run", 0)
                tests_passed = test_results.get("tests_passed", 0)
                tests_failed = test_results.get("tests_failed", 0)

                status = "PASS" if tests_failed == 0 and tests_run > 0 else "FAIL"
                status_style = "green" if tests_failed == 0 and tests_run > 0 else "red"

                coverage = (
                    test_results.get("coverage", 0.0)
                    if "coverage" in test_results
                    else "N/A"
                )

                table.add_row(
                    test_type.title(),
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{tests_passed}/{tests_run}",
                    (
                        f"{coverage:.1f}%"
                        if isinstance(coverage, float)
                        else str(coverage)
                    ),
                )

        self.console.print(table)
