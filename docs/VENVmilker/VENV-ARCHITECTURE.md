# VENVmilker — Virtual‑Env Project Bootstrapper

_Module Type • Environment Manager / Project Scaffolder_

---

## OVERVIEW

Status: **design‑ready** (stand‑alone CLI to be integrated into MilkBottle later)

- **Role** Create, activate, and optionally seed a **`.venv`** folder for any
  Python project via a single command (`milk bottle venv`).
  Think of it as “PyCharm’s New Project workflow, recreated for the terminal.”
- **One‑Shot Flow** Detect project root ▶ Prompt & Options ▶ Create venv
  ▶ Activate/Shell hook ▶ Dependency install ▶ Snapshot ▶ Report.
- **CLI Snippet** `milk bottle venv [PATH] [OPTIONS]`
- **Key Deps** Typer • Rich/tqdm • python‑slugify • virtualenv (Py 3.11)
- **Extensible** entry‑point hooks, `venvmilker.toml`, dry‑run, hash dedup,
  **pre/post** scripts.

| What it Does                                                                                                | Key Touch‑Points                                                                                                                                              | Quick CLI                                               |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Build a deterministic **`.venv`** in the target directory, activate it, and optionally install starter pkgs | • Atomic folder creation • Cross‑platform (Windows & POSIX) • Interactive menu • Auto‑detect Python ⇢ pick interpreter • Shell sourcing / PowerShell activate | `milk bottle venv . --python 3.11 --install rich typer` |

---

## 1. Scope Clarification

- **Primary goal** Create/activate `.venv` with zero manual steps.
  _No_ project templating, _no_ dependency managers (Poetry/PDM) — keep SRP.
- **PLACEHOLDERS** Future module (**`TemplateMilker`**) can chain cookiecutter /
  project scaffolds; environment reproducibility (**`LockMilker`**) can pin deps.

---

## 2. Output Directory Layout

**VENV CREATION / ACTIVATION ONLY:**

```
<project_root>/
├─ .venv/                # isolated interpreter
│  └─ ...                # (managed by virtualenv / venv)
├─ requirements.lock     # optional: frozen deps snapshot
└─ .venvmilker.json      # run‑metadata (Python path, hash, date)
```

**WITH Python directory template output:**

```
<project_root>/
├─ .venv/                # isolated interpreter
│  └─ ...                # (managed by virtualenv / venv)
├── .gitignore                 # Git ignores (Python, venv, etc.)
├── pyproject.toml             # Build system, dependencies (PEP 621)
├── requirements.txt           # Optional: pip requirements fallback
├── README.md                  # Project description and usage
├── LICENSE                    # License file (MIT, Apache, etc.)
├── setup.cfg                  # Optional: tool config (pytest, flake8)
│
├── docs/                      # Documentation files
│   └── index.md
│
├── src/                       # Source code (avoids import shadowing)
│   └── project_name/          # Main package
│       ├── __init__.py
│       ├── main.py            # Entry point or CLI
│       ├── config.py          # Configuration loading
│       ├── utils.py           # Helper functions
│       └── ...                # Other modules
│
├── tests/                     # Unit and integration tests
│   ├── __init__.py
│   ├── test_main.py
│   └── ...
│
├── scripts/                   # Helper scripts (e.g., init venv)
│
├── requirements.lock          # optional: frozen deps snapshot
├── .venvmilker.json           # run‑metadata (Python path, hash, date)
├── .vscode/                   # Editor config (optional)
│   └── settings.json
│
└── .gitignore                 # Git ignores (Python, venv, etc.)
```

| Folder/File               | Purpose                                          |
| ------------------------- | ------------------------------------------------ |
| `.gitignore`              | Ignore `__pycache__`, `.venv/`, `.env`, etc.     |
| `pyproject.toml`          | Modern Python build config (replaces `setup.py`) |
| `requirements.txt`        | Legacy/fallback dependencies list                |
| `README.md`               | Overview, installation, usage instructions       |
| `LICENSE`                 | Legal usage terms                                |
| `setup.cfg`               | Linting, formatting, and pytest settings         |
| `.env.example`            | Show which environment variables are needed      |
| `.pre-commit-config.yaml` | Automate linting, formatting on commit           |
| `docs/`                   | Project documentation                            |
| `src/`                    | All Python code (avoids import conflicts)        |
| `tests/`                  | Test suite                                       |
| `scripts/`                | Utilities like your venv/project creator script  |
| `.vscode/`                | Developer convenience configs                    |

### **Example `.gitignore` (Python-focused)**

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*.so

# Virtual environments
.venv/
venv/

# Environment variables
.env

# PyInstaller
dist/
build/

# MacOS
.DS_Store
```

---

## 3. Processing Pipeline (SRP‑compliant helpers)

| Step         | Responsibility                                                                      | Key Output          | Suggested Libs              |
| ------------ | ----------------------------------------------------------------------------------- | ------------------- | --------------------------- |
| **Detect**   | Locate project root (walk up for `pyproject.toml` / `.git`)                         | `Path`              | `pathlib`                   |
| **Prompt**   | Display interactive Rich menu / parse CLI flags                                     | config dict         | `Typer` + `Rich`            |
| **Create**   | Generate `.venv` via `python -m venv` _or_ `virtualenv`                             | venv path           | std `venv` / **virtualenv** |
| **Activate** | Spawn sub‑shell sourced into env (fish / bash / zsh / PowerShell) *or* write script | shell cmd / script  | stdlib + `subprocess`       |
| **Install**  | Optional: pip‑install starter packages (`--install`)                                | pip summary         | `pip` (subprocess)          |
| **Snapshot** | Freeze deps to `requirements.lock` (`pip freeze`), hash Python exe                  | lockfile + hash str | stdlib + `hashlib`          |
| **Report**   | Pretty Rich panel summary, write `.venvmilker.json`                                 | json metadata file  | `json`, `rich`              |

---

## 4. Interactive CLI Menu

```bash
milk bottle venv

┌─ VENVmilker ─────────────────────────────────────┐
│ Target directory:  ~/code/myproj                 │
│ Python binary:     /opt/homebrew/bin/python3     │
│                                                  │
│ [1] Create & activate                            │
│ [2] Create only                                  │
│ [3] Activate existing .venv                      │
│ ------------------------------------------------ │
│ Options:                                         │
│   Interpreter  : 3.11 (detected)                 │
│   Install pkgs : rich typer (editable)           │
│   Snapshot     : [x] requirements.lock           │
│   Dry‑run      : [ ]                             │
│ ------------------------------------------------ │
│ [0] Back  |  [q] Quit                            │
└──────────────────────────────────────────────────┘
```

> **Non‑interactive mode** > `milk bottle venv . --python 3.11 --install rich typer --no-activate --quiet`

### Command‑line Flags

| Flag                         | Purpose                               |                                           |
| ---------------------------- | ------------------------------------- | ----------------------------------------- |
| `PATH`                       | Project root (default = cwd)          |                                           |
| \`--python \<ver             | path>\`                               | Pick interpreter (auto‑detect if omitted) |
| `--install pkga pkgb ...`    | Space‑separated initial packages      |                                           |
| `--no-activate / --activate` | Skip or force shell spawn             |                                           |
| `--snapshot / --no-snapshot` | Write `requirements.lock`             |                                           |
| `--dry`                      | Preview actions without touching disk |                                           |
| `--log-level`                | `info` (default) / `debug` / `quiet`  |                                           |

---

## 5. Dependency Set

| Category | Library                  | Rationale                         |
| -------- | ------------------------ | --------------------------------- |
| Core     | **virtualenv** (≥ 20.x)  | reliable, cross‑platform, fast    |
| CLI      | **Typer**                | sub‑command, autocompletion       |
| UX       | **Rich**, **tqdm**       | menus, progress bars              |
| Helpers  | **python‑slugify**       | sanitize names for metadata files |
| Tests    | **pytest**, **coverage** | unit / E2E validation             |

_All under Python 3.11; versions pinned in `pyproject.toml`._

---

## 6. Configuration & Extensibility

- **`venvmilker.toml`** (look up toward root) for defaults:

  ```toml
  [default]
  python = "3.11"
  install = ["rich", "typer"]
  snapshot = true
  ```

- **Entry‑point hooks**
  Group: `milkbottle.venvmilker_hooks`
  Signature: `def post_create(ctx: VenvContext) -> None: ...`

- **Dry‑run + hash dedupe**
  _If_ existing `.venv` hash matches requested interpreter, skip recreate.

---

## 7. Error Handling & Logging

```
VenvMilkerError (module‑specific)
    ↳ CreateError
    ↳ ActivateError
MilkBottleError (shared)  
Root CLI
    ↳ Rich traceback on --debug
```

- Write JSONL logs to `.venvmilker.<date>.log`.
- Graceful exit codes: `0` success, `1` user abort, `2` fatal.

---

## 8. Testing Strategy

1. **Unit** Mock interpreter discovery, env creation (temp dirs).
2. **Integration** Matrix: {Windows cmd, PowerShell, bash, zsh, fish}.
3. **Regression** Golden hash of `.venv/Scripts/python` path.

---

## 9. Project Structure (within MilkBottle repo)

**DIRECTORY STRUCTURE IN PLACE:**

```
src/
└─ milkbottle/
   └─ modules/
      └─ venvmilker/
         ├─ __init__.py          # metadata + get_cli()
         ├─ cli.py               # Typer app + menu
         ├─ workflow.py          # Detect/Create/Activate pipeline
         ├─ config.py            # load + merge local `.toml`
         ├─ errors.py            # VenvMilkerError hierarchy
         └─ utils.py             # shell helpers, hash fn
tests/
└─ modules/
   └─ venvmilker/
      ├─ test_detect.py
      ├─ test_create.py
      └─ ...
```

Entry‑point declaration:

```toml
[project.entry-points.'milkbottle.bottles']
venvmilker = 'milkbottle.modules.venvmilker:cli'
```

---

## 10. Quick Start and Default Commands

> **DEFAULT .venv creation and activation**

```bash
milk bottle venv
```

- Automatically creates a .venv in the project root folder and activates it

> **DEFAULT Directory Templater**

```bash
milk bottle venv --snakemake
```

- IF NO PYTHON SPECIFIED, ALWAYS DEFAULT TO 3.11
- Automatically creates and activates .venv, then creates the MilkBottle Python Directory Template (snakemake).

> Activate an already existing milk venv

```bash
milk bottle venv --activate
# ALIAS FOR ACTIVATE
milk bottle venv --a
```

## 11. Integration Touch‑Points with MilkBottle

| Needs from Core                                | Provides back                  |
| ---------------------------------------------- | ------------------------------ |
| Registry alias `VENVmilker → milk bottle venv` | Fully‑fledged Typer sub‑app    |
| Shared `config.get()`                          | Adds `[VENVmilker]` section    |
| Rich console instance                          | Uniform theming                |
| Error surface (`MilkBottleError`)              | Bubble VenvMilkerError to root |

---

## 12. Roadmap

| Version    | Target                                          | Notes                            |
| ---------- | ----------------------------------------------- | -------------------------------- |
| **v0.1.0** | Stand‑alone CLI + cross‑platform env creation   | focus on Detect/Create/Activate  |
| **v0.2.0** | Package install & snapshot                      | `--install`, `requirements.lock` |
| **v0.3.x** | Hook system, post‑create scripts                | plugin SDK                       |
| **v1.0.0** | Integrated into MilkBottle, semantic versioning | stable API                       |

---

## 13. Example Usage Recipes

> **Bootstrap new repo**

```bash
git clone https://github.com/you/coolproj
cd coolproj
milk bottle venv . --python 3.11 --install typer rich --snapshot
```

> **Re‑activate later**

```bash
milk bottle venv . --activate
```

> **Dry‑run audit**

```bash
milk bottle venv /path/to/proj --dry --log-level debug
```
