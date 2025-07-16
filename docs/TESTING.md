# Testing Guide for Dotz

This document explains how to run different types of tests in the dotz project.

## Test Categories

The dotz project has two main categories of tests:

### 1. Core Tests (CLI, Core functionality, Integration)
- **Files**: `test_cli.py`, `test_core.py`, `test_integration.py`, `test_progress.py`, `test_watcher.py`
- **Coverage**: Command-line interface, core dotfiles management, file operations, configuration management
- **Environment**: Can run in any environment, including headless CI/CD systems

### 2. GUI Tests
- **Files**: `test_gui_*.py` (dashboard, files, init, integration, main, settings)
- **Coverage**: PySide6-based graphical user interface components
- **Environment**: Requires display or virtual display setup
- **Marked with**: `@pytest.mark.gui`

## Running Tests

### Run All Tests (Local Development)
```bash
# Run everything (requires display for GUI tests)
pytest

# Run with coverage
pytest --cov=dotz --cov-report=html
```

### Run Core Tests Only (CI/CD Safe)
```bash
# Skip GUI tests - ideal for CI/CD environments
pytest -m "not gui"

# With coverage (recommended for CI)
pytest --cov=dotz --cov-report=xml -m "not gui"
```

### Run GUI Tests Only
```bash
# Run only GUI tests (requires display)
pytest -m "gui"

# Run GUI tests in headless mode (Linux with xvfb)
QT_QPA_PLATFORM=offscreen pytest -m "gui"
```

### Run Specific Test Files
```bash
# Core functionality
pytest tests/test_core.py

# CLI commands
pytest tests/test_cli.py

# Integration tests
pytest tests/test_integration.py

# Specific GUI component
pytest tests/test_gui_main.py
```

## CI/CD Configuration

### GitHub Actions (Recommended)
```yaml
- name: Run tests
  run: |
    pytest --cov=dotz --cov-report=xml -m "not gui"
```

### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-core
        name: Run core tests
        entry: pytest
        args: ["-m", "not gui", "--tb=short"]
        language: system
        pass_filenames: false
```

### Local GUI Testing
If you want to run GUI tests locally:

```bash
# Standard run (requires display)
pytest -m "gui"

# Headless run (Linux)
xvfb-run pytest -m "gui"

# With environment variable
QT_QPA_PLATFORM=offscreen pytest -m "gui"
```

## Test Statistics

- **Total Tests**: ~251
- **Core Tests**: ~161 (CLI, core, integration, watcher, progress)
- **GUI Tests**: ~90 (all GUI components)
- **Coverage**: Core tests provide ~95% coverage of core functionality

## Troubleshooting

### GUI Tests Hanging
If GUI tests hang or freeze:
```bash
# Use timeout
pytest -m "gui" --timeout=30

# Force headless mode
QT_QPA_PLATFORM=offscreen CI=true pytest -m "gui"

# Skip problematic tests
pytest -m "gui" -k "not test_problematic_function"
```

### Missing Dependencies
```bash
# Install test dependencies
pip install -e ".[test]"

# For GUI testing on Linux
sudo apt-get install xvfb libxcb-xinerama0
```

### CI Environment Detection
The test suite automatically detects CI environments and enables headless mode:
- `CI=true`
- `GITHUB_ACTIONS=true`
- `QT_QPA_PLATFORM=offscreen`

## Best Practices

1. **Local Development**: Run all tests to ensure full functionality
2. **CI/CD**: Use `-m "not gui"` for reliability and speed
3. **Pre-commit**: Run core tests only for quick feedback
4. **GUI Development**: Test GUI components individually during development
5. **Coverage**: Core tests provide sufficient coverage for CI purposes

## Performance

- **Core Tests**: ~3-5 seconds
- **GUI Tests**: ~6-10 seconds
- **All Tests**: ~8-15 seconds (when GUI tests don't hang)

The separation allows for fast CI builds while maintaining comprehensive test coverage for both CLI and GUI functionality.
