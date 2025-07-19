"""VENVmilker core workflow
=================================

Handles the heavy lifting for the ``milk bottle venv`` command.

Flow (simplified)
-----------------
1. *Detect* project root.
2. *Build* and validate configuration.
3. *Create* or *reuse* a virtual environment (hash‑aware).
4. *Optionally install* packages.
5. *Optionally scaffold* a project template (Snakemake, etc.).
6. *Snapshot* dependencies.
7. *Write* run metadata and print a Rich summary.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from rich.console import Console
from rich.panel import Panel

from milkbottle.modules.venvmilker.config import VenvConfig, build_config
from milkbottle.modules.venvmilker.errors import (
    ActivateError,
    CreateError,
    InstallError,
    SnapshotError,
)
from milkbottle.modules.venvmilker.template import scaffold_project_template
from milkbottle.modules.venvmilker.utils import (
    find_interpreter,
    run_subprocess,
    sha256_of_file,
    shell_join,
)

__all__ = [
    "bootstrap_environment",
    "activate_environment",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _write_jsonl_log(root: Path, level: str, message: str, **kwargs: Any) -> None:
    """Write a JSONL log entry to .venvmilker.<date>.log."""
    log_file = root / f".venvmilker.{datetime.now().strftime('%Y%m%d')}.log"
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        **kwargs,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ---------------------------------------------------------------------------
# Detect
# ---------------------------------------------------------------------------


def detect_project_root(start: Path | None = None) -> Path:
    """Walk upward from *start* (or CWD) for a marker file, else return CWD."""
    path = (start or Path.cwd()).resolve()
    markers = {".git", "pyproject.toml"}
    return next(
        (
            parent
            for parent in [path, *path.parents]
            if any((parent / m).exists() for m in markers)
        ),
        path,
    )


# ---------------------------------------------------------------------------
# Create / install helpers
# ---------------------------------------------------------------------------


def _venv_dir(root: Path) -> Path:
    """Return the path to the virtual environment directory."""
    return root / ".venv"


def create_venv(cfg: VenvConfig, root: Path, console: Console) -> Path:
    """Create the .venv if needed; return path to python inside it."""
    venv_dir = _venv_dir(root)
    python_target = venv_dir / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )

    # If venv exists and hash matches, short‑circuit.
    meta_file = root / ".venvmilker.json"
    if python_target.exists() and meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
            if meta.get("interpreter_hash") == sha256_of_file(
                find_interpreter(cfg.python)
            ):
                console.print("[green]✓ Reusing existing .venv (hash match)")
                _write_jsonl_log(
                    root, "info", "Reusing existing .venv", hash_match=True
                )
                return python_target
        except (OSError, ValueError, json.JSONDecodeError):  # pragma: no cover
            pass  # ignore corrupt metadata; fall through to rebuild
        console.print("[yellow]ℹ Existing .venv hash mismatch – rebuilding…")
        _write_jsonl_log(root, "info", "Rebuilding .venv due to hash mismatch")
        shutil.rmtree(venv_dir, ignore_errors=True)

    # Build command
    interpreter = find_interpreter(cfg.python)
    cmd = [interpreter, "-m", "venv", str(venv_dir)]
    if cfg.dry_run:
        console.print(f"[cyan]DRY RUN » {shell_join(cmd)}")
        _write_jsonl_log(
            root, "info", "Dry run: would create venv", command=shell_join(cmd)
        )
        return python_target

    console.print(f"[blue]→ Creating virtualenv with {interpreter}")
    _write_jsonl_log(root, "info", "Creating virtualenv", interpreter=str(interpreter))

    result = run_subprocess(cmd, capture=False)
    if result.returncode != 0:
        _write_jsonl_log(
            root, "error", "Virtualenv creation failed", returncode=result.returncode
        )
        raise CreateError("venv creation failed")

    _write_jsonl_log(root, "info", "Virtualenv created successfully")
    return python_target


def install_packages(
    python_bin: Path, pkgs: Sequence[str], cfg: VenvConfig, console: Console, root: Path
) -> None:
    """Install packages into the virtual environment."""
    if not pkgs:
        return
    cmd = [str(python_bin), "-m", "pip", "install", *pkgs]
    if cfg.dry_run:
        console.print(f"[cyan]DRY RUN » {shell_join(cmd)}")
        _write_jsonl_log(
            root, "info", "Dry run: would install packages", packages=list(pkgs)
        )
        return
    console.print(f"[blue]→ Installing packages: {', '.join(pkgs)}")
    _write_jsonl_log(root, "info", "Installing packages", packages=list(pkgs))

    result = run_subprocess(cmd, capture=False)
    if result.returncode != 0:
        _write_jsonl_log(
            root, "error", "Package installation failed", returncode=result.returncode
        )
        raise InstallError("pip install failed")

    _write_jsonl_log(root, "info", "Packages installed successfully")


def snapshot_requirements(
    python_bin: Path, root: Path, cfg: VenvConfig, console: Console
) -> None:
    """Snapshot the current package requirements to requirements.lock."""
    if not cfg.snapshot:
        return
    lock_path = root / "requirements.lock"
    cmd = [str(python_bin), "-m", "pip", "freeze"]
    if cfg.dry_run:
        console.print(f"[cyan]DRY RUN » {shell_join(cmd)} > {lock_path}")
        _write_jsonl_log(root, "info", "Dry run: would snapshot requirements")
        return

    _write_jsonl_log(root, "info", "Snapshotting requirements")
    result = run_subprocess(cmd, capture=True)
    if result.returncode != 0:
        _write_jsonl_log(
            root, "error", "Requirements snapshot failed", returncode=result.returncode
        )
        raise SnapshotError("pip freeze failed")
    lock_path.write_text(result.stdout, encoding="utf-8")
    console.print(
        f"[green]✓ requirements.lock written ({lock_path.stat().st_size} bytes)"
    )
    _write_jsonl_log(
        root, "info", "Requirements snapshot completed", size=lock_path.stat().st_size
    )


# ---------------------------------------------------------------------------
# Metadata & Summary
# ---------------------------------------------------------------------------


def write_metadata(root: Path, cfg: VenvConfig, python_bin: Path) -> None:
    """Write metadata about the virtual environment to .venvmilker.json."""
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python": str(python_bin),
        "interpreter_hash": sha256_of_file(python_bin),
        "config": cfg.as_dict(),
    }
    (root / ".venvmilker.json").write_text(json.dumps(meta, indent=2))
    _write_jsonl_log(root, "info", "Metadata written", config=cfg.as_dict())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def bootstrap_environment(
    project_root: Path, cli_overrides: dict[str, object], console: Console | None = None
) -> None:
    """High‑level orchestrator used by the CLI."""
    console = console or Console()
    cfg = build_config(project_root, cli_overrides)

    _write_jsonl_log(
        project_root, "info", "VENVmilker session started", config=cfg.as_dict()
    )
    console.rule("[bold green]VENVmilker")

    # 1. venv
    python_bin = create_venv(cfg, project_root, console)

    # 2. install packages
    install_packages(python_bin, cfg.install, cfg, console, project_root)

    # 3. scaffold template (if requested)
    if cfg.template:
        console.print(f"[blue]→ Generating template '{cfg.template}'")
        _write_jsonl_log(
            project_root, "info", "Generating template", template=cfg.template
        )
        if not cfg.dry_run:
            scaffold_project_template(project_root, cfg.template, console=console)

    # 4. snapshot
    snapshot_requirements(python_bin, project_root, cfg, console)

    # 5. metadata
    if not cfg.dry_run:
        write_metadata(project_root, cfg, python_bin)

    console.print(Panel.fit("[bold green]✓ Environment ready", title="Done"))
    _write_jsonl_log(project_root, "info", "VENVmilker session completed successfully")


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------


def activate_environment(project_root: Path, console: Console | None = None) -> None:
    """Spawn a new interactive shell inside the venv."""
    console = console or Console()
    venv_dir = _venv_dir(project_root)
    if not venv_dir.exists():
        _write_jsonl_log(project_root, "error", "Cannot activate: .venv does not exist")
        raise ActivateError(".venv does not exist; cannot activate")

    if os.name == "nt":
        activate_script = venv_dir / "Scripts/activate.bat"
        shell = os.environ.get("COMSPEC", "cmd.exe")
        cmd = [str(shell), "/K", str(activate_script)]
    else:
        activate_script = venv_dir / "bin/activate"
        shell = os.environ.get("SHELL", "bash")
        cmd = [shell, "--rcfile", str(activate_script)]

    console.print(f"[blue]→ Launching shell ({shell}) – exit to return…")
    _write_jsonl_log(project_root, "info", "Activating environment", shell=shell)
    os.execvp(cmd[0], cmd)  # replace current process
