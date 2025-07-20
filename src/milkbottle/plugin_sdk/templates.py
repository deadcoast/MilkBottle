"""Plugin template system for MilkBottle Plugin SDK.

This module provides template management for creating new plugins
with predefined structures and configurations.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger("milkbottle.plugin_sdk.templates")


class PluginTemplate:
    """Plugin template management system."""

    def __init__(self, sdk_path: Path):
        """Initialize template manager.

        Args:
            sdk_path: Path to SDK directory
        """
        self.sdk_path = sdk_path
        self.templates_dir = sdk_path / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Create default templates if they don't exist
        self._create_default_templates()

    def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates.

        Returns:
            List of template information
        """
        templates = []

        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                template_info = self._load_template_info(template_dir)
                if template_info:
                    templates.append(template_info)

        return templates

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template.

        Args:
            template_name: Name of template

        Returns:
            Template information or None if not found
        """
        template_dir = self.templates_dir / template_name
        if template_dir.exists() and template_dir.is_dir():
            return self._load_template_info(template_dir)
        return None

    def create_template(
        self, template_name: str, template_path: Path, description: str = ""
    ) -> bool:
        """Create a new plugin template.

        Args:
            template_name: Name of the template
            template_path: Path to template files
            description: Template description

        Returns:
            True if creation successful, False otherwise
        """
        try:
            template_dir = self.templates_dir / template_name
            template_dir.mkdir(exist_ok=True)

            # Copy template files
            if template_path.is_dir():
                shutil.copytree(template_path, template_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(template_path, template_dir)

            # Create template info
            template_info = {
                "name": template_name,
                "description": description,
                "version": "1.0.0",
                "author": "Plugin Developer",
                "tags": ["custom"],
                "files": self._get_template_files(template_dir),
            }

            # Save template info
            info_file = template_dir / "template.yaml"
            with open(info_file, "w", encoding="utf-8") as f:
                yaml.dump(template_info, f, default_flow_style=False)

            logger.info(f"Created template: {template_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create template {template_name}: {e}")
            return False

    def render_template(
        self, template_name: str, context: Dict[str, Any], output_dir: Path
    ) -> bool:
        """Render a template with context.

        Args:
            template_name: Name of template to render
            context: Template context variables
            output_dir: Output directory

        Returns:
            True if rendering successful, False otherwise
        """
        try:
            template_dir = self.templates_dir / template_name
            if not template_dir.exists():
                logger.error(f"Template not found: {template_name}")
                return False

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Render template files
            for file_path in template_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    relative_path = file_path.relative_to(template_dir)
                    output_path = output_dir / relative_path

                    # Create parent directories
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Render file content
                    self._render_file(file_path, output_path, context)

            logger.info(f"Rendered template {template_name} to {output_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return False

    def _load_template_info(self, template_dir: Path) -> Optional[Dict[str, Any]]:
        """Load template information from directory.

        Args:
            template_dir: Template directory

        Returns:
            Template information or None if not found
        """
        info_file = template_dir / "template.yaml"
        if info_file.exists():
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info = yaml.safe_load(f)
                    info["path"] = str(template_dir)
                    info["files"] = self._get_template_files(template_dir)
                    return info
            except Exception as e:
                logger.error(f"Failed to load template info from {info_file}: {e}")

        # Fallback to basic info
        return {
            "name": template_dir.name,
            "description": f"Template: {template_dir.name}",
            "version": "1.0.0",
            "author": "Unknown",
            "tags": ["basic"],
            "path": str(template_dir),
            "files": self._get_template_files(template_dir),
        }

    def _get_template_files(self, template_dir: Path) -> List[str]:
        """Get list of files in template.

        Args:
            template_dir: Template directory

        Returns:
            List of file paths
        """
        files = []
        for file_path in template_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                relative_path = file_path.relative_to(template_dir)
                files.append(str(relative_path))
        return files

    def _render_file(
        self, input_path: Path, output_path: Path, context: Dict[str, Any]
    ) -> None:
        """Render a single file with context.

        Args:
            input_path: Input file path
            output_path: Output file path
            context: Template context
        """
        try:
            # Read input file
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if file should be processed as template
            if input_path.suffix in [".py", ".yaml", ".yml", ".json", ".md", ".txt"]:
                # Process as Jinja2 template
                template = Template(content)
                rendered_content = template.render(**context)
            else:
                # Copy as-is
                rendered_content = content

            # Write output file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)

        except Exception as e:
            logger.error(f"Failed to render file {input_path}: {e}")
            # Fallback to copying file as-is
            shutil.copy2(input_path, output_path)

    def _create_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        default_templates = {
            "basic": self._get_basic_template(),
            "cli": self._get_cli_template(),
            "web": self._get_web_template(),
            "api": self._get_api_template(),
        }

        for template_name, template_data in default_templates.items():
            template_dir = self.templates_dir / template_name
            if not template_dir.exists():
                self._create_template_from_data(template_name, template_data)

    def _create_template_from_data(
        self, template_name: str, template_data: Dict[str, Any]
    ) -> None:
        """Create template from data structure.

        Args:
            template_name: Name of template
            template_data: Template data
        """
        template_dir = self.templates_dir / template_name
        template_dir.mkdir(exist_ok=True)

        # Create template files
        for file_path, content in template_data.get("files", {}).items():
            file_path = template_dir / file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Create template info
        info = template_data.get("info", {})
        info_file = template_dir / "template.yaml"
        with open(info_file, "w", encoding="utf-8") as f:
            yaml.dump(info, f, default_flow_style=False)

    def _get_basic_template(self) -> Dict[str, Any]:
        """Get basic template data."""
        return {
            "info": {
                "name": "basic",
                "description": "Basic plugin template with minimal structure",
                "version": "1.0.0",
                "author": "MilkBottle Team",
                "tags": ["basic", "minimal"],
            },
            "files": {
                "__init__.py": """\"\"\"{{ plugin_name }} - {{ description }}\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{{ version }}"
__name__ = "{{ plugin_name }}"
__description__ = "{{ description }}"
__author__ = "{{ author }}"
__email__ = "{{ email }}"
__license__ = "{{ license }}"
__dependencies__ = {{ dependencies | tojson }}
__capabilities__ = {{ capabilities | tojson }}
__tags__ = {{ tags | tojson }}

class {{ class_name }}(PluginInterface):
    \"\"\"{{ description }}\"\"\"

    def __init__(self):
        \"\"\"Initialize the plugin.\"\"\"
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False

    def get_cli(self) -> Any:
        \"\"\"Return the CLI interface.\"\"\"
        from .cli import cli
        return cli

    def get_metadata(self) -> PluginMetadata:
        \"\"\"Return plugin metadata.\"\"\"
        return PluginMetadata(
            name=__name__,
            version=__version__,
            description=__description__,
            author=__author__,
            email=__email__,
            license=__license__,
            dependencies=__dependencies__,
            capabilities=__capabilities__,
            tags=__tags__
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        \"\"\"Validate plugin configuration.\"\"\"
        return isinstance(config, dict)

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform plugin health check.\"\"\"
        return {
            "status": "healthy" if self.initialized else "initializing",
            "details": "Plugin is functioning normally",
            "version": __version__
        }

    async def initialize(self) -> bool:
        \"\"\"Initialize the plugin.\"\"\"
        self.initialized = True
        return True

    async def shutdown(self) -> None:
        \"\"\"Shutdown the plugin.\"\"\"
        self.initialized = False

    def get_capabilities(self) -> List[str]:
        \"\"\"Return list of plugin capabilities.\"\"\"
        return __capabilities__

    def get_dependencies(self) -> List[str]:
        \"\"\"Return list of plugin dependencies.\"\"\"
        return __dependencies__

    def get_config_schema(self) -> Dict[str, Any]:
        \"\"\"Return configuration schema.\"\"\"
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        \"\"\"Return performance metrics.\"\"\"
        return {
            "score": 1.0,
            "response_time": 0.001,
            "memory_usage": 0.1
        }

    def get_error_log(self) -> List[Dict[str, Any]]:
        \"\"\"Return error log.\"\"\"
        return []

# Plugin instance
plugin_instance = {{ class_name }}()

# Required exports
def get_plugin_interface() -> PluginInterface:
    \"\"\"Get plugin interface.\"\"\"
    return plugin_instance

def get_cli():
    \"\"\"Get plugin CLI interface.\"\"\"
    return plugin_instance.get_cli()

def get_metadata():
    \"\"\"Get plugin metadata.\"\"\"
    return plugin_instance.get_metadata()

def validate_config(config: Dict[str, Any]) -> bool:
    \"\"\"Validate plugin configuration.\"\"\"
    return plugin_instance.validate_config(config)

def health_check() -> Dict[str, Any]:
    \"\"\"Perform plugin health check.\"\"\"
    return plugin_instance.health_check()
""",
                "cli.py": """\"\"\"CLI interface for {{ plugin_name }}.\"\"\"

import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    \"\"\"{{ description }}\"\"\"
    pass

@cli.command()
def status():
    \"\"\"Show plugin status.\"\"\"
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    console.print(f"Plugin: {metadata.name}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Status: {health['status']}")

if __name__ == "__main__":
    cli()
""",
                "README.md": """# {{ plugin_name }}

{{ description }}

## Installation

This plugin is part of the MilkBottle ecosystem.

## Usage

```bash
milk bottle {{ plugin_name }} status
```

## Configuration

No configuration required.

## Development

This plugin was created using the MilkBottle Plugin SDK.

## License

{{ license }}
""",
                "requirements.txt": """# {{ plugin_name }} dependencies
# Add your plugin dependencies here
""",
                "tests/__init__.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"
""",
                "tests/test_{{ plugin_name }}.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"

import pytest
from pathlib import Path

from {{ plugin_name }} import {{ class_name }}

class Test{{ class_name }}:
    \"\"\"Test {{ class_name }}.\"\"\"

    def test_plugin_creation(self):
        \"\"\"Test creating the plugin.\"\"\"
        plugin = {{ class_name }}()
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        \"\"\"Test plugin initialization.\"\"\"
        plugin = {{ class_name }}()
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True

    def test_health_check(self):
        \"\"\"Test health check.\"\"\"
        plugin = {{ class_name }}()
        health = plugin.health_check()
        assert "status" in health
        assert "version" in health
""",
            },
        }

    def _get_cli_template(self) -> Dict[str, Any]:
        """Get CLI template data."""
        return {
            "info": {
                "name": "cli",
                "description": "CLI-focused plugin template with Click integration",
                "version": "1.0.0",
                "author": "MilkBottle Team",
                "tags": ["cli", "click", "command-line"],
            },
            "files": {
                "__init__.py": """\"\"\"{{ plugin_name }} - {{ description }}\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{{ version }}"
__name__ = "{{ plugin_name }}"
__description__ = "{{ description }}"
__author__ = "{{ author }}"
__email__ = "{{ email }}"
__license__ = "{{ license }}"
__dependencies__ = {{ dependencies | tojson }}
__capabilities__ = {{ capabilities | tojson }}
__tags__ = {{ tags | tojson }}

class {{ class_name }}(PluginInterface):
    \"\"\"{{ description }}\"\"\"

    def __init__(self):
        \"\"\"Initialize the plugin.\"\"\"
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False

    def get_cli(self) -> Any:
        \"\"\"Return the CLI interface.\"\"\"
        from .cli import cli
        return cli

    def get_metadata(self) -> PluginMetadata:
        \"\"\"Return plugin metadata.\"\"\"
        return PluginMetadata(
            name=__name__,
            version=__version__,
            description=__description__,
            author=__author__,
            email=__email__,
            license=__license__,
            dependencies=__dependencies__,
            capabilities=__capabilities__,
            tags=__tags__
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        \"\"\"Validate plugin configuration.\"\"\"
        return isinstance(config, dict)

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform plugin health check.\"\"\"
        return {
            "status": "healthy" if self.initialized else "initializing",
            "details": "Plugin is functioning normally",
            "version": __version__
        }

    async def initialize(self) -> bool:
        \"\"\"Initialize the plugin.\"\"\"
        self.initialized = True
        return True

    async def shutdown(self) -> None:
        \"\"\"Shutdown the plugin.\"\"\"
        self.initialized = False

    def get_capabilities(self) -> List[str]:
        \"\"\"Return list of plugin capabilities.\"\"\"
        return __capabilities__

    def get_dependencies(self) -> List[str]:
        \"\"\"Return list of plugin dependencies.\"\"\"
        return __dependencies__

    def get_config_schema(self) -> Dict[str, Any]:
        \"\"\"Return configuration schema.\"\"\"
        return {
            "type": "object",
            "properties": {
                "default_option": {
                    "type": "string",
                    "description": "Default option value",
                    "default": "default"
                }
            },
            "required": []
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        \"\"\"Return performance metrics.\"\"\"
        return {
            "score": 1.0,
            "response_time": 0.001,
            "memory_usage": 0.1
        }

    def get_error_log(self) -> List[Dict[str, Any]]:
        \"\"\"Return error log.\"\"\"
        return []

# Plugin instance
plugin_instance = {{ class_name }}()

# Required exports
def get_plugin_interface() -> PluginInterface:
    \"\"\"Get plugin interface.\"\"\"
    return plugin_instance

def get_cli():
    \"\"\"Get plugin CLI interface.\"\"\"
    return plugin_instance.get_cli()

def get_metadata():
    \"\"\"Get plugin metadata.\"\"\"
    return plugin_instance.get_metadata()

def validate_config(config: Dict[str, Any]) -> bool:
    \"\"\"Validate plugin configuration.\"\"\"
    return plugin_instance.validate_config(config)

def health_check() -> Dict[str, Any]:
    \"\"\"Perform plugin health check.\"\"\"
    return plugin_instance.health_check()
""",
                "cli.py": """\"\"\"CLI interface for {{ plugin_name }}.\"\"\"

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group()
def cli():
    \"\"\"{{ description }}\"\"\"
    pass

@cli.command()
@click.option("--name", "-n", help="Name parameter")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(name: str, verbose: bool):
    \"\"\"Main command.\"\"\"
    from . import plugin_instance
    
    if verbose:
        console.print(f"Running {{ plugin_name }} with name: {name}")
    
    # Your main logic here
    result = f"Hello, {name or 'World'}!"
    
    panel = Panel(
        result,
        title="{{ plugin_name }}",
        border_style="green"
    )
    console.print(panel)

@cli.command()
def status():
    \"\"\"Show plugin status.\"\"\"
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    table = Table(title="Plugin Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Name", metadata.name)
    table.add_row("Version", metadata.version)
    table.add_row("Status", health['status'])
    table.add_row("Details", health['details'])
    
    console.print(table)

@cli.command()
def config():
    \"\"\"Show plugin configuration.\"\"\"
    from . import plugin_instance
    
    if plugin_instance.config:
        table = Table(title="Plugin Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        for key, value in plugin_instance.config.items():
            table.add_row(key, str(value))
        
        console.print(table)
    else:
        console.print("No configuration loaded")

if __name__ == "__main__":
    cli()
""",
                "README.md": """# {{ plugin_name }}

{{ description }}

## Installation

This plugin is part of the MilkBottle ecosystem.

## Usage

```bash
# Main command
milk bottle {{ plugin_name }} main --name "Your Name"

# Show status
milk bottle {{ plugin_name }} status

# Show configuration
milk bottle {{ plugin_name }} config
```

## Configuration

The plugin supports the following configuration options:

- `default_option`: Default option value (default: "default")

## Development

This plugin was created using the MilkBottle Plugin SDK CLI template.

## License

{{ license }}
""",
                "requirements.txt": """# {{ plugin_name }} dependencies
click>=8.0.0
rich>=13.0.0
""",
                "tests/__init__.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"
""",
                "tests/test_{{ plugin_name }}.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"

import pytest
from click.testing import CliRunner
from pathlib import Path

from {{ plugin_name }} import {{ class_name }}
from {{ plugin_name }}.cli import cli

class Test{{ class_name }}:
    \"\"\"Test {{ class_name }}.\"\"\"

    def test_plugin_creation(self):
        \"\"\"Test creating the plugin.\"\"\"
        plugin = {{ class_name }}()
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        \"\"\"Test plugin initialization.\"\"\"
        plugin = {{ class_name }}()
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True

    def test_health_check(self):
        \"\"\"Test health check.\"\"\"
        plugin = {{ class_name }}()
        health = plugin.health_check()
        assert "status" in health
        assert "version" in health

class TestCLI:
    \"\"\"Test CLI interface.\"\"\"

    def test_status_command(self):
        \"\"\"Test status command.\"\"\"
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_config_command(self):
        \"\"\"Test config command.\"\"\"
        runner = CliRunner()
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
""",
            },
        }

    def _get_web_template(self) -> Dict[str, Any]:
        """Get web template data."""
        return {
            "info": {
                "name": "web",
                "description": "Web-focused plugin template with HTTP server capabilities",
                "version": "1.0.0",
                "author": "MilkBottle Team",
                "tags": ["web", "http", "server"],
            },
            "files": {
                "__init__.py": """\"\"\"{{ plugin_name }} - {{ description }}\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{{ version }}"
__name__ = "{{ plugin_name }}"
__description__ = "{{ description }}"
__author__ = "{{ author }}"
__email__ = "{{ email }}"
__license__ = "{{ license }}"
__dependencies__ = {{ dependencies | tojson }}
__capabilities__ = {{ capabilities | tojson }}
__tags__ = {{ tags | tojson }}

class {{ class_name }}(PluginInterface):
    \"\"\"{{ description }}\"\"\"

    def __init__(self):
        \"\"\"Initialize the plugin.\"\"\"
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False
        self.server = None

    def get_cli(self) -> Any:
        \"\"\"Return the CLI interface.\"\"\"
        from .cli import cli
        return cli

    def get_metadata(self) -> PluginMetadata:
        \"\"\"Return plugin metadata.\"\"\"
        return PluginMetadata(
            name=__name__,
            version=__version__,
            description=__description__,
            author=__author__,
            email=__email__,
            license=__license__,
            dependencies=__dependencies__,
            capabilities=__capabilities__,
            tags=__tags__
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        \"\"\"Validate plugin configuration.\"\"\"
        required_fields = ["host", "port"]
        return all(field in config for field in required_fields)

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform plugin health check.\"\"\"
        return {
            "status": "healthy" if self.initialized else "initializing",
            "details": "Web plugin is functioning normally",
            "version": __version__,
            "server_running": self.server is not None
        }

    async def initialize(self) -> bool:
        \"\"\"Initialize the plugin.\"\"\"
        try:
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self) -> None:
        \"\"\"Shutdown the plugin.\"\"\"
        if self.server:
            # Stop server logic here
            pass
        self.initialized = False

    def get_capabilities(self) -> List[str]:
        \"\"\"Return list of plugin capabilities.\"\"\"
        return __capabilities__

    def get_dependencies(self) -> List[str]:
        \"\"\"Return list of plugin dependencies.\"\"\"
        return __dependencies__

    def get_config_schema(self) -> Dict[str, Any]:
        \"\"\"Return configuration schema.\"\"\"
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Server host",
                    "default": "localhost"
                },
                "port": {
                    "type": "integer",
                    "description": "Server port",
                    "default": 8080
                }
            },
            "required": ["host", "port"]
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        \"\"\"Return performance metrics.\"\"\"
        return {
            "score": 1.0,
            "response_time": 0.001,
            "memory_usage": 0.1
        }

    def get_error_log(self) -> List[Dict[str, Any]]:
        \"\"\"Return error log.\"\"\"
        return []

# Plugin instance
plugin_instance = {{ class_name }}()

# Required exports
def get_plugin_interface() -> PluginInterface:
    \"\"\"Get plugin interface.\"\"\"
    return plugin_instance

def get_cli():
    \"\"\"Get plugin CLI interface.\"\"\"
    return plugin_instance.get_cli()

def get_metadata():
    \"\"\"Get plugin metadata.\"\"\"
    return plugin_instance.get_metadata()

def validate_config(config: Dict[str, Any]) -> bool:
    \"\"\"Validate plugin configuration.\"\"\"
    return plugin_instance.validate_config(config)

def health_check() -> Dict[str, Any]:
    \"\"\"Perform plugin health check.\"\"\"
    return plugin_instance.health_check()
""",
                "cli.py": """\"\"\"CLI interface for {{ plugin_name }}.\"\"\"

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group()
def cli():
    \"\"\"{{ description }}\"\"\"
    pass

@cli.command()
@click.option("--host", default="localhost", help="Server host")
@click.option("--port", default=8080, help="Server port")
def serve(host: str, port: int):
    \"\"\"Start the web server.\"\"\"
    from . import plugin_instance
    
    console.print(f"Starting server on {host}:{port}")
    # Server logic would go here

@cli.command()
def status():
    \"\"\"Show plugin status.\"\"\"
    from . import plugin_instance
    
    health = plugin_instance.health_check()
    metadata = plugin_instance.get_metadata()
    
    console.print(f"Plugin: {metadata.name}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Status: {health['status']}")
    console.print(f"Server Running: {health['server_running']}")

if __name__ == "__main__":
    cli()
""",
                "README.md": """# {{ plugin_name }}

{{ description }}

## Installation

This plugin is part of the MilkBottle ecosystem.

## Usage

```bash
# Start server
milk bottle {{ plugin_name }} serve --host localhost --port 8080

# Show status
milk bottle {{ plugin_name }} status
```

## Configuration

The plugin requires the following configuration:

- `host`: Server host (default: localhost)
- `port`: Server port (default: 8080)

## Development

This plugin was created using the MilkBottle Plugin SDK web template.

## License

{{ license }}
""",
                "requirements.txt": """# {{ plugin_name }} dependencies
click>=8.0.0
rich>=13.0.0
aiohttp>=3.9.0
""",
                "tests/__init__.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"
""",
                "tests/test_{{ plugin_name }}.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"

import pytest
from {{ plugin_name }} import {{ class_name }}

class Test{{ class_name }}:
    \"\"\"Test {{ class_name }}.\"\"\"

    def test_plugin_creation(self):
        \"\"\"Test creating the plugin.\"\"\"
        plugin = {{ class_name }}()
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        \"\"\"Test plugin initialization.\"\"\"
        plugin = {{ class_name }}()
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True

    def test_config_validation(self):
        \"\"\"Test configuration validation.\"\"\"
        plugin = {{ class_name }}()
        
        # Valid config
        valid_config = {"host": "localhost", "port": 8080}
        assert plugin.validate_config(valid_config) is True
        
        # Invalid config
        invalid_config = {"host": "localhost"}
        assert plugin.validate_config(invalid_config) is False
""",
            },
        }

    def _get_api_template(self) -> Dict[str, Any]:
        """Get API template data."""
        return {
            "info": {
                "name": "api",
                "description": "API-focused plugin template with REST API capabilities",
                "version": "1.0.0",
                "author": "MilkBottle Team",
                "tags": ["api", "rest", "json"],
            },
            "files": {
                "__init__.py": """\"\"\"{{ plugin_name }} - {{ description }}\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{{ version }}"
__name__ = "{{ plugin_name }}"
__description__ = "{{ description }}"
__author__ = "{{ author }}"
__email__ = "{{ email }}"
__license__ = "{{ license }}"
__dependencies__ = {{ dependencies | tojson }}
__capabilities__ = {{ capabilities | tojson }}
__tags__ = {{ tags | tojson }}

class {{ class_name }}(PluginInterface):
    \"\"\"{{ description }}\"\"\"

    def __init__(self):
        \"\"\"Initialize the plugin.\"\"\"
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False
        self.api_routes = {}

    def get_cli(self) -> Any:
        \"\"\"Return the CLI interface.\"\"\"
        from .cli import cli
        return cli

    def get_metadata(self) -> PluginMetadata:
        \"\"\"Return plugin metadata.\"\"\"
        return PluginMetadata(
            name=__name__,
            version=__version__,
            description=__description__,
            author=__author__,
            email=__email__,
            license=__license__,
            dependencies=__dependencies__,
            capabilities=__capabilities__,
            tags=__tags__
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        \"\"\"Validate plugin configuration.\"\"\"
        required_fields = ["api_version", "base_path"]
        return all(field in config for field in required_fields)

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform plugin health check.\"\"\"
        return {
            "status": "healthy" if self.initialized else "initializing",
            "details": "API plugin is functioning normally",
            "version": __version__,
            "api_routes": len(self.api_routes)
        }

    async def initialize(self) -> bool:
        \"\"\"Initialize the plugin.\"\"\"
        try:
            # Initialize API routes
            self.api_routes = {
                "/health": self.health_check,
                "/info": self.get_metadata
            }
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self) -> None:
        \"\"\"Shutdown the plugin.\"\"\"
        self.api_routes.clear()
        self.initialized = False

    def get_capabilities(self) -> List[str]:
        \"\"\"Return list of plugin capabilities.\"\"\"
        return __capabilities__

    def get_dependencies(self) -> List[str]:
        \"\"\"Return list of plugin dependencies.\"\"\"
        return __dependencies__

    def get_config_schema(self) -> Dict[str, Any]:
        \"\"\"Return configuration schema.\"\"\"
        return {
            "type": "object",
            "properties": {
                "api_version": {
                    "type": "string",
                    "description": "API version",
                    "default": "v1"
                },
                "base_path": {
                    "type": "string",
                    "description": "API base path",
                    "default": "/api"
                }
            },
            "required": ["api_version", "base_path"]
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        \"\"\"Return performance metrics.\"\"\"
        return {
            "score": 1.0,
            "response_time": 0.001,
            "memory_usage": 0.1
        }

    def get_error_log(self) -> List[Dict[str, Any]]:
        \"\"\"Return error log.\"\"\"
        return []

# Plugin instance
plugin_instance = {{ class_name }}()

# Required exports
def get_plugin_interface() -> PluginInterface:
    \"\"\"Get plugin interface.\"\"\"
    return plugin_instance

def get_cli():
    \"\"\"Get plugin CLI interface.\"\"\"
    return plugin_instance.get_cli()

def get_metadata():
    \"\"\"Get plugin metadata.\"\"\"
    return plugin_instance.get_metadata()

def validate_config(config: Dict[str, Any]) -> bool:
    \"\"\"Validate plugin configuration.\"\"\"
    return plugin_instance.validate_config(config)

def health_check() -> Dict[str, Any]:
    \"\"\"Perform plugin health check.\"\"\"
    return plugin_instance.health_check()
""",
                "cli.py": """\"\"\"CLI interface for {{ plugin_name }}.\"\"\"

import click
import json
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    \"\"\"{{ description }}\"\"\"
    pass

@cli.command()
@click.option("--format", "-f", default="json", help="Output format")
def info(format: str):
    \"\"\"Get API information.\"\"\"
    from . import plugin_instance
    
    metadata = plugin_instance.get_metadata()
    
    if format == "json":
        console.print(json.dumps(metadata.__dict__, indent=2))
    else:
        table = Table(title="API Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        for key, value in metadata.__dict__.items():
            table.add_row(key, str(value))
        
        console.print(table)

@cli.command()
def routes():
    \"\"\"List API routes.\"\"\"
    from . import plugin_instance
    
    table = Table(title="API Routes")
    table.add_column("Route", style="cyan")
    table.add_column("Description", style="magenta")
    
    for route, handler in plugin_instance.api_routes.items():
        table.add_row(route, handler.__name__)
    
    console.print(table)

if __name__ == "__main__":
    cli()
""",
                "README.md": """# {{ plugin_name }}

{{ description }}

## Installation

This plugin is part of the MilkBottle ecosystem.

## Usage

```bash
# Get API information
milk bottle {{ plugin_name }} info

# List API routes
milk bottle {{ plugin_name }} routes
```

## Configuration

The plugin requires the following configuration:

- `api_version`: API version (default: v1)
- `base_path`: API base path (default: /api)

## Development

This plugin was created using the MilkBottle Plugin SDK API template.

## License

{{ license }}
""",
                "requirements.txt": """# {{ plugin_name }} dependencies
click>=8.0.0
rich>=13.0.0
aiohttp>=3.9.0
""",
                "tests/__init__.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"
""",
                "tests/test_{{ plugin_name }}.py": """\"\"\"Tests for {{ plugin_name }}.\"\"\"

import pytest
from {{ plugin_name }} import {{ class_name }}

class Test{{ class_name }}:
    \"\"\"Test {{ class_name }}.\"\"\"

    def test_plugin_creation(self):
        \"\"\"Test creating the plugin.\"\"\"
        plugin = {{ class_name }}()
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        \"\"\"Test plugin initialization.\"\"\"
        plugin = {{ class_name }}()
        success = await plugin.initialize()
        assert success is True
        assert plugin.initialized is True
        assert len(plugin.api_routes) > 0

    def test_config_validation(self):
        \"\"\"Test configuration validation.\"\"\"
        plugin = {{ class_name }}()
        
        # Valid config
        valid_config = {"api_version": "v1", "base_path": "/api"}
        assert plugin.validate_config(valid_config) is True
        
        # Invalid config
        invalid_config = {"api_version": "v1"}
        assert plugin.validate_config(invalid_config) is False
""",
            },
        }
