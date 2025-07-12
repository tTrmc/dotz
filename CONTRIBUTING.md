# Contributing to dotz

Thank you for your interest in contributing to dotz! I welcome all pull requests, bug reports, and feature suggestions.

## Table of Contents

* [Getting Started](#getting-started)
* [Development Setup](#development-setup)
* [Development Tools](#development-tools)
* [Code Style](#code-style)
* [Testing](#testing)
* [Commit Guidelines](#commit-guidelines)
* [Pull Requests](#pull-requests)
* [Reporting Issues](#reporting-issues)
* [Feature Requests](#feature-requests)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/yourusername/dotz.git
   cd dotz
   ```

3. **Set up the development environment**:

   ```bash
   ./setup-dev.sh  # This sets up virtual environment and installs dependencies
   ```

   Or manually:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev,test]"
   ```

4. **Create a new branch** for your changes:

   ```bash
   git checkout -b feature/my-new-feature
   ```

5. **Make your changes** locally in this new branch
6. **Test your changes** thoroughly
7. **Submit a pull request**

## Development Setup

### Prerequisites

* Python 3.9 or newer
* Git
* Virtual environment (recommended)

### Quick Setup

```bash
git clone https://github.com/yourusername/dotz.git
cd dotz
./setup-dev.sh
```

This will:

* Create a virtual environment
* Install development dependencies
* Set up pre-commit hooks automatically
* Run initial tests to verify setup

### Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,test]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically run code quality checks before each commit. The hooks are configured in `.pre-commit-config.yaml` and include:

**Code Formatting:**

* `black`: Python code formatting
* `isort`: Import sorting
* `trailing-whitespace`: Remove trailing whitespace
* `end-of-file-fixer`: Ensure files end with newline

**Code Quality:**

* `flake8`: Python linting with additional plugins
* `mypy`: Static type checking
* `bandit`: Security vulnerability scanning
* `pydocstyle`: Docstring style checking

**Commit Quality:**

* `conventional-pre-commit`: Enforce conventional commit messages
* `markdownlint`: Markdown formatting and style

**Setup Pre-commit:**

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg

# Run against all files (optional, for first setup)
pre-commit run --all-files
```

**Using Pre-commit:**

Once installed, pre-commit will run automatically on `git commit`. You can also run it manually:

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black

# Skip hooks for a commit (use sparingly)
git commit --no-verify -m "commit message"
```

## Development Tools

This project uses modern Python development tools:

* **pytest**: Testing framework with comprehensive coverage
* **black**: Code formatting for consistent style
* **isort**: Import sorting and organization
* **flake8**: Linting for code quality
* **mypy**: Static type checking
* **GitHub Actions**: Automated CI/CD pipeline

### Running Development Commands

```bash
make help          # Show all available commands
make test          # Run the complete test suite
make lint          # Check code style and quality
make format        # Auto-format code with black and isort
make type-check    # Run mypy type checking
make build         # Build distribution packages
make clean         # Clean build artifacts
```

Run all quality checks:

```bash
make test lint type-check
```

## Code Style

### Python Code Guidelines

* Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines
* Use type hints for function parameters and return values
* Write docstrings for public functions and classes
* Keep functions focused and reasonably sized
* Use descriptive variable and function names

### Formatting

Code is automatically formatted using **black** and **isort**:

```bash
make format  # Auto-format all code
```

### Import Organization

* Standard library imports first
* Third-party imports second
* Local/project imports last
* Use absolute imports when possible

Example:

```python
import os
import sys
from pathlib import Path

import typer
from git import Repo

from dotz.core import DotzCore
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=dotz

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_init_repo
```

### Writing Tests

When adding new features or fixing bugs:

* **Add tests** for new functionality
* **Follow existing patterns** in the test suite
* **Use descriptive test names** that explain what is being tested
* **Test both success and failure scenarios**
* **Ensure tests are isolated** and don't depend on external state
* **Mock external dependencies** when appropriate

Test file structure:

```python
import pytest
from unittest.mock import Mock, patch

from dotz.core import DotzCore


class TestFeatureName:
    def test_successful_operation(self):
        # Test the happy path
        pass

    def test_handles_error_condition(self):
        # Test error handling
        pass
```

### Test Environment

* Tests run in isolated temporary directories
* No interference with your actual dotz configuration
* Automatic cleanup after test completion

## Commit Guidelines

### Conventional Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for consistent and meaningful commit messages. The pre-commit hooks will enforce this format.

**Format:**

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation only changes
* `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `test`: Adding missing tests or correcting existing tests
* `build`: Changes that affect the build system or external dependencies
* `ci`: Changes to CI configuration files and scripts
* `perf`: A code change that improves performance
* `chore`: Other changes that don't modify src or test files

**Examples:**

```text
feat(gui): add dashboard widget for repository status
fix(cli): resolve path resolution on Windows
docs: update installation instructions for GUI support
test: add integration tests for file restoration
refactor(core): simplify config loading logic
```

**Scope (optional):**

* `cli`: Command-line interface
* `gui`: Graphical user interface
* `core`: Core functionality
* `config`: Configuration management
* `docs`: Documentation
* `tests`: Test-related changes

### Legacy Commit Format

For compatibility, you can also use descriptive commit messages:

* **Use imperative mood**: "Add feature" not "Added feature"
* **Be specific**: Explain what changed and why
* **Keep first line under 72 characters**
* **Add detail in body if needed**

Good examples:

```text
Add support for encrypted backup storage

Fix symlink validation for broken links

Update documentation for new config options

Refactor file pattern matching for better performance
```

### Commit Organization

* **One logical change per commit**
* **Group related changes together**
* **Separate formatting changes from logic changes**
* **Include tests with the feature they test**

## Pull Requests

### Before Submitting

1. **Ensure all tests pass**:

   ```bash
   make test
   ```

2. **Check code quality**:

   ```bash
   make lint
   ```

3. **Format your code**:

   ```bash
   make format
   ```

4. **Update documentation** if needed

### Submitting Your PR

1. **Push your branch** to your fork:

   ```bash
   git push -u origin feature/my-new-feature
   ```

2. **Open a pull request** on GitHub with:

   * Clear description of changes
   * Link to related issues (if any)
   * Screenshots or examples (if relevant)
   * Testing instructions (if needed)

### PR Review Process

* I'll review PRs as soon as possible
* May request changes or ask questions
* Once approved, I'll merge the changes
* Your contribution will be acknowledged

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

* **Clear description** of the problem
* **Steps to reproduce** the issue
* **Expected vs actual behavior**
* **Environment information**:
  * Operating system and version
  * Python version (`python --version`)
  * dotz version (`dotz version`)
  * Relevant configuration details
* **Error messages or logs** (if any)
* **Additional context** that might be helpful

### Issue Templates

Use the provided issue templates when available:

* **Bug Report**: For reporting problems
* **Feature Request**: For suggesting new features
* **Documentation**: For documentation improvements

## Feature Requests

When suggesting new features:

* **Describe the use case**: What problem does this solve?
* **Provide examples**: How would you use this feature?
* **Consider alternatives**: Are there existing ways to achieve this?
* **Think about implementation**: Any ideas on how it could work?

### Feature Discussion

* Features are discussed in GitHub issues
* Community input is welcome
* Implementation complexity is considered
* Backward compatibility is important

## Development Guidelines

### Project Goals

Keep these principles in mind:

* **Simplicity**: dotz should be easy to use and understand
* **Reliability**: Robust error handling and comprehensive testing
* **Performance**: Efficient operations, especially for large configurations
* **Compatibility**: Support for different Linux distributions and Python versions
* **Security**: Safe handling of sensitive configuration files

### Code Organization

* **Keep modules focused**: Each module should have a clear purpose
* **Minimize dependencies**: Only add dependencies when necessary
* **Document interfaces**: Clear function and class documentation
* **Handle errors gracefully**: Provide helpful error messages

## Getting Help

### Resources

* **README.md**: Project overview and basic usage
* **Issues**: Search existing issues for similar problems
* **Code**: Read the source code for implementation details
* **Tests**: Look at tests for usage examples

### Communication

* **GitHub Issues**: Primary communication channel
* **Pull Request discussions**: For code-specific questions
* **Email**: For security issues only (see SECURITY.md)

### Response Times

* I aim to respond to issues and PRs within a few days
* Complex changes may take longer to review
* Feel free to ping if you haven't heard back in a week

## Recognition

Contributors are acknowledged in:

* **README.md acknowledgments section**
* **Git commit history**
* **Release notes** (for significant contributions)

Thank you for helping make dotz better!
