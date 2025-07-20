"""Plugin packaging system for MilkBottle Plugin SDK.

This module provides functionality to package plugins for distribution
in various formats including zip, tar.gz, and wheel.
"""

from __future__ import annotations

import importlib.util
import logging
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger("milkbottle.plugin_sdk.packaging")


class PluginPackager:
    """Plugin packaging system."""

    def __init__(self):
        """Initialize the plugin packager."""
        self.console = Console()

    def package_plugin(
        self, plugin_path: Path, output_path: Optional[Path] = None, format: str = "zip"
    ) -> bool:
        """Package a plugin for distribution.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for package
            format: Package format (zip, tar.gz, wheel)

        Returns:
            True if packaging successful, False otherwise
        """
        try:
            # Validate plugin path
            if not plugin_path.exists() or not plugin_path.is_dir():
                self.console.print(
                    f"[red]Plugin path does not exist: {plugin_path}[/red]"
                )
                return False

            # Determine output path
            if output_path is None:
                output_path = plugin_path.parent / f"{plugin_path.name}.{format}"

            # Create package based on format
            if format == "zip":
                return self._create_zip_package(plugin_path, output_path)
            elif format == "tar.gz":
                return self._create_targz_package(plugin_path, output_path)
            elif format == "wheel":
                return self._create_wheel_package(plugin_path, output_path)
            else:
                self.console.print(f"[red]Unsupported format: {format}[/red]")
                return False

        except Exception as e:
            logger.error(f"Packaging failed: {e}")
            self.console.print(f"[red]Packaging failed: {e}[/red]")
            return False

    def _create_zip_package(self, plugin_path: Path, output_path: Path) -> bool:
        """Create ZIP package.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for ZIP file

        Returns:
            True if creation successful, False otherwise
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating ZIP package...", total=None)

                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    # Add all files to ZIP
                    for file_path in plugin_path.rglob("*"):
                        if file_path.is_file():
                            # Calculate relative path
                            relative_path = file_path.relative_to(plugin_path)

                            # Skip certain files
                            if self._should_skip_file(relative_path):
                                continue

                            # Add file to ZIP
                            zipf.write(file_path, relative_path)

                progress.update(task, description="ZIP package created")

            self.console.print(f"[green]Created ZIP package: {output_path}[/green]")
            return True

        except Exception as e:
            logger.error(f"Failed to create ZIP package: {e}")
            return False

    def _create_targz_package(self, plugin_path: Path, output_path: Path) -> bool:
        """Create tar.gz package.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for tar.gz file

        Returns:
            True if creation successful, False otherwise
        """
        try:
            import tarfile

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating tar.gz package...", total=None)

                with tarfile.open(output_path, "w:gz") as tar:
                    # Add all files to tar
                    for file_path in plugin_path.rglob("*"):
                        if file_path.is_file():
                            # Calculate relative path
                            relative_path = file_path.relative_to(plugin_path)

                            # Skip certain files
                            if self._should_skip_file(relative_path):
                                continue

                            # Add file to tar
                            tar.add(file_path, arcname=relative_path)

                progress.update(task, description="tar.gz package created")

            self.console.print(f"[green]Created tar.gz package: {output_path}[/green]")
            return True

        except Exception as e:
            logger.error(f"Failed to create tar.gz package: {e}")
            return False

    def _create_wheel_package(self, plugin_path: Path, output_path: Path) -> bool:
        """Create wheel package.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for wheel file

        Returns:
            True if creation successful, False otherwise
        """
        try:
            # Check if setuptools is available
            if importlib.util.find_spec("setuptools") is None:
                self.console.print(
                    "[red]setuptools not available for wheel creation[/red]"
                )
                return False

            # Create setup.py if it doesn't exist
            setup_py = plugin_path / "setup.py"
            if not setup_py.exists():
                self._create_setup_py(plugin_path)

            # Create pyproject.toml if it doesn't exist
            pyproject_toml = plugin_path / "pyproject.toml"
            if not pyproject_toml.exists():
                self._create_pyproject_toml(plugin_path)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating wheel package...", total=None)

                # Run build command
                import subprocess
                import sys

                cmd = [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    str(output_path.parent),
                ]

                process = subprocess.run(
                    cmd, cwd=plugin_path, capture_output=True, text=True, timeout=300
                )

                progress.update(task, description="Wheel package created")

            if process.returncode == 0:
                self.console.print(
                    f"[green]Created wheel package in: {output_path.parent}[/green]"
                )
                return True
            else:
                self.console.print(
                    f"[red]Wheel creation failed: {process.stderr}[/red]"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to create wheel package: {e}")
            return False

    def _should_skip_file(self, relative_path: Path) -> bool:
        """Check if file should be skipped during packaging.

        Args:
            relative_path: Relative path of file

        Returns:
            True if file should be skipped, False otherwise
        """
        # Skip hidden files and directories
        if any(part.startswith(".") for part in relative_path.parts):
            return True

        # Skip common files to exclude
        skip_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git",
            ".gitignore",
            ".DS_Store",
            "Thumbs.db",
            "*.log",
            "*.tmp",
            "build",
            "dist",
            "*.egg-info",
        ]

        return any(pattern in str(relative_path) for pattern in skip_patterns)

    def _create_setup_py(self, plugin_path: Path) -> None:
        """Create setup.py file for wheel packaging.

        Args:
            plugin_path: Path to plugin directory
        """
        try:
            # Extract metadata from __init__.py
            metadata = self._extract_metadata(plugin_path)

            setup_content = f'''"""Setup script for {metadata.get('name', plugin_path.name)} plugin."""

from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="{metadata.get('name', plugin_path.name)}",
    version="{metadata.get('version', '1.0.0')}",
    description="{metadata.get('description', 'A MilkBottle plugin')}",
    author="{metadata.get('author', 'Plugin Developer')}",
    author_email="{metadata.get('email', 'developer@example.com')}",
    license="{metadata.get('license', 'MIT')}",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={{
        "milkbottle.plugins": [
            "{metadata.get('name', plugin_path.name)} = {metadata.get('name', plugin_path.name)}:get_plugin_interface",
        ],
    }},
)
'''

            setup_file = plugin_path / "setup.py"
            with open(setup_file, "w", encoding="utf-8") as f:
                f.write(setup_content)

        except Exception as e:
            logger.warning(f"Failed to create setup.py: {e}")

    def _create_pyproject_toml(self, plugin_path: Path) -> None:
        """Create pyproject.toml file for wheel packaging.

        Args:
            plugin_path: Path to plugin directory
        """
        try:
            # Extract metadata from __init__.py
            metadata = self._extract_metadata(plugin_path)

            pyproject_content = f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{metadata.get('name', plugin_path.name)}"
version = "{metadata.get('version', '1.0.0')}"
description = "{metadata.get('description', 'A MilkBottle plugin')}"
authors = [
    {{name = "{metadata.get('author', 'Plugin Developer')}", email = "{metadata.get('email', 'developer@example.com')}"}}
]
license = {{text = "{metadata.get('license', 'MIT')}"}}
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]

[project.entry-points."milkbottle.plugins"]
"{metadata.get('name', plugin_path.name)}" = "{metadata.get('name', plugin_path.name)}:get_plugin_interface"

[tool.setuptools.packages.find]
where = ["."]
include = ["{metadata.get('name', plugin_path.name)}*"]
"""

            pyproject_file = plugin_path / "pyproject.toml"
            with open(pyproject_file, "w", encoding="utf-8") as f:
                f.write(pyproject_content)

        except Exception as e:
            logger.warning(f"Failed to create pyproject.toml: {e}")

    def _extract_metadata(self, plugin_path: Path) -> Dict[str, Any]:
        """Extract metadata from plugin __init__.py file.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Extracted metadata
        """
        metadata = {}

        try:
            init_file = plugin_path / "__init__.py"
            if init_file.exists():
                self._extracted_from__extract_metadata_(init_file, metadata)
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

        return metadata

    # TODO Rename this here and in `_extract_metadata`
    def _extracted_from__extract_metadata_(self, init_file, metadata):
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract basic metadata
        import re

        if version_match := re.search(
            r'__version__\s*=\s*["\']([^"\']+)["\']', content
        ):
            metadata["version"] = version_match.group(1)

        if name_match := re.search(r'__name__\s*=\s*["\']([^"\']+)["\']', content):
            metadata["name"] = name_match.group(1)

        if desc_match := re.search(
            r'__description__\s*=\s*["\']([^"\']+)["\']', content
        ):
            metadata["description"] = desc_match.group(1)

        if author_match := re.search(r'__author__\s*=\s*["\']([^"\']+)["\']', content):
            metadata["author"] = author_match.group(1)

        if email_match := re.search(r'__email__\s*=\s*["\']([^"\']+)["\']', content):
            metadata["email"] = email_match.group(1)

        if license_match := re.search(
            r'__license__\s*=\s*["\']([^"\']+)["\']', content
        ):
            metadata["license"] = license_match.group(1)

    def create_manifest(
        self, plugin_path: Path, output_path: Optional[Path] = None
    ) -> bool:
        """Create manifest file for plugin.

        Args:
            plugin_path: Path to plugin directory
            output_path: Output path for manifest file

        Returns:
            True if creation successful, False otherwise
        """
        try:
            if output_path is None:
                output_path = plugin_path / "MANIFEST.in"

            # Get all files in plugin
            all_files = []
            for file_path in plugin_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(plugin_path)
                    if not self._should_skip_file(relative_path):
                        all_files.append(str(relative_path))

            manifest_content = (
                "# Plugin manifest file\n" + "# Generated by MilkBottle Plugin SDK\n\n"
            )
            # Add include statements
            for file_path in sorted(all_files):
                manifest_content += f"include {file_path}\n"

            # Write manifest file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(manifest_content)

            self.console.print(f"[green]Created manifest file: {output_path}[/green]")
            return True

        except Exception as e:
            logger.error(f"Failed to create manifest: {e}")
            return False

    def validate_package(self, package_path: Path) -> Dict[str, Any]:
        """Validate a packaged plugin.

        Args:
            package_path: Path to package file

        Returns:
            Validation results
        """
        results = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "file_size": 0,
            "file_count": 0,
        }

        try:
            if not package_path.exists():
                results["errors"].append(f"Package file does not exist: {package_path}")
                return results

            # Get file size
            results["file_size"] = package_path.stat().st_size

            # Validate based on file extension
            if package_path.suffix == ".zip":
                return self._validate_zip_package(package_path, results)
            elif package_path.suffix == ".gz" and package_path.name.endswith(".tar.gz"):
                return self._validate_targz_package(package_path, results)
            elif package_path.suffix == ".whl":
                return self._validate_wheel_package(package_path, results)
            else:
                results["errors"].append(
                    f"Unknown package format: {package_path.suffix}"
                )
                return results

        except Exception as e:
            results["errors"].append(f"Package validation failed: {e}")
            return results

    def _validate_zip_package(
        self, package_path: Path, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate ZIP package.

        Args:
            package_path: Path to ZIP package
            results: Validation results

        Returns:
            Updated validation results
        """
        try:
            with zipfile.ZipFile(package_path, "r") as zipf:
                file_list = zipf.namelist()
                self._extracted_from__validate_targz_package_16(file_list, results)
        except Exception as e:
            results["errors"].append(f"ZIP validation failed: {e}")

        return results

    def _validate_targz_package(
        self, package_path: Path, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate tar.gz package.

        Args:
            package_path: Path to tar.gz package
            results: Validation results

        Returns:
            Updated validation results
        """
        try:
            import tarfile

            with tarfile.open(package_path, "r:gz") as tar:
                file_list = tar.getnames()
                self._extracted_from__validate_targz_package_16(file_list, results)
        except Exception as e:
            results["errors"].append(f"tar.gz validation failed: {e}")

        return results

    # TODO Rename this here and in `_validate_zip_package` and `_validate_targz_package`
    def _extracted_from__validate_targz_package_16(self, file_list, results):
        results["file_count"] = len(file_list)
        required_files = ["__init__.py", "cli.py", "README.md"]
        if missing_files := [
            required_file
            for required_file in required_files
            if not any(f.endswith(required_file) for f in file_list)
        ]:
            results["errors"].append(f"Missing required files: {missing_files}")
        else:
            results["valid"] = True
        if suspicious_files := [
            file_name
            for file_name in file_list
            if any(pattern in file_name for pattern in [".pyc", "__pycache__", ".git"])
        ]:
            results["warnings"].append(f"Suspicious files found: {suspicious_files}")

    def _validate_wheel_package(
        self, package_path: Path, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate wheel package.

        Args:
            package_path: Path to wheel package
            results: Validation results

        Returns:
            Updated validation results
        """
        try:
            # Wheel packages are more complex, basic validation for now
            results["file_count"] = 1  # Single wheel file
            results["valid"] = True

            # Check wheel filename format
            wheel_name = package_path.name
            if not wheel_name.endswith(".whl"):
                results["errors"].append("Invalid wheel filename")
                results["valid"] = False

        except Exception as e:
            results["errors"].append(f"Wheel validation failed: {e}")

        return results
