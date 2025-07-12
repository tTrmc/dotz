# Pre-commit Setup for dotz

This document describes the automated code quality and formatting setup for dotz using pre-commit hooks.

## Overview

The pre-commit configuration automatically runs the following checks:

### Code Formatting

- **black**: Python code formatting
- **isort**: Import sorting and organization
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline

### Code Quality

- **flake8**: Python linting with plugins:
  - flake8-docstrings: Docstring style checking
  - flake8-bugbear: Additional bug and design problems
  - flake8-comprehensions: Better list/dict/set comprehensions
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **pydocstyle**: Documentation style checking

### Documentation

**Note**: Markdown linting is currently disabled to focus on core Python development tools.

### Commit Quality

- **conventional-pre-commit**: Enforce conventional commit message format

## Installation

Pre-commit hooks are automatically installed when you run `./setup-dev.sh`.

For manual installation:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

## Usage

### Automatic (Recommended)

Pre-commit hooks run automatically on `git commit`. If any checks fail, the commit is aborted and you'll need to fix the issues before committing.

### Manual

You can run pre-commit hooks manually:

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black

# Skip hooks for emergency commits (use sparingly)
git commit --no-verify -m "emergency fix"
```

## Configuration

The pre-commit configuration is in `.pre-commit-config.yaml`. Tool-specific settings are in `pyproject.toml`.

### Conventional Commits

Commit messages must follow the conventional commit format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Examples:

- `feat(gui): add new dashboard widget`
- `fix(cli): resolve path resolution issue`
- `docs: update installation instructions`

## Troubleshooting

### Hooks Fail on First Run

This is normal - pre-commit downloads and installs tools on first use. Subsequent runs will be faster.

### Black/isort Conflicts

If black and isort make conflicting changes, run:

```bash
pre-commit run --all-files
```

### Updating Hooks

```bash
pre-commit autoupdate
```

### Skipping Specific Files

Add files to the `exclude` pattern in `.pre-commit-config.yaml`.

## Integration with Make

Use the Makefile commands for consistency:

```bash
make format        # Format code (black + isort)
make lint          # Run linting checks
make lint-all      # Run all checks including security
make pre-commit-run # Run all pre-commit hooks
```
