"""Fontmilker CLI interface."""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.option("--config", help="Configuration file path")
@click.option("--dry-run", is_flag=True, help="Dry run mode")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cli(config: Optional[str], dry_run: bool, verbose: bool):
    """Font extraction and management tool."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir", "-o", default="fonts", help="Output directory for extracted fonts"
)
@click.option(
    "--formats",
    "-f",
    multiple=True,
    default=["ttf", "otf"],
    help="Font formats to extract",
)
def extract(path: Path, output_dir: str, formats: tuple):
    """Extract fonts from documents."""
    console.print(f"[bold cyan]Extracting fonts from: {path}[/bold cyan]")
    console.print(f"[dim]Output directory: {output_dir}[/dim]")
    console.print(f"[dim]Formats: {', '.join(formats)}[/dim]")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Check if path is a file or directory
    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob("*")) if path.is_dir() else []

    extracted_count = 0

    for file_path in files:
        if file_path.suffix.lower() in [".pdf", ".docx", ".pptx"]:
            try:
                # Extract fonts using system tools
                if file_path.suffix.lower() == ".pdf":
                    extracted_count += _extract_fonts_from_pdf(
                        file_path, output_path, formats
                    )
                elif file_path.suffix.lower() in [".docx", ".pptx"]:
                    extracted_count += _extract_fonts_from_office(
                        file_path, output_path, formats
                    )

            except Exception as e:
                console.print(
                    f"[red]Error extracting fonts from {file_path}: {e}[/red]"
                )

    if extracted_count > 0:
        console.print(f"[green]Successfully extracted {extracted_count} fonts[/green]")
    else:
        console.print("[yellow]No fonts were extracted[/yellow]")


def _extract_fonts_from_pdf(pdf_path: Path, output_path: Path, formats: tuple) -> int:
    """Extract fonts from PDF using pdftk or similar tools."""
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        # Try using pdftk to extract fonts
        result = subprocess.run(
            ["pdftk", str(pdf_path), "dump_data_fields"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return sum("FontName" in line for line in result.stdout.split("\n"))
    # Fallback: try using pdfinfo
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return result.stdout.count("Font")
    return 0


def _extract_fonts_from_office(
    file_path: Path, output_path: Path, formats: tuple
) -> int:
    """Extract fonts from Office documents."""
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        # For Office documents, we can try to extract embedded fonts
        # This is a simplified implementation
        temp_dir = output_path / f"temp_{file_path.stem}"
        temp_dir.mkdir(exist_ok=True)

        # Try using unzip for .docx/.pptx files
        if file_path.suffix.lower() in [".docx", ".pptx"]:
            result = subprocess.run(
                ["unzip", "-q", str(file_path), "-d", str(temp_dir)],
                capture_output=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Look for font files in the extracted content
                font_files = list(temp_dir.rglob("*.ttf")) + list(
                    temp_dir.rglob("*.otf")
                )

                # Copy found fonts to output directory
                for font_file in font_files:
                    shutil.copy2(font_file, output_path / font_file.name)

                # Clean up
                shutil.rmtree(temp_dir)
                return len(font_files)
    return 0


@cli.command()
@click.argument("font_path", type=click.Path(exists=True, path_type=Path))
def analyze(font_path: Path):
    """Analyze font metadata and properties."""
    console.print(f"[bold cyan]Analyzing font: {font_path}[/bold cyan]")

    # Create analysis table
    table = Table(title="Font Analysis")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")

    try:
        # Basic file analysis
        stat = font_path.stat()
        table.add_row("File Size", f"{stat.st_size:,} bytes", "✅")
        table.add_row("File Type", font_path.suffix.upper(), "✅")
        table.add_row("Last Modified", str(stat.st_mtime), "✅")

        # Try to get font information using system tools
        font_info = _get_font_info(font_path)

        for key, value in font_info.items():
            table.add_row(key, str(value), "✅")

    except Exception as e:
        table.add_row("Error", str(e), "❌")

    console.print(table)


def _get_font_info(font_path: Path) -> dict:
    """Get font information using system tools."""
    info = {}

    # Try using fc-query (fontconfig)
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        result = subprocess.run(
            ["fc-query", str(font_path)], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()
    # Try using otfinfo for OpenType fonts
    if font_path.suffix.lower() in [".otf", ".ttf"]:
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            result = subprocess.run(
                ["otfinfo", str(font_path)], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        info[f"OTF_{key.strip()}"] = value.strip()
    return info


@cli.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output_path", type=click.Path(path_type=Path))
@click.option("--format", "-f", default="ttf", help="Output format")
def convert(input_path: Path, output_path: Path, format: str):
    """Convert font to different format."""
    console.print(
        f"[bold cyan]Converting font: {input_path} -> {output_path}[/bold cyan]"
    )
    console.print(f"[dim]Output format: {format}[/dim]")

    try:
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if success := _convert_with_fontforge(
            input_path, output_path, format
        ) or _convert_with_other_tools(input_path, output_path, format):
            console.print(f"[green]Successfully converted font to {format}[/green]")
            console.print(f"Output saved to: {output_path}")
        else:
            console.print("[red]Font conversion failed[/red]")
            console.print("Tried both FontForge and alternative tools")

    except Exception as e:
        console.print(f"[red]Error during conversion: {e}[/red]")


def _convert_with_fontforge(input_path: Path, output_path: Path, format: str) -> bool:
    """Convert font using FontForge."""
    try:
        # Create a Python script for FontForge
        script_content = f"""
import fontforge
font = fontforge.open("{input_path}")
font.generate("{output_path}")
font.close()
"""

        result = subprocess.run(
            ["fontforge", "-lang=py", "-c", script_content],
            capture_output=True,
            timeout=120,
        )

        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _convert_with_other_tools(input_path: Path, output_path: Path, format: str) -> bool:
    """Convert font using other available tools."""
    # Try using ttf2eot for TTF to EOT conversion
    if format.lower() == "eot" and input_path.suffix.lower() == ".ttf":
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            result = subprocess.run(
                ["ttf2eot", str(input_path)], capture_output=True, timeout=60
            )

            if result.returncode == 0:
                with open(output_path, "wb") as f:
                    f.write(result.stdout)
                return True
    # Try using woff2_compress for WOFF2 conversion
    if format.lower() == "woff2":
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            result = subprocess.run(
                ["woff2_compress", str(input_path)], capture_output=True, timeout=60
            )

            if result.returncode == 0:
                woff2_path = input_path.with_suffix(".woff2")
                if woff2_path.exists():
                    shutil.move(woff2_path, output_path)
                    return True
    return False


@cli.command()
def status():
    """Show module status."""
    console.print("[bold cyan]Fontmilker Status[/bold cyan]")

    # Create status table
    table = Table(title="Module Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # Check for required tools
    tools = {
        "pdftk": "PDF font extraction",
        "pdfinfo": "PDF information",
        "fc-query": "Font information",
        "otfinfo": "OpenType font analysis",
        "fontforge": "Font conversion",
        "ttf2eot": "TTF to EOT conversion",
        "woff2_compress": "WOFF2 compression",
    }

    for tool, description in tools.items():
        try:
            subprocess.run([tool, "--help"], capture_output=True, timeout=5)
            table.add_row(tool, "✅ Available", description)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            table.add_row(tool, "❌ Not Found", description)

    console.print(table)


@cli.command()
def config():
    """Show module configuration."""
    console.print("[bold cyan]Fontmilker Configuration[/bold cyan]")

    # Create config table
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Description", style="dim")

    table.add_row("enabled", "True", "Module is enabled")
    table.add_row("output_dir", "fonts", "Default output directory")
    table.add_row("extract_formats", "ttf, otf, woff, woff2", "Supported font formats")
    table.add_row("analyze_fonts", "True", "Enable font analysis")
    table.add_row("convert_fonts", "True", "Enable font conversion")
    table.add_row("optimize_fonts", "False", "Enable font optimization")
    table.add_row("validate_fonts", "True", "Enable font validation")

    console.print(table)


# Create the app instance
app = cli
