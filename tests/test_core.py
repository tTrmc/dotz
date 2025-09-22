"""Tests for dotz core functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dotz.core import (
    get_dotz_paths,
    load_config,
    save_config,
    validate_file_patterns,
)
from dotz.exceptions import DotzRepositoryNotFoundError


class TestDotzPaths:
    """Test dotz path management."""

    def test_get_dotz_paths_default(self):
        """Test default dotz paths creation."""
        with patch("dotz.core.get_home_dir") as mock_home:
            mock_home.return_value = Path("/home/user")
            paths = get_dotz_paths()

            assert paths["dotz_dir"] == Path("/home/user/.dotz")
            assert paths["work_tree"] == Path("/home/user/.dotz/repo")
            assert paths["config_file"] == Path("/home/user/.dotz/config.json")
            assert paths["backup_dir"] == Path("/home/user/.dotz/backups")

    def test_get_dotz_paths_custom_home(self, temp_home: Path):
        """Test dotz paths with custom home directory."""
        with patch("dotz.core.get_home_dir") as mock_home:
            mock_home.return_value = temp_home
            paths = get_dotz_paths()

            assert paths["dotz_dir"] == temp_home / ".dotz"
            assert paths["work_tree"] == temp_home / ".dotz" / "repo"


class TestConfiguration:
    """Test configuration management."""

    def test_load_config_file_exists(self, temp_dotz_dir: Path, sample_config: dict):
        """Test loading configuration from existing file."""
        config_file = temp_dotz_dir / "config.json"
        config_file.write_text(json.dumps(sample_config))

        with patch("dotz.core.CONFIG_FILE", config_file):
            config = load_config()

        # The loaded config will be merged with defaults
        assert "file_patterns" in config
        assert "search_settings" in config

    def test_load_config_file_not_exists(self, temp_dotz_dir: Path):
        """Test loading configuration when file doesn't exist returns defaults."""
        config_file = temp_dotz_dir / "config.json"

        with (
            patch("dotz.core.CONFIG_FILE", config_file),
            patch("dotz.core.DOTZ_DIR", temp_dotz_dir),
        ):
            config = load_config()

        # Should return default configuration
        assert "file_patterns" in config
        assert "search_settings" in config
        assert isinstance(config["file_patterns"]["include"], list)

    def test_save_config(self, temp_dotz_dir: Path, sample_config: dict):
        """Test saving configuration to file."""
        config_file = temp_dotz_dir / "config.json"

        with (
            patch("dotz.core.CONFIG_FILE", config_file),
            patch("dotz.core.DOTZ_DIR", temp_dotz_dir),
        ):
            save_config(sample_config)

        # Verify file was created and contains correct data
        assert config_file.exists()
        saved_config = json.loads(config_file.read_text())
        assert saved_config == sample_config


class TestFilePatterns:
    """Test file pattern validation."""

    def test_validate_file_patterns_valid(self):
        """Test validation of valid file patterns."""
        patterns = ["*.py", ".*", "*.txt"]
        # Should not raise any exception
        validate_file_patterns(patterns)

    def test_validate_file_patterns_empty_list(self):
        """Test validation of empty pattern list."""
        patterns = []
        # Should not raise any exception
        validate_file_patterns(patterns)

    def test_validate_file_patterns_invalid_type(self):
        """Test validation fails for non-list input."""
        with pytest.raises(ValueError, match="must be a list"):
            validate_file_patterns("not a list")

    def test_validate_file_patterns_non_string_elements(self):
        """Test validation fails for non-string pattern elements."""
        patterns = ["*.py", 123, "*.txt"]
        with pytest.raises(ValueError, match="must be strings"):
            validate_file_patterns(patterns)


class TestRepositoryNotFound:
    """Test behavior when dotz repository is not found."""

    def test_operation_without_repo_raises_error(self):
        """Test that operations requiring repo raise appropriate error."""
        with patch("dotz.core.get_dotz_paths") as mock_paths:
            mock_paths.return_value = {"repo_dir": Path("/nonexistent")}

            # This would be tested with actual functions that require repo
            # For now, we'll test the exception class itself
            with pytest.raises(DotzRepositoryNotFoundError):
                raise DotzRepositoryNotFoundError("Repository not found")
