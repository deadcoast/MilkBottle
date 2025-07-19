# VENVmilker Cheat Sheet

## Purpose

- Create, activate, and seed `.venv` for Python projects via CLI.
- One-shot flow: Detect → Prompt → Create → Activate → Install → Snapshot → Report.

## CLI Usage

- `milk bottle venv [PATH] [OPTIONS]`
- Interactive: `milk bottle venv`
- Non-interactive: `milk bottle venv . --python 3.11 --install rich typer --no-activate --quiet`

## Key Flags

- `--python <ver|path>`: Specify Python version/path (default: 3.11)
- `--install <pkgs>`: Space-separated packages to install
- `--activate/-a`: Activate existing venv
- `--snapshot/--no-snapshot`: Write requirements.lock
- `--dry`: Preview actions, no changes
- `--log-level`: info | debug | quiet
- `--snakemake`: Scaffold Snakemake project template

## Output Structure

- `.venv/` (virtualenv)
- `requirements.lock` (optional)
- `.venvmilker.json` (metadata)

## Extensibility

- Config: `venvmilker.toml` (look up toward root)
- Entry-point hooks: `milkbottle.venvmilker_hooks`
- Dry-run & hash deduplication

## Error Handling

- Custom errors: VenvMilkerError, CreateError, ActivateError, etc.
- Logs: `.venvmilker.<date>.log`

## Project Structure

- `src/milkbottle/modules/venvmilker/`
  - `__init__.py`, `cli.py`, `workflow.py`, `config.py`, `errors.py`, `utils.py`
- Tests: `tests/modules/venvmilker/`

## Quick Recipes

- Create & activate: `milk bottle venv`
- With template: `milk bottle venv --snakemake`
- Activate only: `milk bottle venv --activate`
- Dry-run: `milk bottle venv /path/to/proj --dry --log-level debug`
