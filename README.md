# loom

[![PyPI version](https://badge.fury.io/py/loomctl.svg)](https://badge.fury.io/py/loomctl)
[![Python versions](https://img.shields.io/pypi/pyversions/loomctl.svg)](https://pypi.org/project/loomctl/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![CI](https://github.com/tTrmc/loom/workflows/CI/badge.svg)](https://github.com/tTrmc/loom/actions)
[![Tests](https://img.shields.io/badge/tests-148%20passing-brightgreen.svg)](https://github.com/tTrmc/loom/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tTrmc/loom/pulls)
[![GitHub issues](https://img.shields.io/github/issues/tTrmc/loom.svg)](https://github.com/tTrmc/loom/issues)

> A minimal **dotfiles** manager for Linux, backed by Git.

**loom** simplifies tracking, versioning, and synchronizing your configuration files across machines. An open source project welcoming community contributions.

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Usage](#usage)
* [Project Structure](#project-structure)
* [Configuration](#configuration)
* [Testing](#testing)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [Support](#support)
* [Acknowledgments](#acknowledgments)
* [License](#license)

## Features

* **Easy setup**: Initialize a local loom repository with a single command
* **Git-based**: Full version history, branching, and remote synchronization
* **File management**: Add and remove dotfiles with automatic symlinking
* **Recursive directory support**: Add all dotfiles (optionally recursively) from a directory
* **Tracked directories**: Only directories you add are watched for new dotfiles
* **Configurable patterns**: Customize which file types to track with include/exclude patterns
* **Status overview**: Display untracked, modified, and staged files at a glance
* **Configuration management**: Built-in commands to manage file patterns and search settings
* **File watching**: Automatic detection and addition of new configuration files
* **Diagnostics**: Built-in `diagnose` command for troubleshooting
* **Shell completion**: Tab-completion for all commands and options
* **Robust & testable**: Comprehensive test suite with environment isolation
* **Portable**: Requires only Python 3.9+ and Git

---

## Installation

### For End Users (Recommended)

**From PyPI:**

```bash
pip install loomctl
```

**Using pipx (isolated environment):**

```bash
# Install pipx if needed
sudo apt install pipx           # Debian/Ubuntu
# or
sudo pacman -S python-pipx      # Arch Linux

# Install loomctl
pipx install loomctl
```

### For Developers

**Quick setup:**

```bash
git clone https://github.com/tTrmc/loom.git
cd loom
./setup-dev.sh  # Sets up virtual environment and installs dependencies
```

**Manual setup:**

```bash
git clone https://github.com/tTrmc/loom.git
cd loom
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

### Verify Installation

```bash
loom --help
```

**Requirements:**

* Python 3.9 or newer
* Git

---

>[!CAUTION]
>**NEVER use public Git repositories with loom.** Your dotfiles often contain:
>
>* SSH keys and certificates
>* API tokens and passwords
>* Personal file paths and system information
>* Application configurations with sensitive data
>
>**Always use private repositories** or consider excluding sensitive files with loom's pattern configuration.

---

## Quick Start

### Initialize your loom repository

```bash
# Local repository only
loom init

# With private remote repository (recommended)
loom init --remote git@github.com:yourusername/dotfiles-private.git
```

### Add your first dotfile

```bash
# Add a single file
loom add .bashrc

# Add all dotfiles in a directory
loom add .config

# Add and push to remote
loom add .vimrc --push
```

### Sync across machines

```bash
# Pull latest changes
loom pull

# Push your changes
loom push
```

---

## Usage

### Repository Management

**Initialize:**

```bash
loom init                                                    # Local only
loom init --remote git@github.com:user/dotfiles-private.git # With remote
```

**Sync:**

```bash
loom pull    # Fetch and merge changes
loom push    # Push local commits
```

### File Management

**Add files:**

```bash
loom add .bashrc              # Single file
loom add .config              # Directory (recursive by default)
loom add .config --no-recursive  # Top-level files only
loom add .vimrc --push        # Add and push
```

**Remove files:**

```bash
loom delete .vimrc            # Remove file
loom delete .vimrc --push     # Remove and push
```

**Restore files:**

```bash
loom restore .vimrc           # Restore single file
loom restore .config          # Restore directory
```

### Information Commands

```bash
loom status        # Show repository status
loom list-files    # List tracked files
loom diagnose      # Troubleshoot issues
loom version       # Show version
```

### Advanced Features

**File watching:**

```bash
loom watch    # Automatically add new dotfiles in tracked directories
```

**Shell completion:**

```bash
loom --install-completion    # Enable tab completion
```

### Configuration Management

Manage file patterns and search settings:

```bash
loom config show              # Show current configuration
loom config list-patterns     # List file patterns
loom config add-pattern "*.py"           # Include Python files
loom config add-pattern "*.log" --type exclude  # Exclude log files
loom config remove-pattern "*.py"        # Remove pattern
loom config set search_settings.recursive false  # Disable recursion
loom config reset             # Reset to defaults
loom config help              # Show detailed help
```

---

## Project Structure

```text
loom/
├── src/
│   └── loom/
│       ├── __init__.py
│       ├── cli.py          # Typer-based CLI entry point
│       ├── core.py         # Core logic for dotfile management
│       └── watcher.py      # Watchdog-based directory watcher
├── tests/
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_cli.py         # CLI command tests
│   ├── test_cli_config.py  # Configuration command tests  
│   ├── test_core.py        # Core functionality tests
│   └── test_watcher.py     # File watching tests
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # Project documentation
├── LICENSE                 # GPL-3.0-or-later license
├── CONTRIBUTING.md         # Contribution guidelines
└── .gitignore              # Files and directories to exclude
```

The `.git` folder is created inside `~/.loom/repo` once you initialize loom.

---

## Configuration

loom uses configurable file patterns to determine which files to track. The configuration is stored in `~/.loom/config.json`.

### Default File Patterns

**Include patterns** (files that will be tracked):

* `.*` - All dotfiles (files starting with `.`)
* `*.conf`, `*.config`, `*.cfg`, `*.ini` - Configuration files
* `*.toml`, `*.yaml`, `*.yml`, `*.json` - Structured config files

**Exclude patterns** (files that will be ignored):

* `.DS_Store`, `.Trash*` - System files
* `.cache`, `.git`, `.svn` - Cache and VCS directories
* `*.log`, `*.tmp` - Temporary files

### Search Settings

* `recursive`: Search subdirectories recursively (default: `true`)
* `case_sensitive`: Case-sensitive pattern matching (default: `false`)
* `follow_symlinks`: Follow symbolic links during search (default: `false`)

### Customizing Configuration

Use the `loom config` commands to customize which files are tracked:

```bash
# Add Python files to tracking
loom config add-pattern "*.py"

# Exclude compiled Python files  
loom config add-pattern "*.pyc" --type exclude

# Disable recursive search
loom config set search_settings.recursive false
```

---

## Testing

loom has a comprehensive test suite to ensure reliability and catch regressions. Contributors are encouraged to run tests before submitting changes.

### Running Tests

**Quick test run:**

```bash
pip install pytest
pytest
```

**With coverage:**

```bash
pytest --cov=loom
```

### Test Categories

The project includes **148 passing tests** covering:

* **CLI commands**: All loom commands and options
* **Core functionality**: File management, Git operations, configuration
* **Configuration management**: Pattern matching, settings, validation
* **File watching**: Automatic detection and tracking of new files
* **Error handling**: Graceful handling of edge cases and failures
* **Environment isolation**: Tests run in isolated temporary environments

### Development Testing

For development, install with test dependencies:

```bash
pip install -e ".[dev,test]"  # Install with all dependencies
pytest -v                     # Run tests with verbose output
pytest --cov=loom             # Run tests with coverage report
make test-cov                 # Run tests with HTML coverage report
```

### Development Workflow

```bash
make help          # Show all available commands
make test          # Run tests
make lint          # Run code quality checks
make format        # Auto-format code
make build         # Build distribution packages
```

### Writing Tests

When contributing new features:

* Add tests to the appropriate test file in `tests/`
* Follow existing test patterns and naming conventions
* Ensure tests are isolated and don't depend on external state
* Test both success and failure scenarios
* Update test documentation if needed

All tests run in isolated temporary environments to prevent interference with your actual loom configuration.

---

## Roadmap

loom is actively developed as a personal project with community input welcome. Here are some areas being explored:

### Planned Features

* **Cross-platform support**: Extend beyond Linux to macOS
* **Plugin system**: Allow custom extensions and integrations
* **Advanced conflict resolution**: Better handling of merge conflicts
* **Performance optimizations**: Faster operations for large dotfile collections
* **Enhanced CLI**: More interactive commands and better user experience

---

## Contributing

Contributions are welcome!

### Ways to Contribute

* **Report bugs**: Found an issue? [Open a bug report](https://github.com/tTrmc/loom/issues/new?labels=bug&template=bug_report.md)
* **Request features**: Have an idea? [Submit a feature request](https://github.com/tTrmc/loom/issues/new?labels=enhancement&template=feature_request.md)
* **Improve documentation**: Help make the docs clearer and more comprehensive
* **Submit code**: Fix bugs or implement new features with a pull request
* **Review PRs**: Help review and test pull requests from other contributors
* **Share feedback**: Let me know how loom works for you and what could be better

### Getting Started

1. **Fork the repository** and clone it locally
2. **Set up development environment**:

   ```bash
   git clone https://github.com/yourusername/loom.git
   cd loom
   ./setup-dev.sh  # Sets up virtual environment and installs dependencies
   ```

3. **Make your changes** and add tests if applicable
4. **Run the test suite** to ensure everything works:

   ```bash
   make test           # Run all tests
   make lint           # Check code quality
   make format         # Auto-format code
   ```

5. **Submit a pull request** with a clear description of your changes

### Development Guidelines

* Follow the existing code style and conventions
* Write tests for new features and bug fixes
* Update documentation when adding new functionality
* Keep commits focused and write clear commit messages

### Need Help?

* Check out [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines
* Browse [existing issues](https://github.com/tTrmc/loom/issues) to see what needs work
* Join discussions in [pull requests](https://github.com/tTrmc/loom/pulls)
* Feel free to ask questions in issues or discussions

---

## Support

### Getting Help

* **Documentation**: Check this README and the built-in help (`loom --help`)
* **Issues**: [Search existing issues](https://github.com/tTrmc/loom/issues) or create a new one
* **Troubleshooting**: Use `loom diagnose` for common problems

### Reporting Issues

When reporting bugs, please include:

* Your operating system and Python version
* loom version (`loom version`)
* Steps to reproduce the issue
* Expected vs. actual behavior
* Any error messages or logs

---

## Acknowledgments

This project has benefited from the contributions and support of the following people:

### Contributors

[![Contributors](https://contrib.rocks/image?repo=tTrmc/loom)](https://github.com/tTrmc/loom/graphs/contributors)

---

## License

This project is distributed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

By contributing to loom, you agree that your contributions will be licensed under the same license.

---
