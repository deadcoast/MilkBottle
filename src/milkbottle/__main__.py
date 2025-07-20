"""Main entry point for MilkBottle Phase 5 CLI."""

import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from milkbottle.cli import cli

if __name__ == "__main__":
    cli()
