"""Tests for MilkBottle Plugin SDK."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from milkbottle.plugin_sdk import (
    PluginSDK,
    build_plugin,
    create_plugin,
    get_sdk,
    list_templates,
    package_plugin,
    test_plugin,
    validate_plugin,
)
from milkbottle.plugin_sdk.generator import PluginGenerator
from milkbottle.plugin_sdk.packaging import PluginPackager
from milkbottle.plugin_sdk.templates import PluginTemplate
from milkbottle.plugin_sdk.testing import PluginTester
from milkbottle.plugin_sdk.validator import PluginValidator


class TestPluginSDK:
    """Test PluginSDK class."""

    def test_sdk_initialization(self):
        """Test SDK initialization."""
        sdk = PluginSDK()
        assert sdk is not None
        assert sdk.template_manager is not None
        assert sdk.generator is not None
        assert sdk.validator is not None
        assert sdk.tester is not None
        assert sdk.packager is not None

    def test_get_sdk_singleton(self):
        """Test SDK singleton pattern."""
        sdk1 = get_sdk()
        sdk2 = get_sdk()
        assert sdk1 is sdk2

    @patch("milkbottle.plugin_sdk.generator.PluginGenerator.generate_plugin")
    def test_create_plugin_success(self, mock_generate):
        """Test successful plugin creation."""
        mock_generate.return_value = True

        sdk = PluginSDK()
        result = sdk.create_plugin("test_plugin", "basic")

        assert result is True
        mock_generate.assert_called_once()

    @patch("milkbottle.plugin_sdk.generator.PluginGenerator.generate_plugin")
    def test_create_plugin_failure(self, mock_generate):
        """Test failed plugin creation."""
        mock_generate.return_value = False

        sdk = PluginSDK()
        result = sdk.create_plugin("test_plugin", "basic")

        assert result is False

    @patch("milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin")
    def test_validate_plugin(self, mock_validate):
        """Test plugin validation."""
        mock_validate.return_value = {"valid": True, "score": 0.9}

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.validate_plugin(plugin_path)

        assert result["valid"] is True
        assert result["score"] == 0.9
        mock_validate.assert_called_once_with(plugin_path)

    @patch("milkbottle.plugin_sdk.testing.PluginTester.test_plugin")
    def test_test_plugin(self, mock_test):
        """Test plugin testing."""
        mock_test.return_value = {"success": True, "tests_passed": 5}

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.test_plugin(plugin_path, "unit")

        assert result["success"] is True
        assert result["tests_passed"] == 5
        mock_test.assert_called_once_with(plugin_path, "unit")

    @patch("milkbottle.plugin_sdk.packaging.PluginPackager.package_plugin")
    def test_package_plugin(self, mock_package):
        """Test plugin packaging."""
        mock_package.return_value = True

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.package_plugin(plugin_path, format="zip")

        assert result is True
        mock_package.assert_called_once_with(plugin_path, None, "zip")

    @patch("milkbottle.plugin_sdk.templates.PluginTemplate.list_templates")
    def test_list_templates(self, mock_list):
        """Test template listing."""
        mock_list.return_value = [{"name": "basic", "description": "Basic template"}]

        sdk = PluginSDK()
        result = sdk.list_templates()

        assert len(result) == 1
        assert result[0]["name"] == "basic"
        mock_list.assert_called_once()

    @patch("milkbottle.plugin_sdk.templates.PluginTemplate.get_template_info")
    def test_get_template_info(self, mock_get_info):
        """Test template info retrieval."""
        mock_get_info.return_value = {"name": "basic", "description": "Basic template"}

        sdk = PluginSDK()
        result = sdk.get_template_info("basic")

        assert result["name"] == "basic"
        assert result["description"] == "Basic template"
        mock_get_info.assert_called_once_with("basic")

    @patch("milkbottle.plugin_sdk.templates.PluginTemplate.create_template")
    def test_create_template(self, mock_create):
        """Test template creation."""
        mock_create.return_value = True

        sdk = PluginSDK()
        template_path = Path("/tmp/template")
        result = sdk.create_template("custom", template_path, "Custom template")

        assert result is True
        mock_create.assert_called_once_with("custom", template_path, "Custom template")

    @patch("milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin")
    @patch("milkbottle.plugin_sdk.testing.PluginTester.test_plugin")
    @patch("milkbottle.plugin_sdk.packaging.PluginPackager.package_plugin")
    def test_build_plugin_development(self, mock_package, mock_test, mock_validate):
        """Test plugin build for development."""
        mock_validate.return_value = {"valid": True}
        mock_test.return_value = {"success": True}

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.build_plugin(plugin_path, "development")

        assert result is True
        mock_validate.assert_called_once_with(plugin_path)
        mock_test.assert_called_once_with(plugin_path, "all")
        mock_package.assert_not_called()

    @patch("milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin")
    @patch("milkbottle.plugin_sdk.testing.PluginTester.test_plugin")
    @patch("milkbottle.plugin_sdk.packaging.PluginPackager.package_plugin")
    def test_build_plugin_production(self, mock_package, mock_test, mock_validate):
        """Test plugin build for production."""
        mock_validate.return_value = {"valid": True}
        mock_test.return_value = {"success": True}
        mock_package.return_value = True

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.build_plugin(plugin_path, "production")

        assert result is True
        mock_validate.assert_called_once_with(plugin_path)
        mock_test.assert_called_once_with(plugin_path, "all")
        mock_package.assert_called_once_with(plugin_path, None, "zip")

    @patch("milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin")
    @patch("milkbottle.plugin_sdk.testing.PluginTester.test_plugin")
    def test_build_plugin_validation_failure(self, mock_test, mock_validate):
        """Test plugin build with validation failure."""
        mock_validate.return_value = {"valid": False}

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.build_plugin(plugin_path, "development")

        assert result is False
        mock_validate.assert_called_once_with(plugin_path)
        mock_test.assert_not_called()

    @patch("milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin")
    @patch("milkbottle.plugin_sdk.testing.PluginTester.test_plugin")
    def test_build_plugin_test_failure(self, mock_test, mock_validate):
        """Test plugin build with test failure."""
        mock_validate.return_value = {"valid": True}
        mock_test.return_value = {"success": False}

        sdk = PluginSDK()
        plugin_path = Path("/tmp/test_plugin")
        result = sdk.build_plugin(plugin_path, "development")

        assert result is False
        mock_validate.assert_called_once_with(plugin_path)
        mock_test.assert_called_once_with(plugin_path, "all")

    def test_get_plugin_info(self):
        """Test plugin info retrieval."""
        sdk = PluginSDK()
        plugin_path = Path("/tmp/nonexistent_plugin")

        with patch(
            "milkbottle.plugin_sdk.validator.PluginValidator.validate_plugin"
        ) as mock_validate:
            with patch(
                "milkbottle.plugin_sdk.testing.PluginTester.test_plugin"
            ) as mock_test:
                mock_validate.return_value = {"valid": True}
                mock_test.return_value = {"success": True}

                result = sdk.get_plugin_info(plugin_path)

                assert result["path"] == str(plugin_path)
                assert result["exists"] is False
                assert "validation" in result
                assert "tests" in result
                assert "metadata" in result


class TestPluginTemplate:
    """Test PluginTemplate class."""

    def test_template_initialization(self):
        """Test template initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = PluginTemplate(Path(temp_dir))
            assert template is not None
            assert template.templates_dir == Path(temp_dir) / "templates"

    def test_list_templates_empty(self):
        """Test listing templates when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = PluginTemplate(Path(temp_dir))
            templates = template.list_templates()
            assert templates == []

    def test_get_template_info_nonexistent(self):
        """Test getting info for nonexistent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = PluginTemplate(Path(temp_dir))
            info = template.get_template_info("nonexistent")
            assert info is None

    def test_create_template(self):
        """Test template creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = PluginTemplate(Path(temp_dir))

            # Create a simple template
            template_dir = Path(temp_dir) / "test_template"
            template_dir.mkdir()
            (template_dir / "test_file.txt").write_text("test content")

            result = template.create_template("test", template_dir, "Test template")
            assert result is True

            # Check if template was created
            templates = template.list_templates()
            assert len(templates) == 1
            assert templates[0]["name"] == "test"

    def test_render_template(self):
        """Test template rendering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = PluginTemplate(Path(temp_dir))

            # Create a template with variables
            template_dir = Path(temp_dir) / "test_template"
            template_dir.mkdir()
            (template_dir / "test_file.txt").write_text("Hello {{ name }}!")

            # Create template info
            (template_dir / "template.yaml").write_text(
                """
name: test
description: Test template
version: 1.0.0
author: Test Author
tags: [test]
files: [test_file.txt]
"""
            )

            # Render template
            output_dir = Path(temp_dir) / "output"
            context = {"name": "World"}

            result = template.render_template("test", context, output_dir)
            assert result is True

            # Check rendered file
            rendered_file = output_dir / "test_file.txt"
            assert rendered_file.exists()
            assert rendered_file.read_text() == "Hello World!"


class TestPluginGenerator:
    """Test PluginGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = PluginGenerator()
        assert generator is not None

    def test_validate_plugin_name_valid(self):
        """Test valid plugin name validation."""
        generator = PluginGenerator()

        valid_names = ["test_plugin", "my_plugin", "plugin123", "testPlugin"]
        for name in valid_names:
            assert generator._validate_plugin_name(name) is True

    def test_validate_plugin_name_invalid(self):
        """Test invalid plugin name validation."""
        generator = PluginGenerator()

        invalid_names = ["", "test-plugin", "123plugin", "test", "tests", "docs"]
        for name in invalid_names:
            assert generator._validate_plugin_name(name) is False

    def test_prepare_context(self):
        """Test context preparation."""
        generator = PluginGenerator()
        template_info = {"name": "basic", "description": "Basic template"}

        context = generator._prepare_context(
            "test_plugin", template_info, author="Test Author", version="2.0.0"
        )

        assert context["plugin_name"] == "test_plugin"
        assert context["class_name"] == "TestPlugin"
        assert context["author"] == "Test Author"
        assert context["version"] == "2.0.0"
        assert context["template_info"] == template_info

    @patch("milkbottle.plugin_sdk.generator.PluginTemplate")
    @patch("milkbottle.plugin_sdk.generator.PluginGenerator._validate_plugin_name")
    def test_generate_plugin_invalid_name(self, mock_validate, mock_template_class):
        """Test plugin generation with invalid name."""
        mock_validate.return_value = False

        generator = PluginGenerator()
        result = generator.generate_plugin("invalid-name")

        assert result is False

    @patch("milkbottle.plugin_sdk.generator.PluginTemplate")
    @patch("milkbottle.plugin_sdk.generator.PluginGenerator._validate_plugin_name")
    def test_generate_plugin_output_exists(self, mock_validate, mock_template_class):
        """Test plugin generation when output directory exists."""
        mock_validate.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "existing_plugin"
            output_dir.mkdir()

            generator = PluginGenerator()
            result = generator.generate_plugin("existing_plugin", output_dir=output_dir)

            assert result is False


class TestPluginValidator:
    """Test PluginValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = PluginValidator()
        assert validator is not None
        assert len(validator.required_files) > 0
        assert len(validator.required_exports) > 0

    def test_validate_structure_missing_files(self):
        """Test structure validation with missing files."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            results = validator._validate_structure(plugin_path)

            assert results["valid"] is False
            assert len(results["errors"]) > 0
            assert len(results["missing_files"]) > 0

    def test_validate_structure_valid(self):
        """Test structure validation with valid structure."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)

            # Create required files
            for file_name in validator.required_files:
                file_path = plugin_path / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("test content")

            results = validator._validate_structure(plugin_path)
            assert results["valid"] is True
            assert len(results["errors"]) == 0

    def test_extract_metadata(self):
        """Test metadata extraction."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            init_file = Path(temp_dir) / "__init__.py"
            init_content = """
__version__ = "1.0.0"
__name__ = "test_plugin"
__description__ = "Test plugin"
__author__ = "Test Author"
__email__ = "test@example.com"
__license__ = "MIT"
__dependencies__ = ["click", "rich"]
__capabilities__ = ["cli", "web"]
__tags__ = ["test", "example"]
"""
            init_file.write_text(init_content)

            metadata = validator._extract_metadata(init_file)

            assert metadata["version"] == "1.0.0"
            assert metadata["name"] == "test_plugin"
            assert metadata["description"] == "Test plugin"
            assert metadata["author"] == "Test Author"
            assert metadata["email"] == "test@example.com"
            assert metadata["license"] == "MIT"
            assert "click" in metadata["dependencies"]
            assert "cli" in metadata["capabilities"]
            assert "test" in metadata["tags"]

    def test_validate_metadata_valid(self):
        """Test metadata validation with valid metadata."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            init_file = plugin_path / "__init__.py"
            init_content = """
__version__ = "1.0.0"
__name__ = "test_plugin"
__description__ = "Test plugin"
__author__ = "Test Author"
__email__ = "test@example.com"
__license__ = "MIT"
"""
            init_file.write_text(init_content)

            results = validator._validate_metadata(plugin_path)
            assert results["valid"] is True
            assert len(results["errors"]) == 0

    def test_validate_metadata_invalid_version(self):
        """Test metadata validation with invalid version."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            init_file = plugin_path / "__init__.py"
            init_content = """
__version__ = "invalid-version"
__name__ = "test_plugin"
__description__ = "Test plugin"
__author__ = "Test Author"
"""
            init_file.write_text(init_content)

            results = validator._validate_metadata(plugin_path)
            assert results["valid"] is False
            assert len(results["errors"]) > 0

    def test_validate_code(self):
        """Test code validation."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)

            # Create a Python file
            py_file = plugin_path / "test.py"
            py_content = '''
"""Test module docstring."""

def test_function() -> str:
    """Test function docstring."""
    return "test"

class TestClass:
    """Test class docstring."""
    
    def test_method(self) -> None:
        """Test method docstring."""
        pass
'''
            py_file.write_text(py_content)

            results = validator._validate_code(plugin_path)
            assert results["valid"] is True
            assert results["metrics"]["total_files"] == 1
            assert results["metrics"]["total_lines"] > 0
            assert results["metrics"]["total_functions"] > 0
            assert results["metrics"]["total_classes"] > 0

    def test_validate_dependencies(self):
        """Test dependencies validation."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            requirements_file = plugin_path / "requirements.txt"
            requirements_file.write_text("click>=8.0.0\nrich>=13.0.0\n")

            results = validator._validate_dependencies(plugin_path)
            assert results["valid"] is True
            assert len(results["dependencies"]) == 2

    def test_validate_interface(self):
        """Test interface validation."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            init_file = plugin_path / "__init__.py"
            init_content = '''
from milkbottle.plugin_system.core import PluginInterface

class TestPlugin(PluginInterface):
    """Test plugin implementation."""
    pass

def get_plugin_interface() -> PluginInterface:
    return TestPlugin()

def get_cli():
    pass

def get_metadata():
    pass

def validate_config(config):
    pass

def health_check():
    pass
'''
            init_file.write_text(init_content)

            results = validator._validate_interface(plugin_path)
            assert results["valid"] is True
            assert len(results["found_exports"]) >= 5

    def test_validate_security(self):
        """Test security validation."""
        validator = PluginValidator()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            py_file = plugin_path / "test.py"
            py_content = """
import os
import subprocess

def dangerous_function():
    os.system("rm -rf /")
    subprocess.call(["rm", "-rf", "/"])
    eval("print('dangerous')")
    exec("print('dangerous')")
"""
            py_file.write_text(py_content)

            results = validator._validate_security(plugin_path)
            assert results["valid"] is True  # Should be valid but with warnings
            assert len(results["security_issues"]) > 0
            assert len(results["warnings"]) > 0

    def test_calculate_score(self):
        """Test score calculation."""
        validator = PluginValidator()

        checks = {
            "structure": {"valid": True},
            "metadata": {"valid": True},
            "code": {"valid": True},
            "dependencies": {"valid": True},
            "interface": {"valid": True},
            "security": {"valid": True},
        }

        score = validator._calculate_score(checks)
        assert score == 1.0

        # Test with some failures
        checks["structure"] = {"valid": False, "errors": ["Missing file"]}
        score = validator._calculate_score(checks)
        assert score < 1.0


class TestPluginTester:
    """Test PluginTester class."""

    def test_tester_initialization(self):
        """Test tester initialization."""
        tester = PluginTester()
        assert tester is not None

    @patch("milkbottle.plugin_sdk.testing.subprocess.run")
    def test_run_unit_tests_success(self, mock_run):
        """Test successful unit test execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "5 passed, 0 failed, 0 skipped"
        mock_run.return_value = mock_process

        tester = PluginTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            test_file = plugin_path / "tests" / "test_plugin.py"
            test_file.parent.mkdir()
            test_file.write_text("def test_function(): pass")

            results = tester._run_unit_tests(plugin_path)

            assert results["tests_passed"] == 5
            assert results["tests_failed"] == 0
            assert results["tests_skipped"] == 0
            assert results["return_code"] == 0

    @patch("milkbottle.plugin_sdk.testing.subprocess.run")
    def test_run_unit_tests_failure(self, mock_run):
        """Test failed unit test execution."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "3 passed, 2 failed, 0 skipped"
        mock_run.return_value = mock_process

        tester = PluginTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            test_file = plugin_path / "tests" / "test_plugin.py"
            test_file.parent.mkdir()
            test_file.write_text("def test_function(): pass")

            results = tester._run_unit_tests(plugin_path)

            assert results["tests_passed"] == 3
            assert results["tests_failed"] == 2
            assert results["tests_skipped"] == 0
            assert results["return_code"] == 1
            assert len(results["errors"]) > 0

    def test_create_test_template_unit(self):
        """Test unit test template creation."""
        tester = PluginTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            tests_dir = plugin_path / "tests"

            result = tester.create_test_template(plugin_path, "unit")
            assert result is True

            # Check if test file was created
            test_files = list(tests_dir.rglob("*.py"))
            assert len(test_files) > 0

    def test_create_test_template_integration(self):
        """Test integration test template creation."""
        tester = PluginTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            tests_dir = plugin_path / "tests"

            result = tester.create_test_template(plugin_path, "integration")
            assert result is True

            # Check if test file was created
            test_files = list(tests_dir.rglob("*integration*.py"))
            assert len(test_files) > 0

    def test_create_test_template_performance(self):
        """Test performance test template creation."""
        tester = PluginTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            tests_dir = plugin_path / "tests"

            result = tester.create_test_template(plugin_path, "performance")
            assert result is True

            # Check if test file was created
            test_files = list(tests_dir.rglob("*performance*.py"))
            assert len(test_files) > 0


class TestPluginPackager:
    """Test PluginPackager class."""

    def test_packager_initialization(self):
        """Test packager initialization."""
        packager = PluginPackager()
        assert packager is not None

    def test_should_skip_file(self):
        """Test file skipping logic."""
        packager = PluginPackager()

        # Files that should be skipped
        skip_files = [
            Path(".git/config"),
            Path("__pycache__/test.pyc"),
            Path(".DS_Store"),
            Path("build/"),
            Path("dist/"),
            Path("*.egg-info/"),
        ]

        for file_path in skip_files:
            assert packager._should_skip_file(file_path) is True

        # Files that should not be skipped
        keep_files = [
            Path("__init__.py"),
            Path("cli.py"),
            Path("README.md"),
            Path("requirements.txt"),
        ]

        for file_path in keep_files:
            assert packager._should_skip_file(file_path) is False

    def test_create_zip_package(self):
        """Test ZIP package creation."""
        packager = PluginPackager()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "test_plugin"
            plugin_path.mkdir()

            # Create some test files
            (plugin_path / "__init__.py").write_text("test")
            (plugin_path / "cli.py").write_text("test")
            (plugin_path / "README.md").write_text("test")
            (plugin_path / "__pycache__" / "test.pyc").write_text("test")
            (plugin_path / "__pycache__").mkdir()

            output_path = Path(temp_dir) / "test_plugin.zip"

            result = packager._create_zip_package(plugin_path, output_path)
            assert result is True
            assert output_path.exists()

            # Verify ZIP contents
            import zipfile

            with zipfile.ZipFile(output_path, "r") as zipf:
                file_list = zipf.namelist()
                assert "__init__.py" in file_list
                assert "cli.py" in file_list
                assert "README.md" in file_list
                assert "__pycache__/test.pyc" not in file_list  # Should be skipped

    def test_create_targz_package(self):
        """Test tar.gz package creation."""
        packager = PluginPackager()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "test_plugin"
            plugin_path.mkdir()

            # Create some test files
            (plugin_path / "__init__.py").write_text("test")
            (plugin_path / "cli.py").write_text("test")
            (plugin_path / "README.md").write_text("test")

            output_path = Path(temp_dir) / "test_plugin.tar.gz"

            result = packager._create_targz_package(plugin_path, output_path)
            assert result is True
            assert output_path.exists()

    def test_extract_metadata(self):
        """Test metadata extraction."""
        packager = PluginPackager()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)
            init_file = plugin_path / "__init__.py"
            init_content = """
__version__ = "1.0.0"
__name__ = "test_plugin"
__description__ = "Test plugin"
__author__ = "Test Author"
__email__ = "test@example.com"
__license__ = "MIT"
"""
            init_file.write_text(init_content)

            metadata = packager._extract_metadata(plugin_path)

            assert metadata["version"] == "1.0.0"
            assert metadata["name"] == "test_plugin"
            assert metadata["description"] == "Test plugin"
            assert metadata["author"] == "Test Author"
            assert metadata["email"] == "test@example.com"
            assert metadata["license"] == "MIT"

    def test_create_manifest(self):
        """Test manifest creation."""
        packager = PluginPackager()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)

            # Create some test files
            (plugin_path / "__init__.py").write_text("test")
            (plugin_path / "cli.py").write_text("test")
            (plugin_path / "README.md").write_text("test")
            (plugin_path / "__pycache__" / "test.pyc").write_text("test")
            (plugin_path / "__pycache__").mkdir()

            result = packager.create_manifest(plugin_path)
            assert result is True

            manifest_file = plugin_path / "MANIFEST.in"
            assert manifest_file.exists()

            content = manifest_file.read_text()
            assert "include __init__.py" in content
            assert "include cli.py" in content
            assert "include README.md" in content
            assert "include __pycache__/test.pyc" not in content  # Should be excluded

    def test_validate_package_zip(self):
        """Test ZIP package validation."""
        packager = PluginPackager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test ZIP package
            plugin_path = Path(temp_dir) / "test_plugin"
            plugin_path.mkdir()
            (plugin_path / "__init__.py").write_text("test")
            (plugin_path / "cli.py").write_text("test")
            (plugin_path / "README.md").write_text("test")

            zip_path = Path(temp_dir) / "test_plugin.zip"
            packager._create_zip_package(plugin_path, zip_path)

            results = packager.validate_package(zip_path)
            assert results["valid"] is True
            assert results["file_count"] > 0
            assert results["file_size"] > 0


# Convenience function tests
class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_create_plugin_function(self, mock_get_sdk):
        """Test create_plugin convenience function."""
        mock_sdk = Mock()
        mock_sdk.create_plugin.return_value = True
        mock_get_sdk.return_value = mock_sdk

        result = create_plugin("test_plugin", "basic")

        assert result is True
        mock_sdk.create_plugin.assert_called_once_with("test_plugin", "basic", None)

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_validate_plugin_function(self, mock_get_sdk):
        """Test validate_plugin convenience function."""
        mock_sdk = Mock()
        mock_sdk.validate_plugin.return_value = {"valid": True}
        mock_get_sdk.return_value = mock_sdk

        plugin_path = Path("/tmp/test_plugin")
        result = validate_plugin(plugin_path)

        assert result["valid"] is True
        mock_sdk.validate_plugin.assert_called_once_with(plugin_path)

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_test_plugin_function(self, mock_get_sdk):
        """Test test_plugin convenience function."""
        mock_sdk = Mock()
        mock_sdk.test_plugin.return_value = {"success": True}
        mock_get_sdk.return_value = mock_sdk

        plugin_path = Path("/tmp/test_plugin")
        result = test_plugin(plugin_path, "unit")

        assert result["success"] is True
        mock_sdk.test_plugin.assert_called_once_with(plugin_path, "unit")

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_package_plugin_function(self, mock_get_sdk):
        """Test package_plugin convenience function."""
        mock_sdk = Mock()
        mock_sdk.package_plugin.return_value = True
        mock_get_sdk.return_value = mock_sdk

        plugin_path = Path("/tmp/test_plugin")
        result = package_plugin(plugin_path, format="zip")

        assert result is True
        mock_sdk.package_plugin.assert_called_once_with(plugin_path, None, "zip")

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_list_templates_function(self, mock_get_sdk):
        """Test list_templates convenience function."""
        mock_sdk = Mock()
        mock_sdk.list_templates.return_value = [{"name": "basic"}]
        mock_get_sdk.return_value = mock_sdk

        result = list_templates()

        assert len(result) == 1
        assert result[0]["name"] == "basic"
        mock_sdk.list_templates.assert_called_once()

    @patch("milkbottle.plugin_sdk.get_sdk")
    def test_build_plugin_function(self, mock_get_sdk):
        """Test build_plugin convenience function."""
        mock_sdk = Mock()
        mock_sdk.build_plugin.return_value = True
        mock_get_sdk.return_value = mock_sdk

        plugin_path = Path("/tmp/test_plugin")
        result = build_plugin(plugin_path, "development")

        assert result is True
        mock_sdk.build_plugin.assert_called_once_with(plugin_path, "development")
        plugin_path = Path("/tmp/test_plugin")
        result = build_plugin(plugin_path, "development")

        assert result is True
        mock_sdk.build_plugin.assert_called_once_with(plugin_path, "development")
