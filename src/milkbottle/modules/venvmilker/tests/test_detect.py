"""Unit tests for interpreter detection helpers in utils.py."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(name="utils")
def _utils() -> ModuleType:
    """Reload utils to pick up any changes."""
    if "milkbottle.modules.venvmilker.utils" in sys.modules:
        del sys.modules["milkbottle.modules.venvmilker.utils"]
    return importlib.import_module("milkbottle.modules.venvmilker.utils")


# ---------------------------------------------------------------------------
# Interpreter discovery tests
# ---------------------------------------------------------------------------


def test_find_interpreter_default(utils: ModuleType) -> None:
    """`find_interpreter()` should use default when None is passed."""

    # Mock which to return a known path
    def mock_which(exe: str) -> str | None:
        if exe in ["python3.11", "python3", "python"]:
            return "/usr/bin/python3.11"
        return None

    with pytest.MonkeyPatch().context() as m:
        m.setattr("shutil.which", mock_which)
        result = utils.find_interpreter(None)
        assert result == Path("/usr/bin/python3.11")


def test_find_interpreter_version_spec(utils: ModuleType) -> None:
    """`find_interpreter()` should find version-specific interpreters."""

    def mock_which(exe: str) -> str | None:
        if exe == "python3.10":
            return "/usr/bin/python3.10"
        return None

    with pytest.MonkeyPatch().context() as m:
        m.setattr("shutil.which", mock_which)
        result = utils.find_interpreter("3.10")
        assert result == Path("/usr/bin/python3.10")


def test_find_interpreter_absolute_path(utils: ModuleType, tmp_path: Path) -> None:
    """`find_interpreter()` should accept absolute paths."""
    python_exe = tmp_path / "python"
    python_exe.touch()
    python_exe.chmod(0o755)  # Make executable

    result = utils.find_interpreter(str(python_exe))
    assert result == python_exe


def test_find_interpreter_absolute_path_not_found(utils: ModuleType) -> None:
    """`find_interpreter()` should raise DetectError for non-existent absolute path."""
    with pytest.raises(utils.DetectError, match="Interpreter not found"):
        utils.find_interpreter("/nonexistent/python")


def test_find_interpreter_not_found(utils: ModuleType) -> None:
    """`find_interpreter()` should raise DetectError when no interpreter found."""

    def mock_which(exe: str) -> str | None:
        return None

    with pytest.MonkeyPatch().context() as m:
        m.setattr("shutil.which", mock_which)
        with pytest.raises(utils.DetectError, match="Unable to locate"):
            utils.find_interpreter("nonexistent")


def test_find_interpreter_fallback_chain(utils: ModuleType) -> None:
    """`find_interpreter()` should try fallback chain for version specs."""

    def mock_which(exe: str) -> str | None:
        # Only the last fallback should succeed
        if exe == "python":
            return "/usr/bin/python"
        return None

    with pytest.MonkeyPatch().context() as m:
        m.setattr("shutil.which", mock_which)
        result = utils.find_interpreter("3.11")
        assert result == Path("/usr/bin/python")


# ---------------------------------------------------------------------------
# Hash function tests
# ---------------------------------------------------------------------------


def test_sha256_of_file(utils: ModuleType, tmp_path: Path) -> None:
    """`sha256_of_file()` should compute correct SHA-256 hash."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Known SHA-256 for "Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    result = utils.sha256_of_file(test_file)
    assert result == expected_hash


def test_sha256_of_file_large(utils: ModuleType, tmp_path: Path) -> None:
    """`sha256_of_file()` should handle large files with chunking."""
    test_file = tmp_path / "large.txt"
    # Create a file larger than the chunk size
    large_content = "x" * 100000
    test_file.write_text(large_content)

    result = utils.sha256_of_file(test_file)
    assert len(result) == 64  # SHA-256 hex digest length
    assert result.isalnum()  # Should be alphanumeric


# ---------------------------------------------------------------------------
# Subprocess helper tests
# ---------------------------------------------------------------------------


def test_run_subprocess_success(utils: ModuleType) -> None:
    """`run_subprocess()` should return CompletedProcess on success."""
    result = utils.run_subprocess(["echo", "hello"], capture=True)
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_run_subprocess_failure(utils: ModuleType) -> None:
    """`run_subprocess()` should raise InstallError on failure."""
    with pytest.raises(utils.InstallError, match="Command failed"):
        utils.run_subprocess(["false"], capture=True)


def test_run_subprocess_with_cwd(utils: ModuleType, tmp_path: Path) -> None:
    """`run_subprocess()` should respect cwd parameter."""
    result = utils.run_subprocess(["pwd"], cwd=tmp_path, capture=True)
    assert str(tmp_path) in result.stdout


# ---------------------------------------------------------------------------
# Misc helper tests
# ---------------------------------------------------------------------------


def test_shell_join(utils: ModuleType) -> None:
    """`shell_join()` should properly quote shell arguments."""
    result = utils.shell_join(["echo", "hello world", "with spaces"])
    assert "hello world" in result
    assert "with spaces" in result
    # Should be properly quoted
    assert '"' in result


def test_ensure_clean_dir(utils: ModuleType, tmp_path: Path) -> None:
    """`ensure_clean_dir()` should clean and recreate directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").touch()

    utils.ensure_clean_dir(test_dir)

    assert test_dir.exists()
    assert test_dir.is_dir()
    assert not (test_dir / "file.txt").exists()


def test_ensure_clean_dir_file(utils: ModuleType, tmp_path: Path) -> None:
    """`ensure_clean_dir()` should handle existing files."""
    test_file = tmp_path / "test_file"
    test_file.touch()

    utils.ensure_clean_dir(test_file)

    assert test_file.exists()
    assert test_file.is_dir()
