# MilkBottle Cheat Sheet

## Purpose

- Modular Python CLI toolbox (Typer + Rich)
- Plug-and-play "bottles" (tools) via registry/entry-points

## CLI Grammar

- `milk [GLOBAL_OPTS] bottle <BottleName|Alias> [BOTTLE_OPTS] [PATTERN]`
- Example: `milk bottle PDFmilker --log-level quiet`

## Core Components

- CLI Root: `MilkBottle.py` (Typer app, console)
- Registry: `registry.py` (discovers bottles, alias → Typer app)
- Shared Core: `config.py`, `utils.py`, `errors.py`
- Bottles: `src/milkbottle/modules/<name>/`
- Tests & Docs: `/tests/`, `README.md`, module docs

## Bottle Interface

- Must provide: `get_cli() -> typer.Typer`
- Metadata: `__alias__`, `__description__`, `__version__`
- Registered via entry-point or module

## Config Strategy

- Layered: defaults ← system/user/project toml ← CLI flags
- Example: `milkbottle.toml` with [global], [PDFmilker], [FONTmilker] sections

## Error Handling

- Module errors bubble to MilkBottleError
- Root CLI: Rich summary or trace

## Roadmap

- Plugin SDK, stable API, semantic versioning

## Docs

- `README.md`, architecture, module docs, man pages
