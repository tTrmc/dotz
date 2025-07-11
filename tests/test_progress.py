"""Tests for progress indicators in dotz CLI operations."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from dotz import cli, core


class TestProgressIndicators:
    """Test progress indicator functionality."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_add_dotfiles_with_progress_many_files(self, temp_home: Path):
        """Test progress bar appears for many files."""
        # Create many files to trigger progress bar
        config_dir = temp_home / ".config"
        config_dir.mkdir(parents=True)

        files = []
        for i in range(60):  # Above progress bar threshold
            file_path = config_dir / f"config{i}.conf"
            file_path.write_text(f"config {i}")
            files.append(file_path)

        with patch("dotz.core.add_dotfile") as mock_add:
            mock_add.return_value = True

            with patch("dotz.core.Progress") as mock_progress:
                mock_progress_instance = MagicMock()
                mock_progress.return_value.__enter__.return_value = (
                    mock_progress_instance
                )

                result = core.add_dotfiles_with_progress(files, push=False, quiet=False)

                # Should process all files successfully
                assert result["success"] == 60
                assert result["failed"] == 0

                # Progress bar should be used
                mock_progress.assert_called_once()
                mock_progress_instance.add_task.assert_called_once()

    def test_add_dotfiles_with_progress_quiet_mode(self, temp_home: Path):
        """Test no progress bar in quiet mode."""
        files = [temp_home / ".bashrc", temp_home / ".vimrc"]
        for f in files:
            f.write_text("test content")

        with patch("dotz.core.add_dotfile") as mock_add:
            mock_add.return_value = True

            with patch("dotz.core.Progress") as mock_progress:
                result = core.add_dotfiles_with_progress(files, push=False, quiet=True)

                # Should process all files
                assert result["success"] == 2
                assert result["failed"] == 0

                # Progress should not be used in quiet mode
                mock_progress.assert_not_called()

    def test_add_dotfiles_with_progress_failures(self, temp_home: Path):
        """Test handling of failures during add operations."""
        files = [temp_home / ".bashrc", temp_home / ".vimrc", temp_home / ".zshrc"]
        for f in files:
            f.write_text("test content")

        with patch("dotz.core.add_dotfile") as mock_add:
            # Make some additions fail
            mock_add.side_effect = [True, False, True]

            result = core.add_dotfiles_with_progress(files, push=False, quiet=True)

            # Should track successes and failures
            assert result["success"] == 2
            assert result["failed"] == 1

    def test_restore_dotfiles_with_progress(self, temp_home: Path):
        """Test progress bar for restore operations."""
        files = []
        for i in range(50):
            file_path = temp_home / f"dotfile{i}.conf"
            file_path.write_text(f"dotfile {i}")
            files.append(file_path)

        with patch("dotz.core.restore_dotfile") as mock_restore:
            mock_restore.return_value = True

            with patch("dotz.core.Progress") as mock_progress:
                mock_progress_instance = MagicMock()
                mock_progress.return_value.__enter__.return_value = (
                    mock_progress_instance
                )

                result = core.restore_dotfiles_with_progress(files, quiet=False)

                # Should process all files
                assert result["success"] == 50
                assert result["failed"] == 0

                # Progress bar should be used
                mock_progress.assert_called_once()

    def test_find_config_files_with_progress_large_directory(self, temp_home: Path):
        """Test progress bar for scanning large directories."""
        # Create a large directory structure
        large_dir = temp_home / "large_config"
        large_dir.mkdir()

        # Create 100 files to trigger progress bar
        for i in range(100):
            file_path = large_dir / f"config{i}.conf"
            file_path.write_text(f"config {i}")

        with patch("dotz.core.find_config_files") as mock_find:
            mock_find.return_value = []

            with patch("dotz.core.Progress") as mock_progress:
                mock_progress_instance = MagicMock()
                mock_progress.return_value.__enter__.return_value = (
                    mock_progress_instance
                )

                result = core.find_config_files_with_progress(large_dir, quiet=False)

                # Should return a list
                assert isinstance(result, list)

                # Progress bar should be used for large directories
                mock_progress.assert_called_once()

    def test_find_config_files_with_progress_small_directory(self, temp_home: Path):
        """Test no progress bar for small directories."""
        # Create only a few files
        small_dir = temp_home / "small_config"
        small_dir.mkdir()

        files = []
        for i in range(10):  # Below progress bar threshold
            file_path = small_dir / f"config{i}.conf"
            file_path.write_text(f"config {i}")
            files.append(file_path)

        with patch("dotz.core.find_config_files") as mock_find:
            mock_find.return_value = files

            result = core.find_config_files_with_progress(small_dir, quiet=False)

            # Should use the regular function for small directories
            mock_find.assert_called_once()
            assert result == files

    def test_progress_with_push(self, temp_home: Path):
        """Test progress with push operation."""
        files = [temp_home / ".bashrc", temp_home / ".vimrc"]
        for f in files:
            f.write_text("test content")

        with patch("dotz.core.add_dotfile") as mock_add:
            with patch("dotz.core.push_repo") as mock_push:
                mock_add.return_value = True
                mock_push.return_value = True

                result = core.add_dotfiles_with_progress(files, push=True, quiet=True)

                # Should succeed and push
                assert result["success"] == 2
                mock_push.assert_called_once_with(quiet=True)

    def test_progress_no_push_on_failures(self, temp_home: Path):
        """Test no push when all operations fail."""
        files = [temp_home / ".bashrc", temp_home / ".vimrc"]
        for f in files:
            f.write_text("test content")

        with patch("dotz.core.add_dotfile") as mock_add:
            with patch("dotz.core.push_repo") as mock_push:
                mock_add.return_value = False  # All operations fail

                result = core.add_dotfiles_with_progress(files, push=True, quiet=True)

                # Should fail and not push
                assert result["success"] == 0
                assert result["failed"] == 2
                mock_push.assert_not_called()

    def test_empty_file_list(self):
        """Test handling of empty file lists."""
        result = core.add_dotfiles_with_progress([], push=False, quiet=False)

        assert result["success"] == 0
        assert result["failed"] == 0

    @patch("dotz.core.add_dotfiles_with_progress")
    @patch("dotz.core.find_config_files")
    @patch("dotz.core.load_config")
    def test_cli_add_directory_with_progress(
        self, mock_load_config, mock_find, mock_add_progress, temp_home: Path
    ):
        """Test CLI add command triggers progress for directories."""
        # Setup
        config_dir = temp_home / ".config"
        config_dir.mkdir(parents=True)

        files = []
        for i in range(60):
            file_path = config_dir / f"config{i}.conf"
            file_path.write_text(f"config {i}")
            files.append(file_path)

        mock_load_config.return_value = {
            "file_patterns": {"include": ["*"], "exclude": []}
        }
        mock_find.return_value = files
        mock_add_progress.return_value = {"success": 60, "failed": 0}

        with patch("dotz.cli.refresh_cli_paths"):
            result = self.runner.invoke(
                cli.app, ["add", str(config_dir), "--recursive"]
            )

        # Should succeed and use progress function
        assert result.exit_code == 0
        mock_add_progress.assert_called_once()

    @patch("dotz.core.add_dotfile")
    def test_cli_add_single_file_with_status(self, mock_add, temp_home: Path):
        """Test CLI add command shows status for single file."""
        # Create test file
        test_file = temp_home / ".bashrc"
        test_file.write_text("test content")

        mock_add.return_value = True

        with patch("dotz.cli.refresh_cli_paths"):
            result = self.runner.invoke(cli.app, ["add", str(test_file)])

        assert result.exit_code == 0
        mock_add.assert_called_once()

    @patch("dotz.core.restore_dotfiles_with_progress")
    @patch("dotz.core.list_tracked_files")
    def test_cli_restore_all_with_progress(
        self, mock_list, mock_restore_progress, temp_home: Path
    ):
        """Test CLI restore-all command uses progress indicators."""
        # Setup many tracked files
        tracked_files = [f".config/app{i}/config.conf" for i in range(50)]
        mock_list.return_value = tracked_files
        mock_restore_progress.return_value = {"success": 50, "failed": 0}

        with patch("dotz.cli.refresh_cli_paths"):
            with patch("dotz.cli.HOME", temp_home):
                with patch("typer.confirm", return_value=True):
                    result = self.runner.invoke(cli.app, ["restore-all"])

        # Should succeed and use progress function
        assert result.exit_code == 0
        mock_restore_progress.assert_called_once()

    def test_progress_indicators_imports(self):
        """Test that progress indicator modules import correctly."""
        from rich.console import Console
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
        from rich.status import Status

        # Should be able to create instances
        console = Console()
        assert console is not None

        # Test progress bar components
        progress = Progress(
            SpinnerColumn(),
            TextColumn("test"),
            BarColumn(),
        )
        assert progress is not None

        # Test status
        status = Status("test")
        assert status is not None
