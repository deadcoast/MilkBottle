"""CLI interface for MilkBottle Plugin SDK."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import (
    build_plugin,
    create_plugin,
    get_sdk,
    list_templates,
    package_plugin,
    test_plugin,
    validate_plugin,
)

console = Console()


@click.group()
def cli():
    """MilkBottle Plugin SDK - Development tools for plugin creators."""
    pass


@cli.command()
@click.argument("name")
@click.option("--template", "-t", default="basic", help="Template to use")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory")
@click.option("--description", "-d", help="Plugin description")
@click.option("--author", "-a", help="Plugin author")
@click.option("--email", "-e", help="Author email")
@click.option("--license", "-l", default="MIT", help="License")
@click.option("--version", "-v", default="1.0.0", help="Version")
@click.option("--init-git", is_flag=True, help="Initialize git repository")
def create(
    name: str,
    template: str,
    output_dir: str,
    description: str,
    author: str,
    email: str,
    license: str,
    version: str,
    init_git: bool,
):
    """Create a new plugin."""
    try:
        output_path = Path(output_dir) if output_dir else None

        success = create_plugin(
            name=name,
            template=template,
            output_dir=output_path,
            description=description,
            author=author,
            email=email,
            license=license,
            version=version,
            init_git=init_git,
        )

        if success:
            console.print(f"[green]✓ Successfully created plugin: {name}[/green]")
        else:
            console.print(f"[red]✗ Failed to create plugin: {name}[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error creating plugin: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--format",
    "-f",
    default="detailed",
    type=click.Choice(["simple", "detailed"]),
    help="Output format",
)
def validate(plugin_path: str, format: str):
    """Validate a plugin."""
    try:
        path = Path(plugin_path)
        results = validate_plugin(path)

        if format == "simple":
            if results["valid"]:
                console.print(
                    f"[green]✓ Plugin is valid (Score: {results['score']:.1%})[/green]"
                )
            else:
                console.print(
                    f"[red]✗ Plugin is invalid (Score: {results['score']:.1%})[/red]"
                )
                exit(1)
        else:
            # Detailed output
            sdk = get_sdk()
            sdk.validator.print_validation_report(results)

    except Exception as e:
        console.print(f"[red]Error validating plugin: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "-t",
    default="all",
    type=click.Choice(["unit", "integration", "performance", "all"]),
    help="Type of tests to run",
)
@click.option(
    "--format",
    "-f",
    default="detailed",
    type=click.Choice(["simple", "detailed"]),
    help="Output format",
)
def test(plugin_path: str, type: str, format: str):
    """Test a plugin."""
    try:
        path = Path(plugin_path)
        results = test_plugin(path, type)

        if format == "simple":
            if results["success"]:
                console.print(
                    f"[green]✓ Tests passed ({results['tests_passed']}/{results['tests_run']})[/green]"
                )
            else:
                console.print(
                    f"[red]✗ Tests failed ({results['tests_failed']} failed)[/red]"
                )
                exit(1)
        else:
            # Detailed output
            sdk = get_sdk()
            sdk.tester.print_test_report(results)

    except Exception as e:
        console.print(f"[red]Error testing plugin: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", type=click.Path(), help="Output path")
@click.option(
    "--format",
    "-f",
    default="zip",
    type=click.Choice(["zip", "tar.gz", "wheel"]),
    help="Package format",
)
def package(plugin_path: str, output: str, format: str):
    """Package a plugin for distribution."""
    try:
        path = Path(plugin_path)
        output_path = Path(output) if output else None

        success = package_plugin(path, output_path, format)

        if success:
            console.print("[green]✓ Successfully packaged plugin[/green]")
        else:
            console.print("[red]✗ Failed to package plugin[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error packaging plugin: {e}[/red]")
        exit(1)


@cli.command()
def templates():
    """List available templates."""
    try:
        templates_list = list_templates()

        if not templates_list:
            console.print("[yellow]No templates available[/yellow]")
            return

        table = Table(title="Available Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="magenta")
        table.add_column("Version", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Tags", style="blue")

        for template in templates_list:
            tags = ", ".join(template.get("tags", []))
            table.add_row(
                template.get("name", ""),
                template.get("description", ""),
                template.get("version", ""),
                template.get("author", ""),
                tags,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "-t",
    default="development",
    type=click.Choice(["development", "production"]),
    help="Build type",
)
def build(plugin_path: str, type: str):
    """Build a plugin (validate, test, and optionally package)."""
    try:
        path = Path(plugin_path)
        success = build_plugin(path, type)

        if success:
            console.print(f"[green]✓ Successfully built plugin ({type})[/green]")
        else:
            console.print("[red]✗ Failed to build plugin[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error building plugin: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
def info(plugin_path: str):
    """Get comprehensive information about a plugin."""
    try:
        path = Path(plugin_path)
        sdk = get_sdk()
        info = sdk.get_plugin_info(path)

        console.print("\n[bold blue]Plugin Information[/bold blue]")
        console.print(f"Path: {info['path']}")
        console.print(f"Exists: {info['exists']}")

        if info["exists"]:
            if "validation" in info and info["validation"]:
                console.print("\n[bold green]Validation:[/bold green]")
                console.print(f"  Valid: {info['validation'].get('valid', False)}")
                console.print(f"  Score: {info['validation'].get('score', 0):.1%}")

            if "tests" in info and info["tests"]:
                console.print("\n[bold green]Tests:[/bold green]")
                console.print(f"  Success: {info['tests'].get('success', False)}")
                console.print(f"  Tests Run: {info['tests'].get('tests_run', 0)}")
                console.print(f"  Tests Passed: {info['tests'].get('tests_passed', 0)}")
                console.print(f"  Tests Failed: {info['tests'].get('tests_failed', 0)}")

            if "metadata" in info and info["metadata"]:
                console.print("\n[bold green]Metadata:[/bold green]")
                for key, value in info["metadata"].items():
                    console.print(f"  {key}: {value}")
        else:
            console.print("[red]Plugin does not exist[/red]")

    except Exception as e:
        console.print(f"[red]Error getting plugin info: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "-t",
    default="unit",
    type=click.Choice(["unit", "integration", "performance"]),
    help="Type of test template to create",
)
def create_tests(plugin_path: str, type: str):
    """Create test templates for a plugin."""
    try:
        path = Path(plugin_path)
        sdk = get_sdk()

        success = sdk.tester.create_test_template(path, type)

        if success:
            console.print(f"[green]✓ Successfully created {type} test template[/green]")
        else:
            console.print(f"[red]✗ Failed to create {type} test template[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error creating test template: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("plugin_path", type=click.Path(exists=True, file_okay=False))
def create_manifest(plugin_path: str):
    """Create a manifest file for a plugin."""
    try:
        path = Path(plugin_path)
        sdk = get_sdk()

        success = sdk.packager.create_manifest(path)

        if success:
            console.print("[green]✓ Successfully created manifest file[/green]")
        else:
            console.print("[red]✗ Failed to create manifest file[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error creating manifest: {e}[/red]")
        exit(1)


@cli.command()
@click.argument("template_name")
@click.argument("template_path", type=click.Path(exists=True, file_okay=False))
@click.option("--description", "-d", help="Template description")
def create_template(template_name: str, template_path: str, description: str):
    """Create a new plugin template."""
    try:
        path = Path(template_path)
        sdk = get_sdk()

        success = sdk.create_template(template_name, path, description or "")

        if success:
            console.print(
                f"[green]✓ Successfully created template: {template_name}[/green]"
            )
        else:
            console.print(f"[red]✗ Failed to create template: {template_name}[/red]")
            exit(1)

    except Exception as e:
        console.print(f"[red]Error creating template: {e}[/red]")
        exit(1)


@cli.command()
def version():
    """Show SDK version."""
    console.print("[blue]MilkBottle Plugin SDK v1.0.0[/blue]")


if __name__ == "__main__":
    cli()
