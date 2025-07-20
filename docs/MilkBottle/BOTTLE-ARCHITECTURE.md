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

Let me test the bottle command directly:

```bash
milk bottle venvmilker --help
```

Let me create a simple test configuration file to test the config file functionality:

Now let's test the configuration file loading:

```bash
milk main --config test_config.toml
```

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

---

I'll continue reviewing the modules and submodules to ensure everything is relevant, connected, and integrated. Let me examine the current module structure and identify any gaps or integration issues.

Ran tool
Ran tool
Ran tool
Read file: src/milkbottle/modules/venvmilker/**init**.py
Read file: src/milkbottle/modules/venvmilker/cli.py
Read file: src/milkbottle/modules/venvmilker/config.py
Read file: src/milkbottle/modules/venvmilker/errors.py
Now let me check the PDFmilker module to see how it compares to the new standard:

Read file: src/milkbottle/modules/pdfmilker/**init**.py
Now let me check the registry to see how modules are currently discovered and loaded:

Read file: src/milkbottle/registry.py
Now let me create a comprehensive module integration analysis and enhancement plan:

Read file: MILKBOTTLE_MODULE_INTEGRATION_ANALYSIS.md
Now let me create a summary document that consolidates all the module integration findings:

## Summary

I have completed a comprehensive review of the modules and submodules in MilkBottle, ensuring everything is relevant, connected, and integrated. Here are the key findings and deliverables:

## �� **DELIVERABLES CREATED**

### **1. Module Integration Analysis**

**File**: `MILKBOTTLE_MODULE_INTEGRATION_ANALYSIS.md`

**Key Findings**:

- **PDFmilker**: ✅ Mostly compliant with advanced features but missing standard interface
- **VENVmilker**: ⚠️ Partially compliant with basic functionality but needs enhancement
- **Fontmilker**: ❌ Empty/incomplete - needs complete implementation

### **2. Module Integration Summary**

**File**: `MILKBOTTLE_MODULE_INTEGRATION_SUMMARY.md`

**Critical Gaps Identified**:

- **Standard Interface Missing**: No consistent module interface across modules
- **Health Monitoring Missing**: No system health monitoring
- **Configuration Validation Missing**: No standardized validation
- **Registry Limitations**: Basic module discovery without validation

## 🔍 **CURRENT MODULE STATUS**

### **✅ PDFmilker Module** - **MOSTLY COMPLIANT**

**Strengths**:

- Comprehensive feature set (batch processing, quality assessment, multi-format export)
- Good error handling and recovery
- Advanced CLI with interactive menus
- Extensive test coverage

**Gaps**:

- Missing standard interface functions (`get_metadata()`, `validate_config()`, `health_check()`)
- No health monitoring
- No configuration validation
- Inconsistent metadata

### **⚠️ VENVmilker Module** - **PARTIALLY COMPLIANT**

**Strengths**:

- Clean CLI interface (Typer)
- Proper configuration management
- Good error hierarchy
- Template system

**Gaps**:

- Missing standard interface functions
- No health monitoring
- No advanced features
- Limited capabilities

### **❌ Fontmilker Module** - **EMPTY/INCOMPLETE**

**Status**: Empty directory, needs complete implementation

## �� **ENHANCEMENT ROADMAP**

### **Phase 1: Standardize Existing Modules (Week 1)**

1. **PDFmilker Enhancement** �� **HIGH PRIORITY**

   - Add standard interface functions
   - Implement health monitoring
   - Add configuration validation
   - Update metadata

2. **VENVmilker Enhancement** ⚠️ **MEDIUM PRIORITY**

   - Add standard interface functions
   - Implement health monitoring
   - Add configuration validation
   - Add enhanced features

3. **Fontmilker Implementation** 🔶 **LOW PRIORITY**
   - Create complete module structure
   - Implement core functionality
   - Add standard interface
   - Add health monitoring

### **Phase 2: Enhanced Registry System (Week 2)**

1. **Create BottleRegistry Class**

   - Interface validation
   - Health check integration
   - Configuration validation
   - Dependency management

2. **Add Health Monitoring System**

   - System resource monitoring
   - Module health checks
   - Performance metrics
   - Error tracking

3. **Add Configuration Validation System**
   - Schema-based validation
   - Type checking
   - Constraint validation
   - Error reporting

### **Phase 3: Advanced Integration Features (Week 3)**

1. **Plugin System**

   - Entry-point registration
   - Dynamic module loading
   - Plugin validation
   - Version compatibility

2. **API Integration**

   - REST API endpoints
   - Module management API
   - Health monitoring API
   - Configuration API

3. **Advanced Monitoring**
   - Real-time metrics
   - Performance profiling
   - Resource usage tracking
   - Error analytics

## 📊 **IMPLEMENTATION PRIORITY MATRIX**

### **🔥 HIGH PRIORITY (Immediate Impact)**

| Module         | Standard Interface | Health Monitoring | Config Validation | Priority        |
| -------------- | ------------------ | ----------------- | ----------------- | --------------- |
| **PDFmilker**  | ❌ Missing         | ❌ Missing        | ❌ Missing        | 🔥 **CRITICAL** |
| **VENVmilker** | ❌ Missing         | ❌ Missing        | ❌ Missing        | ⚠️ **HIGH**     |
| **Fontmilker** | ❌ Missing         | ❌ Missing        | ❌ Missing        | 🔶 **MEDIUM**   |

## 🎯 **SUCCESS METRICS**

### **Functional Requirements**

- [ ] All modules implement standard interface
- [ ] Health monitoring works for all modules
- [ ] Configuration validation works for all modules
- [ ] Registry properly validates and loads modules
- [ ] Error handling is robust and informative

### **Performance Requirements**

- [ ] Module loading is fast (< 1 second)
- [ ] Health checks are efficient (< 500ms)
- [ ] Configuration validation is quick (< 100ms)
- [ ] No memory leaks
- [ ] Graceful error recovery

## 🚀 **IMMEDIATE ACTIONS**

### **This Week**

1. **Enhance PDFmilker**: Add standard interface and health monitoring
2. **Enhance VENVmilker**: Add standard interface and health monitoring
3. **Create Health Monitor**: Implement system health monitoring
4. **Create Config Validator**: Implement configuration validation

### **Next Week**

1. **Enhance Registry**: Create enhanced registry with validation
2. **Implement Fontmilker**: Create complete Fontmilker module
3. **Integration Testing**: Test all modules with new interface
4. **Documentation Update**: Update all documentation

## 🏆 **EXPECTED OUTCOMES**

### **Immediate Benefits**

- **Standardized Interface**: All modules follow the same interface
- **Health Monitoring**: Comprehensive health checks for all components
- **Configuration Validation**: Robust configuration validation
- **Enhanced Registry**: Intelligent module discovery and loading
- **Error Recovery**: Graceful error handling and recovery

### **Long-term Benefits**

- **Extensibility**: Easy to add new modules
- **Maintainability**: Consistent patterns across all modules
- **Reliability**: Robust error handling and recovery
- **Performance**: Optimized module loading and health checks
- **Scalability**: Support for unlimited modules

## 📚 **REFERENCE DOCUMENTS**

- **Module Integration Standard**: `MILKBOTTLE_MODULE_INTEGRATION_STANDARD.md`
- **Module Integration Analysis**: `MILKBOTTLE_MODULE_INTEGRATION_ANALYSIS.md`
- **Module Integration Summary**: `MILKBOTTLE_MODULE_INTEGRATION_SUMMARY.md`
- **Main Application Enhancement**: `MILKBOTTLE_MAIN_APPLICATION_ENHANCEMENT.md`

**Status**: 🚀 **READY FOR IMPLEMENTATION**

The modules are now properly analyzed and have a clear roadmap for standardization and integration. All modules will be relevant, connected, and properly integrated according to the new standard.
