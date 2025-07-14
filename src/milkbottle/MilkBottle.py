import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

from milkbottle import registry
from milkbottle.utils import print_menu_border

app = typer.Typer(
    help="MilkBottle – The Fluid Code Toolbox. Modular CLI with interactive ASCII menus."
)

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


def show_main_menu() -> None:
    """
    Display the MilkBottle main menu with Rich border and handle user input.
    """
    while True:
        console.clear()
        print_menu_border()
        console.print("[bold cyan]Welcome to MilkBottle![/bold cyan]", justify="center")
        console.print(
            "[dim]Select a bottle or option below to continue:[/dim]\n",
            justify="center",
        )
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
                        f"[bold][{idx}][/bold] {b['alias']} [dim](v{b['version']})[/dim]: {b['description']}"
                    )
                console.print("[bold][0][/bold] BACK -> MilkBottle Main Menu")
                valid_choices = [str(i) for i in range(len(bottles) + 1)]
                bottle_choice = Prompt.ask(
                    "Select a bottle to launch", choices=valid_choices, default="0"
                )
                if bottle_choice == "0":
                    continue
                else:
                    idx = int(bottle_choice) - 1
                    if 0 <= idx < len(bottles):
                        alias = bottles[idx]["alias"]
                        bottle_cli = registry.get_bottle(alias)
                        if bottle_cli:
                            try:
                                # Launch the bottle's Typer CLI
                                bottle_cli()
                            except Exception as e:
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
            from milkbottle.config import get_config

            config = get_config()
            from rich.panel import Panel
            from rich.pretty import Pretty

            console.print(
                Panel(
                    Pretty(config),
                    title="Current MilkBottle Configuration",
                    border_style="cyan",
                )
            )
            Prompt.ask("Press Enter to return to menu")
        elif choice == "q":
            console.print("[bold green]Goodbye![/bold green]")
            raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    log_level: Optional[str] = typer.Option(
        "info", "--log-level", help="Set log level: debug, info, warn, error"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to config file (TOML)"
    ),
    dry: bool = typer.Option(False, "--dry", help="Dry run mode (no changes made)"),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=lambda v: (print(__version__), sys.exit(0)) if v else None,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    MilkBottle CLI root. Use --help for options.
    """
    # Set log level
    level = logging.INFO
    if log_level is not None:
        level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    if ctx.invoked_subcommand is None:
        try:
            show_main_menu()
        except Exception as e:
            logger.error(f"[red]Fatal error:[/red] {e}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
