"""VENVmilker Typer CLI – interactive menu + power‑user flags
=============================================================

Invoked by MilkBottle as:

    $ milk bottle venv            # interactive menu (streamlined default)
    $ milk bottle venv . --python 3.10 --install rich typer --no-snapshot
    $ milk bottle venv --activate

This module intentionally imports Rich and Typer only when the user
actually runs the CLI, so the base `venvmilker` package remains lightweight
for non‑CLI use.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from milkbottle.modules.venvmilker.errors import VenvMilkerError
from milkbottle.modules.venvmilker.utils import find_interpreter
from milkbottle.modules.venvmilker.workflow import (
    activate_environment,
    bootstrap_environment,
    detect_project_root,
)

# --------------------------------------------------------------------------- #
# Typer app
# --------------------------------------------------------------------------- #

app = typer.Typer(
    help="Create, activate, and manage a local .venv for your project.",
    add_completion=False,
    no_args_is_help=False,  # we want zero‑flag default to fall through
)

console = Console()

# --------------------------------------------------------------------------- #
# CLI flags
# --------------------------------------------------------------------------- #


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(
        None,
        exists=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        help="Project root (defaults to CWD)",
    ),
    python: Optional[str] = typer.Option(
        None,
        "--python",
        "-p",
        help="Python version or absolute interpreter path",
    ),
    install: List[str] = typer.Option(
        None, help="Packages to install into the new environment"
    ),
    activate: bool = typer.Option(
        False,
        "--activate",
        "-a",
        help="Activate an existing .venv (skip creation)",
    ),
    snapshot: bool = typer.Option(
        True,
        "--snapshot/--no-snapshot",
        help="Write requirements.lock after install",
        show_default=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry",
        help="Preview actions without touching disk",
    ),
    snakemake: bool = typer.Option(
        False,
        "--snakemake",
        help="Also scaffold the Snakemake project template",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        help="info | debug | quiet",
        show_default=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Force the interactive menu even when flags are supplied",
    ),
) -> None:
    """Main entry point — routes to flags or interactive menu."""
    try:
        if interactive or _no_action_flags(ctx):
            _interactive_menu(path or Path.cwd())
            return

        if activate:
            _activate_flow(path or Path.cwd())
            return

        _create_flow(
            path or Path.cwd(),
            python,
            install,
            snapshot,
            dry_run,
            snakemake,
            log_level,
        )

    except VenvMilkerError as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(code=2) from err


# --------------------------------------------------------------------------- #
# High‑level flows
# --------------------------------------------------------------------------- #


def _create_flow(
    path: Path,
    python: Optional[str],
    install: List[str],
    snapshot: bool,
    dry_run: bool,
    snakemake: bool,
    log_level: str,
) -> None:
    try:
        root = detect_project_root(path)
        cli_kwargs = {
            "path": str(root),
            "python": python,
            "install": install,
            "snapshot": snapshot,
            "dry_run": dry_run,
            "template": "snakemake" if snakemake else None,
            "log_level": log_level,
        }
        bootstrap_environment(root, cli_kwargs, console)
    except VenvMilkerError:
        raise  # Re-raise VENVmilker-specific errors
    except Exception as exc:
        raise VenvMilkerError(
            f"Unexpected error during environment creation: {exc}"
        ) from exc


def _activate_flow(project_root: Path) -> None:
    try:
        activate_environment(project_root, console)
    except VenvMilkerError:
        raise  # Re-raise VENVmilker-specific errors
    except Exception as exc:
        raise VenvMilkerError(f"Unexpected error during activation: {exc}") from exc


# --------------------------------------------------------------------------- #
# Interactive Rich menu
# --------------------------------------------------------------------------- #


def _interactive_menu(project_root: Path) -> None:
    try:
        # mutable state for the session
        options = {
            "python": "3.11",
            "install": ["rich", "typer"],
            "snapshot": True,
            "dry_run": False,
        }

        while True:
            console.clear()
            _render_menu(project_root, options)

            choice = Prompt.ask(
                "\n[bold cyan]Select[/bold cyan]",
                choices=["1", "2", "3", "e", "0", "q"],
                default="1",
            )

            if choice in ["q", "0"]:
                return

            if choice == "e":
                _edit_options(options)
                continue

            if choice == "3":  # activate existing
                _activate_flow(project_root)
                continue

            # build CLI‑like args from current options
            _create_flow(
                project_root,
                options["python"],
                options["install"],
                options["snapshot"],
                options["dry_run"],
                False,  # snakemake
                "info",
            )
            Prompt.ask("\n[green]Done! Press Enter to return to menu…[/green]")
    except VenvMilkerError:
        raise  # Re-raise VENVmilker-specific errors
    except Exception as exc:
        raise VenvMilkerError(f"Unexpected error in interactive menu: {exc}") from exc


def _render_menu(project_root: Path, opt: dict) -> None:
    table = Table.grid()
    table.add_column(no_wrap=True)
    table.add_column()

    table.add_row("[bold]Target directory:[/bold]", str(project_root))
    table.add_row(
        "[bold]Python binary:[/bold]",
        str(find_interpreter(opt["python"])),
    )
    table.add_row()
    table.add_row("[bold]1.[/bold]", "Create & activate")
    table.add_row("[bold]2.[/bold]", "Create only")
    table.add_row("[bold]3.[/bold]", "Activate existing .venv")
    table.add_row("─" * 40, "")
    table.add_row("[u]Options[/u]", "")
    table.add_row("  Python :", opt["python"])
    table.add_row("  Install pkgs :", " ".join(opt["install"]) or "—")
    table.add_row("  Snapshot     :", "[x]" if opt["snapshot"] else "[ ]")
    table.add_row("  Dry‑run      :", "[x]" if opt["dry_run"] else "[ ]")
    table.add_row("─" * 40, "")
    table.add_row("[bold]e.[/bold]", "Edit options")
    table.add_row("[bold]0.[/bold]", "Back  |  [bold]q.[/bold] Quit")

    console.rule("[bright_magenta]VENVmilker")
    console.print(table)


def _edit_options(opt: dict) -> None:
    console.print("\n[bold yellow]-- Edit Options --[/bold yellow]")
    opt["python"] = Prompt.ask("Python", default=opt["python"])
    pkgs = Prompt.ask(
        "Packages (space‑separated, blank for none)",
        default=" ".join(opt["install"]),
    )
    opt["install"] = pkgs.split() if pkgs.strip() else []
    opt["snapshot"] = (
        Prompt.ask("Snapshot requirements.lock?", choices=["y", "n"], default="y")
        == "y"
    )
    opt["dry_run"] = Prompt.ask("Dry‑run only?", choices=["y", "n"], default="n") == "y"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _no_action_flags(ctx: typer.Context) -> bool:
    """Check if no action flags were provided (for interactive fallback)."""
    # Check if any non-default flags were provided
    return not any(
        [
            ctx.params.get("python"),
            ctx.params.get("install"),
            ctx.params.get("activate"),
            ctx.params.get("snapshot") is not None,
            ctx.params.get("dry_run"),
            ctx.params.get("snakemake"),
            ctx.params.get("log_level") != "info",
        ]
    )


def _banner_panel() -> Panel:
    table = Table.grid(padding=1)
    table.add_column(style="cyan", justify="right")
    table.add_column()
    table.add_row("[bold]1.[/bold]", "Create & activate .venv")
    table.add_row("[bold]2.[/bold]", "Create only")
    table.add_row("[bold]3.[/bold]", "Activate existing .venv")
    table.add_row("[bold]q.[/bold]", "Quit")
    return Panel(
        table, title="[b]VENVmilker[/b]", border_style="bright_magenta", box=box.DOUBLE
    )


# --------------------------------------------------------------------------- #
# Entry‑point for `python -m venvmilker.cli` debugging
# --------------------------------------------------------------------------- #


def run() -> None:  # pragma: no cover
    """Execute Typer app directly."""
    app()


if __name__ == "__main__":  # pragma: no cover
    run()
