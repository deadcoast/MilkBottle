# MilkBottle Module Integration Standard

## 📋 **QUICK REFERENCE**

**Purpose**: Standardized approach for integrating new modules into MilkBottle  
**Scope**: All modules must follow this standard for seamless integration  
**Version**: 1.0.0

## 🏗️ **MODULE STRUCTURE REQUIREMENTS**

### **Required File Structure**

```
src/milkbottle/modules/[module_name]/
├── __init__.py              # Required: Interface & metadata
├── cli.py                   # Required: CLI interface
├── config.py                # Required: Configuration
├── errors.py                # Required: Custom errors
├── utils.py                 # Optional: Utilities
├── tests/                   # Required: Test suite
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_integration.py
└── requirements.txt         # Optional: Dependencies
```

### **Required Interface Implementation**

```python
# Required: src/milkbottle/modules/[module_name]/__init__.py

# Required metadata
__version__ = "1.0.0"
__alias__ = "module_name"
__description__ = "Module description"
__author__ = "Author Name"
__email__ = "author@example.com"

# Required exports
def get_cli():
    """Get module CLI interface."""
    from .cli import cli
    return cli

def get_metadata():
    """Get module metadata."""
    return {
        "name": __alias__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "email": __email__,
        "capabilities": get_capabilities(),
        "dependencies": get_dependencies(),
        "config_schema": get_config_schema()
    }

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate module configuration."""
    from .config import validate_config as validate
    return validate(config)

def health_check() -> Dict[str, Any]:
    """Perform module health check."""
    return {
        "status": "healthy",
        "details": "Module is functioning normally",
        "timestamp": datetime.now().isoformat(),
        "version": __version__
    }

def get_capabilities() -> List[str]:
    """Return list of module capabilities."""
    return []

def get_dependencies() -> List[str]:
    """Return list of module dependencies."""
    return []

def get_config_schema() -> Dict[str, Any]:
    """Return configuration schema."""
    return {}
```

## ⚙️ **CONFIGURATION REQUIREMENTS**

### **Configuration Schema**

```python
# Required: src/milkbottle/modules/[module_name]/config.py

@dataclass
class ModuleConfig:
    """Module configuration schema."""
    enabled: bool = True
    dry_run: bool = False
    verbose: bool = False

    def validate(self) -> bool:
        """Validate configuration."""
        return True

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "verbose": self.verbose
        }

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    try:
        module_config = ModuleConfig(**config)
        return module_config.validate()
    except Exception:
        return False
```

## 🛡️ **ERROR HANDLING REQUIREMENTS**

### **Custom Error Classes**

```python
# Required: src/milkbottle/modules/[module_name]/errors.py

class ModuleError(Exception):
    """Base exception for module errors."""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ConfigurationError(ModuleError):
    """Configuration-related errors."""
    pass

class ValidationError(ModuleError):
    """Validation-related errors."""
    pass

class ProcessingError(ModuleError):
    """Processing-related errors."""
    pass
```

## 🖥️ **CLI INTERFACE REQUIREMENTS**

### **CLI Implementation**

```python
# Required: src/milkbottle/modules/[module_name]/cli.py

import click
from rich.console import Console
from .errors import ModuleError, ConfigurationError

console = Console()

@click.group()
@click.option("--config", help="Configuration file path")
@click.option("--dry-run", is_flag=True, help="Dry run mode")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cli(config: Optional[str], dry_run: bool, verbose: bool):
    """Module CLI interface."""
    pass

@cli.command()
def main():
    """Main module command."""
    try:
        # Module implementation
        pass
    except ModuleError as e:
        console.print(f"[red]Module error: {e.message}[/red]")
        if e.details:
            console.print(f"[dim]{e.details}[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

@cli.command()
def status():
    """Show module status."""
    pass

@cli.command()
def config():
    """Show module configuration."""
    pass
```

## 🧪 **TESTING REQUIREMENTS**

### **Test Structure**

```python
# Required: src/milkbottle/modules/[module_name]/tests/test_cli.py

import pytest
from click.testing import CliRunner
from ..cli import cli

def test_cli_main():
    """Test main CLI command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['main'])
    assert result.exit_code == 0

def test_cli_status():
    """Test status command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0

def test_cli_config():
    """Test config command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['config'])
    assert result.exit_code == 0
```

## 📊 **HEALTH CHECK REQUIREMENTS**

### **Health Check Implementation**

```python
def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    try:
        # Check module dependencies
        deps_status = check_dependencies()

        # Check configuration
        config_status = check_configuration()

        # Check functionality
        func_status = check_functionality()

        # Determine overall status
        if all(status['status'] == 'healthy' for status in [deps_status, config_status, func_status]):
            overall_status = 'healthy'
            details = 'All checks passed'
        elif any(status['status'] == 'critical' for status in [deps_status, config_status, func_status]):
            overall_status = 'critical'
            details = 'Critical issues detected'
        else:
            overall_status = 'warning'
            details = 'Some warnings detected'

        return {
            "status": overall_status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "version": __version__,
            "checks": {
                "dependencies": deps_status,
                "configuration": config_status,
                "functionality": func_status
            }
        }
    except Exception as e:
        return {
            "status": "critical",
            "details": f"Health check failed: {e}",
            "timestamp": datetime.now().isoformat(),
            "version": __version__
        }
```

## 🔧 **INTEGRATION CHECKLIST**

### **Module Development**

- [ ] **Create module directory structure**
- [ ] **Implement required interface in `__init__.py`**
- [ ] **Create configuration schema in `config.py`**
- [ ] **Define custom error classes in `errors.py`**
- [ ] **Implement CLI interface in `cli.py`**
- [ ] **Add comprehensive test suite**
- [ ] **Create module documentation**

### **Interface Compliance**

- [ ] **Export `get_cli()` function**
- [ ] **Export `get_metadata()` function**
- [ ] **Export `validate_config()` function**
- [ ] **Export `health_check()` function**
- [ ] **Implement required metadata fields**
- [ ] **Define capabilities list**
- [ ] **Define dependencies list**
- [ ] **Create configuration schema**

### **Error Handling**

- [ ] **Define base ModuleError class**
- [ ] **Create specific error types**
- [ ] **Implement proper error messages**
- [ ] **Add error details support**
- [ ] **Handle exceptions gracefully**

### **CLI Implementation**

- [ ] **Create Click/Typer CLI group**
- [ ] **Implement main command**
- [ ] **Add status command**
- [ ] **Add config command**
- [ ] **Handle command-line arguments**
- [ ] **Implement error handling**
- [ ] **Add help text and documentation**

### **Configuration Management**

- [ ] **Define configuration dataclass**
- [ ] **Implement validation logic**
- [ ] **Create default values**
- [ ] **Add configuration conversion methods**
- [ ] **Handle configuration errors**

### **Testing**

- [ ] **Create unit tests for all functions**
- [ ] **Add integration tests**
- [ ] **Test error conditions**
- [ ] **Test configuration validation**
- [ ] **Test CLI commands**
- [ ] **Test health checks**

### **Documentation**

- [ ] **Create module README**
- [ ] **Document API functions**
- [ ] **Add usage examples**
- [ ] **Document configuration options**
- [ ] **Add troubleshooting guide**

### **Quality Assurance**

- [ ] **Run all tests successfully**
- [ ] **Validate configuration schemas**
- [ ] **Test health check functionality**
- [ ] **Verify CLI interface**
- [ ] **Check error handling**
- [ ] **Validate metadata**

## 🚀 **QUICK START TEMPLATE**

### **1. Create Module Structure**

```bash
mkdir -p src/milkbottle/modules/my_module/tests
touch src/milkbottle/modules/my_module/__init__.py
touch src/milkbottle/modules/my_module/cli.py
touch src/milkbottle/modules/my_module/config.py
touch src/milkbottle/modules/my_module/errors.py
touch src/milkbottle/modules/my_module/utils.py
touch src/milkbottle/modules/my_module/tests/__init__.py
touch src/milkbottle/modules/my_module/tests/test_cli.py
touch src/milkbottle/modules/my_module/tests/test_config.py
touch src/milkbottle/modules/my_module/requirements.txt
```

### **2. Implement Required Interface**

```python
# Copy the interface template from above
# Replace placeholders with actual implementation
```

### **3. Test Integration**

```bash
cd src/milkbottle/modules/my_module
python -m pytest tests/
```

### **4. Register Module**

```python
# Add to pyproject.toml entry points
[project.entry-points."milkbottle.bottles"]
my_module = "milkbottle.modules.my_module:get_cli"
```

## 📋 **VALIDATION CHECKLIST**

### **Pre-Integration Validation**

- [ ] **All required files exist**
- [ ] **Interface functions implemented**
- [ ] **Metadata fields defined**
- [ ] **Configuration schema created**
- [ ] **Error classes defined**
- [ ] **CLI interface implemented**
- [ ] **Tests written and passing**
- [ ] **Documentation complete**

### **Integration Testing**

- [ ] **Module loads without errors**
- [ ] **CLI commands work correctly**
- [ ] **Configuration validation passes**
- [ ] **Health checks return valid status**
- [ ] **Error handling works properly**
- [ ] **Metadata is accessible**
- [ ] **Dependencies are resolved**

### **Post-Integration Validation**

- [ ] **Module appears in bottle list**
- [ ] **Module can be launched from main menu**
- [ ] **Configuration is loaded correctly**
- [ ] **Health status is displayed**
- [ ] **Errors are handled gracefully**
- [ ] **Performance is acceptable**

## 🎯 **SUCCESS CRITERIA**

### **Functional Requirements**

- [ ] **Module integrates seamlessly with MilkBottle**
- [ ] **All CLI commands work correctly**
- [ ] **Configuration is properly validated**
- [ ] **Health checks provide accurate status**
- [ ] **Error handling is robust**

### **Quality Requirements**

- [ ] **Code follows Python best practices**
- [ ] **Type hints are used throughout**
- [ ] **Documentation is comprehensive**
- [ ] **Tests provide good coverage**
- [ ] **Error messages are user-friendly**

### **Performance Requirements**

- [ ] **Module loads quickly**
- [ ] **Commands execute efficiently**
- [ ] **Memory usage is reasonable**
- [ ] **No resource leaks**
- [ ] **Graceful error recovery**

## 📚 **REFERENCE DOCUMENTS**

- **Main Application Enhancement**: `MILKBOTTLE_MAIN_APPLICATION_ENHANCEMENT.md`
- **PDFmilker Enhancements**: `PDFMILKER_ENHANCEMENTS_IMPLEMENTED.md`
- **Code Enhancement Analysis**: `PDFMILKER_CODE_ENHANCEMENT_ANALYSIS.md`
- **Enhancement Summary**: `PDFMILKER_ENHANCEMENT_SUMMARY.md`

## 🔄 **VERSION HISTORY**

- **1.0.0**: Initial standard definition
- **Future**: Will be updated based on implementation feedback

---

**Status**: ✅ **READY FOR IMPLEMENTATION**  
**Next Step**: Use this standard to enhance existing modules and create new ones
