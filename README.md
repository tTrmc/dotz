# dotz

> Git-backed dotfiles manager for Linux

Keep your configuration files synced across machines with Git. Back up your `.bashrc`, `.vimrc`, and other dotfiles with full version history.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tTrmc/dotz/pulls)

## Features

- **Git-backed**: Full version history for your configs
- **Cross-machine sync**: Pull your setup anywhere
- **Smart detection**: Finds common dotfiles automatically
- **Templates & profiles**: Different setups for work/personal
- **File watching**: Auto-track new config files
- **GUI & CLI**: Use what you prefer
- **Secure**: Works with private repositories

## Quick Start

### Install

```bash
# Basic installation
pip install dotz

# With GUI support
pip install dotz[gui]

# Using pipx (recommended)
pipx install dotz[gui]
```

### Initialize

```bash
# Local repository
dotz init

# With remote backup (recommended)
dotz init --remote git@github.com:yourusername/my-dotfiles.git
```

### Basic Usage

```bash
# Add files
dotz add .bashrc
dotz add .config

# Sync changes
dotz pull    # Get updates
dotz push    # Send updates

# View status
dotz status
dotz list-files
```

## Commands

### File Management
```bash
dotz add <file>              # Add file/directory
dotz delete <file>           # Remove from tracking
dotz restore <file>          # Restore from repository
dotz watch                   # Auto-track new files
```

### Repository
```bash
dotz init [--remote URL]     # Initialize repository
dotz pull                    # Fetch and merge changes
dotz push                    # Push local commits
dotz status                  # Show repository status
```

### Configuration
```bash
dotz config show            # View current config
dotz config add-pattern "*.py"        # Include Python files
dotz config add-pattern "*.log" --type exclude  # Exclude logs
```

### Templates & Profiles
```bash
# Templates - save specific file configurations
dotz template create work --file .bashrc --file .vimrc
dotz template apply work

# Profiles - complete environment setups
dotz profile create work-env
dotz profile switch work-env
```

### GUI
```bash
dotz gui                     # Launch graphical interface
```

## Configuration

dotz automatically tracks common dotfiles but you can customize patterns:

**Default includes:** `.*`, `*.conf`, `*.config`, `*.toml`, `*.yaml`, `*.json`  
**Default excludes:** `.git`, `.cache`, `*.log`, `*.tmp`, `.DS_Store`

Modify patterns with `dotz config` commands.

## Development

```bash
git clone https://github.com/tTrmc/dotz.git
cd dotz
./setup-dev.sh              # Setup dev environment
make test                    # Run tests
make lint                    # Check code quality
```

## Security Note

**Always use private repositories.** Dotfiles contain sensitive information like SSH keys and API tokens.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- Report bugs: [Issues](https://github.com/tTrmc/dotz/issues)
- Request features: [Feature requests](https://github.com/tTrmc/dotz/issues)
- Submit code: [Pull requests](https://github.com/tTrmc/dotz/pulls)

## License

GPL-3.0-or-later