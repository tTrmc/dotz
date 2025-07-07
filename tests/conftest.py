"""
Shared pytest fixtures for dotkeep tests.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Generator

import pytest

from dotkeep.core import update_paths
from dotkeep.watcher import update_watcher_paths


@pytest.fixture
def temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory and update environment."""
    home = tmp_path / "home"
    home.mkdir()

    # Set environment variable for HOME
    monkeypatch.setenv("HOME", str(home))

    # Update paths in all modules

    # Add src to path to import dotkeep modules
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    update_paths(home)
    update_watcher_paths(home)

    # Clean up any existing .dotkeep directory
    dotkeep = home / ".dotkeep"
    if dotkeep.exists():
        shutil.rmtree(dotkeep)

    return home


@pytest.fixture
def initialized_dotkeep(temp_home: Path) -> Path:
    """Create an initialized dotkeep repository."""
    from dotkeep.core import init_repo

    init_repo(quiet=True)
    return temp_home
