# MilkBottle Build Plan

## 1 · Architecture Snapshot

| Layer                               | Purpose                                                                               | Key Artifacts                                  |
| ----------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **CLI Root (`MilkBottle.py`)**      | Launches `milk` command, parses global flags, delegates to _bottles_                  | Typer app, Rich console                        |
| **Bottle Registry (`registry.py`)** | Discovers installed modules (entry‑points or `/modules/`), maps alias ⇒ Typer sub‑app | Dynamic import logic                           |
| **Shared Core**                     | Cross‑module helpers, config merger, base errors                                      | `config.py`, `utils.py`, `errors.py`           |
| **Built‑in Bottles**                | Self‑contained tools (start with _PDFmilker_)                                         | each lives in `src/milkbottle/modules/<name>/` |
| **Tests & Docs**                    | Quality gate, usage guides                                                            | `/tests/`, `README.md`, module pages           |

## MilkBottle Documentation Plan

_A living outline for the main “Fluid Code Toolbox” docs, harmonised with current and future bottles._

## 1 · Project Manifesto (Why MilkBottle?)

| Pillar                    | Description                                                                      |
| ------------------------- | -------------------------------------------------------------------------------- |
| **Fluidity**              | Every bottle can be plugged in, removed, or upgraded without touching core code. |
| **SRP Discipline**        | Each file/class does one thing; each bottle owns its own CLI, errors, tests.     |
| **Discover‑First UX**     | All commands begin with a single verb—`milk`—so users explore via `--help`.      |
| **No Lock‑In**            | Bottles register via entry‑points; external packages can extend at runtime.      |
| **Human‑Readable Output** | Rich‑styled CLI, YAML/JSON side‑cars, Markdown artifacts.                        |

## 2 · CLI Grammar Cheat‑Sheet

```
milk [GLOBAL_OPTS] bottle  <BottleName|Alias>  [BOTTLE_OPTS] [PATTERN]
```

| Element  | Role                                    | Example                   |
| -------- | --------------------------------------- | ------------------------- |
| `milk`   | Root Typer app (`MilkBottle.py`)        | `milk --version`          |
| `bottle` | Sub‑command group & registry gateway    | `milk bottle --list`      |
| _Alias_  | Unique bottle identifier (case‑insens)  | `PDFmilker`, `FONTmilker` |
| Pattern  | Optional glob/regex forwarded to bottle | `*.pdf`, `**/*.ttf`       |

**Global Options**
`--log-level`, `--config`, `--dry`, `--version`, `--help`

**Bottle‑Scoped Options** (defined inside each bottle’s `cli.py`)
e.g. `--images/--no-images` (PDFmilker), `--move/--copy` (FONTmilker planned)

---

### 3 · Core Components & Contracts

| Component         | File            | Contract Summary                                                                                                                                     |
| ----------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI Root**      | `MilkBottle.py` | Builds Typer app, injects Rich console, exposes `bottle` group.                                                                                      |
| **Registry**      | `registry.py`   | Discovers bottles via `importlib.metadata.entry_points(group='milkbottle.bottles')` _or_ local `/modules/`. Provides `get_bottle(alias) → TyperApp`. |
| **Config Loader** | `config.py`     | Reads layered settings: built‑in defaults ← `milkbottle.toml` ← ENV ← CLI.                                                                           |
| **Shared Errors** | `errors.py`     | `MilkBottleError` base + helpers like `UserAbort`, `BottleNotFound`.                                                                                 |
| **Shared Utils**  | `utils.py`      | Path helpers, Rich console factory, slugify wrapper.                                                                                                 |

**Bottle Interface Minimal Set**

```python
# 1. Provide Typer app
def get_cli() -> typer.Typer: ...

# 2. Expose metadata
__alias__ = "PDFmilker"
__description__ = "PDF Extractor / Transformer"
__version__ = "0.1.0"
```

Registry will import the bottle’s `get_cli()` and mount it under `milk bottle <alias>`.

---

### 4 · Module Spotlights

#### 4.1 PDFmilker (\[btl.2_PDFmilker])

_Status: In‑progress, stand‑alone CLI working_

- **Needs from MilkBottle**

  1. Registration under alias `PDFmilker` so users can call `milk bottle PDFmilker`.
  2. Access to global config (`config.get()`) for default output path.
  3. Rich console instance for consistent theming.
  4. Centralised error capture (uncaught `PDFMilkerError` bubbles to root handler).

- **Provides back**

  - Completed Typer sub‑app (`pdfmilker/cli.py`) with interactive menu.
  - Entry‑point declared in its `pyproject.toml`:

    ```toml
    [project.entry-points.'milkbottle.bottles']
    pdfmilker = 'milkbottle.modules.pdfmilker:cli'
    ```

#### 4.2 FONTmilker (\[btl.1*FONTmilker] • \_future*)

_Goal: organise font files (OTF, TTF, WOFF, TTC) into a clean hierarchy._

- **Will need**

  1. Same alias routing: `milk bottle FONTmilker`.
  2. Shared `utils.slugify()` for safe directory names.
  3. Option to call `MilkBottle` logger for progress bars.
  4. Registry support for multiple versioned bottles (allow `--dev` flag to load dev build).

- **Early Pipeline Sketch**

  1. Discover fonts (recursive).
  2. Normalise metadata via `fontTools`.
  3. Copy/Move into `/foundries/<family>/<style>/`.
  4. Generate `index.md` table of fonts.

---

### 5 · Configuration Strategy

```toml
# milkbottle.toml  (user‑editable)
[global]
outdir = "~/MilkBottleOutput"
log_level = "info"
dry = false

[PDFmilker]
images = true
overwrite = false

[FONTmilker]
move = true
formats = ["otf", "ttf", "woff", "woff2"]
```

Loading order (lowest → highest precedence):
`defaults` ← `/etc/milkbottle.toml` ← `~/.config/milkbottle.toml` ← project `milkbottle.toml` ← CLI flags.

---

### 6 · Error‑Handling Flow

```
BottleError (module‑specific)
    ↳ catches internally → writes /meta/log
MilkBottleError (shared)
    ↳ propagated to root
Root CLI
    ↳ pretty ‑‑trace flag shows stack
    ↳ default shows Rich panel summary
```

---

### 7 · Roadmap & Versioning

| Milestone  | Target                                       | Notes                             |
| ---------- | -------------------------------------------- | --------------------------------- |
| **v0.1.0** | Bottle registry + PDFmilker fully integrated | Fonts not yet                     |
| **v0.2.0** | FONTmilker MVP                               | Adds `fontTools`, symlink support |
| **v0.3.x** | Plugin SDK docs + cookiecutter template      | Encourage community bottles       |
| **v1.0.0** | Stable API freeze, semantic versioning       | Backward‑compat guar.             |

---

### 8 · Documentation Assets To Produce

- `README.md` → High‑level intro, quickstart, GIF demo.
- `docs/architecture.md` → Detailed explanation of components (this plan).
- `docs/modules/`

  - `PDFmilker.md` (already drafted)
  - `FONTmilker.md` (placeholder)

- Man‑pages auto‑generated by Typer: `docs/man/milk.1`

---

You're absolutely right! The `config` and `dry` arguments in the `milk_bottle.py` module are currently unused and need to be integrated into the functionality. Let me fix this by implementing proper configuration handling and dry-run mode support.

Read file: src/milkbottle/config.py
I see that the current config.py is specifically for VENVmilker. I need to create a more general MilkBottle configuration system. Let me check if there's a general config module or if I need to create one:

Ran tool
Let me check if there's a general MilkBottle configuration system or if I need to create one:

Ran tool
I need to create a general MilkBottle configuration system. Let me create a new general config module and integrate it with the main CLI:

Now let me integrate the configuration system into the main CLI:

I need to fix the linter error. The issue is that I'm trying to assign a config attribute to a Typer object, which doesn't support that. Let me fix this by using a different approach:

Now let me reinstall the package and test the configuration integration:

```bash
pip install -e .
```

Let me try the install command again:

```bash
pip install -e .
```

Now let's test the configuration integration:

```bash
milk main --help
```

I see the issue. The entry point is still pointing to the old `MilkBottle` module, but I renamed it to `milk_bottle`. Let me fix the entry point:

```bash
pip install -e .
```

Now let's test the CLI:

```bash
milk main --help
```

Perfect! Now let's test the dry-run functionality:

```bash
milk main --dry
```

Excellent! The dry-run functionality is working. I can see that:

1. The configuration is being loaded correctly with `dry_run: True`
2. The dry-run indicator is showing in the menu: "🔍 DRY RUN MODE - No changes will be made"
3. The configuration logging is working

Let me test the configuration display functionality:

```bash
milk main --dry --log-level debug
```

Let me test the bottle command with configuration:

```bash
milk bottle venvmilker --help
```

Let me test the bottle command directly:

```bash
milk bottle venvmilker --help
```

Let me create a simple test configuration file to test the config file functionality:

Now let's test the configuration file loading:

```bash
milk main --config test_config.toml
```

Perfect! The configuration system is working correctly. I can see that:

1. The configuration file is being loaded: `'config_file': 'test_config.toml'`
2. The bottle-specific configuration is being loaded: `'venvmilker': {'python': '3.12', 'install': ['rich', 'typer', 'pytest'], 'snapshot': False}`
3. The global settings are being loaded: `'global': {'interactive': False, 'color': True, 'verbose': True}`
4. The dry-run mode is enabled: `'dry_run': True`

Let me clean up the test file and create a summary:

Ran tool

## Summary

I have successfully integrated the `config` and `dry` arguments into the MilkBottle CLI system. Here's what was implemented:

### ✅ **Configuration System Integration**

1. **Created `milk_config.py`** - A comprehensive configuration system that:

   - Loads defaults from hardcoded values
   - Searches for `milkbottle.toml` in project directories
   - Supports custom config files via `--config` argument
   - Applies CLI overrides with proper precedence

2. **Updated `milk_bottle.py`** to:
   - Import and use the new configuration system
   - Load configuration in the `main()` function using the `config_file` and `dry` arguments
   - Display dry-run indicator in the menu when enabled
   - Implement configuration display functionality (option 2 in menu)
   - Pass configuration to bottles when available

### ✅ **Key Features Implemented**

- **Dry-run mode**: Shows "🔍 DRY RUN MODE - No changes will be made" indicator
- **Configuration file support**: Loads TOML files with `--config` argument
- **Configuration display**: Shows current settings in the interactive menu
- **Logging integration**: Configuration loading is logged with debug info
- **Bottle-specific configs**: Supports per-bottle configuration sections
- **Global settings**: Supports global configuration options

### ✅ **Usage Examples**

```bash
# Basic usage with dry-run
milk main --dry

# With custom config file
milk main --config my_config.toml

# With debug logging
milk main --log-level debug --dry

# Bottle command with configuration
milk bottle venvmilker
```

### ✅ **Configuration File Format**

The system supports TOML configuration files like:

```toml
log_level = "debug"
dry_run = true

[global]
interactive = false
color = true
verbose = true

[bottles.venvmilker]
python = "3.12"
install = ["rich", "typer", "pytest"]
snapshot = false
```

The configuration system is now fully functional and the previously unused `config` and `dry` arguments are properly integrated into the MilkBottle CLI workflow. The system follows the layered configuration approach with proper precedence: defaults < TOML < config file < CLI overrides.
