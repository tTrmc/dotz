"""Shared pytest fixtures and configuration."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_home() -> Generator[Path, None, None]:
    """Create a temporary home directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_dotz_dir(temp_home: Path) -> Path:
    """Create a temporary dotz directory structure."""
    dotz_dir = temp_home / ".dotz"
    dotz_dir.mkdir()
    (dotz_dir / "repo").mkdir()
    (dotz_dir / "backups").mkdir()
    return dotz_dir


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration for testing."""
    return {
        "file_patterns": {
            "include": [".*", "*.conf", "*.config"],
            "exclude": [".git", ".cache", "*.log"],
        },
        "search_settings": {
            "recursive": True,
            "case_sensitive": False,
            "follow_symlinks": False,
        },
    }
