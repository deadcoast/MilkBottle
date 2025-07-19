#!/usr/bin/env python3
"""
generate_venvmilker_structure.py
--------------------------------
Create the skeleton directory tree and placeholder files for the
VENVmilker module inside a MilkBottle repository.

Usage:
    python generate_venvmilker_structure.py          # create under CWD
    python generate_venvmilker_structure.py /path/to/repo
"""

from pathlib import Path
import argparse
import sys

# Relative dirs ➟ list of files to create inside each
STRUCTURE: dict[str, list[str]] = {
    "src/milkbottle/modules/venvmilker": [
        "__init__.py",
        "cli.py",
        "workflow.py",
        "config.py",
        "errors.py",
        "utils.py",
    ],
    "tests/modules/venvmilker": [
        "test_detect.py",
        "test_create.py",
    ],
}

# Minimal starter content for stubs
PLACEHOLDER_CONTENT: dict[str, str] = {
    "__init__.py": '"""VENVmilker package init."""\n',
    "cli.py": '"""Typer CLI entry‑point stub for VENVmilker."""\n\nimport typer\n\na pp = typer.Typer(help="VENVmilker CLI")\n\n\n@a pp.callback()\ndef main() -> None:\n    """Root command."""\n    pass\n',
    "workflow.py": '"""Detect/Create/Activate pipeline (stub)."""\n',
    "config.py": '"""Load and merge `.toml` settings (stub)."""\n',
    "errors.py": '"""VENVmilker‑specific error hierarchy (stub)."""\n\nclass VenvMilkerError(Exception):\n    """Base exception for VENVmilker."""\n',
    "utils.py": '"""Shell helpers and hash utilities (stub)."""\n',
    "test_detect.py": '"""Unit tests for detection logic (stub)."""\n',
    "test_create.py": '"""Unit tests for venv creation logic (stub)."""\n',
}


def create_structure(base_path: Path) -> None:
    """Create directories and files relative to *base_path*."""
    for rel_dir, files in STRUCTURE.items():
        dir_path = base_path / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        for file_name in files:
            file_path = dir_path / file_name
            if file_path.exists():
                continue
            content = PLACEHOLDER_CONTENT.get(file_name, "pass\n")
            file_path.write_text(content)
    print(f"VENVmilker skeleton created under: {base_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="generate_venvmilker_structure",
        description="Bootstrap VENVmilker folder & stub files",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root (defaults to current directory)",
    )
    args = parser.parse_args()

    target = Path(args.path).expanduser().resolve()
    try:
        create_structure(target)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
