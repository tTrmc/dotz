# dotkeep

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Last Commit](https://img.shields.io/github/last-commit/tTrmc/dotkeep.svg)](https://github.com/tTrmc/dotkeep/commits/main)

A minimal **dotfiles** manager for Linux, backed by Git. **dotkeep** simplifies tracking, versioning, and synchronizing your configuration files across machines.

---

## Features

* **Easy setup**: Initialize a local dotkeep repository with a single command.
* **Git-based**: Provides full version history, branching, and remote synchronization.
* **File management**: Add and remove dotfiles with automatic symlinking.
* **Status overview**: Display untracked, modified, and staged files at a glance.
* **Portable**: Requires only Python 3.8+ and Git.

---

## Installation

1. **Clone and install**

   ```bash
   git clone https://github.com/tTrmc/dotkeep.git
   cd dotkeep
   pip install -e .
   ```

   Installing in editable mode (`-e`) installs the `dotkeep` CLI globally and allows code changes to take effect immediately.

2. **Verify installation**

   ```bash
   dotkeep --help
   ```

**Requirements:** Python 3.8 or newer, Git

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

### Add a dotfile

Copy, commit, and symlink a configuration file from your home directory:

```bash
# Add without pushing
dotkeep add .bashrc

# Add and push to remote
dotkeep add .bashrc --push
```

### Remove a dotfile

Unlink, delete, and commit the removal of a managed dotfile:

```bash
# Remove without pushing
dotkeep delete .vimrc

# Remove and push to remote
dotkeep delete .vimrc --push
```

### Status

List untracked, modified, and staged files in your dotkeep repository:

```bash
dotkeep status
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

---

## Project Structure

```
dotkeep/
├── src/                # Source code
│   └── cli.py          # Typer-based CLI entry point
├── pyproject.toml      # Project metadata and dependencies
├── README.md           # Project documentation
├── LICENSE             # GPL-3.0-or-later license
└── .gitignore          # Files and directories to exclude
```

The `.git` folder is created inside `~/.dotkeep/repo` once you initialize dotkeep.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/YourFeature`.
3. Commit your changes: `git commit -m 'Add new feature'`.
4. Push to the branch: `git push origin feature/YourFeature`.
5. Open a Pull Request.

Please ensure your code follows [PEP 8](https://peps.python.org/pep-0008/) and includes relevant tests.

---

## License

This project is distributed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

---
