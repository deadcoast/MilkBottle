"""Top‑level package for **VENVmilker**.

Exposes version metadata and a *lazy* `get_cli()` accessor so that importing
`venvmilker` in third‑party code does **not** pull heavy Typer/Rich deps until
absolutely necessary.
"""

from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType
from typing import Any

__all__ = ["__version__", "get_cli"]

# ------------------------------------------------------------
# Version metadata
# ------------------------------------------------------------
try:
    __version__: str = version("milkbottle-venvmilker")
except PackageNotFoundError:  # pragma: no cover – not installed
    __version__ = "0.0.0.dev0"


# ------------------------------------------------------------
# Lazy CLI accessor
# ------------------------------------------------------------


def get_cli() -> Any:  # type: ignore[valid-type, name-defined, attr-defined]
    """Return the Typer application defined in ``venvmilker.cli``.

    The import is deferred until first call to keep top‑level import cost low.
    """

    cli_module: ModuleType = importlib.import_module(
        "milkbottle.modules.venvmilker.cli"
    )
    if hasattr(cli_module, "app"):
        return cli_module.app  # type: ignore[attr-defined]
    raise RuntimeError("venvmilker.cli does not define 'app'.")
