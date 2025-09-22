"""Tests for dotz CLI functionality."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from dotz.cli import app


class TestCLIBasics:
    """Test basic CLI functionality."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dotz - a Git-backed dotfiles manager" in result.stdout

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.4.0" in result.stdout

    def test_completion_command(self):
        """Test completion command."""
        result = self.runner.invoke(app, ["completion"])
        assert result.exit_code == 0
        assert (
            "install-completion" in result.stdout.lower()
            or "shell completion" in result.stdout.lower()
        )


class TestCLICommands:
    """Test CLI commands that require mocking."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_diagnose_command(self):
        """Test diagnose command runs without error."""
        result = self.runner.invoke(app, ["diagnose"])
        # Just verify it doesn't crash - the output will vary by system
        assert result.exit_code == 0

    @patch("dotz.cli.get_repo_status")
    def test_status_command_no_repo(self, mock_status):
        """Test status command when no repository exists."""
        from dotz.exceptions import DotzRepositoryNotFoundError

        mock_status.side_effect = DotzRepositoryNotFoundError("No repository found")
        result = self.runner.invoke(app, ["status"])
        assert result.exit_code != 0
        assert "No repository found" in result.stdout

    @patch("dotz.cli.list_tracked_files")
    @patch("dotz.cli.get_dotz_paths")
    def test_list_files_command(self, mock_paths, mock_list):
        """Test list-files command."""
        mock_paths.return_value = {"repo_dir": "/fake/path"}
        mock_list.return_value = ["/home/user/.bashrc", "/home/user/.vimrc"]

        result = self.runner.invoke(app, ["list-files"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


class TestConfigCommands:
    """Test configuration-related CLI commands."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.load_config")
    def test_config_show(self, mock_load):
        """Test config show command."""
        mock_config = {
            "include_patterns": [".*"],
            "exclude_patterns": [".git"],
        }
        mock_load.return_value = mock_config

        result = self.runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        mock_load.assert_called_once()

    @patch("dotz.cli.add_file_pattern")
    def test_config_add_pattern(self, mock_add):
        """Test config add-pattern command."""
        result = self.runner.invoke(app, ["config", "add-pattern", "*.py"])
        assert result.exit_code == 0
        mock_add.assert_called_once_with("*.py", "include")

    @patch("dotz.cli.remove_file_pattern")
    def test_config_remove_pattern(self, mock_remove):
        """Test config remove-pattern command."""
        result = self.runner.invoke(app, ["config", "remove-pattern", "*.log"])
        assert result.exit_code == 0
        mock_remove.assert_called_once_with("*.log", "include")
