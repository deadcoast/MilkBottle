"""REST API server for MilkBottle.

This module provides a FastAPI-based REST API server for programmatic access
to MilkBottle functionalities.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .advanced_analytics import get_advanced_analytics
from .enterprise_features import AuditEventType, UserRole, get_enterprise_features
from .export_menu import get_export_menu
from .plugin_system import get_plugin_manager, list_plugins, load_plugin, unload_plugin
from .preview_system import get_preview_system
from .registry import get_registry
from .wizards import run_wizard

logger = logging.getLogger("milkbottle.api")

# Enterprise features integration
enterprise = get_enterprise_features()


# API Models
class BottleInfo(BaseModel):
    """Bottle information model."""

    name: str
    version: str
    description: str
    author: str
    capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    status: str
    health: Dict[str, Any] = Field(default_factory=dict)


class PluginInfo(BaseModel):
    """Plugin information model."""

    name: str
    version: str
    description: str
    author: str
    status: str
    health: Dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    """Health status model."""

    status: str
    timestamp: str
    uptime: float
    bottles_count: int
    plugins_count: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ConfigUpdate(BaseModel):
    """Configuration update model."""

    config: Dict[str, Any]
    validate_only: bool = False


class ProcessingRequest(BaseModel):
    """Processing request model."""

    bottle_name: str
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None


class ProcessingResponse(BaseModel):
    """Processing response model."""

    request_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float


class APIStats(BaseModel):
    """API statistics model."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    active_connections: int
    uptime: float


# Phase 4.1 API Models
class PreviewRequest(BaseModel):
    """Preview request model."""

    file_path: str
    config: Optional[Dict[str, Any]] = None
    include_quality_assessment: bool = True
    include_structured_content: bool = True


class PreviewResponse(BaseModel):
    """Preview response model."""

    request_id: str
    status: str
    preview_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float


class ExportRequest(BaseModel):
    """Export request model."""

    file_path: str
    selected_formats: List[str]
    config: Optional[Dict[str, Any]] = None
    output_directory: Optional[str] = None


class ExportResponse(BaseModel):
    """Export response model."""

    request_id: str
    status: str
    exported_files: List[str] = []
    error: Optional[str] = None
    processing_time: float


class AnalyticsRequest(BaseModel):
    """Analytics request model."""

    file_path: str
    include_quality_metrics: bool = True
    include_classification: bool = True
    include_predictive_insights: bool = True


class AnalyticsResponse(BaseModel):
    """Analytics response model."""

    request_id: str
    status: str
    analytics_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float


class WizardRequest(BaseModel):
    """Wizard request model."""

    wizard_type: str  # "pdfmilker", "venvmilker", "fontmilker"
    config: Optional[Dict[str, Any]] = None


class WizardResponse(BaseModel):
    """Wizard response model."""

    request_id: str
    status: str
    configuration: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float


# Enterprise-specific models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    session_id: str
    user: Dict[str, Any]
    expires_at: str


class LogoutResponse(BaseModel):
    """Logout response model."""

    message: str


class UserCreateRequest(BaseModel):
    """User creation request model."""

    username: str
    email: str
    password: str
    role: str
    permissions: Optional[List[str]] = None


class UserUpdateRequest(BaseModel):
    """User update request model."""

    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None


class AuditReportRequest(BaseModel):
    """Audit report request model."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    user_id: Optional[str] = None


class AuditReportResponse(BaseModel):
    """Audit report response model."""

    period: Dict[str, Any]
    summary: Dict[str, Any]
    event_types: Dict[str, int]
    users: Dict[str, int]
    recent_events: List[Dict[str, Any]]


class MilkBottleAPI:
    """MilkBottle API server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize the API server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.start_time = time.time()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "active_connections": 0,
        }

        # Initialize FastAPI app
        self.app = FastAPI(
            title="MilkBottle API",
            description="REST API for MilkBottle CLI Toolbox",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add request tracking middleware
        self.app.middleware("http")(self._track_request)

        # Setup routes
        self._setup_routes()

        # Initialize registry and plugin manager
        self.registry = get_registry()
        self.plugin_manager = get_plugin_manager()

    def _track_request(self, request: Request, call_next):
        """Track request statistics."""
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["active_connections"] += 1

        try:
            response = call_next(request)
            self.stats["successful_requests"] += 1
            return response
        except Exception:
            self.stats["failed_requests"] += 1
            raise
        finally:
            response_time = time.time() - start_time
            self.stats["response_times"].append(response_time)
            self.stats["active_connections"] -= 1

            # Keep only last 1000 response times
            if len(self.stats["response_times"]) > 1000:
                self.stats["response_times"] = self.stats["response_times"][-1000:]

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint."""
            return {
                "message": "MilkBottle API Server",
                "version": "1.0.0",
                "docs": "/docs",
            }

        @self.app.get("/health", response_model=HealthStatus)
        async def health_check():
            """Get system health status."""
            try:
                bottles = self.registry.discover_bottles()
                plugins = list_plugins()

                # Check for errors and warnings
                errors = []
                warnings = []

                # Check bottle health
                for bottle_name, bottle_info in bottles.items():
                    if not bottle_info.get("is_valid", False):
                        errors.append(f"Invalid bottle: {bottle_name}")

                # Check plugin health
                for plugin in plugins:
                    health_status = plugin.get("health", {}).get("status", "unknown")
                    if health_status == "error":
                        errors.append(f"Plugin error: {plugin['name']}")
                    elif health_status == "warning":
                        warnings.append(f"Plugin warning: {plugin['name']}")

                return HealthStatus(
                    status="unhealthy" if errors else "healthy",
                    timestamp=datetime.now().isoformat(),
                    uptime=time.time() - self.start_time,
                    bottles_count=len(bottles),
                    plugins_count=len(plugins),
                    errors=errors,
                    warnings=warnings,
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return HealthStatus(
                    status="error",
                    timestamp=datetime.now().isoformat(),
                    uptime=time.time() - self.start_time,
                    bottles_count=0,
                    plugins_count=0,
                    errors=[str(e)],
                )

        @self.app.get("/bottles", response_model=List[BottleInfo])
        async def list_bottles():
            """List all available bottles."""
            try:
                bottles = self.registry.discover_bottles()
                bottle_list = []

                for name, info in bottles.items():
                    bottle_list.append(
                        BottleInfo(
                            name=name,
                            version=info.get("version", "0.0.0"),
                            description=info.get("description", ""),
                            author=info.get("author", "Unknown"),
                            capabilities=info.get("capabilities", []),
                            dependencies=info.get("dependencies", []),
                            status=(
                                "active" if info.get("is_valid", False) else "inactive"
                            ),
                            health=info.get("health", {}),
                        )
                    )

                return bottle_list
            except Exception as e:
                logger.error(f"Failed to list bottles: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/bottles/{bottle_name}", response_model=BottleInfo)
        async def get_bottle(bottle_name: str):
            """Get specific bottle information."""
            try:
                bottles = self.registry.discover_bottles()
                if bottle_name not in bottles:
                    raise HTTPException(
                        status_code=404, detail=f"Bottle not found: {bottle_name}"
                    )

                info = bottles[bottle_name]
                return BottleInfo(
                    name=bottle_name,
                    version=info.get("version", "0.0.0"),
                    description=info.get("description", ""),
                    author=info.get("author", "Unknown"),
                    capabilities=info.get("capabilities", []),
                    dependencies=info.get("dependencies", []),
                    status="active" if info.get("is_valid", False) else "inactive",
                    health=info.get("health", {}),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get bottle {bottle_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(
            "/bottles/{bottle_name}/process", response_model=ProcessingResponse
        )
        async def process_with_bottle(
            bottle_name: str,
            request: ProcessingRequest,
        ):
            """Process data with a specific bottle."""
            try:
                # Get bottle
                bottles = self.registry.discover_bottles()
                if bottle_name not in bottles:
                    raise HTTPException(
                        status_code=404, detail=f"Bottle not found: {bottle_name}"
                    )

                bottle_info = bottles[bottle_name]
                if not bottle_info.get("is_valid", False):
                    raise HTTPException(
                        status_code=400, detail=f"Bottle {bottle_name} is not valid"
                    )

                # Log bottle execution
                enterprise.log_bottle_execution(bottle_name, request.input_data)

                # Process with bottle
                start_time = time.time()
                result = {
                    "message": f"Processed with {bottle_name}",
                    "data": request.input_data,
                }
                processing_time = time.time() - start_time

                return ProcessingResponse(
                    request_id=str(uuid4()),
                    status="completed",
                    result=result,
                    processing_time=processing_time,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to process with bottle {bottle_name}: {e}")
                enterprise.log_bottle_execution(
                    bottle_name, request.input_data, success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

        # Enterprise authentication endpoints
        @self.app.post("/auth/login", response_model=LoginResponse)
        async def login(request: LoginRequest):
            """Authenticate user and create session."""
            try:
                success = enterprise.login(request.username, request.password)
                if not success:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                session = enterprise.current_session
                user = enterprise.current_user

                # Add null checks for session and user
                if session is None or user is None:
                    raise HTTPException(
                        status_code=500, detail="Login failed - no session created"
                    )

                return LoginResponse(
                    session_id=session.session_id,
                    user={
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "permissions": list(user.permissions),
                    },
                    expires_at=session.expires_at.isoformat(),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Login failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/auth/logout", response_model=LogoutResponse)
        async def logout():
            """Logout current user."""
            try:
                enterprise.logout()
                return LogoutResponse(message="Logged out successfully")
            except Exception as e:
                logger.error(f"Logout failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Enterprise user management endpoints
        @self.app.post("/enterprise/users", response_model=Dict[str, Any])
        async def create_user(request: UserCreateRequest):
            """Create a new user."""
            try:
                # Check if current user has permission
                if not enterprise.check_permission("user_manage"):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                role = UserRole(request.role)
                user = enterprise.user_manager.create_user(
                    username=request.username,
                    email=request.email,
                    password=request.password,
                    role=role,
                    permissions=request.permissions,
                )

                # Log user creation
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "system"
                    ),
                    event_type=AuditEventType.USER_CREATE,
                    resource="user_management",
                    action="create_user",
                    details={"username": request.username, "role": request.role},
                    success=True,
                )

                return {
                    "message": "User created successfully",
                    "user": {
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                    },
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Failed to create user: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/enterprise/users", response_model=List[Dict[str, Any]])
        async def list_users():
            """List all users."""
            try:
                # Check if current user has permission
                if not enterprise.check_permission("user_manage"):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                users = enterprise.user_manager.list_users()
                return [
                    {
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat(),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
                    }
                    for user in users
                ]
            except Exception as e:
                logger.error(f"Failed to list users: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/enterprise/users/{username}", response_model=Dict[str, Any])
        async def update_user(username: str, request: UserUpdateRequest):
            """Update a user."""
            try:
                # Check if current user has permission
                if not enterprise.check_permission("user_manage"):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                role = UserRole(request.role) if request.role else None
                user = enterprise.user_manager.update_user(
                    username=username,
                    email=request.email,
                    role=role,
                    is_active=request.is_active,
                    permissions=request.permissions,
                )

                if not user:
                    raise HTTPException(
                        status_code=404, detail=f"User {username} not found"
                    )

                # Log user update
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "system"
                    ),
                    event_type=AuditEventType.USER_UPDATE,
                    resource="user_management",
                    action="update_user",
                    details={
                        "username": username,
                        "updates": request.dict(exclude_none=True),
                    },
                    success=True,
                )

                return {
                    "message": "User updated successfully",
                    "user": {
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "is_active": user.is_active,
                    },
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to update user: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/enterprise/users/{username}", response_model=Dict[str, str])
        async def delete_user(username: str):
            """Delete a user."""
            try:
                # Check if current user has permission
                if not enterprise.check_permission("user_manage"):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                if username == "admin":
                    raise HTTPException(
                        status_code=400, detail="Cannot delete admin user"
                    )

                success = enterprise.user_manager.delete_user(username)
                if not success:
                    raise HTTPException(
                        status_code=404, detail=f"User {username} not found"
                    )

                # Log user deletion
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "system"
                    ),
                    event_type=AuditEventType.USER_DELETE,
                    resource="user_management",
                    action="delete_user",
                    details={"username": username},
                    success=True,
                )

                return {"message": f"User {username} deleted successfully"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to delete user: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Enterprise audit endpoints
        @self.app.post("/enterprise/audit/report", response_model=AuditReportResponse)
        async def get_audit_report(request: AuditReportRequest):
            """Get audit report."""
            try:
                # Check if current user has permission
                if not enterprise.check_permission("audit_view"):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                start_date = None
                end_date = None

                if request.start_date:
                    start_date = datetime.fromisoformat(request.start_date)
                if request.end_date:
                    end_date = datetime.fromisoformat(request.end_date)

                report = enterprise.get_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=request.user_id,
                )

                return AuditReportResponse(**report)
            except Exception as e:
                logger.error(f"Failed to get audit report: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Continue with existing endpoints...
        @self.app.get("/plugins", response_model=List[PluginInfo])
        async def list_plugins_endpoint():
            """List all available plugins."""
            try:
                plugins = list_plugins()
                return [
                    PluginInfo(
                        name=plugin["name"],
                        version=plugin.get("version", "0.0.0"),
                        description=plugin.get("description", ""),
                        author=plugin.get("author", "Unknown"),
                        status=(
                            "active" if plugin.get("is_valid", False) else "inactive"
                        ),
                        health=plugin.get("health", {}),
                    )
                    for plugin in plugins
                ]
            except Exception as e:
                logger.error(f"Failed to list plugins: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/plugins/{plugin_name}/load")
        async def load_plugin_endpoint(plugin_name: str):
            """Load a plugin."""
            try:
                # Log plugin operation
                enterprise.log_file_access(f"plugin:{plugin_name}", "load")

                result = load_plugin(plugin_name)
                return {
                    "message": f"Plugin {plugin_name} loaded successfully",
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                enterprise.log_file_access(
                    f"plugin:{plugin_name}", "load", success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/plugins/{plugin_name}/unload")
        async def unload_plugin_endpoint(plugin_name: str):
            """Unload a plugin."""
            try:
                # Log plugin operation
                enterprise.log_file_access(f"plugin:{plugin_name}", "unload")

                result = unload_plugin(plugin_name)
                return {
                    "message": f"Plugin {plugin_name} unloaded successfully",
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                enterprise.log_file_access(
                    f"plugin:{plugin_name}",
                    "unload",
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/config/{bottle_name}")
        async def get_bottle_config(bottle_name: str):
            """Get bottle configuration."""
            try:
                # Log configuration access
                enterprise.log_file_access(f"config:{bottle_name}", "read")

                config = get_bottle_config(bottle_name)
                return {"bottle": bottle_name, "config": config}
            except Exception as e:
                logger.error(f"Failed to get config for {bottle_name}: {e}")
                enterprise.log_file_access(
                    f"config:{bottle_name}", "read", success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/config/{bottle_name}")
        async def update_bottle_config_endpoint(
            bottle_name: str, config_update: ConfigUpdate
        ):
            """Update bottle configuration."""
            try:
                # Log configuration change
                enterprise.log_file_access(f"config:{bottle_name}", "update")

                # Extract config from ConfigUpdate object
                result = update_bottle_config_mock(bottle_name, config_update.config)
                return {
                    "message": "Configuration updated successfully",
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Failed to update config for {bottle_name}: {e}")
                enterprise.log_file_access(
                    f"config:{bottle_name}",
                    "update",
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/stats", response_model=APIStats)
        async def get_api_stats():
            """Get API statistics."""
            try:
                avg_response_time = (
                    sum(self.stats["response_times"])
                    / len(self.stats["response_times"])
                    if self.stats["response_times"]
                    else 0
                )

                return APIStats(
                    total_requests=self.stats["total_requests"],
                    successful_requests=self.stats["successful_requests"],
                    failed_requests=self.stats["failed_requests"],
                    average_response_time=avg_response_time,
                    active_connections=self.stats["active_connections"],
                    uptime=time.time() - self.start_time,
                )
            except Exception as e:
                logger.error(f"Failed to get API stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/logs")
        async def get_logs(limit: int = Query(100, ge=1, le=1000)):
            """Get recent logs."""
            try:
                # Log access to logs
                enterprise.log_file_access("system:logs", "read")

                logs = get_recent_logs(limit)
                return {"logs": logs}
            except Exception as e:
                logger.error(f"Failed to get logs: {e}")
                enterprise.log_file_access(
                    "system:logs", "read", success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

        # Phase 4.1 endpoints with enterprise integration
        @self.app.post("/preview", response_model=PreviewResponse)
        async def preview_file(request: PreviewRequest):
            """Preview file content."""
            try:
                # Log file access
                enterprise.log_file_access(request.file_path, "preview")

                start_time = time.time()
                preview_system = get_preview_system()

                # Use the correct method signature - only takes pdf_path and output_dir
                preview_result = preview_system.preview_pdf_extraction(
                    Path(request.file_path)
                )

                processing_time = time.time() - start_time

                return PreviewResponse(
                    request_id=str(uuid4()),
                    status="completed",
                    preview_result={
                        "content": preview_result.content,
                        "metadata": preview_result.metadata,
                        "structure": preview_result.structure,
                        "quality_metrics": preview_result.quality_metrics,
                        "file_size": preview_result.file_size,
                        "extraction_time": preview_result.extraction_time,
                        "confidence_score": preview_result.confidence_score,
                        "warnings": preview_result.warnings,
                        "errors": preview_result.errors,
                    },
                    processing_time=processing_time,
                )
            except FileNotFoundError:
                enterprise.log_file_access(
                    request.file_path,
                    "preview",
                    success=False,
                    error_message="File not found",
                )
                raise HTTPException(status_code=404, detail="File not found")
            except Exception as e:
                logger.error(f"Preview failed: {e}")
                enterprise.log_file_access(
                    request.file_path, "preview", success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/export/formats", response_model=List[Dict[str, Any]])
        async def get_export_formats():
            """Get available export formats."""
            try:
                export_menu = get_export_menu()
                formats = []

                for format_id, export_format in export_menu.available_formats.items():
                    formats.append(
                        {
                            "id": format_id,
                            "name": export_format.name,
                            "extension": export_format.extension,
                            "description": export_format.description,
                            "supported_features": export_format.supported_features,
                            "config_options": export_format.config_options,
                            "preview_supported": export_format.preview_supported,
                        }
                    )

                return formats
            except Exception as e:
                logger.error(f"Failed to get export formats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/export", response_model=ExportResponse)
        async def export_file(request: ExportRequest):
            """Export file to multiple formats."""
            try:
                # Log export operation
                enterprise.log_export_operation(
                    request.file_path, request.selected_formats
                )

                start_time = time.time()
                export_menu = get_export_menu()

                # Generate sample content for demonstration
                sample_content = {
                    "title": "Sample Document",
                    "content": "This is a sample document for export demonstration.",
                    "metadata": {"author": "MilkBottle", "created": "2024-01-01"},
                }

                output_dir = (
                    Path(request.output_directory)
                    if request.output_directory
                    else Path("exports")
                )
                output_dir.mkdir(exist_ok=True)

                exported_files = export_menu.execute_export(sample_content, output_dir)

                processing_time = time.time() - start_time

                return ExportResponse(
                    request_id=str(uuid4()),
                    status="completed",
                    exported_files=list(exported_files.values()),
                    processing_time=processing_time,
                )
            except FileNotFoundError:
                enterprise.log_export_operation(
                    request.file_path,
                    request.selected_formats,
                    success=False,
                    error_message="File not found",
                )
                raise HTTPException(status_code=404, detail="File not found")
            except Exception as e:
                logger.error(f"Export failed: {e}")
                enterprise.log_export_operation(
                    request.file_path,
                    request.selected_formats,
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/analytics", response_model=AnalyticsResponse)
        async def analyze_file(request: AnalyticsRequest):
            """Analyze file with advanced analytics."""
            try:
                # Log analytics access
                enterprise.log_analytics_access(request.file_path, "full_analysis")

                start_time = time.time()
                analytics = get_advanced_analytics()

                # Create content data from file path
                content_data = {"file_path": request.file_path}
                result = analytics.analyze_content(content_data)

                processing_time = time.time() - start_time

                return AnalyticsResponse(
                    request_id=str(uuid4()),
                    status="completed",
                    analytics_result={
                        "quality_metrics": {
                            "overall_score": result.quality_metrics.overall_score,
                            "text_quality": getattr(
                                result.quality_metrics, "text_quality", 0.0
                            ),
                            "structure_quality": getattr(
                                result.quality_metrics, "structure_quality", 0.0
                            ),
                            "metadata_completeness": getattr(
                                result.quality_metrics, "metadata_completeness", 0.0
                            ),
                        },
                        "classification": {
                            "document_type": result.classification.document_type,
                            "complexity_level": result.classification.complexity_level,
                            "content_categories": getattr(
                                result.classification, "content_categories", []
                            ),
                            "confidence": result.classification.confidence,
                        },
                        "insights": {
                            "processing_time_prediction": result.insights.processing_time_prediction,
                            "quality_improvement_suggestions": getattr(
                                result.insights, "quality_improvement_suggestions", []
                            ),
                            "content_recommendations": getattr(
                                result.insights, "content_recommendations", []
                            ),
                            "risk_assessment": getattr(
                                result.insights, "risk_assessment", {}
                            ),
                        },
                    },
                    processing_time=processing_time,
                )
            except FileNotFoundError:
                enterprise.log_analytics_access(
                    request.file_path,
                    "full_analysis",
                    success=False,
                    error_message="File not found",
                )
                raise HTTPException(status_code=404, detail="File not found")
            except Exception as e:
                logger.error(f"Analytics failed: {e}")
                enterprise.log_analytics_access(
                    request.file_path,
                    "full_analysis",
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/wizards", response_model=List[str])
        async def get_available_wizards():
            """Get available configuration wizards."""
            try:
                return ["pdfmilker", "venvmilker", "fontmilker"]
            except Exception as e:
                logger.error(f"Failed to get wizards: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/wizards/{wizard_type}", response_model=WizardResponse)
        async def run_configuration_wizard(wizard_type: str, request: WizardRequest):
            """Run a configuration wizard."""
            try:
                # Log wizard execution
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "anonymous"
                    ),
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource=f"wizard:{wizard_type}",
                    action="run_wizard",
                    details={"wizard_type": wizard_type, "config": request.config},
                    success=True,
                )

                start_time = time.time()
                # run_wizard only takes wizard_type as argument
                config = run_wizard(wizard_type)
                processing_time = time.time() - start_time

                return WizardResponse(
                    request_id=str(uuid4()),
                    status="completed",
                    configuration=config,
                    processing_time=processing_time,
                )
            except ValueError as e:
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "anonymous"
                    ),
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource=f"wizard:{wizard_type}",
                    action="run_wizard",
                    details={"wizard_type": wizard_type, "config": request.config},
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Wizard failed: {e}")
                enterprise.audit_logger.log_event(
                    user_id=(
                        enterprise.current_user.username
                        if enterprise.current_user
                        else "anonymous"
                    ),
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource=f"wizard:{wizard_type}",
                    action="run_wizard",
                    details={"wizard_type": wizard_type, "config": request.config},
                    success=False,
                    error_message=str(e),
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Upload a file."""
            try:
                # Add null check for filename
                if file.filename is None:
                    raise HTTPException(status_code=400, detail="No filename provided")

                # Log file upload
                enterprise.log_file_access(file.filename, "upload")

                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)

                file_path = upload_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                return {
                    "message": "File uploaded successfully",
                    "filename": file.filename,
                    "size": len(content),
                    "path": str(file_path),
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                if file.filename:
                    enterprise.log_file_access(
                        file.filename, "upload", success=False, error_message=str(e)
                    )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/download/{file_path:path}")
        async def download_file(file_path: str):
            """Download a file."""
            try:
                # Log file download
                enterprise.log_file_access(file_path, "download")

                path = Path(file_path)
                if not path.exists():
                    enterprise.log_file_access(
                        file_path,
                        "download",
                        success=False,
                        error_message="File not found",
                    )
                    raise HTTPException(status_code=404, detail="File not found")

                return FileResponse(path)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Download failed: {e}")
                enterprise.log_file_access(
                    file_path, "download", success=False, error_message=str(e)
                )
                raise HTTPException(status_code=500, detail=str(e))

    def start(self, reload: bool = False):
        """Start the API server."""
        import uvicorn

        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            reload=reload,
            log_level="info",
        )

    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app


# Global API server instance
_api_server: Optional[MilkBottleAPI] = None


def get_api_server(host: str = "0.0.0.0", port: int = 8000) -> MilkBottleAPI:
    """Get the global API server instance.

    Args:
        host: Host to bind to
        port: Port to bind to

    Returns:
        API server instance
    """
    global _api_server
    if _api_server is None:
        _api_server = MilkBottleAPI(host, port)
    return _api_server


def start_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
    """
    server = get_api_server(host, port)
    server.start(reload=reload)


# Mock functions for missing dependencies
def get_bottle_config(bottle_name: str):
    """Get bottle config (mock implementation)."""
    return {"default_config": True}


def update_bottle_config_mock(bottle_name: str, config: Dict[str, Any]):
    """Update bottle config (mock implementation)."""
    return {"status": "updated", "bottle": bottle_name}


def get_recent_logs(limit: int):
    """Get recent logs (mock implementation)."""
    return [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "Sample log entry",
        }
    ]
