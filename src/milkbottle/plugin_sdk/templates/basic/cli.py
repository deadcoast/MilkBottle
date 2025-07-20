"""CLI interface for {{ plugin_name }}."""

import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    """{{ description }}"""
    pass

@cli.command()
def status():
    """Show plugin status."""
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    console.print(f"Plugin: {metadata.name}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Status: {health['status']}")

if __name__ == "__main__":
    cli()
