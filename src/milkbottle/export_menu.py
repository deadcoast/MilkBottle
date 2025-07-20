"""Enhanced Export Options Menu for MilkBottle.

This module provides an interactive export options menu with format selection
and previews, allowing users to see what different export formats will look like
before committing to the export.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class ExportFormat:
    """Represents an export format with its configuration."""

    name: str
    extension: str
    description: str
    supported_features: List[str]
    config_options: Dict[str, Any]
    preview_supported: bool = True


@dataclass
class ExportPreview:
    """Represents a preview of an export format."""

    format_name: str
    content: str
    metadata: Dict[str, Any]
    file_size: int
    quality_score: float
    warnings: List[str]
    errors: List[str]


class ExportOptionsMenu:
    """Enhanced export options menu with format selection and previews."""

    def __init__(self):
        """Initialize the export options menu."""
        self.available_formats: Dict[str, ExportFormat] = self._initialize_formats()
        self.selected_formats: List[str] = []
        self.export_config: Dict[str, Any] = {}

    def _initialize_formats(self) -> Dict[str, ExportFormat]:
        """Initialize available export formats."""
        return {
            "txt": ExportFormat(
                name="Plain Text",
                extension=".txt",
                description="Simple text format, good for basic content",
                supported_features=["text", "basic_structure"],
                config_options={
                    "encoding": "utf-8",
                    "line_breaks": True,
                    "preserve_formatting": False,
                },
            ),
            "json": ExportFormat(
                name="JSON",
                extension=".json",
                description="Structured data format, preserves all metadata",
                supported_features=[
                    "text",
                    "tables",
                    "images",
                    "metadata",
                    "structure",
                ],
                config_options={
                    "indent": 2,
                    "include_metadata": True,
                    "include_images": True,
                },
            ),
            "markdown": ExportFormat(
                name="Markdown",
                extension=".md",
                description="Rich text format, good for documentation",
                supported_features=["text", "tables", "basic_images", "structure"],
                config_options={
                    "include_toc": True,
                    "preserve_formatting": True,
                    "image_format": "markdown",
                },
            ),
            "html": ExportFormat(
                name="HTML",
                extension=".html",
                description="Web format, good for online viewing",
                supported_features=["text", "tables", "images", "styling"],
                config_options={
                    "include_css": True,
                    "responsive": True,
                    "include_metadata": True,
                },
            ),
            "latex": ExportFormat(
                name="LaTeX",
                extension=".tex",
                description="Academic format, good for papers and publications",
                supported_features=["text", "tables", "math", "citations"],
                config_options={
                    "document_class": "article",
                    "include_bibliography": True,
                    "math_mode": True,
                },
            ),
            "docx": ExportFormat(
                name="Word Document",
                extension=".docx",
                description="Microsoft Word format, good for editing",
                supported_features=["text", "tables", "images", "styling"],
                config_options={
                    "include_styles": True,
                    "preserve_formatting": True,
                    "include_metadata": True,
                },
            ),
            "pdf": ExportFormat(
                name="PDF",
                extension=".pdf",
                description="Portable document format, good for sharing",
                supported_features=["text", "tables", "images", "styling"],
                config_options={
                    "page_size": "A4",
                    "margins": "1in",
                    "include_toc": True,
                },
            ),
        }

    def show_format_selection(self, content_data: Dict[str, Any]) -> List[str]:
        """Show interactive format selection menu."""
        console.print("\n[bold underline]Export Format Selection[/bold underline]")
        console.print("Select export formats for your content.\n")

        # Display available formats
        format_table = Table(title="Available Export Formats")
        format_table.add_column("ID", style="cyan", justify="center")
        format_table.add_column("Format", style="white")
        format_table.add_column("Extension", style="green")
        format_table.add_column("Features", style="yellow")
        format_table.add_column("Description", style="dim")

        for i, (format_id, format_info) in enumerate(self.available_formats.items(), 1):
            features = ", ".join(format_info.supported_features[:3])
            if len(format_info.supported_features) > 3:
                features += "..."

            format_table.add_row(
                str(i),
                format_info.name,
                format_info.extension,
                features,
                format_info.description,
            )

        console.print(format_table)
        console.print()

        # Get user selection
        console.print(
            "Select formats (comma-separated numbers, or 'all' for all formats):"
        )
        selection = Prompt.ask("Enter your choice", default="1,2")

        if selection.lower() == "all":
            self.selected_formats = list(self.available_formats.keys())
        else:
            selected_indices = []
            for choice in selection.split(","):
                try:
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(self.available_formats):
                        selected_indices.append(idx)
                except ValueError:
                    pass

            format_ids = list(self.available_formats.keys())
            self.selected_formats = [
                format_ids[i] for i in selected_indices if i < len(format_ids)
            ]

        if not self.selected_formats:
            console.print(
                "[yellow]No valid formats selected. Using default (txt, json).[/yellow]"
            )
            self.selected_formats = ["txt", "json"]

        return self.selected_formats

    def show_format_previews(
        self, content_data: Dict[str, Any]
    ) -> Dict[str, ExportPreview]:
        """Show previews for selected formats."""
        console.print("\n[bold underline]Format Previews[/bold underline]")
        console.print("Preview how your content will look in different formats.\n")

        previews = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for format_id in self.selected_formats:
                if format_id not in self.available_formats:
                    continue

                format_info = self.available_formats[format_id]
                task = progress.add_task(
                    f"Generating {format_info.name} preview...", total=None
                )

                try:
                    preview = self._generate_format_preview(format_id, content_data)
                    previews[format_id] = preview
                    progress.update(task, completed=True)
                except Exception as e:
                    console.print(
                        f"[red]Error generating {format_info.name} preview: {e}[/red]"
                    )
                    progress.update(task, completed=True)

        # Display previews
        for format_id, preview in previews.items():
            format_info = self.available_formats[format_id]
            self._display_format_preview(format_info, preview)

        return previews

    def _generate_format_preview(
        self, format_id: str, content_data: Dict[str, Any]
    ) -> ExportPreview:
        """Generate a preview for a specific format."""
        format_info = self.available_formats[format_id]

        # Generate preview content based on format
        if format_id == "txt":
            content = self._generate_txt_preview(content_data)
        elif format_id == "json":
            content = self._generate_json_preview(content_data)
        elif format_id == "markdown":
            content = self._generate_markdown_preview(content_data)
        elif format_id == "html":
            content = self._generate_html_preview(content_data)
        elif format_id == "latex":
            content = self._generate_latex_preview(content_data)
        else:
            content = f"Preview not available for {format_info.name}"

        # Calculate metadata
        metadata = {
            "format": format_id,
            "content_length": len(content),
            "features_supported": format_info.supported_features,
        }

        # Calculate quality score
        quality_score = self._calculate_quality_score(format_id, content_data)

        # Check for warnings and errors
        warnings = []
        errors = []

        if len(content) < 100:
            warnings.append("Content seems very short")

        if format_id in ["html", "latex"] and not content_data.get("tables"):
            warnings.append("No tables found - some features may not be utilized")

        return ExportPreview(
            format_name=format_info.name,
            content=content,
            metadata=metadata,
            file_size=len(content.encode("utf-8")),
            quality_score=quality_score,
            warnings=warnings,
            errors=errors,
        )

    def _generate_txt_preview(self, content_data: Dict[str, Any]) -> str:
        """Generate plain text preview."""
        lines = []

        if content_data.get("title"):
            lines.append(f"Title: {content_data['title']}")
            lines.append("")

        if content_data.get("abstract"):
            lines.append(f"Abstract: {content_data['abstract']}")
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages[:2]):  # Show first 2 pages
            lines.append(f"Page {i+1}:")
            lines.append(
                page.get("text", "")[:200] + "..."
                if len(page.get("text", "")) > 200
                else page.get("text", "")
            )
            lines.append("")

        return "\n".join(lines)

    def _generate_json_preview(self, content_data: Dict[str, Any]) -> str:
        """Generate JSON preview."""
        preview_data = {
            "title": content_data.get("title"),
            "abstract": content_data.get("abstract"),
            "pages_count": len(content_data.get("pages", [])),
            "tables_count": len(content_data.get("tables", [])),
            "images_count": len(content_data.get("images", [])),
            "sample_page": (
                content_data.get("pages", [{}])[0]
                if content_data.get("pages")
                else None
            ),
        }

        return json.dumps(preview_data, indent=2)

    def _generate_markdown_preview(self, content_data: Dict[str, Any]) -> str:
        """Generate Markdown preview."""
        lines = []

        if content_data.get("title"):
            lines.append(f"# {content_data['title']}")
            lines.append("")

        if content_data.get("abstract"):
            lines.append(f"**Abstract:** {content_data['abstract']}")
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages[:2]):  # Show first 2 pages
            lines.append(f"## Page {i+1}")
            lines.append(
                page.get("text", "")[:200] + "..."
                if len(page.get("text", "")) > 200
                else page.get("text", "")
            )
            lines.append("")

        return "\n".join(lines)

    def _generate_html_preview(self, content_data: Dict[str, Any]) -> str:
        """Generate HTML preview."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Document Preview</title>",
            "</head>",
            "<body>",
        ]

        if content_data.get("title"):
            html.append(f"<h1>{content_data['title']}</h1>")

        if content_data.get("abstract"):
            html.append(f"<p><strong>Abstract:</strong> {content_data['abstract']}</p>")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages[:2]):  # Show first 2 pages
            html.append(f"<h2>Page {i+1}</h2>")
            html.append(f"<p>{page.get('text', '')[:200]}...</p>")

        html.extend(["</body>", "</html>"])
        return "\n".join(html)

    def _generate_latex_preview(self, content_data: Dict[str, Any]) -> str:
        """Generate LaTeX preview."""
        lines = ["\\documentclass{article}", "\\begin{document}", ""]

        if content_data.get("title"):
            lines.append(f"\\title{{{content_data['title']}}}")
            lines.append("\\maketitle")
            lines.append("")

        if content_data.get("abstract"):
            lines.append("\\begin{abstract}")
            lines.append(content_data["abstract"])
            lines.append("\\end{abstract}")
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages[:2]):  # Show first 2 pages
            lines.append(f"\\section*{{Page {i+1}}}")
            lines.append(
                page.get("text", "")[:200] + "..."
                if len(page.get("text", "")) > 200
                else page.get("text", "")
            )
            lines.append("")

        lines.extend(["\\end{document}"])
        return "\n".join(lines)

    def _calculate_quality_score(
        self, format_id: str, content_data: Dict[str, Any]
    ) -> float:
        """Calculate quality score for a format based on content."""
        score = 0.5  # Base score

        # Content richness
        if content_data.get("title"):
            score += 0.1
        if content_data.get("abstract"):
            score += 0.1
        if content_data.get("tables"):
            score += 0.1
        if content_data.get("images"):
            score += 0.1
        if content_data.get("math_formulas"):
            score += 0.1

        # Format-specific bonuses
        if format_id == "json" and content_data.get("metadata"):
            score += 0.1
        if format_id == "latex" and content_data.get("math_formulas"):
            score += 0.1
        if format_id == "html" and content_data.get("images"):
            score += 0.1

        return min(score, 1.0)

    def _display_format_preview(
        self, format_info: ExportFormat, preview: ExportPreview
    ) -> None:
        """Display a format preview."""
        # Create preview panel
        preview_panel = Panel(
            (
                preview.content[:500] + "..."
                if len(preview.content) > 500
                else preview.content
            ),
            title=f"[bold]{format_info.name} Preview[/bold]",
            border_style="blue",
            width=80,
        )

        # Create metadata table
        metadata_table = Table(title=f"{format_info.name} Metadata")
        metadata_table.add_column("Property", style="cyan")
        metadata_table.add_column("Value", style="white")

        metadata_table.add_row("File Size", f"{preview.file_size} bytes")
        metadata_table.add_row("Quality Score", f"{preview.quality_score:.2f}")
        metadata_table.add_row("Features", ", ".join(format_info.supported_features))

        console.print(preview_panel)
        console.print(metadata_table)

        # Show warnings and errors
        if preview.warnings:
            warnings_panel = Panel(
                "\n".join(f"⚠️ {warning}" for warning in preview.warnings),
                title="[bold yellow]Warnings[/bold yellow]",
                border_style="yellow",
            )
            console.print(warnings_panel)

        if preview.errors:
            errors_panel = Panel(
                "\n".join(f"❌ {error}" for error in preview.errors),
                title="[bold red]Errors[/bold red]",
                border_style="red",
            )
            console.print(errors_panel)

        console.print()

    def configure_export_options(self) -> Dict[str, Any]:
        """Configure export options for selected formats."""
        console.print("\n[bold underline]Export Configuration[/bold underline]")

        config = {}

        for format_id in self.selected_formats:
            if format_id not in self.available_formats:
                continue

            format_info = self.available_formats[format_id]
            console.print(f"\n[bold]Configuring {format_info.name}[/bold]")

            format_config = {}

            # Configure format-specific options
            for option, default_value in format_info.config_options.items():
                if isinstance(default_value, bool):
                    value = Confirm.ask(f"Enable {option}?", default=default_value)
                elif isinstance(default_value, str):
                    value = Prompt.ask(f"Enter {option}", default=default_value)
                elif isinstance(default_value, int):
                    value = Prompt.ask(f"Enter {option}", default=str(default_value))
                    try:
                        value = int(value)
                    except ValueError:
                        value = default_value
                else:
                    value = default_value

                format_config[option] = value

            config[format_id] = format_config

        self.export_config = config
        return config

    def execute_export(
        self, content_data: Dict[str, Any], output_dir: Path
    ) -> Dict[str, str]:
        """Execute the export with selected formats and configuration."""
        console.print("\n[bold underline]Executing Export[/bold underline]")

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for format_id in self.selected_formats:
                if format_id not in self.available_formats:
                    continue

                format_info = self.available_formats[format_id]
                task = progress.add_task(
                    f"Exporting to {format_info.name}...", total=None
                )

                try:
                    output_file = self._export_to_format(
                        format_id, content_data, output_dir
                    )
                    results[format_id] = str(output_file)
                    progress.update(task, completed=True)
                except Exception as e:
                    console.print(
                        f"[red]Error exporting to {format_info.name}: {e}[/red]"
                    )
                    results[format_id] = f"Error: {e}"
                    progress.update(task, completed=True)

        return results

    def _export_to_format(
        self, format_id: str, content_data: Dict[str, Any], output_dir: Path
    ) -> Path:
        """Export content to a specific format."""
        format_info = self.available_formats[format_id]
        config = self.export_config.get(format_id, {})

        # Generate filename
        title = content_data.get("title", "document")
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_title = safe_title.replace(" ", "_")
        filename = f"{safe_title}{format_info.extension}"
        output_file = output_dir / filename

        # Export based on format
        if format_id == "txt":
            content = self._export_to_txt(content_data, config)
        elif format_id == "json":
            content = self._export_to_json(content_data, config)
        elif format_id == "markdown":
            content = self._export_to_markdown(content_data, config)
        elif format_id == "html":
            content = self._export_to_html(content_data, config)
        elif format_id == "latex":
            content = self._export_to_latex(content_data, config)
        else:
            content = f"Export not implemented for {format_info.name}"

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file

    def _export_to_txt(
        self, content_data: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """Export to plain text format."""
        lines = []

        if content_data.get("title"):
            lines.append(content_data["title"])
            lines.append("=" * len(content_data["title"]))
            lines.append("")

        if content_data.get("abstract"):
            lines.append("ABSTRACT")
            lines.append("-" * 8)
            lines.append(content_data["abstract"])
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages):
            lines.append(f"PAGE {i+1}")
            lines.append("-" * 6)
            lines.append(page.get("text", ""))
            lines.append("")

        return "\n".join(lines)

    def _export_to_json(
        self, content_data: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """Export to JSON format."""
        export_data = content_data.copy()

        if not config.get("include_images", True):
            export_data.pop("images", None)

        indent = config.get("indent", 2)
        return json.dumps(export_data, indent=indent, ensure_ascii=False)

    def _export_to_markdown(
        self, content_data: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """Export to Markdown format."""
        lines = []

        if content_data.get("title"):
            lines.append(f"# {content_data['title']}")
            lines.append("")

        if config.get("include_toc", True):
            lines.append("## Table of Contents")
            lines.append("")
            # Add TOC entries here

        if content_data.get("abstract"):
            lines.append("## Abstract")
            lines.append(content_data["abstract"])
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages):
            lines.append(f"## Page {i+1}")
            lines.append(page.get("text", ""))
            lines.append("")

        return "\n".join(lines)

    def _export_to_html(
        self, content_data: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """Export to HTML format."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>"
            + (content_data.get("title", "Document") or "Document")
            + "</title>",
        ]

        if config.get("include_css", True):
            html.append("<style>")
            html.append("body { font-family: Arial, sans-serif; margin: 40px; }")
            html.append("h1 { color: #333; }")
            html.append("h2 { color: #666; }")
            html.append("</style>")

        html.append("</head>")
        html.append("<body>")

        if content_data.get("title"):
            html.append(f"<h1>{content_data['title']}</h1>")

        if content_data.get("abstract"):
            html.append(f"<p><strong>Abstract:</strong> {content_data['abstract']}</p>")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages):
            html.append(f"<h2>Page {i+1}</h2>")
            html.append(f"<p>{page.get('text', '')}</p>")

        html.extend(["</body>", "</html>"])
        return "\n".join(html)

    def _export_to_latex(
        self, content_data: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """Export to LaTeX format."""
        lines = [
            "\\documentclass{article}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{geometry}",
            "\\geometry{margin=1in}",
            "\\begin{document}",
            "",
        ]

        if content_data.get("title"):
            lines.append(f"\\title{{{content_data['title']}}}")
            lines.append("\\maketitle")
            lines.append("")

        if content_data.get("abstract"):
            lines.append("\\begin{abstract}")
            lines.append(content_data["abstract"])
            lines.append("\\end{abstract}")
            lines.append("")

        pages = content_data.get("pages", [])
        for i, page in enumerate(pages):
            lines.append(f"\\section*{{Page {i+1}}}")
            lines.append(page.get("text", ""))
            lines.append("")

        lines.extend(["\\end{document}"])
        return "\n".join(lines)


def get_export_menu() -> ExportOptionsMenu:
    """Get the global export menu instance."""
    return ExportOptionsMenu()


def export_content_interactive(
    content_data: Dict[str, Any], output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """Export content using the interactive export menu."""
    if output_dir is None:
        output_dir = Path("exports")

    export_menu = get_export_menu()

    # Step 1: Format selection
    selected_formats = export_menu.show_format_selection(content_data)

    # Step 2: Format previews
    previews = export_menu.show_format_previews(content_data)

    # Step 3: Configuration
    config = export_menu.configure_export_options()

    # Step 4: Execute export
    results = export_menu.execute_export(content_data, output_dir)

    return results


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="exports",
    help="Output directory",
)
def export_cli(input_file: Path, output_dir: Path) -> None:
    """Export content using the interactive export menu."""
    try:
        # Load content data (this would integrate with existing extraction)
        content_data = {
            "title": "Sample Document",
            "abstract": "This is a sample document for export testing.",
            "pages": [
                {"text": "This is the content of page 1."},
                {"text": "This is the content of page 2."},
            ],
        }

        results = export_content_interactive(content_data, output_dir)

        console.print("\n[bold green]Export completed successfully![/bold green]")
        console.print(f"Files saved to: {output_dir}")

        for format_id, result in results.items():
            if result.startswith("Error:"):
                console.print(f"[red]{format_id}: {result}[/red]")
            else:
                console.print(f"[green]{format_id}: {result}[/green]")

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        raise


if __name__ == "__main__":
    export_cli()
