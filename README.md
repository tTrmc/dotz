# dotz

> Sync your dotfiles across machines with Git

If you've ever spent time setting up your perfect shell, vim, or desktop configuration, you know the pain of losing it when you switch computers. dotz helps you backup your dotfiles (`.bashrc`, `.vimrc`, etc.) to a Git repository so you can quickly restore your setup on any machine.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tTrmc/dotz/pulls)

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Getting Started](#getting-started)
* [Usage](#usage)
* [Project Structure](#project-structure)
* [Configuration](#configuration)
* [Testing](#testing)
* [Contributing](#contributing)
* [Support](#support)
* [Acknowledgments](#acknowledgments)
* [License](#license)

## Features

* **Backup your dotfiles**: Keep your configuration files in Git with full version history
* **Sync across machines**: Pull your configs on any computer and get your environment back quickly
* **Smart file detection**: Automatically finds common config files (`.bashrc`, `.vimrc`, `.config/*`)
* **Templates and profiles**: Save and share different setups for work, personal use, or specific projects
* **File watching**: Automatically track new config files as you create them
* **GUI available**: Use the command line or a graphical interface
* **Safe and secure**: Works with private Git repositories to keep your configs safe

## Installation

### Basic Installation

**From PyPI:**

```bash
pip install dotz           # Basic version
pip install dotz[gui]      # With graphical interface
```

**Using pipx (recommended for isolation):**

```bash
# Install pipx if you don't have it
sudo apt install pipx           # Debian/Ubuntu
sudo pacman -S python-pipx      # Arch Linux

# Install dotz
pipx install dotz[gui]
```

### Development Setup

```bash
git clone https://github.com/tTrmc/dotz.git
cd dotz
./setup-dev.sh  # Creates virtual environment and installs dependencies
```

### Check Installation

```bash
dotz --help
```

**Requirements:**

* Python 3.9 or newer
* Git

**Security Note:**
Never use public Git repositories with dotz. Your dotfiles contain sensitive information like SSH keys, API tokens, and personal configurations. Always use private repositories.

## Getting Started

### Set up your first repository

```bash
# Local repository only
dotz init

# With a private remote repository (recommended)
dotz init --remote git@github.com:yourusername/my-dotfiles.git
```

### Add some config files

```bash
# Add your shell config
dotz add .bashrc

# Add your entire .config directory
dotz add .config

# Add a file and push it immediately
dotz add .vimrc --push
```

### Sync to another machine

```bash
# Get the latest changes
dotz pull

# Send your changes
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

### Graphical Interface

**Launch GUI:**

```bash
dotz gui           # Open the Qt6-based graphical interface
```

The GUI provides:

* **Dashboard**: Repository status and quick actions
* **File Management**: Visual file browser with add/remove capabilities
* **Settings**: Configuration management with pattern editor
* **Repository Setup**: Interactive initialization wizard

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

### Template Management

Create and manage reusable dotfile configurations:

```bash
# Create templates
dotz template create work -d "Work environment setup"
dotz template create minimal --file .bashrc --file .vimrc

# List and view templates
dotz template list            # List all templates
dotz template list --verbose  # Show detailed information
dotz template info work       # Show template details

# Apply templates
dotz template apply work      # Apply template (overwrite files)
dotz template apply work --merge  # Apply without overwriting existing files

# Share templates
dotz template export work -o work-setup.tar.gz  # Export as archive
dotz template import shared-config.tar.gz       # Import from archive

# Clean up
dotz template delete old-template  # Delete template
dotz template help            # Show detailed help
```

### Profile Management

Switch between complete dotfile environments:

```bash
# Create profiles
dotz profile create work -d "Work setup" -e work
dotz profile create personal --copy-from work  # Copy from existing profile

# List and view profiles
dotz profile list             # List all profiles
dotz profile list --verbose  # Show detailed information
dotz profile current          # Show active profile
dotz profile info work        # Show profile details

# Switch profiles
dotz profile switch work      # Switch to work profile
dotz profile switch personal --no-backup  # Switch without saving current state

# Clean up
dotz profile delete old-profile  # Delete profile
dotz profile help             # Show detailed help
```

**Templates vs Profiles:**

* **Templates**: Snapshots of specific files that can be applied to any repository
* **Profiles**: Complete environments including all files, configuration, and state

**When to use each:**

* **Templates**: Save working configurations, share setups, quick file restoration
* **Profiles**: Work vs personal environments, machine-specific configs, project contexts

## Project Structure

```text
dotz/
├── src/
│   └── dotz/
│       ├── __init__.py
│       ├── cli.py          # Typer-based CLI entry point
│       ├── core.py         # Core logic for dotfile management
│       ├── templates.py    # Template and profile management
│       ├── watcher.py      # Watchdog-based directory watcher
│       └── gui/            # Qt6-based graphical interface
│           ├── __init__.py
│           ├── main.py     # Main GUI application window
│           └── widgets/    # Individual GUI components
│               ├── dashboard.py   # Status and quick actions
│               ├── files.py       # File management interface
│               ├── settings.py    # Configuration editor
│               └── init.py        # Repository setup wizard
├── tests/
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_cli.py         # CLI command tests
│   ├── test_cli_config.py  # Configuration command tests
│   ├── test_core.py        # Core functionality tests
│   ├── test_templates.py   # Template and profile tests
│   ├── test_templates_cli.py # Template/profile CLI tests
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

dotz includes tests to make sure everything works correctly. If you're contributing code, please run the tests.

### Running Tests

```bash
# Basic test run
pytest

# With coverage report
pytest --cov=dotz
```

### Test Coverage

We have 161 tests covering:

* All CLI commands and options
* File management and Git operations
* Configuration and pattern matching
* File watching and error handling
* GUI components (when available)

### For Contributors

```bash
# Install with development dependencies
pip install -e ".[dev,test]"

# Run tests with verbose output
pytest -v

# Run with coverage and HTML report
make test-cov
```

All tests run in isolated environments so they won't mess with your actual dotz setup.

## Contributing

Contributions are welcome!

### Ways to Contribute

* **Report bugs**: Found an issue? [Open a bug report](https://github.com/tTrmc/dotz/issues/new?labels=bug&template=bug_report.md)
* **Request features**: Have an idea? [Submit a feature request](https://github.com/tTrmc/dotz/issues/new?labels=enhancement&template=feature_request.md)
* **Improve documentation**: Help make the docs clearer and more comprehensive
* **Submit code**: Fix bugs or implement new features with a pull request
* **Review PRs**: Help review and test pull requests from other contributors
* **Share feedback**: Let me know how dotz works for you and what could be better

### Contributing Code

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
