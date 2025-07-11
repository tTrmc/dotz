# dotz

[![PyPI version](https://badge.fury.io/py/dotz.svg)](https://badge.fury.io/py/dotz)
[![Python versions](https://img.shields.io/pypi/pyversions/dotz.svg)](https://pypi.org/project/dotz/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![CI](https://github.com/tTrmc/dotz/workflows/CI/badge.svg)](https://github.com/tTrmc/dotz/actions)
[![Tests](https://img.shields.io/badge/tests-148%20passing-brightgreen.svg)](https://github.com/tTrmc/dotz/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tTrmc/dotz/pulls)
[![GitHub issues](https://img.shields.io/github/issues/tTrmc/dotz.svg)](https://github.com/tTrmc/dotz/issues)

> A minimal **dotfiles** manager for Linux, backed by Git.

**dotz** simplifies tracking, versioning, and synchronizing your configuration files across machines. An open source project welcoming community contributions.

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

* **Easy setup**: Initialize a local dotz repository with a single command
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

## Installation

### For End Users (Recommended)

**From PyPI:**

```bash
pip install dotz
```

**Using pipx (isolated environment):**

```bash
# Install pipx if needed
sudo apt install pipx           # Debian/Ubuntu
# or
sudo pacman -S python-pipx      # Arch Linux

# Install dotz
pipx install dotz
```

### For Developers

**Quick setup:**

```bash
git clone https://github.com/tTrmc/dotz.git
cd dotz
./setup-dev.sh  # Sets up virtual environment and installs dependencies
```

**Manual setup:**

```bash
git clone https://github.com/tTrmc/dotz.git
cd dotz
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

### Verify Installation

```bash
dotz --help
```

**Requirements:**

* Python 3.9 or newer
* Git



>[!CAUTION]
>**NEVER use public Git repositories with dotz.** Your dotfiles often contain:
>
>* SSH keys and certificates
>* API tokens and passwords
>* Personal file paths and system information
>* Application configurations with sensitive data
>
>**Always use private repositories** or consider excluding sensitive files with dotz's pattern configuration.



## Quick Start

### Initialize your dotz repository

```bash
# Local repository only
dotz init

# With private remote repository (recommended)
dotz init --remote git@github.com:yourusername/dotfiles-private.git
```

### Add your first dotfile

```bash
# Add a single file
dotz add .bashrc

# Add all dotfiles in a directory
dotz add .config

# Add and push to remote
dotz add .vimrc --push
```

### Sync across machines

```bash
# Pull latest changes
dotz pull

# Push your changes
dotz push
```



## Usage

### Repository Management

**Initialize:**

```bash
dotz init                                                    # Local only
dotz init --remote git@github.com:user/dotfiles-private.git # With remote
```

**Sync:**

```bash
dotz pull    # Fetch and merge changes
dotz push    # Push local commits
```

### File Management

**Add files:**

```bash
dotz add .bashrc              # Single file
dotz add .config              # Directory (recursive by default)
dotz add .config --no-recursive  # Top-level files only
dotz add .vimrc --push        # Add and push
```

**Remove files:**

```bash
dotz delete .vimrc            # Remove file
dotz delete .vimrc --push     # Remove and push
```

**Restore files:**

```bash
dotz restore .vimrc           # Restore single file
dotz restore .config          # Restore directory
```

### Information Commands

```bash
dotz status        # Show repository status
dotz list-files    # List tracked files
dotz diagnose      # Troubleshoot issues
dotz version       # Show version
```

### Advanced Features

**File watching:**

```bash
dotz watch    # Automatically add new dotfiles in tracked directories
```

**Shell completion:**

```bash
dotz --install-completion    # Enable tab completion
```

### Configuration Management

Manage file patterns and search settings:

```bash
dotz config show              # Show current configuration
dotz config list-patterns     # List file patterns
dotz config add-pattern "*.py"           # Include Python files
dotz config add-pattern "*.log" --type exclude  # Exclude log files
dotz config remove-pattern "*.py"        # Remove pattern
dotz config set search_settings.recursive false  # Disable recursion
dotz config reset             # Reset to defaults
dotz config help              # Show detailed help
```



## Project Structure

```text
dotz/
├── src/
│   └── dotz/
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

The `.git` folder is created inside `~/.dotz/repo` once you initialize dotz.



## Configuration

dotz uses configurable file patterns to determine which files to track. The configuration is stored in `~/.dotz/config.json`.

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

Use the `dotz config` commands to customize which files are tracked:

```bash
# Add Python files to tracking
dotz config add-pattern "*.py"

# Exclude compiled Python files  
dotz config add-pattern "*.pyc" --type exclude

# Disable recursive search
dotz config set search_settings.recursive false
```



## Testing

dotz has a comprehensive test suite to ensure reliability and catch regressions. Contributors are encouraged to run tests before submitting changes.

### Running Tests

**Quick test run:**

```bash
pip install pytest
pytest
```

**With coverage:**

```bash
pytest --cov=dotz
```

### Test Categories

The project includes **148 passing tests** covering:

* **CLI commands**: All dotz commands and options
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
pytest --cov=dotz             # Run tests with coverage report
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

All tests run in isolated temporary environments to prevent interference with your actual dotz configuration.



## Roadmap

dotz is actively developed as a personal project with community input welcome. Here are some areas being explored:

### Planned Features

* **Cross-platform support**: Extend beyond Linux to macOS
* **Plugin system**: Allow custom extensions and integrations
* **Advanced conflict resolution**: Better handling of merge conflicts
* **Performance optimizations**: Faster operations for large dotfile collections
* **Enhanced CLI**: More interactive commands and better user experience



## Contributing

Contributions are welcome!

### Ways to Contribute

* **Report bugs**: Found an issue? [Open a bug report](https://github.com/tTrmc/dotz/issues/new?labels=bug&template=bug_report.md)
* **Request features**: Have an idea? [Submit a feature request](https://github.com/tTrmc/dotz/issues/new?labels=enhancement&template=feature_request.md)
* **Improve documentation**: Help make the docs clearer and more comprehensive
* **Submit code**: Fix bugs or implement new features with a pull request
* **Review PRs**: Help review and test pull requests from other contributors
* **Share feedback**: Let me know how dotz works for you and what could be better

### Getting Started

1. **Fork the repository** and clone it locally
2. **Set up development environment**:

   ```bash
   git clone https://github.com/yourusername/dotz.git
   cd dotz
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
* Browse [existing issues](https://github.com/tTrmc/dotz/issues) to see what needs work
* Join discussions in [pull requests](https://github.com/tTrmc/dotz/pulls)
* Feel free to ask questions in issues or discussions



## Support

### Getting Help

* **Documentation**: Check this README and the built-in help (`dotz --help`)
* **Issues**: [Search existing issues](https://github.com/tTrmc/dotz/issues) or create a new one
* **Troubleshooting**: Use `dotz diagnose` for common problems

### Reporting Issues

When reporting bugs, please include:

* Your operating system and Python version
* dotz version (`dotz version`)
* Steps to reproduce the issue
* Expected vs. actual behavior
* Any error messages or logs



## Acknowledgments

This project has benefited from the contributions and support of the following people:

### Contributors

[![Contributors](https://contrib.rocks/image?repo=tTrmc/dotz)](https://github.com/tTrmc/dotz/graphs/contributors)



## License

This project is distributed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

By contributing to dotz, you agree that your contributions will be licensed under the same license.


