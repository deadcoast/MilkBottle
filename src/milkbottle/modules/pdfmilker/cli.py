"""PDFmilker CLI with enhanced features and interactive menus."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from milkbottle.modules.pdfmilker.batch_processor import batch_processor
from milkbottle.modules.pdfmilker.citation_processor import citation_processor
from milkbottle.modules.pdfmilker.config import pdfmilker_config
from milkbottle.modules.pdfmilker.config_validator import config_validator
from milkbottle.modules.pdfmilker.error_recovery import (
    error_recovery_manager,
    pdf_processing_recovery,
)
from milkbottle.modules.pdfmilker.format_exporter import format_exporter
from milkbottle.modules.pdfmilker.image_processor import image_processor
from milkbottle.modules.pdfmilker.pipeline import pipeline
from milkbottle.modules.pdfmilker.quality_assessor import quality_assessor
from milkbottle.modules.pdfmilker.table_processor import table_processor
from milkbottle.utils import get_console

logger = logging.getLogger("pdfmilker.cli")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", type=click.Path(), help="Configuration file path")
def cli(verbose: bool, config: Optional[str]) -> None:
    """PDFmilker - Advanced PDF extraction and processing tool."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if config:
        pdfmilker_config.load_from_file(Path(config))


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "latex", "json", "docx"]),
    default="markdown",
    help="Output format",
)
@click.option("--quality", "-q", is_flag=True, help="Enable quality assessment")
@click.option("--images", "-i", is_flag=True, help="Extract images with captions")
@click.option("--tables", "-t", is_flag=True, help="Extract tables with structure")
@click.option(
    "--citations", "-c", is_flag=True, help="Extract citations and bibliography"
)
def extract(
    pdf_path: str,
    output: Optional[str],
    format: str,
    quality: bool,
    images: bool,
    tables: bool,
    citations: bool,
) -> None:
    """Extract content from a single PDF file with enhanced features."""
    console = get_console()

    try:
        pdf_file = Path(pdf_path)
        output_dir = Path(output) if output else pdf_file.parent / "extracted"

        with console.status(f"[bold green]Processing {pdf_file.name}..."):
            # Process PDF with error recovery
            result = pdf_processing_recovery.process_pdf_with_recovery(
                pdf_file,
                lambda p: pipeline.process_pdf(p, output_dir),
                lambda p: pipeline.process_pdf_fallback(p, output_dir),
            )

            if hasattr(result, "data"):  # Partial result
                console.print(
                    f"[yellow]Partial extraction completed: {result.success_ratio:.1%} success[/yellow]"
                )
                extracted_content = result.data
            else:
                extracted_content = result

            # Enhanced processing based on flags
            if images:
                console.print("[blue]Extracting images with captions...[/blue]")
                figures = image_processor.extract_figures_with_captions(pdf_file)
                extracted_content["figures"] = [f.to_dict() for f in figures]

                # Image statistics
                img_stats = image_processor.get_image_statistics(figures)
                console.print(
                    f"[green]Extracted {img_stats['total_figures']} images[/green]"
                )

            if tables:
                console.print("[blue]Extracting tables with structure...[/blue]")
                table_structures = table_processor.extract_tables_with_structure(
                    pdf_file
                )
                extracted_content["tables"] = [t.to_dict() for t in table_structures]

                # Table statistics
                table_stats = table_processor.get_table_statistics(table_structures)
                console.print(
                    f"[green]Extracted {table_stats['total_tables']} tables[/green]"
                )

            if citations:
                console.print("[blue]Extracting citations and bibliography...[/blue]")
                bibliography = citation_processor.extract_citations(pdf_file)
                extracted_content["citations"] = bibliography.to_dict()

                # Citation statistics
                citation_stats = citation_processor.get_citation_statistics(
                    bibliography
                )
                console.print(
                    f"[green]Extracted {citation_stats['total_citations']} citations[/green]"
                )

            # Quality assessment
            if quality:
                console.print("[blue]Assessing extraction quality...[/blue]")
                quality_report = quality_assessor.assess_extraction_quality(
                    pdf_file, extracted_content
                )
                extracted_content["quality_report"] = quality_report.to_dict()

                # Display quality summary
                overall_quality = quality_report.overall_quality
                quality_level = quality_report.get_quality_level()
                console.print(
                    f"[green]Quality Assessment: {quality_level} ({overall_quality:.1%})[/green]"
                )

            # Export to specified format
            console.print(f"[blue]Exporting to {format.upper()} format...[/blue]")
            output_file = format_exporter.export_to_format(
                extracted_content, format, output_dir
            )

            console.print(
                "[bold green]✅ Extraction completed successfully![/bold green]"
            )
            console.print(f"Output: {output_file}")

    except Exception as e:
        console.print(f"[bold red]❌ Extraction failed: {e}[/bold red]")
        logger.error(f"Extraction failed: {e}", exc_info=True)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "latex", "json", "docx"]),
    default="markdown",
    help="Output format",
)
@click.option("--quality", "-q", is_flag=True, help="Enable quality assessment")
@click.option("--images", "-i", is_flag=True, help="Extract images with captions")
@click.option("--tables", "-t", is_flag=True, help="Extract tables with structure")
@click.option(
    "--citations", "-c", is_flag=True, help="Extract citations and bibliography"
)
def batch(
    input_path: str,
    output: Optional[str],
    format: str,
    quality: bool,
    images: bool,
    tables: bool,
    citations: bool,
) -> None:
    """Process multiple PDF files with batch processing and enhanced features."""
    console = get_console()

    try:
        input_dir = Path(input_path)
        output_dir = Path(output) if output else input_dir / "extracted"

        # Find PDF files
        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            console.print(
                "[yellow]No PDF files found in the specified directory[/yellow]"
            )
            return

        console.print(f"[blue]Found {len(pdf_files)} PDF files[/blue]")

        # Configure batch processing
        batch_config = configure_batch_settings(console)

        # Process files with enhanced features
        results = batch_processor.process_batch(
            pdf_files,
            output_dir=output_dir,
            format_type=format,
            quality_assessment=quality,
            image_extraction=images,
            table_extraction=tables,
            citation_extraction=citations,
            **batch_config,
        )

        # Display results
        display_batch_results(console, results)

    except Exception as e:
        console.print(f"[bold red]❌ Batch processing failed: {e}[/bold red]")
        logger.error(f"Batch processing failed: {e}", exc_info=True)


@cli.command()
def menu() -> None:
    """Interactive menu for PDFmilker operations."""
    console = get_console()

    while True:
        console.print("\n" + "=" * 60)
        console.print("[bold blue]PDFmilker Interactive Menu[/bold blue]")
        console.print("=" * 60)

        options = [
            "1. Single PDF Extraction",
            "2. Batch PDF Processing",
            "3. Export Options",
            "4. Quality Assessment",
            "5. Image Processing",
            "6. Table Processing",
            "7. Citation Processing",
            "8. Configuration Validation",
            "9. Error Recovery Status",
            "0. Exit",
        ]

        for option in options:
            console.print(f"  {option}")

        choice = Prompt.ask(
            "\nSelect an option",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        )

        if choice == "0":
            console.print("[green]Goodbye![/green]")
            break
        elif choice == "1":
            single_file_menu(console)
        elif choice == "2":
            batch_menu(console)
        elif choice == "3":
            export_options_menu(console)
        elif choice == "4":
            quality_assessment_menu(console)
        elif choice == "5":
            image_processing_menu(console)
        elif choice == "6":
            table_processing_menu(console)
        elif choice == "7":
            citation_processing_menu(console)
        elif choice == "8":
            configuration_validation_menu(console)
        elif choice == "9":
            error_recovery_status_menu(console)


def single_file_menu(console: Console) -> None:
    """Interactive menu for single file processing."""
    console.print("\n[bold blue]Single PDF Extraction[/bold blue]")

    pdf_path = Prompt.ask("Enter PDF file path")
    if not Path(pdf_path).exists():
        console.print("[red]File not found![/red]")
        return

    output_dir = Prompt.ask("Output directory (optional)", default="")
    format_type = Prompt.ask(
        "Output format",
        choices=["markdown", "html", "latex", "json", "docx"],
        default="markdown",
    )

    # Enhanced features
    quality = Confirm.ask("Enable quality assessment?")
    images = Confirm.ask("Extract images with captions?")
    tables = Confirm.ask("Extract tables with structure?")
    citations = Confirm.ask("Extract citations and bibliography?")

    # Execute extraction
    try:
        pdf_file = Path(pdf_path)
        output_path = Path(output_dir) if output_dir else pdf_file.parent / "extracted"

        with console.status(f"[bold green]Processing {pdf_file.name}..."):
            # Process with all selected features
            result = process_single_file_with_features(
                pdf_file, output_path, format_type, quality, images, tables, citations
            )

            console.print("[bold green]✅ Extraction completed![/bold green]")
            console.print(f"Output: {result}")

    except Exception as e:
        console.print(f"[bold red]❌ Extraction failed: {e}[/bold red]")


def batch_menu(console: Console) -> None:
    """Interactive menu for batch processing."""
    console.print("\n[bold blue]Batch PDF Processing[/bold blue]")

    input_path = Prompt.ask("Enter input directory path")
    if not Path(input_path).exists():
        console.print("[red]Directory not found![/red]")
        return

    output_dir = Prompt.ask("Output directory (optional)", default="")
    format_type = Prompt.ask(
        "Output format",
        choices=["markdown", "html", "latex", "json", "docx"],
        default="markdown",
    )

    # Enhanced features
    quality = Confirm.ask("Enable quality assessment?")
    images = Confirm.ask("Extract images with captions?")
    tables = Confirm.ask("Extract tables with structure?")
    citations = Confirm.ask("Extract citations and bibliography?")

    # Batch configuration
    batch_config = configure_batch_settings(console)

    # Execute batch processing
    try:
        input_dir = Path(input_path)
        output_path = Path(output_dir) if output_dir else input_dir / "extracted"

        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            console.print("[yellow]No PDF files found![/yellow]")
            return

        console.print(f"[blue]Found {len(pdf_files)} PDF files[/blue]")

        results = batch_processor.process_batch(
            pdf_files,
            output_dir=output_path,
            format_type=format_type,
            quality_assessment=quality,
            image_extraction=images,
            table_extraction=tables,
            citation_extraction=citations,
            **batch_config,
        )

        display_batch_results(console, results)

    except Exception as e:
        console.print(f"[bold red]❌ Batch processing failed: {e}[/bold red]")


def image_processing_menu(console: Console) -> None:
    """Interactive menu for image processing."""
    console.print("\n[bold blue]Image Processing[/bold blue]")

    pdf_path = Prompt.ask("Enter PDF file path")
    if not Path(pdf_path).exists():
        console.print("[red]File not found![/red]")
        return

    output_dir = Prompt.ask(
        "Image output directory (optional)", default="extracted_images"
    )

    try:
        pdf_file = Path(pdf_path)
        output_path = Path(output_dir)

        with console.status("[bold green]Extracting images with captions..."):
            figures = image_processor.extract_figures_with_captions(pdf_file)

            # Display results
            stats = image_processor.get_image_statistics(figures)

            table = Table(title="Image Extraction Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Figures", str(stats["total_figures"]))
            table.add_row("Pages with Figures", str(stats["pages_with_figures"]))
            table.add_row("Captions Extracted", str(stats["captions_extracted"]))
            table.add_row(
                "Figure Numbers Assigned", str(stats["figure_numbers_assigned"])
            )
            table.add_row(
                "Total File Size", f"{stats['total_file_size'] / 1024 / 1024:.1f} MB"
            )

            console.print(table)

            # Quality distribution
            quality_table = Table(title="Image Quality Distribution")
            quality_table.add_column("Quality Level", style="cyan")
            quality_table.add_column("Count", style="green")

            for level, count in stats["quality_distribution"].items():
                quality_table.add_row(level.title(), str(count))

            console.print(quality_table)

            console.print("[bold green]✅ Image extraction completed![/bold green]")
            console.print(f"Images saved to: {output_path}")

    except Exception as e:
        console.print(f"[bold red]❌ Image processing failed: {e}[/bold red]")


def table_processing_menu(console: Console) -> None:
    """Interactive menu for table processing."""
    console.print("\n[bold blue]Table Processing[/bold blue]")

    pdf_path = Prompt.ask("Enter PDF file path")
    if not Path(pdf_path).exists():
        console.print("[red]File not found![/red]")
        return

    export_format = Prompt.ask(
        "Export format", choices=["csv", "excel", "json"], default="csv"
    )

    try:
        pdf_file = Path(pdf_path)

        with console.status("[bold green]Extracting tables with structure..."):
            tables = table_processor.extract_tables_with_structure(pdf_file)

            # Display results
            stats = table_processor.get_table_statistics(tables)

            table = Table(title="Table Extraction Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Tables", str(stats["total_tables"]))
            table.add_row("Pages with Tables", str(stats["pages_with_tables"]))
            table.add_row("Tables with Headers", str(stats["tables_with_headers"]))
            table.add_row("Captions Extracted", str(stats["captions_extracted"]))
            table.add_row("Average Confidence", f"{stats['average_confidence']:.1%}")

            console.print(table)

            # Structure type distribution
            structure_table = Table(title="Table Structure Types")
            structure_table.add_column("Structure Type", style="cyan")
            structure_table.add_column("Count", style="green")

            for structure_type, count in stats["structure_types"].items():
                structure_table.add_row(structure_type.title(), str(count))

            console.print(structure_table)

            # Export tables if requested
            if tables and export_format:
                output_dir = pdf_file.parent / "extracted_tables"
                output_dir.mkdir(exist_ok=True)

                for i, table in enumerate(tables):
                    if export_format == "csv":
                        output_file = output_dir / f"table_{i+1}.csv"
                        table_processor.export_table_to_csv(table, output_file)
                    elif export_format == "excel":
                        output_file = output_dir / f"table_{i+1}.xlsx"
                        table_processor.export_table_to_excel(table, output_file)

                console.print(f"[green]Tables exported to: {output_dir}[/green]")

            console.print("[bold green]✅ Table extraction completed![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Table processing failed: {e}[/bold red]")


def citation_processing_menu(console: Console) -> None:
    """Interactive menu for citation processing."""
    console.print("\n[bold blue]Citation Processing[/bold blue]")

    pdf_path = Prompt.ask("Enter PDF file path")
    if not Path(pdf_path).exists():
        console.print("[red]File not found![/red]")
        return

    export_format = Prompt.ask(
        "Export format", choices=["bibtex", "markdown", "json"], default="bibtex"
    )

    try:
        pdf_file = Path(pdf_path)

        with console.status("[bold green]Extracting citations and bibliography..."):
            bibliography = citation_processor.extract_citations(pdf_file)

            # Display results
            stats = citation_processor.get_citation_statistics(bibliography)

            table = Table(title="Citation Extraction Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Citations", str(stats["total_citations"]))
            table.add_row("Pages with Citations", str(stats["pages_with_citations"]))
            table.add_row(
                "Citations with Authors", str(stats["citations_with_authors"])
            )
            table.add_row("Citations with Years", str(stats["citations_with_years"]))
            table.add_row("Citations with Titles", str(stats["citations_with_titles"]))
            table.add_row("Citations with DOIs", str(stats["citations_with_dois"]))
            table.add_row("Average Confidence", f"{stats['average_confidence']:.1%}")

            console.print(table)

            # Citation type distribution
            type_table = Table(title="Citation Types")
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="green")

            for citation_type, count in stats["citation_types"].items():
                type_table.add_row(citation_type.title(), str(count))

            console.print(type_table)

            # Export citations if requested
            if bibliography.citations and export_format:
                output_dir = pdf_file.parent / "extracted_citations"
                output_dir.mkdir(exist_ok=True)

                if export_format == "bibtex":
                    output_file = output_dir / f"{pdf_file.stem}_citations.bib"
                    with open(output_file, "w") as f:
                        f.write(bibliography.to_bibtex())
                elif export_format == "markdown":
                    output_file = output_dir / f"{pdf_file.stem}_citations.md"
                    with open(output_file, "w") as f:
                        f.write(bibliography.to_markdown())
                elif export_format == "json":
                    output_file = output_dir / f"{pdf_file.stem}_citations.json"
                    import json

                    with open(output_file, "w") as f:
                        json.dump(bibliography.to_dict(), f, indent=2)

                console.print(f"[green]Citations exported to: {output_file}[/green]")

            console.print("[bold green]✅ Citation extraction completed![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Citation processing failed: {e}[/bold red]")


def configuration_validation_menu(console: Console) -> None:
    """Interactive menu for configuration validation."""
    console.print("\n[bold blue]Configuration Validation[/bold blue]")

    try:
        with console.status("[bold green]Validating configuration..."):
            validation_results = config_validator.validate_config(pdfmilker_config)

            # Display validation report
            report = config_validator.get_validation_report()
            console.print(Panel(report, title="Configuration Validation Report"))

            # Display detailed results
            if validation_results["errors"]:
                console.print("\n[bold red]Validation Errors:[/bold red]")
                for error in validation_results["errors"]:
                    console.print(f"  • {error['message']}")

            if validation_results["recommendations"]:
                console.print("\n[bold yellow]Recommendations:[/bold yellow]")
                for rec in validation_results["recommendations"]:
                    console.print(f"  • {rec}")

            if validation_results["overall_valid"]:
                console.print("[bold green]✅ Configuration is valid![/bold green]")
            else:
                console.print(
                    "[bold red]❌ Configuration has issues that need to be addressed.[/bold red]"
                )

    except Exception as e:
        console.print(f"[bold red]❌ Configuration validation failed: {e}[/bold red]")


def error_recovery_status_menu(console: Console) -> None:
    """Interactive menu for error recovery status."""
    console.print("\n[bold blue]Error Recovery Status[/bold blue]")

    try:
        stats = error_recovery_manager.get_error_statistics()

        table = Table(title="Error Recovery Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Errors", str(stats["total_errors"]))
        table.add_row("Partial Results", str(stats["partial_results"]))

        console.print(table)

        # Error type distribution
        if stats["error_types"]:
            error_table = Table(title="Error Types")
            error_table.add_column("Error Type", style="cyan")
            error_table.add_column("Count", style="red")

            for error_type, count in stats["error_types"].items():
                error_table.add_row(error_type, str(count))

            console.print(error_table)

        # Strategy usage
        if stats["strategies_used"]:
            strategy_table = Table(title="Recovery Strategies Used")
            strategy_table.add_column("Strategy", style="cyan")
            strategy_table.add_column("Count", style="blue")

            for strategy, count in stats["strategies_used"].items():
                strategy_table.add_row(strategy, str(count))

            console.print(strategy_table)

        # Recent errors
        if stats["recent_errors"]:
            console.print("\n[bold yellow]Recent Errors:[/bold yellow]")
            for error_info in stats["recent_errors"][-5:]:  # Last 5 errors
                console.print(
                    f"  • {error_info['error_type']}: {error_info['error_message']}"
                )

        # Clear history option
        if Confirm.ask("\nClear error history?"):
            error_recovery_manager.clear_history()
            console.print("[green]Error history cleared![/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error recovery status failed: {e}[/bold red]")


def process_single_file_with_features(
    pdf_file: Path,
    output_dir: Path,
    format_type: str,
    quality: bool,
    images: bool,
    tables: bool,
    citations: bool,
) -> Path:
    """Process a single file with all selected features."""
    # Basic extraction
    extracted_content = pipeline.process_pdf(pdf_file, output_dir)

    # Enhanced features
    if images:
        figures = image_processor.extract_figures_with_captions(pdf_file)
        extracted_content["figures"] = [f.to_dict() for f in figures]

    if tables:
        table_structures = table_processor.extract_tables_with_structure(pdf_file)
        extracted_content["tables"] = [t.to_dict() for t in table_structures]

    if citations:
        bibliography = citation_processor.extract_citations(pdf_file)
        extracted_content["citations"] = bibliography.to_dict()

    if quality:
        quality_report = quality_assessor.assess_extraction_quality(
            pdf_file, extracted_content
        )
        extracted_content["quality_report"] = quality_report.to_dict()

    # Export to specified format
    return format_exporter.export_to_format(extracted_content, format_type, output_dir)


def configure_batch_settings(console: Console) -> Dict[str, Any]:
    """Configure batch processing settings interactively."""
    console.print("\n[bold blue]Batch Processing Configuration[/bold blue]")

    max_workers = int(Prompt.ask("Max workers", default="4"))
    batch_size = int(Prompt.ask("Batch size", default="10"))
    memory_limit = Prompt.ask("Memory limit (e.g., 2GB)", default="2GB")
    timeout = int(Prompt.ask("Timeout (seconds)", default="300"))

    return {
        "max_workers": max_workers,
        "batch_size": batch_size,
        "memory_limit": memory_limit,
        "timeout": timeout,
    }


def display_batch_results(console: Console, results: List[Any]) -> None:
    """Display batch processing results."""
    successful = sum(
        1 for r in results if not hasattr(r, "success_ratio") or r.success_ratio >= 0.5
    )
    total = len(results)

    console.print("\n[bold green]Batch Processing Complete![/bold green]")
    console.print(
        f"Successfully processed: {successful}/{total} files ({successful/total*100:.1f}%)"
    )

    if successful < total:
        console.print("[yellow]Some files had issues. Check logs for details.[/yellow]")


if __name__ == "__main__":
    cli()

if __name__ == "__main__":
    cli()
