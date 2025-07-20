"""Backup Manager - Data backup and recovery management."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import MilkBottleConfig


@dataclass
class BackupConfig:
    """Backup configuration."""

    backup_dir: str = "~/.milkbottle/backups"
    retention_days: int = 30
    compression: bool = True
    encryption: bool = False
    encryption_key: Optional[str] = None
    include_logs: bool = True
    include_config: bool = True
    include_data: bool = True
    exclude_patterns: List[str] = field(default_factory=list)


@dataclass
class BackupInfo:
    """Backup information."""

    backup_id: str
    timestamp: str
    size: int
    type: str  # full, incremental, differential
    status: str  # completed, failed, in_progress
    files_count: int
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackupManager:
    """Data backup and recovery management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.backup_config = BackupConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.backup")
        self.backup_dir = Path(self.backup_config.backup_dir).expanduser()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(
        self, backup_type: str = "full", description: Optional[str] = None
    ) -> Optional[str]:
        """Create a new backup."""
        try:
            self.logger.info(f"Creating {backup_type} backup")

            # Generate backup ID
            backup_id = self._generate_backup_id()

            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=self._get_timestamp(),
                size=0,
                type=backup_type,
                status="in_progress",
                files_count=0,
                checksum="",
                metadata={"description": description or ""},
            )

            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)

            # Collect files to backup
            files_to_backup = await self._collect_files_to_backup()

            # Create backup
            success = await self._create_backup_archive(
                backup_path, files_to_backup, backup_info
            )

            if success:
                # Update backup info
                backup_info.status = "completed"
                backup_info.size = backup_path.stat().st_size
                backup_info.files_count = len(files_to_backup)
                backup_info.checksum = await self._calculate_checksum(backup_path)

                # Save backup info
                await self._save_backup_info(backup_info)

                self.logger.info(f"Backup {backup_id} completed successfully")
                return backup_id
            else:
                backup_info.status = "failed"
                await self._save_backup_info(backup_info)
                self.logger.error(f"Backup {backup_id} failed")
                return None

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    async def restore_backup(
        self, backup_id: str, target_dir: Optional[str] = None
    ) -> bool:
        """Restore from backup."""
        try:
            self.logger.info(f"Restoring from backup: {backup_id}")

            # Load backup info
            backup_info = await self._load_backup_info(backup_id)
            if not backup_info:
                self.logger.error(f"Backup {backup_id} not found")
                return False

            # Set target directory
            restore_dir = Path(target_dir) if target_dir else Path.cwd()
            restore_dir.mkdir(parents=True, exist_ok=True)

            # Restore backup
            backup_path = self.backup_dir / backup_id / f"{backup_id}.tar.gz"
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            success = await self._restore_backup_archive(backup_path, restore_dir)

            if success:
                self.logger.info(
                    f"Successfully restored backup {backup_id} to {restore_dir}"
                )
                return True
            else:
                self.logger.error(f"Failed to restore backup {backup_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False

    async def list_backups(self) -> List[BackupInfo]:
        """List all available backups."""
        try:
            backups = []

            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    backup_info = await self._load_backup_info(backup_dir.name)
                    if backup_info:
                        backups.append(backup_info)

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)
            return backups

        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        try:
            self.logger.info(f"Deleting backup: {backup_id}")

            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
                self.logger.info(f"Successfully deleted backup {backup_id}")
                return True
            else:
                self.logger.error(f"Backup {backup_id} not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to delete backup: {e}")
            return False

    async def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy."""
        try:
            self.logger.info("Cleaning up old backups")

            cutoff_date = datetime.now() - timedelta(
                days=self.backup_config.retention_days
            )
            deleted_count = 0

            backups = await self.list_backups()
            for backup in backups:
                backup_date = datetime.strptime(backup.timestamp, "%Y-%m-%d %H:%M:%S")
                if backup_date < cutoff_date and await self.delete_backup(
                    backup.backup_id
                ):
                    deleted_count += 1

            self.logger.info(f"Deleted {deleted_count} old backups")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0

    async def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        try:
            self.logger.info(f"Verifying backup: {backup_id}")

            # Load backup info
            backup_info = await self._load_backup_info(backup_id)
            if not backup_info:
                self.logger.error(f"Backup {backup_id} not found")
                return False

            # Check backup file exists
            backup_path = self.backup_dir / backup_id / f"{backup_id}.tar.gz"
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_path)
            if current_checksum != backup_info.checksum:
                self.logger.error(f"Backup checksum mismatch for {backup_id}")
                return False

            # Test archive integrity
            try:
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.getmembers()  # This will raise an error if archive is corrupted
                self.logger.info(f"Backup {backup_id} verification successful")
                return True
            except Exception as e:
                self.logger.error(f"Backup archive corrupted: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to verify backup: {e}")
            return False

    async def _collect_files_to_backup(self) -> List[Path]:
        """Collect files to include in backup."""
        files_to_backup = []

        # Add configuration files
        if self.backup_config.include_config:
            config_files = [
                Path("milkbottle.toml"),
                Path("pyproject.toml"),
                Path("requirements.txt"),
            ]
            files_to_backup.extend(
                config_file for config_file in config_files if config_file.exists()
            )
        # Add data files
        if self.backup_config.include_data:
            data_dirs = [
                Path.home() / ".milkbottle" / "data",
                Path.home() / ".milkbottle" / "plugins",
                Path.home() / ".milkbottle" / "marketplace_cache",
            ]
            for data_dir in data_dirs:
                if data_dir.exists():
                    files_to_backup.extend(
                        file_path
                        for file_path in data_dir.rglob("*")
                        if file_path.is_file()
                        and not self._should_exclude_file(file_path)
                    )
        # Add log files
        if self.backup_config.include_logs:
            log_dirs = [Path.home() / ".milkbottle" / "logs"]
            for log_dir in log_dirs:
                if log_dir.exists():
                    files_to_backup.extend(iter(log_dir.glob("*.log")))
        return files_to_backup

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from backup."""
        return any(
            pattern in str(file_path) for pattern in self.backup_config.exclude_patterns
        )

    async def _create_backup_archive(
        self, backup_path: Path, files: List[Path], backup_info: BackupInfo
    ) -> bool:
        """Create backup archive."""
        try:
            archive_path = backup_path / f"{backup_info.backup_id}.tar.gz"

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating backup archive", total=len(files))

                with tarfile.open(archive_path, "w:gz") as tar:
                    for file_path in files:
                        try:
                            # Add file to archive with relative path
                            arcname = file_path.relative_to(Path.cwd())
                            tar.add(file_path, arcname=arcname)
                            progress.update(task, advance=1)
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to add {file_path} to backup: {e}"
                            )
                            continue

                progress.update(task, completed=True)

            return True

        except Exception as e:
            self.logger.error(f"Failed to create backup archive: {e}")
            return False

    async def _restore_backup_archive(
        self, archive_path: Path, target_dir: Path
    ) -> bool:
        """Restore backup archive."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Restoring backup archive", total=None)

                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(target_dir)

                progress.update(task, completed=True)

            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup archive: {e}")
            return False

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum: {e}")
            return ""

    async def _save_backup_info(self, backup_info: BackupInfo) -> None:
        """Save backup information."""
        try:
            info_file = self.backup_dir / backup_info.backup_id / "backup_info.json"
            with open(info_file, "w") as f:
                json.dump(backup_info.__dict__, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save backup info: {e}")

    async def _load_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Load backup information."""
        try:
            info_file = self.backup_dir / backup_id / "backup_info.json"
            if info_file.exists():
                with open(info_file, "r") as f:
                    data = json.load(f)
                    return BackupInfo(**data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to load backup info: {e}")
            return None

    def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
