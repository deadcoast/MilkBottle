"""Docker Manager - Docker container and image management."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import MilkBottleConfig


@dataclass
class DockerConfig:
    """Docker configuration."""

    image_name: str = "milkbottle"
    image_tag: str = "latest"
    container_name: str = "milkbottle-app"
    port_mapping: str = "8000:8000"
    volume_mapping: str = "./data:/app/data"
    environment_vars: Optional[List[str]] = None
    dockerfile_path: str = "Dockerfile"


class DockerManager:
    """Docker container and image management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.docker_config = DockerConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.docker")

    async def build_image(
        self,
        dockerfile_path: Optional[str] = None,
        image_name: Optional[str] = None,
        image_tag: Optional[str] = None,
    ) -> bool:
        """Build Docker image."""
        try:
            self.logger.info("Building Docker image")

            dockerfile = dockerfile_path or self.docker_config.dockerfile_path
            name = image_name or self.docker_config.image_name
            tag = image_tag or self.docker_config.image_tag

            # Check if Dockerfile exists
            if not Path(dockerfile).exists():
                await self._create_dockerfile(dockerfile)

            # Build image
            cmd = ["docker", "build", "-t", f"{name}:{tag}", "-f", dockerfile, "."]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Building Docker image", total=None)

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    progress.update(task, completed=True)
                    self.logger.info(f"Successfully built image: {name}:{tag}")
                    return True
                else:
                    progress.update(task, completed=False)
                    self.logger.error(f"Docker build failed: {result.stderr}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to build Docker image: {e}")
            return False

    async def run_container(
        self,
        container_name: Optional[str] = None,
        port_mapping: Optional[str] = None,
        volume_mapping: Optional[str] = None,
        environment_vars: Optional[List[str]] = None,
    ) -> bool:
        """Run Docker container."""
        try:
            self.logger.info("Starting Docker container")

            name = container_name or self.docker_config.container_name
            ports = port_mapping or self.docker_config.port_mapping
            volumes = volume_mapping or self.docker_config.volume_mapping
            env_vars = environment_vars or self.docker_config.environment_vars or []

            # Stop existing container if running
            await self.stop_container(name)

            # Run container
            cmd = [
                "docker",
                "run",
                "-d",  # Detached mode
                "--name",
                name,
                "-p",
                ports,
                "-v",
                volumes,
            ]

            # Add environment variables
            for env_var in env_vars:
                cmd.extend(["-e", env_var])

            # Add image
            cmd.append(
                f"{self.docker_config.image_name}:{self.docker_config.image_tag}"
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Starting Docker container", total=None)

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    progress.update(task, completed=True)
                    self.logger.info(f"Successfully started container: {name}")
                    return True
                else:
                    progress.update(task, completed=False)
                    self.logger.error(f"Docker run failed: {result.stderr}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to run Docker container: {e}")
            return False

    async def stop_container(self, container_name: Optional[str] = None) -> bool:
        """Stop Docker container."""
        try:
            name = container_name or self.docker_config.container_name

            # Check if container exists and is running
            cmd = ["docker", "ps", "-q", "-f", f"name={name}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                # Container is running, stop it
                stop_cmd = ["docker", "stop", name]
                subprocess.run(stop_cmd, capture_output=True)

                # Remove container
                rm_cmd = ["docker", "rm", name]
                subprocess.run(rm_cmd, capture_output=True)

                self.logger.info(f"Stopped and removed container: {name}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to stop container: {e}")
            return False

    async def get_container_status(
        self, container_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get container status."""
        try:
            name = container_name or self.docker_config.container_name

            cmd = ["docker", "ps", "-a", "--format", "json", "-f", f"name={name}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                import json

                container_info = json.loads(result.stdout.strip())
                return {
                    "name": container_info.get("Names", ""),
                    "status": container_info.get("Status", ""),
                    "ports": container_info.get("Ports", ""),
                    "image": container_info.get("Image", ""),
                }
            else:
                return {"status": "not_found"}

        except Exception as e:
            self.logger.error(f"Failed to get container status: {e}")
            return {"status": "error", "error": str(e)}

    async def list_containers(self) -> List[Dict[str, Any]]:
        """List all containers."""
        try:
            cmd = ["docker", "ps", "-a", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            containers = []
            if result.stdout.strip():
                import json

                for line in result.stdout.strip().split("\n"):
                    if line:
                        container_info = json.loads(line)
                        containers.append(
                            {
                                "name": container_info.get("Names", ""),
                                "status": container_info.get("Status", ""),
                                "ports": container_info.get("Ports", ""),
                                "image": container_info.get("Image", ""),
                            }
                        )

            return containers

        except Exception as e:
            self.logger.error(f"Failed to list containers: {e}")
            return []

    async def list_images(self) -> List[Dict[str, Any]]:
        """List all images."""
        try:
            cmd = ["docker", "images", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            images = []
            if result.stdout.strip():
                import json

                for line in result.stdout.strip().split("\n"):
                    if line:
                        image_info = json.loads(line)
                        images.append(
                            {
                                "repository": image_info.get("Repository", ""),
                                "tag": image_info.get("Tag", ""),
                                "size": image_info.get("Size", ""),
                                "created": image_info.get("CreatedAt", ""),
                            }
                        )

            return images

        except Exception as e:
            self.logger.error(f"Failed to list images: {e}")
            return []

    async def clean_up(
        self, remove_containers: bool = True, remove_images: bool = False
    ) -> bool:
        """Clean up Docker resources."""
        try:
            self.logger.info("Cleaning up Docker resources")

            if remove_containers:
                # Remove stopped containers
                subprocess.run(
                    ["docker", "container", "prune", "-f"], capture_output=True
                )
                self.logger.info("Removed stopped containers")

            if remove_images:
                # Remove unused images
                subprocess.run(["docker", "image", "prune", "-f"], capture_output=True)
                self.logger.info("Removed unused images")

            return True

        except Exception as e:
            self.logger.error(f"Failed to clean up Docker resources: {e}")
            return False

    async def _create_dockerfile(self, dockerfile_path: str) -> None:
        """Create a default Dockerfile."""
        dockerfile_content = """# MilkBottle Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MILKBOTTLE_ENV=production

# Run application
CMD ["python", "-m", "milkbottle"]
"""

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        self.logger.info(f"Created Dockerfile: {dockerfile_path}")

    async def create_docker_compose(
        self, compose_file: str = "docker-compose.yml"
    ) -> bool:
        """Create Docker Compose configuration."""
        try:
            compose_config = {
                "version": "3.8",
                "services": {
                    "milkbottle": {
                        "build": ".",
                        "container_name": self.docker_config.container_name,
                        "ports": [self.docker_config.port_mapping],
                        "volumes": [self.docker_config.volume_mapping],
                        "environment": self.docker_config.environment_vars or [],
                        "restart": "unless-stopped",
                        "healthcheck": {
                            "test": [
                                "CMD",
                                "curl",
                                "-f",
                                "http://localhost:8000/health",
                            ],
                            "interval": "30s",
                            "timeout": "10s",
                            "retries": "3",
                        },
                    }
                },
            }

            with open(compose_file, "w") as f:
                yaml.dump(compose_config, f, default_flow_style=False)

            self.logger.info(f"Created Docker Compose file: {compose_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create Docker Compose file: {e}")
            return False

    async def run_with_compose(self, compose_file: str = "docker-compose.yml") -> bool:
        """Run application using Docker Compose."""
        try:
            self.logger.info("Starting application with Docker Compose")

            # Create compose file if it doesn't exist
            if not Path(compose_file).exists():
                await self.create_docker_compose(compose_file)

            # Run with docker-compose
            cmd = ["docker-compose", "-f", compose_file, "up", "-d"]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Starting with Docker Compose", total=None)

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    progress.update(task, completed=True)
                    self.logger.info("Successfully started with Docker Compose")
                    return True
                else:
                    progress.update(task, completed=False)
                    self.logger.error(f"Docker Compose failed: {result.stderr}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to run with Docker Compose: {e}")
            return False
