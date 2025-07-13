import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

app = typer.Typer(help="PDFmilker – Extract text, images, and metadata from PDFs.")

__alias__ = "PDFmilker"
__description__ = "PDF Extractor / Transformer"
__version__ = "0.1.0"

console = Console()


def show_pdfmilker_menu() -> None:
    """
    Display the PDFmilker interactive menu using Rich.
    """
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
            console.print("[yellow]Extraction process not yet implemented.[/yellow]")
            Prompt.ask("Press Enter to return to menu")
        elif choice == "2":
            show_options_menu()
        elif choice == "0":
            return
        elif choice == "q":
            console.print("[bold green]Goodbye![/bold green]")
            raise typer.Exit()


def show_options_menu() -> None:
    """
    Display the PDFmilker options menu.
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
        console.print("[bold][1][/bold] [+]OVERWRITE allow re-milking existing slugs")
        console.print("[bold][2][/bold] LOG LEVEL [-]info|[-]debug|[+]quiet]")
        console.print("[bold][0][/bold] GO BACK -> PDFmilker Main Menu\n")
        choice = Prompt.ask("Select an option", choices=["1", "2", "0"], default="0")
        if choice == "0":
            return
        elif choice == "1":
            console.print("[yellow]Overwrite toggle not yet implemented.[/yellow]")
            Prompt.ask("Press Enter to return to options menu")
        elif choice == "2":
            console.print("[yellow]Log level toggle not yet implemented.[/yellow]")
            Prompt.ask("Press Enter to return to options menu")


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
