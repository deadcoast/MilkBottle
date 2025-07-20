# MilkBottle 🍼 – The Fluid Code Toolbox

A **modular CLI framework** that lets you plug in task‑focused "bottles" (sub‑tools) without touching core code.  
Write once, bottle forever—whether you're batch‑extracting PDFs, organising fonts, or shipping your own milker.

---

## Table of Contents

- [MilkBottle 🍼 – The Fluid Code Toolbox](#milkbottle---the-fluid-code-toolbox)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [CLI Grammar](#cli-grammar)
  - [Built‑In Bottles](#builtin-bottles)
  - [PDFmilker Usage](#pdfmilker-usage)
    - [Basic Usage](#basic-usage)
    - [Advanced Features](#advanced-features)
    - [Output Structure](#output-structure)
    - [Processing Pipeline](#processing-pipeline)
    - [Supported Content Types](#supported-content-types)
  - [Configuration](#configuration)
    - [PDFmilker Configuration Options](#pdfmilker-configuration-options)
  - [Running Tests](#running-tests)
  - [Adding New Bottles/Plugins](#adding-new-bottlesplugins)
    - [Bottle Structure Example](#bottle-structure-example)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Debug Mode](#debug-mode)
    - [Performance Optimization](#performance-optimization)
  - [Contributing](#contributing)
    - [Development Setup](#development-setup)
  - [Task 5 — README Usage Snippet (COMPLETED)](#task5readmeusagesnippetcompleted)
    - [Hybrid Sourcery PR Workflow](#hybrid-sourcery-pr-workflow)
      - [How to use](#howto-use)
  - [Roadmap](#roadmap)
    - [Recent Updates (Phase 4.1 \& 4.2)](#recent-updates-phase-41--42)
  - [License](#license)

---

## Features

- **Single Verb UX** – everything begins with `milk`.
- **Bottle Registry** – auto‑discovers installed bottles via entry‑points or `src/milkbottle/modules/`.
- **Rich CLI** – colourised tables, progress bars, and styled tracebacks.
- **SRP by Design** – each bottle is fully self‑contained: CLI, pipeline, errors, tests.
- **Human‑Readable Artifacts** – YAML / JSON side‑cars, Markdown exports.
- **Advanced PDF Processing** – Structured text extraction, image processing, table detection, math recognition.
- **Comprehensive Testing** – 164+ tests with 90%+ coverage for core modules.
- **Enterprise-Grade Plugin System** – Complete plugin architecture with SDK, marketplace, and deployment
- **Performance Optimization** – Advanced caching, monitoring, and resource optimization
- **Deployment Management** – Multi-environment deployment with CI/CD integration

> **Suggestion:** Add a badges row here (PyPI version, build, coverage) once you publish.

---

## Installation

**Requirements:**

- Python 3.11+
- [System dependencies for PyMuPDF and Pillow](https://pymupdf.readthedocs.io/en/latest/installation.html#system-requirements) (e.g., libmupdf, libjpeg, zlib, etc.)

```bash
# Clone & install editable for local dev
git clone https://github.com/your‑user/milkbottle.git
cd milkbottle
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # pulls Rich, Typer, PyMuPDF, Pillow, PyYAML, etc.
```

> **Note:** The CLI entry point is set to `src.milkbottle.MilkBottle:main` in `pyproject.toml`. Ensure this file exists or update the entry point accordingly.

> **Suggestion:** Provide a published PyPI install command when ready (`pip install milkbottle`).

---

## Quick Start

```bash
# List available bottles
milk bottle --list

# Run the PDF extractor on all PDFs in the cwd
milk bottle PDFmilker

# Same, but quiet logs and images off
milk bottle PDFmilker --no-images --log-level quiet

# Process a specific PDF with verbose output
milk bottle PDFmilker --input document.pdf --verbose
```

## Phase 5: Enterprise Features (✅ Complete)

MilkBottle Phase 5 introduces enterprise-grade features including a comprehensive plugin system, performance optimization, and deployment management.

### Plugin SDK

```bash
# Create a new plugin from template
milkbottle sdk create my-plugin --template basic

# Validate a plugin
milkbottle sdk validate /path/to/plugin

# Test a plugin
milkbottle sdk test /path/to/plugin

# Package a plugin for distribution
milkbottle sdk package /path/to/plugin

# List available templates
milkbottle sdk templates
```

### Performance Optimization

```bash
# Start performance monitoring
milkbottle performance start-monitoring

# Show current metrics
milkbottle performance metrics

# Generate performance report
milkbottle performance report

# Optimize memory usage
milkbottle performance optimize-memory

# Show cache statistics
milkbottle performance cache-stats
```

### Plugin Marketplace

```bash
# Search for plugins
milkbottle marketplace search pdf

# Install a plugin
milkbottle marketplace install plugin-name

# Show plugin information
milkbottle marketplace info plugin-name

# Rate a plugin
milkbottle marketplace rate plugin-name
```

### Deployment Management

```bash
# Deploy application
milkbottle deployment deploy

# Show deployment status
milkbottle deployment status

# Scale application
milkbottle deployment scaling scale-up

# Security scan
milkbottle deployment security scan
```

### System Status

```bash
# Show system status
milkbottle status

# Show version
milkbottle version
```

---

## CLI Grammar

```
milk [GLOBAL_OPTS] bottle <BottleName|Alias> [BOTTLE_OPTS] [PATTERN]
```

- **Global Opts** `--log-level` `--config` `--dry` `--version`
- **Bottle Opts** defined by each bottle (see docs below).

---

## Built‑In Bottles

| Alias          | Status      | Purpose                                        | Key Options                          |
| -------------- | ----------- | ---------------------------------------------- | ------------------------------------ |
| **PDFmilker**  | ✅ Complete | Extract text, images, metadata → bundle output | `--images/--no-images` `--overwrite` |
| **FONTmilker** | 🚧 Planned  | Organise fonts into `<family>/<style>` tree    | `--move/--copy` `--formats`          |

> **Suggestion:** Once FONTmilker lands, link its doc page here.

---

## PDFmilker Usage

PDFmilker is a comprehensive PDF processing tool that extracts structured content, images, tables, and metadata from PDF documents.

### Basic Usage

```bash
# Process all PDFs in current directory
milk bottle PDFmilker

# Process specific PDF file
milk bottle PDFmilker --input document.pdf

# Process PDFs in specific directory
milk bottle PDFmilker --input /path/to/pdfs/

# Specify output directory
milk bottle PDFmilker --input document.pdf --output /path/to/output/
```

### Advanced Features

```bash
# Extract with images and tables
milk bottle PDFmilker --input document.pdf --images --tables

# Dry run (preview without processing)
milk bottle PDFmilker --input document.pdf --dry-run

# Verbose logging
milk bottle PDFmilker --input document.pdf --verbose

# Quiet mode
milk bottle PDFmilker --input document.pdf --quiet

# Overwrite existing files
milk bottle PDFmilker --input document.pdf --overwrite
```

### Output Structure

PDFmilker creates a structured output directory for each processed PDF:

```
output/
├── document_name/
│   ├── pdf/           # Relocated PDF files
│   ├── markdown/      # Extracted text in Markdown format
│   ├── images/        # Extracted images with captions
│   ├── tables/        # Extracted tables in CSV format
│   └── meta/          # Metadata and processing reports
```

### Processing Pipeline

PDFmilker follows a comprehensive processing pipeline:

1. **Discovery** - Find and validate PDF files
2. **Preparation** - Create output directory structure
3. **Extraction** - Extract text, images, tables, and metadata
4. **Transformation** - Convert to Markdown with YAML front-matter
5. **Validation** - Verify extracted assets and PDF integrity
6. **Relocation** - Move PDFs to organized structure
7. **Reporting** - Generate processing reports and summaries

### Supported Content Types

- **Text**: Structured text extraction with semantic classification
- **Images**: Figure extraction with captions and metadata
- **Tables**: Table detection and CSV export
- **Math**: Mathematical expression recognition
- **Metadata**: Document properties, author, title, etc.
- **References**: Citation and bibliography extraction

---

## Configuration

MilkBottle layers settings from multiple sources (lowest → highest):

1. Package defaults
2. System‑wide `/etc/milkbottle.toml`
3. User `~/.config/milkbottle.toml`
4. Project‑local `milkbottle.toml`
5. CLI flags

Example **milkbottle.toml**

```toml
[global]
outdir = "~/MilkBottleOutput"
log_level = "info"
dry = false

[PDFmilker]
images = true
tables = true
overwrite = false
extract_math = true
extract_citations = true
quality_assessment = true
output_format = "markdown"
```

### PDFmilker Configuration Options

| Option               | Type   | Default      | Description                                 |
| -------------------- | ------ | ------------ | ------------------------------------------- |
| `images`             | bool   | `true`       | Extract images with captions                |
| `tables`             | bool   | `true`       | Extract tables to CSV                       |
| `overwrite`          | bool   | `false`      | Overwrite existing files                    |
| `extract_math`       | bool   | `true`       | Extract mathematical expressions            |
| `extract_citations`  | bool   | `true`       | Extract citations and bibliography          |
| `quality_assessment` | bool   | `true`       | Perform quality assessment                  |
| `output_format`      | string | `"markdown"` | Output format (markdown, html, latex, json) |

---

## Running Tests

To run all tests (unit, integration, render):

```bash
# Run all tests
pytest

# Run PDFmilker tests only
pytest src/tests/pdfmilker/

# Run with coverage
pytest --cov=milkbottle.modules.pdfmilker --cov-report=term-missing

# Run specific test file
pytest src/tests/pdfmilker/test_extract.py -v
```

- Ensure you have all dev dependencies installed: `pip install -e ".[dev]"`
- Test coverage should be 90%+ for all modules and bottles.
- Current PDFmilker coverage: 97% for core modules (discovery, extract, prepare, relocate, report, transform, validate)

---

## Adding New Bottles/Plugins

1. Create a new folder under `src/milkbottle/modules/` (e.g., `mybottle/`).
2. Implement your CLI in `cli.py` and expose a `get_cli()` function and metadata (`__alias__`, `__description__`, `__version__`).
3. Add your logic, errors, and tests in the same folder.
4. Register your bottle via entry-point in `pyproject.toml` or let the registry auto-discover it.
5. Add documentation and update the main menu if needed.

### Bottle Structure Example

```
src/milkbottle/modules/mybottle/
├── __init__.py          # Metadata and exports
├── cli.py              # CLI interface
├── core.py             # Main logic
├── errors.py           # Custom exceptions
├── config.py           # Configuration handling
├── tests/              # Test suite
│   ├── test_core.py
│   ├── test_cli.py
│   └── test_integration.py
└── README.md           # Bottle-specific documentation
```

---

## Troubleshooting

### Common Issues

**PDF Processing Errors**

```bash
# Check if PyMuPDF is properly installed
python -c "import fitz; print('PyMuPDF OK')"

# Verify system dependencies
brew install mupdf  # macOS
sudo apt-get install libmupdf-dev  # Ubuntu/Debian
```

**Permission Errors**

```bash
# Check file permissions
ls -la document.pdf

# Run with appropriate permissions
sudo milk bottle PDFmilker --input /protected/directory/
```

**Memory Issues with Large PDFs**

```bash
# Use batch processing for large files
milk bottle PDFmilker --input large_document.pdf --batch-size 1

# Monitor memory usage
milk bottle PDFmilker --input large_document.pdf --verbose
```

**Corrupted PDF Files**

```bash
# PDFmilker handles corrupted files gracefully
# Check the meta/reports for error details
cat output/meta/processing_report.json
```

### Debug Mode

```bash
# Enable debug logging
milk bottle PDFmilker --input document.pdf --log-level debug

# Check detailed processing logs
tail -f ~/.milkbottle/logs/pdfmilker.log
```

### Performance Optimization

```bash
# Process multiple files in parallel
milk bottle PDFmilker --input /path/to/pdfs/ --workers 4

# Skip existing files for faster re-runs
milk bottle PDFmilker --input /path/to/pdfs/ --skip-existing

# Use dry-run to preview operations
milk bottle PDFmilker --input /path/to/pdfs/ --dry-run
```

---

## Contributing

1. Fork, branch, code.
2. Ensure **Black**, **isort**, and **pytest** pass (`pytest -q`).
3. Submit a PR with a clear description and link to a TASKLIST item if applicable.

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run linting
black src/
isort src/

# Run tests
pytest src/tests/ -v

# Check coverage
pytest --cov=milkbottle --cov-report=html
```

> **Suggestion:** Add a GitHub Action for lint + tests to automate checks.

---

## Task 5 — README Usage Snippet (COMPLETED)

Below is a drop‑in section you can paste into your project’s `README.md` to document the new Hybrid Sourcery Workflow.

---

### Hybrid Sourcery PR Workflow

This repository uses an **automated PR workflow** that combines a local guardrail, a one‑command PR helper, and CI enforcement.

| Stage          | Tool                                    | What it does                                              |
| -------------- | --------------------------------------- | --------------------------------------------------------- |
| Local pre‑push | `.githooks/pre‑push`                    | Runs `sourcery review` and blocks pushes if issues found. |
| One‑command PR | `auto_pr_to_sourcery()`                 | Pushes branch, opens PR, triggers Sourcery review.        |
| CI enforcement | `.github/workflows/sourcery-review.yml` | Runs Sourcery in GitHub Actions for every PR update.      |

#### How to use

```bash
# 1. (Optional) Verify everything is set up
./scripts/pr_check.sh

# 2. Create / switch to a feature branch and commit your changes

# 3. Let Sourcery vet your code locally
#    (automatically triggered by the pre‑push hook)

git push

# 4. Create and open a PR in one go

auto_pr_to_sourcery
```

> **Tip:** The GitHub Action will re‑run Sourcery for every push made to your PR, ensuring continuous feedback.

---

## Roadmap

| Milestone  | Target                                 | Notes                       |
| ---------- | -------------------------------------- | --------------------------- |
| **v0.1.0** | Bottle registry + PDFmilker integrated | ✅ Complete                 |
| **v0.2.0** | FONTmilker MVP                         | Adds `fontTools` dep        |
| **v0.3.x** | Plugin SDK + cookiecutter              | Encourage community bottles |
| **v1.0.0** | Stable API freeze                      | Semantic versioning         |

### Recent Updates (Phase 4.1 & 4.2)

- ✅ **Comprehensive Testing Suite**: 164+ tests with 97% coverage for core modules
- ✅ **Advanced PDF Processing**: Structured text extraction, image processing, table detection
- ✅ **Integration Tests**: Full pipeline workflow testing with error handling
- ✅ **CLI Testing**: Command-line interface behavior testing
- ✅ **Error Recovery**: Robust error handling and recovery mechanisms
- ✅ **Performance Optimization**: Batch processing and memory management
- ✅ **Documentation**: Comprehensive usage examples and troubleshooting guide

---

## License

MIT © 2025

```
deadcoast.net
```
