"""
Shared pytest fixtures for dotkeep tests.
"""

import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Create a temporary home directory and update environment."""
    home = tmp_path / "home"
    home.mkdir()

    # Set environment variable for HOME
    monkeypatch.setenv("HOME", str(home))

    # Update paths in all modules
    from dotkeep.core import update_paths
    from dotkeep.watcher import update_watcher_paths

    update_paths(home)
    update_watcher_paths(home)

    # Clean up any existing .dotkeep directory
    dotkeep = home / ".dotkeep"
    if dotkeep.exists():
        shutil.rmtree(dotkeep)

    return home


@pytest.fixture
def initialized_dotkeep(temp_home):
    """Create an initialized dotkeep repository."""
    from dotkeep.core import init_repo

    init_repo(quiet=True)
    return temp_home
