"""CLI interface for {{ plugin_name }}."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group()
def cli():
    """{{ description }}"""
    pass

@cli.command()
@click.option("--host", default="localhost", help="Server host")
@click.option("--port", default=8080, help="Server port")
def serve(host: str, port: int):
    """Start the web server."""
    from . import plugin_instance
    
    console.print(f"Starting server on {host}:{port}")
    # Server logic would go here

@cli.command()
def status():
    """Show plugin status."""
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    console.print(f"Plugin: {metadata.name}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Status: {health['status']}")
    console.print(f"Server Running: {health['server_running']}")

if __name__ == "__main__":
    cli()
