"""
Comprehensive test configuration and fixtures for dotz test suite.

This module provides shared fixtures for isolated testing environments,
mock objects, sample data, and test utilities across all test categories.
"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from git import Repo
from git.objects import Commit

# Import dotz modules
from dotz import cli, core, templates, watcher

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "gui: marks tests as GUI tests requiring display"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location."""
    for item in items:
        # Mark GUI tests
        if "gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)

        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def test_session_id():
    """Generate unique session ID for test isolation."""
    return f"dotz_test_{int(time.time())}"


@pytest.fixture
def isolated_home(tmp_path, monkeypatch, test_session_id):
    """
    Create completely isolated home directory for testing.

    This fixture ensures complete isolation between tests by:
    - Creating a temporary home directory
    - Setting HOME environment variable
    - Updating dotz internal paths
    - Providing cleanup after test completion
    """
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Backup original environment
    original_home = os.environ.get("HOME")
    original_xdg_config = os.environ.get("XDG_CONFIG_HOME")

    # Set isolated environment
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home_dir / ".config"))

    # Update dotz paths to use isolated home
    monkeypatch.setattr(core, "HOME_DIR", home_dir)
    core.update_paths(home_dir)

    # Create common directories
    (home_dir / ".config").mkdir(exist_ok=True)
    (home_dir / ".local" / "share").mkdir(parents=True, exist_ok=True)

    yield home_dir

    # Cleanup is automatic with tmp_path


@pytest.fixture
def mock_home(isolated_home):
    """
    Create a home directory populated with sample dotfiles.

    Provides a realistic home environment with common dotfiles
    for testing file detection and management operations.
    """
    # Create sample dotfiles
    dotfiles = {
        ".bashrc": "# Sample bashrc\\nexport PATH=$PATH:/usr/local/bin\\nalias ll='ls -la'\\n",
        ".vimrc": '" Sample vimrc\\nset number\\nset tabstop=4\\nsyntax on\\n',
        ".gitconfig": "[user]\\n    name = Test User\\n    email = test@example.com\\n",
        ".profile": "# Sample profile\\nexport EDITOR=vim\\n",
        ".zshrc": "# Sample zshrc\\nautoload -U compinit\\ncompinit\\n",
    }

    for filename, content in dotfiles.items():
        (isolated_home / filename).write_text(content)

    # Create config directories
    config_dir = isolated_home / ".config"
    config_files = {
        "git/config": "[core]\\n    editor = vim\\n",
        "htop/htoprc": "# htop configuration\\n",
        "tmux/tmux.conf": "# tmux configuration\\nset -g mouse on\\n",
        "nvim/init.vim": '" neovim configuration\\nset number\\n',
    }

    for config_path, content in config_files.items():
        full_path = config_dir / config_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    return isolated_home


# ============================================================================
# GIT REPOSITORY FIXTURES
# ============================================================================


@pytest.fixture
def mock_git_repo():
    """
    Create a comprehensive mock Git repository.

    Provides a fully mocked Repo object with realistic behavior
    for testing Git operations without actual Git commands.
    """
    repo = Mock(spec=Repo)

    # Basic repository state
    repo.is_dirty.return_value = False
    repo.git.ls_files.return_value = ""
    repo.git.status.return_value = (
        "On branch main\\nnothing to commit, working tree clean"
    )
    repo.untracked_files = []
    repo.bare = False
    repo.git_dir = "/tmp/test_repo/.git"
    repo.working_dir = "/tmp/test_repo"

    # Index operations
    mock_index = Mock()
    mock_index.add.return_value = None
    mock_index.commit.return_value = Mock(hexsha="abc123def456")
    mock_index.diff.return_value = []
    repo.index = mock_index

    # Branch operations
    mock_branch = Mock()
    mock_branch.name = "main"
    mock_branch.tracking_branch.return_value = None
    repo.active_branch = mock_branch
    repo.heads = [mock_branch]

    # Remote operations
    mock_remote = Mock()
    mock_remote.name = "origin"
    mock_remote.url = "git@github.com:user/dotfiles.git"
    mock_remote.pull.return_value = []
    mock_remote.push.return_value = []
    repo.remotes = [mock_remote]
    repo.remote.return_value = mock_remote

    # Diff operations
    repo.head.commit.diff.return_value = []

    return repo


@pytest.fixture
def real_git_repo(tmp_path):
    """
    Create a real Git repository for integration testing.

    Provides an actual Git repository for testing operations
    that require real Git functionality.
    """
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize repository
    repo = Repo.init(str(repo_dir))

    # Configure user for commits
    with repo.config_writer() as git_config:
        git_config.set_value("user", "name", "Test User")
        git_config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repository\\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return repo


@pytest.fixture
def initialized_dotz_repo(mock_home):
    """
    Create a fully initialized dotz repository.

    Provides a complete dotz setup with:
    - .dotz directory structure
    - Git repository
    - Configuration files
    - Sample tracked files
    """
    dotz_dir = mock_home / ".dotz"
    dotz_dir.mkdir()

    # Create repository directory
    repo_dir = dotz_dir / "repo"
    repo_dir.mkdir()

    # Initialize Git repository
    repo = Repo.init(str(repo_dir))

    # Configure Git user
    with repo.config_writer() as git_config:
        git_config.set_value("user", "name", "Test User")
        git_config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme = repo_dir / "README.md"
    readme.write_text("# Dotz Repository\\n\\nThis repository contains dotfiles.\\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial dotz repository")

    # Create configuration
    config_file = dotz_dir / "config.json"
    config_data = {
        "file_patterns": {
            "include": [
                ".*",
                "*.conf",
                "*.config",
                "*.cfg",
                "*.ini",
                "*.toml",
                "*.yaml",
                "*.yml",
                "*.json",
            ],
            "exclude": [
                ".DS_Store",
                ".Trash*",
                ".cache",
                ".git",
                ".svn",
                "*.log",
                "*.tmp",
                "*.lock",
            ],
        },
        "search_settings": {
            "recursive": True,
            "case_sensitive": False,
            "follow_symlinks": False,
        },
    }
    config_file.write_text(json.dumps(config_data, indent=2))

    # Create tracked directories file
    tracked_dirs_file = dotz_dir / "tracked_dirs.json"
    tracked_dirs_file.write_text("[]")

    # Create backups directory
    backup_dir = dotz_dir / "backups"
    backup_dir.mkdir()

    return dotz_dir


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def default_config():
    """Provide default dotz configuration."""
    return {
        "file_patterns": {
            "include": [
                ".*",
                "*.conf",
                "*.config",
                "*.cfg",
                "*.ini",
                "*.toml",
                "*.yaml",
                "*.yml",
                "*.json",
            ],
            "exclude": [
                ".DS_Store",
                ".Trash*",
                ".cache",
                ".git",
                ".svn",
                "*.log",
                "*.tmp",
                "*.lock",
            ],
        },
        "search_settings": {
            "recursive": True,
            "case_sensitive": False,
            "follow_symlinks": False,
        },
    }


@pytest.fixture
def custom_config():
    """Provide custom dotz configuration for testing."""
    return {
        "file_patterns": {
            "include": [".*", "*.py", "*.js", "*.ts"],
            "exclude": ["*.pyc", "*.pyo", "__pycache__", "node_modules"],
        },
        "search_settings": {
            "recursive": False,
            "case_sensitive": True,
            "follow_symlinks": True,
        },
    }


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_dotfiles():
    """Provide sample dotfile contents for testing."""
    return {
        ".bashrc": """# Sample bashrc configuration
export PATH=$PATH:/usr/local/bin
export EDITOR=vim
alias ll='ls -la'
alias grep='grep --color=auto'

# Custom functions
function mkcd() {
    mkdir -p "$1" && cd "$1"
}
""",
        ".vimrc": """\" Sample vim configuration
set number
set relativenumber
set tabstop=4
set shiftwidth=4
set expandtab
syntax on
colorscheme desert

\" Key mappings
nnoremap <leader>w :w<CR>
nnoremap <leader>q :q<CR>
""",
        ".gitconfig": """[user]
    name = Test User
    email = test@example.com

[core]
    editor = vim
    autocrlf = input

[alias]
    st = status
    co = checkout
    br = branch
    cm = commit
    lg = log --oneline --graph
""",
        ".tmux.conf": """# Sample tmux configuration
set -g prefix C-a
unbind C-b
bind C-a send-prefix

set -g mouse on
set -g base-index 1
setw -g pane-base-index 1

# Key bindings
bind r source-file ~/.tmux.conf \\; display "Config reloaded!"
bind | split-window -h
bind - split-window -v
""",
    }


@pytest.fixture
def sample_config_files():
    """Provide sample configuration files for testing."""
    return {
        ".config/git/config": """[user]
    name = Test User
    email = test@example.com
[core]
    editor = vim
""",
        ".config/htop/htoprc": """# htop configuration
tree_view=1
hide_kernel_threads=1
hide_userland_threads=1
shadow_other_users=1
""",
        ".config/nvim/init.vim": """\" Neovim configuration
set number
set relativenumber
set tabstop=2
set shiftwidth=2
syntax on

\" Plugin management
call plug#begin()
Plug 'preservim/nerdtree'
call plug#end()
""",
        ".ssh/config": """Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa

Host myserver
    HostName example.com
    User myuser
    Port 2222
""",
    }


# ============================================================================
# TEMPLATE AND PROFILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_template_data():
    """Provide sample template data for testing."""
    return {
        "name": "development",
        "description": "Development environment setup",
        "files": [".bashrc", ".vimrc", ".gitconfig"],
        "metadata": {
            "created": "2024-01-01T00:00:00Z",
            "author": "Test User",
            "version": "1.0.0",
        },
    }


@pytest.fixture
def sample_profile_data():
    """Provide sample profile data for testing."""
    return {
        "name": "work",
        "description": "Work environment profile",
        "template": "development",
        "environment": {"GIT_AUTHOR_EMAIL": "work@company.com", "EDITOR": "code"},
        "metadata": {
            "created": "2024-01-01T00:00:00Z",
            "last_used": "2024-01-02T10:30:00Z",
        },
    }


# ============================================================================
# GUI TESTING FIXTURES
# ============================================================================


@pytest.fixture
def qtbot_skip_if_no_display():
    """Skip GUI tests if no display is available."""
    try:
        import os

        if (
            os.environ.get("DISPLAY") is None
            and os.environ.get("WAYLAND_DISPLAY") is None
        ):
            pytest.skip("No display available for GUI tests")
    except ImportError:
        pytest.skip("PySide6 not available for GUI tests")


@pytest.fixture
def mock_qt_application():
    """Provide a mock Qt application for testing."""
    try:
        import sys

        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        yield app

        # Cleanup
        if app:
            app.quit()
    except ImportError:
        pytest.skip("PySide6 not available")


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================


@pytest.fixture
def large_repo_setup(tmp_path):
    """Create a large repository setup for performance testing."""
    home_dir = tmp_path / "large_home"
    home_dir.mkdir()

    # Create many dotfiles
    for i in range(1000):
        dotfile = home_dir / f".config{i:04d}"
        dotfile.write_text(f"# Configuration file {i}\\nvalue={i}\\n")

    # Create nested directory structure
    for i in range(100):
        config_dir = home_dir / ".config" / f"app{i:03d}"
        config_dir.mkdir(parents=True, exist_ok=True)
        for j in range(10):
            config_file = config_dir / f"config{j}.conf"
            config_file.write_text(f"[section{j}]\\nkey=value{j}\\n")

    return home_dir


@pytest.fixture(scope="session")
def benchmark_repo(tmp_path_factory):
    """Create a repository for benchmarking operations."""
    repo_dir = tmp_path_factory.mktemp("benchmark_repo")

    # Initialize Git repository
    repo = Repo.init(str(repo_dir))

    # Configure Git
    with repo.config_writer() as git_config:
        git_config.set_value("user", "name", "Benchmark User")
        git_config.set_value("user", "email", "benchmark@example.com")

    # Create benchmark files
    for i in range(1000):
        test_file = repo_dir / f"file{i:04d}.txt"
        test_file.write_text(f"Test content for file {i}\\n" * 100)
        if i % 100 == 0:
            repo.index.add([str(test_file)])
            repo.index.commit(f"Add batch {i//100}")

    return repo_dir


# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture
def capture_logs(caplog):
    """Capture and provide access to log messages."""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def mock_time():
    """Provide a mock time function for deterministic testing."""
    with patch("time.time") as mock:
        mock.return_value = 1609459200.0  # 2021-01-01 00:00:00 UTC
        yield mock


@pytest.fixture
def mock_datetime():
    """Provide a mock datetime for deterministic testing."""
    from datetime import datetime

    with patch("dotz.core.datetime") as mock:
        mock.now.return_value = datetime(2021, 1, 1, 12, 0, 0)
        mock.datetime = datetime
        yield mock


# ============================================================================
# CLEANUP AND VALIDATION FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Ensure clean environment before and after each test."""
    # Pre-test cleanup
    yield
    # Post-test cleanup is handled by tmp_path and monkeypatch fixtures


@pytest.fixture
def validate_no_side_effects(isolated_home):
    """Validate that tests don't have side effects on the real filesystem."""
    import os

    real_home = Path.home()

    yield

    # Ensure no modifications to real home directory
    assert (
        not (real_home / ".dotz").exists()
        or (real_home / ".dotz").stat().st_mtime < time.time() - 60
    )
