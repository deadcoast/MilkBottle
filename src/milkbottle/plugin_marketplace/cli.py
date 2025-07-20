"""CLI commands for the plugin marketplace system."""

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import MilkBottleConfig
from .marketplace_manager import MarketplaceManager
from .plugin_repository import PluginRepository
from .plugin_security import PluginSecurity

console = Console()


@click.group()
def marketplace():
    """Plugin marketplace commands."""
    pass


@marketplace.command()
@click.argument("query")
@click.option("--category", help="Filter by category")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--limit", default=20, help="Maximum number of results")
def search(query: str, category: Optional[str], tags: Optional[str], limit: int):
    """Search for plugins in the marketplace."""

    async def _search():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        tag_list = tags.split(",") if tags else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Searching plugins...", total=None)

            results = await marketplace_manager.search_plugins(
                query, category, tag_list, limit
            )

            if results:
                table = Table(title=f"Search Results for '{query}'")
                table.add_column("Name", style="cyan")
                table.add_column("Description", style="green")
                table.add_column("Author", style="yellow")
                table.add_column("Rating", style="blue")
                table.add_column("Downloads", style="red")

                for plugin in results:
                    table.add_row(
                        plugin.name,
                        (
                            f"{plugin.description[:50]}..."
                            if len(plugin.description) > 50
                            else plugin.description
                        ),
                        plugin.author,
                        f"{plugin.rating:.1f}",
                        str(plugin.download_count),
                    )

                console.print(table)
            else:
                console.print("No plugins found matching your search criteria")

    asyncio.run(_search())


@marketplace.command()
@click.argument("plugin_name")
def info(plugin_name: str):
    """Get detailed information about a plugin."""

    async def _info():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        info = await marketplace_manager.get_plugin_info(plugin_name)

        if info:
            table = Table(title=f"Plugin Information: {plugin_name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Name", info.name)
            table.add_row("Description", info.description)
            table.add_row("Author", info.author)
            table.add_row("License", info.license)
            table.add_row("Latest Version", info.latest_version or "N/A")
            table.add_row("Rating", f"{info.rating:.1f}")
            table.add_row("Downloads", str(info.download_count))
            table.add_row("Reviews", str(info.review_count))
            table.add_row("Last Updated", info.last_updated)
            table.add_row("Status", info.status)

            if info.tags:
                table.add_row("Tags", ", ".join(info.tags))

            if info.categories:
                table.add_row("Categories", ", ".join(info.categories))

            console.print(table)
        else:
            console.print(f"❌ Plugin '{plugin_name}' not found")

    asyncio.run(_info())


@marketplace.command()
@click.argument("plugin_name")
@click.option("--version", help="Specific version to install")
def install(plugin_name: str, version: Optional[str]):
    """Install a plugin from the marketplace."""

    async def _install():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Installing {plugin_name}...", total=None)

            result = await marketplace_manager.install_plugin(plugin_name, version)

            if result:
                console.print(f"✅ Successfully installed plugin: {plugin_name}")
            else:
                console.print(f"❌ Failed to install plugin: {plugin_name}")

    asyncio.run(_install())


@marketplace.command()
@click.argument("plugin_name")
@click.argument("rating", type=float)
@click.argument("review")
@click.option("--user", default="anonymous", help="Username for the review")
def rate(plugin_name: str, rating: float, review: str, user: str):
    """Rate and review a plugin."""

    async def _rate():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        if not 0 <= rating <= 5:
            console.print("❌ Rating must be between 0 and 5")
            return

        result = await marketplace_manager.submit_review(
            plugin_name, user, rating, review
        )

        if result:
            console.print(f"✅ Review submitted for {plugin_name}")
        else:
            console.print(f"❌ Failed to submit review for {plugin_name}")

    asyncio.run(_rate())


@marketplace.command()
@click.argument("plugin_name")
@click.option("--limit", default=10, help="Maximum number of reviews to show")
def reviews(plugin_name: str, limit: int):
    """Show reviews for a plugin."""

    async def _reviews():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        reviews = await marketplace_manager.get_reviews(plugin_name, limit)

        if reviews:
            table = Table(title=f"Reviews for {plugin_name}")
            table.add_column("User", style="cyan")
            table.add_column("Rating", style="yellow")
            table.add_column("Review", style="green")
            table.add_column("Date", style="blue")

            for review in reviews:
                table.add_row(
                    review.user,
                    f"{review.rating:.1f}",
                    (
                        f"{review.review[:100]}..."
                        if len(review.review) > 100
                        else review.review
                    ),
                    review.timestamp,
                )

            console.print(table)
        else:
            console.print(f"No reviews found for {plugin_name}")

    asyncio.run(_reviews())


@marketplace.command()
@click.argument("plugin_name")
def analytics(plugin_name: str):
    """Show analytics for a plugin."""

    async def _analytics():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        download_count = await marketplace_manager.get_download_count(plugin_name)
        avg_rating = await marketplace_manager.get_average_rating(plugin_name)
        usage_stats = await marketplace_manager.get_usage_stats(plugin_name)

        table = Table(title=f"Analytics for {plugin_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Downloads", str(download_count))
        table.add_row("Average Rating", f"{avg_rating:.1f}")
        table.add_row("Usage Events", str(len(usage_stats)))

        console.print(table)

    asyncio.run(_analytics())


@marketplace.command()
@click.option("--limit", default=10, help="Number of plugins to show")
def popular(limit: int):
    """Show most popular plugins."""

    async def _popular():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        plugins = await marketplace_manager.get_popular_plugins(limit)

        if plugins:
            table = Table(title="Most Popular Plugins")
            table.add_column("Rank", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Downloads", style="yellow")
            table.add_column("Rating", style="blue")
            table.add_column("Author", style="red")

            for i, plugin in enumerate(plugins, 1):
                table.add_row(
                    str(i),
                    plugin.name,
                    str(plugin.download_count),
                    f"{plugin.rating:.1f}",
                    plugin.author,
                )

            console.print(table)
        else:
            console.print("No plugins found")

    asyncio.run(_popular())


@marketplace.command()
@click.option("--limit", default=10, help="Number of plugins to show")
def recent(limit: int):
    """Show recently updated plugins."""

    async def _recent():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        plugins = await marketplace_manager.get_recent_plugins(limit)

        if plugins:
            table = Table(title="Recently Updated Plugins")
            table.add_column("Name", style="cyan")
            table.add_column("Last Updated", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Author", style="blue")

            for plugin in plugins:
                table.add_row(
                    plugin.name,
                    plugin.last_updated,
                    plugin.latest_version or "N/A",
                    plugin.author,
                )

            console.print(table)
        else:
            console.print("No plugins found")

    asyncio.run(_recent())


@marketplace.command()
@click.argument("category")
@click.option("--limit", default=20, help="Number of plugins to show")
def category(category: str, limit: int):
    """Show plugins by category."""

    async def _category():
        config = MilkBottleConfig()
        marketplace_manager = MarketplaceManager(config)

        plugins = await marketplace_manager.get_plugins_by_category(category, limit)

        if plugins:
            table = Table(title=f"Plugins in Category: {category}")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Rating", style="yellow")
            table.add_column("Downloads", style="blue")

            for plugin in plugins:
                table.add_row(
                    plugin.name,
                    (
                        f"{plugin.description[:50]}..."
                        if len(plugin.description) > 50
                        else plugin.description
                    ),
                    f"{plugin.rating:.1f}",
                    str(plugin.download_count),
                )

            console.print(table)
        else:
            console.print(f"No plugins found in category: {category}")

    asyncio.run(_category())


@marketplace.command()
@click.argument("plugin_path", type=click.Path(exists=True))
def validate(plugin_path: str):
    """Validate a plugin for marketplace submission."""

    async def _validate():
        config = MilkBottleConfig()
        repository = PluginRepository(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Validating plugin...", total=None)

            result = await repository.validate_plugin(Path(plugin_path))

            if result["valid"]:
                console.print("✅ Plugin validation passed")

                if result["warnings"]:
                    console.print("\n⚠️  Warnings:")
                    for warning in result["warnings"]:
                        console.print(f"  - {warning}")
            else:
                console.print("❌ Plugin validation failed")

                if result["errors"]:
                    console.print("\n❌ Errors:")
                    for error in result["errors"]:
                        console.print(f"  - {error}")

    asyncio.run(_validate())


@marketplace.command()
@click.argument("plugin_name")
def security_scan(plugin_name: str):
    """Perform security scan on a plugin."""

    async def _security_scan():
        security = PluginSecurity()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Scanning plugin...", total=None)

            result = await security.scan_plugin(plugin_name, f"/tmp/{plugin_name}")

            if result.passed:
                console.print("✅ Security scan passed")
            else:
                console.print("❌ Security scan failed")

                if result.issues:
                    console.print("\n⚠️  Issues found:")
                    for issue in result.issues:
                        console.print(f"  - {issue}")

    asyncio.run(_security_scan())
