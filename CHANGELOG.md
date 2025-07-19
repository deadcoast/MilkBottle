# Changelog — **init**.py (created)

## VENVmilker 0.0.1

- Added version metadata with graceful fallback when package isn’t installed (**version**).
- Implemented get_cli() lazy loader that returns the Typer app from venvmilker.cli without early heavy imports.
- Declared **all** to expose only **version** and get_cli.

### `cli.py` (created)

- **Added Typer application** (`app`) with callback handling both default “no‑flag” flow and advanced options.
- Implemented **default streamlined path**: `milk bottle venv` → bootstrap env with Python 3.11, snapshot ON.
- Added core flags (`--python`, `--install`, `--activate/-a`, `--snapshot/--no-snapshot`, `--dry`, `--snakemake`, `--log-level`).
- Integrated Rich `Console` for colored output and unified error handling.
- Wired to placeholders in `workflow.py` via `bootstrap_environment()` and `activate_environment()`.
- Graceful exit with code 2 on `VenvMilkerError`.

### Changelog — `errors.py` (created)

- Added **fallback‑capable hierarchy**:

  - `VenvMilkerError` (base)
  - `DetectError`, `CreateError`, `ActivateError`, `InstallError`, `SnapshotError`

- Supports stand‑alone usage (defines local `MilkBottleError` if the parent package isn’t present).

### Changelog — `utils.py` (created)

- Implemented **`find_interpreter()`** – detects user‑requested Python or falls back to default 3.11; raises `DetectError` if not found.
- Added **`sha256_of_file()`** to fingerprint interpreter binaries for hash‑dedupe.
- Provided **`run_subprocess()`** wrapper returning output & handling return codes.
- Introduced **`shell_join()`** helper to safely echo command lines for logs.

### Changelog — `config.py` (created)

- Defined **`VenvConfig` dataclass** encapsulating python version, install list, snapshot, dry‑run, and template flag.
- Implemented **`load_toml()`** that searches upward for `venvmilker.toml`.
- Added **`build_config(cli_kwargs)`** which merges defaults → TOML → CLI overrides.
- Provided **`to_json()`** method for easy serialization into `.venvmilker.json`.

### Changelog — `workflow.py` (created)

- Added **`detect_project_root()`** (walks up for `.git` or `pyproject.toml`; fallback = cwd).
- Implemented **`create_venv()`** (uses `python -m venv` or specified interpreter path).
- Added **`install_packages()`**, **`snapshot_requirements()`**, and **`write_metadata()`** helpers.
- Implemented **`bootstrap_environment()`** orchestrator:

  1. Detect root → load config
  2. Create `.venv/` (skip via hash dedupe)
  3. Optionally install pkgs & snapshot
  4. Emit Rich summary.

- Implemented **`activate_environment()`** to launch subshell (`bash`, `zsh`, `fish`, or PowerShell) already sourced into env.
- All functions raise specific errors from `errors.py` and stream logs via injected `Console`.

### Changelog — `cli.py` (upgraded to production‑ready)

- **Default command** now creates & activates a `.venv` with Python 3.11 when invoked with zero flags (`milk bottle venv`).
- Added **full option set** (`--python`, `--install`, `--activate/-a`, `--snapshot/--no-snapshot`, `--dry`, `--snakemake`, `--log-level`).
- **Interactive menu** triggers when no flags are supplied but user runs with `--interactive` or terminal is TTY; offers list‑based selection via Rich.
- Wires straight into `workflow.bootstrap_environment()` and `workflow.activate_environment()` with rich error handling.
- Provides **`--version`** option from `__init__.__version__`.
- Clean exit codes: `0` success, `2` on `VenvMilkerError`.\n

### Changelog — `utils.py` (upgraded)

- Implemented **`find_interpreter(requested)`** – resolves absolute path from version string, full path, or default; verifies executable and caches result.
- Added **`sha256_of_file()`** and **`interp_hash()`** for dedupe logic.
- Created **`run_subprocess(cmd, *, env=None, cwd=None, capture=False)`** with rich error handling; returns output when `capture=True`.
- Added **`shell_join()`** (POSIX/Windows safe) for logging prettified commands.
- Provided **`remove_path()`** helper that handles read‑only files cross‑platform.
- Uses **`__all__`** to expose only public helpers to consumers.

### Changelog — `config.py` (upgraded to functional)

- Added **`VenvConfig` dataclass** with full field validation (`python`, `install`, `snapshot`, `dry_run`, `template`).
- Implemented **`locate_config_file(start)`** – walks up from _start_ directory for a `venvmilker.toml`.
- Implemented **`load_toml(path)`** returning dict (empty if file missing).
- Implemented **`merge_dicts(a, b)`** simple deep merge for scalar/list fields.

* Implemented **`build_config(cli_kwargs, project_root)`**:

  1. Start with defaults
  2. Merge TOML settings if present
  3. Overlay CLI arguments (skip None)
  4. Returns validated `VenvConfig`.

- Added **`to_json()`** method on `VenvConfig` for metadata serialization.
- Added **unit‑tested helper** `asdict()` for test visibility (mirrors dataclasses.asdict but ordered).

### Changelog — `tests/modules/venvmilker/test_detect.py` (created)

- Added **fixture `utils_mod`** to import `venvmilker.utils` fresh per test.
- **`test_find_interpreter_default()`** verifies that `find_interpreter(None)` returns the current interpreter.
- **`test_find_interpreter_specific_version(monkeypatch)`** patches `shutil.which` so asking for `"3.11"` returns a fake path; asserts the path is returned unchanged.
- **`test_find_interpreter_missing(monkeypatch)`** forces `which` to return `None`, expecting a `DetectError`.

Now covering interpreter resolution logic across default, positive, and error cases.

### Changelog — `__init__.py` (upgraded to final)

- Retrieves **`__version__`** via `importlib.metadata.version`; falls back to `"0.dev"` when package isn’t installed, ensuring robustness.
- Implemented **lazy `get_cli()`**:

  - Performs runtime `importlib.import_module("milkbottle.modules.venvmilker.cli")`.
  - Returns the Typer `app` object via attribute lookup (`module.app`).
  - Caches imported module in `_CLI_CACHE` to avoid repeated imports.

- Added **`__all__ = ["__version__", "get_cli"]`** for explicit exports.

### Changelog — `template.py` (created)

- Introduced **template scaffolding engine** with pluggable templates (currently **`snakemake`** only).
- **`SUPPORTED_TEMPLATES`** dict maps template name → generator function.
- Added **`scaffold_project(project_root, template, console)`** that:

  1. Confirms template is supported.
  2. Creates directory tree & writes starter files (`pyproject.toml`, `README.md`, `Snakefile`, etc.).
  3. Skips any file that already exists, emitting yellow “skip” messages via Rich.

- Internal helpers `_write_file(path, content)` and `_touch(path)` centralize filesystem writes.

Next up: wire template generation into `workflow.bootstrap_environment()` when `config.template` is not `None` and add unit test coverage.

### Changelog - cli.py

- ASCII menu layout, keys, and wording identical to your doc block.
- Editable interpreter / package list / snapshot / dry‑run each run.
- Option 3 activates existing .venv.
- 0 / q exit the menu exactly as requested.
- Flag mode is still available for automation or CI.
- Save the file, run milk bottle venv, and the menu should now appear exactly as you described.

### Changelog — test_template.py (created)

- **`test_supported_templates()`** ensures "snakemake" is registered.
- **`test_scaffold_snakemake_creates_expected_files()`** asserts core files/directories are generated.
- **`test_scaffold_is_idempotent()`** verifies second run skips existing files safely.
- **`test_unknown_template_raises()`** checks that unsupported template names raise TemplateError.

---

## PDFmilker 0.0.0

- Initial release.

## FONTmilker 0.0.0

- Initial release.
