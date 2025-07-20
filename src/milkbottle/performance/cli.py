"""CLI interface for MilkBottle Performance Optimization System."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import (
    clear_cache,
    get_cache_stats,
    get_performance_report,
    optimize_io,
    optimize_memory,
    parallel_execute,
    profile_function,
    start_monitoring,
    stop_monitoring,
)

console = Console()
logger = logging.getLogger("milkbottle.performance.cli")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--log-level", default="INFO", help="Logging level")
def cli(verbose: bool, log_level: str):
    """MilkBottle Performance Optimization CLI."""
    if verbose:
        logging.basicConfig(level=getattr(logging, log_level.upper()))

    console.print(
        Panel.fit(
            "[bold blue]MilkBottle Performance Optimization System[/bold blue]\n"
            "Advanced performance monitoring, optimization, and profiling tools",
            border_style="blue",
        )
    )


@cli.command()
@click.option("--duration", "-d", default=60, help="Monitoring duration in seconds")
@click.option(
    "--interval", "-i", default=1, help="Metrics collection interval in seconds"
)
@click.option("--output", "-o", help="Output file for monitoring data")
def monitor(duration: int, interval: int, output: Optional[str]):
    """Start performance monitoring."""
    console.print(
        f"[bold green]Starting performance monitoring for {duration} seconds...[/bold green]"
    )

    try:
        start_monitoring()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Monitoring...", total=duration)

            for i in range(duration):
                time.sleep(interval)
                progress.update(task, completed=i + 1)

        stop_monitoring()

        # Get and display report
        report = get_performance_report()

        if output:
            with open(output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]Monitoring data saved to {output}[/green]")

        display_performance_report(report)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        stop_monitoring()
    except Exception as e:
        console.print(f"[red]Monitoring failed: {e}[/red]")
        logger.error(f"Monitoring failed: {e}")


@cli.command()
@click.option("--memory", is_flag=True, help="Optimize memory usage")
@click.option("--io", is_flag=True, help="Optimize I/O operations")
@click.option("--cache", is_flag=True, help="Optimize cache")
@click.option("--all", is_flag=True, help="Run all optimizations")
def optimize(memory: bool, io: bool, cache: bool, all: bool):
    """Run performance optimizations."""
    if all:
        memory = io = cache = True

    if not any([memory, io, cache]):
        memory = io = cache = True  # Default to all

    console.print("[bold green]Running performance optimizations...[/bold green]")

    try:
        results = {}

        if memory:
            console.print("[blue]Optimizing memory...[/blue]")
            results["memory"] = optimize_memory()

        if io:
            console.print("[blue]Optimizing I/O...[/blue]")
            results["io"] = optimize_io()

        if cache:
            console.print("[blue]Optimizing cache...[/blue]")
            clear_cache()
            results["cache"] = get_cache_stats()

        display_optimization_results(results)

    except Exception as e:
        console.print(f"[red]Optimization failed: {e}[/red]")
        logger.error(f"Optimization failed: {e}")


@cli.command()
@click.argument("function_name")
@click.option("--args", help="Function arguments (JSON format)")
@click.option("--iterations", "-n", default=1, help="Number of iterations to profile")
def profile(function_name: str, args: Optional[str], iterations: int):
    """Profile a function's performance."""
    console.print(f"[bold green]Profiling function: {function_name}[/bold green]")

    try:
        # Parse function arguments
        function_args = []
        function_kwargs = {}

        if args:
            try:
                parsed_args = json.loads(args)
                if isinstance(parsed_args, list):
                    function_args = parsed_args
                elif isinstance(parsed_args, dict):
                    function_kwargs = parsed_args
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON format for arguments[/red]")
                return

        # Import and profile function
        import importlib

        module_name, func_name = function_name.rsplit(".", 1)

        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            console.print(f"[red]Could not import function {function_name}: {e}[/red]")
            return

        # Profile function
        results = []
        for _ in range(iterations):
            result = profile_function(func, *function_args, **function_kwargs)
            results.append(result)

        display_profiling_results(results)

    except Exception as e:
        console.print(f"[red]Profiling failed: {e}[/red]")
        logger.error(f"Profiling failed: {e}")


@cli.command()
@click.argument("function_name")
@click.option("--args", help="Function arguments (JSON format)")
@click.option("--items", help="Items to process (JSON format)")
@click.option("--workers", "-w", default=4, help="Number of worker processes")
def parallel(
    function_name: str, args: Optional[str], items: Optional[str], workers: int
):
    """Execute function in parallel."""
    console.print(
        f"[bold green]Executing {function_name} in parallel with {workers} workers[/bold green]"
    )

    try:
        # Parse arguments
        function_args = []
        function_kwargs = {}

        if args:
            try:
                parsed_args = json.loads(args)
                if isinstance(parsed_args, list):
                    function_args = parsed_args
                elif isinstance(parsed_args, dict):
                    function_kwargs = parsed_args
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON format for arguments[/red]")
                return

        # Parse items
        if not items:
            console.print("[red]Items must be provided[/red]")
            return

        try:
            items_list = json.loads(items)
            if not isinstance(items_list, list):
                console.print("[red]Items must be a list[/red]")
                return
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON format for items[/red]")
            return

        # Import function
        import importlib

        module_name, func_name = function_name.rsplit(".", 1)

        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            console.print(f"[red]Could not import function {function_name}: {e}[/red]")
            return

        # Execute in parallel
        results = parallel_execute(func, items_list, max_workers=workers)

        display_parallel_results(results)

    except Exception as e:
        console.print(f"[red]Parallel execution failed: {e}[/red]")
        logger.error(f"Parallel execution failed: {e}")


@cli.command()
def report():
    """Generate performance report."""
    console.print("[bold green]Generating performance report...[/bold green]")

    try:
        report = get_performance_report()
        display_performance_report(report)

    except Exception as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        logger.error(f"Report generation failed: {e}")


@cli.command()
@click.option("--output", "-o", help="Output file for report")
def export(output: Optional[str]):
    """Export performance data."""
    console.print("[bold green]Exporting performance data...[/bold green]")

    try:
        report = get_performance_report()

        if output:
            with open(output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]Performance data exported to {output}[/green]")
        else:
            console.print(json.dumps(report, indent=2, default=str))

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        logger.error(f"Export failed: {e}")


@cli.command()
def clear():
    """Clear all performance data and caches."""
    console.print(
        "[bold yellow]Clearing all performance data and caches...[/bold yellow]"
    )

    try:
        clear_cache()
        console.print("[green]Performance data cleared successfully[/green]")

    except Exception as e:
        console.print(f"[red]Clear operation failed: {e}[/red]")
        logger.error(f"Clear operation failed: {e}")


def display_performance_report(report: Dict[str, Any]):
    """Display performance report in a formatted table."""
    console.print("\n[bold blue]Performance Report[/bold blue]")

    # Cache Statistics
    if "cache_stats" in report:
        cache_table = _extracted_from_display_performance_report_7(
            "Cache Statistics", "Metric", "Value"
        )
        cache_stats = report["cache_stats"]
        for key, value in cache_stats.items():
            cache_table.add_row(key, str(value))

        console.print(cache_table)

    # Performance Metrics
    if "performance_metrics" in report:
        metrics_table = _extracted_from_display_performance_report_7(
            "Performance Metrics", "Metric", "Value"
        )
        metrics = report["performance_metrics"]
        for key, value in metrics.items():
            if isinstance(value, float):
                metrics_table.add_row(key, f"{value:.2f}")
            else:
                metrics_table.add_row(key, str(value))

        console.print(metrics_table)

    # Resource Usage
    if "resource_usage" in report:
        resource_table = _extracted_from_display_performance_report_7(
            "Resource Usage", "Resource", "Usage"
        )
        resource_table.add_column("Status", style="yellow")

        usage = report["resource_usage"]
        for resource, value in usage.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    status = (
                        "🟢" if sub_value < 80 else "🟡" if sub_value < 90 else "🔴"
                    )
                    resource_table.add_row(
                        f"{resource}.{sub_key}", f"{sub_value:.1f}%", status
                    )
            else:
                status = "🟢" if value < 80 else "🟡" if value < 90 else "🔴"
                resource_table.add_row(resource, f"{value:.1f}%", status)

        console.print(resource_table)


# TODO Rename this here and in `display_performance_report`
def _extracted_from_display_performance_report_7(title, arg1, arg2):
    result = Table(title=title)
    result.add_column(arg1, style="cyan")
    result.add_column(arg2, style="green")

    return result


def display_optimization_results(results: Dict[str, Any]):
    """Display optimization results."""
    console.print("\n[bold blue]Optimization Results[/bold blue]")

    for optimization_type, result in results.items():
        console.print(
            f"\n[bold cyan]{optimization_type.upper()} Optimization[/bold cyan]"
        )

        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict):
                    console.print(f"  [yellow]{key}:[/yellow]")
                    for sub_key, sub_value in value.items():
                        console.print(f"    {sub_key}: {sub_value}")
                else:
                    console.print(f"  [yellow]{key}:[/yellow] {value}")
        else:
            console.print(f"  {result}")


def display_profiling_results(results: List[Dict[str, Any]]):
    """Display profiling results."""
    console.print("\n[bold blue]Profiling Results[/bold blue]")

    if len(results) == 1:
        result = results[0]
        profile_table = Table(title="Function Profile")
        profile_table.add_column("Metric", style="cyan")
        profile_table.add_column("Value", style="green")

        profile_table.add_row("Function", result.get("function_name", "Unknown"))
        profile_table.add_row("Execution Time", f"{result.get('total_time', 0):.3f}s")
        profile_table.add_row("Memory Usage", f"{result.get('memory_usage', 0):.2f}MB")
        profile_table.add_row("CPU Usage", f"{result.get('cpu_percent', 0):.1f}%")

        console.print(profile_table)

        # Display suggestions if available
        if "suggestions" in result:
            console.print("\n[bold yellow]Optimization Suggestions:[/bold yellow]")
            for suggestion in result["suggestions"]:
                console.print(f"  • {suggestion}")
    else:
        # Multiple iterations
        summary_table = Table(title="Profiling Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        times = [r.get("total_time", 0) for r in results]
        memories = [r.get("memory_usage", 0) for r in results]

        summary_table.add_row("Iterations", str(len(results)))
        summary_table.add_row("Avg Execution Time", f"{sum(times)/len(times):.3f}s")
        summary_table.add_row("Min Execution Time", f"{min(times):.3f}s")
        summary_table.add_row("Max Execution Time", f"{max(times):.3f}s")
        summary_table.add_row(
            "Avg Memory Usage", f"{sum(memories)/len(memories):.2f}MB"
        )

        console.print(summary_table)


def display_parallel_results(results: List[Any]):
    """Display parallel execution results."""
    console.print("\n[bold blue]Parallel Execution Results[/bold blue]")

    results_table = Table(title="Results")
    results_table.add_column("Index", style="cyan")
    results_table.add_column("Result", style="green")
    results_table.add_column("Status", style="yellow")

    for i, result in enumerate(results):
        if result is None:
            results_table.add_row(str(i), "Error", "🔴")
        else:
            results_table.add_row(str(i), str(result), "🟢")

    console.print(results_table)

    # Summary
    total = len(results)
    successful = sum(bool(r is not None) for r in results)
    failed = total - successful

    console.print(
        f"\n[bold]Summary:[/bold] {successful}/{total} successful, {failed} failed"
    )


if __name__ == "__main__":
    cli()
