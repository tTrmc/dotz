# Contributing to dotz

Thank you for your interest in contributing! All pull requests, bug reports, and feature suggestions are welcome.

## Quick Start

1. **Fork and clone**
   ```bash
   git clone https://github.com/yourusername/dotz.git
   cd dotz
   ```

2. **Setup development environment**
   ```bash
   ./setup-dev.sh  # Sets up venv, installs deps, configures pre-commit
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

4. **Make changes and test**
   ```bash
   make test lint  # Run tests and check code quality
   ```

5. **Submit pull request**

## Development Commands

```bash
make test          # Run tests
make lint          # Check code style
make format        # Auto-format code
make test-cov      # Test with coverage
make clean         # Clean build artifacts
```

## Code Style

- **Python**: Follow PEP 8, use type hints, write docstrings
- **Formatting**: Automatic with `black` and `isort`
- **Testing**: Add tests for new features and bug fixes
- **Imports**: Standard library → third-party → local imports

Example:
```python
import os
from pathlib import Path

import typer
from git import Repo

from dotz.core import DotzCore
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[(scope)]: <description>

[optional body]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Other changes

**Examples:**
```
feat(gui): add dashboard widget
fix(cli): resolve Windows path issue
docs: update installation guide
test: add integration tests for restore
```

## Testing

- Tests run in isolated environments
- Use descriptive test names
- Test both success and error cases
- Mock external dependencies

```bash
pytest                    # Run all tests
pytest tests/test_core.py # Run specific file
pytest -v                 # Verbose output
pytest --cov=dotz        # With coverage
```

## Pull Request Guidelines

**Before submitting:**
- [ ] Tests pass (`make test`)
- [ ] Code formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated (if needed)

**PR description should include:**
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Testing instructions

## Reporting Issues

**Bug reports should include:**
- Clear problem description
- Steps to reproduce
- Expected vs actual behavior
- Environment details:
  - OS and version
  - Python version (`python --version`)
  - dotz version (`dotz version`)
- Error messages/logs

**Feature requests should include:**
- Use case description
- Examples of how it would work
- Consider alternatives

## Development Environment

**Requirements:**
- Python 3.9+
- Git
- Virtual environment (recommended)

**Manual setup:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,test]"
pre-commit install
```

## Project Goals

- **Simplicity**: Easy to use and understand
- **Reliability**: Robust error handling
- **Performance**: Efficient operations
- **Security**: Safe handling of sensitive files

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/tTrmc/dotz/issues)
- **Discussions**: PR comments for code questions
- **Code**: Read source and tests for examples

Response time: Usually within a few days. Feel free to ping if no response after a week.

## Recognition

Contributors are acknowledged in README.md and git history. Significant contributions are mentioned in release notes.

Thank you!