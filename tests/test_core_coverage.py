"""
Additional tests to improve coverage for loom core functionality.
These tests focus on edge cases and error conditions not covered by existing tests.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import GitCommandError

import loom.core as core
from loom.core import (
    add_dotfile,
    count_files_in_directory,
    delete_dotfile,
    ensure_repo,
    find_config_files,
    get_config_value,
    get_repo_status,
    init_repo,
    list_tracked_files,
    load_config,
    pull_repo,
    push_repo,
    remove_tracked_dir,
    restore_dotfile,
    save_config,
    save_tracked_dir,
    update_paths,
)


class TestCoreEdgeCases:
    """Test edge cases and error conditions in core functionality."""

    def test_count_files_in_directory_file(self, temp_home: Path) -> None:
        """Test counting files when path is a file."""
        test_file = temp_home / "test.txt"
        test_file.write_text("content")

        count = count_files_in_directory(test_file)
        assert count == 1

    def test_count_files_in_directory_nonexistent(self, temp_home: Path) -> None:
        """Test counting files when path doesn't exist."""
        nonexistent = temp_home / "nonexistent"

        count = count_files_in_directory(nonexistent)
        assert count == 0

    def test_count_files_in_directory_empty_dir(self, temp_home: Path) -> None:
        """Test counting files in empty directory."""
        empty_dir = temp_home / "empty"
        empty_dir.mkdir()

        count = count_files_in_directory(empty_dir)
        assert count == 0

    def test_save_tracked_dir_new_file(self, initialized_loom: Path) -> None:
        """Test saving tracked directory when file doesn't exist."""
        test_dir = initialized_loom / "newdir"
        test_dir.mkdir()

        # Remove tracked_dirs.json if it exists
        tracked_file = initialized_loom / ".loom" / "tracked_dirs.json"
        if tracked_file.exists():
            tracked_file.unlink()

        save_tracked_dir(test_dir)

        # Verify file was created and contains the directory
        assert tracked_file.exists()
        with open(tracked_file) as f:
            tracked = json.load(f)
        assert str(test_dir) in tracked

    def test_remove_tracked_dir_nonexistent_file(self, initialized_loom: Path) -> None:
        """Test removing tracked directory when file doesn't exist."""
        test_dir = initialized_loom / "testdir"

        # Ensure file doesn't exist
        tracked_file = initialized_loom / ".loom" / "tracked_dirs.json"
        if tracked_file.exists():
            tracked_file.unlink()

        # Should not raise error
        remove_tracked_dir(test_dir)

    def test_add_dotfile_already_symlinked(self, initialized_loom: Path) -> None:
        """Test adding a file that's already properly symlinked."""
        home = initialized_loom

        # Create a dotfile and add it normally
        dotfile = home / ".testrc"
        dotfile.write_text("test config")
        result1 = add_dotfile(Path(".testrc"), quiet=True)
        assert result1 is True

        # Try to add again - should return True without error
        result2 = add_dotfile(Path(".testrc"), quiet=True)
        assert result2 is True

    def test_add_dotfile_invalid_type(self, initialized_loom: Path) -> None:
        """Test adding something that's not a file or directory."""
        home = initialized_loom

        # Test with a non-existent path that would fail the exists check first
        nonexistent = Path(".nonexistent")
        result = add_dotfile(nonexistent, quiet=True)
        assert result is False

    def test_delete_dotfile_not_in_repo(self, initialized_loom: Path) -> None:
        """Test deleting a symlink that doesn't exist in repo."""
        home = initialized_loom
        repo_dir = home / ".loom" / "repo"

        # Create a symlink pointing to a non-existent repo file
        fake_target = repo_dir / ".fake"
        symlink = home / ".fake"
        symlink.symlink_to(fake_target)

        result = delete_dotfile(Path(".fake"), quiet=True)
        assert result is False

    def test_restore_dotfile_existing_file(self, initialized_loom: Path) -> None:
        """Test restoring when a regular file exists at target location."""
        home = initialized_loom

        # Add a dotfile first
        dotfile = home / ".restoretest"
        dotfile.write_text("original")
        add_dotfile(Path(".restoretest"), quiet=True)

        # Remove symlink and create a regular file
        dotfile.unlink()
        dotfile.write_text("different content")

        # Restore should replace the file
        result = restore_dotfile(Path(".restoretest"), quiet=True)
        assert result is True
        assert dotfile.is_symlink()

    def test_restore_dotfile_existing_directory(self, initialized_loom: Path) -> None:
        """Test restoring when a directory exists at target location."""
        home = initialized_loom

        # Add a dotfile first
        dotfile = home / ".restoredirtest"
        dotfile.write_text("original")
        add_dotfile(Path(".restoredirtest"), quiet=True)

        # Remove symlink and create a directory
        dotfile.unlink()
        dotfile.mkdir()
        (dotfile / "somefile").write_text("content")

        # Restore should replace the directory
        result = restore_dotfile(Path(".restoredirtest"), quiet=True)
        assert result is True
        assert dotfile.is_symlink()

    def test_pull_repo_no_origin(self, initialized_loom: Path) -> None:
        """Test pulling when no origin remote exists."""
        result = pull_repo(quiet=True)
        assert result is False

    def test_pull_repo_no_tracking_branch(self, initialized_loom: Path) -> None:
        """Test pulling when no tracking branch is set."""
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock the pull method by patching the Remote class
        with (
            patch("loom.core.GitCommandError", GitCommandError),
            patch("git.Remote.pull") as mock_pull,
        ):
            mock_pull.side_effect = GitCommandError(
                "git pull", "no tracking information"
            )
            result = pull_repo(quiet=True)
            assert result is False

    def test_pull_repo_divergent_branches(self, initialized_loom: Path) -> None:
        """Test pulling when branches have diverged."""
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock the pull method by patching the Remote class
        with (
            patch("loom.core.GitCommandError", GitCommandError),
            patch("git.Remote.pull") as mock_pull,
        ):
            mock_pull.side_effect = GitCommandError("git pull", "divergent branches")
            result = pull_repo(quiet=True)
            assert result is False

    def test_push_repo_no_origin(self, initialized_loom: Path) -> None:
        """Test pushing when no origin remote exists."""
        result = push_repo(quiet=True)
        assert result is False

    def test_push_repo_non_fast_forward(self, initialized_loom: Path) -> None:
        """Test pushing when push is rejected (non-fast-forward)."""
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock push result with error
        mock_push_info = MagicMock()
        mock_push_info.flags = mock_push_info.ERROR
        mock_push_info.summary = "non-fast-forward"

        with patch("git.Remote.push") as mock_push:
            mock_push.return_value = [mock_push_info]
            result = push_repo(quiet=True)
            assert result is False

    def test_push_repo_git_command_error(self, initialized_loom: Path) -> None:
        """Test pushing when git command fails."""
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        with patch("git.Remote.push") as mock_push:
            mock_push.side_effect = GitCommandError("git push", "no upstream branch")
            result = push_repo(quiet=True)
            assert result is False

    def test_get_repo_status_with_remote(self, initialized_loom: Path) -> None:
        """Test getting repo status when remote exists."""
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Create some changes
        test_file = initialized_loom / ".statustest"
        test_file.write_text("content")
        add_dotfile(Path(".statustest"), quiet=True)

        status = get_repo_status()
        assert "untracked" in status
        assert "modified" in status
        assert "staged" in status
        assert "unpushed" in status
        assert "untracked_home_dotfiles" in status

    def test_find_config_files_follow_symlinks(self, initialized_loom: Path) -> None:
        """Test finding config files with follow_symlinks setting."""
        home = initialized_loom

        # Create config with follow_symlinks=True
        config = load_config()
        config["search_settings"]["follow_symlinks"] = True
        save_config(config)

        # Create a symlinked config file
        real_file = home / "real_config.conf"
        real_file.write_text("config")
        symlink = home / "symlinked.conf"
        symlink.symlink_to(real_file)

        found = find_config_files(home, config, recursive=False)
        symlink_found = any(f.name == "symlinked.conf" for f in found)
        assert symlink_found

    def test_find_config_files_ignore_symlinks(self, initialized_loom: Path) -> None:
        """Test finding config files with follow_symlinks=False."""
        home = initialized_loom

        # Create config with follow_symlinks=False (default)
        config = load_config()
        config["search_settings"]["follow_symlinks"] = False
        save_config(config)

        # Create a symlinked config file
        real_file = home / "real_config2.conf"
        real_file.write_text("config")
        symlink = home / "symlinked2.conf"
        symlink.symlink_to(real_file)

        found = find_config_files(home, config, recursive=False)
        symlink_found = any(f.name == "symlinked2.conf" for f in found)
        assert not symlink_found

    def test_load_config_key_error(self, initialized_loom: Path) -> None:
        """Test loading config with JSON decode error."""
        config_file = initialized_loom / ".loom" / "config.json"

        # Create invalid JSON
        with open(config_file, "w") as f:
            f.write("{invalid json")

        config = load_config()
        # Should return defaults when config is malformed
        assert "file_patterns" in config
        assert "include" in config["file_patterns"]

    def test_update_paths(self, temp_home: Path) -> None:
        """Test updating global paths."""
        new_home = temp_home / "newhome"
        new_home.mkdir()

        # Store original values
        original_home = core.HOME

        # Update paths
        update_paths(new_home)

        # Verify paths were updated
        assert core.HOME == new_home
        assert core.LOOM_DIR == new_home / ".loom"

        # Restore original paths
        update_paths(original_home)


class TestCorePushPullWithPush:
    """Test push/pull scenarios with actual push parameter."""

    def test_add_dotfile_with_push_success(self, initialized_loom: Path) -> None:
        """Test adding dotfile with push=True when push succeeds."""
        home = initialized_loom
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock successful push
        mock_push_info = MagicMock()
        mock_push_info.flags = 0  # No error
        mock_push_info.ERROR = 1024  # Define ERROR flag for the mock

        with patch("git.Remote.push") as mock_push:
            mock_push.return_value = [mock_push_info]

            dotfile = home / ".pushtest"
            dotfile.write_text("content")
            result = add_dotfile(Path(".pushtest"), push=True, quiet=True)
            assert result is True

    def test_add_dotfile_with_push_failure(self, initialized_loom: Path) -> None:
        """Test adding dotfile with push=True when push fails."""
        home = initialized_loom
        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        with patch("git.Remote.push") as mock_push:
            mock_push.side_effect = GitCommandError("push", "failed")

            dotfile = home / ".pushfailtest"
            dotfile.write_text("content")
            result = add_dotfile(Path(".pushfailtest"), push=True, quiet=True)
            assert result is False

    def test_delete_dotfile_with_push_success(self, initialized_loom: Path) -> None:
        """Test deleting dotfile with push=True when push succeeds."""
        home = initialized_loom

        # Add file first
        dotfile = home / ".deletetest"
        dotfile.write_text("content")
        add_dotfile(Path(".deletetest"), quiet=True)

        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock successful push
        mock_push_info = MagicMock()
        mock_push_info.flags = 0  # No error
        mock_push_info.ERROR = 1024  # Define ERROR flag for the mock

        with patch("git.Remote.push") as mock_push:
            mock_push.return_value = [mock_push_info]

            result = delete_dotfile(Path(".deletetest"), push=True, quiet=True)
            assert result is True

    def test_restore_dotfile_with_push_success(self, initialized_loom: Path) -> None:
        """Test restoring dotfile with push=True when push succeeds."""
        home = initialized_loom

        # Add file first
        dotfile = home / ".restoretest2"
        dotfile.write_text("content")
        add_dotfile(Path(".restoretest2"), quiet=True)

        # Remove symlink
        dotfile.unlink()

        repo = ensure_repo()
        repo.create_remote("origin", "https://github.com/fake/repo.git")

        # Mock successful push
        mock_push_info = MagicMock()
        mock_push_info.flags = 0  # No error
        mock_push_info.ERROR = 1024  # Define ERROR flag for the mock

        with patch("git.Remote.push") as mock_push:
            mock_push.return_value = [mock_push_info]

            result = restore_dotfile(Path(".restoretest2"), push=True, quiet=True)
            assert result is True
