"""MilkBottle CLI - Modular CLI Toolbox.

This module provides the main CLI interface for MilkBottle, a modular
command-line toolbox with bottle-based architecture.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .advanced_analytics import get_advanced_analytics
from .enterprise_features import get_enterprise_features
from .export_menu import get_export_menu
from .preview_system import get_preview_system
from .registry import get_registry
from .wizards import run_wizard

console = Console()
logger = logging.getLogger("milkbottle.cli")


def _show_main_menu() -> None:
    """Display the main menu."""
    menu_text = """
[bold cyan]MilkBottle CLI Toolbox[/bold cyan]

[bold]Available Options:[/bold]
1.  List available bottles
2.  Execute a bottle
3.  Show bottle information
4.  Interactive preview system
5.  Configuration wizards
6.  Advanced analytics
7.  Export options menu
8.  REST API server
9.  Enterprise features
0.  Exit

[dim]Enter your choice (0-9):[/dim]
"""
    console.print(Panel(menu_text, title="Main Menu", border_style="blue"))


def _show_enterprise_menu() -> None:
    """Display the enterprise features menu."""
    enterprise = get_enterprise_features()

    if enterprise.current_user:
        menu_text = f"""
[bold cyan]Enterprise Features[/bold cyan]
[green]Logged in as: {enterprise.current_user.username} ({enterprise.current_user.role.value})[/green]

[bold]Available Options:[/bold]
1.  User management
2.  Audit reports
3.  Logout
0.  Back to main menu

[dim]Enter your choice (0-3):[/dim]
"""
    else:
        menu_text = """
[bold cyan]Enterprise Features[/bold cyan]
[red]Not logged in[/red]

[bold]Available Options:[/bold]
1.  Login
2.  Setup enterprise features
0.  Back to main menu

[dim]Enter your choice (0-2):[/dim]
"""

    console.print(Panel(menu_text, title="Enterprise Menu", border_style="blue"))


def _handle_enterprise_features() -> None:
    """Handle enterprise features menu."""
    enterprise = get_enterprise_features()

    while True:
        _show_enterprise_menu()
        choice = Prompt.ask("Choice", choices=["0", "1", "2", "3"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            if enterprise.current_user:
                _handle_user_management()
            else:
                _handle_login()
        elif choice == "2":
            if enterprise.current_user:
                _handle_audit_reports()
            else:
                _handle_setup_enterprise()
        elif choice == "3" and enterprise.current_user:
            enterprise.logout()
            console.print("[green]Logged out successfully![/green]")


def _handle_login() -> None:
    """Handle user login."""
    console.print("\n[bold cyan]Login[/bold cyan]")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)

    enterprise = get_enterprise_features()
    if enterprise.login(username, password):
        console.print(f"[green]Welcome, {username}![/green]")
    else:
        console.print("[red]Login failed. Invalid credentials.[/red]")


def _handle_setup_enterprise() -> None:
    """Handle enterprise features setup."""
    console.print("\n[bold cyan]Enterprise Features Setup[/bold cyan]")
    console.print("Setting up user management and audit logging...\n")

    enterprise = get_enterprise_features()

    # Check if admin user exists
    admin_user = enterprise.user_manager.get_user("admin")
    if admin_user:
        console.print("[green]Admin user already exists.[/green]")
        return

    # Create admin user
    console.print("Creating initial admin user...")
    username = Prompt.ask("Admin username", default="admin")
    email = Prompt.ask("Admin email", default="admin@milkbottle.local")
    password = Prompt.ask("Admin password", password=True)

    try:
        from .enterprise_features import create_admin_user

        create_admin_user(username, email, password)
        console.print(f"[green]Admin user '{username}' created successfully![/green]")
        console.print("You can now log in using the enterprise features.")
    except Exception as e:
        console.print(f"[red]Failed to create admin user: {e}[/red]")


def _handle_user_management() -> None:
    """Handle user management."""
    enterprise = get_enterprise_features()

    if not enterprise.check_permission("user_manage"):
        console.print("[red]You don't have permission to manage users.[/red]")
        return

    console.print("\n[bold cyan]User Management[/bold cyan]")

    while True:
        console.print("\n1. List users")
        console.print("2. Create user")
        console.print("3. Update user")
        console.print("4. Delete user")
        console.print("0. Back")

        choice = Prompt.ask("Choice", choices=["0", "1", "2", "3", "4"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            _list_users()
        elif choice == "2":
            _create_user()
        elif choice == "3":
            _update_user()
        elif choice == "4":
            _delete_user()


def _list_users() -> None:
    """List all users."""
    enterprise = get_enterprise_features()
    user_list = enterprise.user_manager.list_users()

    if not user_list:
        console.print("No users found.")
        return

    table = Table(title="Users")
    table.add_column("Username", style="cyan")
    table.add_column("Email", style="green")
    table.add_column("Role", style="yellow")
    table.add_column("Status", style="red")
    table.add_column("Created", style="dim")

    for user in user_list:
        status = "Active" if user.is_active else "Inactive"
        table.add_row(
            user.username,
            user.email,
            user.role.value,
            status,
            user.created_at.strftime("%Y-%m-%d"),
        )

    console.print(table)


def _create_user() -> None:
    """Create a new user."""
    console.print("\n[bold cyan]Create User[/bold cyan]")

    username = Prompt.ask("Username")
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)

    # Role selection
    console.print("\nAvailable roles:")
    console.print("1. admin - Full access")
    console.print("2. manager - Management access")
    console.print("3. user - Standard access")
    console.print("4. guest - Limited access")

    role_choice = Prompt.ask("Role", choices=["1", "2", "3", "4"], default="3")
    role_map = {"1": "admin", "2": "manager", "3": "user", "4": "guest"}

    try:
        from .enterprise_features import UserRole

        role = UserRole(role_map[role_choice])

        enterprise = get_enterprise_features()
        enterprise.user_manager.create_user(username, email, password, role)
        console.print(f"[green]User '{username}' created successfully![/green]")
    except Exception as e:
        console.print(f"[red]Failed to create user: {e}[/red]")


def _update_user() -> None:
    """Update a user."""
    console.print("\n[bold cyan]Update User[/bold cyan]")

    username = Prompt.ask("Username to update")
    enterprise = get_enterprise_features()

    user = enterprise.user_manager.get_user(username)
    if not user:
        console.print(f"[red]User '{username}' not found.[/red]")
        return

    console.print(f"Current user: {user.username} ({user.role.value})")
    console.print("Leave blank to keep current value")

    email = Prompt.ask("New email", default=user.email)
    if email == user.email:
        email = None

    # Role selection
    console.print("\nAvailable roles:")
    console.print("1. admin - Full access")
    console.print("2. manager - Management access")
    console.print("3. user - Standard access")
    console.print("4. guest - Limited access")
    console.print("0. Keep current role")

    role_choice = Prompt.ask("New role", choices=["0", "1", "2", "3", "4"], default="0")
    role = None
    if role_choice != "0":
        role_map = {"1": "admin", "2": "manager", "3": "user", "4": "guest"}
        from .enterprise_features import UserRole

        role = UserRole(role_map[role_choice])

    try:
        enterprise.user_manager.update_user(username, email=email, role=role)
        console.print(f"[green]User '{username}' updated successfully![/green]")
    except Exception as e:
        console.print(f"[red]Failed to update user: {e}[/red]")


def _delete_user() -> None:
    """Delete a user."""
    console.print("\n[bold cyan]Delete User[/bold cyan]")

    username = Prompt.ask("Username to delete")

    if username == "admin":
        console.print("[red]Cannot delete admin user.[/red]")
        return

    confirm = Prompt.ask(
        f"Are you sure you want to delete user '{username}'?",
        choices=["y", "n"],
        default="n",
    )
    if confirm.lower() != "y":
        console.print("User deletion cancelled.")
        return

    try:
        enterprise = get_enterprise_features()
        if enterprise.user_manager.delete_user(username):
            console.print(f"[green]User '{username}' deleted successfully![/green]")
        else:
            console.print(f"[red]User '{username}' not found.[/red]")
    except Exception as e:
        console.print(f"[red]Failed to delete user: {e}[/red]")


def _handle_audit_reports() -> None:
    """Handle audit reports."""
    enterprise = get_enterprise_features()

    if not enterprise.check_permission("audit_view"):
        console.print("[red]You don't have permission to view audit reports.[/red]")
        return

    console.print("\n[bold cyan]Audit Reports[/bold cyan]")

    # Get report for last 30 days
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    report = enterprise.get_audit_report(start_date, end_date)

    console.print(
        Panel(
            f"Audit Report (Last 30 Days)\n\n"
            f"Total Events: {report['summary']['total_events']}\n"
            f"Successful: {report['summary']['successful_events']}\n"
            f"Failed: {report['summary']['failed_events']}\n"
            f"Success Rate: {report['summary']['success_rate']:.1f}%",
            title="Enterprise Audit Report",
        )
    )

    # Show recent events
    if report["recent_events"]:
        console.print("\n[bold]Recent Events:[/bold]")
        table = Table()
        table.add_column("Time", style="dim")
        table.add_column("User", style="cyan")
        table.add_column("Event", style="yellow")
        table.add_column("Resource", style="green")
        table.add_column("Status", style="red")

        for event in report["recent_events"][:10]:
            status = "✓" if event["success"] else "✗"
            table.add_row(
                event["timestamp"][:19],  # Remove timezone info
                event["user_id"],
                event["event_type"],
                event["resource"],
                status,
            )

        console.print(table)


def _show_advanced_analytics() -> None:
    """Show advanced analytics interface."""
    console.print("\n[bold cyan]Advanced Analytics[/bold cyan]")
    console.print(
        "This feature provides machine learning-based quality assessment and content analysis."
    )

    # Check enterprise permissions
    enterprise = get_enterprise_features()
    if enterprise.current_user and not enterprise.check_permission("analytics_access"):
        console.print(
            "[red]You don't have permission to access analytics features.[/red]"
        )
        return

    file_path = Prompt.ask("Enter file path to analyze")
    file_path = Path(file_path)

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return

    try:
        analytics = get_advanced_analytics()
        result = analytics.analyze_content(str(file_path))

        console.print("\n[bold]Analytics Results:[/bold]")
        console.print(f"Quality Score: {result.quality_metrics.overall_score:.2f}")
        console.print(f"Document Type: {result.classification.document_type}")
        console.print(f"Complexity Level: {result.classification.complexity_level}")
        console.print(
            f"Processing Time Prediction: {result.insights.processing_time_prediction:.1f}s"
        )

        # Log analytics access
        if enterprise.current_user:
            enterprise.log_analytics_access(
                str(file_path), "full_analysis", success=True
            )

    except Exception as e:
        console.print(f"[red]Analytics failed: {e}[/red]")
        if enterprise.current_user:
            enterprise.log_analytics_access(
                str(file_path), "full_analysis", success=False, error_message=str(e)
            )


def _show_rest_api_server() -> None:
    """Show REST API server interface."""
    console.print("\n[bold cyan]REST API Server[/bold cyan]")
    console.print(
        "This feature starts a REST API server for programmatic access to MilkBottle."
    )

    # Check enterprise permissions
    enterprise = get_enterprise_features()
    if enterprise.current_user and not enterprise.check_permission("api_access"):
        console.print("[red]You don't have permission to access API features.[/red]")
        return

    host = Prompt.ask("Host", default="0.0.0.0")
    port = int(Prompt.ask("Port", default="8000"))

    console.print(f"\nStarting API server on {host}:{port}")
    console.print("Press Ctrl+C to stop the server")

    try:
        from .api_server import start_api_server

        start_api_server(host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[green]API server stopped.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to start API server: {e}[/red]")


def _show_preview_system() -> None:
    """Show preview system interface."""
    console.print("\n[bold cyan]Interactive Preview System[/bold cyan]")
    console.print("This feature provides real-time preview of extraction results.")

    # Check enterprise permissions
    enterprise = get_enterprise_features()
    if enterprise.current_user and not enterprise.check_permission("file_access"):
        console.print(
            "[red]You don't have permission to access file preview features.[/red]"
        )
        return

    file_path = Prompt.ask("Enter file path to preview")
    file_path = Path(file_path)

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return

    try:
        preview_system = get_preview_system()
        success = preview_system.interactive_preview_workflow(file_path)

        if success:
            console.print("[green]Preview completed successfully![/green]")
        else:
            console.print("[yellow]Preview was cancelled or failed.[/yellow]")

        # Log file access
        if enterprise.current_user:
            enterprise.log_file_access(str(file_path), "preview", success=success)

    except Exception as e:
        console.print(f"[red]Preview failed: {e}[/red]")
        if enterprise.current_user:
            enterprise.log_file_access(
                str(file_path), "preview", success=False, error_message=str(e)
            )


def _show_export_menu() -> None:
    """Show export options menu."""
    console.print("\n[bold cyan]Export Options Menu[/bold cyan]")
    console.print(
        "This feature provides enhanced export format selection with previews."
    )

    # Check enterprise permissions
    enterprise = get_enterprise_features()
    if enterprise.current_user and not enterprise.check_permission("export_operation"):
        console.print("[red]You don't have permission to access export features.[/red]")
        return

    file_path = Prompt.ask("Enter file path to export")
    file_path = Path(file_path)

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return

    try:
        # Generate sample content for demonstration
        sample_content = {
            "title": "Sample Document",
            "content": "This is a sample document for export demonstration.",
            "metadata": {"author": "MilkBottle", "created": "2024-01-01"},
        }

        export_menu = get_export_menu()
        selected_formats = export_menu.show_format_selection(sample_content)

        if selected_formats:
            console.print(f"\nSelected formats: {', '.join(selected_formats)}")

            # Show format previews
            previews = export_menu.show_format_previews(sample_content)

            # Configure export options
            export_config = export_menu.configure_export_options()

            # Execute export
            output_dir = Path("exports")
            output_dir.mkdir(exist_ok=True)

            exported_files = export_menu.execute_export(sample_content, output_dir)

            console.print(
                f"\n[green]Export completed! Files saved to: {output_dir}[/green]"
            )
            for format_id, file_path in exported_files.items():
                console.print(f"  - {format_id}: {file_path}")

            # Log export operation
            if enterprise.current_user:
                enterprise.log_export_operation(
                    str(file_path), selected_formats, success=True
                )
        else:
            console.print("[yellow]No formats selected. Export cancelled.[/yellow]")

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        if enterprise.current_user:
            enterprise.log_export_operation(
                str(file_path), [], success=False, error_message=str(e)
            )


def _show_wizards() -> None:
    """Show configuration wizards."""
    console.print("\n[bold cyan]Configuration Wizards[/bold cyan]")
    console.print("This feature provides guided configuration setup for bottles.")

    # Check enterprise permissions
    enterprise = get_enterprise_features()
    if enterprise.current_user and not enterprise.check_permission("config_change"):
        console.print(
            "[red]You don't have permission to access configuration features.[/red]"
        )
        return

    console.print("\nAvailable wizards:")
    console.print("1. PDFmilker configuration")
    console.print("2. VENVmilker configuration")
    console.print("3. Fontmilker configuration")
    console.print("0. Back")

    choice = Prompt.ask("Select wizard", choices=["0", "1", "2", "3"], default="0")

    if choice == "0":
        return

    wizard_map = {"1": "pdfmilker", "2": "venvmilker", "3": "fontmilker"}

    wizard_type = wizard_map[choice]

    try:
        config = run_wizard(wizard_type)
        console.print(f"\n[green]Configuration for {wizard_type} completed![/green]")
        console.print(f"Configuration: {config}")

        # Log configuration change
        if enterprise.current_user:
            enterprise.audit_logger.log_event(
                user_id=enterprise.current_user.username,
                event_type=enterprise.audit_logger.AuditEventType.CONFIG_CHANGE,
                resource=wizard_type,
                action="wizard_configuration",
                details={"wizard_type": wizard_type, "config": config},
                success=True,
            )

    except Exception as e:
        console.print(f"[red]Wizard failed: {e}[/red]")
        if enterprise.current_user:
            enterprise.audit_logger.log_event(
                user_id=enterprise.current_user.username,
                event_type=enterprise.audit_logger.AuditEventType.CONFIG_CHANGE,
                resource=wizard_type,
                action="wizard_configuration",
                details={"wizard_type": wizard_type},
                success=False,
                error_message=str(e),
            )


def _list_bottles() -> None:
    """List available bottles."""
    registry = get_registry()
    bottles = registry.discover_bottles()

    if not bottles:
        console.print("[yellow]No bottles found.[/yellow]")
        return

    table = Table(title="Available Bottles")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Status", style="red")

    for name, info in bottles.items():
        status = "Active" if info.get("is_valid", False) else "Inactive"
        table.add_row(
            name,
            info.get("version", "Unknown"),
            info.get("description", "No description"),
            status,
        )

    console.print(table)


def _execute_bottle() -> None:
    """Execute a bottle."""
    registry = get_registry()
    bottles = registry.discover_bottles()

    if not bottles:
        console.print("[yellow]No bottles available.[/yellow]")
        return

    console.print("\n[bold cyan]Execute Bottle[/bold cyan]")
    console.print("Available bottles:")

    valid_bottles = [
        name for name, info in bottles.items() if info.get("is_valid", False)
    ]

    for i, name in enumerate(valid_bottles, 1):
        console.print(f"{i}. {name}")

    try:
        choice = int(
            Prompt.ask(
                "Select bottle",
                choices=[str(i) for i in range(1, len(valid_bottles) + 1)],
            )
        )
        bottle_name = valid_bottles[choice - 1]

        console.print(f"\nExecuting {bottle_name}...")

        # Get bottle CLI and execute
        bottle_info = bottles[bottle_name]
        if "cli_function" in bottle_info:
            bottle_info["cli_function"]()
        else:
            console.print(f"[red]Bottle {bottle_name} has no CLI function.[/red]")

        # Log bottle execution
        enterprise = get_enterprise_features()
        if enterprise.current_user:
            enterprise.log_bottle_execution(
                bottle_name, {"bottle_name": bottle_name}, success=True
            )

    except (ValueError, IndexError):
        console.print("[red]Invalid selection.[/red]")
    except Exception as e:
        console.print(f"[red]Failed to execute bottle: {e}[/red]")

        # Log failed execution
        enterprise = get_enterprise_features()
        if enterprise.current_user:
            enterprise.log_bottle_execution(
                bottle_name,
                {"bottle_name": bottle_name},
                success=False,
                error_message=str(e),
            )


def _show_bottle_info() -> None:
    """Show detailed bottle information."""
    registry = get_registry()
    bottles = registry.discover_bottles()

    if not bottles:
        console.print("[yellow]No bottles available.[/yellow]")
        return

    console.print("\n[bold cyan]Bottle Information[/bold cyan]")
    bottle_name = Prompt.ask("Enter bottle name")

    if bottle_name not in bottles:
        console.print(f"[red]Bottle '{bottle_name}' not found.[/red]")
        return

    info = bottles[bottle_name]

    console.print(f"\n[bold]Name:[/bold] {bottle_name}")
    console.print(f"[bold]Version:[/bold] {info.get('version', 'Unknown')}")
    console.print(
        f"[bold]Description:[/bold] {info.get('description', 'No description')}"
    )
    console.print(f"[bold]Author:[/bold] {info.get('author', 'Unknown')}")
    console.print(
        f"[bold]Status:[/bold] {'Active' if info.get('is_valid', False) else 'Inactive'}"
    )

    if "capabilities" in info:
        console.print(f"[bold]Capabilities:[/bold] {', '.join(info['capabilities'])}")

    if "dependencies" in info:
        console.print(f"[bold]Dependencies:[/bold] {', '.join(info['dependencies'])}")


@click.command()
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--list-bottles", is_flag=True, help="List available bottles")
@click.option("--execute", help="Execute a specific bottle")
@click.option("--info", help="Show information about a specific bottle")
def main(
    version: bool, list_bottles: bool, execute: Optional[str], info: Optional[str]
) -> None:
    """MilkBottle CLI - Modular CLI Toolbox."""
    if version:
        console.print("[bold cyan]MilkBottle CLI Toolbox v1.0.0[/bold cyan]")
        return

    if list_bottles:
        _list_bottles()
        return

    if execute:
        registry = get_registry()
        bottles = registry.discover_bottles()

        if execute not in bottles:
            console.print(f"[red]Bottle '{execute}' not found.[/red]")
            return

        bottle_info = bottles[execute]
        if "cli_function" in bottle_info:
            bottle_info["cli_function"]()
        else:
            console.print(f"[red]Bottle {execute} has no CLI function.[/red]")
        return

    if info:
        registry = get_registry()
        bottles = registry.discover_bottles()

        if info not in bottles:
            console.print(f"[red]Bottle '{info}' not found.[/red]")
            return

        bottle_info = bottles[info]
        console.print(f"\n[bold]Name:[/bold] {info}")
        console.print(f"[bold]Version:[/bold] {bottle_info.get('version', 'Unknown')}")
        console.print(
            f"[bold]Description:[/bold] {bottle_info.get('description', 'No description')}"
        )
        console.print(f"[bold]Author:[/bold] {bottle_info.get('author', 'Unknown')}")
        console.print(
            f"[bold]Status:[/bold] {'Active' if bottle_info.get('is_valid', False) else 'Inactive'}"
        )
        return

    # Interactive mode
    console.print("[bold cyan]Welcome to MilkBottle CLI Toolbox![/bold cyan]")

    while True:
        try:
            _show_main_menu()
            choice = Prompt.ask(
                "Choice",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                default="0",
            )

            if choice == "0":
                console.print("[green]Goodbye![/green]")
                break
            elif choice == "1":
                _list_bottles()
            elif choice == "2":
                _execute_bottle()
            elif choice == "3":
                _show_bottle_info()
            elif choice == "4":
                _show_preview_system()
            elif choice == "5":
                _show_wizards()
            elif choice == "6":
                _show_advanced_analytics()
            elif choice == "7":
                _show_export_menu()
            elif choice == "8":
                _show_rest_api_server()
            elif choice == "9":
                _handle_enterprise_features()

            if choice != "0":
                Prompt.ask("\nPress Enter to continue")

        except KeyboardInterrupt:
            console.print("\n[green]Goodbye![/green]")
            break
        except Exception as e:
            console.print(f"[red]An error occurred: {e}[/red]")
            logger.error(f"CLI error: {e}")


if __name__ == "__main__":
    main()
