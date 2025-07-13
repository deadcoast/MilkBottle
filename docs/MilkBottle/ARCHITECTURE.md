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
