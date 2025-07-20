# MilkBottle Plugin Development Guide

## 🚀 Overview

MilkBottle provides a comprehensive plugin system that allows developers to extend functionality through **bottles** - self-contained modules that can be discovered, loaded, and managed dynamically. This guide covers everything you need to know to create, package, and distribute MilkBottle plugins.

## 📋 Table of Contents

1. [Plugin Architecture](#plugin-architecture)
2. [Creating Your First Plugin](#creating-your-first-plugin)
3. [Plugin Manifest](#plugin-manifest)
4. [Entry Point Registration](#entry-point-registration)
5. [Standard Interface](#standard-interface)
6. [Configuration Management](#configuration-management)
7. [Testing Your Plugin](#testing-your-plugin)
8. [Packaging and Distribution](#packaging-and-distribution)
9. [Advanced Features](#advanced-features)
10. [Best Practices](#best-practices)

## 🏗️ Plugin Architecture

### Core Concepts

- **Bottle**: A self-contained module that provides specific functionality
- **Registry**: Central system for discovering and managing bottles
- **Entry Point**: Standard Python mechanism for plugin registration
- **Manifest**: Metadata file describing plugin capabilities and requirements

### Plugin Types

1. **Entry Point Plugins**: Registered via `setup.py` or `pyproject.toml`
2. **Local Plugins**: Placed in `src/milkbottle/modules/` directory
3. **Archive Plugins**: Distributed as `.zip`, `.tar.gz`, or `.whl` files

## 🎯 Creating Your First Plugin

### Step 1: Project Structure

Create a new directory for your plugin:

```bash
mkdir my-milkbottle-plugin
cd my-milkbottle-plugin
```

### Step 2: Basic Structure

```
my-milkbottle-plugin/
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       ├── cli.py
│       ├── core.py
│       └── config.py
├── tests/
│   ├── __init__.py
│   └── test_my_plugin.py
├── pyproject.toml
├── README.md
└── plugin.yaml
```

### Step 3: Core Implementation

#### `src/my_plugin/__init__.py`

```python
"""My MilkBottle Plugin - A sample plugin for demonstration."""

from __future__ import annotations

from typing import Any, Dict

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "A sample MilkBottle plugin for demonstration purposes"


def get_metadata() -> Dict[str, Any]:
    """Get plugin metadata for registry discovery."""
    return {
        "name": "my_plugin",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "email": __email__,
        "capabilities": ["text_processing", "data_export"],
        "dependencies": ["requests>=2.25.0"],
        "config_schema": {
            "enabled": {"type": "boolean", "default": True},
            "api_key": {"type": "string", "required": True},
            "endpoint": {"type": "string", "default": "https://api.example.com"},
        },
    }


def get_cli():
    """Get CLI interface for the plugin."""
    from .cli import app
    return app


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate plugin configuration."""
    if not config.get("enabled", True):
        return True

    if not config.get("api_key"):
        return False

    return True
```

#### `src/my_plugin/cli.py`

```python
"""CLI interface for My MilkBottle Plugin."""

import typer
from rich.console import Console
from rich.table import Table

from .core import MyPluginProcessor

app = typer.Typer(name="my_plugin", help="My MilkBottle Plugin")
console = Console()


@app.command()
def process(
    input_file: str = typer.Argument(..., help="Input file to process"),
    output_file: str = typer.Option(None, "--output", "-o", help="Output file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Process a file using My Plugin."""
    try:
        processor = MyPluginProcessor()
        result = processor.process_file(input_file, output_file)

        if verbose:
            console.print(f"✅ Successfully processed {input_file}")
            console.print(f"📊 Results: {result}")
        else:
            console.print(f"✅ Processed {input_file}")

    except Exception as e:
        console.print(f"❌ Error processing {input_file}: {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """Show plugin status and configuration."""
    table = Table(title="My Plugin Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", "1.0.0")
    table.add_row("Status", "Active")
    table.add_row("Capabilities", "text_processing, data_export")

    console.print(table)


if __name__ == "__main__":
    app()
```

#### `src/my_plugin/core.py`

```python
"""Core functionality for My MilkBottle Plugin."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("my_plugin.core")


class MyPluginProcessor:
    """Main processor for My Plugin."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.

        Args:
            config: Plugin configuration
        """
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        self.endpoint = self.config.get("endpoint", "https://api.example.com")

    def process_file(self, input_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Process an input file.

        Args:
            input_file: Path to input file
            output_file: Path to output file (optional)

        Returns:
            Processing results
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Read input file
        content = input_path.read_text(encoding="utf-8")

        # Process content (your plugin logic here)
        processed_content = self._process_content(content)

        # Write output
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(processed_content, encoding="utf-8")
            logger.info(f"Output written to: {output_file}")

        return {
            "input_file": str(input_path),
            "output_file": output_file,
            "content_length": len(content),
            "processed_length": len(processed_content),
            "success": True,
        }

    def _process_content(self, content: str) -> str:
        """Process content according to plugin logic.

        Args:
            content: Input content

        Returns:
            Processed content
        """
        # Example processing: convert to uppercase
        return content.upper()
```

### Step 4: Configuration

#### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-milkbottle-plugin"
version = "1.0.0"
description = "A sample MilkBottle plugin for demonstration purposes"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "requests>=2.25.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
]

[project.entry-points."milkbottle.bottles"]
my_plugin = "my_plugin"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
src_paths = ["src"]
```

#### `plugin.yaml`

```yaml
name: my_plugin
version: 1.0.0
description: A sample MilkBottle plugin for demonstration purposes
author: Your Name
entry_point: my_plugin
dependencies:
  - requests>=2.25.0
capabilities:
  - text_processing
  - data_export
config_schema:
  enabled:
    type: boolean
    default: true
    description: Enable or disable the plugin
  api_key:
    type: string
    required: true
    description: API key for external service
  endpoint:
    type: string
    default: https://api.example.com
    description: API endpoint URL
```

## 📋 Plugin Manifest

The plugin manifest (`plugin.yaml`) provides metadata and configuration information:

### Required Fields

- `name`: Unique plugin identifier
- `version`: Semantic version (e.g., "1.0.0")
- `description`: Human-readable description
- `entry_point`: Python module name

### Optional Fields

- `author`: Plugin author name
- `dependencies`: List of required packages
- `capabilities`: List of plugin capabilities
- `config_schema`: Configuration validation schema

### Configuration Schema

```yaml
config_schema:
  enabled:
    type: boolean
    default: true
    description: Enable or disable the plugin
  api_key:
    type: string
    required: true
    description: API key for authentication
  timeout:
    type: integer
    default: 30
    minimum: 1
    maximum: 300
    description: Request timeout in seconds
  retries:
    type: integer
    default: 3
    minimum: 0
    maximum: 10
    description: Number of retry attempts
```

## 🔌 Entry Point Registration

### Method 1: Using pyproject.toml (Recommended)

```toml
[project.entry-points."milkbottle.bottles"]
my_plugin = "my_plugin"
```

### Method 2: Using setup.py

```python
from setuptools import setup, find_packages

setup(
    name="my-milkbottle-plugin",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "milkbottle.bottles": [
            "my_plugin = my_plugin",
        ],
    },
    install_requires=[
        "requests>=2.25.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
)
```

## 🎯 Standard Interface

MilkBottle expects plugins to implement a standard interface:

### Required Functions

#### `get_metadata() -> Dict[str, Any]`

Returns plugin metadata for registry discovery.

#### `get_cli() -> typer.Typer`

Returns the CLI interface for the plugin.

### Optional Functions

#### `validate_config(config: Dict[str, Any]) -> bool`

Validates plugin configuration.

#### `health_check() -> Dict[str, Any]`

Performs plugin health check.

### Example Implementation

```python
def get_metadata() -> Dict[str, Any]:
    """Get plugin metadata."""
    return {
        "name": "my_plugin",
        "version": "1.0.0",
        "description": "My plugin description",
        "author": "Your Name",
        "capabilities": ["text_processing"],
        "dependencies": ["requests>=2.25.0"],
        "config_schema": {
            "enabled": {"type": "boolean", "default": True},
            "api_key": {"type": "string", "required": True},
        },
    }


def get_cli():
    """Get CLI interface."""
    from .cli import app
    return app


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration."""
    if not config.get("enabled", True):
        return True

    if not config.get("api_key"):
        return False

    return True


def health_check() -> Dict[str, Any]:
    """Perform health check."""
    try:
        # Test plugin functionality
        processor = MyPluginProcessor()
        result = processor.test_connection()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "details": result,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
```

## ⚙️ Configuration Management

### Plugin Configuration

Plugins can be configured through multiple sources:

1. **Default Values**: Hard-coded in the plugin
2. **Configuration Files**: `milkbottle.toml` or `plugin.yaml`
3. **Environment Variables**: `MY_PLUGIN_API_KEY`
4. **CLI Arguments**: `--api-key`

### Configuration Loading

```python
from milkbottle.config import get_config

def load_plugin_config():
    """Load plugin configuration."""
    config = get_config()
    plugin_config = config.get_bottle_config("my_plugin")

    # Merge with environment variables
    api_key = os.getenv("MY_PLUGIN_API_KEY") or plugin_config.get("api_key")

    return {
        "enabled": plugin_config.get("enabled", True),
        "api_key": api_key,
        "endpoint": plugin_config.get("endpoint", "https://api.example.com"),
    }
```

### Configuration Validation

```python
def validate_config(config: Dict[str, Any]) -> bool:
    """Validate plugin configuration."""
    if not config.get("enabled", True):
        return True

    # Check required fields
    if not config.get("api_key"):
        return False

    # Validate URL format
    endpoint = config.get("endpoint", "")
    if not endpoint.startswith(("http://", "https://")):
        return False

    return True
```

## 🧪 Testing Your Plugin

### Unit Tests

#### `tests/test_my_plugin.py`

```python
"""Tests for My MilkBottle Plugin."""

import pytest
from pathlib import Path
from my_plugin.core import MyPluginProcessor


class TestMyPluginProcessor:
    """Test MyPluginProcessor functionality."""

    def test_process_file_success(self, tmp_path):
        """Test successful file processing."""
        # Create test file
        input_file = tmp_path / "test.txt"
        input_file.write_text("hello world")

        # Process file
        processor = MyPluginProcessor()
        result = processor.process_file(str(input_file))

        # Verify results
        assert result["success"] is True
        assert result["input_file"] == str(input_file)
        assert result["content_length"] == 11

    def test_process_file_not_found(self):
        """Test file not found error."""
        processor = MyPluginProcessor()

        with pytest.raises(FileNotFoundError):
            processor.process_file("nonexistent.txt")

    def test_process_content(self):
        """Test content processing."""
        processor = MyPluginProcessor()
        result = processor._process_content("hello world")

        assert result == "HELLO WORLD"


class TestPluginInterface:
    """Test plugin interface compliance."""

    def test_get_metadata(self):
        """Test metadata function."""
        from my_plugin import get_metadata

        metadata = get_metadata()

        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert metadata["name"] == "my_plugin"

    def test_get_cli(self):
        """Test CLI function."""
        from my_plugin import get_cli

        app = get_cli()
        assert app is not None
        assert hasattr(app, "command")

    def test_validate_config(self):
        """Test configuration validation."""
        from my_plugin import validate_config

        # Valid config
        valid_config = {"enabled": True, "api_key": "test-key"}
        assert validate_config(valid_config) is True

        # Invalid config (missing API key)
        invalid_config = {"enabled": True}
        assert validate_config(invalid_config) is False
```

### Integration Tests

```python
"""Integration tests for My Plugin."""

import pytest
from typer.testing import CliRunner
from my_plugin import get_cli


class TestPluginCLI:
    """Test plugin CLI interface."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def app(self):
        """Get plugin CLI app."""
        return get_cli()

    def test_process_command(self, runner, app, tmp_path):
        """Test process command."""
        # Create test file
        input_file = tmp_path / "test.txt"
        input_file.write_text("hello world")

        # Run command
        result = runner.invoke(app, ["process", str(input_file)])

        # Verify success
        assert result.exit_code == 0
        assert "Processed" in result.stdout

    def test_status_command(self, runner, app):
        """Test status command."""
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "My Plugin Status" in result.stdout
        assert "Version" in result.stdout
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=my_plugin tests/

# Run linting
black src/
isort src/
```

## 📦 Packaging and Distribution

### Building the Package

```bash
# Build package
python -m build

# Check package
twine check dist/*
```

### Publishing to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*
```

### Local Installation

```bash
# Install in development mode
pip install -e .

# Install from local package
pip install dist/my-milkbottle-plugin-1.0.0.tar.gz
```

## 🚀 Advanced Features

### Plugin Dependencies

```python
def check_dependencies() -> Dict[str, Any]:
    """Check plugin dependencies."""
    import importlib

    dependencies = {
        "requests": "2.25.0",
        "typer": "0.9.0",
        "rich": "13.0.0",
    }

    results = {}
    for package, min_version in dependencies.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            results[package] = {
                "installed": True,
                "version": version,
                "satisfied": version >= min_version,
            }
        except ImportError:
            results[package] = {
                "installed": False,
                "version": None,
                "satisfied": False,
            }

    return results
```

### Plugin Health Monitoring

```python
def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    import time

    start_time = time.time()

    try:
        # Check dependencies
        deps = check_dependencies()

        # Test core functionality
        processor = MyPluginProcessor()
        test_result = processor.test_connection()

        # Check configuration
        config_valid = validate_config(load_plugin_config())

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "response_time": time.time() - start_time,
            "dependencies": deps,
            "configuration": config_valid,
            "test_result": test_result,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "response_time": time.time() - start_time,
            "error": str(e),
        }
```

### Plugin Metrics

```python
def get_metrics() -> Dict[str, Any]:
    """Get plugin metrics."""
    return {
        "version": "1.0.0",
        "uptime": get_uptime(),
        "requests_processed": get_request_count(),
        "errors": get_error_count(),
        "performance": {
            "avg_response_time": get_avg_response_time(),
            "success_rate": get_success_rate(),
        },
    }
```

## 📚 Best Practices

### 1. Code Organization

- Keep plugin code modular and well-structured
- Separate CLI interface from core logic
- Use type hints throughout
- Follow PEP 8 style guidelines

### 2. Error Handling

- Provide meaningful error messages
- Log errors with appropriate levels
- Handle configuration errors gracefully
- Validate inputs thoroughly

### 3. Documentation

- Write comprehensive docstrings
- Include usage examples
- Document configuration options
- Provide troubleshooting guides

### 4. Testing

- Write unit tests for all functions
- Include integration tests
- Test error conditions
- Achieve high test coverage

### 5. Configuration

- Use sensible defaults
- Validate configuration thoroughly
- Support environment variables
- Document all options

### 6. Performance

- Optimize for common use cases
- Cache expensive operations
- Use async operations when appropriate
- Monitor resource usage

### 7. Security

- Validate all inputs
- Sanitize user data
- Use secure defaults
- Follow security best practices

## 🔧 Troubleshooting

### Common Issues

#### Plugin Not Discovered

1. Check entry point registration in `pyproject.toml`
2. Verify package installation
3. Check for import errors

#### Configuration Issues

1. Validate configuration schema
2. Check environment variables
3. Verify configuration file format

#### CLI Problems

1. Ensure `get_cli()` returns a Typer app
2. Check command registration
3. Verify argument parsing

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Plugin Registry Status

Check plugin status:

```bash
milk bottle list
milk bottle status my_plugin
```

## 📖 Examples

### Complete Plugin Examples

- [PDFmilker](https://github.com/your-org/milkbottle-pdfmilker): PDF processing plugin
- [VENVmilker](https://github.com/your-org/milkbottle-venvmilker): Virtual environment management
- [Fontmilker](https://github.com/your-org/milkbottle-fontmilker): Font processing plugin

### Template Repository

Use the [MilkBottle Plugin Template](https://github.com/your-org/milkbottle-plugin-template) to get started quickly.

## 🤝 Contributing

### Plugin Development

1. Fork the MilkBottle repository
2. Create a feature branch
3. Implement your plugin
4. Add tests and documentation
5. Submit a pull request

### Community Guidelines

- Follow the code of conduct
- Write clear commit messages
- Include tests for new features
- Update documentation as needed

## 📞 Support

### Getting Help

- [Documentation](https://milkbottle.readthedocs.io/)
- [GitHub Issues](https://github.com/your-org/milkbottle/issues)
- [Discord Community](https://discord.gg/milkbottle)

### Plugin Development Support

- [Plugin Development Guide](https://milkbottle.readthedocs.io/en/latest/plugins/)
- [API Reference](https://milkbottle.readthedocs.io/en/latest/api/)
- [Examples Repository](https://github.com/your-org/milkbottle-examples)

---

**Happy Plugin Development! 🎉**

This guide covers everything you need to create powerful, reliable, and maintainable MilkBottle plugins. Start building today and contribute to the growing MilkBottle ecosystem!
