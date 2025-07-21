"""Deployment Manager - Core deployment orchestration system."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import MilkBottleConfig
from ..utils import ErrorHandler, InputValidator


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    environment: str = "production"
    target_host: str = "localhost"
    target_port: int = 22
    target_user: str = "deploy"
    target_path: str = "/opt/milkbottle"
    backup_enabled: bool = True
    monitoring_enabled: bool = True
    scaling_enabled: bool = False
    security_enabled: bool = True


@dataclass
class DeploymentStatus:
    """Deployment status information."""

    status: str = "pending"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    steps_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class DeploymentManager:
    """Main deployment orchestration system."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.deployment_config = DeploymentConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.deployment")
        self.error_handler = ErrorHandler()
        self.validator = InputValidator()
        self.current_deployment: Optional[DeploymentStatus] = None

    async def deploy(
        self,
        environment: str = "production",
        target_host: Optional[str] = None,
        target_path: Optional[str] = None,
    ) -> bool:
        """Deploy MilkBottle to target environment."""
        try:
            self.logger.info(f"Starting deployment to {environment}")

            # Initialize deployment
            self.current_deployment = DeploymentStatus(
                status="running", start_time=self._get_timestamp()
            )

            # Update deployment config
            if target_host:
                self.deployment_config.target_host = target_host
            if target_path:
                self.deployment_config.target_path = target_path
            self.deployment_config.environment = environment

            # Validate deployment configuration
            if not await self._validate_deployment_config():
                self.logger.error("Deployment configuration validation failed")
                return False

            # Execute deployment steps
            deployment_steps = [
                ("Preparing deployment", self._prepare_deployment),
                ("Building application", self._build_application),
                ("Creating backup", self._create_backup),
                ("Deploying application", self._deploy_application),
                ("Configuring services", self._configure_services),
                ("Starting services", self._start_services),
                ("Running health checks", self._run_health_checks),
                ("Finalizing deployment", self._finalize_deployment),
            ]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                for step_name, step_func in deployment_steps:
                    task = progress.add_task(step_name, total=None)

                    try:
                        await step_func()
                        self.current_deployment.steps_completed.append(step_name)
                        progress.update(task, completed=True)

                    except Exception as e:
                        error_msg = f"Step '{step_name}' failed: {e}"
                        self.logger.error(error_msg)
                        self.current_deployment.errors.append(error_msg)
                        progress.update(task, completed=False)
                        return False

            # Mark deployment as successful
            self.current_deployment.status = "completed"
            self.current_deployment.end_time = self._get_timestamp()

            self.logger.info("Deployment completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            if self.current_deployment:
                self.current_deployment.status = "failed"
                self.current_deployment.errors.append(str(e))
                self.current_deployment.end_time = self._get_timestamp()
            return False

    async def rollback(self, deployment_id: Optional[str] = None) -> bool:
        """Rollback to previous deployment."""
        try:
            self.logger.info("Starting deployment rollback")

            # Find previous deployment
            previous_deployment = await self._find_previous_deployment(deployment_id)
            if not previous_deployment:
                self.logger.error("No previous deployment found for rollback")
                return False

            # Execute rollback steps
            rollback_steps = [
                ("Stopping current services", self._stop_services),
                ("Restoring previous version", self._restore_previous_version),
                ("Starting previous services", self._start_services),
                ("Running health checks", self._run_health_checks),
            ]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                for step_name, step_func in rollback_steps:
                    task = progress.add_task(step_name, total=None)

                    try:
                        await step_func()
                        progress.update(task, completed=True)

                    except Exception as e:
                        error_msg = f"Rollback step '{step_name}' failed: {e}"
                        self.logger.error(error_msg)
                        progress.update(task, completed=False)
                        return False

            self.logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    async def deploy_application(self, environment: str = "production") -> bool:
        """Deploy application (alias for deploy method)."""
        return await self.deploy(environment)

    async def rollback_deployment(self, deployment_id: Optional[str] = None) -> bool:
        """Rollback deployment (alias for rollback method)."""
        return await self.rollback(deployment_id)

    async def get_deployment_status(self) -> Optional[DeploymentStatus]:
        """Get current deployment status."""
        return self.current_deployment

    async def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments."""
        deployments = []

        # Read deployment history from file
        deployment_history_file = (
            Path.home() / ".milkbottle" / "deployment_history.yaml"
        )

        if deployment_history_file.exists():
            try:
                with open(deployment_history_file, "r") as f:
                    history = yaml.safe_load(f) or []
                    deployments.extend(history)
            except Exception as e:
                self.logger.error(f"Failed to read deployment history: {e}")

        return deployments

    async def _validate_deployment_config(self) -> bool:
        """Validate deployment configuration."""
        try:
            # Check if target host is reachable
            if not await self._check_host_connectivity():
                self.logger.error(
                    f"Cannot connect to target host: {self.deployment_config.target_host}"
                )
                return False

            # Check if target path exists and is writable
            if not await self._check_target_path():
                self.logger.error(
                    f"Target path not accessible: {self.deployment_config.target_path}"
                )
                return False

            # Validate environment configuration
            if not self._validate_environment_config():
                self.logger.error("Environment configuration validation failed")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Deployment configuration validation failed: {e}")
            return False

    async def _prepare_deployment(self) -> None:
        """Prepare deployment environment."""
        self.logger.info("Preparing deployment environment")

        # Create deployment directory
        deployment_dir = (
            Path.home() / ".milkbottle" / "deployments" / self._get_timestamp()
        )
        deployment_dir.mkdir(parents=True, exist_ok=True)

        # Copy application files
        app_files = [
            "src/milkbottle",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
        ]

        for file_path in app_files:
            source_path = Path(file_path)
            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(source_path, deployment_dir / source_path.name)
                else:
                    shutil.copy2(source_path, deployment_dir)

    async def _build_application(self) -> None:
        """Build application for deployment."""
        self.logger.info("Building application")

        # Install dependencies
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
        )

        # Run tests
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/"], check=True, capture_output=True
        )

    async def _create_backup(self) -> None:
        """Create backup of current deployment."""
        if not self.deployment_config.backup_enabled:
            self.logger.info("Backup disabled, skipping")
            return

        self.logger.info("Creating backup of current deployment")

        # Create backup directory
        backup_dir = Path.home() / ".milkbottle" / "backups" / self._get_timestamp()
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup current deployment
        if Path(self.deployment_config.target_path).exists():
            shutil.copytree(self.deployment_config.target_path, backup_dir / "current")

    async def _deploy_application(self) -> None:
        """Deploy application to target."""
        self.logger.info(
            f"Deploying application to {self.deployment_config.target_host}"
        )

        # Create target directory
        target_path = Path(self.deployment_config.target_path)
        target_path.mkdir(parents=True, exist_ok=True)

        # Copy application files
        deployment_dir = (
            Path.home() / ".milkbottle" / "deployments" / self._get_timestamp()
        )
        if deployment_dir.exists():
            shutil.copytree(deployment_dir, target_path, dirs_exist_ok=True)

    async def _configure_services(self) -> None:
        """Configure application services."""
        self.logger.info("Configuring application services")

        # Create service configuration
        service_config = {
            "environment": self.deployment_config.environment,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
            "log_level": "info",
        }

        config_file = Path(self.deployment_config.target_path) / "service_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(service_config, f)

    async def _start_services(self) -> None:
        """Start application services."""
        self.logger.info("Starting application services")

        # Start application using systemd or similar
        service_file = Path(self.deployment_config.target_path) / "milkbottle.service"

        if service_file.exists():
            subprocess.run(["systemctl", "start", "milkbottle"], check=True)
        else:
            # Fallback to direct start
            subprocess.run(
                [sys.executable, "-m", "milkbottle"],
                cwd=self.deployment_config.target_path,
                check=True,
            )

    async def _run_health_checks(self) -> None:
        """Run health checks on deployed application."""
        self.logger.info("Running health checks")

        # Wait for services to start
        await asyncio.sleep(5)

        # Check if application is responding
        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Health check failed: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def _finalize_deployment(self) -> None:
        """Finalize deployment."""
        self.logger.info("Finalizing deployment")

        # Update deployment history
        await self._update_deployment_history()

        # Clean up temporary files
        deployment_dir = (
            Path.home() / ".milkbottle" / "deployments" / self._get_timestamp()
        )
        if deployment_dir.exists():
            shutil.rmtree(deployment_dir)

    async def _stop_services(self) -> None:
        """Stop current services."""
        self.logger.info("Stopping current services")

        try:
            subprocess.run(["systemctl", "stop", "milkbottle"], check=True)
        except subprocess.CalledProcessError:
            # Fallback to process termination
            subprocess.run(["pkill", "-f", "milkbottle"])

    async def _restore_previous_version(self) -> None:
        """Restore previous version."""
        self.logger.info("Restoring previous version")

        # Find latest backup
        backup_dir = Path.home() / ".milkbottle" / "backups"
        if backup_dir.exists():
            if backups := sorted(
                backup_dir.iterdir(), key=lambda x: x.name, reverse=True
            ):
                latest_backup = backups[0] / "current"
                if latest_backup.exists():
                    shutil.rmtree(self.deployment_config.target_path)
                    shutil.copytree(latest_backup, self.deployment_config.target_path)

    async def _check_host_connectivity(self) -> bool:
        """Check if target host is reachable."""
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(
                (self.deployment_config.target_host, self.deployment_config.target_port)
            )
            sock.close()
            return result == 0
        except Exception:
            return False

    async def _check_target_path(self) -> bool:
        """Check if target path is accessible."""
        try:
            target_path = Path(self.deployment_config.target_path)
            if target_path.exists():
                return os.access(target_path, os.W_OK)
            # Try to create directory
            target_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def _validate_environment_config(self) -> bool:
        """Validate environment configuration."""
        required_vars = ["DATABASE_URL", "SECRET_KEY", "LOG_LEVEL"]

        for var in required_vars:
            if not os.getenv(var):
                self.logger.warning(f"Environment variable {var} not set")
                return False

        return True

    async def _find_previous_deployment(
        self, deployment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find previous deployment for rollback."""
        deployments = await self.list_deployments()

        if deployment_id:
            for deployment in deployments:
                if deployment.get("id") == deployment_id:
                    return deployment
        elif deployments:
            return deployments[-1]  # Return latest deployment

        return None

    async def _update_deployment_history(self) -> None:
        """Update deployment history."""
        deployment_history_file = (
            Path.home() / ".milkbottle" / "deployment_history.yaml"
        )

        history = []
        if deployment_history_file.exists():
            try:
                with open(deployment_history_file, "r") as f:
                    history = yaml.safe_load(f) or []
            except Exception:
                history = []

        # Add current deployment
        if self.current_deployment:
            deployment_record = {
                "id": self._get_timestamp(),
                "status": self.current_deployment.status,
                "start_time": self.current_deployment.start_time,
                "end_time": self.current_deployment.end_time,
                "environment": self.deployment_config.environment,
                "target_host": self.deployment_config.target_host,
                "steps_completed": self.current_deployment.steps_completed,
                "errors": self.current_deployment.errors,
                "warnings": self.current_deployment.warnings,
            }

            history.append(deployment_record)

            # Keep only last 10 deployments
            if len(history) > 10:
                history = history[-10:]

        # Write updated history
        deployment_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(deployment_history_file, "w") as f:
            yaml.dump(history, f)

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
