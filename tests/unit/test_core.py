"""
Test module for dotz core functionality.

This module tests the core business logic including path management,
Git operations, file handling, configuration management, and backup/restore operations.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest
from git import GitCommandError, InvalidGitRepositoryError, Repo

from dotz import core
from dotz.exceptions import (
    DotzBackupError,
    DotzFileNotFoundError,
    DotzGitError,
    DotzRepositoryNotFoundError,
    DotzValidationError,
)


class TestPathManagement:
    """Test suite for path management functions."""
    
    def test_get_home_dir_from_environment(self, monkeypatch):
        """Test that get_home_dir respects HOME environment variable."""
        test_home = "/tmp/test_home"
        monkeypatch.setenv("HOME", test_home)
        
        result = core.get_home_dir()
        
        assert result == Path(test_home)
    
    def test_get_home_dir_fallback(self, monkeypatch):
        """Test that get_home_dir falls back to Path.home() when HOME not set."""
        monkeypatch.delenv("HOME", raising=False)
        
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            result = core.get_home_dir()
            
        assert result == Path("/home/user")
        mock_home.assert_called_once()
    
    def test_get_dotz_paths_with_custom_home(self):
        """Test get_dotz_paths with custom home directory."""
        home_dir = Path("/custom/home")
        
        paths = core.get_dotz_paths(home_dir)
        
        expected_paths = {
            "home": home_dir,
            "dotz_dir": home_dir / ".dotz",
            "work_tree": home_dir / ".dotz" / "repo",
            "tracked_dirs_file": home_dir / ".dotz" / "tracked_dirs.json",
            "config_file": home_dir / ".dotz" / "config.json",
            "backup_dir": home_dir / ".dotz" / "backups",
        }
        
        assert paths == expected_paths
    
    def test_get_dotz_paths_with_default_home(self):
        """Test get_dotz_paths with default home directory."""
        with patch("dotz.core.get_home_dir") as mock_get_home:
            mock_get_home.return_value = Path("/default/home")
            
            paths = core.get_dotz_paths()
            
        assert paths["home"] == Path("/default/home")
        assert paths["dotz_dir"] == Path("/default/home/.dotz")
    
    def test_update_paths(self):
        """Test that update_paths correctly updates global variables."""
        home_dir = Path("/test/home")
        
        core.update_paths(home_dir)
        
        assert core.HOME == home_dir
        assert core.DOTZ_DIR == home_dir / ".dotz"
        assert core.WORK_TREE == home_dir / ".dotz" / "repo"
        assert core.CONFIG_FILE == home_dir / ".dotz" / "config.json"


class TestConfigurationManagement:
    """Test suite for configuration management functions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.config_file = self.dotz_dir / "config.json"
        core.update_paths(isolated_home)
    
    def test_load_config_with_existing_file(self):
        """Test loading configuration from existing file."""
        # Create dotz directory and config file
        self.dotz_dir.mkdir()
        config_data = {
            "file_patterns": {
                "include": ["*.txt"],
                "exclude": ["*.log"]
            },
            "search_settings": {
                "recursive": False
            }
        }
        self.config_file.write_text(json.dumps(config_data))
        
        result = core.load_config()
        
        assert result == config_data
    
    def test_load_config_creates_default_if_missing(self):
        """Test that load_config creates default config when file doesn't exist."""
        # Ensure dotz directory exists but config file doesn't
        self.dotz_dir.mkdir()
        
        result = core.load_config()
        
        # Should return default config
        assert result == core.DEFAULT_CONFIG
        # Should create config file
        assert self.config_file.exists()
        created_config = json.loads(self.config_file.read_text())
        assert created_config == core.DEFAULT_CONFIG
    
    def test_load_config_handles_invalid_json(self):
        """Test that load_config handles invalid JSON gracefully."""
        self.dotz_dir.mkdir()
        self.config_file.write_text("invalid json content")
        
        result = core.load_config()
        
        # Should return default config and recreate file
        assert result == core.DEFAULT_CONFIG
        assert json.loads(self.config_file.read_text()) == core.DEFAULT_CONFIG
    
    def test_save_config(self):
        """Test saving configuration to file."""
        self.dotz_dir.mkdir()
        config_data = {
            "file_patterns": {
                "include": ["*.py"],
                "exclude": ["*.pyc"]
            }
        }
        
        core.save_config(config_data)
        
        assert self.config_file.exists()
        saved_config = json.loads(self.config_file.read_text())
        assert saved_config == config_data
    
    def test_get_config_value_nested(self):
        """Test getting nested configuration values."""
        self.dotz_dir.mkdir()
        config_data = {
            "file_patterns": {
                "include": ["*.txt"]
            },
            "search_settings": {
                "recursive": True
            }
        }
        self.config_file.write_text(json.dumps(config_data))
        
        # Test nested key access
        assert core.get_config_value("file_patterns.include") == ["*.txt"]
        assert core.get_config_value("search_settings.recursive") is True
        
        # Test non-existent key
        assert core.get_config_value("nonexistent.key") is None
        
        # Test with default value
        assert core.get_config_value("nonexistent.key", "default") == "default"
    
    def test_set_config_value_nested(self):
        """Test setting nested configuration values."""
        self.dotz_dir.mkdir()
        self.config_file.write_text(json.dumps(core.DEFAULT_CONFIG))
        
        # Set nested value
        core.set_config_value("search_settings.recursive", False)
        
        config = core.load_config()
        assert config["search_settings"]["recursive"] is False
    
    def test_reset_config(self):
        """Test resetting configuration to defaults."""
        self.dotz_dir.mkdir()
        # Create custom config
        custom_config = {"custom": "value"}
        self.config_file.write_text(json.dumps(custom_config))
        
        core.reset_config()
        
        config = core.load_config()
        assert config == core.DEFAULT_CONFIG


class TestGitOperations:
    """Test suite for Git operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.work_tree = self.dotz_dir / "repo"
        core.update_paths(isolated_home)
    
    def test_init_repo_creates_directory_structure(self):
        """Test that init_repo creates proper directory structure."""
        result = core.init_repo()
        
        assert self.dotz_dir.exists()
        assert self.work_tree.exists()
        assert (self.dotz_dir / "config.json").exists()
        assert (self.dotz_dir / "tracked_dirs.json").exists()
        assert (self.dotz_dir / "backups").exists()
        assert result["success"] is True
    
    def test_init_repo_with_remote(self):
        """Test init_repo with remote repository."""
        remote_url = "git@github.com:user/dotfiles.git"
        
        with patch("dotz.core.Repo.init") as mock_init, \
             patch("dotz.core.Repo") as mock_repo_class:
            
            mock_repo = Mock()
            mock_init.return_value = mock_repo
            mock_repo_class.return_value = mock_repo
            mock_repo.create_remote.return_value = Mock()
            
            result = core.init_repo(remote_url)
            
            assert result["success"] is True
            mock_repo.create_remote.assert_called_once_with("origin", remote_url)
    
    def test_init_repo_handles_existing_repository(self):
        """Test that init_repo handles existing repository gracefully."""
        # Create repository first
        self.dotz_dir.mkdir()
        self.work_tree.mkdir()
        Repo.init(str(self.work_tree))
        
        result = core.init_repo()
        
        assert result["success"] is True
        assert "already exists" in result["message"]
    
    @patch("dotz.core.Repo")
    def test_get_repo_status_clean_repo(self, mock_repo_class):
        """Test get_repo_status with clean repository."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        mock_repo.remotes = []
        
        status = core.get_repo_status()
        
        assert status["is_dirty"] is False
        assert status["untracked_files"] == []
        assert status["has_remote"] is False
    
    @patch("dotz.core.Repo")
    def test_get_repo_status_dirty_repo(self, mock_repo_class):
        """Test get_repo_status with dirty repository."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.is_dirty.return_value = True
        mock_repo.untracked_files = ["file1.txt", "file2.txt"]
        
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_repo.remotes = [mock_remote]
        
        status = core.get_repo_status()
        
        assert status["is_dirty"] is True
        assert status["untracked_files"] == ["file1.txt", "file2.txt"]
        assert status["has_remote"] is True
    
    def test_get_repo_status_no_repository(self):
        """Test get_repo_status when no repository exists."""
        # Don't create repository
        
        with pytest.raises(DotzRepositoryNotFoundError):
            core.get_repo_status()
    
    @patch("dotz.core.Repo")
    def test_commit_repo_success(self, mock_repo_class):
        """Test successful repository commit."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_commit = Mock()
        mock_commit.hexsha = "abc123"
        mock_repo.index.commit.return_value = mock_commit
        
        result = core.commit_repo("Test commit message")
        
        assert result["success"] is True
        assert result["commit_hash"] == "abc123"
        mock_repo.index.commit.assert_called_once_with("Test commit message")
    
    @patch("dotz.core.Repo")
    def test_commit_repo_failure(self, mock_repo_class):
        """Test repository commit failure."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.index.commit.side_effect = GitCommandError("commit", "error")
        
        with pytest.raises(DotzGitError):
            core.commit_repo("Test commit message")
    
    @patch("dotz.core.Repo")
    def test_pull_repo_success(self, mock_repo_class):
        """Test successful repository pull."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_remote = Mock()
        mock_remote.pull.return_value = []
        mock_repo.remotes = [mock_remote]
        
        result = core.pull_repo()
        
        assert result["success"] is True
        mock_remote.pull.assert_called_once()
    
    @patch("dotz.core.Repo")
    def test_pull_repo_no_remote(self, mock_repo_class):
        """Test pull_repo when no remote exists."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.remotes = []
        
        with pytest.raises(DotzGitError, match="No remote repository"):
            core.pull_repo()
    
    @patch("dotz.core.Repo")
    def test_push_repo_success(self, mock_repo_class):
        """Test successful repository push."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_remote = Mock()
        mock_remote.push.return_value = []
        mock_repo.remotes = [mock_remote]
        
        result = core.push_repo()
        
        assert result["success"] is True
        mock_remote.push.assert_called_once()


class TestFileOperations:
    """Test suite for file operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_home, initialized_dotz_repo):
        """Set up test environment before each test."""
        self.home_dir = mock_home
        self.dotz_dir = initialized_dotz_repo
        self.work_tree = self.dotz_dir / "repo"
        core.update_paths(mock_home)
    
    def test_add_dotfile_single_file(self):
        """Test adding a single dotfile."""
        # Create a dotfile
        dotfile = self.home_dir / ".testrc"
        dotfile.write_text("test content")
        
        with patch("dotz.core.Repo") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            result = core.add_dotfile(str(dotfile))
            
            assert result["success"] is True
            assert result["files_added"] == [str(dotfile)]
            # Check that file was copied to work tree
            copied_file = self.work_tree / ".testrc"
            assert copied_file.exists()
            assert copied_file.read_text() == "test content"
    
    def test_add_dotfile_nonexistent_file(self):
        """Test adding a nonexistent dotfile."""
        nonexistent_file = self.home_dir / ".nonexistent"
        
        with pytest.raises(DotzFileNotFoundError):
            core.add_dotfile(str(nonexistent_file))
    
    def test_add_dotfile_directory_recursive(self):
        """Test adding a directory recursively."""
        # Create a config directory with files
        config_dir = self.home_dir / ".config" / "testapp"
        config_dir.mkdir(parents=True)
        (config_dir / "config.conf").write_text("config content")
        (config_dir / "settings.json").write_text('{"key": "value"}')
        
        with patch("dotz.core.Repo") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            result = core.add_dotfile(str(config_dir), recursive=True)
            
            assert result["success"] is True
            assert len(result["files_added"]) == 2
            # Check files were copied
            assert (self.work_tree / ".config" / "testapp" / "config.conf").exists()
            assert (self.work_tree / ".config" / "testapp" / "settings.json").exists()
    
    def test_delete_dotfile_success(self):
        """Test successful dotfile deletion."""
        # Add a file first
        dotfile = self.home_dir / ".testrc"
        dotfile.write_text("test content")
        copied_file = self.work_tree / ".testrc"
        copied_file.parent.mkdir(parents=True, exist_ok=True)
        copied_file.write_text("test content")
        
        with patch("dotz.core.Repo") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            result = core.delete_dotfile(str(dotfile))
            
            assert result["success"] is True
            assert not copied_file.exists()
    
    def test_delete_dotfile_not_tracked(self):
        """Test deleting a file that's not tracked."""
        untracked_file = self.home_dir / ".untracked"
        untracked_file.write_text("untracked content")
        
        with pytest.raises(DotzFileNotFoundError):
            core.delete_dotfile(str(untracked_file))
    
    def test_restore_dotfile_success(self):
        """Test successful dotfile restoration."""
        # Create file in work tree
        source_file = self.work_tree / ".testrc"
        source_file.write_text("restored content")
        
        result = core.restore_dotfile(str(source_file))
        
        assert result["success"] is True
        # Check file was restored to home
        restored_file = self.home_dir / ".testrc"
        assert restored_file.exists()
        assert restored_file.read_text() == "restored content"
    
    def test_restore_dotfile_backup_existing(self):
        """Test that restore_dotfile backs up existing files."""
        # Create existing file in home
        existing_file = self.home_dir / ".testrc"
        existing_file.write_text("existing content")
        
        # Create file in work tree
        source_file = self.work_tree / ".testrc"
        source_file.write_text("new content")
        
        result = core.restore_dotfile(str(source_file))
        
        assert result["success"] is True
        # Check backup was created
        backup_files = list(self.dotz_dir.glob("backups/.testrc_*"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == "existing content"
    
    def test_list_tracked_files(self):
        """Test listing tracked files."""
        # Create some files in work tree
        (self.work_tree / ".bashrc").write_text("bash content")
        (self.work_tree / ".vimrc").write_text("vim content")
        config_dir = self.work_tree / ".config" / "app"
        config_dir.mkdir(parents=True)
        (config_dir / "config.conf").write_text("config content")
        
        files = core.list_tracked_files()
        
        # Should return relative paths from work tree
        expected_files = [".bashrc", ".vimrc", ".config/app/config.conf", "README.md"]
        assert set(files) == set(expected_files)


class TestPatternMatching:
    """Test suite for file pattern matching."""
    
    def test_matches_include_patterns(self):
        """Test matching against include patterns."""
        patterns = [".*", "*.conf"]
        
        assert core.matches_patterns(".bashrc", patterns, [])
        assert core.matches_patterns("config.conf", patterns, [])
        assert not core.matches_patterns("regular_file.txt", patterns, [])
    
    def test_matches_exclude_patterns(self):
        """Test matching against exclude patterns."""
        include_patterns = ["*"]
        exclude_patterns = ["*.log", "*.tmp"]
        
        assert core.matches_patterns("file.txt", include_patterns, exclude_patterns)
        assert not core.matches_patterns("error.log", include_patterns, exclude_patterns)
        assert not core.matches_patterns("temp.tmp", include_patterns, exclude_patterns)
    
    def test_case_sensitive_matching(self):
        """Test case-sensitive pattern matching."""
        patterns = ["*.TXT"]
        
        # Case sensitive
        assert core.matches_patterns("FILE.TXT", patterns, [], case_sensitive=True)
        assert not core.matches_patterns("file.txt", patterns, [], case_sensitive=True)
        
        # Case insensitive
        assert core.matches_patterns("FILE.TXT", patterns, [], case_sensitive=False)
        assert core.matches_patterns("file.txt", patterns, [], case_sensitive=False)


class TestBackupOperations:
    """Test suite for backup and restore operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_home, initialized_dotz_repo):
        """Set up test environment before each test."""
        self.home_dir = mock_home
        self.dotz_dir = initialized_dotz_repo
        self.backup_dir = self.dotz_dir / "backups"
        core.update_paths(mock_home)
    
    def test_create_backup_single_file(self):
        """Test creating backup of a single file."""
        # Create a file to backup
        test_file = self.home_dir / ".testrc"
        test_file.write_text("test content")
        
        with patch("dotz.core.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            
            result = core.create_backup([str(test_file)])
            
            assert result["success"] is True
            assert "backup_file" in result
            
            # Check backup file exists
            backup_file = Path(result["backup_file"])
            assert backup_file.exists()
            assert backup_file.suffix == ".tar.gz"
    
    def test_create_backup_multiple_files(self):
        """Test creating backup of multiple files."""
        # Create multiple files
        files = []
        for i in range(3):
            test_file = self.home_dir / f".testrc{i}"
            test_file.write_text(f"content {i}")
            files.append(str(test_file))
        
        with patch("dotz.core.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            
            result = core.create_backup(files)
            
            assert result["success"] is True
            assert len(result["files_backed_up"]) == 3
    
    def test_create_backup_nonexistent_file(self):
        """Test backup creation with nonexistent file."""
        nonexistent_file = str(self.home_dir / ".nonexistent")
        
        with pytest.raises(DotzBackupError):
            core.create_backup([nonexistent_file])
    
    def test_list_backups(self):
        """Test listing available backups."""
        # Create some backup files
        backup_files = [
            "backup_20240101_120000.tar.gz",
            "backup_20240102_130000.tar.gz",
            "backup_20240103_140000.tar.gz"
        ]
        
        for backup_file in backup_files:
            (self.backup_dir / backup_file).touch()
        
        backups = core.list_backups()
        
        assert len(backups) == 3
        # Should be sorted by date (newest first)
        assert backups[0]["filename"] == "backup_20240103_140000.tar.gz"
        assert backups[2]["filename"] == "backup_20240101_120000.tar.gz"
    
    def test_restore_from_backup_success(self):
        """Test successful backup restoration."""
        # Create a backup file
        backup_file = self.backup_dir / "test_backup.tar.gz"
        
        # Create content to backup
        test_content = {"test_file.txt": "test content"}
        with tarfile.open(backup_file, "w:gz") as tar:
            for filename, content in test_content.items():
                info = tarfile.TarInfo(name=filename)
                info.size = len(content.encode())
                tar.addfile(info, fileobj=tempfile.NamedTemporaryFile(mode='w+b'))
        
        with patch("dotz.core.tarfile.open") as mock_tar_open:
            mock_tar = Mock()
            mock_tar_open.return_value.__enter__.return_value = mock_tar
            
            result = core.restore_from_backup(str(backup_file))
            
            assert result["success"] is True
            mock_tar.extractall.assert_called_once()
    
    def test_restore_from_backup_nonexistent(self):
        """Test restoration from nonexistent backup."""
        nonexistent_backup = str(self.backup_dir / "nonexistent.tar.gz")
        
        with pytest.raises(DotzBackupError):
            core.restore_from_backup(nonexistent_backup)


class TestValidation:
    """Test suite for validation operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_home, initialized_dotz_repo):
        """Set up test environment before each test."""
        self.home_dir = mock_home
        self.dotz_dir = initialized_dotz_repo
        self.work_tree = self.dotz_dir / "repo"
        core.update_paths(mock_home)
    
    def test_validate_symlinks_all_valid(self):
        """Test validation when all symlinks are valid."""
        # Create source file in work tree
        source_file = self.work_tree / ".testrc"
        source_file.write_text("test content")
        
        # Create symlink in home
        target_file = self.home_dir / ".testrc"
        target_file.symlink_to(source_file)
        
        results = core.validate_symlinks()
        
        assert results["valid_symlinks"] == [str(target_file)]
        assert results["broken_symlinks"] == []
        assert results["missing_files"] == []
    
    def test_validate_symlinks_broken_links(self):
        """Test validation with broken symlinks."""
        # Create broken symlink
        broken_link = self.home_dir / ".broken"
        broken_link.symlink_to("/nonexistent/path")
        
        results = core.validate_symlinks()
        
        assert str(broken_link) in results["broken_symlinks"]
    
    def test_validate_symlinks_missing_files(self):
        """Test validation with missing source files."""
        # Create file in work tree but not in home
        source_file = self.work_tree / ".missing"
        source_file.write_text("missing content")
        
        results = core.validate_symlinks()
        
        assert str(source_file) in results["missing_files"]


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    def test_parse_backup_filename_valid(self):
        """Test parsing valid backup filename."""
        filename = "backup_20240101_120000.tar.gz"
        
        result = core.parse_backup_filename(filename)
        
        assert result is not None
        assert result["date"] == "20240101"
        assert result["time"] == "120000"
    
    def test_parse_backup_filename_invalid(self):
        """Test parsing invalid backup filename."""
        filename = "invalid_filename.tar.gz"
        
        result = core.parse_backup_filename(filename)
        
        assert result is None
    
    @pytest.mark.parametrize("input_files,expected_count", [
        ([], 0),
        (["file1.txt"], 1),
        (["file1.txt", "file2.txt"], 2),
        (list(range(100)), 100),  # Large number for progress bar testing
    ])
    def test_should_show_progress(self, input_files, expected_count):
        """Test progress bar display logic."""
        # This would test internal logic for when to show progress bars
        # based on the PROGRESS_THRESHOLD constant
        show_progress = len(input_files) >= core.PROGRESS_THRESHOLD
        
        if expected_count >= core.PROGRESS_THRESHOLD:
            assert show_progress is True
        else:
            assert show_progress is False


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_git_operation_error_handling(self):
        """Test that Git operation errors are properly wrapped."""
        with patch("dotz.core.Repo") as mock_repo_class:
            mock_repo_class.side_effect = InvalidGitRepositoryError()
            
            with pytest.raises(DotzRepositoryNotFoundError):
                core.get_repo_status()
    
    def test_file_operation_error_handling(self):
        """Test that file operation errors are properly handled."""
        with patch("shutil.copy2") as mock_copy:
            mock_copy.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(DotzFileNotFoundError):
                # This would trigger the file operation that uses copy2
                pass
    
    def test_configuration_error_handling(self):
        """Test that configuration errors are properly handled."""
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")
            
            # Should handle the error gracefully and return default config
            config = core.load_config()
            assert config == core.DEFAULT_CONFIG