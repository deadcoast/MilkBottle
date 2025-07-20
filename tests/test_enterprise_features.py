"""Tests for enterprise features functionality."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from milkbottle.enterprise_features import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    EnterpriseFeatures,
    Session,
    User,
    UserManager,
    UserRole,
    create_admin_user,
    get_enterprise_features,
    initialize_enterprise_features,
)


class TestUser:
    """Test User dataclass."""

    def test_user_creation(self):
        """Test User creation."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.created_at is not None
        assert user.last_login is None
        assert user.password_hash is None
        assert user.permissions == set()
        assert user.metadata == {}

    def test_user_with_all_fields(self):
        """Test User creation with all fields."""
        user = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            password_hash="hashed_password",
            permissions={"user_manage", "audit_view"},
            metadata={"department": "IT"},
        )

        assert user.username == "admin"
        assert user.email == "admin@example.com"
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.password_hash == "hashed_password"
        assert user.permissions == {"user_manage", "audit_view"}
        assert user.metadata == {"department": "IT"}


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    def test_audit_event_creation(self):
        """Test AuditEvent creation."""
        event = AuditEvent(
            event_id="event_123",
            timestamp=datetime.now(),
            user_id="testuser",
            event_type=AuditEventType.LOGIN,
            resource="system",
            action="login",
            details={"ip": "127.0.0.1"},
        )

        assert event.event_id == "event_123"
        assert event.user_id == "testuser"
        assert event.event_type == AuditEventType.LOGIN
        assert event.resource == "system"
        assert event.action == "login"
        assert event.details == {"ip": "127.0.0.1"}
        assert event.success is True
        assert event.error_message is None

    def test_audit_event_with_all_fields(self):
        """Test AuditEvent creation with all fields."""
        event = AuditEvent(
            event_id="event_456",
            timestamp=datetime.now(),
            user_id="admin",
            event_type=AuditEventType.BOTTLE_EXECUTE,
            resource="pdfmilker",
            action="execute",
            details={"file": "test.pdf"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=False,
            error_message="File not found",
        )

        assert event.event_id == "event_456"
        assert event.user_id == "admin"
        assert event.event_type == AuditEventType.BOTTLE_EXECUTE
        assert event.resource == "pdfmilker"
        assert event.action == "execute"
        assert event.details == {"file": "test.pdf"}
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.success is False
        assert event.error_message == "File not found"


class TestSession:
    """Test Session dataclass."""

    def test_session_creation(self):
        """Test Session creation."""
        now = datetime.now()
        expires_at = now + timedelta(hours=24)

        session = Session(
            session_id="session_123",
            user_id="testuser",
            created_at=now,
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="CLI",
        )

        assert session.session_id == "session_123"
        assert session.user_id == "testuser"
        assert session.created_at == now
        assert session.expires_at == expires_at
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "CLI"
        assert session.is_active is True


class TestUserManager:
    """Test UserManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.user_manager = UserManager(self.data_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_user(self):
        """Test user creation."""
        user = self.user_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role=UserRole.USER,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Should be hashed

        # Check that user was saved
        saved_user = self.user_manager.get_user("testuser")
        assert saved_user is not None
        assert saved_user.username == "testuser"

    def test_create_user_duplicate(self):
        """Test creating duplicate user."""
        self.user_manager.create_user("testuser", "test@example.com", "password123")

        with pytest.raises(ValueError, match="User testuser already exists"):
            self.user_manager.create_user(
                "testuser", "test2@example.com", "password456"
            )

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        self.user_manager.create_user("testuser", "test@example.com", "password123")

        user = self.user_manager.authenticate_user("testuser", "password123")
        assert user is not None
        assert user.username == "testuser"
        assert user.last_login is not None

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        self.user_manager.create_user("testuser", "test@example.com", "password123")

        user = self.user_manager.authenticate_user("testuser", "wrongpassword")
        assert user is None

    def test_authenticate_user_nonexistent(self):
        """Test authentication with nonexistent user."""
        user = self.user_manager.authenticate_user("nonexistent", "password123")
        assert user is None

    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        user.is_active = False
        self.user_manager._save_users()

        auth_user = self.user_manager.authenticate_user("testuser", "password123")
        assert auth_user is None

    def test_create_session(self):
        """Test session creation."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )

        session = self.user_manager.create_session(
            user, "127.0.0.1", "CLI", duration_hours=24
        )

        assert session.user_id == "testuser"
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "CLI"
        assert session.is_active is True
        assert session.expires_at > datetime.now()

    def test_get_session_valid(self):
        """Test getting valid session."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        session = self.user_manager.create_session(user, "127.0.0.1", "CLI")

        retrieved_session = self.user_manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id

    def test_get_session_invalid(self):
        """Test getting invalid session."""
        session = self.user_manager.get_session("nonexistent_session")
        assert session is None

    def test_get_session_expired(self):
        """Test getting expired session."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        session = self.user_manager.create_session(
            user, "127.0.0.1", "CLI", duration_hours=0
        )

        # Manually set expiration to past
        session.expires_at = datetime.now() - timedelta(hours=1)
        self.user_manager._save_sessions()

        retrieved_session = self.user_manager.get_session(session.session_id)
        assert retrieved_session is None

    def test_invalidate_session(self):
        """Test session invalidation."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        session = self.user_manager.create_session(user, "127.0.0.1", "CLI")

        result = self.user_manager.invalidate_session(session.session_id)
        assert result is True

        retrieved_session = self.user_manager.get_session(session.session_id)
        assert retrieved_session is None

    def test_invalidate_nonexistent_session(self):
        """Test invalidating nonexistent session."""
        result = self.user_manager.invalidate_session("nonexistent_session")
        assert result is False

    def test_update_user(self):
        """Test user update."""
        user = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )

        updated_user = self.user_manager.update_user(
            "testuser",
            email="newemail@example.com",
            role=UserRole.ADMIN,
            is_active=False,
        )

        assert updated_user is not None
        assert updated_user.email == "newemail@example.com"
        assert updated_user.role == UserRole.ADMIN
        assert updated_user.is_active is False

        # Verify changes were saved
        saved_user = self.user_manager.get_user("testuser")
        assert saved_user.email == "newemail@example.com"
        assert saved_user.role == UserRole.ADMIN
        assert saved_user.is_active is False

    def test_update_nonexistent_user(self):
        """Test updating nonexistent user."""
        updated_user = self.user_manager.update_user(
            "nonexistent", email="new@example.com"
        )
        assert updated_user is None

    def test_delete_user(self):
        """Test user deletion."""
        self.user_manager.create_user("testuser", "test@example.com", "password123")

        result = self.user_manager.delete_user("testuser")
        assert result is True

        user = self.user_manager.get_user("testuser")
        assert user is None

    def test_delete_nonexistent_user(self):
        """Test deleting nonexistent user."""
        result = self.user_manager.delete_user("nonexistent")
        assert result is False

    def test_list_users(self):
        """Test listing users."""
        self.user_manager.create_user("user1", "user1@example.com", "password123")
        self.user_manager.create_user("user2", "user2@example.com", "password456")

        users = self.user_manager.list_users()
        assert len(users) == 2
        usernames = [user.username for user in users]
        assert "user1" in usernames
        assert "user2" in usernames

    def test_has_permission_admin(self):
        """Test admin permission check."""
        user = User("admin", "admin@example.com", UserRole.ADMIN)

        # Admin should have all permissions
        assert self.user_manager.has_permission(user, "any_permission") is True
        assert self.user_manager.has_permission(user, "another_permission") is True

    def test_has_permission_user(self):
        """Test user permission check."""
        user = User("user", "user@example.com", UserRole.USER)
        user.permissions = {"read_files", "write_files"}

        assert self.user_manager.has_permission(user, "read_files") is True
        assert self.user_manager.has_permission(user, "write_files") is True
        assert self.user_manager.has_permission(user, "admin_access") is False


class TestAuditLogger:
    """Test AuditLogger functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)
        self.audit_logger = AuditLogger(self.log_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_event(self):
        """Test logging an event."""
        event = self.audit_logger.log_event(
            user_id="testuser",
            event_type=AuditEventType.LOGIN,
            resource="system",
            action="login",
            details={"ip": "127.0.0.1"},
        )

        assert event.user_id == "testuser"
        assert event.event_type == AuditEventType.LOGIN
        assert event.resource == "system"
        assert event.action == "login"
        assert event.details == {"ip": "127.0.0.1"}
        assert event.success is True

        # Check that log file was created
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        assert log_file.exists()

    def test_log_event_failure(self):
        """Test logging a failed event."""
        event = self.audit_logger.log_event(
            user_id="testuser",
            event_type=AuditEventType.LOGIN,
            resource="system",
            action="login",
            details={"ip": "127.0.0.1"},
            success=False,
            error_message="Invalid credentials",
        )

        assert event.success is False
        assert event.error_message == "Invalid credentials"

    def test_get_events_no_filters(self):
        """Test getting events without filters."""
        # Log some events
        self.audit_logger.log_event(
            "user1", AuditEventType.LOGIN, "system", "login", {}
        )
        self.audit_logger.log_event(
            "user2", AuditEventType.LOGOUT, "system", "logout", {}
        )

        events = self.audit_logger.get_events()
        assert len(events) >= 2

        # Check that events are sorted by timestamp (newest first)
        timestamps = [event.timestamp for event in events]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_events_with_filters(self):
        """Test getting events with filters."""
        # Log events
        self.audit_logger.log_event(
            "user1", AuditEventType.LOGIN, "system", "login", {}
        )
        self.audit_logger.log_event(
            "user2", AuditEventType.LOGOUT, "system", "logout", {}
        )
        self.audit_logger.log_event(
            "user1", AuditEventType.BOTTLE_EXECUTE, "pdfmilker", "execute", {}
        )

        # Filter by user
        events = self.audit_logger.get_events(user_id="user1")
        assert all(event.user_id == "user1" for event in events)

        # Filter by event type
        events = self.audit_logger.get_events(event_type=AuditEventType.LOGIN)
        assert all(event.event_type == AuditEventType.LOGIN for event in events)

        # Filter by resource
        events = self.audit_logger.get_events(resource="pdfmilker")
        assert all(event.resource == "pdfmilker" for event in events)

        # Filter by success only
        events = self.audit_logger.get_events(success_only=True)
        assert all(event.success for event in events)

    def test_get_events_date_range(self):
        """Test getting events with date range."""
        # Log events
        self.audit_logger.log_event(
            "user1", AuditEventType.LOGIN, "system", "login", {}
        )

        # Get events for today
        today = datetime.now().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())

        events = self.audit_logger.get_events(start_date=start_date, end_date=end_date)
        assert len(events) >= 1

        # Get events for yesterday (should be empty)
        yesterday = today - timedelta(days=1)
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday, datetime.max.time())

        events = self.audit_logger.get_events(start_date=start_date, end_date=end_date)
        assert len(events) == 0


class TestEnterpriseFeatures:
    """Test EnterpriseFeatures functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.enterprise = EnterpriseFeatures(self.data_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_login_success(self):
        """Test successful login."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )

        result = self.enterprise.login("testuser", "password123")
        assert result is True
        assert self.enterprise.current_user is not None
        assert self.enterprise.current_user.username == "testuser"
        assert self.enterprise.current_session is not None

    def test_login_failure(self):
        """Test failed login."""
        result = self.enterprise.login("nonexistent", "password123")
        assert result is False
        assert self.enterprise.current_user is None
        assert self.enterprise.current_session is None

    def test_logout(self):
        """Test logout."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        self.enterprise.logout()
        assert self.enterprise.current_user is None
        assert self.enterprise.current_session is None

    def test_check_permission_logged_out(self):
        """Test permission check when not logged in."""
        result = self.enterprise.check_permission("any_permission")
        assert result is False

    def test_check_permission_logged_in(self):
        """Test permission check when logged in."""
        user = self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        user.permissions = {"read_files"}
        self.enterprise.user_manager._save_users()

        self.enterprise.login("testuser", "password123")

        assert self.enterprise.check_permission("read_files") is True
        assert self.enterprise.check_permission("write_files") is False

    def test_log_bottle_execution(self):
        """Test logging bottle execution."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        self.enterprise.log_bottle_execution("pdfmilker", {"file": "test.pdf"})

        # Check that event was logged
        events = self.enterprise.audit_logger.get_events()
        bottle_events = [
            e for e in events if e.event_type == AuditEventType.BOTTLE_EXECUTE
        ]
        assert len(bottle_events) >= 1

    def test_log_file_access(self):
        """Test logging file access."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        self.enterprise.log_file_access("test.pdf", "read")

        # Check that event was logged
        events = self.enterprise.audit_logger.get_events()
        file_events = [e for e in events if e.event_type == AuditEventType.FILE_ACCESS]
        assert len(file_events) >= 1

    def test_log_export_operation(self):
        """Test logging export operation."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        self.enterprise.log_export_operation("test.pdf", ["pdf", "markdown"])

        # Check that event was logged
        events = self.enterprise.audit_logger.get_events()
        export_events = [
            e for e in events if e.event_type == AuditEventType.EXPORT_OPERATION
        ]
        assert len(export_events) >= 1

    def test_log_analytics_access(self):
        """Test logging analytics access."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        self.enterprise.log_analytics_access("test.pdf", "quality_assessment")

        # Check that event was logged
        events = self.enterprise.audit_logger.get_events()
        analytics_events = [
            e for e in events if e.event_type == AuditEventType.ANALYTICS_ACCESS
        ]
        assert len(analytics_events) >= 1

    def test_get_audit_report(self):
        """Test getting audit report."""
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        # Log some events
        self.enterprise.log_bottle_execution("pdfmilker", {"file": "test.pdf"})
        self.enterprise.log_file_access("test.pdf", "read")

        report = self.enterprise.get_audit_report()

        assert "summary" in report
        assert "total_events" in report["summary"]
        assert "successful_events" in report["summary"]
        assert "failed_events" in report["summary"]
        assert "success_rate" in report["summary"]
        assert "event_types" in report
        assert "users" in report
        assert "recent_events" in report

        assert report["summary"]["total_events"] >= 2
        assert report["summary"]["success_rate"] >= 0


class TestEnterpriseFunctions:
    """Test enterprise utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_admin_user(self):
        """Test creating admin user."""
        import time

        unique_username = f"testadmin_{int(time.time())}"
        unique_email = f"{unique_username}@example.com"

        user = create_admin_user(unique_username, unique_email, "adminpass")

        assert user.username == unique_username
        assert user.email == unique_email
        assert user.role == UserRole.ADMIN
        assert "*" in user.permissions  # All permissions

    def test_get_enterprise_features_singleton(self):
        """Test that get_enterprise_features returns the same instance."""
        enterprise1 = get_enterprise_features()
        enterprise2 = get_enterprise_features()

        assert enterprise1 is enterprise2

    def test_initialize_enterprise_features(self):
        """Test initializing enterprise features with custom data directory."""
        enterprise = initialize_enterprise_features(self.data_dir)

        assert enterprise.data_dir == self.data_dir
        assert enterprise.user_manager.data_dir == self.data_dir
        assert enterprise.audit_logger.log_dir == self.data_dir / "audit"


class TestEnterpriseIntegration:
    """Test enterprise features integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.enterprise = EnterpriseFeatures(self.data_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_workflow(self):
        """Test complete enterprise workflow."""
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create admin user using the test enterprise instance
        admin_user = self.enterprise.user_manager.create_user(
            "admin", "admin@example.com", "adminpass", UserRole.ADMIN, permissions=["*"]
        )
        assert admin_user.role == UserRole.ADMIN

        # Login as admin
        result = self.enterprise.login("admin", "adminpass")
        assert result is True
        assert self.enterprise.current_user.username == "admin"

        # Create regular user
        regular_user = self.enterprise.user_manager.create_user(
            "user1", "user1@example.com", "userpass", UserRole.USER
        )
        assert regular_user.role == UserRole.USER

        # Log some activities
        self.enterprise.log_bottle_execution("pdfmilker", {"file": "test.pdf"})
        self.enterprise.log_file_access("test.pdf", "read")
        self.enterprise.log_export_operation("test.pdf", ["pdf", "markdown"])

        # Get audit report
        report = self.enterprise.get_audit_report()
        assert report["summary"]["total_events"] >= 3

        # Logout
        self.enterprise.logout()
        assert self.enterprise.current_user is None

        # Login as regular user
        result = self.enterprise.login("user1", "userpass")
        assert result is True
        assert self.enterprise.current_user.username == "user1"

        # Check permissions
        assert (
            self.enterprise.check_permission("read_files") is False
        )  # No specific permissions
        assert self.enterprise.check_permission("admin_access") is False

    def test_permission_system(self):
        """Test permission system."""
        # Create users with different roles
        admin_user = self.enterprise.user_manager.create_user(
            "admin", "admin@example.com", "adminpass", UserRole.ADMIN
        )
        manager_user = self.enterprise.user_manager.create_user(
            "manager", "manager@example.com", "managerpass", UserRole.MANAGER
        )
        regular_user = self.enterprise.user_manager.create_user(
            "user", "user@example.com", "userpass", UserRole.USER
        )

        # Admin should have all permissions
        assert (
            self.enterprise.user_manager.has_permission(admin_user, "any_permission")
            is True
        )

        # Manager and user need specific permissions
        assert (
            self.enterprise.user_manager.has_permission(manager_user, "any_permission")
            is False
        )
        assert (
            self.enterprise.user_manager.has_permission(regular_user, "any_permission")
            is False
        )

        # Add specific permissions
        manager_user.permissions = {"user_manage"}
        regular_user.permissions = {"read_files"}
        self.enterprise.user_manager._save_users()

        assert (
            self.enterprise.user_manager.has_permission(manager_user, "user_manage")
            is True
        )
        assert (
            self.enterprise.user_manager.has_permission(regular_user, "read_files")
            is True
        )
        assert (
            self.enterprise.user_manager.has_permission(regular_user, "write_files")
            is False
        )

    def test_session_management(self):
        """Test session management."""
        # Create user and login
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        result = self.enterprise.login("testuser", "password123")
        assert result is True

        # Get session
        session = self.enterprise.current_session
        assert session is not None
        assert session.user_id == "testuser"

        # Verify session is valid
        retrieved_session = self.enterprise.user_manager.get_session(session.session_id)
        assert retrieved_session is not None

        # Invalidate session
        self.enterprise.user_manager.invalidate_session(session.session_id)
        retrieved_session = self.enterprise.user_manager.get_session(session.session_id)
        assert retrieved_session is None

    def test_audit_logging_comprehensive(self):
        """Test comprehensive audit logging."""
        # Create user and login
        self.enterprise.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.enterprise.login("testuser", "password123")

        # Log various types of events
        self.enterprise.log_bottle_execution(
            "pdfmilker", {"file": "test.pdf"}, success=True
        )
        self.enterprise.log_bottle_execution(
            "venvmilker",
            {"project": "test"},
            success=False,
            error_message="Project not found",
        )

        self.enterprise.log_file_access("test.pdf", "read", success=True)
        self.enterprise.log_file_access(
            "nonexistent.pdf", "read", success=False, error_message="File not found"
        )

        self.enterprise.log_export_operation(
            "test.pdf", ["pdf", "markdown"], success=True
        )
        self.enterprise.log_analytics_access(
            "test.pdf", "quality_assessment", success=True
        )

        # Get events with different filters
        all_events = self.enterprise.audit_logger.get_events()
        assert len(all_events) >= 6

        # Filter by success
        successful_events = self.enterprise.audit_logger.get_events(success_only=True)
        failed_events = [e for e in all_events if not e.success]

        assert len(successful_events) + len(failed_events) == len(all_events)

        # Filter by event type
        bottle_events = self.enterprise.audit_logger.get_events(
            event_type=AuditEventType.BOTTLE_EXECUTE
        )
        file_events = self.enterprise.audit_logger.get_events(
            event_type=AuditEventType.FILE_ACCESS
        )

        assert len(bottle_events) >= 2
        assert len(file_events) >= 2

        # Check that failed events have error messages
        failed_bottle_events = [e for e in bottle_events if not e.success]
        assert len(failed_bottle_events) >= 1
        assert failed_bottle_events[0].error_message is not None
