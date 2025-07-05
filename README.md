[![PyPI version](https://badge.fury.io/py/dotkeep.svg)](https://badge.fury.io/py/dotkeep)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![CI](https://github.com/tTrmc/dotkeep/workflows/CI/badge.svg)](https://github.com/tTrmc/dotkeep/actions)
[![Last Commit](https://img.shields.io/github/last-commit/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/issues)

<div>
  <img src="dotlogo.png" alt="dotkeep logo" width="300" align="left" style="margin-right: 20px; margin-bottom: 10px;"/>
  <div style="margin-left: 320px; padding-top: 90px;">
    <h3 style="margin-top: 0;">A minimal <strong>dotfiles</strong> manager for Linux, backed by Git.</h3>
    <p><em>dotkeep</em> simplifies tracking, versioning, and synchronizing your configuration files across machines.</p>
  </div>
</div>

<div style="clear: both;"></div>

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
* **Portable**: Requires only Python 3.8+ and Git.

---

## Installation

### From PyPI (Recommended)

```bash
pip install dotkeep
```

### From source

#### Clone the repository

```bash
git clone https://github.com/tTrmc/dotkeep.git
cd dotkeep
```

#### For developers (editable install)

> **Recommended for development**

**Quick setup with the provided script:**

```bash
git clone https://github.com/tTrmc/dotkeep.git
cd dotkeep
./setup-dev.sh  # Sets up virtual environment and installs dependencies
```

**Manual setup:**

Use a virtual environment to avoid conflicts with your system Python:

```bash
python -m venv .venv         # Create virtual environment
source .venv/bin/activate    # Activate virtual environment
pip install -e ".[dev,test]" # Install with all dependencies
```

Installing in editable mode (`-e`) installs the `dotkeep` CLI inside the virtual environment and allows your code changes to take effect immediately.

---

### For users (global CLI install)

> **Recommended for end users**

**From PyPI (simplest):**
```bash
pip install dotkeep
```

**Using pipx (isolated environment):**
```bash
# Install pipx if you do not have it:
sudo pacman -S python-pipx      # Arch Linux
# or
sudo apt install pipx           # Debian/Ubuntu

# Ensure pipx is set up:
pipx ensurepath

# Install dotkeep globally:
pipx install dotkeep
```

**From source:**
```bash
pipx install git+https://github.com/tTrmc/dotkeep.git
```

---

### Verify installation

```bash
dotkeep --help
```

---

**Requirements:**

* Python **3.8** or newer
* Git
* `pipx` (recommended for global CLI use)

---

## Usage

### Initialize

Create your dotkeep repository at `~/.dotkeep/repo` (where the `.git` directory resides) and optionally add a remote:

```bash
# Initialize locally
dotkeep init

# Initialize with remote
dotkeep init --remote git@github.com:yourusername/dotkeep.git
```

### Add a dotfile or directory

Copy, commit, and symlink a configuration file or all dotfiles in a directory from your home directory:

```bash
# Add a single file without pushing
dotkeep add .bashrc

# Add and push to remote
dotkeep add .bashrc --push

# Add all dotfiles in a directory (recursively, default)
dotkeep add .config

# Add only top-level dotfiles in a directory (non-recursive)
dotkeep add .config --no-recursive
```

### Remove a dotfile

Unlink, delete, and commit the removal of a managed dotfile:

```bash
# Remove without pushing
dotkeep delete .vimrc

# Remove and push to remote
dotkeep delete .vimrc --push
```

### Restore a dotfile

Restore a dotfile or directory from the dotkeep repository to your home directory:

```bash
dotkeep restore .vimrc
dotkeep restore .config --push
```

### Status

List untracked, modified, and staged files in your dotkeep repository:

```bash
dotkeep status
```

### List tracked files

Show all files currently tracked by dotkeep:

```bash
dotkeep list-files
```

### Pull

Fetch and merge the latest changes from the remote into your local dotkeep repository:

```bash
dotkeep pull
```

### Push

Push all local commits (including added or deleted dotfiles) to the remote:

```bash
dotkeep push
```

### Watch for new dotfiles

Automatically add new dotfiles created in tracked directories:

```bash
dotkeep watch
```

### Configuration management

Manage file patterns and search settings:

```bash
# Show current configuration
dotkeep config show

# List current file patterns
dotkeep config list-patterns

# Add a file pattern to include
dotkeep config add-pattern "*.py"

# Add a file pattern to exclude
dotkeep config add-pattern "*.log" --type exclude

# Remove a pattern
dotkeep config remove-pattern "*.py"

# Set configuration values
dotkeep config set search_settings.recursive false

# Reset configuration to defaults
dotkeep config reset

# Show detailed configuration help
dotkeep config help
```

### Diagnostics

Diagnose common issues with your dotkeep setup and git repository:

```bash
dotkeep diagnose
```

### Shell completion

Enable tab-completion for your shell:

```bash
dotkeep --install-completion
```
Follow the printed instructions for your shell (bash, zsh, fish, etc.).

### Show version

```bash
dotkeep version
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
- `.*` - All dotfiles (files starting with `.`)
- `*.conf`, `*.config`, `*.cfg`, `*.ini` - Configuration files
- `*.toml`, `*.yaml`, `*.yml`, `*.json` - Structured config files

**Exclude patterns** (files that will be ignored):
- `.DS_Store`, `.Trash*` - System files
- `.cache`, `.git`, `.svn` - Cache and VCS directories  
- `*.log`, `*.tmp` - Temporary files

### Search Settings

- `recursive`: Search subdirectories recursively (default: `true`)
- `case_sensitive`: Case-sensitive pattern matching (default: `false`)
- `follow_symlinks`: Follow symbolic links during search (default: `false`)

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

- **CLI commands**: All dotkeep commands and options
- **Core functionality**: File management, Git operations, configuration
- **Configuration management**: Pattern matching, settings, validation  
- **File watching**: Automatic detection and tracking of new files
- **Error handling**: Graceful handling of edge cases and failures
- **Environment isolation**: Tests run in isolated temporary environments

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
