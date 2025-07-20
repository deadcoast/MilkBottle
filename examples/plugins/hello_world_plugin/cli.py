"""CLI interface for the Hello World plugin."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
def cli():
    """Hello World Plugin for MilkBottle."""
    pass


@cli.command()
@click.option("--name", "-n", help="Name to greet")
@click.option(
    "--repeat", "-r", default=1, help="Number of times to repeat the greeting"
)
def hello(name: str, repeat: int):
    """Say hello to someone."""
    from . import plugin_instance

    greeting = plugin_instance.say_hello(name)

    for i in range(repeat):
        panel = Panel(greeting, title="Hello World Plugin", border_style="green")
        console.print(panel)


@cli.command()
def status():
    """Show plugin status."""
    from . import plugin_instance

    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()

    console.print(f"Plugin: {metadata.name}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Status: {health['status']}")
    console.print(f"Details: {health['details']}")


@cli.command()
def config():
    """Show plugin configuration."""
    from . import plugin_instance

    if plugin_instance.config:
        console.print("Plugin Configuration:")
        for key, value in plugin_instance.config.items():
            console.print(f"  {key}: {value}")
    else:
        console.print("No configuration loaded")


if __name__ == "__main__":
    cli()
