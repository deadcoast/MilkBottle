"""Scaling Manager - Application scaling and load balancing management."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console

from ..config import MilkBottleConfig


@dataclass
class ScalingConfig:
    """Scaling configuration."""

    auto_scaling: bool = True
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 80.0
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    cooldown_period: int = 300  # seconds
    load_balancer_enabled: bool = True
    health_check_interval: int = 30


@dataclass
class InstanceInfo:
    """Application instance information."""

    instance_id: str
    host: str
    port: int
    status: str  # running, stopped, starting, stopping
    cpu_usage: float
    memory_usage: float
    active_connections: int
    start_time: str
    health_status: str  # healthy, unhealthy, unknown


@dataclass
class ScalingEvent:
    """Scaling event information."""

    event_id: str
    timestamp: str
    event_type: str  # scale_up, scale_down
    reason: str
    instances_before: int
    instances_after: int
    metrics: Dict[str, float]


class ScalingManager:
    """Application scaling and load balancing management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.scaling_config = ScalingConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.scaling")
        self.instances: Dict[str, InstanceInfo] = {}
        self.scaling_events: List[ScalingEvent] = []
        self.last_scale_time = 0
        self.scaling_active = False

    async def start_scaling(self) -> bool:
        """Start automatic scaling."""
        try:
            self.logger.info("Starting automatic scaling")
            self.scaling_active = True

            while self.scaling_active:
                # Check if scaling is needed
                await self._check_scaling_needs()

                # Update instance health
                await self._update_instance_health()

                # Wait for next check
                await asyncio.sleep(self.scaling_config.health_check_interval)

            return True

        except Exception as e:
            self.logger.error(f"Scaling failed: {e}")
            return False

    async def stop_scaling(self) -> None:
        """Stop automatic scaling."""
        self.logger.info("Stopping automatic scaling")
        self.scaling_active = False

    async def scale_up(self, count: int = 1, reason: str = "manual") -> bool:
        """Scale up by adding instances."""
        try:
            self.logger.info(f"Scaling up by {count} instances")

            current_count = len(self.instances)
            target_count = min(current_count + count, self.scaling_config.max_instances)

            if target_count <= current_count:
                self.logger.info("Already at maximum instances")
                return False

            # Create new instances
            for i in range(count):
                if len(self.instances) >= self.scaling_config.max_instances:
                    break

                instance_id = await self._create_instance()
                if instance_id:
                    self.logger.info(f"Created instance: {instance_id}")
                else:
                    self.logger.error(f"Failed to create instance {i+1}")

            # Record scaling event
            await self._record_scaling_event(
                "scale_up", reason, current_count, len(self.instances)
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to scale up: {e}")
            return False

    async def scale_down(self, count: int = 1, reason: str = "manual") -> bool:
        """Scale down by removing instances."""
        try:
            self.logger.info(f"Scaling down by {count} instances")

            current_count = len(self.instances)
            target_count = max(current_count - count, self.scaling_config.min_instances)

            if target_count >= current_count:
                self.logger.info("Already at minimum instances")
                return False

            # Remove instances (start with least healthy ones)
            instances_to_remove = await self._select_instances_to_remove(count)

            for instance_id in instances_to_remove:
                if await self._remove_instance(instance_id):
                    self.logger.info(f"Removed instance: {instance_id}")
                else:
                    self.logger.error(f"Failed to remove instance: {instance_id}")

            # Record scaling event
            await self._record_scaling_event(
                "scale_down", reason, current_count, len(self.instances)
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to scale down: {e}")
            return False

    async def get_instances(self) -> List[InstanceInfo]:
        """Get all instances."""
        return list(self.instances.values())

    async def get_instance(self, instance_id: str) -> Optional[InstanceInfo]:
        """Get specific instance."""
        return self.instances.get(instance_id)

    async def restart_instance(self, instance_id: str) -> bool:
        """Restart a specific instance."""
        try:
            self.logger.info(f"Restarting instance: {instance_id}")

            if instance_id not in self.instances:
                self.logger.error(f"Instance {instance_id} not found")
                return False

            # Stop instance
            if await self._stop_instance(instance_id):
                # Wait a moment
                await asyncio.sleep(5)

                # Start instance
                if await self._start_instance(instance_id):
                    self.logger.info(f"Successfully restarted instance: {instance_id}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to start instance after restart: {instance_id}"
                    )
                    return False
            else:
                self.logger.error(f"Failed to stop instance for restart: {instance_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to restart instance: {e}")
            return False

    async def update_load_balancer(self) -> bool:
        """Update load balancer configuration."""
        try:
            if not self.scaling_config.load_balancer_enabled:
                return True

            self.logger.info("Updating load balancer configuration")

            # Get healthy instances
            healthy_instances = [
                instance
                for instance in self.instances.values()
                if instance.status == "running" and instance.health_status == "healthy"
            ]

            # Update load balancer config
            config = {
                "instances": [
                    {"host": instance.host, "port": instance.port, "weight": 1}
                    for instance in healthy_instances
                ],
                "health_check": {
                    "interval": self.scaling_config.health_check_interval,
                    "timeout": 5,
                    "path": "/health",
                },
            }

            # Write config to file
            config_file = Path.home() / ".milkbottle" / "load_balancer.yaml"
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

            self.logger.info(
                f"Updated load balancer with {len(healthy_instances)} instances"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update load balancer: {e}")
            return False

    async def _check_scaling_needs(self) -> None:
        """Check if scaling is needed based on metrics."""
        try:
            # Check cooldown period
            current_time = asyncio.get_event_loop().time()
            if (
                current_time - self.last_scale_time
                < self.scaling_config.cooldown_period
            ):
                return

            # Calculate average metrics
            if not self.instances:
                return

            avg_cpu = sum(
                instance.cpu_usage for instance in self.instances.values()
            ) / len(self.instances)
            avg_memory = sum(
                instance.memory_usage for instance in self.instances.values()
            ) / len(self.instances)

            # Check scale up conditions
            if (
                avg_cpu > self.scaling_config.scale_up_threshold
                or avg_memory > self.scaling_config.scale_up_threshold
            ):
                if len(self.instances) < self.scaling_config.max_instances:
                    await self.scale_up(
                        1,
                        f"High resource usage (CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%)",
                    )
                    self.last_scale_time = current_time

            # Check scale down conditions
            elif (
                avg_cpu < self.scaling_config.scale_down_threshold
                and avg_memory < self.scaling_config.scale_down_threshold
            ):
                if len(self.instances) > self.scaling_config.min_instances:
                    await self.scale_down(
                        1,
                        f"Low resource usage (CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%)",
                    )
                    self.last_scale_time = current_time

        except Exception as e:
            self.logger.error(f"Failed to check scaling needs: {e}")

    async def _update_instance_health(self) -> None:
        """Update health status of all instances."""
        try:
            for instance_id, instance in self.instances.items():
                # Check if instance is still running
                if not await self._is_instance_running(instance_id):
                    instance.status = "stopped"
                    instance.health_status = "unhealthy"
                    continue

                # Update metrics
                instance.cpu_usage = await self._get_instance_cpu_usage(instance_id)
                instance.memory_usage = await self._get_instance_memory_usage(
                    instance_id
                )
                instance.active_connections = await self._get_instance_connections(
                    instance_id
                )

                # Update health status
                if await self._check_instance_health(instance_id):
                    instance.health_status = "healthy"
                else:
                    instance.health_status = "unhealthy"

        except Exception as e:
            self.logger.error(f"Failed to update instance health: {e}")

    async def _create_instance(self) -> Optional[str]:
        """Create a new application instance."""
        try:
            # Generate instance ID
            instance_id = self._generate_instance_id()

            # Find available port
            port = await self._find_available_port()

            # Create instance info
            instance = InstanceInfo(
                instance_id=instance_id,
                host="localhost",
                port=port,
                status="starting",
                cpu_usage=0.0,
                memory_usage=0.0,
                active_connections=0,
                start_time=self._get_timestamp(),
                health_status="unknown",
            )

            # Start instance process
            if await self._start_instance_process(instance):
                self.instances[instance_id] = instance
                return instance_id
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to create instance: {e}")
            return None

    async def _remove_instance(self, instance_id: str) -> bool:
        """Remove an instance."""
        try:
            if instance_id not in self.instances:
                return False

            # Stop instance
            if await self._stop_instance(instance_id):
                # Remove from instances
                del self.instances[instance_id]
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove instance: {e}")
            return False

    async def _select_instances_to_remove(self, count: int) -> List[str]:
        """Select instances to remove (least healthy first)."""
        # Sort instances by health and resource usage
        sorted_instances = sorted(
            self.instances.items(),
            key=lambda x: (
                x[1].health_status != "healthy",  # Unhealthy first
                x[1].cpu_usage + x[1].memory_usage,  # Lower usage first
            ),
        )

        return [instance_id for instance_id, _ in sorted_instances[:count]]

    async def _start_instance_process(self, instance: InstanceInfo) -> bool:
        """Start instance process."""
        try:
            # This would typically start a new process or container
            # For now, simulate instance creation
            self.logger.info(f"Starting instance process: {instance.instance_id}")

            # Simulate process start
            await asyncio.sleep(2)

            instance.status = "running"
            return True

        except Exception as e:
            self.logger.error(f"Failed to start instance process: {e}")
            return False

    async def _stop_instance(self, instance_id: str) -> bool:
        """Stop an instance."""
        try:
            self.logger.info(f"Stopping instance: {instance_id}")

            # This would typically stop the process or container
            # For now, simulate instance stop
            await asyncio.sleep(1)

            if instance_id in self.instances:
                self.instances[instance_id].status = "stopped"

            return True

        except Exception as e:
            self.logger.error(f"Failed to stop instance: {e}")
            return False

    async def _start_instance(self, instance_id: str) -> bool:
        """Start an instance."""
        try:
            self.logger.info(f"Starting instance: {instance_id}")

            # This would typically start the process or container
            # For now, simulate instance start
            await asyncio.sleep(2)

            if instance_id in self.instances:
                self.instances[instance_id].status = "running"

            return True

        except Exception as e:
            self.logger.error(f"Failed to start instance: {e}")
            return False

    async def _is_instance_running(self, instance_id: str) -> bool:
        """Check if instance is running."""
        try:
            if instance_id not in self.instances:
                return False

            instance = self.instances[instance_id]
            return instance.status == "running"

        except Exception as e:
            self.logger.error(f"Failed to check instance status: {e}")
            return False

    async def _get_instance_cpu_usage(self, instance_id: str) -> float:
        """Get CPU usage for instance."""
        try:
            # This would typically get CPU usage from the process/container
            # For now, return a simulated value
            import random

            return random.uniform(10.0, 90.0)

        except Exception as e:
            self.logger.error(f"Failed to get CPU usage: {e}")
            return 0.0

    async def _get_instance_memory_usage(self, instance_id: str) -> float:
        """Get memory usage for instance."""
        try:
            # This would typically get memory usage from the process/container
            # For now, return a simulated value
            import random

            return random.uniform(20.0, 85.0)

        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    async def _get_instance_connections(self, instance_id: str) -> int:
        """Get active connections for instance."""
        try:
            # This would typically get connection count from the process/container
            # For now, return a simulated value
            import random

            return random.randint(0, 100)

        except Exception as e:
            self.logger.error(f"Failed to get connection count: {e}")
            return 0

    async def _check_instance_health(self, instance_id: str) -> bool:
        """Check instance health."""
        try:
            # This would typically perform a health check
            # For now, return True for running instances
            if instance_id in self.instances:
                return self.instances[instance_id].status == "running"
            return False

        except Exception as e:
            self.logger.error(f"Failed to check instance health: {e}")
            return False

    async def _find_available_port(self) -> int:
        """Find an available port."""
        try:
            import socket

            for port in range(8000, 9000):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(("localhost", port)) != 0:
                        return port

            return 8000  # Fallback

        except Exception as e:
            self.logger.error(f"Failed to find available port: {e}")
            return 8000

    async def _record_scaling_event(
        self, event_type: str, reason: str, instances_before: int, instances_after: int
    ) -> None:
        """Record a scaling event."""
        try:
            event = ScalingEvent(
                event_id=self._generate_event_id(),
                timestamp=self._get_timestamp(),
                event_type=event_type,
                reason=reason,
                instances_before=instances_before,
                instances_after=instances_after,
                metrics={
                    "avg_cpu": (
                        sum(instance.cpu_usage for instance in self.instances.values())
                        / len(self.instances)
                        if self.instances
                        else 0
                    ),
                    "avg_memory": (
                        sum(
                            instance.memory_usage
                            for instance in self.instances.values()
                        )
                        / len(self.instances)
                        if self.instances
                        else 0
                    ),
                },
            )

            self.scaling_events.append(event)

            # Keep only last 100 events
            if len(self.scaling_events) > 100:
                self.scaling_events = self.scaling_events[-100:]

        except Exception as e:
            self.logger.error(f"Failed to record scaling event: {e}")

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID."""
        return self._extracted_from__generate_event_id_3("instance_")

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return self._extracted_from__generate_event_id_3("event_")

    # TODO Rename this here and in `_generate_instance_id` and `_generate_event_id`
    def _extracted_from__generate_event_id_3(self, arg0):
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random

        random_suffix = random.randint(1000, 9999)
        return f"{arg0}{timestamp}_{random_suffix}"

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
