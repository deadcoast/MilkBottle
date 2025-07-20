"""CLI commands for the deployment system."""

import asyncio

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import MilkBottleConfig
from .backup_manager import BackupManager
from .ci_cd_manager import CICDManager
from .deployment_manager import DeploymentManager
from .docker_manager import DockerManager
from .monitoring_manager import MonitoringManager
from .scaling_manager import ScalingManager
from .security_manager import SecurityManager

console = Console()


@click.group()
def deployment():
    """Deployment management commands."""
    pass


@deployment.group()
def scaling():
    """Application scaling commands."""
    pass


@scaling.command()
@click.option("--count", default=1, help="Number of instances to add")
@click.option("--reason", default="manual", help="Reason for scaling")
def scale_up(count: int, reason: str):
    """Scale up the application by adding instances."""

    async def _scale_up():
        config = MilkBottleConfig()
        scaling_manager = ScalingManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Scaling up...", total=None)

            result = await scaling_manager.scale_up(count, reason)

            if result:
                console.print(f"✅ Successfully scaled up by {count} instances")
            else:
                console.print("❌ Failed to scale up")

    asyncio.run(_scale_up())


@scaling.command()
@click.option("--count", default=1, help="Number of instances to remove")
@click.option("--reason", default="manual", help="Reason for scaling")
def scale_down(count: int, reason: str):
    """Scale down the application by removing instances."""

    async def _scale_down():
        config = MilkBottleConfig()
        scaling_manager = ScalingManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Scaling down...", total=None)

            result = await scaling_manager.scale_down(count, reason)

            if result:
                console.print(f"✅ Successfully scaled down by {count} instances")
            else:
                console.print("❌ Failed to scale down")

    asyncio.run(_scale_down())


@scaling.command()
def list_instances():
    """List all application instances."""

    async def _list_instances():
        config = MilkBottleConfig()
        scaling_manager = ScalingManager(config)

        instances = await scaling_manager.get_instances()

        if not instances:
            console.print("No instances found")
            return

        table = Table(title="Application Instances")
        table.add_column("Instance ID", style="cyan")
        table.add_column("Host", style="green")
        table.add_column("Port", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("CPU %", style="red")
        table.add_column("Memory %", style="red")
        table.add_column("Health", style="green")

        for instance in instances:
            health_color = "green" if instance.health_status == "healthy" else "red"
            table.add_row(
                instance.instance_id,
                instance.host,
                str(instance.port),
                instance.status,
                f"{instance.cpu_usage:.1f}",
                f"{instance.memory_usage:.1f}",
                f"[{health_color}]{instance.health_status}[/{health_color}]",
            )

        console.print(table)

    asyncio.run(_list_instances())


@deployment.group()
def security():
    """Security management commands."""
    pass


@security.command()
@click.argument("username")
@click.argument("email")
@click.argument("password")
@click.option("--role", default="user", help="User role (admin, user, guest)")
def create_user(username: str, email: str, password: str, role: str):
    """Create a new user."""

    async def _create_user():
        config = MilkBottleConfig()
        security_manager = SecurityManager(config)

        result = await security_manager.create_user(username, email, password, role)

        if result:
            console.print(f"✅ Successfully created user: {username}")
        else:
            console.print("❌ Failed to create user")

    asyncio.run(_create_user())


@security.command()
@click.argument("username")
@click.argument("password")
def authenticate(username: str, password: str):
    """Authenticate a user."""

    async def _authenticate():
        config = MilkBottleConfig()
        security_manager = SecurityManager(config)

        result = await security_manager.authenticate_user(username, password)

        if result:
            console.print(f"✅ Authentication successful for: {username}")
        else:
            console.print("❌ Authentication failed")

    asyncio.run(_authenticate())


@security.command()
def security_report():
    """Generate security report."""

    async def _security_report():
        config = MilkBottleConfig()
        security_manager = SecurityManager(config)

        report = await security_manager.generate_security_report()

        if report:
            table = Table(title="Security Report")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            for key, value in report.items():
                table.add_row(key, str(value))

            console.print(table)
        else:
            console.print("❌ Failed to generate security report")

    asyncio.run(_security_report())


@deployment.group()
def monitoring():
    """Monitoring commands."""
    pass


@monitoring.command()
def start_monitoring():
    """Start system monitoring."""

    async def _start_monitoring():
        config = MilkBottleConfig()
        monitoring_manager = MonitoringManager(config)

        result = await monitoring_manager.start_monitoring()

        if result:
            console.print("✅ Monitoring started successfully")
        else:
            console.print("❌ Failed to start monitoring")

    asyncio.run(_start_monitoring())


@monitoring.command()
def system_metrics():
    """Get current system metrics."""

    async def _system_metrics():
        config = MilkBottleConfig()
        monitoring_manager = MonitoringManager(config)

        metrics = await monitoring_manager.collect_system_metrics()

        if metrics:
            table = Table(title="System Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("CPU Usage", f"{metrics.cpu_percent:.1f}%")
            table.add_row("Memory Usage", f"{metrics.memory_percent:.1f}%")
            table.add_row("Disk Usage", f"{metrics.disk_usage_percent:.1f}%")
            table.add_row("Uptime", f"{metrics.uptime:.1f} seconds")

            console.print(table)
        else:
            console.print("❌ Failed to collect system metrics")

    asyncio.run(_system_metrics())


@deployment.group()
def backup():
    """Backup management commands."""
    pass


@backup.command()
def create_backup():
    """Create a new backup."""

    async def _create_backup():
        config = MilkBottleConfig()
        backup_manager = BackupManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Creating backup...", total=None)

            result = await backup_manager.create_backup()

            if result:
                console.print("✅ Backup created successfully")
            else:
                console.print("❌ Failed to create backup")

    asyncio.run(_create_backup())


@backup.command()
@click.argument("backup_id")
def restore_backup(backup_id: str):
    """Restore from a backup."""

    async def _restore_backup():
        config = MilkBottleConfig()
        backup_manager = BackupManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Restoring backup...", total=None)

            result = await backup_manager.restore_backup(backup_id)

            if result:
                console.print("✅ Backup restored successfully")
            else:
                console.print("❌ Failed to restore backup")

    asyncio.run(_restore_backup())


@deployment.group()
def docker():
    """Docker management commands."""
    pass


@docker.command()
def build_image():
    """Build Docker image."""

    async def _build_image():
        config = MilkBottleConfig()
        docker_manager = DockerManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Building Docker image...", total=None)

            result = await docker_manager.build_image()

            if result:
                console.print("✅ Docker image built successfully")
            else:
                console.print("❌ Failed to build Docker image")

    asyncio.run(_build_image())


@docker.command()
def run_container():
    """Run Docker container."""

    async def _run_container():
        config = MilkBottleConfig()
        docker_manager = DockerManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Running Docker container...", total=None)

            result = await docker_manager.run_container()

            if result:
                console.print("✅ Docker container started successfully")
            else:
                console.print("❌ Failed to start Docker container")

    asyncio.run(_run_container())


@deployment.group()
def cicd():
    """CI/CD pipeline commands."""
    pass


@cicd.command()
def run_pipeline():
    """Run CI/CD pipeline."""

    async def _run_pipeline():
        config = MilkBottleConfig()
        cicd_manager = CICDManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Running CI/CD pipeline...", total=None)

            result = await cicd_manager.run_pipeline()

            if result:
                console.print("✅ CI/CD pipeline completed successfully")
            else:
                console.print("❌ CI/CD pipeline failed")

    asyncio.run(_run_pipeline())


@cicd.command()
def pipeline_status():
    """Get CI/CD pipeline status."""

    async def _pipeline_status():
        config = MilkBottleConfig()
        cicd_manager = CICDManager(config)

        status = await cicd_manager.get_pipeline_status()

        if status:
            table = Table(title="CI/CD Pipeline Status")
            table.add_column("Stage", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Duration", style="yellow")

            for stage, info in status.items():
                status_color = "green" if info.get("status") == "success" else "red"
                table.add_row(
                    stage,
                    f"[{status_color}]{info.get('status', 'unknown')}[/{status_color}]",
                    f"{info.get('duration', 0):.1f}s",
                )

            console.print(table)
        else:
            console.print("❌ Failed to get pipeline status")

    asyncio.run(_pipeline_status())


@deployment.command()
def deploy():
    """Deploy the application."""

    async def _deploy():
        config = MilkBottleConfig()
        deployment_manager = DeploymentManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Deploying application...", total=None)

            result = await deployment_manager.deploy_application()

            if result:
                console.print("✅ Application deployed successfully")
            else:
                console.print("❌ Deployment failed")

    asyncio.run(_deploy())


@deployment.command()
def rollback():
    """Rollback the deployment."""

    async def _rollback():
        config = MilkBottleConfig()
        deployment_manager = DeploymentManager(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _task = progress.add_task("Rolling back deployment...", total=None)

            result = await deployment_manager.rollback_deployment()

            if result:
                console.print("✅ Deployment rolled back successfully")
            else:
                console.print("❌ Rollback failed")

    asyncio.run(_rollback())
