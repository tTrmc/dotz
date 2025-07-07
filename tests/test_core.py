"""
Core functionality tests for loom.
Tests the core module functions like add_dotfile, init_repo, etc.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

import loom.core as core
from loom.core import (
    DEFAULT_CONFIG,
    add_dotfile,
    add_file_pattern,
    find_config_files,
    get_config_value,
    init_repo,
    load_config,
    matches_patterns,
    remove_file_pattern,
    reset_config,
    save_config,
    set_config_value,
)


class TestCoreBasicFunctionality:
    """Test basic loom core functionality."""

    def test_init_repo(self, temp_home: Path) -> None:
        """Test repository initialization."""
        result = init_repo(quiet=True)
        assert result is True

        loom_dir = temp_home / ".loom"
        work_tree = loom_dir / "repo"
        assert loom_dir.exists()
        assert work_tree.exists()

        # Second init should return False
        result2 = init_repo(quiet=True)
        assert result2 is False

    def test_add_single_dotfile(self, initialized_loom: Path) -> None:
        """Test adding a single dotfile."""
        home = initialized_loom

        # Create a dotfile
        dotfile = home / ".bashrc"
        dotfile.write_text("export TEST=1\n")

        # Add the file
        result = add_dotfile(Path(".bashrc"), quiet=True)
        assert result is True

        # Check that file was moved and symlinked
        assert dotfile.is_symlink()
        work_tree = home / ".loom" / "repo"
        assert (work_tree / ".bashrc").exists()

    def test_add_directory_recursive(self, initialized_loom: Path) -> None:
        """Test adding a directory with dotfiles recursively."""
        home = initialized_loom

        # Create a directory with dotfiles
        config_dir = home / ".config"
        config_dir.mkdir()
        (config_dir / ".gitconfig").write_text("config content")
        (config_dir / "app.conf").write_text("app config")

        sub_dir = config_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / ".hidden").write_text("hidden file")

        # Add the directory
        result = add_dotfile(Path(".config"), recursive=True, quiet=True)
        assert result is True

        # Check files were added based on default patterns
        repo_dir = home / ".loom" / "repo"
        assert (repo_dir / ".config" / ".gitconfig").exists()
        assert (repo_dir / ".config" / "app.conf").exists()  # matches *.conf pattern
        assert (repo_dir / ".config" / "subdir" / ".hidden").exists()


class TestConfigurationSystem:
    """Test the configuration system functionality."""

    def test_load_default_config(self, temp_home: Path) -> None:
        """Test loading default configuration."""

        # Patch paths
        original_config_file = core.CONFIG_FILE
        original_loom_dir = core.LOOM_DIR

        try:
            core.LOOM_DIR = temp_home / ".loom"
            core.CONFIG_FILE = core.LOOM_DIR / "config.json"

            # Ensure no config file exists
            if core.CONFIG_FILE.exists():
                core.CONFIG_FILE.unlink()

            config = load_config()
            assert config == DEFAULT_CONFIG
        finally:
            core.CONFIG_FILE = original_config_file
            core.LOOM_DIR = original_loom_dir

    def test_save_and_load_config(self, temp_home: Path) -> None:
        """Test saving and loading custom configuration."""
        custom_config: Dict[str, Any] = {
            "file_patterns": {"include": ["*.py", "*.txt"], "exclude": ["*.pyc"]},
            "search_settings": {
                "recursive": False,
                "case_sensitive": True,
                "follow_symlinks": True,
            },
        }

        save_config(custom_config)
        loaded_config = load_config()

        # Should merge with defaults
        assert "*.py" in loaded_config["file_patterns"]["include"]
        assert "*.txt" in loaded_config["file_patterns"]["include"]
        assert loaded_config["search_settings"]["recursive"] is False
        assert loaded_config["search_settings"]["case_sensitive"] is True

    def test_get_config_value(self, temp_home: Path) -> None:
        """Test getting configuration values by key path."""
        # Reset to defaults first to ensure predictable state
        reset_config(quiet=True)
        config = load_config()

        # Test getting nested values
        include_patterns = get_config_value("file_patterns.include", quiet=True)
        assert isinstance(include_patterns, list)
        assert ".*" in include_patterns  # dotfiles pattern

        # Test getting top-level values
        file_patterns = get_config_value("file_patterns", quiet=True)
        assert isinstance(file_patterns, dict)
        assert "include" in file_patterns

        # Test non-existent key
        result = get_config_value("nonexistent.key", quiet=True)
        assert result is None

    def test_set_config_value(self, temp_home: Path) -> None:
        """Test setting configuration values."""
        # Test setting boolean
        result = set_config_value("search_settings.recursive", "false", quiet=True)
        assert result is True

        config = load_config()
        assert config["search_settings"]["recursive"] is False

        # Test setting string
        result = set_config_value("test_key", "test_value", quiet=True)
        assert result is True

        config = load_config()
        assert config["test_key"] == "test_value"

    def test_add_remove_file_pattern(self, temp_home: Path) -> None:
        """Test adding and removing file patterns."""
        try:
            # Add include pattern
            result = add_file_pattern("*.py", "include", quiet=True)
            assert result is True

            config = load_config()
            assert "*.py" in config["file_patterns"]["include"]

            # Add duplicate pattern (should succeed but not add duplicate)
            result = add_file_pattern("*.py", "include", quiet=True)
            assert result is True

            # Add exclude pattern
            result = add_file_pattern("*.pyc", "exclude", quiet=True)
            assert result is True

            config = load_config()
            assert "*.pyc" in config["file_patterns"]["exclude"]

            # Remove pattern
            result = remove_file_pattern("*.py", "include", quiet=True)
            assert result is True

            config = load_config()
            assert "*.py" not in config["file_patterns"]["include"]

            # Remove non-existent pattern
            result = remove_file_pattern("*.nonexistent", "include", quiet=True)
            assert result is False
        finally:
            # Always reset to defaults to avoid test pollution
            reset_config(quiet=True)

    def test_reset_config(self, temp_home: Path) -> None:
        """Test resetting configuration to defaults."""
        # Modify config
        set_config_value("search_settings.recursive", "false", quiet=True)
        add_file_pattern("*.custom", "include", quiet=True)

        # Reset
        result = reset_config(quiet=True)
        assert result is True

        # Check it's back to defaults
        config = load_config()
        assert config == DEFAULT_CONFIG


class TestPatternMatching:
    """Test file pattern matching functionality."""

    def test_matches_patterns_basic(self) -> None:
        """Test basic pattern matching."""
        include: List[str] = [".*", "*.conf"]
        exclude: List[str] = ["*.log"]

        # Should match dotfiles
        assert matches_patterns(".bashrc", include, exclude, False)
        assert matches_patterns(".gitconfig", include, exclude, False)

        # Should match config files
        assert matches_patterns("app.conf", include, exclude, False)
        assert matches_patterns("nginx.conf", include, exclude, False)

        # Should not match excluded files
        assert not matches_patterns("error.log", include, exclude, False)

        # Should not match unincluded files
        assert not matches_patterns("readme.txt", include, exclude, False)

    def test_matches_patterns_case_sensitivity(self) -> None:
        """Test case sensitivity in pattern matching."""
        include: List[str] = ["*.CONF"]
        exclude: List[str] = []

        # Case insensitive (default)
        assert matches_patterns("app.conf", include, exclude, False)
        assert matches_patterns("app.CONF", include, exclude, False)

        # Case sensitive
        assert not matches_patterns("app.conf", include, exclude, True)
        assert matches_patterns("app.CONF", include, exclude, True)

    def test_find_config_files(self, temp_home: Path) -> None:
        """Test finding files matching configuration patterns."""
        # Create test directory with various files
        test_dir = temp_home / "test"
        test_dir.mkdir()

        # Test files that should be found
        (test_dir / ".bashrc").write_text("content")
        (test_dir / ".gitignore").write_text("content")
        (test_dir / "app.conf").write_text("content")
        (test_dir / "settings.json").write_text("content")

        # Test files that should NOT be found
        (test_dir / "readme.txt").write_text("content")
        (test_dir / "backup.log").write_text("content")

        # Test with default config
        config = load_config()
        found = find_config_files(test_dir, config, recursive=False)
        found_names = [f.name for f in found]

        # Should find dotfiles and config files
        assert ".bashrc" in found_names
        assert ".gitignore" in found_names
        assert "app.conf" in found_names
        assert "settings.json" in found_names

        # Should not find non-config files
        assert "readme.txt" not in found_names
        assert "backup.log" not in found_names

    def test_find_config_files_recursive(self, temp_home: Path) -> None:
        """Test recursive file finding."""
        # Create nested directory structure
        test_dir = temp_home / "test"
        test_dir.mkdir()
        sub_dir = test_dir / "subdir"
        sub_dir.mkdir()

        (test_dir / ".bashrc").write_text("content")
        (sub_dir / "app.conf").write_text("content")

        config = load_config()

        # Non-recursive
        found = find_config_files(test_dir, config, recursive=False)
        found_names = [f.name for f in found]
        assert ".bashrc" in found_names
        assert "app.conf" not in found_names

        # Recursive
        found = find_config_files(test_dir, config, recursive=True)
        found_names = [f.name for f in found]
        assert ".bashrc" in found_names
        assert "app.conf" in found_names


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_load_config_with_invalid_json(self, temp_home: Path) -> None:
        """Test loading config when JSON is invalid."""
        # Create invalid config file
        config_file = temp_home / ".loom" / "config.json"
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text("invalid json {")

        # Should fall back to defaults
        with patch("typer.secho"):  # Suppress warning output
            config = load_config()
        assert config == DEFAULT_CONFIG

    def test_set_config_value_invalid_json(self, temp_home: Path) -> None:
        """Test setting config value with invalid JSON."""
        result = set_config_value("test_key", "{invalid json", quiet=True)
        assert result is False

    def test_add_pattern_invalid_type(self, temp_home: Path) -> None:
        """Test adding pattern with invalid type."""
        result = add_file_pattern("*.py", "invalid_type", quiet=True)
        assert result is False

    def test_remove_pattern_invalid_type(self, temp_home: Path) -> None:
        """Test removing pattern with invalid type."""
        result = remove_file_pattern("*.py", "invalid_type", quiet=True)
        assert result is False
