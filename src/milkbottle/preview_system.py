"""Interactive Preview System for MilkBottle.

This module provides real-time preview capabilities for extraction results,
allowing users to see what will be extracted before committing to full processing.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

console = Console()


@dataclass
class PreviewConfig:
    """Configuration for preview system."""

    max_preview_size: int = 1000  # Maximum characters to preview
    show_metadata: bool = True
    show_structure: bool = True
    show_quality_metrics: bool = True
    auto_refresh: bool = False
    refresh_interval: float = 2.0  # seconds


@dataclass
class PreviewResult:
    """Result of a preview operation."""

    content: str
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    file_size: int
    extraction_time: float
    confidence_score: float
    warnings: List[str]
    errors: List[str]


class InteractivePreview:
    """Interactive preview system for extraction results."""

    def __init__(self, config: Optional[PreviewConfig] = None):
        """Initialize the preview system."""
        self.config = config or PreviewConfig()
        self.preview_cache: Dict[str, PreviewResult] = {}
        self.live_display: Optional[Live] = None

    def preview_pdf_extraction(
        self, pdf_path: Path, output_dir: Optional[Path] = None
    ) -> PreviewResult:
        """Preview PDF extraction results."""
        from .modules.pdfmilker.extract import extract_text_structured
        from .modules.pdfmilker.quality_assessor import QualityAssessor

        console.print(
            f"[bold cyan]Previewing PDF extraction: {pdf_path.name}[/bold cyan]"
        )

        # Create temporary output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp())

        try:
            # Extract structured content
            start_time = asyncio.get_event_loop().time()
            structured_content = extract_text_structured(pdf_path)
            extraction_time = asyncio.get_event_loop().time() - start_time

            # Assess quality
            quality_assessor = QualityAssessor()
            quality_metrics = quality_assessor.assess_extraction_quality(
                structured_content
            )

            # Create preview content
            preview_content = self._create_pdf_preview(structured_content)

            # Extract metadata
            metadata = {
                "filename": pdf_path.name,
                "file_size": pdf_path.stat().st_size,
                "pages": len(structured_content.get("pages", [])),
                "extraction_time": extraction_time,
                "output_directory": str(output_dir),
            }

            # Create structure summary
            structure = self._analyze_content_structure(structured_content)

            # Calculate confidence score
            confidence_score = quality_metrics.get("overall_confidence", 0.0)

            # Check for warnings and errors
            warnings = []
            errors = []

            if quality_metrics.get("text_quality", 0) < 0.7:
                warnings.append("Text quality is below optimal threshold")

            if not structured_content.get("tables"):
                warnings.append("No tables detected in document")

            if not structured_content.get("images"):
                warnings.append("No images detected in document")

            result = PreviewResult(
                content=preview_content,
                metadata=metadata,
                structure=structure,
                quality_metrics=quality_metrics,
                file_size=pdf_path.stat().st_size,
                extraction_time=extraction_time,
                confidence_score=confidence_score,
                warnings=warnings,
                errors=errors,
            )

            self.preview_cache[str(pdf_path)] = result
            return result

        except Exception as e:
            console.print(f"[red]Error during preview: {e}[/red]")
            return PreviewResult(
                content="Error during extraction",
                metadata={},
                structure={},
                quality_metrics={},
                file_size=0,
                extraction_time=0.0,
                confidence_score=0.0,
                warnings=[],
                errors=[str(e)],
            )

    def _create_pdf_preview(self, structured_content: Dict[str, Any]) -> str:
        """Create a preview of PDF content."""
        preview_parts = []

        # Add title if available
        if structured_content.get("title"):
            preview_parts.append(f"Title: {structured_content['title']}")
            preview_parts.append("")

        # Add abstract if available
        if structured_content.get("abstract"):
            abstract = structured_content["abstract"]
            if len(abstract) > self.config.max_preview_size:
                abstract = abstract[: self.config.max_preview_size] + "..."
            preview_parts.append(f"Abstract: {abstract}")
            preview_parts.append("")

        # Add first few pages
        pages = structured_content.get("pages", [])
        for i, page in enumerate(pages[:3]):  # Show first 3 pages
            page_text = page.get("text", "")
            if len(page_text) > 200:
                page_text = page_text[:200] + "..."
            preview_parts.append(f"Page {i+1}: {page_text}")
            preview_parts.append("")

        # Add summary of other content
        if structured_content.get("tables"):
            preview_parts.append(f"Tables: {len(structured_content['tables'])} found")

        if structured_content.get("images"):
            preview_parts.append(f"Images: {len(structured_content['images'])} found")

        if structured_content.get("math_formulas"):
            preview_parts.append(
                f"Math Formulas: {len(structured_content['math_formulas'])} found"
            )

        return "\n".join(preview_parts)

    def _analyze_content_structure(
        self, structured_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the structure of extracted content."""
        structure = {
            "total_pages": len(structured_content.get("pages", [])),
            "has_title": bool(structured_content.get("title")),
            "has_abstract": bool(structured_content.get("abstract")),
            "has_tables": bool(structured_content.get("tables")),
            "has_images": bool(structured_content.get("images")),
            "has_math": bool(structured_content.get("math_formulas")),
            "has_references": bool(structured_content.get("references")),
            "sections": [],
        }

        # Analyze sections
        pages = structured_content.get("pages", [])
        for page in pages:
            if page.get("sections"):
                structure["sections"].extend(page["sections"])

        return structure

    def display_preview(self, result: PreviewResult) -> None:
        """Display the preview result in an interactive format."""
        # Create main preview panel
        preview_panel = Panel(
            result.content,
            title="[bold]Content Preview[/bold]",
            border_style="blue",
            width=80,
        )

        # Create metadata table
        if self.config.show_metadata:
            metadata_table = Table(title="File Metadata")
            metadata_table.add_column("Property", style="cyan")
            metadata_table.add_column("Value", style="white")

            for key, value in result.metadata.items():
                metadata_table.add_row(key, str(value))

        # Create structure table
        if self.config.show_structure:
            structure_table = Table(title="Content Structure")
            structure_table.add_column("Component", style="cyan")
            structure_table.add_column("Status", style="green")
            structure_table.add_column("Count", style="yellow")

            structure = result.structure
            structure_table.add_row("Pages", "✅", str(structure.get("total_pages", 0)))
            structure_table.add_row(
                "Title",
                "✅" if structure.get("has_title") else "❌",
                "1" if structure.get("has_title") else "0",
            )
            structure_table.add_row(
                "Abstract",
                "✅" if structure.get("has_abstract") else "❌",
                "1" if structure.get("has_abstract") else "0",
            )
            structure_table.add_row(
                "Tables",
                "✅" if structure.get("has_tables") else "❌",
                "Multiple" if structure.get("has_tables") else "0",
            )
            structure_table.add_row(
                "Images",
                "✅" if structure.get("has_images") else "❌",
                "Multiple" if structure.get("has_images") else "0",
            )
            structure_table.add_row(
                "Math Formulas",
                "✅" if structure.get("has_math") else "❌",
                "Multiple" if structure.get("has_math") else "0",
            )

        # Create quality metrics table
        if self.config.show_quality_metrics:
            quality_table = Table(title="Quality Assessment")
            quality_table.add_column("Metric", style="cyan")
            quality_table.add_column("Score", style="green")
            quality_table.add_column("Status", style="yellow")

            metrics = result.quality_metrics
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    status = (
                        "✅ Good"
                        if value > 0.7
                        else "⚠️ Fair" if value > 0.4 else "❌ Poor"
                    )
                    quality_table.add_row(metric, f"{value:.2f}", status)

        # Display warnings and errors
        if result.warnings:
            warnings_panel = Panel(
                "\n".join(f"⚠️ {warning}" for warning in result.warnings),
                title="[bold yellow]Warnings[/bold yellow]",
                border_style="yellow",
            )

        if result.errors:
            errors_panel = Panel(
                "\n".join(f"❌ {error}" for error in result.errors),
                title="[bold red]Errors[/bold red]",
                border_style="red",
            )

        # Display all components
        console.print(preview_panel)
        console.print()

        if self.config.show_metadata:
            console.print(metadata_table)
            console.print()

        if self.config.show_structure:
            console.print(structure_table)
            console.print()

        if self.config.show_quality_metrics:
            console.print(quality_table)
            console.print()

        if result.warnings:
            console.print(warnings_panel)
            console.print()

        if result.errors:
            console.print(errors_panel)
            console.print()

    def interactive_preview_workflow(self, file_path: Path) -> bool:
        """Run interactive preview workflow."""
        console.print(
            f"[bold cyan]Starting Interactive Preview for: {file_path.name}[/bold cyan]"
        )
        console.print()

        # Preview the file
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing file...", total=None)
            result = self.preview_pdf_extraction(file_path)
            progress.update(task, completed=True)

        # Display preview
        self.display_preview(result)

        # Ask user what to do
        console.print("[bold]What would you like to do?[/bold]")
        console.print("[1] Proceed with full extraction")
        console.print("[2] Adjust extraction settings")
        console.print("[3] Export preview only")
        console.print("[4] Cancel")

        choice = Prompt.ask(
            "Enter your choice", choices=["1", "2", "3", "4"], default="1"
        )

        if choice == "1":
            return self._proceed_with_extraction(file_path, result)
        elif choice == "2":
            return self._adjust_settings(file_path, result)
        elif choice == "3":
            return self._export_preview_only(file_path, result)
        else:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return False

    def _proceed_with_extraction(self, file_path: Path, result: PreviewResult) -> bool:
        """Proceed with full extraction."""
        console.print("[green]Proceeding with full extraction...[/green]")
        # This would integrate with the actual extraction pipeline
        return True

    def _adjust_settings(self, file_path: Path, result: PreviewResult) -> bool:
        """Adjust extraction settings."""
        console.print("[yellow]Settings adjustment not yet implemented.[/yellow]")
        return False

    def _export_preview_only(self, file_path: Path, result: PreviewResult) -> bool:
        """Export preview only."""
        output_file = file_path.with_suffix(".preview.json")

        preview_data = {
            "file_path": str(file_path),
            "preview_content": result.content,
            "metadata": result.metadata,
            "structure": result.structure,
            "quality_metrics": result.quality_metrics,
            "confidence_score": result.confidence_score,
            "warnings": result.warnings,
            "errors": result.errors,
        }

        with open(output_file, "w") as f:
            json.dump(preview_data, f, indent=2)

        console.print(f"[green]Preview exported to: {output_file}[/green]")
        return True


# Global preview instance
_preview_system: Optional[InteractivePreview] = None


def get_preview_system() -> InteractivePreview:
    """Get the global preview system instance."""
    global _preview_system
    if _preview_system is None:
        _preview_system = InteractivePreview()
    return _preview_system


def preview_file(file_path: Path) -> bool:
    """Preview a file using the interactive preview system."""
    preview_system = get_preview_system()
    return preview_system.interactive_preview_workflow(file_path)


@click.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", help="Preview configuration file")
def preview_cli(file_path: Path, config: Optional[str]) -> None:
    """Preview extraction results for a file."""
    preview_system = get_preview_system()

    if config:
        # Load configuration from file
        import json

        with open(config, "r") as f:
            config_data = json.load(f)
        preview_system.config = PreviewConfig(**config_data)

    preview_system.interactive_preview_workflow(file_path)


if __name__ == "__main__":
    preview_cli()
