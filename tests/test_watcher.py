"""Tests for dotz.watcher module."""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from watchdog.events import FileCreatedEvent, FileModifiedEvent

from dotz import watcher
from tests.conftest import create_test_files


class TestWatcherPaths:
    """Test watcher path management."""

    def test_get_watcher_paths(self, temp_home: Path) -> None:
        """Test watcher path generation."""
        paths = watcher.get_watcher_paths(temp_home)

        assert paths["home"] == temp_home
        assert paths["dotz_dir"] == temp_home / ".dotz"

    def test_update_watcher_paths(self, temp_home: Path) -> None:
        """Test updating watcher paths."""
        watcher.update_watcher_paths(temp_home)

        assert watcher.HOME == temp_home
        assert watcher.DOTZ_DIR == temp_home / ".dotz"


class TestTrackedDirectories:
    """Test tracked directory functions."""

    def test_get_tracked_dirs_empty(self, temp_home: Path) -> None:
        """Test getting tracked dirs when file doesn't exist."""
        watcher.update_watcher_paths(temp_home)
        tracked_dirs = watcher.get_tracked_dirs()

        assert tracked_dirs == []

    def test_get_tracked_dirs_with_data(self, temp_home: Path) -> None:
        """Test getting tracked dirs with existing data."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        tracked_dirs_data = ["/home/user/.config", "/home/user/.local"]
        tracked_file = dotz_dir / "tracked_dirs.json"
        tracked_file.write_text(json.dumps(tracked_dirs_data))

        watcher.update_watcher_paths(temp_home)
        tracked_dirs = watcher.get_tracked_dirs()

        assert tracked_dirs == tracked_dirs_data

    def test_get_tracked_dirs_invalid_json(self, temp_home: Path) -> None:
        """Test getting tracked dirs with invalid JSON."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        tracked_file = dotz_dir / "tracked_dirs.json"
        tracked_file.write_text("not valid json")

        watcher.update_watcher_paths(temp_home)
        tracked_dirs = watcher.get_tracked_dirs()

        assert tracked_dirs == []

    def test_get_tracked_dirs_non_list(self, temp_home: Path) -> None:
        """Test getting tracked dirs when data is not a list."""
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        tracked_file = dotz_dir / "tracked_dirs.json"
        tracked_file.write_text('{"not": "a list"}')

        watcher.update_watcher_paths(temp_home)
        tracked_dirs = watcher.get_tracked_dirs()

        assert tracked_dirs == []


class TestIsInTrackedDirectory:
    """Test checking if files are in tracked directories."""

    @patch("dotz.watcher.ensure_repo")
    def test_is_in_tracked_directory_true(
        self, mock_ensure_repo, temp_home: Path
    ) -> None:
        """Test file is in tracked directory."""
        mock_repo = Mock()
        mock_repo.git.ls_files.return_value = ".config\n.config/app.conf"
        mock_ensure_repo.return_value = mock_repo

        result = watcher.is_in_tracked_directory(Path(".config/new_file.txt"))

        assert result is True

    @patch("dotz.watcher.ensure_repo")
    def test_is_in_tracked_directory_false(
        self, mock_ensure_repo, temp_home: Path
    ) -> None:
        """Test file is not in tracked directory."""
        mock_repo = Mock()
        mock_repo.git.ls_files.return_value = ".bashrc\n.vimrc"
        mock_ensure_repo.return_value = mock_repo

        result = watcher.is_in_tracked_directory(Path(".config/new_file.txt"))

        assert result is False

    @patch("dotz.watcher.ensure_repo")
    def test_is_in_tracked_directory_parent_match(
        self, mock_ensure_repo, temp_home: Path
    ) -> None:
        """Test file's parent directory is tracked."""
        mock_repo = Mock()
        mock_repo.git.ls_files.return_value = ".config"
        mock_ensure_repo.return_value = mock_repo

        result = watcher.is_in_tracked_directory(Path(".config/subdir/deep/file.txt"))

        assert result is True


class TestDotzEventHandler:
    """Test the DotzEventHandler class."""

    def setup_method(self) -> None:
        """Set up event handler for tests."""
        with patch("dotz.watcher.load_config") as mock_load:
            mock_load.return_value = {
                "file_patterns": {
                    "include": [".*", "*.conf", "*.json"],
                    "exclude": [".cache", "*.log"],
                },
                "search_settings": {"case_sensitive": False},
            }
            self.handler = watcher.DotzEventHandler()

    def test_should_track_file_match(self) -> None:
        """Test file matching include patterns."""
        assert self.handler.should_track_file(".bashrc") is True
        assert self.handler.should_track_file("app.conf") is True
        assert self.handler.should_track_file("settings.json") is True

    def test_should_track_file_exclude(self) -> None:
        """Test file matching exclude patterns."""
        assert self.handler.should_track_file(".cache") is False
        assert self.handler.should_track_file("debug.log") is False

    def test_should_track_file_no_match(self) -> None:
        """Test file not matching include patterns."""
        assert self.handler.should_track_file("document.pdf") is False
        assert self.handler.should_track_file("script.py") is False

    @patch("dotz.watcher.add_dotfile")
    @patch("dotz.watcher.is_in_tracked_directory")
    @patch("os.path.islink")
    def test_on_created_file_tracked(
        self, mock_islink, mock_is_tracked, mock_add, temp_home: Path
    ) -> None:
        """Test handling file creation that should be tracked."""
        mock_islink.return_value = False  # Not a symlink
        mock_is_tracked.return_value = False  # Not already tracked
        mock_add.return_value = True

        # Create event for a dotfile
        event = FileCreatedEvent(str(temp_home / ".new_config"))
        event.is_directory = False

        with patch("pathlib.Path.home", return_value=temp_home):
            self.handler.on_created(event)

        # Should have called add_dotfile
        mock_add.assert_called_once()

    @patch("dotz.watcher.add_dotfile")
    @patch("dotz.watcher.is_in_tracked_directory")
    @patch("os.path.islink")
    def test_on_created_file_already_tracked(
        self, mock_islink, mock_is_tracked, mock_add, temp_home: Path
    ) -> None:
        """Test handling file creation for already tracked file."""
        mock_islink.return_value = False  # Not a symlink
        mock_is_tracked.return_value = True  # Already tracked

        # Create event for a dotfile
        event = FileCreatedEvent(str(temp_home / ".new_config"))
        event.is_directory = False

        with patch("pathlib.Path.home", return_value=temp_home):
            self.handler.on_created(event)

        # Should not have called add_dotfile
        mock_add.assert_not_called()

    @patch("dotz.watcher.add_dotfile")
    @patch("os.path.islink")
    def test_on_created_symlink_ignored(
        self, mock_islink, mock_add, temp_home: Path
    ) -> None:
        """Test that symlink creation is ignored."""
        mock_islink.return_value = True  # Is a symlink

        # Create event for a symlink
        event = FileCreatedEvent(str(temp_home / ".symlink"))
        event.is_directory = False

        self.handler.on_created(event)

        # Should not have called add_dotfile
        mock_add.assert_not_called()

    def test_on_created_directory_ignored(self, temp_home: Path) -> None:
        """Test that directory creation is ignored."""
        with patch("dotz.watcher.add_dotfile") as mock_add:
            # Create event for a directory
            event = FileCreatedEvent(str(temp_home / ".new_dir"))
            event.is_directory = True

            self.handler.on_created(event)

            # Should not have called add_dotfile
            mock_add.assert_not_called()

    @patch("dotz.watcher.add_dotfile")
    @patch("dotz.watcher.is_in_tracked_directory")
    @patch("os.path.islink")
    def test_on_created_file_not_tracked(
        self, mock_islink, mock_is_tracked, mock_add, temp_home: Path
    ) -> None:
        """Test handling file creation for file that shouldn't be tracked."""
        mock_islink.return_value = False  # Not a symlink
        mock_is_tracked.return_value = False  # Not already tracked

        # Create event for a non-matching file
        event = FileCreatedEvent(str(temp_home / "document.pdf"))
        event.is_directory = False

        with patch("pathlib.Path.home", return_value=temp_home):
            self.handler.on_created(event)

        # Should not have called add_dotfile (doesn't match patterns)
        mock_add.assert_not_called()

    @patch("dotz.watcher.load_config")
    def test_on_modified_config_reload(self, mock_load, temp_home: Path) -> None:
        """Test config reload when config file is modified."""
        new_config = {
            "file_patterns": {"include": ["*.new"], "exclude": []},
            "search_settings": {"case_sensitive": True},
        }
        mock_load.return_value = new_config

        # Create event for config file modification
        config_path = str(temp_home / ".dotz" / "config.json")
        event = FileModifiedEvent(config_path)

        self.handler.on_modified(event)

        # Config should have been reloaded
        mock_load.assert_called_once()
        assert self.handler.config == new_config

    def test_on_modified_non_config(self, temp_home: Path) -> None:
        """Test that non-config file modifications don't reload config."""
        old_config = self.handler.config

        with patch("dotz.watcher.load_config") as mock_load:
            # Create event for non-config file
            event = FileModifiedEvent(str(temp_home / ".bashrc"))

            self.handler.on_modified(event)

            # Config should not have been reloaded
            mock_load.assert_not_called()
            assert self.handler.config == old_config

    def test_on_created_bytes_filename(self, temp_home: Path) -> None:
        """Test handling file creation with bytes filename."""
        with (
            patch("dotz.watcher.add_dotfile") as mock_add,
            patch("dotz.watcher.is_in_tracked_directory") as mock_is_tracked,
            patch("os.path.islink") as mock_islink,
            patch("os.path.basename") as mock_basename,
        ):
            mock_islink.return_value = False
            mock_is_tracked.return_value = False
            mock_basename.return_value = b".bashrc"  # Return bytes
            mock_add.return_value = True

            event = FileCreatedEvent(str(temp_home / ".bashrc"))
            event.is_directory = False

            with patch("pathlib.Path.home", return_value=temp_home):
                # Should not raise an exception
                self.handler.on_created(event)


class TestWatcherMain:
    """Test the main watcher function."""

    @patch("dotz.watcher.Observer")
    @patch("dotz.watcher.get_tracked_dirs")
    def test_main_no_tracked_dirs(
        self, mock_get_dirs, mock_observer_class, temp_home: Path
    ) -> None:
        """Test main function when no directories are tracked."""
        mock_get_dirs.return_value = []

        with patch("builtins.print") as mock_print:
            watcher.main()

            mock_print.assert_called_with(
                "No tracked directories. Add one with dotz add <dir>"
            )

    @patch("dotz.watcher.Observer")
    @patch("dotz.watcher.get_tracked_dirs")
    @patch("time.sleep")
    def test_main_with_tracked_dirs(
        self, mock_sleep, mock_get_dirs, mock_observer_class, temp_home: Path
    ) -> None:
        """Test main function with tracked directories."""
        mock_get_dirs.return_value = ["/home/user/.config", "/home/user/.local"]
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        # Simulate KeyboardInterrupt after one sleep
        mock_sleep.side_effect = KeyboardInterrupt()

        watcher.main()

        # Should have scheduled directories for watching
        assert mock_observer.schedule.call_count == 2
        mock_observer.start.assert_called_once()
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()

    @patch("dotz.watcher.Observer")
    @patch("dotz.watcher.get_tracked_dirs")
    @patch("time.sleep")
    def test_main_keyboard_interrupt(
        self, mock_sleep, mock_get_dirs, mock_observer_class, temp_home: Path
    ) -> None:
        """Test main function handles KeyboardInterrupt properly."""
        mock_get_dirs.return_value = ["/home/user/.config"]
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        # Simulate KeyboardInterrupt
        mock_sleep.side_effect = KeyboardInterrupt()

        # Should not raise exception
        watcher.main()

        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()


class TestIntegration:
    """Integration tests for watcher functionality."""

    def test_event_handler_with_real_config(self, temp_home: Path) -> None:
        """Test event handler with real configuration loading."""
        # Create dotz directory and config
        dotz_dir = temp_home / ".dotz"
        dotz_dir.mkdir()

        config = {
            "file_patterns": {"include": [".*", "*.txt"], "exclude": ["*.log"]},
            "search_settings": {"case_sensitive": False},
        }

        config_file = dotz_dir / "config.json"
        config_file.write_text(json.dumps(config))

        with patch("dotz.watcher.DOTZ_DIR", dotz_dir):
            handler = watcher.DotzEventHandler()

            # Test file matching
            assert handler.should_track_file(".bashrc") is True
            assert handler.should_track_file("notes.txt") is True
            assert handler.should_track_file("debug.log") is False

    @patch("dotz.watcher.ensure_repo")
    def test_tracked_directory_check_integration(
        self, mock_ensure_repo, temp_home: Path
    ) -> None:
        """Test tracked directory checking with realistic scenarios."""
        # Mock repo with some tracked files
        mock_repo = Mock()
        mock_repo.git.ls_files.return_value = (
            ".config\n" ".config/app/settings.json\n" ".bashrc\n" ".vimrc"
        )
        mock_ensure_repo.return_value = mock_repo

        # Test various file paths
        assert watcher.is_in_tracked_directory(Path(".config/new.conf")) is True
        assert watcher.is_in_tracked_directory(Path(".config/app/new.conf")) is True
        assert watcher.is_in_tracked_directory(Path(".bashrc")) is True
        assert watcher.is_in_tracked_directory(Path(".local/new.conf")) is False
        assert watcher.is_in_tracked_directory(Path("Documents/file.txt")) is False
