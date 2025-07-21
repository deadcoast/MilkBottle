"""End‑to‑end tests for `workflow.py` helpers.

These tests monkey‑patch heavy system calls (`subprocess.run`, file writes)
so they execute quickly and do not touch the real filesystem.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reload_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # noqa: ANN001
    """Reload `workflow` fresh for every test and point CWD to tmp dir."""
    root = tmp_path / "proj"
    root.mkdir()
    monkeypatch.chdir(root)

    # Ensure utils & workflow see the fake project root
    if "milkbottle.modules.venvmilker.utils" in sys.modules:
        del sys.modules["milkbottle.modules.venvmilker.utils"]
    if "milkbottle.modules.venvmilker.workflow" in sys.modules:
        del sys.modules["milkbottle.modules.venvmilker.workflow"]

    yield  # run the test


# ---------------------------------------------------------------------------
# Happy‑path create‑venv
# ---------------------------------------------------------------------------


def test_create_venv_happy_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`create_venv` should build folder, write metadata, and be idempotent."""
    wf = importlib.import_module("milkbottle.modules.venvmilker.workflow")

    # Patch subprocess.run so it doesn't call the real venv builder
    def _fake_run(cmd: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        # Simulate `python -m venv .venv` creating the folder structure
        where = Path(".venv")
        (where / ("Scripts" if os.name == "nt" else "bin")).mkdir(
            parents=True, exist_ok=True
        )
        (where / ("Scripts/python.exe" if os.name == "nt" else "bin/python")).touch()
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    # Patch interpreter hash so we can detect idempotency later
    monkeypatch.setattr(wf, "sha256_of_file", lambda _: "deadbeef")

    console = SimpleNamespace()  # dummy console
    cfg = SimpleNamespace(python="3.11", dry_run=False)
    wf.create_venv(cfg, Path.cwd(), console)

    # Verify env exists
    python_exe = Path(".venv") / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    assert python_exe.exists(), "Interpreter was not created"

    # Metadata file written
    meta = json.loads(Path(".venvmilker.json").read_text())
    assert meta["interpreter_hash"] == "deadbeef"

    # Second run should *not* invoke subprocess.run again (hash matches)
    called = False

    def _fail_run(*_: Any, **__: Any) -> None:  # pragma: no cover
        nonlocal called
        called = True

    monkeypatch.setattr(subprocess, "run", _fail_run)
    wf.create_venv(cfg, Path.cwd(), console)
    assert not called, "create_venv reran when it should be idempotent"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_create_venv_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`create_venv` should raise CreateError when subprocess fails."""
    wf = importlib.import_module("milkbottle.modules.venvmilker.workflow")

    def _fail_run(cmd: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, "", "venv creation failed")

    monkeypatch.setattr(subprocess, "run", _fail_run)

    console = SimpleNamespace()
    cfg = SimpleNamespace(python="3.11", dry_run=False)

    with pytest.raises(wf.CreateError, match="venv creation failed"):
        wf.create_venv(cfg, Path.cwd(), console)


def test_install_packages_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`install_packages` should raise InstallError when pip fails."""
    wf = importlib.import_module("milkbottle.modules.venvmilker.workflow")

    def _fail_run(cmd: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, "", "pip install failed")

    monkeypatch.setattr(subprocess, "run", _fail_run)

    console = SimpleNamespace()
    cfg = SimpleNamespace(dry_run=False)
    python_bin = Path("/fake/python")

    with pytest.raises(wf.InstallError, match="pip install failed"):
        wf.install_packages(python_bin, ["rich"], cfg, console)


# ---------------------------------------------------------------------------
# Dry‑run mode end‑to‑end
# ---------------------------------------------------------------------------


def test_bootstrap_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`bootstrap_environment` should do *nothing* when dry_run=True."""
    wf = importlib.import_module("milkbottle.modules.venvmilker.workflow")

    # Monkeypatch heavy functions to track calls
    called: dict[str, int] = {"create": 0, "install": 0, "snap": 0}

    monkeypatch.setattr(
        wf,
        "create_venv",
        lambda *_, **__: called.__setitem__("create", called["create"] + 1),
    )
    monkeypatch.setattr(
        wf,
        "install_packages",
        lambda *_, **__: called.__setitem__("install", called["install"] + 1),
    )
    monkeypatch.setattr(
        wf,
        "snapshot_requirements",
        lambda *_, **__: called.__setitem__("snap", called["snap"] + 1),
    )

    cli_overrides = {
        "python": "3.11",
        "install": [],
        "snapshot": True,
        "dry_run": True,
        "template": None,
    }
    wf.bootstrap_environment(tmp_path, cli_overrides, SimpleNamespace())

    assert all(v == 0 for v in called.values()), "Dry‑run triggered side‑effects"


# ---------------------------------------------------------------------------
# Template scaffolding
# ---------------------------------------------------------------------------


def test_template_scaffolding(tmp_path: Path) -> None:
    """Template scaffolding should create expected files."""
    from milkbottle.modules.venvmilker.template import scaffold_project_template

    project_root = tmp_path / "test_project"
    project_root.mkdir()

    scaffold_project_template(project_root, "snakemake")

    # Check that key files were created
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "README.md").exists()
    assert (project_root / ".gitignore").exists()
    assert (project_root / "Snakefile").exists()
    assert (project_root / "src" / "test_project").exists()


def test_unknown_template(tmp_path: Path) -> None:
    """Unknown templates should raise TemplateError."""
    from milkbottle.modules.venvmilker.errors import TemplateError
    from milkbottle.modules.venvmilker.template import scaffold_project_template

    project_root = tmp_path / "test_project"
    project_root.mkdir()

    with pytest.raises(TemplateError, match="Unknown template"):
        scaffold_project_template(project_root, "unknown_template")
