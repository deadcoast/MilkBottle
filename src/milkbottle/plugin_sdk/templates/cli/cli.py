"""CLI interface for {{ plugin_name }}."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group()
def cli():
    """{{ description }}"""
    pass

@cli.command()
@click.option("--name", "-n", help="Name parameter")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(name: str, verbose: bool):
    """Main command."""
    from . import plugin_instance
    
    if verbose:
        console.print(f"Running {{ plugin_name }} with name: {name}")
    
    # Your main logic here
    result = f"Hello, {name or 'World'}!"
    
    panel = Panel(
        result,
        title="{{ plugin_name }}",
        border_style="green"
    )
    console.print(panel)

@cli.command()
def status():
    """Show plugin status."""
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    table = Table(title="Plugin Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Name", metadata.name)
    table.add_row("Version", metadata.version)
    table.add_row("Status", health['status'])
    table.add_row("Details", health['details'])
    
    console.print(table)

@cli.command()
def config():
    """Show plugin configuration."""
    from . import plugin_instance
    
    if plugin_instance.config:
        table = Table(title="Plugin Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        for key, value in plugin_instance.config.items():
            table.add_row(key, str(value))
        
        console.print(table)
    else:
        console.print("No configuration loaded")

if __name__ == "__main__":
    cli()
