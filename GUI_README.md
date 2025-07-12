# dotz GUI Setup

This document describes the Qt6/PySide6 GUI expansion for dotz.

## Installation

To use the dotz GUI, install the GUI dependencies:

```bash
# Install with GUI support
pip install -e ".[gui]"

# Or install PySide6 separately
pip install PySide6
```

## Usage

### Launch GUI from CLI

```bash
# Launch the graphical interface
dotz gui
```

### Direct GUI launcher

```bash
# Alternative launcher
dotz-gui
```

## Features

The dotz GUI provides a user-friendly interface for managing your dotfiles:

### Dashboard Tab

- **Repository Status**: Shows current state of your repository
- **Quick Actions**: Push, pull, and refresh buttons
- **File Lists**: View tracked and modified files

### Files Tab

- **Add Files**: Browse and add individual files or directories
- **File Management**: Restore or delete tracked files
- **Multi-selection**: Select multiple files for batch operations

### Settings Tab

- **Search Settings**: Configure recursive search, case sensitivity, etc.
- **File Patterns**: Manage include/exclude patterns for dotfile detection
- **Raw Configuration**: Direct JSON editing of configuration

### Initialization

If dotz is not yet initialized, the GUI will show a setup wizard to:

- Initialize the dotz repository
- Optionally configure a remote Git repository
- Display setup progress and status

## Development

### Project Structure

```text
src/dotz/gui/
├── __init__.py          # GUI module initialization
├── main.py              # Main application window and entry point
└── widgets/
    ├── __init__.py      # Widget module
    ├── dashboard.py     # Dashboard widget
    ├── files.py         # File management widget
    ├── init.py          # Initialization widget
    └── settings.py      # Settings configuration widget
```

### Dependencies

- **PySide6**: Qt6 Python bindings
- **Qt6**: Modern UI framework
- **Threading**: Background operations to keep UI responsive

### Architecture

- **Main Window**: `DotzMainWindow` - Central application window
- **Tab System**: Organized into functional tabs
- **Worker Threads**: Long-running operations run in separate threads
- **Signal/Slot**: Qt's event system for communication between components

## Requirements

- Python 3.9+
- PySide6 6.5.0+
- Display server (X11, Wayland, etc.) for GUI functionality

## Notes

- The GUI gracefully handles missing dependencies
- All core dotz functionality remains available via CLI
- GUI operations use the same core functions as the CLI
- Settings are synchronized between GUI and CLI interfaces
