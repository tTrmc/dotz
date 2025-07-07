"""
Simplified CLI tests for loom configuration functionality.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

import pytest


@pytest.fixture
def temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory for testing."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def run_loom(
    *args: str, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess[str]:
    """Helper function to run loom CLI commands."""
    cmd = ["loom"] + list(map(str, args))
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestConfigCommands:
    """Test configuration CLI commands."""

    def test_config_show_all(self, temp_home: Path) -> None:
        """Test showing all configuration."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "show", env=env)
        assert result.returncode == 0

        # Should contain JSON configuration
        assert "file_patterns" in result.stdout
        assert "search_settings" in result.stdout
        assert "include" in result.stdout
        assert "exclude" in result.stdout

    def test_config_add_pattern(self, temp_home: Path) -> None:
        """Test adding file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Add include pattern
        result = run_loom("config", "add-pattern", "*.py", env=env)
        assert result.returncode == 0
        assert "✓ Added '*.py' to include patterns" in result.stdout

        # Verify the change
        result2 = run_loom("config", "show", "file_patterns.include", env=env)
        assert "*.py" in result2.stdout

    def test_config_list_patterns(self, temp_home: Path) -> None:
        """Test listing file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "list-patterns", env=env)
        assert result.returncode == 0

        # Should show patterns in readable format
        assert "Include patterns:" in result.stdout
        assert "Exclude patterns:" in result.stdout
        assert "+ .*" in result.stdout  # Include pattern format

    def test_config_help(self, temp_home: Path) -> None:
        """Test configuration help command."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "help", env=env)
        assert result.returncode == 0

        # Should show comprehensive help
        assert "Configuration Help" in result.stdout
        assert "Examples:" in result.stdout


class TestDirectoryWithConfig:
    """Test directory handling with configuration."""

    def test_add_directory_with_custom_patterns(self, temp_home: Path) -> None:
        """Test adding directory with custom file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Add Python files to include patterns
        run_loom("config", "add-pattern", "*.py", env=env)

        # Create a directory with various files
        project_dir = temp_home / "myproject"
        project_dir.mkdir()
        (project_dir / "script.py").write_text("print('hello')")
        (project_dir / "config.conf").write_text("setting=value")
        (project_dir / "readme.txt").write_text("readme content")
        (project_dir / ".gitignore").write_text("*.pyc")

        # Add the directory
        result = run_loom("add", "myproject", env=env)
        assert result.returncode == 0

        # List files to see what was added
        result2 = run_loom("list-files", env=env)

        # Should include Python files, config files, and dotfiles
        assert "script.py" in result2.stdout
        assert "config.conf" in result2.stdout
        assert ".gitignore" in result2.stdout
        # Should not include txt files (not in patterns)
        assert "readme.txt" not in result2.stdout
