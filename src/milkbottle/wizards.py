"""Configuration Wizards for MilkBottle.

This module provides guided setup wizards for complex configurations,
making it easier for users to configure services and modules.
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class ConfigurationWizard:
    """Base class for configuration wizards."""

    def __init__(self):
        """Initialize the wizard."""
        self.config: Dict[str, Any] = {}
        self.current_step = 0
        self.total_steps = 0

    def run(self) -> Dict[str, Any]:
        """Run the configuration wizard."""
        raise NotImplementedError("Subclasses must implement run()")

    def display_progress(self) -> None:
        """Display current progress."""
        progress = (self.current_step / self.total_steps) * 100
        console.print(
            f"[dim]Progress: {progress:.1f}% ({self.current_step}/{self.total_steps})[/dim]"
        )

    def save_config(self, config_path: Path) -> None:
        """Save configuration to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

        console.print(f"[green]Configuration saved to: {config_path}[/green]")


class PDFmilkerWizard(ConfigurationWizard):
    """Wizard for configuring PDFmilker."""

    def __init__(self):
        """Initialize the PDFmilker wizard."""
        super().__init__()
        self.total_steps = 6

    def run(self) -> Dict[str, Any]:
        """Run the PDFmilker configuration wizard."""
        console.print(
            Panel(
                "[bold cyan]PDFmilker Configuration Wizard[/bold cyan]\n"
                "This wizard will help you configure PDFmilker for optimal performance.\n"
                "You can skip any step by pressing Enter to use defaults.",
                border_style="blue",
            )
        )

        # Step 1: Basic Settings
        self.current_step = 1
        self._configure_basic_settings()

        # Step 2: Output Settings
        self.current_step = 2
        self._configure_output_settings()

        # Step 3: Service Configuration
        self.current_step = 3
        self._configure_services()

        # Step 4: Quality Settings
        self.current_step = 4
        self._configure_quality_settings()

        # Step 5: Performance Settings
        self.current_step = 5
        self._configure_performance_settings()

        # Step 6: Validation and Save
        self.current_step = 6
        self._validate_and_save()

        return self.config

    def _configure_basic_settings(self) -> None:
        """Configure basic settings."""
        self.display_progress()
        console.print("\n[bold]Step 1: Basic Settings[/bold]")

        # Output directory
        default_output = "extracted"
        output_dir = Prompt.ask(
            "Output directory for extracted files", default=default_output
        )
        self.config["output_dir"] = output_dir

        # Verbose mode
        verbose = Confirm.ask("Enable verbose output?", default=False)
        self.config["verbose"] = verbose

        # Dry run mode
        dry_run = Confirm.ask("Enable dry run mode?", default=False)
        self.config["dry_run"] = dry_run

    def _configure_output_settings(self) -> None:
        """Configure output settings."""
        self.display_progress()
        console.print("\n[bold]Step 2: Output Settings[/bold]")

        # Output formats
        console.print("Available output formats:")
        formats = ["txt", "json", "markdown", "html", "latex", "docx"]
        for i, fmt in enumerate(formats, 1):
            console.print(f"  {i}. {fmt}")

        format_choice = Prompt.ask(
            "Select output formats (comma-separated numbers)", default="1,2"
        )

        selected_formats = []
        for choice in format_choice.split(","):
            with contextlib.suppress(ValueError):
                idx = int(choice.strip()) - 1
                if 0 <= idx < len(formats):
                    selected_formats.append(formats[idx])
        if not selected_formats:
            selected_formats = ["txt", "json"]

        self.config["formats"] = selected_formats

        # Include images
        include_images = Confirm.ask("Include extracted images?", default=True)
        self.config["include_images"] = include_images

        # Include tables
        include_tables = Confirm.ask("Include extracted tables?", default=True)
        self.config["include_tables"] = include_tables

    def _configure_services(self) -> None:
        """Configure external services."""
        self.display_progress()
        console.print("\n[bold]Step 3: Service Configuration[/bold]")

        self.config["services"] = {}

        # Grobid service
        console.print("\n[bold]Grobid Service (for enhanced text extraction)[/bold]")
        if use_grobid := Confirm.ask("Use Grobid service?", default=False):
            grobid_url = Prompt.ask(
                "Grobid service URL", default="http://localhost:8070"
            )
            self.config["services"]["grobid"] = {
                "enabled": True,
                "url": grobid_url,
                "timeout": 30,
            }
            console.print(f"[green]✅ Grobid service configured: {grobid_url}[/green]")
        else:
            self.config["services"]["grobid"] = {"enabled": False}
            console.print("[yellow]⚠️ Grobid service disabled[/yellow]")

        # MathPix service
        console.print("\n[bold]MathPix Service (for math formula extraction)[/bold]")
        if use_mathpix := Confirm.ask("Use MathPix service?", default=False):
            mathpix_app_id = Prompt.ask("MathPix App ID")
            mathpix_app_key = Prompt.ask("MathPix App Key", password=True)

            self.config["services"]["mathpix"] = {
                "enabled": True,
                "app_id": mathpix_app_id,
                "app_key": mathpix_app_key,
                "timeout": 30,
            }
            console.print(
                f"[green]✅ MathPix service configured: {mathpix_app_id}[/green]"
            )
        else:
            self.config["services"]["mathpix"] = {"enabled": False}
            console.print("[yellow]⚠️ MathPix service disabled[/yellow]")

    def _configure_quality_settings(self) -> None:
        """Configure quality assessment settings."""
        self.display_progress()
        console.print("\n[bold]Step 4: Quality Settings[/bold]")

        # Enable quality assessment
        enable_quality = Confirm.ask("Enable quality assessment?", default=True)
        self.config["quality_assessment"] = {"enabled": enable_quality}

        if enable_quality:
            # Quality thresholds
            text_threshold = Prompt.ask(
                "Text quality threshold (0.0-1.0)", default="0.7"
            )
            try:
                self.config["quality_assessment"]["text_threshold"] = float(
                    text_threshold
                )
            except ValueError:
                self.config["quality_assessment"]["text_threshold"] = 0.7

            # Confidence threshold
            confidence_threshold = Prompt.ask(
                "Confidence threshold (0.0-1.0)", default="0.8"
            )
            try:
                self.config["quality_assessment"]["confidence_threshold"] = float(
                    confidence_threshold
                )
            except ValueError:
                self.config["quality_assessment"]["confidence_threshold"] = 0.8

    def _configure_performance_settings(self) -> None:
        """Configure performance settings."""
        self.display_progress()
        console.print("\n[bold]Step 5: Performance Settings[/bold]")

        # Batch processing
        enable_batch = Confirm.ask("Enable batch processing?", default=True)
        self.config["batch_processing"] = {"enabled": enable_batch}

        if enable_batch:
            max_workers = Prompt.ask("Maximum parallel workers", default="4")
            try:
                self.config["batch_processing"]["max_workers"] = int(max_workers)
            except ValueError:
                self.config["batch_processing"]["max_workers"] = 4

        # Memory management
        max_memory = Prompt.ask("Maximum memory usage (MB)", default="1024")
        try:
            self.config["max_memory_mb"] = int(max_memory)
        except ValueError:
            self.config["max_memory_mb"] = 1024

    def _validate_and_save(self) -> None:
        """Validate configuration and save."""
        self.display_progress()
        console.print("\n[bold]Step 6: Validation and Save[/bold]")

        # Display configuration summary
        console.print("\n[bold]Configuration Summary:[/bold]")

        summary_table = Table()
        summary_table.add_column("Setting", style="cyan")
        summary_table.add_column("Value", style="white")

        for key, value in self.config.items():
            if isinstance(value, dict):
                summary_table.add_row(key, "Configured")
            else:
                summary_table.add_row(key, str(value))

        console.print(summary_table)

        if is_valid := self._validate_configuration():
            console.print("[green]✅ Configuration validation passed[/green]")
            # Save configuration
            config_path = Path("pdfmilker_config.toml")
            if save_config := Confirm.ask(
                f"Save configuration to {config_path}?", default=True
            ):
                self.save_config(config_path)
                console.print(f"[green]✅ Configuration saved to {config_path}[/green]")
                console.print(
                    "[green]Configuration wizard completed successfully![/green]"
                )
            else:
                console.print("[yellow]⚠️ Configuration not saved.[/yellow]")
        else:
            console.print(
                "[red]❌ Configuration validation failed. Please review settings.[/red]"
            )

    def _validate_configuration(self) -> bool:
        """Validate the configuration."""
        errors = []

        # Check output directory
        if not self.config.get("output_dir"):
            errors.append("Output directory is required")

        # Check service configurations
        services = self.config.get("services", {})

        if services.get("grobid", {}).get("enabled"):
            grobid_url = services["grobid"].get("url")
            if not grobid_url:
                errors.append("Grobid URL is required when Grobid is enabled")

        if services.get("mathpix", {}).get("enabled"):
            if not services["mathpix"].get("app_id"):
                errors.append("MathPix App ID is required when MathPix is enabled")
            if not services["mathpix"].get("app_key"):
                errors.append("MathPix App Key is required when MathPix is enabled")

        if errors:
            console.print("[red]Validation errors:[/red]")
            for error in errors:
                console.print(f"  ❌ {error}")
            return False

        return True


class VenvMilkerWizard(ConfigurationWizard):
    """Wizard for configuring VenvMilker."""

    def __init__(self):
        """Initialize the VenvMilker wizard."""
        super().__init__()
        self.total_steps = 4

    def run(self) -> Dict[str, Any]:
        """Run the VenvMilker configuration wizard."""
        console.print(
            Panel(
                "[bold cyan]VenvMilker Configuration Wizard[/bold cyan]\n"
                "This wizard will help you configure VenvMilker for virtual environment management.\n"
                "You can skip any step by pressing Enter to use defaults.",
                border_style="blue",
            )
        )

        # Step 1: Python Configuration
        self.current_step = 1
        self._configure_python()

        # Step 2: Package Management
        self.current_step = 2
        self._configure_packages()

        # Step 3: Template Settings
        self.current_step = 3
        self._configure_templates()

        # Step 4: Validation and Save
        self.current_step = 4
        self._validate_and_save()

        return self.config

    def _configure_python(self) -> None:
        """Configure Python settings."""
        self.display_progress()
        console.print("\n[bold]Step 1: Python Configuration[/bold]")

        # Python version
        python_version = Prompt.ask("Python version to use", default="3.11")
        self.config["python"] = python_version

        if use_system_python := Confirm.ask("Use system Python?", default=True):
            self.config["python_path"] = None
            console.print("[green]✅ Using system Python[/green]")
        else:
            python_path = Prompt.ask("Custom Python path")
            self.config["python_path"] = python_path
            console.print(f"[green]✅ Using custom Python: {python_path}[/green]")

    def _configure_packages(self) -> None:
        """Configure package management."""
        self.display_progress()
        console.print("\n[bold]Step 2: Package Management[/bold]")

        # Default packages
        default_packages = Prompt.ask(
            "Default packages to install (comma-separated)", default="rich,typer"
        )
        self.config["install"] = [pkg.strip() for pkg in default_packages.split(",")]

        # Snapshot requirements
        snapshot = Confirm.ask("Create requirements snapshot?", default=True)
        self.config["snapshot"] = snapshot

        # Upgrade packages
        upgrade = Confirm.ask("Upgrade existing packages?", default=False)
        self.config["upgrade"] = upgrade

    def _configure_templates(self) -> None:
        """Configure template settings."""
        self.display_progress()
        console.print("\n[bold]Step 3: Template Settings[/bold]")

        # Use templates
        use_templates = Confirm.ask("Use project templates?", default=False)
        self.config["use_templates"] = use_templates

        if use_templates:
            template_name = Prompt.ask("Default template name", default="basic")
            self.config["template"] = template_name

    def _validate_and_save(self) -> None:
        """Validate configuration and save."""
        self.display_progress()
        console.print("\n[bold]Step 4: Validation and Save[/bold]")

        # Display configuration summary
        console.print("\n[bold]Configuration Summary:[/bold]")

        summary_table = Table()
        summary_table.add_column("Setting", style="cyan")
        summary_table.add_column("Value", style="white")

        for key, value in self.config.items():
            if isinstance(value, list):
                summary_table.add_row(key, ", ".join(value))
            else:
                summary_table.add_row(key, str(value))

        console.print(summary_table)

        # Save configuration
        config_path = Path("venvmilker_config.toml")
        if save_config := Confirm.ask(
            f"Save configuration to {config_path}?", default=True
        ):
            self.save_config(config_path)
            console.print(f"[green]✅ Configuration saved to {config_path}[/green]")
            console.print("[green]Configuration wizard completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Configuration not saved.[/yellow]")


class FontMilkerWizard(ConfigurationWizard):
    """Wizard for configuring FontMilker."""

    def __init__(self):
        """Initialize the FontMilker wizard."""
        super().__init__()
        self.total_steps = 3

    def run(self) -> Dict[str, Any]:
        """Run the FontMilker configuration wizard."""
        console.print(
            Panel(
                "[bold cyan]FontMilker Configuration Wizard[/bold cyan]\n"
                "This wizard will help you configure FontMilker for font extraction and management.\n"
                "You can skip any step by pressing Enter to use defaults.",
                border_style="blue",
            )
        )

        # Step 1: Extraction Settings
        self.current_step = 1
        self._configure_extraction()

        # Step 2: Analysis Settings
        self.current_step = 2
        self._configure_analysis()

        # Step 3: Validation and Save
        self.current_step = 3
        self._validate_and_save()

        return self.config

    def _configure_extraction(self) -> None:
        """Configure extraction settings."""
        self.display_progress()
        console.print("\n[bold]Step 1: Extraction Settings[/bold]")

        # Output directory
        output_dir = Prompt.ask("Output directory for extracted fonts", default="fonts")
        self.config["output_dir"] = output_dir

        # Supported formats
        console.print("Supported font formats:")
        formats = ["ttf", "otf", "woff", "woff2", "eot"]
        for i, fmt in enumerate(formats, 1):
            console.print(f"  {i}. {fmt}")

        format_choice = Prompt.ask(
            "Select formats to extract (comma-separated numbers)", default="1,2"
        )

        selected_formats = []
        for choice in format_choice.split(","):
            with contextlib.suppress(ValueError):
                idx = int(choice.strip()) - 1
                if 0 <= idx < len(formats):
                    selected_formats.append(formats[idx])
        if not selected_formats:
            selected_formats = ["ttf", "otf"]

        self.config["extract_formats"] = selected_formats

    def _configure_analysis(self) -> None:
        """Configure analysis settings."""
        self.display_progress()
        console.print("\n[bold]Step 2: Analysis Settings[/bold]")

        # Enable analysis
        enable_analysis = Confirm.ask("Enable font analysis?", default=True)
        self.config["analyze_fonts"] = enable_analysis

        if enable_analysis:
            # Analysis depth
            analysis_depth = Prompt.ask(
                "Analysis depth (basic, detailed, full)", default="detailed"
            )
            self.config["analysis_depth"] = analysis_depth

            # Generate reports
            generate_reports = Confirm.ask("Generate analysis reports?", default=True)
            self.config["generate_reports"] = generate_reports

    def _validate_and_save(self) -> None:
        """Validate configuration and save."""
        self.display_progress()
        console.print("\n[bold]Step 3: Validation and Save[/bold]")

        # Display configuration summary
        console.print("\n[bold]Configuration Summary:[/bold]")

        summary_table = Table()
        summary_table.add_column("Setting", style="cyan")
        summary_table.add_column("Value", style="white")

        for key, value in self.config.items():
            if isinstance(value, list):
                summary_table.add_row(key, ", ".join(value))
            else:
                summary_table.add_row(key, str(value))

        console.print(summary_table)

        # Save configuration
        config_path = Path("fontmilker_config.toml")
        if save_config := Confirm.ask(
            f"Save configuration to {config_path}?", default=True
        ):
            self.save_config(config_path)
            console.print(f"[green]✅ Configuration saved to {config_path}[/green]")
            console.print("[green]Configuration wizard completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Configuration not saved.[/yellow]")


def run_wizard(wizard_type: str) -> Dict[str, Any]:
    """Run a specific configuration wizard."""
    wizards = {
        "pdfmilker": PDFmilkerWizard,
        "venvmilker": VenvMilkerWizard,
        "fontmilker": FontMilkerWizard,
    }

    if wizard_type not in wizards:
        raise ValueError(f"Unknown wizard type: {wizard_type}")

    wizard_class = wizards[wizard_type]
    wizard = wizard_class()
    return wizard.run()


@click.command()
@click.argument(
    "wizard_type", type=click.Choice(["pdfmilker", "venvmilker", "fontmilker"])
)
def wizard_cli(wizard_type: str) -> None:
    """Run a configuration wizard."""
    try:
        config = run_wizard(wizard_type)
        console.print(
            f"[green]✅ Wizard completed successfully! Generated {len(config)} configuration items[/green]"
        )
    except Exception as e:
        console.print(f"[red]❌ Wizard failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    wizard_cli()
