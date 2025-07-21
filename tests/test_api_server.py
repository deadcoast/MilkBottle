"""Tests for REST API server functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from milkbottle.api_server import (
    AnalyticsRequest,
    AnalyticsResponse,
    APIStats,
    BottleInfo,
    ExportRequest,
    ExportResponse,
    HealthStatus,
    MilkBottleAPI,
    PluginInfo,
    PreviewRequest,
    PreviewResponse,
    ProcessingRequest,
    ProcessingResponse,
    WizardRequest,
    WizardResponse,
    get_api_server,
    start_api_server,
)


class TestAPIModels:
    """Test API data models."""

    def test_bottle_info_model(self):
        """Test BottleInfo model."""
        bottle_info = BottleInfo(
            name="test_bottle",
            version="1.0.0",
            description="Test bottle",
            author="Test Author",
            capabilities=["extract", "process"],
            dependencies=["numpy"],
            status="active",
            health={"status": "healthy"},
        )

        assert bottle_info.name == "test_bottle"
        assert bottle_info.version == "1.0.0"
        assert bottle_info.description == "Test bottle"
        assert bottle_info.author == "Test Author"
        assert bottle_info.capabilities == ["extract", "process"]
        assert bottle_info.dependencies == ["numpy"]
        assert bottle_info.status == "active"
        assert bottle_info.health["status"] == "healthy"

    def test_plugin_info_model(self):
        """Test PluginInfo model."""
        plugin_info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            status="loaded",
            health={"status": "healthy"},
        )

        assert plugin_info.name == "test_plugin"
        assert plugin_info.version == "1.0.0"
        assert plugin_info.description == "Test plugin"
        assert plugin_info.author == "Test Author"
        assert plugin_info.status == "loaded"
        assert plugin_info.health["status"] == "healthy"

    def test_health_status_model(self):
        """Test HealthStatus model."""
        health_status = HealthStatus(
            status="healthy",
            timestamp="2023-01-01T00:00:00",
            uptime=3600.0,
            bottles_count=3,
            plugins_count=2,
            errors=[],
            warnings=["Plugin warning"],
        )

        assert health_status.status == "healthy"
        assert health_status.timestamp == "2023-01-01T00:00:00"
        assert health_status.uptime == 3600.0
        assert health_status.bottles_count == 3
        assert health_status.plugins_count == 2
        assert health_status.errors == []
        assert health_status.warnings == ["Plugin warning"]

    def test_processing_request_model(self):
        """Test ProcessingRequest model."""
        request = ProcessingRequest(
            bottle_name="pdfmilker",
            input_data={"file_path": "test.pdf"},
            config={"output_format": "markdown"},
            timeout=300,
        )

        assert request.bottle_name == "pdfmilker"
        assert request.input_data["file_path"] == "test.pdf"
        assert request.config["output_format"] == "markdown"
        assert request.timeout == 300

    def test_processing_response_model(self):
        """Test ProcessingResponse model."""
        response = ProcessingResponse(
            request_id="req_123",
            status="completed",
            result={"output": "processed content"},
            processing_time=2.5,
        )

        assert response.request_id == "req_123"
        assert response.status == "completed"
        assert response.result["output"] == "processed content"
        assert response.processing_time == 2.5

    def test_api_stats_model(self):
        """Test APIStats model."""
        stats = APIStats(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=0.5,
            active_connections=2,
            uptime=3600.0,
        )

        assert stats.total_requests == 100
        assert stats.successful_requests == 95
        assert stats.failed_requests == 5
        assert stats.average_response_time == 0.5
        assert stats.active_connections == 2
        assert stats.uptime == 3600.0

    def test_preview_request_model(self):
        """Test PreviewRequest model."""
        request = PreviewRequest(
            file_path="test.pdf",
            config={"include_images": True},
            include_quality_assessment=True,
            include_structured_content=True,
        )

        assert request.file_path == "test.pdf"
        assert request.config["include_images"] is True
        assert request.include_quality_assessment is True
        assert request.include_structured_content is True

    def test_preview_response_model(self):
        """Test PreviewResponse model."""
        response = PreviewResponse(
            request_id="preview_123",
            status="completed",
            preview_result={"quality_score": 0.8},
            processing_time=1.5,
        )

        assert response.request_id == "preview_123"
        assert response.status == "completed"
        assert response.preview_result["quality_score"] == 0.8
        assert response.processing_time == 1.5

    def test_export_request_model(self):
        """Test ExportRequest model."""
        request = ExportRequest(
            file_path="test.pdf",
            selected_formats=["pdf", "markdown"],
            config={"include_images": True},
            output_directory="exports",
        )

        assert request.file_path == "test.pdf"
        assert request.selected_formats == ["pdf", "markdown"]
        assert request.config["include_images"] is True
        assert request.output_directory == "exports"

    def test_export_response_model(self):
        """Test ExportResponse model."""
        response = ExportResponse(
            request_id="export_123",
            status="completed",
            exported_files=["test.pdf", "test.md"],
            processing_time=3.0,
        )

        assert response.request_id == "export_123"
        assert response.status == "completed"
        assert response.exported_files == ["test.pdf", "test.md"]
        assert response.processing_time == 3.0

    def test_analytics_request_model(self):
        """Test AnalyticsRequest model."""
        request = AnalyticsRequest(
            file_path="test.pdf",
            include_quality_metrics=True,
            include_classification=True,
            include_predictive_insights=True,
        )

        assert request.file_path == "test.pdf"
        assert request.include_quality_metrics is True
        assert request.include_classification is True
        assert request.include_predictive_insights is True

    def test_analytics_response_model(self):
        """Test AnalyticsResponse model."""
        response = AnalyticsResponse(
            request_id="analytics_123",
            status="completed",
            analytics_result={"quality_score": 0.8},
            processing_time=2.0,
        )

        assert response.request_id == "analytics_123"
        assert response.status == "completed"
        assert response.analytics_result["quality_score"] == 0.8
        assert response.processing_time == 2.0

    def test_wizard_request_model(self):
        """Test WizardRequest model."""
        request = WizardRequest(
            wizard_type="pdfmilker", config={"output_dir": "extracted"}
        )

        assert request.wizard_type == "pdfmilker"
        assert request.config["output_dir"] == "extracted"

    def test_wizard_response_model(self):
        """Test WizardResponse model."""
        response = WizardResponse(
            request_id="wizard_123",
            status="completed",
            configuration={"output_dir": "extracted"},
            processing_time=1.0,
        )

        assert response.request_id == "wizard_123"
        assert response.status == "completed"
        assert response.configuration["output_dir"] == "extracted"
        assert response.processing_time == 1.0


class TestMilkBottleAPI:
    """Test MilkBottleAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = MilkBottleAPI(host="127.0.0.1", port=8000)
        self.client = TestClient(self.api.app)

    def test_init(self):
        """Test API initialization."""
        assert self.api.host == "127.0.0.1"
        assert self.api.port == 8000
        assert self.api.start_time > 0
        assert "total_requests" in self.api.stats
        assert "successful_requests" in self.api.stats
        assert "failed_requests" in self.api.stats
        assert "response_times" in self.api.stats
        assert "active_connections" in self.api.stats

    def test_track_request(self):
        """Test request tracking."""
        # Mock request and response
        mock_request = Mock()
        mock_call_next = Mock(return_value=Mock())

        # Test successful request
        response = self.api._track_request(mock_request, mock_call_next)

        # Verify response was returned successfully
        assert response is not None

        assert self.api.stats["total_requests"] == 1
        assert self.api.stats["successful_requests"] == 1
        assert self.api.stats["failed_requests"] == 0
        assert len(self.api.stats["response_times"]) == 1
        assert self.api.stats["active_connections"] == 0

    def test_track_request_failure(self):
        """Test request tracking with failure."""
        # Mock request and response that raises exception
        mock_request = Mock()
        mock_call_next = Mock(side_effect=Exception("Test error"))

        # Test failed request
        with pytest.raises(Exception):
            self.api._track_request(mock_request, mock_call_next)

        assert self.api.stats["total_requests"] == 1
        assert self.api.stats["successful_requests"] == 0
        assert self.api.stats["failed_requests"] == 1
        assert len(self.api.stats["response_times"]) == 1
        assert self.api.stats["active_connections"] == 0

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "MilkBottle API Server"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"

    @patch("milkbottle.api_server.list_plugins")
    def test_health_check_endpoint(self, mock_list_plugins):
        """Test health check endpoint."""
        # Mock plugins
        mock_list_plugins.return_value = [
            {"name": "test_plugin", "health": {"status": "healthy"}}
        ]

        # Mock the registry instance directly
        mock_registry = Mock()
        mock_registry.discover_bottles.return_value = {
            "pdfmilker": {"is_valid": True, "health": {"status": "healthy"}},
            "venvmilker": {"is_valid": False, "health": {"status": "error"}},
        }
        self.api.registry = mock_registry

        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        # The health check should return unhealthy if any bottle is invalid
        assert data["status"] == "unhealthy"  # Because venvmilker is invalid
        assert data["bottles_count"] == 2
        assert data["plugins_count"] == 1
        assert data["uptime"] > 0

    def test_list_bottles_endpoint(self):
        """Test list bottles endpoint."""
        # Mock registry instance directly
        mock_registry = Mock()
        mock_registry.discover_bottles.return_value = {
            "pdfmilker": {
                "version": "1.0.0",
                "description": "PDF processor",
                "author": "Test Author",
                "capabilities": ["extract"],
                "dependencies": ["numpy"],
                "is_valid": True,
                "health": {"status": "healthy"},
            }
        }
        self.api.registry = mock_registry

        response = self.client.get("/bottles")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "pdfmilker"
        assert data[0]["version"] == "1.0.0"
        assert data[0]["description"] == "PDF processor"
        assert data[0]["author"] == "Test Author"
        assert data[0]["capabilities"] == ["extract"]
        assert data[0]["dependencies"] == ["numpy"]
        assert data[0]["status"] == "active"
        assert data[0]["health"]["status"] == "healthy"

    def test_get_bottle_endpoint(self):
        """Test get specific bottle endpoint."""
        # Mock registry instance directly
        mock_registry = Mock()
        mock_registry.discover_bottles.return_value = {
            "pdfmilker": {
                "version": "1.0.0",
                "description": "PDF processor",
                "author": "Test Author",
                "capabilities": ["extract"],
                "dependencies": ["numpy"],
                "is_valid": True,
                "health": {"status": "healthy"},
            }
        }
        self.api.registry = mock_registry

        response = self.client.get("/bottles/pdfmilker")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "pdfmilker"
        assert data["version"] == "1.0.0"
        assert data["description"] == "PDF processor"
        assert data["author"] == "Test Author"
        assert data["capabilities"] == ["extract"]
        assert data["dependencies"] == ["numpy"]
        assert data["status"] == "active"
        assert data["health"]["status"] == "healthy"

    @patch("milkbottle.api_server.get_registry")
    def test_get_bottle_not_found(self, mock_get_registry):
        """Test get bottle endpoint with non-existent bottle."""
        # Mock registry
        mock_registry = Mock()
        mock_registry.discover_bottles.return_value = {}
        mock_get_registry.return_value = mock_registry

        response = self.client.get("/bottles/nonexistent")
        assert response.status_code == 404
        assert "Bottle not found" in response.json()["detail"]

    @patch("milkbottle.api_server.get_registry")
    def test_process_with_bottle_endpoint(self, mock_get_registry):
        """Test process with bottle endpoint."""
        # Mock registry
        mock_registry = Mock()
        mock_registry.discover_bottles.return_value = {
            "pdfmilker": {"is_valid": True, "health": {"status": "healthy"}}
        }
        mock_get_registry.return_value = mock_registry

        request_data = {
            "bottle_name": "pdfmilker",
            "input_data": {"file_path": "test.pdf"},
            "config": {"output_format": "markdown"},
            "timeout": 300,
        }

        response = self.client.post("/bottles/pdfmilker/process", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert "request_id" in data
        assert data["processing_time"] > 0

    @patch("milkbottle.api_server.list_plugins")
    def test_list_plugins_endpoint(self, mock_list_plugins):
        """Test list plugins endpoint."""
        # Mock plugins
        mock_list_plugins.return_value = [
            {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "author": "Test Author",
                "status": "loaded",
                "health": {"status": "healthy"},
            }
        ]

        response = self.client.get("/plugins")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_plugin"
        assert data[0]["version"] == "1.0.0"
        assert data[0]["status"] == "loaded"

    @patch("milkbottle.api_server.load_plugin")
    def test_load_plugin_endpoint(self, mock_load_plugin):
        """Test load plugin endpoint."""
        # Mock plugin loading
        mock_load_plugin.return_value = True

        response = self.client.post("/plugins/test_plugin/load")
        assert response.status_code == 200

        data = response.json()
        assert "loaded successfully" in data["message"]

    @patch("milkbottle.api_server.load_plugin")
    def test_load_plugin_failure(self, mock_load_plugin):
        """Test load plugin endpoint with failure."""
        # Mock plugin loading failure
        mock_load_plugin.return_value = False

        response = self.client.post("/plugins/test_plugin/load")
        assert response.status_code == 400
        assert "Failed to load plugin" in response.json()["detail"]

    @patch("milkbottle.api_server.unload_plugin")
    def test_unload_plugin_endpoint(self, mock_unload_plugin):
        """Test unload plugin endpoint."""
        # Mock plugin unloading
        mock_unload_plugin.return_value = True

        response = self.client.post("/plugins/test_plugin/unload")
        assert response.status_code == 200

        data = response.json()
        assert "unloaded successfully" in data["message"]

    def test_get_api_stats_endpoint(self):
        """Test get API stats endpoint."""
        # Make a request to generate some stats
        self.client.get("/")

        response = self.client.get("/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_requests"] > 0
        assert data["successful_requests"] > 0
        assert data["failed_requests"] >= 0
        assert data["average_response_time"] >= 0
        assert data["uptime"] > 0

    def test_get_logs_endpoint(self):
        """Test get logs endpoint."""
        response = self.client.get("/logs")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Log retrieval not implemented"
        assert data["limit"] == 100

    def test_get_logs_with_limit(self):
        """Test get logs endpoint with custom limit."""
        response = self.client.get("/logs?limit=50")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 50


class TestPhase41Endpoints:
    """Test Phase 4.1 API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = MilkBottleAPI(host="127.0.0.1", port=8000)
        self.client = TestClient(self.api.app)

    @patch("milkbottle.api_server.get_preview_system")
    def test_preview_endpoint(self, mock_get_preview_system):
        """Test preview endpoint."""
        # Mock preview system
        mock_preview_system = Mock()
        mock_preview_result = Mock()
        mock_preview_result.content = "Test content"
        mock_preview_result.metadata = {"filename": "test.pdf"}
        mock_preview_result.structure = {"total_pages": 1}
        mock_preview_result.quality_metrics = {"overall_confidence": 0.8}
        mock_preview_result.file_size = 1024
        mock_preview_result.extraction_time = 1.5
        mock_preview_result.confidence_score = 0.8
        mock_preview_result.warnings = []
        mock_preview_result.errors = []
        mock_preview_system.preview_pdf_extraction.return_value = mock_preview_result
        mock_get_preview_system.return_value = mock_preview_system

        # Create test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"test content")
            test_file = f.name

        try:
            request_data = {
                "file_path": test_file,
                "config": {"max_preview_size": 1000},
                "include_quality_assessment": True,
                "include_structured_content": True,
            }

            response = self.client.post("/preview", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "completed"
            assert "request_id" in data
            assert data["preview_result"]["confidence_score"] == 0.8
            assert data["processing_time"] > 0

        finally:
            Path(test_file).unlink()

    def test_preview_file_not_found(self):
        """Test preview endpoint with non-existent file."""
        request_data = {
            "file_path": "nonexistent.pdf",
            "include_quality_assessment": True,
            "include_structured_content": True,
        }

        response = self.client.post("/preview", json=request_data)
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    @patch("milkbottle.api_server.get_export_menu")
    def test_get_export_formats_endpoint(self, mock_get_export_menu):
        """Test get export formats endpoint."""
        # Mock export menu with proper ExportFormat objects
        from milkbottle.export_menu import ExportFormat

        mock_export_menu = Mock()
        mock_export_menu.available_formats = {
            "pdf": ExportFormat(
                name="PDF",
                extension=".pdf",
                description="PDF format",
                supported_features=["text", "images"],
                config_options={"quality": "high"},
                preview_supported=True,
            ),
            "markdown": ExportFormat(
                name="Markdown",
                extension=".md",
                description="Markdown format",
                supported_features=["text"],
                config_options={},
                preview_supported=True,
            ),
        }
        mock_get_export_menu.return_value = mock_export_menu

        response = self.client.get("/export/formats")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "pdf"
        assert data[0]["name"] == "PDF"
        assert data[0]["extension"] == ".pdf"
        assert data[1]["id"] == "markdown"
        assert data[1]["name"] == "Markdown"

    @patch("milkbottle.api_server.get_export_menu")
    def test_export_endpoint(self, mock_get_export_menu):
        """Test export endpoint."""
        # Mock export menu
        mock_export_menu = Mock()
        mock_export_menu.selected_formats = []
        mock_export_menu.export_config = {}
        mock_export_menu.execute_export.return_value = {
            "pdf": "test.pdf",
            "markdown": "test.md",
        }
        mock_get_export_menu.return_value = mock_export_menu

        # Create test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"test content")
            test_file = f.name

        try:
            request_data = {
                "file_path": test_file,
                "selected_formats": ["pdf", "markdown"],
                "config": {"include_images": True},
                "output_directory": "exports",
            }

            response = self.client.post("/export", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "completed"
            assert "request_id" in data
            assert data["exported_files"] == ["test.pdf", "test.md"]
            assert data["processing_time"] > 0

        finally:
            Path(test_file).unlink()

    def test_export_file_not_found(self):
        """Test export endpoint with non-existent file."""
        request_data = {
            "file_path": "nonexistent.pdf",
            "selected_formats": ["pdf"],
            "output_directory": "exports",
        }

        response = self.client.post("/export", json=request_data)
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    @patch("milkbottle.api_server.get_advanced_analytics")
    def test_analytics_endpoint(self, mock_get_advanced_analytics):
        """Test analytics endpoint."""
        # Mock advanced analytics
        mock_analytics = Mock()
        mock_result = Mock()
        mock_result.quality_metrics = Mock(
            readability_score=0.8,
            coherence_score=0.7,
            completeness_score=0.9,
            accuracy_score=0.85,
            relevance_score=0.75,
            overall_score=0.8,
            confidence=0.9,
            recommendations=["Improve readability"],
            warnings=[],
        )
        mock_result.classification = Mock(
            document_type="Academic Paper",
            subject_area="Technology",
            complexity_level="Advanced",
            target_audience="Researchers",
            language="English",
            confidence=0.9,
            tags=["research", "technology"],
        )
        mock_result.insights = Mock(
            processing_time_prediction=2.5,
            quality_improvement_potential=0.2,
            recommended_formats=["pdf", "markdown"],
            optimization_suggestions=["Simplify sentences"],
            risk_factors=[],
        )
        mock_analytics.analyze_content.return_value = mock_result
        mock_get_advanced_analytics.return_value = mock_analytics

        # Create test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"test content")
            test_file = f.name

        try:
            request_data = {
                "file_path": test_file,
                "include_quality_metrics": True,
                "include_classification": True,
                "include_predictive_insights": True,
            }

            response = self.client.post("/analytics", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "completed"
            assert "request_id" in data
            assert data["analytics_result"]["quality_metrics"]["overall_score"] == 0.8
            assert (
                data["analytics_result"]["classification"]["document_type"]
                == "Academic Paper"
            )
            assert (
                data["analytics_result"]["insights"]["processing_time_prediction"]
                == 2.5
            )
            assert data["processing_time"] > 0

        finally:
            Path(test_file).unlink()

    def test_analytics_file_not_found(self):
        """Test analytics endpoint with non-existent file."""
        request_data = {
            "file_path": "nonexistent.pdf",
            "include_quality_metrics": True,
            "include_classification": True,
            "include_predictive_insights": True,
        }

        response = self.client.post("/analytics", json=request_data)
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_get_available_wizards_endpoint(self):
        """Test get available wizards endpoint."""
        response = self.client.get("/wizards")
        assert response.status_code == 200

        data = response.json()
        assert data == ["pdfmilker", "venvmilker", "fontmilker"]

    @patch("milkbottle.api_server.run_wizard")
    def test_run_configuration_wizard_endpoint(self, mock_run_wizard):
        """Test run configuration wizard endpoint."""
        # Mock wizard
        mock_run_wizard.return_value = {"output_dir": "extracted"}

        request_data = {
            "wizard_type": "pdfmilker",
            "config": {"output_dir": "extracted"},
        }

        response = self.client.post("/wizards/pdfmilker", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert "request_id" in data
        assert data["configuration"]["output_dir"] == "extracted"
        assert data["processing_time"] > 0

    def test_run_wizard_invalid_type(self):
        """Test run wizard endpoint with invalid wizard type."""
        request_data = {"wizard_type": "invalid_wizard", "config": {}}

        response = self.client.post("/wizards/invalid_wizard", json=request_data)
        assert response.status_code == 400
        assert "Unknown wizard type" in response.json()["detail"]

    def test_upload_file_endpoint(self):
        """Test file upload endpoint."""
        # Create test file content
        test_content = b"test file content"

        response = self.client.post(
            "/upload", files={"file": ("test.txt", test_content, "text/plain")}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "File uploaded successfully"
        assert "file_path" in data
        assert data["file_size"] == len(test_content)
        assert data["filename"] == "test.txt"

        # Clean up uploaded file
        uploaded_file = Path(data["file_path"])
        if uploaded_file.exists():
            uploaded_file.unlink()

    def test_download_file_endpoint(self):
        """Test file download endpoint."""
        # Create test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            test_file = f.name

        try:
            response = self.client.get(f"/download/{test_file}")
            assert response.status_code == 200
            assert response.content == b"test content"

        finally:
            Path(test_file).unlink()

    def test_download_file_not_found(self):
        """Test download endpoint with non-existent file."""
        response = self.client.get("/download/nonexistent.txt")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]


class TestAPIServerFunctions:
    """Test API server utility functions."""

    def test_get_api_server(self):
        """Test get_api_server function."""
        api_server = get_api_server(host="127.0.0.1", port=8000)

        assert isinstance(api_server, MilkBottleAPI)
        assert api_server.host == "127.0.0.1"
        assert api_server.port == 8000

    @patch("milkbottle.api_server.uvicorn.run")
    def test_start_api_server(self, mock_uvicorn_run):
        """Test start_api_server function."""
        # Mock uvicorn.run to avoid actually starting the server
        mock_uvicorn_run.return_value = None

        # This should not raise an exception
        start_api_server(host="127.0.0.1", port=8000, reload=False)

        # Verify uvicorn.run was called
        mock_uvicorn_run.assert_called_once()

    def test_api_server_singleton(self):
        """Test that get_api_server returns the same instance."""
        api_server1 = get_api_server(host="127.0.0.1", port=8000)
        api_server2 = get_api_server(host="127.0.0.1", port=8000)

        assert api_server1 is api_server2


class TestAPIErrorHandling:
    """Test API error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = MilkBottleAPI(host="127.0.0.1", port=8000)
        self.client = TestClient(self.api.app)

    def test_health_check_exception_handling(self):
        """Test health check endpoint exception handling."""
        # Mock registry to raise exception
        mock_registry = Mock()
        mock_registry.discover_bottles.side_effect = Exception("Registry error")
        self.api.registry = mock_registry

        response = self.client.get("/health")
        assert response.status_code == 200  # Should still return 200 with error status

        data = response.json()
        assert data["status"] == "error"
        assert "Registry error" in data["errors"][0]

    def test_list_bottles_exception_handling(self):
        """Test list bottles endpoint exception handling."""
        # Mock registry to raise exception
        mock_registry = Mock()
        mock_registry.discover_bottles.side_effect = Exception("Registry error")
        self.api.registry = mock_registry

        response = self.client.get("/bottles")
        assert response.status_code == 500
        assert "Registry error" in response.json()["detail"]

    @patch("milkbottle.api_server.get_export_menu")
    def test_export_formats_exception_handling(self, mock_get_export_menu):
        """Test export formats endpoint exception handling."""
        # Mock export menu to raise exception
        mock_get_export_menu.side_effect = Exception("Export menu error")

        response = self.client.get("/export/formats")
        assert response.status_code == 500
        assert "Export menu error" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
