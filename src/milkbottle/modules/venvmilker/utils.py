"""VENVmilker utility helpers – production‑ready
================================================

These helpers are imported by both workflow and CLI and MUST remain
lightweight (no Rich, no Typer) to avoid side‑effects.
"""

from __future__ import annotations

import hashlib
import shlex
import shutil
import subprocess
from pathlib import Path
from shutil import which
from typing import Sequence

from milkbottle.modules.venvmilker.errors import DetectError, InstallError

# Default Python interpreter version
DEFAULT_INTERPRETER = "3.11"

# ---------------------------------------------------------------------------
# Interpreter discovery utilities
# ---------------------------------------------------------------------------


def find_interpreter(request: str | None = None) -> Path:
    """Return a *Path* to the Python interpreter that will own the venv.

    *request* may be:
    • None  → use DEFAULT_INTERPRETER
    • "3.11"  → discover `python3.11` in PATH
    • absolute path  → verify file exists & is executable
    """
    if request is None:
        request = DEFAULT_INTERPRETER

    # Absolute path → verify directly
    p = Path(request)
    if p.is_absolute():
        if p.is_file() and p.stat().st_mode & 0o111:  # Check if executable
            return p
        raise DetectError(f"Interpreter not found or not executable at {p}")

    # Version spec → try `python3.X` then `pythonX` then fallback to `python`
    candidates: list[str] = []
    if request and request.replace(".", "").isdigit():
        major_minor = request
        candidates.extend([f"python{major_minor}", f"python{major_minor[0]}"])
    if request:
        candidates.append(request)

    for exe in candidates:
        if resolved := which(exe):
            return Path(resolved)

    raise DetectError(
        f"Unable to locate a Python interpreter matching '{request}' in PATH."
    )


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------


def sha256_of_file(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA‑256 of a file (streaming)."""
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):  # type: ignore[arg-type]
            sha.update(chunk)
    return sha.hexdigest()


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------


def run_subprocess(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Wrapper around *subprocess.run* with uniform error reporting."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=capture,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InstallError(
            f"Command failed: {shell_join(cmd)}\n{exc.stderr.strip() if exc.stderr else exc}"
        ) from exc
    return proc


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def shell_join(parts: Sequence[str]) -> str:  # pragma: no cover (python <3.8 backport)
    """Return a pretty‑printed shell command string."""

    return " ".join(shlex.quote(str(p)) for p in parts)


def ensure_clean_dir(path: Path) -> None:
    """Delete *path* if it exists then recreate it (used in tests)."""
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.mkdir(parents=True, exist_ok=True)
