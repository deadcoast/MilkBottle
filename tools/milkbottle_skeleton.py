#!/usr/bin/env python3
"""
create_milkbottle_tree.py
-------------------------

Tiny helper that builds the **milkbottle** project scaffold exactly as shown
in the ASCII directory tree.

Usage
~~~~~
    # Create the tree in the *current* directory
    python create_milkbottle_tree.py

    # Or choose a different parent directory
    python create_milkbottle_tree.py /path/to/parent

Behaviour
~~~~~~~~~
* Skips any path that already exists—nothing is overwritten.
* Produces **empty** placeholder files so you can start filling code/tests later.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# 1. Determine where to build the scaffold
# --------------------------------------------------------------------------- #
PARENT_DIR = (
    Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()
)
ROOT = PARENT_DIR / "milkbottle"


# --------------------------------------------------------------------------- #
# 2. Explicit list of files to create (dirs are inferred automatically)
# --------------------------------------------------------------------------- #
FILES: list[str] = [
    "pyproject.toml",
    "README.md",
    "TASKLIST.md",
    "milkbottle.toml",
    "src/milkbottle/__init__.py",
    "src/milkbottle/MilkBottle.py",
    "src/milkbottle/registry.py",
    "src/milkbottle/config.py",
    "src/milkbottle/utils.py",
    "src/milkbottle/errors.py",
    "src/milkbottle/modules/__init__.py",
    "src/milkbottle/modules/pdfmilker/__init__.py",
    "src/milkbottle/modules/pdfmilker/cli.py",
    "src/milkbottle/modules/pdfmilker/discovery.py",
    "src/milkbottle/modules/pdfmilker/prepare.py",
    "src/milkbottle/modules/pdfmilker/extract.py",
    "src/milkbottle/modules/pdfmilker/transform.py",
    "src/milkbottle/modules/pdfmilker/validate.py",
    "src/milkbottle/modules/pdfmilker/relocate.py",
    "src/milkbottle/modules/pdfmilker/report.py",
    "src/milkbottle/modules/pdfmilker/utils.py",
    "src/milkbottle/modules/pdfmilker/errors.py",
    "tests/__init__.py",
    "tests/test_milkbottle_cli.py",
    "tests/test_registry.py",
    "tests/test_config.py",
    "tests/pdfmilker/test_discovery.py",
    "tests/pdfmilker/test_prepare.py",
    "tests/pdfmilker/test_extract.py",
    "tests/pdfmilker/test_transform.py",
    "tests/pdfmilker/test_validate.py",
    "tests/pdfmilker/test_relocate.py",
    "tests/pdfmilker/test_report.py",
    ".gitignore",
    ".editorconfig",
]


# --------------------------------------------------------------------------- #
# 3. Helper: create parent dirs then touch file (if absent)
# --------------------------------------------------------------------------- #
def create_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


# --------------------------------------------------------------------------- #
# 4. Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    print(f"Creating milkbottle scaffold at: {ROOT}")
    for relative in FILES:
        create_path(ROOT / relative)

    print("✅  Done – directory tree created with all placeholder files.")


if __name__ == "__main__":
    main()
