# PDFMILKER ARCHITECTURE

_A `MilkBottle` CLI Toolbox PDF Organization Module_

_Module Type • Extractor / Transformer_

---

## OVERVIEW

Status: Stand-alone (CLI menu built-in, MilkBottle integration pending)\_

- **Role** Quick-scan every `.pdf` in the working directory → convert into a structured bundle of **Markdown**, **images**, and archived **source PDF**.
- **One-Shot Flow** Discover ▶ Prepare (slugged folder) ▶ Extract ▶ Transform (MD) ▶ Validate ▶ Relocate ▶ Report.
- **CLI Snippet** `milk bottle PDFmilker`
- **Key Deps** PyMuPDF • Pillow • Typer • Rich/tqdm • python-slugify (Python 3.11)
- **Extensible** entry-point hooks, `pdfmilker.toml`, dry-run & hash deduping.

| What it Does                                                                                                                            | Key Touch-Points                                                                                                                                            | Quick CLI                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| One-shot extraction of **text**, **images**, and **metadata** from every `.pdf` in the working directory, then archives the source file | • Deterministic 7-step pipeline (Discover → Report) • Per-PDF bundle: `/markdown · /images · /pdf · /meta` • Interactive menu: start, mode toggles, options | `milk bottle PDFmilker [PATTERN] --images --overwrite --log-level quiet` |

**Core Tech** PyMuPDF · Pillow · Typer · Rich · tqdm (py 3.11)  
**Extensible**  `pdfmilker.toml` defaults, entry-point hooks, dry-run, dedupe via hash

---

## 1. Scope Clarification

- **Primary goal**: deterministic, one-shot extraction of _text_, _images_, and _metadata_ from every `.pdf` in the working directory, then atomic relocation of the source file. The first step is to get the script running without integration to the `MilkBottle` CLI Menu ecosystem yet.
- **PLACEHOLDERS**:
  - OCR of scanned docs (recommend separate “`OCRmilker`” module), advanced NLP summarisation (can be chained later via `Textmilker`).
  - Integration into the `MilkBottle` CLI Menu System(**NOTE:** _This module must still have its own self contained interactive cli menu system_).

---

## 2. Output Directory Layout (per PDF)

```
<root>/
└─ <slug>/            (# created from sanitized filename)
   ├─ markdown/       (# .md w/ YAML front-matter + heading hierarchy)
   ├─ images/         (# extracted bitmaps, original resolution)
   ├─ pdf/            (# relocated original)
   └─ meta/           (# json side-cars, logs)
```

---

## 3. Processing Pipeline (SRP-compliant sub-functions)

| Step          | Responsibility                                 | Key Output    | Suggested Helper Libs       |
| ------------- | ---------------------------------------------- | ------------- | --------------------------- |
| **Discover**  | Enumerate valid PDFs, skip dupes via hash      | list\[path]   | `pathlib`, `hashlib`        |
| **Prepare**   | Create slugged folder tree atomically          | path structs  | `python-slugify`            |
| **Extract**   | Parse text, images, metadata                   | raw assets    | `PyMuPDF` (=fitz), `Pillow` |
| **Transform** | Build Markdown (headings, code-blocks, tables) | `doc.md`      | `markdownify`, custom       |
| **Validate**  | Confirm counts + hashes                        | report dict   | stdlib                      |
| **Relocate**  | Move original into `/pdf`                      | n/a           | `shutil`                    |
| **Report**    | Emit JSON + stdout summary                     | `report.json` | `rich` / `tqdm`             |

Each step lives in its own function/class; `main()` only orchestrates.

---

## 4. CLI Interface (Interactive Menu)

> `MilkBottle` Basics

```bash
milk bottle [OPTIONS] [PATTERN]`
```

> Loading `PDFmilker`

```
milk bottle PDFmilker
```

> Loading `PDFmilker` with a quiet log level.

```
milk bottle PDFmilker --log-level quiet
```

CLI MENU EXAMPLE FOR `PDFmilker`

```bash
"This is a Welcome Message, Make sure your pdf file are in
the same folder as the PDFmilker"
# src/modules/PDFmilker/
# ----------------------

# input an option below to continue
"[1] Start PDF Extraction Process"
	if 1
		# Select an option
		[ENTER] Default, Image and Text
		[1] TEXT only
		[2] IMAGE only
		[0] GO BACK -> PDFmilker Main Menu
"[2] Options"
	if 2
		# Select to Toggle +ON or -OFF
		[1] [+]OVERWRITE allow re-milking existing slugs
		[2] LOG LEVEL [-]info|[-]debug|[+]quiet]
		[0] GO BACK -> PDFmilker Main Menu
"[0] BACK -> MilkBottle Main Menu"
	if 0
		# PLACEHOLDER FOR RETURNING TO MilkBottle Main Toolbox CLI Menu
"[q] QUIT APPLICATION"
	if q
		# QUIT APPLICATION
```

- Set Paths

* `--outdir` custom root (default = cwd)
* `--overwrite` allow re-milking existing slugs
* `--images/--no-images` toggle image extraction
* `--log-level [info|debug|quiet]`
* `--pattern [glob|regex] filter`

---

#### 5. Dependency Set

| Category | Library                  | Rationale                     |
| -------- | ------------------------ | ----------------------------- |
| Core     | **PyMuPDF (fitz)**       | fast text & image extraction  |
| CLI      | **Rich, Typer**          | ergonomic CLI, autocompletion |
| UX       | **Rich**, **tqdm**       | colored logs, progress bars   |
| Files    | **python-slugify**       | safe folder names             |
| Images   | **Pillow**               | format conversions if needed  |
| Tests    | **pytest**, **coverage** | unit / E2E validation         |

> _Lock all versions in `pyproject.toml`; require Python 3.11._

---

#### 6. Error Handling & Logging

- Wrap each pipeline step in `try/except`; raise custom `PDFMilkerError` subclasses.
- Fail-fast per file but continue batch; summary table printed at end.
- Write structured logs to `/meta/<slug>.log` in JSONL for machine parsing.

---

#### 7. Configuration & Extensibility

- Support a `pdfmilker.toml` (searched upward) to pre-define defaults.
- Register post-processors via entry-points (`milkbottle.pdfmilker_hooks`).

---

#### 8. Testing Strategy

1. **Unit**: mock‐based tests for each SRP function.
2. **Integration**: fixture PDFs with text-only, images-only, mixed, corrupted.
3. **Regression**: golden-file comparison of generated Markdown & image counts.

---

## 9. Project Structure

- Use src-layout with `src/your_package_name/`
- Place tests in `tests/` directory parallel to `src/`
- Keep configuration in `config/` or as environment variables
- Store requirements in `requirements.txt` or `pyproject.toml`
- Place static files in `static/` directory

## 10. Code Style

- Follow Black code formatting
- Use isort for import sorting
- Follow PEP 8 naming conventions:
  - snake_case for functions and variables
  - PascalCase for classes
  - UPPER_CASE for constants
- Maximum line length of 88 characters (Black default)
- Use absolute imports over relative imports

## 11. Type Hints

- Use type hints for all function parameters and returns
- Import types from `typing` module
- Use `Optional[Type]` instead of `Type | None`
- Use `TypeVar` for generic types
- Define custom types in `types.py`
- Use `Protocol` for duck typing

## 12. Error Handling

- Create custom exception classes
- Use proper try-except blocks
- Implement proper logging
- Return proper error responses
- Handle edge cases properly
- Use proper error messages

## 13. Documentation

- Use Google-style docstrings
- Keep README.md updated
- Use proper inline comments
- Document environment setup

## 14. Development Workflow

- Use virtual environments (.venv)
- Use proper Git workflow
- Implement proper logging

## 15. Dependencies

- Use a pyproject.toml file for building.
- Pin dependency versions
- Use requirements.txt for production
- Separate dev dependencies
- Use proper package versions
- Regularly update dependencies
