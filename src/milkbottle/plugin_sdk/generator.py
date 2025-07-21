"""Plugin SDK Generator - Generate plugins from templates."""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .templates import PluginTemplate

logger = logging.getLogger("milkbottle.plugin_sdk.generator")


class PluginGenerator:
    """Plugin generation system."""

    def __init__(self, sdk_path: Optional[Path] = None):
        self.sdk_path = sdk_path or Path(__file__).parent
        self.console = Console()
        self.template_manager = PluginTemplate(self.sdk_path)

    def generate_plugin(
        self,
        name: str,
        template: str = "basic",
        output_dir: Optional[Path] = None,
        **kwargs: Any,
    ) -> bool:
        """Generate a new plugin from template."""
        try:
            output_dir = output_dir or Path.cwd() / name

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                progress.add_task(f"Generating plugin {name}...", total=None)

                # Create output directory
                output_dir.mkdir(parents=True, exist_ok=True)

                # Get template
                template_data = self.template_manager.get_template(template)
                if not template_data:
                    self.console.print(f"❌ Template '{template}' not found")
                    return False

                if success := self._generate_structure(
                    name, template_data, output_dir, **kwargs
                ):
                    self.console.print(
                        f"✅ Successfully generated plugin: {name} (success: {success})"
                    )
                    self.console.print(f"📁 Plugin created at: {output_dir}")
                    return True
                else:
                    self.console.print(
                        f"❌ Failed to generate plugin: {name} (success: {success})"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error generating plugin {name}: {e}")
            self.console.print(f"❌ Error generating plugin: {e}")
            return False

    def _generate_structure(
        self, name: str, template_data: Dict[str, Any], output_dir: Path, **kwargs: Any
    ) -> bool:
        """Generate plugin directory structure."""
        try:
            # Create main plugin directory
            plugin_dir = output_dir / name
            plugin_dir.mkdir(exist_ok=True)

            # Generate files from template
            for file_path, content_template in template_data.get("files", {}).items():
                file_path = Path(file_path)
                full_path = plugin_dir / file_path

                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Process template content
                content = self._process_template(content_template, name, **kwargs)

                # Write file
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Copy template files
            template_dir = self.template_manager.get_template_dir(
                template_data.get("template_name", "basic")
            )
            if template_dir and template_dir.exists():
                self._copy_template_files(template_dir, plugin_dir, name, **kwargs)

            return True

        except Exception as e:
            logger.error(f"Error generating structure: {e}")
            return False

    def _process_template(self, template: str, name: str, **kwargs: Any) -> str:
        """Process template string with variables."""
        # Replace common variables
        replacements = {
            "{{ plugin_name }}": name,
            "{{ plugin_name_upper }}": name.upper(),
            "{{ plugin_name_title }}": name.replace("-", " ").title(),
            "{{ author_name }}": kwargs.get("author", "Your Name"),
            "{{ author_email }}": kwargs.get("email", "your.email@example.com"),
            "{{ description }}": kwargs.get(
                "description", f"A {name} plugin for MilkBottle"
            ),
            "{{ version }}": kwargs.get("version", "1.0.0"),
            "{{ license }}": kwargs.get("license", "MIT"),
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, str(value))

        return result

    def _copy_template_files(
        self, template_dir: Path, plugin_dir: Path, name: str, **kwargs: Any
    ) -> None:
        """Copy template files to plugin directory."""
        for item in template_dir.iterdir():
            if item.is_file():
                # Skip template files
                if item.suffix in [".template", ".tmpl"]:
                    continue

                # Copy file
                dest_path = plugin_dir / item.name
                shutil.copy2(item, dest_path)

                # Process file content if it's a text file
                if item.suffix in [".py", ".md", ".txt", ".yaml", ".yml", ".toml"]:
                    self._process_file_content(dest_path, name, **kwargs)

            elif item.is_dir():
                # Copy directory
                dest_dir = plugin_dir / item.name
                shutil.copytree(item, dest_dir, dirs_exist_ok=True)

                # Process all files in directory
                for file_path in dest_dir.rglob("*"):
                    if file_path.is_file() and file_path.suffix in [
                        ".py",
                        ".md",
                        ".txt",
                        ".yaml",
                        ".yml",
                        ".toml",
                    ]:
                        self._process_file_content(file_path, name, **kwargs)

    def _process_file_content(self, file_path: Path, name: str, **kwargs: Any) -> None:
        """Process file content to replace template variables."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Process template variables
            processed_content = self._process_template(content, name, **kwargs)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(processed_content)

        except Exception as e:
            logger.warning(f"Could not process file {file_path}: {e}")

    def package_plugin(
        self, plugin_path: Path, output_path: Optional[Path] = None
    ) -> bool:
        """Package a plugin for distribution."""
        try:
            plugin_path = Path(plugin_path)
            if not plugin_path.exists():
                self.console.print(f"❌ Plugin path does not exist: {plugin_path}")
                return False

            output_path = output_path or plugin_path.parent / f"{plugin_path.name}.zip"

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                progress.add_task("Packaging plugin...", total=None)

                # Create zip file
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in plugin_path.rglob("*"):
                        if file_path.is_file():
                            # Calculate relative path
                            arcname = file_path.relative_to(plugin_path)
                            zipf.write(file_path, arcname)

                self.console.print(f"✅ Plugin packaged: {output_path}")
                return True

        except Exception as e:
            return self._extracted_from_create_plugin_from_scratch_32(
                "Error packaging plugin: ", e, "❌ Error packaging plugin: "
            )

    def create_plugin_from_scratch(
        self, name: str, output_dir: Optional[Path] = None, **kwargs: Any
    ) -> bool:
        """Create a plugin from scratch without templates."""
        try:
            output_dir = output_dir or Path.cwd() / name
            plugin_dir = output_dir / name
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Create basic plugin structure
            files = {
                "__init__.py": self._get_init_template(name, **kwargs),
                "cli.py": self._get_cli_template(name, **kwargs),
                "config.py": self._get_config_template(name, **kwargs),
                "core.py": self._get_core_template(name, **kwargs),
                "errors.py": self._get_errors_template(name, **kwargs),
                "utils.py": self._get_utils_template(name, **kwargs),
                "requirements.txt": self._get_requirements_template(**kwargs),
                "setup.py": self._get_setup_template(name, **kwargs),
                "pyproject.toml": self._get_pyproject_template(name, **kwargs),
                "plugin.yaml": self._get_plugin_yaml_template(name, **kwargs),
                "README.md": self._get_readme_template(name, **kwargs),
            }

            # Create test directory
            test_dir = plugin_dir / "tests"
            test_dir.mkdir(exist_ok=True)

            test_files = {
                "__init__.py": "",
                "test_core.py": self._get_test_core_template(name, **kwargs),
                "test_cli.py": self._get_test_cli_template(name, **kwargs),
            }

            # Write files
            for file_path, content in files.items():
                full_path = plugin_dir / file_path
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            for file_path, content in test_files.items():
                full_path = test_dir / file_path
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            self.console.print(f"✅ Created plugin from scratch: {name}")
            return True

        except Exception as e:
            return self._extracted_from_create_plugin_from_scratch_32(
                "Error creating plugin from scratch: ",
                e,
                "❌ Error creating plugin: ",
            )

    # TODO Rename this here and in `package_plugin` and `create_plugin_from_scratch`
    def _extracted_from_create_plugin_from_scratch_32(self, arg0, e, arg2):
        logger.error(f"{arg0}{e}")
        self.console.print(f"{arg2}{e}")
        return False

    def _get_init_template(self, name: str, **kwargs: Any) -> str:
        """Get __init__.py template."""
        return f'''"""{{ plugin_name_title }} - A MilkBottle plugin."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from milkbottle.plugin_system.core import PluginInterface, PluginMetadata

# Plugin metadata
__version__ = "{kwargs.get('version', '1.0.0')}"
__name__ = "{name}"
__description__ = "{kwargs.get('description', f'A {name} plugin for MilkBottle')}"
__author__ = "{kwargs.get('author', 'Your Name')}"
__email__ = "{kwargs.get('email', 'your.email@example.com')}"
__license__ = "{kwargs.get('license', 'MIT')}"
__dependencies__ = {kwargs.get('dependencies', [])}
__capabilities__ = {kwargs.get('capabilities', [])}
__tags__ = {kwargs.get('tags', [])}

class {name.replace("-", "_").title().replace("_", "")}Plugin(PluginInterface):
    """{{ plugin_name_title }} plugin implementation."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"milkbottle.plugin.{__name__}")
        self.config: Optional[Dict[str, Any]] = None
        self.initialized = False
    
    def get_cli(self):
        """Return the CLI interface."""
        from .cli import cli
        return cli
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
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
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        try:
            self.logger.info(f"Initializing plugin {{ __name__ }}")
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {{ __name__ }}: {{ e }}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        try:
            self.logger.info(f"Shutting down plugin {{ __name__ }}")
            self.initialized = False
        except Exception as e:
            self.logger.error(f"Error during plugin shutdown {{ __name__ }}: {{ e }}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform plugin health check."""
        return {{
            "status": "healthy" if self.initialized else "initializing",
            "version": __version__,
            "dependencies_ok": True
        }}

# Plugin instance
plugin_instance = {name.replace("-", "_").title().replace("_", "")}Plugin()

# Required exports
def get_plugin_interface() -> PluginInterface:
    """Get plugin interface."""
    return plugin_instance

def get_cli():
    """Get plugin CLI interface."""
    return plugin_instance.get_cli()

def get_metadata():
    """Get plugin metadata."""
    return plugin_instance.get_metadata()
'''

    def _get_cli_template(self, name: str, **kwargs: Any) -> str:
        """Get cli.py template."""
        return '''"""CLI interface for { plugin_name_title } plugin."""

import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    """{ plugin_name_title } plugin commands."""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
def process(input_file: str, output: str):
    """Process a file using { plugin_name_title }."""
    console.print(f"Processing { input_file }...")
    # TODO: Implement processing logic
    console.print("✅ Processing completed")

@cli.command()
def status():
    """Show plugin status."""
    console.print("{ plugin_name_title } plugin is running")
    # TODO: Implement status logic

if __name__ == '__main__':
    cli()
'''

    def _get_config_template(self, name: str, **kwargs: Any) -> str:
        """Get config.py template."""
        return f'''"""Configuration management for {{ plugin_name_title }} plugin."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class {name.replace("-", "_").title().replace("_", "")}Config:
    """Configuration for {{ plugin_name_title }} plugin."""
    
    # Add your configuration options here
    option1: str = "default_value"
    option2: int = 42
    option3: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> '{name.replace("-", "_").title().replace("_", "")}Config':
        """Create config from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {{
            "option1": self.option1,
            "option2": self.option2,
            "option3": self.option3,
        }}
'''

    def _get_core_template(self, name: str, **kwargs: Any) -> str:
        """Get core.py template."""
        return f'''"""Core functionality for {{ plugin_name_title }} plugin."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(f"milkbottle.plugin.{name}.core")

class {name.replace("-", "_").title().replace("_", "")}Core:
    """Core functionality for {{ plugin_name_title }} plugin."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
    
    def process_data(self, data: Any) -> Any:
        """Process data using the plugin's core functionality."""
        self.logger.info("Processing data...")
        # TODO: Implement core processing logic
        return data
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        # TODO: Implement input validation
        return True
    
    def generate_output(self, processed_data: Any) -> Any:
        """Generate output from processed data."""
        # TODO: Implement output generation
        return processed_data
'''

    def _get_errors_template(self, name: str, **kwargs: Any) -> str:
        """Get errors.py template."""
        return f'''"""Custom error classes for {{ plugin_name_title }} plugin."""

class {name.replace("-", "_").title().replace("_", "")}Error(Exception):
    """Base error class for {{ plugin_name_title }} plugin."""
    pass

class {name.replace("-", "_").title().replace("_", "")}ConfigError({name.replace("-", "_").title().replace("_", "")}Error):
    """Configuration error."""
    pass

class {name.replace("-", "_").title().replace("_", "")}ProcessingError({name.replace("-", "_").title().replace("_", "")}Error):
    """Processing error."""
    pass

class {name.replace("-", "_").title().replace("_", "")}ValidationError({name.replace("-", "_").title().replace("_", "")}Error):
    """Validation error."""
    pass
'''

    def _get_utils_template(self, name: str, **kwargs: Any) -> str:
        """Get utils.py template."""
        return f'''"""Utility functions for {{ plugin_name_title }} plugin."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(f"milkbottle.plugin.{name}.utils")

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate plugin configuration."""
    # TODO: Implement configuration validation
    return True

def format_output(data: Any) -> str:
    """Format output data."""
    # TODO: Implement output formatting
    return str(data)

def parse_input(input_data: str) -> Any:
    """Parse input data."""
    # TODO: Implement input parsing
    return input_data
'''

    def _get_requirements_template(self, **kwargs: Any) -> str:
        """Get requirements.txt template."""
        return """# Requirements for { plugin_name_title } plugin
# Add your dependencies here

# Core dependencies
click>=8.0.0
rich>=10.0.0

# Plugin-specific dependencies
# Add your specific dependencies here
"""

    def _get_setup_template(self, name: str, **kwargs: Any) -> str:
        """Get setup.py template."""
        return f'''"""Setup script for {{ plugin_name_title }} plugin."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{name}",
    version="{kwargs.get('version', '1.0.0')}",
    author="{kwargs.get('author', 'Your Name')}",
    author_email="{kwargs.get('email', 'your.email@example.com')}",
    description="{kwargs.get('description', f'A {name} plugin for MilkBottle')}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="{kwargs.get('repository', f'https://github.com/yourusername/{name}')}",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
    ],
    entry_points={{
        "milkbottle.plugins": [
            "{name} = {name.replace('-', '_')}:get_plugin_interface",
        ],
    }},
)
'''

    def _get_pyproject_template(self, name: str, **kwargs: Any) -> str:
        """Get pyproject.toml template."""
        return f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "{kwargs.get('version', '1.0.0')}"
description = "{kwargs.get('description', f'A {name} plugin for MilkBottle')}"
readme = "README.md"
license = {{text = "{kwargs.get('license', 'MIT')}"}}
authors = [
    {{name = "{kwargs.get('author', 'Your Name')}", email = "{kwargs.get('email', 'your.email@example.com')}"}},
]
keywords = ["milkbottle", "plugin", "{name}"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.8"
dependencies = [
    "click>=8.0.0",
    "rich>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "pytest-cov>=2.0",
    "black>=21.0",
    "isort>=5.0",
    "flake8>=3.8",
]

[project.entry-points."milkbottle.plugins"]
"{name}" = "{name.replace('-', '_')}:get_plugin_interface"

[project.urls]
Homepage = "{kwargs.get('repository', f'https://github.com/yourusername/{name}')}"
Repository = "{kwargs.get('repository', f'https://github.com/yourusername/{name}')}"
Documentation = "{kwargs.get('documentation', f'https://github.com/yourusername/{name}#readme')}"

[tool.setuptools.packages.find]
where = ["."]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88
"""

    def _get_plugin_yaml_template(self, name: str, **kwargs: Any) -> str:
        """Get plugin.yaml template."""
        return f"""name: "{name}"
version: "{kwargs.get('version', '1.0.0')}"
description: "{kwargs.get('description', f'A {name} plugin for MilkBottle')}"
author: "{kwargs.get('author', 'Your Name')}"
email: "{kwargs.get('email', 'your.email@example.com')}"
license: "{kwargs.get('license', 'MIT')}"
repository: "{kwargs.get('repository', f'https://github.com/yourusername/{name}')}"
homepage: "{kwargs.get('homepage', f'https://github.com/yourusername/{name}')}"
documentation: "{kwargs.get('documentation', f'https://github.com/yourusername/{name}#readme')}"

dependencies:
  - "click>=8.0.0"
  - "rich>=10.0.0"

capabilities:
  - "data_processing"
  - "file_handling"

tags:
  - "{name}"
  - "plugin"

categories:
  - "utilities"

configuration:
  schema:
    type: object
    properties:
      option1:
        type: string
        description: "First configuration option"
        default: "default_value"
      option2:
        type: integer
        description: "Second configuration option"
        default: 42
    required:
      - option1

cli:
  commands:
    - name: "process"
      description: "Process data using the plugin"
    - name: "status"
      description: "Show plugin status"

testing:
  framework: "pytest"
  coverage: 90
  timeout: 30

security:
  permissions:
    - "file_read"
    - "file_write"
  sandbox: false
"""

    def _get_readme_template(self, name: str, **kwargs: Any) -> str:
        """Get README.md template."""
        return f"""# {{ plugin_name_title }}

{kwargs.get('description', f'A {name} plugin for MilkBottle')}

## Installation

```bash
pip install {name}
```

## Usage

```bash
# Process a file
milk bottle {name} process input.txt --output output.txt

# Show status
milk bottle {name} status
```

## Configuration

The plugin can be configured through the MilkBottle configuration file:

```toml
[{name}]
option1 = "custom_value"
option2 = 100
```

## Development

### Setup

```bash
git clone {kwargs.get('repository', f'https://github.com/yourusername/{name}')}
cd {name}
pip install -e .
```

### Testing

```bash
pytest
```

### Building

```bash
python setup.py sdist bdist_wheel
```

## License

{kwargs.get('license', 'MIT')} License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
"""

    def _get_test_core_template(self, name: str, **kwargs: Any) -> str:
        """Get test_core.py template."""
        return f'''"""Tests for {{ plugin_name_title }} core functionality."""

import pytest
from unittest.mock import Mock

from {name.replace('-', '_')}.core import {name.replace("-", "_").title().replace("_", "")}Core

class Test{name.replace("-", "_").title().replace("_", "")}Core:
    """Test core functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {{
            "option1": "test_value",
            "option2": 42,
        }}
    
    @pytest.fixture
    def core(self, config):
        """Create core instance."""
        return {name.replace("-", "_").title().replace("_", "")}Core(config)
    
    def test_process_data(self, core):
        """Test data processing."""
        test_data = "test data"
        result = core.process_data(test_data)
        assert result == test_data
    
    def test_validate_input(self, core):
        """Test input validation."""
        test_input = "valid input"
        result = core.validate_input(test_input)
        assert result is True
    
    def test_generate_output(self, core):
        """Test output generation."""
        test_data = "test data"
        result = core.generate_output(test_data)
        assert result == test_data
'''

    def _get_test_cli_template(self, name: str, **kwargs: Any) -> str:
        """Get test_cli.py template."""
        return f'''"""Tests for {{ plugin_name_title }} CLI interface."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from {name.replace('-', '_')}.cli import cli

class Test{name.replace("-", "_").title().replace("_", "")}CLI:
    """Test CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()
    
    def test_process_command(self, runner):
        """Test process command."""
        with patch('builtins.open', create=True):
            result = runner.invoke(cli, ['process', 'test.txt'])
            assert result.exit_code == 0
    
    def test_status_command(self, runner):
        """Test status command."""
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
'''
