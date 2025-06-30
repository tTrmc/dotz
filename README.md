# dotkeep

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Last Commit](https://img.shields.io/github/last-commit/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/commits/main)

A minimal **dotfiles** manager for Linux, backed by Git. **dotkeep** simplifies tracking, versioning, and synchronizing your configuration files across machines.

---

## Features

* **Easy setup**: Initialize a local dotkeep repository with a single command.
* **Git-based**: Provides full version history, branching, and remote synchronization.
* **File management**: Add and remove dotfiles with automatic symlinking.
* **Recursive directory support**: Add all dotfiles (optionally recursively) from a directory.
* **Tracked directories**: Only directories you add are watched for new dotfiles.
* **Status overview**: Display untracked, modified, and staged files at a glance.
* **Diagnostics**: Built-in `diagnose` command for troubleshooting.
* **Shell completion**: Tab-completion for all commands and options.
* **Portable**: Requires only Python 3.8+ and Git.

---

## Installation

### Clone the repository

```bash
git clone https://github.com/tTrmc/dotkeep.git
cd dotkeep
```

### For developers (editable install)

> **Recommended for development**

Use a virtual environment to avoid conflicts with your system Python:

```bash
python -m venv .venv         # Create virtual environment
source .venv/bin/activate    # Activate virtual environment
pip install -e .             # Install in editable mode
```

Installing in editable mode (`-e`) installs the `dotkeep` CLI inside the virtual environment and allows your code changes to take effect immediately.

---

### For users (global CLI install)

> **Recommended for end users**

Use `pipx` to install `dotkeep` globally in an isolated environment:

```bash
# Install pipx if you do not have it:
sudo pacman -S python-pipx      # Arch Linux
# or
sudo apt install pipx           # Debian/Ubuntu

# Ensure pipx is set up:
pipx ensurepath

# Install dotkeep globally:
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
│   └── test_cli.py         # Pytest-based CLI and core tests
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # Project documentation
├── LICENSE                 # GPL-3.0-or-later license
├── CONTRIBUTING.md         # Contribution guidelines
└── .gitignore              # Files and directories to exclude
```

The `.git` folder is created inside `~/.dotkeep/repo` once you initialize dotkeep.

---

## Testing

To run the test suite (requires [pytest](https://pytest.org/)):

```bash
pip install pytest
pytest
```

This will discover and run all tests in the `tests/` directory, including `test_cli.py`.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, report bugs, or suggest features.

---

## License

This project is distributed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

---
