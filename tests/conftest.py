"""Test configuration and fixtures."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator
from unittest.mock import Mock

import pytest
from git import Repo

from dotz import cli, core, watcher


@pytest.fixture
def temp_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary home directory for testing."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Set HOME environment variable
    old_home = os.environ.get("HOME")
    os.environ["HOME"] = str(home_dir)

    # Update dotz paths to use the temp home
    core.update_paths(home_dir)
    watcher.update_watcher_paths(home_dir)
    cli.update_cli_paths(home_dir)

    yield home_dir

    # Restore original HOME
    if old_home:
        os.environ["HOME"] = old_home
    else:
        os.environ.pop("HOME", None)


@pytest.fixture
def mock_repo() -> Mock:
    """Create a mock Git repository."""
    repo = Mock(spec=Repo)
    repo.is_dirty.return_value = False
    repo.git.ls_files.return_value = ""
    repo.git.status.return_value = ""
    repo.untracked_files = []
    repo.index.diff.return_value = []
    repo.head.commit.diff.return_value = []
    repo.remotes = []
    repo.active_branch.name = "main"
    repo.active_branch.tracking_branch.return_value = None
    return repo


@pytest.fixture
def sample_dotfile(temp_home: Path) -> Path:
    """Create a sample dotfile for testing."""
    dotfile = temp_home / ".bashrc"
    dotfile.write_text("# Sample bashrc\nexport PATH=$PATH:/usr/local/bin\n")
    return dotfile


@pytest.fixture
def sample_config_dir(temp_home: Path) -> Path:
    """Create a sample config directory for testing."""
    config_dir = temp_home / ".config"
    config_dir.mkdir()

    # Create some config files
    (config_dir / "app.conf").write_text("[section]\nkey=value\n")
    (config_dir / "settings.json").write_text('{"theme": "dark"}\n')

    return config_dir


@pytest.fixture
def initialized_dotz(temp_home: Path) -> Path:
    """Initialize a dotz repository in temp home."""
    dotz_dir = temp_home / ".dotz"
    dotz_dir.mkdir()

    work_tree = dotz_dir / "repo"
    work_tree.mkdir()

    # Initialize git repo
    repo = Repo.init(str(work_tree))

    # Create initial commit
    (work_tree / "README.md").write_text("# Dotz repository\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create config
    config_file = dotz_dir / "config.json"
    config_file.write_text(json.dumps(core.DEFAULT_CONFIG, indent=2))

    # Create tracked dirs file
    tracked_dirs_file = dotz_dir / "tracked_dirs.json"
    tracked_dirs_file.write_text("[]")

    # Create backups directory
    backup_dir = dotz_dir / "backups"
    backup_dir.mkdir()

    return dotz_dir


@pytest.fixture
def config_data() -> Dict:
    """Return sample configuration data."""
    return {
        "file_patterns": {
            "include": [".*", "*.conf", "*.json"],
            "exclude": [".DS_Store", "*.log"],
        },
        "search_settings": {
            "recursive": True,
            "case_sensitive": False,
            "follow_symlinks": False,
        },
    }


def create_test_files(base_path: Path, files: Dict[str, str]) -> None:
    """Helper to create test files with content."""
    for file_path, content in files.items():
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def assert_symlink_correct(symlink_path: Path, target_path: Path) -> None:
    """Assert that a symlink points to the correct target."""
    assert symlink_path.is_symlink(), f"{symlink_path} is not a symlink"
    resolved_symlink = symlink_path.resolve()
    resolved_target = target_path.resolve()
    assert resolved_symlink == resolved_target, (
        f"Symlink {symlink_path} points to {resolved_symlink}, "
        f"expected {resolved_target}"
    )
