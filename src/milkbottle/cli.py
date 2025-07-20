"""Main CLI for MilkBottle with Phase 5 integration."""

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import get_config
from .deployment.cli import deployment
from .performance.optimizer import (
    cache_manager,
    performance_monitor_instance,
    resource_optimizer,
)
from .plugin_marketplace.cli import marketplace
from .plugin_sdk import PluginSDK

console = Console()


@click.group()
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--debug", is_flag=True, help="Debug mode")
def cli(config: Optional[str], verbose: bool, debug: bool):
    """MilkBottle - Modular CLI Toolbox with Advanced Features."""
    # Initialize configuration
    config_path = Path(config) if config else None
    milk_config = get_config(config_file=str(config_path) if config_path else None)

    # Set up logging based on verbosity
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        import logging

        logging.basicConfig(level=logging.INFO)

    # Store config in context
    click.get_current_context().obj = {
        "config": milk_config,
        "verbose": verbose,
        "debug": debug,
    }


@cli.group()
def sdk():
    """Plugin SDK commands."""
    pass


@sdk.command()
@click.argument("name")
@click.option("--template", "-t", default="basic", help="Template to use")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory")
@click.option("--author", help="Author name")
@click.option("--email", help="Author email")
@click.option("--description", help="Plugin description")
@click.option("--version", default="1.0.0", help="Plugin version")
@click.option("--license", default="MIT", help="License")
def create(name: str, template: str, output_dir: Optional[str], **kwargs):
    """Create a new plugin."""

    async def _create():
        sdk = PluginSDK()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Creating plugin {name}...", total=None)

            output_path = Path(output_dir) if output_dir else None
            success = sdk.create_plugin(name, template, output_path, **kwargs)

            if success:
                console.print(f"✅ Successfully created plugin: {name}")
                if output_path:
                    console.print(f"📁 Plugin location: {output_path}")
            else:
                console.print(f"❌ Failed to create plugin: {name}")

    asyncio.run(_create())


@sdk.command()
@click.argument("plugin_path", type=click.Path(exists=True))
def validate(plugin_path: str):
    """Validate a plugin."""

    async def _validate():
        sdk = PluginSDK()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Validating plugin...", total=None)

            result = sdk.validate_plugin(Path(plugin_path))

            if result.get("valid", False):
                console.print("✅ Plugin validation passed")

                if result.get("warnings"):
                    console.print("\n⚠️  Warnings:")
                    for warning in result["warnings"]:
                        console.print(f"  - {warning}")
            else:
                console.print("❌ Plugin validation failed")

                if result.get("errors"):
                    console.print("\n❌ Errors:")
                    for error in result["errors"]:
                        console.print(f"  - {error}")

    asyncio.run(_validate())


@sdk.command()
@click.argument("plugin_path", type=click.Path(exists=True))
def test(plugin_path: str):
    """Test a plugin."""

    async def _test():
        sdk = PluginSDK()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Testing plugin...", total=None)

            result = sdk.test_plugin(Path(plugin_path))

            if result.get("success", False):
                console.print("✅ Plugin tests passed")

                if result.get("coverage"):
                    console.print(f"📊 Test coverage: {result['coverage']:.1f}%")
            else:
                console.print("❌ Plugin tests failed")

                if result.get("errors"):
                    console.print("\n❌ Test errors:")
                    for error in result["errors"]:
                        console.print(f"  - {error}")

    asyncio.run(_test())


@sdk.command()
@click.argument("plugin_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output path for package")
def package(plugin_path: str, output: Optional[str]):
    """Package a plugin for distribution."""

    async def _package():
        sdk = PluginSDK()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Packaging plugin...", total=None)

            output_path = Path(output) if output else None
            success = sdk.package_plugin(Path(plugin_path), output_path)

            if success:
                console.print("✅ Plugin packaged successfully")
                if output_path:
                    console.print(f"📦 Package location: {output_path}")
            else:
                console.print("❌ Failed to package plugin")

    asyncio.run(_package())


@sdk.command()
def templates():
    """List available plugin templates."""

    async def _templates():
        sdk = PluginSDK()

        templates = sdk.list_templates()

        if templates:
            table = Table(title="Available Plugin Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Type", style="yellow")

            for template in templates:
                table.add_row(
                    template.get("name", ""),
                    template.get("description", ""),
                    template.get("type", ""),
                )

            console.print(table)
        else:
            console.print("No templates available")

    asyncio.run(_templates())


@cli.group()
def performance():
    """Performance optimization commands."""
    pass


@performance.command()
@click.option("--interval", "-i", default=60, help="Monitoring interval in seconds")
def start_monitoring(interval: int):
    """Start performance monitoring."""

    async def _start_monitoring():
        success = await performance_monitor_instance.start_monitoring(interval)

        if success:
            console.print("✅ Performance monitoring started")
            console.print(f"⏱️  Monitoring interval: {interval} seconds")
        else:
            console.print("❌ Failed to start performance monitoring")

    asyncio.run(_start_monitoring())


@performance.command()
def stop_monitoring():
    """Stop performance monitoring."""

    async def _stop_monitoring():
        await performance_monitor_instance.stop_monitoring()
        console.print("✅ Performance monitoring stopped")

    asyncio.run(_stop_monitoring())


@performance.command()
def metrics():
    """Show current performance metrics."""

    async def _metrics():
        metrics = await performance_monitor_instance.collect_system_metrics()

        table = Table(title="Current Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("CPU Usage", f"{metrics.cpu_usage:.1f}%")
        table.add_row("Memory Usage", f"{metrics.memory_usage:.1f}%")
        table.add_row("Response Time", f"{metrics.response_time:.3f}s")
        table.add_row("Throughput", f"{metrics.throughput:.2f} ops/s")

        console.print(table)

    asyncio.run(_metrics())


@performance.command()
def report():
    """Generate performance report."""

    async def _report():
        report = performance_monitor_instance.get_performance_report()

        if "error" in report:
            console.print(f"❌ {report['error']}")
            return

        table = Table(title="Performance Report")
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("5min Avg", style="yellow")
        table.add_column("1hr Avg", style="blue")

        current = report["current"]
        avg_5min = report["average_5min"]
        avg_1hour = report["average_1hour"]

        table.add_row(
            "CPU Usage",
            f"{current['cpu_usage']:.1f}%",
            f"{avg_5min['cpu_usage']:.1f}%",
            f"{avg_1hour['cpu_usage']:.1f}%",
        )
        table.add_row(
            "Memory Usage",
            f"{current['memory_usage']:.1f}%",
            f"{avg_5min['memory_usage']:.1f}%",
            f"{avg_1hour['memory_usage']:.1f}%",
        )
        table.add_row(
            "Response Time",
            f"{current['response_time']:.3f}s",
            f"{avg_5min['response_time']:.3f}s",
            f"{avg_1hour['response_time']:.3f}s",
        )

        console.print(table)

    asyncio.run(_report())


@performance.command()
def optimize_memory():
    """Optimize memory usage."""

    async def _optimize_memory():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Optimizing memory...", total=None)

            result = await resource_optimizer.optimize_memory()

            if result["success"]:
                console.print("✅ Memory optimization completed")
                console.print(f"💾 Freed memory: {result['freed_memory_mb']:.2f} MB")
                console.print(
                    f"📊 Memory usage before: {result['memory_usage_before']:.1f}%"
                )
                console.print(
                    f"📊 Memory usage after: {result['memory_usage_after']:.1f}%"
                )
            else:
                console.print(f"❌ Memory optimization failed: {result['error']}")

    asyncio.run(_optimize_memory())


@performance.command()
@click.argument("path", type=click.Path(exists=True))
def optimize_disk(path: str):
    """Optimize disk usage for a directory."""

    async def _optimize_disk():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Optimizing disk usage...", total=None)

            result = await resource_optimizer.optimize_disk_usage(Path(path))

            if result["success"]:
                console.print("✅ Disk optimization completed")
                console.print(f"💾 Freed space: {result['freed_space_mb']:.2f} MB")
                console.print(f"🗑️  Temp files removed: {result['temp_files_removed']}")
                console.print(f"📊 Usage before: {result['usage_before_mb']:.2f} MB")
                console.print(f"📊 Usage after: {result['usage_after_mb']:.2f} MB")
            else:
                console.print(f"❌ Disk optimization failed: {result['error']}")

    asyncio.run(_optimize_disk())


@performance.command()
def cache_stats():
    """Show cache statistics."""
    stats = cache_manager.get_stats()

    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cache Size", str(stats["size"]))
    table.add_row("Max Size", str(stats["max_size"]))
    table.add_row("Hit Rate", f"{stats['hit_rate']:.2%}")
    table.add_row("Memory Usage", f"{stats['memory_usage'] / 1024:.2f} KB")

    console.print(table)


@performance.command()
def clear_cache():
    """Clear the cache."""
    cache_manager.clear()
    console.print("✅ Cache cleared")


@cli.command()
def status():
    """Show MilkBottle system status."""

    async def _status():
        # Get context
        ctx = click.get_current_context()
        config = ctx.obj["config"]

        table = Table(title="MilkBottle System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        # Check deployment system
        try:
            from .deployment import DeploymentManager

            _ = DeploymentManager(config)
            table.add_row("Deployment System", "✅ Active", "Ready for deployment")
        except Exception as e:
            table.add_row("Deployment System", "❌ Error", str(e))

        # Check marketplace system
        try:
            from .plugin_marketplace import MarketplaceManager

            _ = MarketplaceManager(config)
            table.add_row(
                "Plugin Marketplace", "✅ Active", "Ready for plugin management"
            )
        except Exception as e:
            table.add_row("Plugin Marketplace", "❌ Error", str(e))

        # Check plugin SDK
        try:
            _ = PluginSDK()
            table.add_row("Plugin SDK", "✅ Active", "Ready for plugin development")
        except Exception as e:
            table.add_row("Plugin SDK", "❌ Error", str(e))

        # Check performance system
        try:
            metrics = await performance_monitor_instance.collect_system_metrics()
            table.add_row(
                "Performance System", "✅ Active", f"CPU: {metrics.cpu_usage:.1f}%"
            )
        except Exception as e:
            table.add_row("Performance System", "❌ Error", str(e))

        # Check cache
        cache_stats = cache_manager.get_stats()
        table.add_row("Cache System", "✅ Active", f"Size: {cache_stats['size']}")

        console.print(table)

    asyncio.run(_status())


@cli.command()
def version():
    """Show MilkBottle version."""
    from . import __version__

    console.print(f"MilkBottle v{__version__}")


# Add subcommands
cli.add_command(deployment)
cli.add_command(marketplace)


if __name__ == "__main__":
    cli()
