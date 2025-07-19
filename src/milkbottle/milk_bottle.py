"""MilkBottle CLI module."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

from milkbottle import registry
from milkbottle.milk_config import MilkBottleConfig, get_config

console = Console()

# Set up logging with RichHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("milkbottle")

__version__ = "0.1.0"

# Global configuration object
config: Optional[MilkBottleConfig] = None


def print_menu_border() -> None:
    """Print a decorative border for the menu."""
    console.print("╭" + "─" * 78 + "╮")
    console.print("│" + " " * 78 + "│")
    console.print("╰" + "─" * 78 + "╯")


def show_main_menu() -> None:
    """
    Display the MilkBottle main menu with Rich border and handle user input.
    """
    global config

    while True:
        console.clear()
        print_menu_border()
        console.print("[bold cyan]Welcome to MilkBottle![/bold cyan]", justify="center")
        console.print(
            "[dim]Select a bottle or option below to continue:[/dim]\n",
            justify="center",
        )

        # Show dry-run indicator if enabled
        if config and config.is_dry_run():
            console.print(
                "[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]",
                justify="center",
            )
            console.print()

        console.print("[bold][1][/bold] List and launch available bottles")
        console.print("[bold][2][/bold] Show configuration")
        console.print("[bold][q][/bold] Quit\n")
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "q"], default="1")
        if choice == "1":
            bottles = registry.list_bottles()
            console.print("\n[bold underline]Available Bottles:[/bold underline]")
            if bottles:
                for idx, b in enumerate(bottles, 1):
                    console.print(
                        f"[bold][{idx}][/bold] {b['alias']} "
                        f"[dim](v{b['version']})[/dim]: {b['description']}"
                    )
                console.print("[bold][0][/bold] BACK -> MilkBottle Main Menu")
                valid_choices = [str(i) for i in range(len(bottles) + 1)]
                bottle_choice = Prompt.ask(
                    "Select a bottle to launch", choices=valid_choices, default="0"
                )
                if bottle_choice == "0":
                    continue
                idx = int(bottle_choice) - 1
                if 0 <= idx < len(bottles):
                    alias = bottles[idx]["alias"]
                    bottle_cli = registry.get_bottle(alias)
                    if bottle_cli:
                        try:
                            # Launch the bottle's CLI
                            bottle_cli([])
                        except (OSError, ImportError, RuntimeError) as e:
                            console.print(
                                f"[red]Error launching bottle '{alias}': {e}[/red]"
                            )
                            Prompt.ask("Press Enter to return to menu")
                    else:
                        console.print(
                            f"[red]Bottle '{alias}' could not be loaded.[/red]"
                        )
                        Prompt.ask("Press Enter to return to menu")
                else:
                    console.print("[red]Invalid selection.[/red]")
                    Prompt.ask("Press Enter to return to menu")
            else:
                console.print(
                    "[yellow]No bottles found. Add a bottle to get started![/yellow]"
                )
                Prompt.ask("Press Enter to return to menu")
        elif choice == "2":
            _show_configuration()
        elif choice == "q":
            console.print("[bold green]Goodbye![/bold green]")
            sys.exit(0)


def _show_configuration() -> None:
    """Display current configuration."""
    global config

    if not config:
        console.print("[yellow]No configuration loaded.[/yellow]")
        Prompt.ask("Press Enter to return to menu")
        return

    console.print("\n[bold underline]MilkBottle Configuration:[/bold underline]")
    console.print(f"Log Level: {config.log_level}")
    console.print(f"Dry Run: {config.is_dry_run()}")
    console.print(f"Config File: {config.config_file or 'None (using defaults)'}")

    if config.bottles:
        console.print("\n[bold]Bottle Configurations:[/bold]")
        for bottle_name, bottle_config in config.bottles.items():
            console.print(f"  {bottle_name}: {bottle_config}")

    if config.global_settings:
        console.print("\n[bold]Global Settings:[/bold]")
        for key, value in config.global_settings.items():
            console.print(f"  {key}: {value}")

    Prompt.ask("Press Enter to return to menu")


@click.group()
@click.option(
    "--log-level",
    default="info",
    help="Set log level: debug, info, warn, error",
    type=click.Choice(["debug", "info", "warn", "error"]),
)
@click.option("--config", "config_file", help="Path to config file (TOML)")
@click.option("--dry", is_flag=True, help="Dry run mode (no changes made)")
def cli(log_level: str, config_file: Optional[str], dry: bool) -> None:
    """
    MilkBottle – The Fluid Code Toolbox. Modular CLI with interactive ASCII menus.
    """
    global config

    # Load configuration
    config = get_config(
        project_root=None,  # Will use current directory
        config_file=config_file,
        dry_run=dry,
        log_level=log_level,
    )

    # Set log level
    level = logging.INFO
    if config.log_level:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Log configuration loading
    logger.info("Configuration loaded: %s", config.as_dict())


@cli.command()
def main() -> None:
    """
    Launch the interactive MilkBottle menu.
    """
    try:
        show_main_menu()
    except (OSError, ImportError, RuntimeError) as e:
        logger.error("[red]Fatal error:[/red] %s", e)
        sys.exit(1)


@cli.command()
@click.argument("bottle_name")
@click.argument("bottle_args", nargs=-1)
@click.pass_context
def bottle(ctx: click.Context, bottle_name: str, bottle_args: tuple) -> None:
    """
    Run a specific bottle by name with arguments.

    Example: milk bottle venvmilker --python 3.11 --dry
    """
    global config

    # Load default configuration if not already loaded
    if config is None:
        config = get_config()

    bottle_cli = registry.get_bottle(bottle_name)
    if bottle_cli:
        # Convert tuple to list and call the bottle CLI
        args = list(bottle_args) or ["--help"]
        bottle_cli(args)
    else:
        console.print(f"[red]Bottle '{bottle_name}' not found.[/red]")
        bottles = registry.list_bottles()
        if bottles:
            console.print("\n[bold]Available bottles:[/bold]")
            for b in bottles:
                console.print(f"  {b['alias']} - {b['description']}")
        sys.exit(1)


def run_cli() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    run_cli()
