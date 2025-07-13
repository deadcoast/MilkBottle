#!/usr/bin/env python3
"""
create_pdfmilker_tree.py
------------------------

Quick-start script that recreates the *pdfmilker* project scaffold exactly as
outlined in the ASCII directory tree.

Usage
~~~~~
    # Create tree inside the current directory
    python create_pdfmilker_tree.py

    # Or specify a different parent directory
    python create_pdfmilker_tree.py /path/to/parent

Notes
~~~~~
* Existing files/directories are **not** overwritten.
* All files are created empty so you can fill them in later.
"""

from __future__ import annotations

import sys
from pathlib import Path


# --------------------------------------------------------------------------- #
# 1. Choose where to create the tree
# --------------------------------------------------------------------------- #
PARENT_DIR = (
    Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()
)
ROOT = PARENT_DIR / "pdfmilker"


# --------------------------------------------------------------------------- #
# 2. Explicit list of *files* to create (directories are inferred)
# --------------------------------------------------------------------------- #
FILES: list[str] = [
    "pyproject.toml",
    "README.md",
    "scratchpad.md",
    "pdfmilker.toml",
    "src/pdfmilker/__init__.py",
    "src/pdfmilker/cli.py",
    "src/pdfmilker/discovery.py",
    "src/pdfmilker/prepare.py",
    "src/pdfmilker/extract.py",
    "src/pdfmilker/transform.py",
    "src/pdfmilker/validate.py",
    "src/pdfmilker/relocate.py",
    "src/pdfmilker/report.py",
    "src/pdfmilker/utils.py",
    "src/pdfmilker/errors.py",
    "tests/__init__.py",
    "tests/test_discovery.py",
    "tests/test_prepare.py",
    "tests/test_extract.py",
    "tests/test_transform.py",
    "tests/test_validate.py",
    "tests/test_relocate.py",
    "tests/test_report.py",
    ".gitignore",
    ".editorconfig",
]


# --------------------------------------------------------------------------- #
# 3. Helpers
# --------------------------------------------------------------------------- #
def create_path(path: Path) -> None:
    """Create parent dirs (if needed) and then an empty file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


# --------------------------------------------------------------------------- #
# 4. Main routine
# --------------------------------------------------------------------------- #
def main() -> None:
    print(f"Creating pdfmilker scaffold at: {ROOT}")
    for relative in FILES:
        create_path(ROOT / relative)

    print("✅  Done – directory tree created.")


if __name__ == "__main__":
    main()
