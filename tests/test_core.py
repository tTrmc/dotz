"""Tests for dotz.core module."""

import json
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from click.exceptions import Exit
from git import GitCommandError, Repo

from dotz import core
from tests.conftest import assert_symlink_correct, create_test_files


class TestPathHelpers:
    """Test path-related helper functions."""

    def test_get_home_dir_respects_env(self, temp_home: Path) -> None:
        """Test that get_home_dir respects HOME environment variable."""
        assert core.get_home_dir() == temp_home

    def test_get_dotz_paths(self, temp_home: Path) -> None:
        """Test dotz path generation."""
        paths = core.get_dotz_paths(temp_home)

        assert paths["home"] == temp_home
        assert paths["dotz_dir"] == temp_home / ".dotz"
        assert paths["work_tree"] == temp_home / ".dotz" / "repo"
        assert paths["tracked_dirs_file"] == temp_home / ".dotz" / "tracked_dirs.json"
        assert paths["config_file"] == temp_home / ".dotz" / "config.json"
        assert paths["backup_dir"] == temp_home / ".dotz" / "backups"

    def test_update_paths(self, temp_home: Path) -> None:
        """Test updating global paths."""
        old_home = core.HOME
        core.update_paths(temp_home)

        assert core.HOME == temp_home
        assert core.DOTZ_DIR == temp_home / ".dotz"
        assert core.WORK_TREE == temp_home / ".dotz" / "repo"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_count_files_in_directory_single_file(self, temp_home: Path) -> None:
        """Test counting files for a single file."""
        test_file = temp_home / "test.txt"
        test_file.write_text("content")

        assert core.count_files_in_directory(test_file) == 1

    def test_count_files_in_directory_with_files(self, temp_home: Path) -> None:
        """Test counting files in a directory."""
        test_dir = temp_home / "test_dir"
        test_dir.mkdir()

        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        assert core.count_files_in_directory(test_dir) == 3

    def test_count_files_in_directory_empty(self, temp_home: Path) -> None:
        """Test counting files in an empty directory."""
        test_dir = temp_home / "empty_dir"
        test_dir.mkdir()

        assert core.count_files_in_directory(test_dir) == 0


class TestTrackedDirectories:
    """Test tracked directory management."""

    def test_save_tracked_dir(self, temp_home: Path) -> None:
        """Test saving a tracked directory."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        test_dir = Path(".config")
        core.save_tracked_dir(test_dir)

        tracked_file = dotz_dir / "tracked_dirs.json"
        assert tracked_file.exists()

        with open(tracked_file) as f:
            data = json.load(f)

        assert str(test_dir) in data

    def test_save_tracked_dir_duplicate(self, temp_home: Path) -> None:
        """Test that duplicate directories are not saved."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        test_dir = Path(".config")

        # Save twice
        core.save_tracked_dir(test_dir)
        core.save_tracked_dir(test_dir)

        tracked_file = dotz_dir / "tracked_dirs.json"
        with open(tracked_file) as f:
            data = json.load(f)

        # Should only appear once
        assert data.count(str(test_dir)) == 1

    def test_remove_tracked_dir(self, temp_home: Path) -> None:
        """Test removing a tracked directory."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        test_dir = Path(".config")

        # Save then remove
        core.save_tracked_dir(test_dir)
        core.remove_tracked_dir(test_dir)

        tracked_file = dotz_dir / "tracked_dirs.json"
        with open(tracked_file) as f:
            data = json.load(f)

        assert str(test_dir) not in data

    def test_remove_tracked_dir_nonexistent(self, temp_home: Path) -> None:
        """Test removing a directory that's not tracked."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        # Create empty tracked dirs file
        tracked_file = dotz_dir / "tracked_dirs.json"
        tracked_file.write_text("[]")

        test_dir = Path(".nonexistent")
        core.remove_tracked_dir(test_dir)  # Should not raise


class TestRepoManagement:
    """Test repository management functions."""

    def test_ensure_repo_success(self, initialized_dotz: Path) -> None:
        """Test successful repo access."""
        repo = core.ensure_repo()
        assert isinstance(repo, Repo)

    def test_ensure_repo_failure(self, temp_home: Path) -> None:
        """Test repo access failure."""
        # No dotz directory exists
        with pytest.raises((SystemExit, typer.Exit)):
            core.ensure_repo()

    def test_init_repo_basic(self, temp_home: Path) -> None:
        """Test basic repository initialization."""
        success = core.init_repo(quiet=True)

        assert success
        assert (temp_home / ".dotz").exists()
        assert (temp_home / ".dotz" / "repo").exists()
        assert (temp_home / ".dotz" / "config.json").exists()
        assert (temp_home / ".dotz" / "tracked_dirs.json").exists()
        assert (temp_home / ".dotz" / "backups").exists()

    def test_init_repo_with_remote(self, temp_home: Path) -> None:
        """Test repository initialization with remote."""
        remote_url = "https://github.com/user/dotfiles.git"

        with patch("dotz.core.Repo") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.init.return_value = mock_repo
            mock_repo.create_remote.return_value = None
            mock_repo.index.add.return_value = None
            mock_repo.index.commit.return_value = None

            success = core.init_repo(remote=remote_url, quiet=True)

            assert success
            mock_repo.create_remote.assert_called_once_with("origin", remote_url)

    def test_init_repo_already_exists(self, initialized_dotz: Path) -> None:
        """Test initialization when repo already exists."""
        success = core.init_repo(quiet=True)
        assert not success  # Should fail if already exists


class TestDotfileManagement:
    """Test dotfile add/delete/restore operations."""

    def test_add_dotfile_single_file(
        self, initialized_dotz: Path, sample_dotfile: Path
    ) -> None:
        """Test adding a single dotfile."""
        relative_path = Path(".bashrc")
        success = core.add_dotfile(relative_path, quiet=True)

        assert success

        # Check file was copied to dotz repo
        dotz_file = core.WORK_TREE / ".bashrc"
        assert dotz_file.exists()
        assert dotz_file.read_text() == sample_dotfile.read_text()

        # Check symlink was created
        assert_symlink_correct(sample_dotfile, dotz_file)

    def test_add_dotfile_directory(
        self, initialized_dotz: Path, sample_config_dir: Path
    ) -> None:
        """Test adding a directory of dotfiles."""
        relative_path = Path(".config")
        success = core.add_dotfile(relative_path, quiet=True, recursive=True)

        assert success

        # Check directory was copied
        dotz_dir = core.WORK_TREE / ".config"
        assert dotz_dir.exists()
        assert (dotz_dir / "app.conf").exists()
        assert (dotz_dir / "settings.json").exists()

        # Check symlink was created
        assert_symlink_correct(sample_config_dir, dotz_dir)

    def test_add_dotfile_nonexistent(self, initialized_dotz: Path) -> None:
        """Test adding a non-existent file."""
        relative_path = Path(".nonexistent")
        success = core.add_dotfile(relative_path, quiet=True)

        assert not success

    def test_delete_dotfile(self, initialized_dotz: Path, sample_dotfile: Path) -> None:
        """Test deleting a dotfile."""
        relative_path = Path(".bashrc")

        # First add the file
        core.add_dotfile(relative_path, quiet=True)

        # Then delete it
        success = core.delete_dotfile([relative_path], quiet=True)

        assert success

        # Check file was removed from dotz repo
        dotz_file = core.WORK_TREE / ".bashrc"
        assert not dotz_file.exists()

        # Check symlink was removed
        assert not sample_dotfile.is_symlink()

    def test_restore_dotfile(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test restoring a dotfile."""
        # Create a file in dotz repo
        dotz_file = core.WORK_TREE / ".vimrc"
        dotz_file.write_text("set number\n")

        # Add to git
        repo = core.ensure_repo()
        repo.index.add([".vimrc"])
        repo.index.commit("Add vimrc")

        relative_path = Path(".vimrc")
        success = core.restore_dotfile(relative_path, quiet=True)

        assert success

        # Check symlink was created
        home_file = temp_home / ".vimrc"
        assert_symlink_correct(home_file, dotz_file)

    def test_restore_dotfile_nonexistent(self, initialized_dotz: Path) -> None:
        """Test restoring a non-existent dotfile."""
        relative_path = Path(".nonexistent")
        success = core.restore_dotfile(relative_path, quiet=True)

        assert not success


class TestConfigManagement:
    """Test configuration management."""

    def test_load_config_default(self, temp_home: Path) -> None:
        """Test loading default configuration."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        config = core.load_config()
        assert config == core.DEFAULT_CONFIG

    def test_load_config_existing(
        self, initialized_dotz: Path, config_data: dict
    ) -> None:
        """Test loading existing configuration."""
        config_file = core.CONFIG_FILE
        config_file.write_text(json.dumps(config_data))

        config = core.load_config()
        assert config == config_data

    def test_save_config(self, temp_home: Path, config_data: dict) -> None:
        """Test saving configuration."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        core.save_config(config_data)

        config_file = dotz_dir / "config.json"
        assert config_file.exists()

        with open(config_file) as f:
            saved_config = json.load(f)

        assert saved_config == config_data

    def test_get_config_value(self, initialized_dotz: Path) -> None:
        """Test getting configuration values."""
        value = core.get_config_value("file_patterns.include", quiet=True)
        assert isinstance(value, list)
        assert ".*" in value

    def test_get_config_value_nonexistent(self, initialized_dotz: Path) -> None:
        """Test getting non-existent configuration value."""
        value = core.get_config_value("nonexistent.key", quiet=True)
        assert value is None

    def test_set_config_value(self, initialized_dotz: Path) -> None:
        """Test setting configuration values."""
        success = core.set_config_value(
            "search_settings.recursive", "false", quiet=True
        )
        assert success

        value = core.get_config_value("search_settings.recursive", quiet=True)
        assert value is False

    def test_add_file_pattern(self, initialized_dotz: Path) -> None:
        """Test adding file patterns."""
        pattern = "*.xml"
        success = core.add_file_pattern(pattern, "include", quiet=True)

        assert success

        config = core.load_config()
        assert pattern in config["file_patterns"]["include"]

    def test_remove_file_pattern(self, initialized_dotz: Path) -> None:
        """Test removing file patterns."""
        pattern = ".*"  # This should exist by default
        success = core.remove_file_pattern(pattern, "include", quiet=True)

        assert success

        config = core.load_config()
        assert pattern not in config["file_patterns"]["include"]

    def test_reset_config(self, initialized_dotz: Path) -> None:
        """Test resetting configuration to defaults."""
        # Modify config first
        core.set_config_value("search_settings.recursive", "false", quiet=True)

        # Reset
        success = core.reset_config(quiet=True)
        assert success

        # Check it's back to default
        config = core.load_config()
        assert config == core.DEFAULT_CONFIG


class TestPatternMatching:
    """Test file pattern matching."""

    def test_matches_patterns_include_only(self) -> None:
        """Test pattern matching with include patterns only."""
        include_patterns = ["*.txt", "*.md"]
        exclude_patterns: list[str] = []

        assert core.matches_patterns(
            "readme.txt", include_patterns, exclude_patterns, False
        )
        assert core.matches_patterns(
            "notes.md", include_patterns, exclude_patterns, False
        )
        assert not core.matches_patterns(
            "script.py", include_patterns, exclude_patterns, False
        )

    def test_matches_patterns_exclude(self) -> None:
        """Test pattern matching with exclude patterns."""
        include_patterns = ["*"]
        exclude_patterns: list[str] = ["*.log", "*.tmp"]

        assert core.matches_patterns(
            "readme.txt", include_patterns, exclude_patterns, False
        )
        assert not core.matches_patterns(
            "debug.log", include_patterns, exclude_patterns, False
        )
        assert not core.matches_patterns(
            "temp.tmp", include_patterns, exclude_patterns, False
        )

    def test_matches_patterns_case_sensitive(self) -> None:
        """Test case-sensitive pattern matching."""
        include_patterns = ["*.TXT"]
        exclude_patterns: list[str] = []

        # Case sensitive
        assert core.matches_patterns(
            "readme.TXT", include_patterns, exclude_patterns, True
        )
        assert not core.matches_patterns(
            "readme.txt", include_patterns, exclude_patterns, True
        )

        # Case insensitive
        assert core.matches_patterns(
            "readme.TXT", include_patterns, exclude_patterns, False
        )
        assert core.matches_patterns(
            "readme.txt", include_patterns, exclude_patterns, False
        )

    def test_find_config_files(self, temp_home: Path) -> None:
        """Test finding configuration files."""
        # Create test directory structure
        test_files = {
            ".bashrc": "# bashrc",
            ".config/app.conf": "[section]\nkey=value",
            ".config/settings.json": '{"theme": "dark"}',
            ".cache/data.txt": "cache data",
            "document.pdf": "binary data",
        }
        create_test_files(temp_home, test_files)

        # Find config files
        test_config = {
            "file_patterns": {
                "include": [".*", "*.conf", "*.json"],
                "exclude": [".cache"],
            },
            "search_settings": {
                "recursive": True,
                "case_sensitive": False,
                "follow_symlinks": False,
            },
        }
        config_files = core.find_config_files(temp_home, test_config, recursive=True)

        # Convert to relative paths for easier testing
        relative_files = [str(f.relative_to(temp_home)) for f in config_files]

        assert ".bashrc" in relative_files
        assert ".config/app.conf" in relative_files
        assert ".config/settings.json" in relative_files
        assert ".cache/data.txt" not in relative_files  # Excluded
        assert "document.pdf" not in relative_files  # Not matching include patterns


class TestRepoOperations:
    """Test repository operations like push, pull, status."""

    def test_list_tracked_files(
        self, initialized_dotz: Path, sample_dotfile: Path
    ) -> None:
        """Test listing tracked files."""
        # Add a file first
        core.add_dotfile(Path(".bashrc"), quiet=True)

        tracked_files = core.list_tracked_files()
        assert ".bashrc" in tracked_files

    def test_get_repo_status_clean(self, initialized_dotz: Path) -> None:
        """Test repo status when clean."""
        status = core.get_repo_status()

        assert status["untracked"] == []
        assert status["modified"] == []
        assert status["staged"] == []

    @patch("dotz.core.typer.confirm")
    def test_push_repo_no_remote(
        self, mock_confirm: Mock, initialized_dotz: Path
    ) -> None:
        """Test pushing when no remote is configured."""
        mock_confirm.return_value = False
        success = core.push_repo(quiet=True)
        assert not success  # Should fail with no remote

    def test_pull_repo_no_remote(self, initialized_dotz: Path) -> None:
        """Test pulling when no remote is configured."""
        success = core.pull_repo(quiet=True)
        assert not success  # Should fail with no remote


class TestBackupManagement:
    """Test backup creation and restoration."""

    def test_create_backup(self, initialized_dotz: Path, sample_dotfile: Path) -> None:
        """Test creating a backup."""
        backup_path = core.create_backup(sample_dotfile, operation="test", quiet=True)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == sample_dotfile.read_text()
        assert "test" in backup_path.name

    def test_create_backup_directory(
        self, initialized_dotz: Path, sample_config_dir: Path
    ) -> None:
        """Test creating a backup of a directory."""
        backup_path = core.create_backup(
            sample_config_dir, operation="test", quiet=True
        )

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.is_file()  # Should be a tar archive

    def test_list_backups(self, initialized_dotz: Path, sample_dotfile: Path) -> None:
        """Test listing backups."""
        # Create a backup
        core.create_backup(sample_dotfile, operation="test", quiet=True)

        backups = core.list_backups()
        assert len(backups) >= 1
        assert any("test" in backup.name for backup in backups)

    def test_restore_from_backup(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test restoring from backup."""
        # Create original file
        original_file = temp_home / ".vimrc"
        original_file.write_text("original content")

        # Create backup
        backup_path = core.create_backup(original_file, operation="test", quiet=True)
        assert backup_path is not None  # Ensure backup was created successfully

        # Modify original
        original_file.write_text("modified content")

        # Restore from backup
        success = core.restore_from_backup(backup_path, quiet=True)

        assert success
        assert original_file.read_text() == "original content"


class TestSymlinkValidation:
    """Test symlink validation and repair."""

    def test_validate_symlinks_all_good(
        self, initialized_dotz: Path, sample_dotfile: Path
    ) -> None:
        """Test validation when all symlinks are correct."""
        # Add file to create proper symlink
        core.add_dotfile(Path(".bashrc"), quiet=True)

        results = core.validate_symlinks(quiet=True)

        assert results is not None
        assert len(results.get("broken", [])) == 0
        # We expect README.md to be missing since it's not a dotfile
        # that should be symlinked. Only check that there are no broken
        # symlinks, not that all files are properly symlinked
        assert len(results.get("wrong_target", [])) == 0

    def test_validate_symlinks_broken(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test validation with broken symlinks."""
        # Create a broken symlink
        broken_link = temp_home / ".broken"
        broken_link.symlink_to("/nonexistent/path")

        # Add it to dotz repo manually to simulate a broken state
        dotz_file = core.WORK_TREE / ".broken"
        dotz_file.write_text("content")
        repo = core.ensure_repo()
        repo.index.add([".broken"])
        repo.index.commit("Add broken file")

        results = core.validate_symlinks(quiet=True)

        assert results is not None
        # The symlink points to wrong target, so it should be in wrong_target
        assert ".broken" in results.get("wrong_target", [])

    def test_validate_symlinks_repair(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test repairing broken symlinks."""
        # Create file in dotz repo
        dotz_file = core.WORK_TREE / ".testfile"
        dotz_file.write_text("test content")
        repo = core.ensure_repo()
        repo.index.add([".testfile"])
        repo.index.commit("Add test file")

        # Create broken symlink in home
        home_file = temp_home / ".testfile"
        home_file.symlink_to("/nonexistent")

        results = core.validate_symlinks(repair=True, quiet=True)

        assert results is not None
        # After repair, the symlink should be fixed
        assert_symlink_correct(home_file, dotz_file)


class TestCloneAndRestore:
    """Test cloning repositories and restoring all dotfiles."""

    @patch("dotz.core.Repo.clone_from")
    def test_clone_repo(self, mock_clone: Mock, temp_home: Path) -> None:
        """Test cloning a repository."""
        mock_repo = Mock()
        mock_clone.return_value = mock_repo
        mock_repo.git.ls_files.return_value = ".bashrc\n.vimrc"

        remote_url = "https://github.com/user/dotfiles.git"
        success = core.clone_repo(remote_url, quiet=True)

        assert success
        mock_clone.assert_called_once()

    def test_restore_all_dotfiles(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test restoring all tracked dotfiles."""
        # Add some files to dotz repo
        test_files = {
            ".bashrc": "# bashrc content",
            ".vimrc": "set number",
            ".config/app.conf": "[section]\nkey=value",
        }

        for file_path, content in test_files.items():
            dotz_file = core.WORK_TREE / file_path
            dotz_file.parent.mkdir(parents=True, exist_ok=True)
            dotz_file.write_text(content)

        repo = core.ensure_repo()
        repo.index.add(list(test_files.keys()))
        repo.index.commit("Add test files")

        success = core.restore_all_dotfiles(quiet=True)

        assert success

        # Check all files were restored as symlinks
        for file_path in test_files.keys():
            home_file = temp_home / file_path
            dotz_file = core.WORK_TREE / file_path
            assert_symlink_correct(home_file, dotz_file)
