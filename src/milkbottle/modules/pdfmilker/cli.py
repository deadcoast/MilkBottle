import os
import tomllib
from pathlib import Path
from typing import Any, Dict

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from milkbottle.modules.pdfmilker.pipeline import run_pdfmilker_pipeline

app = typer.Typer(help="PDFmilker – Extract text, images, and metadata from PDFs.")

__alias__ = "PDFmilker"
__description__ = "PDF Extractor / Transformer"
__version__ = "0.1.0"

console = Console()

# Default options
defaults = {
    "outdir": None,
    "overwrite": False,
    "images": True,
    "log_level": "info",
    "dry_run": False,
    "pattern": None,
}

CONFIG_FILENAMES = ["pdfmilker.toml"]
ENV_PREFIX = "PDFMILKER_"


def load_pdfmilker_config() -> Dict[str, Any]:
    """
    Load and merge config from pdfmilker.toml (searched upward), environment variables, and defaults.
    Precedence: defaults < pdfmilker.toml < env < CLI.
    """
    config = defaults.copy()
    # 1. Load pdfmilker.toml (search upward)
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        for fname in CONFIG_FILENAMES:
            fpath = parent / fname
            if fpath.exists():
                try:
                    with fpath.open("rb") as f:
                        toml_data = tomllib.load(f)
                        config.update(
                            {k: v for k, v in toml_data.get("pdfmilker", {}).items()}
                        )
                except Exception:
                    pass
    # 2. Load env vars
    for k, v in os.environ.items():
        if k.startswith(ENV_PREFIX):
            key = k[len(ENV_PREFIX) :].lower()
            if key in config:
                if isinstance(config[key], bool):
                    config[key] = v.lower() in ("1", "true", "yes", "on")
                else:
                    config[key] = v
    return config


def show_pdfmilker_menu() -> None:
    """
    Display the PDFmilker interactive menu using Rich.
    """
    config = load_pdfmilker_config()
    options = config.copy()
    while True:
        console.clear()
        panel = Panel(
            Text(
                "This is a Welcome Message, Make sure your pdf files are in the same folder as the PDFmilker",
                justify="center",
            ),
            title=Text("PDFmilker", style="bold magenta"),
            subtitle=Text("PDF Extraction & Transformation", style="dim"),
            border_style="bold magenta",
            padding=(1, 2),
        )
        console.print(panel)
        console.print("[bold][1][/bold] Start PDF Extraction Process")
        console.print("[bold][2][/bold] Options")
        console.print("[bold][0][/bold] BACK -> MilkBottle Main Menu")
        console.print("[bold][q][/bold] QUIT APPLICATION\n")
        choice = Prompt.ask(
            "Select an option", choices=["1", "2", "0", "q"], default="1"
        )
        if choice == "1":
            console.clear()
            console.print(
                Panel(
                    "[bold green]Running PDFmilker pipeline...[/bold green]",
                    border_style="green",
                )
            )
            run_pdfmilker_pipeline(
                outdir=options["outdir"],
                overwrite=options["overwrite"],
                images=options["images"],
                log_level=options["log_level"],
                dry_run=options["dry_run"],
                pattern=options["pattern"],
            )
            Prompt.ask("Press Enter to return to menu")
        elif choice == "2":
            show_options_menu(options, config)
        elif choice == "0":
            return
        elif choice == "q":
            console.print("[bold green]Goodbye![/bold green]")
            raise typer.Exit()


def show_options_menu(options: dict, config: dict) -> None:
    """
    Display the PDFmilker options menu and allow user to set options. Show current config.
    """
    while True:
        console.clear()
        panel = Panel(
            Text("Options Menu", justify="center"),
            title=Text("PDFmilker Options", style="bold magenta"),
            border_style="bold magenta",
            padding=(1, 2),
        )
        console.print(panel)
        console.print("[bold]Current config (merged):[/bold]")
        for k, v in config.items():
            console.print(f"  [cyan]{k}[/cyan]: {v}")
        console.print("")
        console.print(
            f"[bold][1][/bold] [+]OVERWRITE allow re-milking existing slugs: [cyan]{options['overwrite']}[/cyan]"
        )
        console.print(
            f"[bold][2][/bold] LOG LEVEL [info|debug|quiet]: [cyan]{options['log_level']}[/cyan]"
        )
        console.print(f"[bold][3][/bold] IMAGES: [cyan]{options['images']}[/cyan]")
        console.print(f"[bold][4][/bold] DRY RUN: [cyan]{options['dry_run']}[/cyan]")
        console.print(
            f"[bold][5][/bold] PATTERN (glob): [cyan]{options['pattern']}[/cyan]"
        )
        console.print(f"[bold][6][/bold] OUTDIR: [cyan]{options['outdir']}[/cyan]")
        console.print("[bold][0][/bold] GO BACK -> PDFmilker Main Menu\n")
        choice = Prompt.ask(
            "Select an option", choices=["1", "2", "3", "4", "5", "6", "0"], default="0"
        )
        if choice == "0":
            return
        elif choice == "1":
            options["overwrite"] = not options["overwrite"]
        elif choice == "2":
            options["log_level"] = Prompt.ask(
                "Set log level",
                choices=["info", "debug", "quiet"],
                default=options["log_level"],
            )
        elif choice == "3":
            options["images"] = not options["images"]
        elif choice == "4":
            options["dry_run"] = not options["dry_run"]
        elif choice == "5":
            options["pattern"] = (
                Prompt.ask(
                    "Set glob pattern (or leave blank for all)",
                    default=options["pattern"] or "",
                )
                or None
            )
        elif choice == "6":
            options["outdir"] = (
                Prompt.ask(
                    "Set output directory (or leave blank for default)",
                    default=options["outdir"] or "",
                )
                or None
            )


def get_cli() -> typer.Typer:
    """
    Return the Typer app for PDFmilker.
    """
    return app


@app.callback()
def main(ctx: typer.Context) -> None:
    """
    PDFmilker CLI entry point. Shows the interactive menu if no subcommand is invoked.
    """
    if ctx.invoked_subcommand is None:
        show_pdfmilker_menu()
    if ctx.invoked_subcommand is None:
        show_pdfmilker_menu()
