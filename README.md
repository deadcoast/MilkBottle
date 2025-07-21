# MilkBottle 🍼 – The Fluid Code Toolbox

## Dual CLI System: Interactive Menu & Modular CLI

MilkBottle now supports **two powerful CLI entry points**:

- **`milk`** — launches the original interactive ASCII menu system (TUI), with all your custom logic, bottle menus, and guided workflows. This is the classic, user-friendly, menu-driven experience.
- **`milk-cli`** — launches the modern modular CLI, with explicit subcommands for bottles, plugins, deployment, performance, and more. This is ideal for scripting, automation, and advanced users.

**You can use both CLIs side-by-side:**

- Use `milk` for interactive exploration, configuration wizards, and guided workflows.
- Use `milk-cli` for direct scripting, automation, and advanced plugin management.

### Example Usage

```bash
# Launch the interactive menu system (recommended for most users)
milk

# Use the modular CLI for scripting and automation
milk-cli bottle list
milk-cli bottle run pdfmilker --input file.pdf --output outdir/
```

---

## Table of Contents

- [MilkBottle 🍼 – The Fluid Code Toolbox](#milkbottle---the-fluid-code-toolbox)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Phase 5: Enterprise Features (✅ Complete)](#phase-5-enterprise-features--complete)
    - [Plugin SDK](#plugin-sdk)
    - [Performance Optimization](#performance-optimization)
    - [Plugin Marketplace](#plugin-marketplace)
    - [Deployment Management](#deployment-management)
    - [System Status](#system-status)
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
    - [Performance Optimization](#performance-optimization-1)
  - [Contributing](#contributing)
    - [Development Setup](#development-setup)
  - [Task 5 — README Usage Snippet (COMPLETED)](#task5readmeusagesnippetcompleted)
    - [Hybrid Sourcery PR Workflow](#hybrid-sourcery-pr-workflow)
      - [How to use](#howto-use)
  - [TROUBLESHOOTING](#troubleshooting-1)
    - [1. **Identify Required Dependencies**](#1-identify-required-dependencies)
    - [2. **Install All Required Dependencies**](#2-install-all-required-dependencies)
    - [3. **Install System/External Tools (if needed)**](#3-install-systemexternal-tools-if-needed)
    - [4. **Verify Installation**](#4-verify-installation)
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

```
