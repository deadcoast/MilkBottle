"""Plugin validator for MilkBottle Plugin SDK.

This module provides comprehensive validation for plugins including
structure, metadata, dependencies, and compliance checks.
"""

from __future__ import annotations

import ast
import importlib.util
import logging
from pathlib import Path
from typing import Any, Dict

from packaging import version as pkg_version
from rich.console import Console
from rich.table import Table

logger = logging.getLogger("milkbottle.plugin_sdk.validator")


class PluginValidator:
    """Plugin validation system."""

    def __init__(self):
        """Initialize the plugin validator."""
        self.console = Console()
        self.required_files = [
            "__init__.py",
            "cli.py",
            "README.md",
            "requirements.txt",
            "tests/__init__.py",
        ]
        self.required_exports = [
            "get_plugin_interface",
            "get_cli",
            "get_metadata",
            "validate_config",
            "health_check",
        ]

    def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate a plugin for compliance.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Validation results
        """
        results = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "checks": {},
            "score": 0.0,
        }

        try:
            self._extracted_from_validate_plugin_20(plugin_path, results)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            results["errors"].append(f"Validation failed: {e}")

        return results

    # TODO Rename this here and in `validate_plugin`
    def _extracted_from_validate_plugin_20(self, plugin_path, results):
        # Basic structure validation
        structure_results = self._validate_structure(plugin_path)
        results["checks"]["structure"] = structure_results

        # Metadata validation
        metadata_results = self._validate_metadata(plugin_path)
        results["checks"]["metadata"] = metadata_results

        # Code validation
        code_results = self._validate_code(plugin_path)
        results["checks"]["code"] = code_results

        # Dependencies validation
        deps_results = self._validate_dependencies(plugin_path)
        results["checks"]["dependencies"] = deps_results

        # Interface validation
        interface_results = self._validate_interface(plugin_path)
        results["checks"]["interface"] = interface_results

        # Security validation
        security_results = self._validate_security(plugin_path)
        results["checks"]["security"] = security_results

        # Calculate overall score
        results["score"] = self._calculate_score(results["checks"])
        results["valid"] = results["score"] >= 0.8  # 80% threshold

        # Collect errors and warnings
        for check_name, check_results in results["checks"].items():
            if "errors" in check_results:
                results["errors"].extend(check_results["errors"])
            if "warnings" in check_results:
                results["warnings"].extend(check_results["warnings"])

    def _validate_structure(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin structure.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Structure validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_files": [],
            "extra_files": [],
        }

        # Check required files
        for required_file in self.required_files:
            file_path = plugin_path / required_file
            if not file_path.exists():
                results["missing_files"].append(required_file)
                results["errors"].append(f"Missing required file: {required_file}")

        # Check for extra files
        all_files = [f.name for f in plugin_path.rglob("*") if f.is_file()]
        expected_files = set(self.required_files + ["tests/test_*.py", ".gitignore"])

        for file_name in all_files:
            if file_name not in expected_files and not file_name.startswith("."):
                results["extra_files"].append(file_name)
                results["warnings"].append(f"Unexpected file: {file_name}")

        results["valid"] = len(results["errors"]) == 0
        return results

    def _validate_metadata(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin metadata.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Metadata validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "metadata": {}}

        try:
            # Load plugin module
            init_file = plugin_path / "__init__.py"
            if not init_file.exists():
                results["errors"].append("No __init__.py file found")
                results["valid"] = False
                return results

            # Parse metadata from __init__.py
            metadata = self._extract_metadata(init_file)
            results["metadata"] = metadata

            # Validate required metadata fields
            required_fields = ["name", "version", "description", "author"]
            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    results["errors"].append(f"Missing required metadata: {field}")

            # Validate version format
            if "version" in metadata:
                try:
                    pkg_version.parse(metadata["version"])
                except pkg_version.InvalidVersion:
                    results["errors"].append(
                        f"Invalid version format: {metadata['version']}"
                    )

            # Validate email format if present
            if "email" in metadata and metadata["email"]:
                import re

                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, metadata["email"]):
                    results["warnings"].append(
                        f"Invalid email format: {metadata['email']}"
                    )

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Metadata validation failed: {e}")
            results["valid"] = False

        return results

    def _extract_metadata(self, init_file: Path) -> Dict[str, Any]:
        """Extract metadata from __init__.py file.

        Args:
            init_file: Path to __init__.py file

        Returns:
            Extracted metadata
        """
        metadata = {}

        try:
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse Python AST
            tree = ast.parse(content)

            # Extract assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id.startswith("__")
                            and target.id.endswith("__")
                        ):
                            # Extract string values
                            if isinstance(node.value, ast.Constant):
                                metadata[target.id[2:-2]] = node.value.value
                            elif isinstance(node.value, ast.Str):
                                metadata[target.id[2:-2]] = node.value.s
                            elif isinstance(node.value, ast.List):
                                # Handle list values (dependencies, capabilities, tags)
                                if hasattr(node.value, "elts"):
                                    metadata[target.id[2:-2]] = [
                                        (
                                            elt.value
                                            if isinstance(elt, ast.Constant)
                                            else str(elt)
                                        )
                                        for elt in node.value.elts
                                        if isinstance(elt, ast.Constant)
                                    ]

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

        return metadata

    def _validate_code(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin code quality.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Code validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "metrics": {}}

        try:
            # Analyze Python files
            py_files = list(plugin_path.rglob("*.py"))
            total_lines = 0
            total_functions = 0
            total_classes = 0

            for py_file in py_files:
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Parse AST
                    tree = ast.parse(content)

                    # Count lines
                    lines = len(content.splitlines())
                    total_lines += lines

                    # Count functions and classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1

                    # Check for docstrings
                    if not self._has_docstring(tree):
                        results["warnings"].append(
                            f"Missing docstring in {py_file.name}"
                        )

                    # Check for type hints
                    if not self._has_type_hints(tree):
                        results["warnings"].append(
                            f"Missing type hints in {py_file.name}"
                        )

                except SyntaxError as e:
                    results["errors"].append(f"Syntax error in {py_file.name}: {e}")
                except Exception as e:
                    results["warnings"].append(f"Error analyzing {py_file.name}: {e}")

            # Calculate metrics
            results["metrics"] = {
                "total_files": len(py_files),
                "total_lines": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "avg_lines_per_file": total_lines / len(py_files) if py_files else 0,
            }

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Code validation failed: {e}")
            results["valid"] = False

        return results

    def _has_docstring(self, tree: ast.Module) -> bool:
        """Check if module has docstring.

        Args:
            tree: AST tree

        Returns:
            True if has docstring, False otherwise
        """
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant):
                return True
            elif isinstance(tree.body[0].value, ast.Str):
                return True
        return False

    def _has_type_hints(self, tree: ast.AST) -> bool:
        """Check if code has type hints.

        Args:
            tree: AST tree

        Returns:
            True if has type hints, False otherwise
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns is not None:
                    return True
                for arg in node.args.args:
                    if arg.annotation is not None:
                        return True
        return False

    def _validate_dependencies(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin dependencies.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Dependencies validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "dependencies": [],
            "missing_deps": [],
        }

        try:
            # Check requirements.txt
            requirements_file = plugin_path / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, "r", encoding="utf-8") as f:
                    deps = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]

                results["dependencies"] = deps

                # Check if dependencies are available
                for dep in deps:
                    dep_name = dep.split("==")[0].split(">=")[0].split("<=")[0]
                    try:
                        importlib.import_module(dep_name)
                    except ImportError:
                        results["missing_deps"].append(dep)
                        results["warnings"].append(f"Missing dependency: {dep}")
            else:
                results["warnings"].append("No requirements.txt file found")

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Dependencies validation failed: {e}")
            results["valid"] = False

        return results

    def _validate_interface(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin interface compliance.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Interface validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_exports": [],
            "found_exports": [],
        }

        try:
            # Check __init__.py for required exports
            init_file = plugin_path / "__init__.py"
            if init_file.exists():
                with open(init_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find function definitions
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        results["found_exports"].append(node.name)

                # Check for required exports
                for export in self.required_exports:
                    if export not in results["found_exports"]:
                        results["missing_exports"].append(export)
                        results["errors"].append(f"Missing required export: {export}")

                # Check for PluginInterface implementation
                if not self._has_plugin_interface(tree):
                    results["errors"].append("No PluginInterface implementation found")

            else:
                results["errors"].append("No __init__.py file found")

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Interface validation failed: {e}")
            results["valid"] = False

        return results

    def _has_plugin_interface(self, tree: ast.AST) -> bool:
        """Check if code implements PluginInterface.

        Args:
            tree: AST tree

        Returns:
            True if implements PluginInterface, False otherwise
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from PluginInterface
                for base in node.bases:
                    if isinstance(base, ast.Name) and "PluginInterface" in base.id:
                        return True
                    elif (
                        isinstance(base, ast.Attribute)
                        and "PluginInterface" in base.attr
                    ):
                        return True
        return False

    def _validate_security(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin security.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Security validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "security_issues": []}

        try:
            # Check for dangerous imports
            dangerous_imports = [
                "os.system",
                "subprocess.call",
                "eval",
                "exec",
                "pickle",
                "marshal",
                "shelve",
            ]

            py_files = list(plugin_path.rglob("*.py"))
            for py_file in py_files:
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for dangerous imports
                    for dangerous_import in dangerous_imports:
                        if dangerous_import in content:
                            results["security_issues"].append(
                                f"Dangerous import '{dangerous_import}' in {py_file.name}"
                            )
                            results["warnings"].append(
                                f"Security warning: {dangerous_import} in {py_file.name}"
                            )

                    # Check for hardcoded secrets
                    if self._has_hardcoded_secrets(content):
                        results["security_issues"].append(
                            f"Potential hardcoded secrets in {py_file.name}"
                        )
                        results["warnings"].append(
                            f"Security warning: Hardcoded secrets in {py_file.name}"
                        )

                except Exception as e:
                    results["warnings"].append(f"Error analyzing {py_file.name}: {e}")

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Security validation failed: {e}")
            results["valid"] = False

        return results

    def _has_hardcoded_secrets(self, content: str) -> bool:
        """Check for hardcoded secrets in code.

        Args:
            content: Code content

        Returns:
            True if potential secrets found, False otherwise
        """
        import re

        # Patterns for potential secrets
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
        ]

        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)

    def _calculate_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall validation score.

        Args:
            checks: Validation check results

        Returns:
            Score between 0.0 and 1.0
        """
        if not checks:
            return 0.0

        scores = []
        weights = {
            "structure": 0.2,
            "metadata": 0.2,
            "code": 0.2,
            "dependencies": 0.1,
            "interface": 0.2,
            "security": 0.1,
        }

        for check_name, check_results in checks.items():
            if check_name in weights:
                # Calculate score for this check
                if check_results.get("valid", False):
                    score = 1.0
                else:
                    # Penalize based on errors vs warnings
                    errors = len(check_results.get("errors", []))
                    warnings = len(check_results.get("warnings", []))
                    score = max(0.0, 1.0 - (errors * 0.3) - (warnings * 0.1))

                scores.append(score * weights[check_name])

        return sum(scores) if scores else 0.0

    def print_validation_report(self, results: Dict[str, Any]) -> None:
        """Print validation report.

        Args:
            results: Validation results
        """
        # Overall status
        status_color = "green" if results["valid"] else "red"
        self.console.print(
            f"\n[bold {status_color}]Validation Status: {'PASS' if results['valid'] else 'FAIL'}[/bold {status_color}]"
        )
        self.console.print(f"Score: {results['score']:.1%}")

        # Errors
        if results["errors"]:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                self.console.print(f"  ❌ {error}")

        # Warnings
        if results["warnings"]:
            self.console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in results["warnings"]:
                self.console.print(f"  ⚠️  {warning}")

        # Detailed results
        if results["checks"]:
            self._extracted_from_print_validation_report_28(results)

    # TODO Rename this here and in `print_validation_report`
    def _extracted_from_print_validation_report_28(self, results):
        self.console.print("\n[bold blue]Detailed Results:[/bold blue]")

        table = Table()
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Score", style="green")

        for check_name, check_results in results["checks"].items():
            status = "PASS" if check_results.get("valid", False) else "FAIL"
            status_style = "green" if check_results.get("valid", False) else "red"

            # Calculate check score
            errors = len(check_results.get("errors", []))
            warnings = len(check_results.get("warnings", []))
            score = max(0.0, 1.0 - (errors * 0.3) - (warnings * 0.1))

            table.add_row(
                check_name.title(),
                f"[{status_style}]{status}[/{status_style}]",
                f"{score:.1%}",
            )

        self.console.print(table)
