[![PyPI version](https://badge.fury.io/py/dotkeep.svg)](https://badge.fury.io/py/dotkeep)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![CI](https://github.com/tTrmc/dotkeep/workflows/CI/badge.svg)](https://github.com/tTrmc/dotkeep/actions)
[![Last Commit](https://img.shields.io/github/last-commit/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/issues)

---

> **dotkeep is a minimal, Git-backed dotfiles manager for Linux, focused on secure, easy, and portable configuration management across machines.**

<div align="center">
  <img width="300" src="dotlogo.png" alt="dotkeep">
  <h3>
    A minimal <strong>dotfiles</strong> manager for Linux, backed by Git.
  </h3>
  <p>
    <em>dotkeep</em> simplifies tracking, versioning, and synchronizing your configuration files across machines.
  </p>
</div>

---

## Why dotkeep?

Unlike generic Git workflows or manual symlink scripts, **dotkeep** automates dotfile management with:

* **Symlinking** and pattern-based inclusion/exclusion
* Safety-focused default rules to prevent accidental leaks
* Simple, consistent CLI for setup, sync, and status

**dotkeep** minimizes manual effort and reduces the risk of exposing sensitive data, while remaining fully Git-compatible and easy to adopt.

---

## Project Status

⚠️ **Actively developed — features and APIs may change. Feedback and contributions are welcome.**

---

## Community

[![Contributors welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/tTrmc/dotkeep/issues)
[![Good First Issue](https://img.shields.io/github/issues/good-first-issue/tTrmc/dotkeep)](https://github.com/tTrmc/dotkeep/labels/good%20first%20issue)

> Looking to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) and browse [good first issues](https://github.com/tTrmc/dotkeep/labels/good%20first%20issue).

---

## Features

* **Easy setup**: Initialize a local dotkeep repository with a single command.
* **Git-based**: Provides full version history, branching, and remote synchronization.
* **File management**: Add and remove dotfiles with automatic symlinking.
* **Recursive directory support**: Add all dotfiles (optionally recursively) from a directory.
* **Tracked directories**: Only directories you add are watched for new dotfiles.
* **Configurable patterns**: Customize which file types to track with include/exclude patterns.
* **Status overview**: Display untracked, modified, and staged files at a glance.
* **Configuration management**: Built-in commands to manage file patterns and search settings.
* **File watching**: Automatic detection and addition of new configuration files.
* **Diagnostics**: Built-in `diagnose` command for troubleshooting.
* **Shell completion**: Tab-completion for all commands and options.
* **Robust & testable**: Comprehensive test suite with environment isolation.
* **Portable**: Requires only Python 3.9+ and Git.

---

## Installation

### For End Users (Recommended)

**From PyPI:**

```bash
pip install dotkeep
```

**Using pipx (isolated environment):**

```bash
# Install pipx if needed
sudo apt install pipx           # Debian/Ubuntu
# or
sudo pacman -S python-pipx      # Arch Linux

# Install dotkeep
pipx install dotkeep
```

### For Developers

**Quick setup:**

```bash
git clone https://github.com/tTrmc/dotkeep.git
cd dotkeep
./setup-dev.sh  # Sets up virtual environment and installs dependencies
```

**Manual setup:**

```bash
git clone https://github.com/tTrmc/dotkeep.git
cd dotkeep
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

### Verify Installation

```bash
dotkeep --help
```

**Requirements:**

* Python 3.9 or newer
* Git

---

> \[!CAUTION]
> **NEVER use public Git repositories with dotkeep.** Your dotfiles often contain:
>
> * SSH keys and certificates
> * API tokens and passwords
> * Personal file paths and system information
> * Application configurations with sensitive data
>
> **Always use private repositories** or consider excluding sensitive files with dotkeep's pattern configuration.

---

## Quick Start

### Initialize your dotkeep repository

```bash
# Local repository only
dotkeep init

# With private remote repository (recommended)
dotkeep init --remote git@github.com:yourusername/dotfiles-private.git
```

### Add your first dotfile

```bash
# Add a single file
dotkeep add .bashrc

# Add all dotfiles in a directory
dotkeep add .config

# Add and push to remote
dotkeep add .vimrc --push
```

### Sync across machines

```bash
# Pull latest changes
dotkeep pull

# Push your changes
dotkeep push
```

---

## Usage

### Repository Management

**Initialize:**

```bash
dotkeep init                                                    # Local only
dotkeep init --remote git@github.com:user/dotfiles-private.git # With remote
```

**Sync:**

```bash
dotkeep pull    # Fetch and merge changes
dotkeep push    # Push local commits
```

### File Management

**Add files:**

```bash
dotkeep add .bashrc              # Single file
dotkeep add .config              # Directory (recursive by default)
dotkeep add .config --no-recursive  # Top-level files only
dotkeep add .vimrc --push        # Add and push
```

**Remove files:**

```bash
dotkeep delete .vimrc            # Remove file
dotkeep delete .vimrc --push     # Remove and push
```

**Restore files:**

```bash
dotkeep restore .vimrc           # Restore single file
dotkeep restore .config          # Restore directory
```

### Information Commands

```bash
dotkeep status        # Show repository status
dotkeep list-files    # List tracked files
dotkeep diagnose      # Troubleshoot issues
dotkeep version       # Show version
```

### Advanced Features

**File watching:**

```bash
dotkeep watch    # Automatically add new dotfiles in tracked directories
```

**Shell completion:**

```bash
dotkeep --install-completion    # Enable tab completion
```

### Configuration Management

Manage file patterns and search settings:

```bash
dotkeep config show              # Show current configuration
dotkeep config list-patterns     # List file patterns
dotkeep config add-pattern "*.py"           # Include Python files
dotkeep config add-pattern "*.log" --type exclude  # Exclude log files
dotkeep config remove-pattern "*.py"        # Remove pattern
dotkeep config set search_settings.recursive false  # Disable recursion
dotkeep config reset             # Reset to defaults
dotkeep config help              # Show detailed help
```

---

## Project Structure

```
dotkeep/
├── src/
│   └── dotkeep/
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

The `.git` folder is created inside `~/.dotkeep/repo` once you initialize dotkeep.

---

## Configuration

dotkeep uses configurable file patterns to determine which files to track. The configuration is stored in `~/.dotkeep/config.json`.

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

Use the `dotkeep config` commands to customize which files are tracked:

```bash
# Add Python files to tracking
dotkeep config add-pattern "*.py"

# Exclude compiled Python files  
dotkeep config add-pattern "*.pyc" --type exclude

# Disable recursive search
dotkeep config set search_settings.recursive false
```

---

## Testing

To run the test suite (requires [pytest](https://pytest.org/)):

```bash
pip install pytest
pytest
```

### Test Coverage

The project includes comprehensive tests with **73 passing tests** covering:

* **CLI commands**: All dotkeep commands and options
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
pytest --cov=dotkeep          # Run tests with coverage report
make test-cov                 # Run tests with HTML coverage report
```

**Development workflow:**

```bash
make help          # Show all available commands
make test          # Run tests
make lint          # Run code quality checks
make format        # Auto-format code
make build         # Build distribution packages
```

This will discover and run all tests in the `tests/` directory with proper environment isolation and cleanup.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, report bugs, or suggest features.

---

## License

This project is distributed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

---
