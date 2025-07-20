"""Tests for the deployment system."""

from unittest.mock import Mock, patch

import pytest

from src.milkbottle.config import MilkBottleConfig
from src.milkbottle.deployment import (
    BackupManager,
    CICDManager,
    DeploymentManager,
    DockerManager,
    MonitoringManager,
    ScalingManager,
    SecurityManager,
)


class TestDeploymentManager:
    """Test DeploymentManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def deployment_manager(self, config):
        """Create DeploymentManager instance."""
        return DeploymentManager(config)

    @pytest.mark.asyncio
    async def test_deploy_application(self, deployment_manager):
        """Test application deployment."""
        with (
            patch.object(deployment_manager, "_create_backup") as mock_backup,
            patch.object(deployment_manager, "_deploy_files") as mock_deploy,
            patch.object(deployment_manager, "_run_tests") as mock_tests,
        ):

            mock_backup.return_value = True
            mock_deploy.return_value = True
            mock_tests.return_value = True

            result = await deployment_manager.deploy_application()
            assert result is True

    @pytest.mark.asyncio
    async def test_rollback_deployment(self, deployment_manager):
        """Test deployment rollback."""
        with patch.object(deployment_manager, "_restore_backup") as mock_restore:
            mock_restore.return_value = True

            result = await deployment_manager.rollback_deployment()
            assert result is True


class TestScalingManager:
    """Test ScalingManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def scaling_manager(self, config):
        """Create ScalingManager instance."""
        return ScalingManager(config)

    @pytest.mark.asyncio
    async def test_scale_up(self, scaling_manager):
        """Test scaling up functionality."""
        with patch.object(scaling_manager, "_create_instance") as mock_create:
            mock_create.return_value = "instance_123"

            result = await scaling_manager.scale_up(1)
            assert result is True
            assert len(scaling_manager.instances) == 1

    @pytest.mark.asyncio
    async def test_scale_down(self, scaling_manager):
        """Test scaling down functionality."""
        # First scale up
        with patch.object(scaling_manager, "_create_instance") as mock_create:
            mock_create.return_value = "instance_123"
            await scaling_manager.scale_up(1)

        # Then scale down
        with patch.object(scaling_manager, "_remove_instance") as mock_remove:
            mock_remove.return_value = True

            result = await scaling_manager.scale_down(1)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_instances(self, scaling_manager):
        """Test getting instances."""
        instances = await scaling_manager.get_instances()
        assert isinstance(instances, list)


class TestSecurityManager:
    """Test SecurityManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def security_manager(self, config):
        """Create SecurityManager instance."""
        return SecurityManager(config)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, security_manager):
        """Test successful user authentication."""
        result = await security_manager.authenticate_user("admin", "admin123")
        assert result is True

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self, security_manager):
        """Test failed user authentication."""
        result = await security_manager.authenticate_user("admin", "wrong_password")
        assert result is False

    @pytest.mark.asyncio
    async def test_create_user(self, security_manager):
        """Test user creation."""
        result = await security_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        assert result is True
        assert "testuser" in security_manager.users

    @pytest.mark.asyncio
    async def test_check_permission(self, security_manager):
        """Test permission checking."""
        # Create admin user first
        await security_manager.create_user(
            "admin", "admin@example.com", "admin123", "admin"
        )

        result = await security_manager.check_permission("admin", "read")
        assert result is True

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_data(self, security_manager):
        """Test data encryption and decryption."""
        test_data = "sensitive information"

        encrypted = await security_manager.encrypt_data(test_data)
        decrypted = await security_manager.decrypt_data(encrypted)

        assert decrypted == test_data


class TestMonitoringManager:
    """Test MonitoringManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def monitoring_manager(self, config):
        """Create MonitoringManager instance."""
        return MonitoringManager(config)

    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, monitoring_manager):
        """Test system metrics collection."""
        with (
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
            patch("psutil.net_io_counters") as mock_network,
        ):

            mock_memory.return_value.percent = 60.0
            mock_disk.return_value.percent = 40.0
            mock_network.return_value.bytes_sent = 1000
            mock_network.return_value.bytes_recv = 2000
            mock_network.return_value.packets_sent = 10
            mock_network.return_value.packets_recv = 20

            metrics = await monitoring_manager.collect_system_metrics()
            assert metrics is not None
            assert hasattr(metrics, "cpu_percent")
            assert hasattr(metrics, "memory_percent")

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitoring_manager):
        """Test monitoring start."""
        with patch.object(monitoring_manager, "collect_system_metrics") as mock_collect:
            mock_collect.return_value = Mock()

            result = await monitoring_manager.start_monitoring()
            assert result is True


class TestBackupManager:
    """Test BackupManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def backup_manager(self, config):
        """Create BackupManager instance."""
        return BackupManager(config)

    @pytest.mark.asyncio
    async def test_create_backup(self, backup_manager):
        """Test backup creation."""
        with (
            patch.object(backup_manager, "_compress_data") as mock_compress,
            patch.object(backup_manager, "_encrypt_backup") as mock_encrypt,
        ):

            mock_compress.return_value = True
            mock_encrypt.return_value = True

            result = await backup_manager.create_backup()
            assert result is True

    @pytest.mark.asyncio
    async def test_restore_backup(self, backup_manager):
        """Test backup restoration."""
        with (
            patch.object(backup_manager, "_decrypt_backup") as mock_decrypt,
            patch.object(backup_manager, "_extract_backup") as mock_extract,
        ):

            mock_decrypt.return_value = True
            mock_extract.return_value = True

            result = await backup_manager.restore_backup("backup_123")
            assert result is True


class TestDockerManager:
    """Test DockerManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def docker_manager(self, config):
        """Create DockerManager instance."""
        return DockerManager(config)

    @pytest.mark.asyncio
    async def test_build_image(self, docker_manager):
        """Test Docker image building."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = await docker_manager.build_image()
            assert result is True

    @pytest.mark.asyncio
    async def test_run_container(self, docker_manager):
        """Test container running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = await docker_manager.run_container()
            assert result is True


class TestCICDManager:
    """Test CICDManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def cicd_manager(self, config):
        """Create CICDManager instance."""
        return CICDManager(config)

    @pytest.mark.asyncio
    async def test_run_pipeline(self, cicd_manager):
        """Test pipeline execution."""
        with patch.object(cicd_manager, "_run_stage") as mock_stage:
            mock_stage.return_value = True

            result = await cicd_manager.run_pipeline()
            assert result is True

    @pytest.mark.asyncio
    async def test_get_pipeline_status(self, cicd_manager):
        """Test pipeline status retrieval."""
        status = await cicd_manager.get_pipeline_status()
        assert isinstance(status, dict)
