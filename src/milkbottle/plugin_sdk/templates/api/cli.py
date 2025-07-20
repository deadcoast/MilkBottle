"""CLI interface for {{ plugin_name }}."""

import click
import json
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    """{{ description }}"""
    pass

@cli.command()
@click.option("--format", "-f", default="json", help="Output format")
def info(format: str):
    """Get API information."""
    from . import plugin_instance
    
    metadata = plugin_instance.get_metadata()
    
    if format == "json":
        console.print(json.dumps(metadata.__dict__, indent=2))
    else:
        table = Table(title="API Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        for key, value in metadata.__dict__.items():
            table.add_row(key, str(value))
        
        console.print(table)

@cli.command()
def routes():
    """List API routes."""
    from . import plugin_instance
    
    table = Table(title="API Routes")
    table.add_column("Route", style="cyan")
    table.add_column("Description", style="magenta")
    
    for route, handler in plugin_instance.api_routes.items():
        table.add_row(route, handler.__name__)
    
    console.print(table)

if __name__ == "__main__":
    cli()
