"""Security Manager - Application security and access control management."""

from __future__ import annotations

import hashlib
import logging
import secrets
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import cryptography.fernet
from rich.console import Console

from ..config import MilkBottleConfig


@dataclass
class SecurityConfig:
    """Security configuration."""

    encryption_enabled: bool = True
    ssl_enabled: bool = True
    access_control_enabled: bool = True
    audit_logging_enabled: bool = True
    password_policy_enabled: bool = True
    session_timeout: int = 3600  # seconds
    max_login_attempts: int = 5
    lockout_duration: int = 900  # seconds
    require_2fa: bool = False
    allowed_ips: List[str] = field(default_factory=list)
    blocked_ips: List[str] = field(default_factory=list)


@dataclass
class User:
    """User information."""

    username: str
    email: str
    role: str  # admin, user, guest
    permissions: List[str] = field(default_factory=list)
    last_login: Optional[str] = None
    failed_attempts: int = 0
    locked_until: Optional[str] = None
    two_factor_enabled: bool = False


@dataclass
class SecurityEvent:
    """Security event information."""

    event_id: str
    timestamp: str
    event_type: str  # login, logout, access_denied, etc.
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CertificateInfo:
    """SSL certificate information."""

    subject: str
    issuer: str
    valid_from: str
    valid_until: str
    serial_number: str
    fingerprint: str


class SecurityManager:
    """Application security and access control management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.security_config = SecurityConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.security")
        self.users: Dict[str, User] = {}
        self.security_events: List[SecurityEvent] = []
        self.encryption_key: Optional[bytes] = None
        self.cipher_suite: Optional[cryptography.fernet.Fernet] = None

        # Initialize security components
        self._initialize_encryption()
        self._load_users()

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Authenticate a user."""
        try:
            # Check if user exists
            if username not in self.users:
                await self._record_security_event(
                    "login_failed",
                    username,
                    ip_address,
                    user_agent,
                    {"reason": "user_not_found"},
                )
                return False

            user = self.users[username]

            # Check if account is locked
            if user.locked_until:
                lock_time = datetime.strptime(user.locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_time:
                    await self._record_security_event(
                        "login_failed",
                        username,
                        ip_address,
                        user_agent,
                        {"reason": "account_locked", "locked_until": user.locked_until},
                    )
                    return False
                else:
                    # Unlock account
                    user.locked_until = None
                    user.failed_attempts = 0

            # Check IP restrictions
            if not await self._check_ip_access(ip_address):
                await self._record_security_event(
                    "access_denied",
                    username,
                    ip_address,
                    user_agent,
                    {"reason": "ip_restricted"},
                )
                return False

            # Verify password (simplified for demo)
            if await self._verify_password(username, password):
                # Reset failed attempts
                user.failed_attempts = 0
                user.last_login = self._get_timestamp()

                await self._record_security_event(
                    "login_success",
                    username,
                    ip_address,
                    user_agent,
                    {"role": user.role},
                )

                return True
            else:
                # Increment failed attempts
                user.failed_attempts += 1

                # Check if account should be locked
                if user.failed_attempts >= self.security_config.max_login_attempts:
                    lock_until = datetime.now() + timedelta(
                        seconds=self.security_config.lockout_duration
                    )
                    user.locked_until = lock_until.strftime("%Y-%m-%d %H:%M:%S")

                    await self._record_security_event(
                        "account_locked",
                        username,
                        ip_address,
                        user_agent,
                        {
                            "reason": "max_attempts_exceeded",
                            "locked_until": user.locked_until,
                        },
                    )
                else:
                    await self._record_security_event(
                        "login_failed",
                        username,
                        ip_address,
                        user_agent,
                        {
                            "reason": "invalid_password",
                            "failed_attempts": user.failed_attempts,
                        },
                    )

                return False

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    async def create_user(
        self, username: str, email: str, password: str, role: str = "user"
    ) -> bool:
        """Create a new user."""
        try:
            if username in self.users:
                self.logger.error(f"User {username} already exists")
                return False

            # Hash password
            hashed_password = await self._hash_password(password)

            # Create user
            user = User(
                username=username,
                email=email,
                role=role,
                permissions=await self._get_default_permissions(role),
            )

            # Store user (in production, this would be in a database)
            self.users[username] = user

            # Store hashed password
            await self._store_password(username, hashed_password)

            await self._record_security_event(
                "user_created", username, None, None, {"email": email, "role": role}
            )

            self.logger.info(f"Created user: {username}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False

    async def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        try:
            if username not in self.users:
                return False

            # Verify old password
            if not await self._verify_password(username, old_password):
                await self._record_security_event(
                    "password_change_failed",
                    username,
                    None,
                    None,
                    {"reason": "invalid_old_password"},
                )
                return False

            # Hash new password
            hashed_password = await self._hash_password(new_password)

            # Store new password
            await self._store_password(username, hashed_password)

            await self._record_security_event(
                "password_changed", username, None, None, {}
            )

            self.logger.info(f"Password changed for user: {username}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to change password: {e}")
            return False

    async def check_permission(self, username: str, permission: str) -> bool:
        """Check if user has specific permission."""
        try:
            if username not in self.users:
                return False

            user = self.users[username]
            return permission in user.permissions

        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return False

    async def generate_ssl_certificate(
        self,
        domain: str,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
    ) -> bool:
        """Generate SSL certificate."""
        try:
            if not self.security_config.ssl_enabled:
                return True

            self.logger.info(f"Generating SSL certificate for {domain}")

            cert_path = cert_path or f"{domain}.crt"
            key_path = key_path or f"{domain}.key"

            # Generate self-signed certificate (for demo)
            # In production, you'd use Let's Encrypt or a proper CA
            cmd = [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:4096",
                "-keyout",
                key_path,
                "-out",
                cert_path,
                "-days",
                "365",
                "-nodes",
                "-subj",
                f"/C=US/ST=State/L=City/O=Organization/CN={domain}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"SSL certificate generated: {cert_path}")
                return True
            else:
                self.logger.error(
                    f"Failed to generate SSL certificate: {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Failed to generate SSL certificate: {e}")
            return False

    async def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        try:
            if not self.security_config.encryption_enabled or not self.cipher_suite:
                return data

            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()

        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {e}")
            return data

    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        try:
            if not self.security_config.encryption_enabled or not self.cipher_suite:
                return encrypted_data

            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()

        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            return encrypted_data

    async def get_security_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events."""
        return self.security_events[-limit:] if self.security_events else []

    async def add_allowed_ip(self, ip_address: str) -> bool:
        """Add IP address to allowed list."""
        try:
            if ip_address not in self.security_config.allowed_ips:
                self.security_config.allowed_ips.append(ip_address)
                await self._record_security_event(
                    "ip_allowed", None, ip_address, None, {}
                )
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add allowed IP: {e}")
            return False

    async def add_blocked_ip(self, ip_address: str) -> bool:
        """Add IP address to blocked list."""
        try:
            if ip_address not in self.security_config.blocked_ips:
                self.security_config.blocked_ips.append(ip_address)
                await self._record_security_event(
                    "ip_blocked", None, ip_address, None, {}
                )
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add blocked IP: {e}")
            return False

    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate security report."""
        try:
            recent_events = self.security_events[-100:] if self.security_events else []

            # Count event types
            event_counts = {}
            for event in recent_events:
                event_counts[event.event_type] = (
                    event_counts.get(event.event_type, 0) + 1
                )

            # Get failed login attempts
            failed_logins = [e for e in recent_events if e.event_type == "login_failed"]

            # Get locked accounts
            locked_accounts = [
                username for username, user in self.users.items() if user.locked_until
            ]

            return {
                "timestamp": self._get_timestamp(),
                "total_users": len(self.users),
                "locked_accounts": len(locked_accounts),
                "recent_events": len(recent_events),
                "event_counts": event_counts,
                "failed_logins_last_24h": len(failed_logins),
                "allowed_ips": len(self.security_config.allowed_ips),
                "blocked_ips": len(self.security_config.blocked_ips),
                "ssl_enabled": self.security_config.ssl_enabled,
                "encryption_enabled": self.security_config.encryption_enabled,
            }

        except Exception as e:
            self.logger.error(f"Failed to generate security report: {e}")
            return {}

    def _initialize_encryption(self) -> None:
        """Initialize encryption components."""
        try:
            if self.security_config.encryption_enabled:
                # Generate or load encryption key
                key_file = Path.home() / ".milkbottle" / "security" / "encryption.key"
                key_file.parent.mkdir(parents=True, exist_ok=True)

                if key_file.exists():
                    with open(key_file, "rb") as f:
                        self.encryption_key = f.read()
                else:
                    self.encryption_key = cryptography.fernet.Fernet.generate_key()
                    with open(key_file, "wb") as f:
                        f.write(self.encryption_key)

                self.cipher_suite = cryptography.fernet.Fernet(self.encryption_key)

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")

    def _load_users(self) -> None:
        """Load users from storage."""
        try:
            # In production, this would load from a database
            # For demo, create some default users
            default_users = [
                User("admin", "admin@example.com", "admin", ["*"]),
                User("user", "user@example.com", "user", ["read", "write"]),
                User("guest", "guest@example.com", "guest", ["read"]),
            ]

            for user in default_users:
                self.users[user.username] = user

        except Exception as e:
            self.logger.error(f"Failed to load users: {e}")

    async def _verify_password(self, username: str, password: str) -> bool:
        """Verify user password."""
        try:
            # In production, this would verify against stored hash
            # For demo, use simple password check
            return bool(
                username == "admin"
                and password == "admin123"
                or username == "user"
                and password == "user123"
                or username == "guest"
                and password == "guest123"
            )
        except Exception as e:
            self.logger.error(f"Failed to verify password: {e}")
            return False

    async def _hash_password(self, password: str) -> str:
        """Hash password."""
        try:
            # In production, use proper password hashing (bcrypt, Argon2, etc.)
            return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash password: {e}")
            return ""

    async def _store_password(self, username: str, hashed_password: str) -> None:
        """Store hashed password."""
        try:
            # In production, store in database
            # For demo, just log it
            self.logger.info(f"Stored password hash for {username}")
        except Exception as e:
            self.logger.error(f"Failed to store password: {e}")

    async def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for role."""
        if role == "admin":
            return ["*"]  # All permissions
        elif role == "user":
            return ["read", "write", "execute"]
        elif role == "guest":
            return ["read"]
        else:
            return []

    async def _check_ip_access(self, ip_address: Optional[str]) -> bool:
        """Check if IP address is allowed."""
        if not ip_address:
            return True

        # Check blocked IPs first
        if ip_address in self.security_config.blocked_ips:
            return False

        # If allowed IPs are specified, check if IP is in the list
        if self.security_config.allowed_ips:
            return ip_address in self.security_config.allowed_ips

        return True

    async def _record_security_event(
        self,
        event_type: str,
        username: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Dict[str, Any],
    ) -> None:
        """Record a security event."""
        try:
            event = SecurityEvent(
                event_id=self._generate_event_id(),
                timestamp=self._get_timestamp(),
                event_type=event_type,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )

            self.security_events.append(event)

            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]

            # Log event
            self.logger.info(
                f"Security event: {event_type} - {username} - {ip_address}"
            )

        except Exception as e:
            self.logger.error(f"Failed to record security event: {e}")

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.randbelow(10000)
        return f"sec_event_{timestamp}_{random_suffix}"

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
