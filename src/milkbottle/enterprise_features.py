"""Enterprise Features for MilkBottle.

This module provides enterprise-grade features including user management,
audit logging, role-based access control, and security enhancements.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()
logger = logging.getLogger("milkbottle.enterprise")


class UserRole(Enum):
    """User roles for access control."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class AuditEventType(Enum):
    """Types of audit events."""

    LOGIN = "login"
    LOGOUT = "logout"
    BOTTLE_EXECUTE = "bottle_execute"
    CONFIG_CHANGE = "config_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_CHANGE = "role_change"
    FILE_ACCESS = "file_access"
    EXPORT_OPERATION = "export_operation"
    ANALYTICS_ACCESS = "analytics_access"
    API_ACCESS = "api_access"


@dataclass
class User:
    """User entity for enterprise features."""

    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Audit event for logging user actions."""

    event_id: str
    timestamp: datetime
    user_id: str
    event_type: AuditEventType
    resource: str
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class Session:
    """User session for authentication."""

    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


class UserManager:
    """User management system."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize user manager.

        Args:
            data_dir: Directory to store user data
        """
        self.data_dir = data_dir or Path.home() / ".milkbottle" / "enterprise"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"

        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}

        self._load_users()
        self._load_sessions()
        self._cleanup_expired_sessions()

    def _load_users(self) -> None:
        """Load users from storage."""
        if self.users_file.exists():
            try:
                with open(self.users_file, "r") as f:
                    data = json.load(f)
                    for user_data in data.values():
                        user = User(
                            username=user_data["username"],
                            email=user_data["email"],
                            role=UserRole(user_data["role"]),
                            is_active=user_data["is_active"],
                            created_at=datetime.fromisoformat(user_data["created_at"]),
                            last_login=(
                                datetime.fromisoformat(user_data["last_login"])
                                if user_data["last_login"]
                                else None
                            ),
                            password_hash=user_data.get("password_hash"),
                            permissions=set(user_data.get("permissions", [])),
                            metadata=user_data.get("metadata", {}),
                        )
                        self.users[user.username] = user
            except Exception as e:
                logger.error(f"Failed to load users: {e}")

    def _save_users(self) -> None:
        """Save users to storage."""
        try:
            data = {}
            for username, user in self.users.items():
                data[username] = {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "last_login": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                    "password_hash": user.password_hash,
                    "permissions": list(user.permissions),
                    "metadata": user.metadata,
                }

            with open(self.users_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")

    def _load_sessions(self) -> None:
        """Load sessions from storage."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r") as f:
                    data = json.load(f)
                    for session_data in data.values():
                        session = Session(
                            session_id=session_data["session_id"],
                            user_id=session_data["user_id"],
                            created_at=datetime.fromisoformat(
                                session_data["created_at"]
                            ),
                            expires_at=datetime.fromisoformat(
                                session_data["expires_at"]
                            ),
                            ip_address=session_data["ip_address"],
                            user_agent=session_data["user_agent"],
                            is_active=session_data["is_active"],
                        )
                        self.sessions[session.session_id] = session
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")

    def _save_sessions(self) -> None:
        """Save sessions to storage."""
        try:
            data = {}
            for session_id, session in self.sessions.items():
                data[session_id] = {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "is_active": session.is_active,
                }

            with open(self.sessions_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        now = datetime.now()
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session.expires_at < now or not session.is_active
        ]

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            self._save_sessions()

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
        permissions: Optional[List[str]] = None,
    ) -> User:
        """Create a new user.

        Args:
            username: Username for the new user
            email: Email address
            password: Plain text password
            role: User role
            permissions: Additional permissions

        Returns:
            Created user object

        Raises:
            ValueError: If username already exists
        """
        if username in self.users:
            raise ValueError(f"User {username} already exists")

        user = User(
            username=username,
            email=email,
            role=role,
            password_hash=self._hash_password(password),
            permissions=set(permissions or []),
        )

        self.users[username] = user
        self._save_users()

        logger.info(f"Created user: {username} with role {role.value}")
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.users.get(username)
        if not user or not user.is_active:
            return None

        if user.password_hash != self._hash_password(password):
            return None

        user.last_login = datetime.now()
        self._save_users()

        logger.info(f"User authenticated: {username}")
        return user

    def create_session(
        self, user: User, ip_address: str, user_agent: str, duration_hours: int = 24
    ) -> Session:
        """Create a new session for a user.

        Args:
            user: User object
            ip_address: IP address of the client
            user_agent: User agent string
            duration_hours: Session duration in hours

        Returns:
            Created session object
        """
        session_id = str(uuid4())
        now = datetime.now()
        expires_at = now + timedelta(hours=duration_hours)

        session = Session(
            session_id=session_id,
            user_id=user.username,
            created_at=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.sessions[session_id] = session
        self._save_sessions()

        logger.info(f"Created session for user: {user.username}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object if valid, None otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None

        if session.expires_at < datetime.now():
            session.is_active = False
            self._save_sessions()
            return None

        return session

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session.

        Args:
            session_id: Session ID

        Returns:
            True if session was invalidated, False if not found
        """
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            self._save_sessions()
            logger.info(f"Invalidated session: {session_id}")
            return True
        return False

    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username.

        Args:
            username: Username

        Returns:
            User object if found, None otherwise
        """
        return self.users.get(username)

    def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        permissions: Optional[List[str]] = None,
    ) -> Optional[User]:
        """Update a user.

        Args:
            username: Username to update
            email: New email address
            role: New role
            is_active: Active status
            permissions: New permissions

        Returns:
            Updated user object if found, None otherwise
        """
        user = self.users.get(username)
        if not user:
            return None

        if email is not None:
            user.email = email
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if permissions is not None:
            user.permissions = set(permissions)

        self._save_users()
        logger.info(f"Updated user: {username}")
        return user

    def delete_user(self, username: str) -> bool:
        """Delete a user.

        Args:
            username: Username to delete

        Returns:
            True if user was deleted, False if not found
        """
        if username in self.users:
            del self.users[username]
            self._save_users()
            logger.info(f"Deleted user: {username}")
            return True
        return False

    def list_users(self) -> List[User]:
        """List all users.

        Returns:
            List of user objects
        """
        return list(self.users.values())

    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission.

        Args:
            user: User object
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        if user.role == UserRole.ADMIN:
            return True

        return permission in user.permissions


class AuditLogger:
    """Audit logging system."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = log_dir or Path.home() / ".milkbottle" / "enterprise" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        user_id: str,
        event_type: AuditEventType,
        resource: str,
        action: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            user_id: ID of the user performing the action
            event_type: Type of audit event
            resource: Resource being accessed
            action: Action being performed
            details: Additional details about the event
            ip_address: IP address of the client
            user_agent: User agent string
            success: Whether the action was successful
            error_message: Error message if action failed

        Returns:
            Created audit event
        """
        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            event_type=event_type,
            resource=resource,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        # Write to daily log file
        log_file = self.log_dir / f"audit_{event.timestamp.strftime('%Y-%m-%d')}.jsonl"

        try:
            with open(log_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "event_id": event.event_id,
                            "timestamp": event.timestamp.isoformat(),
                            "user_id": event.user_id,
                            "event_type": event.event_type.value,
                            "resource": event.resource,
                            "action": event.action,
                            "details": event.details,
                            "ip_address": event.ip_address,
                            "user_agent": event.user_agent,
                            "success": event.success,
                            "error_message": event.error_message,
                        }
                    )
                    + "\n"
                )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

        # Log to console for development
        if not success:
            logger.warning(
                f"Audit event failed: {event_type.value} by {user_id} on {resource}"
            )
        else:
            logger.info(f"Audit event: {event_type.value} by {user_id} on {resource}")

        return event

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource: Optional[str] = None,
        success_only: bool = False,
    ) -> List[AuditEvent]:
        """Get audit events with filtering.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            user_id: User ID for filtering
            event_type: Event type for filtering
            resource: Resource for filtering
            success_only: Only return successful events

        Returns:
            List of audit events
        """
        events = []

        # Determine date range
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        # Read from log files
        current_date = start_date.date()
        end_date_obj = end_date.date()

        while current_date <= end_date_obj:
            log_file = self.log_dir / f"audit_{current_date.strftime('%Y-%m-%d')}.jsonl"

            if log_file.exists():
                try:
                    with open(log_file, "r") as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                event = AuditEvent(
                                    event_id=data["event_id"],
                                    timestamp=datetime.fromisoformat(data["timestamp"]),
                                    user_id=data["user_id"],
                                    event_type=AuditEventType(data["event_type"]),
                                    resource=data["resource"],
                                    action=data["action"],
                                    details=data["details"],
                                    ip_address=data.get("ip_address"),
                                    user_agent=data.get("user_agent"),
                                    success=data["success"],
                                    error_message=data.get("error_message"),
                                )

                                # Apply filters
                                if (
                                    event.timestamp < start_date
                                    or event.timestamp > end_date
                                ):
                                    continue
                                if user_id and event.user_id != user_id:
                                    continue
                                if event_type and event.event_type != event_type:
                                    continue
                                if resource and event.resource != resource:
                                    continue
                                if success_only and not event.success:
                                    continue

                                events.append(event)
                            except Exception as e:
                                logger.error(f"Failed to parse audit log line: {e}")
                except Exception as e:
                    logger.error(f"Failed to read audit log file {log_file}: {e}")

            current_date += timedelta(days=1)

        return sorted(events, key=lambda x: x.timestamp, reverse=True)


class EnterpriseFeatures:
    """Main enterprise features manager."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize enterprise features.

        Args:
            data_dir: Directory to store enterprise data
        """
        self.data_dir = data_dir or Path.home() / ".milkbottle" / "enterprise"
        self.user_manager = UserManager(self.data_dir)
        self.audit_logger = AuditLogger(self.data_dir / "audit")
        self.current_user: Optional[User] = None
        self.current_session: Optional[Session] = None

    def login(
        self,
        username: str,
        password: str,
        ip_address: str = "127.0.0.1",
        user_agent: str = "CLI",
    ) -> bool:
        """Authenticate a user and create a session.

        Args:
            username: Username
            password: Password
            ip_address: IP address
            user_agent: User agent

        Returns:
            True if login successful, False otherwise
        """
        user = self.user_manager.authenticate_user(username, password)
        if not user:
            self.audit_logger.log_event(
                user_id=username,
                event_type=AuditEventType.LOGIN,
                resource="system",
                action="login_attempt",
                details={"username": username},
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Invalid credentials",
            )
            return False

        session = self.user_manager.create_session(user, ip_address, user_agent)
        self.current_user = user
        self.current_session = session

        self.audit_logger.log_event(
            user_id=user.username,
            event_type=AuditEventType.LOGIN,
            resource="system",
            action="login_success",
            details={"username": username, "session_id": session.session_id},
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        return True

    def logout(self) -> None:
        """Logout current user."""
        if self.current_session:
            self.user_manager.invalidate_session(self.current_session.session_id)

            if self.current_user:
                self.audit_logger.log_event(
                    user_id=self.current_user.username,
                    event_type=AuditEventType.LOGOUT,
                    resource="system",
                    action="logout",
                    details={"session_id": self.current_session.session_id},
                    success=True,
                )

        self.current_user = None
        self.current_session = None

    def check_permission(self, permission: str) -> bool:
        """Check if current user has a permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        if not self.current_user:
            return False

        return self.user_manager.has_permission(self.current_user, permission)

    def log_bottle_execution(
        self,
        bottle_name: str,
        input_data: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a bottle execution event.

        Args:
            bottle_name: Name of the bottle being executed
            input_data: Input data for the bottle
            success: Whether execution was successful
            error_message: Error message if execution failed
        """
        if not self.current_user:
            return

        self.audit_logger.log_event(
            user_id=self.current_user.username,
            event_type=AuditEventType.BOTTLE_EXECUTE,
            resource=bottle_name,
            action="execute",
            details={"input_data": input_data},
            success=success,
            error_message=error_message,
        )

    def log_file_access(
        self,
        file_path: str,
        action: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a file access event.

        Args:
            file_path: Path to the file being accessed
            action: Action being performed (read, write, delete, etc.)
            success: Whether action was successful
            error_message: Error message if action failed
        """
        if not self.current_user:
            return

        self.audit_logger.log_event(
            user_id=self.current_user.username,
            event_type=AuditEventType.FILE_ACCESS,
            resource=file_path,
            action=action,
            details={"file_path": file_path},
            success=success,
            error_message=error_message,
        )

    def log_export_operation(
        self,
        file_path: str,
        export_formats: List[str],
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an export operation.

        Args:
            file_path: Path to the file being exported
            export_formats: List of export formats used
            success: Whether export was successful
            error_message: Error message if export failed
        """
        if not self.current_user:
            return

        self.audit_logger.log_event(
            user_id=self.current_user.username,
            event_type=AuditEventType.EXPORT_OPERATION,
            resource=file_path,
            action="export",
            details={"export_formats": export_formats},
            success=success,
            error_message=error_message,
        )

    def log_analytics_access(
        self,
        file_path: str,
        analytics_type: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an analytics access event.

        Args:
            file_path: Path to the file being analyzed
            analytics_type: Type of analytics being performed
            success: Whether analytics was successful
            error_message: Error message if analytics failed
        """
        if not self.current_user:
            return

        self.audit_logger.log_event(
            user_id=self.current_user.username,
            event_type=AuditEventType.ANALYTICS_ACCESS,
            resource=file_path,
            action="analytics",
            details={"analytics_type": analytics_type},
            success=success,
            error_message=error_message,
        )

    def get_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an audit report.

        Args:
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID to filter by

        Returns:
            Audit report data
        """
        events = self.audit_logger.get_events(start_date, end_date, user_id)

        # Calculate statistics
        total_events = len(events)
        successful_events = len([e for e in events if e.success])
        failed_events = total_events - successful_events

        # Group by event type
        event_type_counts = {}
        for event in events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        # Group by user
        user_counts = {}
        for event in events:
            user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1

        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "summary": {
                "total_events": total_events,
                "successful_events": successful_events,
                "failed_events": failed_events,
                "success_rate": (
                    (successful_events / total_events * 100) if total_events > 0 else 0
                ),
            },
            "event_types": event_type_counts,
            "users": user_counts,
            "recent_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "event_type": event.event_type.value,
                    "resource": event.resource,
                    "action": event.action,
                    "success": event.success,
                }
                for event in events[:10]  # Last 10 events
            ],
        }


# Global enterprise features instance
_enterprise_features: Optional[EnterpriseFeatures] = None


def get_enterprise_features() -> EnterpriseFeatures:
    """Get the global enterprise features instance.

    Returns:
        Enterprise features instance
    """
    global _enterprise_features
    if _enterprise_features is None:
        _enterprise_features = EnterpriseFeatures()
    return _enterprise_features


def initialize_enterprise_features(
    data_dir: Optional[Path] = None,
) -> EnterpriseFeatures:
    """Initialize enterprise features with custom data directory.

    Args:
        data_dir: Custom data directory

    Returns:
        Enterprise features instance
    """
    global _enterprise_features
    _enterprise_features = EnterpriseFeatures(data_dir)
    return _enterprise_features


def create_admin_user(username: str, email: str, password: str) -> User:
    """Create an admin user for initial setup.

    Args:
        username: Admin username
        email: Admin email
        password: Admin password

    Returns:
        Created admin user
    """
    enterprise = get_enterprise_features()
    return enterprise.user_manager.create_user(
        username=username,
        email=email,
        password=password,
        role=UserRole.ADMIN,
        permissions=["*"],  # All permissions
    )


def setup_enterprise_features() -> None:
    """Set up enterprise features with initial admin user."""
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
        create_admin_user(username, email, password)
        console.print(f"[green]Admin user '{username}' created successfully![/green]")
        console.print("You can now log in using the enterprise features.")
    except Exception as e:
        console.print(f"[red]Failed to create admin user: {e}[/red]")


@click.command()
@click.option("--setup", is_flag=True, help="Set up enterprise features")
@click.option("--login", is_flag=True, help="Login to enterprise features")
@click.option("--users", is_flag=True, help="List users")
@click.option("--audit", is_flag=True, help="Show audit report")
def enterprise_cli(setup: bool, login: bool, users: bool, audit: bool) -> None:
    """Enterprise features CLI."""
    if setup:
        setup_enterprise_features()
    elif login:
        enterprise = get_enterprise_features()
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)

        if enterprise.login(username, password):
            console.print(f"[green]Welcome, {username}![/green]")
        else:
            console.print("[red]Login failed. Invalid credentials.[/red]")
    elif users:
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
    elif audit:
        enterprise = get_enterprise_features()
        report = enterprise.get_audit_report()

        console.print(
            Panel(
                f"Audit Report\n\n"
                f"Total Events: {report['summary']['total_events']}\n"
                f"Successful: {report['summary']['successful_events']}\n"
                f"Failed: {report['summary']['failed_events']}\n"
                f"Success Rate: {report['summary']['success_rate']:.1f}%",
                title="Enterprise Audit Report",
            )
        )
    else:
        console.print("Use --help to see available options.")


if __name__ == "__main__":
    enterprise_cli()
