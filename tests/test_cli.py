"""Tests for dotz.cli module."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from dotz import cli, core
from tests.conftest import create_test_files


class TestCLIHelpers:
    """Test CLI helper functions."""

    def test_get_cli_paths(self, temp_home: Path) -> None:
        """Test CLI path generation."""
        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            home, dotz_dir, work_tree = cli.get_cli_paths()

            assert home == temp_home
            assert dotz_dir == temp_home / ".dotz"
            assert work_tree == temp_home / ".dotz" / "repo"

    def test_refresh_cli_paths(self, temp_home: Path) -> None:
        """Test refreshing CLI paths."""
        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            cli.refresh_cli_paths()

            assert cli.HOME == temp_home
            assert cli.DOTZ_DIR == temp_home / ".dotz"
            assert cli.WORK_TREE == temp_home / ".dotz" / "repo"


class TestInitCommand:
    """Test the init command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.init_repo")
    def test_init_basic(self, mock_init: Mock, temp_home: Path) -> None:
        """Test basic init command."""
        mock_init.return_value = True

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["init", "--non-interactive"])

            assert result.exit_code == 0
            mock_init.assert_called_once_with(remote="", quiet=False)

    @patch("dotz.cli.init_repo")
    def test_init_with_remote(self, mock_init: Mock, temp_home: Path) -> None:
        """Test init with remote URL."""
        mock_init.return_value = True
        remote_url = "https://github.com/user/dotfiles.git"

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(
                cli.app, ["init", "--remote", remote_url, "--non-interactive"]
            )

            assert result.exit_code == 0
            mock_init.assert_called_once_with(remote=remote_url, quiet=False)

    @patch("dotz.cli.init_repo")
    def test_init_failure(self, mock_init: Mock, temp_home: Path) -> None:
        """Test init command failure."""
        mock_init.return_value = False

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["init", "--non-interactive"])

            assert result.exit_code == 1

    @patch("dotz.cli.init_repo")
    @patch("dotz.cli.add_dotfile")
    @patch("typer.confirm")
    def test_init_interactive_with_dotfiles(
        self, mock_confirm: Mock, mock_add: Mock, mock_init: Mock, temp_home: Path
    ) -> None:
        """Test interactive init with automatic dotfile setup."""
        mock_init.return_value = True
        mock_add.return_value = True
        # No remote, auto-add dotfiles, confirm add
        mock_confirm.side_effect = [False, True, True]

        # Create some common dotfiles
        (temp_home / ".bashrc").write_text("# bashrc")
        (temp_home / ".vimrc").write_text("set number")

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["init"])

            assert result.exit_code == 0
            # Should have tried to add dotfiles
            assert mock_add.call_count >= 1


class TestAddCommand:
    """Test the add command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.core.add_dotfile")
    def test_add_file(self, mock_add: Mock, temp_home: Path) -> None:
        """Test adding a file."""
        mock_add.return_value = True

        # Create the file to add
        (temp_home / ".bashrc").write_text("# bashrc")

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["add", ".bashrc"])

        assert result.exit_code == 0
        mock_add.assert_called_once_with(
            temp_home / ".bashrc", push=False, quiet=False, recursive=True
        )

    @patch("dotz.core.add_dotfile")
    def test_add_file_with_options(self, mock_add: Mock, temp_home: Path) -> None:
        """Test adding a file with options."""
        mock_add.return_value = True

        # Create the file to add
        (temp_home / ".bashrc").write_text("# bashrc")

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(
                cli.app, ["add", ".bashrc", "--push", "--quiet", "--no-recursive"]
            )

        assert result.exit_code == 0
        mock_add.assert_called_once_with(
            temp_home / ".bashrc", push=True, quiet=True, recursive=False
        )

    @patch("dotz.core.add_dotfile")
    def test_add_file_failure(self, mock_add: Mock, temp_home: Path) -> None:
        """Test add command failure."""
        mock_add.return_value = False

        result = self.runner.invoke(cli.app, ["add", ".bashrc"])

        assert result.exit_code == 1


class TestDeleteCommand:
    """Test the delete command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.delete_dotfile")
    def test_delete_file(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test deleting a file."""
        mock_delete.return_value = True

        result = self.runner.invoke(cli.app, ["delete", ".bashrc"])

        assert result.exit_code == 0
        mock_delete.assert_called_once_with([Path(".bashrc")], push=False, quiet=False)

    @patch("dotz.cli.delete_dotfile")
    def test_delete_multiple_files(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test deleting multiple files."""
        mock_delete.return_value = True

        result = self.runner.invoke(cli.app, ["delete", ".bashrc", ".vimrc"])

        assert result.exit_code == 0
        mock_delete.assert_called_once_with(
            [Path(".bashrc"), Path(".vimrc")], push=False, quiet=False
        )

    @patch("dotz.cli.delete_dotfile")
    def test_delete_with_options(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test delete with options."""
        mock_delete.return_value = True

        result = self.runner.invoke(cli.app, ["delete", ".bashrc", "--push", "--quiet"])

        assert result.exit_code == 0
        mock_delete.assert_called_once_with([Path(".bashrc")], push=True, quiet=True)

    @patch("dotz.cli.delete_dotfile")
    def test_delete_failure(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test delete command failure."""
        mock_delete.return_value = False

        result = self.runner.invoke(cli.app, ["delete", ".bashrc"])

        assert result.exit_code == 1


class TestStatusCommand:
    """Test the status command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.get_repo_status")
    def test_status_clean(self, mock_status: Mock, temp_home: Path) -> None:
        """Test status when repository is clean."""
        mock_status.return_value = {
            "untracked": [],
            "modified": [],
            "staged": [],
            "unpushed": [],
            "untracked_home_dotfiles": [],
        }

        result = self.runner.invoke(cli.app, ["status"])

        assert result.exit_code == 0
        assert "Repository is clean" in result.output

    @patch("dotz.cli.get_repo_status")
    def test_status_with_changes(self, mock_status: Mock, temp_home: Path) -> None:
        """Test status with changes."""
        mock_status.return_value = {
            "untracked": [".new_file"],
            "modified": [".bashrc"],
            "staged": [".vimrc"],
            "unpushed": [".gitconfig"],
            "untracked_home_dotfiles": [".zshrc"],
        }

        result = self.runner.invoke(cli.app, ["status"])

        assert result.exit_code == 0
        assert "Untracked files:" in result.output
        assert "Modified files:" in result.output
        assert "Staged files:" in result.output
        assert "Unpushed changes:" in result.output
        assert "Untracked dotfiles in home directory:" in result.output


class TestListFilesCommand:
    """Test the list-files command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.list_tracked_files")
    def test_list_files_empty(self, mock_list: Mock, temp_home: Path) -> None:
        """Test listing when no files are tracked."""
        mock_list.return_value = []

        result = self.runner.invoke(cli.app, ["list-files"])

        assert result.exit_code == 0
        assert "No files tracked" in result.output

    @patch("dotz.cli.list_tracked_files")
    def test_list_files_with_files(self, mock_list: Mock, temp_home: Path) -> None:
        """Test listing tracked files."""
        mock_list.return_value = [".bashrc", ".vimrc", ".gitconfig"]

        result = self.runner.invoke(cli.app, ["list-files"])

        assert result.exit_code == 0
        assert ".bashrc" in result.output
        assert ".vimrc" in result.output
        assert ".gitconfig" in result.output


class TestRestoreCommand:
    """Test the restore command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.restore_dotfile")
    def test_restore_file(self, mock_restore: Mock, temp_home: Path) -> None:
        """Test restoring a file."""
        mock_restore.return_value = True

        result = self.runner.invoke(cli.app, ["restore", ".bashrc"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(Path(".bashrc"), quiet=False, push=False)

    @patch("dotz.cli.restore_dotfile")
    def test_restore_with_options(self, mock_restore: Mock, temp_home: Path) -> None:
        """Test restore with options."""
        mock_restore.return_value = True

        result = self.runner.invoke(
            cli.app, ["restore", ".bashrc", "--push", "--quiet"]
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(Path(".bashrc"), quiet=True, push=True)

    @patch("dotz.cli.restore_dotfile")
    def test_restore_failure(self, mock_restore: Mock, temp_home: Path) -> None:
        """Test restore command failure."""
        mock_restore.return_value = False

        result = self.runner.invoke(cli.app, ["restore", ".bashrc"])

        assert result.exit_code == 1


class TestPullPushCommands:
    """Test pull and push commands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.pull_repo")
    def test_pull_success(self, mock_pull: Mock, temp_home: Path) -> None:
        """Test successful pull."""
        mock_pull.return_value = True

        result = self.runner.invoke(cli.app, ["pull"])

        assert result.exit_code == 0
        mock_pull.assert_called_once_with(quiet=False)

    @patch("dotz.cli.pull_repo")
    def test_pull_failure(self, mock_pull: Mock, temp_home: Path) -> None:
        """Test pull failure."""
        mock_pull.return_value = False

        result = self.runner.invoke(cli.app, ["pull"])

        assert result.exit_code == 1

    @patch("dotz.cli.push_repo")
    def test_push_success(self, mock_push: Mock, temp_home: Path) -> None:
        """Test successful push."""
        mock_push.return_value = True

        result = self.runner.invoke(cli.app, ["push"])

        assert result.exit_code == 0
        mock_push.assert_called_once_with(quiet=False)

    @patch("dotz.cli.push_repo")
    def test_push_failure(self, mock_push: Mock, temp_home: Path) -> None:
        """Test push failure."""
        mock_push.return_value = False

        result = self.runner.invoke(cli.app, ["push"])

        assert result.exit_code == 1


class TestCloneCommand:
    """Test the clone command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.clone_repo")
    def test_clone_success(self, mock_clone: Mock, temp_home: Path) -> None:
        """Test successful clone."""
        mock_clone.return_value = True
        remote_url = "https://github.com/user/dotfiles.git"

        result = self.runner.invoke(cli.app, ["clone", remote_url])

        assert result.exit_code == 0
        mock_clone.assert_called_once_with(remote_url, quiet=False)

    @patch("dotz.cli.clone_repo")
    def test_clone_failure(self, mock_clone: Mock, temp_home: Path) -> None:
        """Test clone failure."""
        mock_clone.return_value = False
        remote_url = "https://github.com/user/dotfiles.git"

        result = self.runner.invoke(cli.app, ["clone", remote_url])

        assert result.exit_code == 1


class TestRestoreAllCommand:
    """Test the restore-all command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.core.restore_dotfiles_with_progress")
    @patch("dotz.core.list_tracked_files")
    @patch("typer.confirm")
    def test_restore_all_with_confirmation(
        self, mock_confirm: Mock, mock_list: Mock, mock_restore: Mock, temp_home: Path
    ) -> None:
        """Test restore-all with confirmation."""
        mock_list.return_value = [".bashrc", ".vimrc"]
        mock_confirm.return_value = True
        mock_restore.return_value = {"success": 2, "failed": 0}

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["restore-all"])

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("dotz.core.restore_dotfiles_with_progress")
    @patch("dotz.core.list_tracked_files")
    @patch("typer.confirm")
    def test_restore_all_cancelled(
        self, mock_confirm: Mock, mock_list: Mock, mock_restore: Mock, temp_home: Path
    ) -> None:
        """Test restore-all cancelled by user."""
        mock_list.return_value = [".bashrc", ".vimrc"]
        mock_confirm.return_value = False

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            result = self.runner.invoke(cli.app, ["restore-all"])

        assert result.exit_code == 0
        assert "cancelled" in result.output
        mock_restore.assert_not_called()

    @patch("dotz.core.restore_dotfiles_with_progress")
    def test_restore_all_skip_confirmation(
        self, mock_restore: Mock, temp_home: Path
    ) -> None:
        """Test restore-all with --yes flag."""
        mock_restore.return_value = {"success": 0, "failed": 0}

        with patch("dotz.cli.get_home_dir", return_value=temp_home):
            with patch("dotz.core.list_tracked_files", return_value=[]):
                result = self.runner.invoke(cli.app, ["restore-all", "--yes"])

        assert result.exit_code == 0
        mock_restore.assert_not_called()  # No files to restore


class TestValidateCommand:
    """Test the validate command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.validate_symlinks")
    def test_validate_success(self, mock_validate: Mock, temp_home: Path) -> None:
        """Test successful validation."""
        mock_validate.return_value = {
            "broken": [],
            "missing": [],
            "wrong_target": [],
            "not_symlink": [],
            "repair_failed": [],
        }

        result = self.runner.invoke(cli.app, ["validate"])

        assert result.exit_code == 0
        mock_validate.assert_called_once_with(repair=False, quiet=False)

    @patch("dotz.cli.validate_symlinks")
    def test_validate_with_repair(self, mock_validate: Mock, temp_home: Path) -> None:
        """Test validation with repair."""
        mock_validate.return_value = {
            "broken": [],
            "missing": [],
            "wrong_target": [],
            "not_symlink": [],
            "repair_failed": [],
        }

        result = self.runner.invoke(cli.app, ["validate", "--repair"])

        assert result.exit_code == 0
        mock_validate.assert_called_once_with(repair=True, quiet=False)

    @patch("dotz.core.validate_symlinks")
    def test_validate_with_issues(self, mock_validate: Mock, temp_home: Path) -> None:
        """Test validation with issues found."""
        mock_validate.return_value = {
            "broken": [".bashrc"],
            "missing": [".vimrc"],
            "wrong_target": [],
            "not_symlink": [],
            "repair_failed": [],
        }

        result = self.runner.invoke(cli.app, ["validate"])

        assert result.exit_code == 1  # Should exit with error if issues found

    @patch("dotz.core.validate_symlinks")
    def test_validate_failure(self, mock_validate: Mock, temp_home: Path) -> None:
        """Test validation failure."""
        mock_validate.return_value = None

        result = self.runner.invoke(cli.app, ["validate"])

        assert result.exit_code == 1


class TestConfigCommands:
    """Test config subcommands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.load_config")
    def test_config_show_all(self, mock_load: Mock, temp_home: Path) -> None:
        """Test showing all configuration."""
        mock_config = {"test": "value"}
        mock_load.return_value = mock_config

        result = self.runner.invoke(cli.app, ["config", "show"])

        assert result.exit_code == 0
        assert '"test": "value"' in result.output

    @patch("dotz.cli.get_config_value")
    def test_config_show_key(self, mock_get: Mock, temp_home: Path) -> None:
        """Test showing specific config key."""
        mock_get.return_value = ["value1", "value2"]

        result = self.runner.invoke(cli.app, ["config", "show", "test.key"])

        assert result.exit_code == 0
        mock_get.assert_called_once_with("test.key", quiet=True)

    @patch("dotz.cli.get_config_value")
    def test_config_show_nonexistent_key(self, mock_get: Mock, temp_home: Path) -> None:
        """Test showing non-existent config key."""
        mock_get.return_value = None

        result = self.runner.invoke(cli.app, ["config", "show", "nonexistent"])

        assert result.exit_code == 1

    @patch("dotz.cli.set_config_value")
    def test_config_set(self, mock_set: Mock, temp_home: Path) -> None:
        """Test setting config value."""
        mock_set.return_value = True

        result = self.runner.invoke(cli.app, ["config", "set", "test.key", "new_value"])

        assert result.exit_code == 0
        mock_set.assert_called_once_with("test.key", "new_value")

    @patch("dotz.cli.set_config_value")
    def test_config_set_failure(self, mock_set: Mock, temp_home: Path) -> None:
        """Test config set failure."""
        mock_set.return_value = False

        result = self.runner.invoke(cli.app, ["config", "set", "test.key", "new_value"])

        assert result.exit_code == 1

    @patch("dotz.cli.add_file_pattern")
    def test_config_add_pattern(self, mock_add: Mock, temp_home: Path) -> None:
        """Test adding file pattern."""
        mock_add.return_value = True

        result = self.runner.invoke(cli.app, ["config", "add-pattern", "*.xml"])

        assert result.exit_code == 0
        mock_add.assert_called_once_with("*.xml", "include")

    @patch("dotz.cli.add_file_pattern")
    def test_config_add_exclude_pattern(self, mock_add: Mock, temp_home: Path) -> None:
        """Test adding exclude pattern."""
        mock_add.return_value = True

        result = self.runner.invoke(
            cli.app, ["config", "add-pattern", "*.log", "--type", "exclude"]
        )

        assert result.exit_code == 0
        mock_add.assert_called_once_with("*.log", "exclude")

    @patch("dotz.cli.remove_file_pattern")
    def test_config_remove_pattern(self, mock_remove: Mock, temp_home: Path) -> None:
        """Test removing file pattern."""
        mock_remove.return_value = True

        result = self.runner.invoke(cli.app, ["config", "remove-pattern", "*.xml"])

        assert result.exit_code == 0
        mock_remove.assert_called_once_with("*.xml", "include")

    @patch("dotz.cli.reset_config")
    @patch("typer.confirm")
    def test_config_reset_with_confirmation(
        self, mock_confirm: Mock, mock_reset: Mock, temp_home: Path
    ) -> None:
        """Test config reset with confirmation."""
        mock_confirm.return_value = True
        mock_reset.return_value = True

        result = self.runner.invoke(cli.app, ["config", "reset"])

        assert result.exit_code == 0
        mock_reset.assert_called_once()

    @patch("dotz.core.reset_config")
    @patch("typer.confirm")
    def test_config_reset_cancelled(
        self, mock_confirm: Mock, mock_reset: Mock, temp_home: Path
    ) -> None:
        """Test config reset cancelled."""
        mock_confirm.return_value = False

        result = self.runner.invoke(cli.app, ["config", "reset"])

        assert result.exit_code == 0
        assert "cancelled" in result.output
        mock_reset.assert_not_called()

    @patch("dotz.cli.reset_config")
    def test_config_reset_skip_confirmation(
        self, mock_reset: Mock, temp_home: Path
    ) -> None:
        """Test config reset with --yes flag."""
        mock_reset.return_value = True

        result = self.runner.invoke(cli.app, ["config", "reset", "--yes"])

        assert result.exit_code == 0
        mock_reset.assert_called_once()

    @patch("dotz.cli.load_config")
    def test_config_list_patterns(self, mock_load: Mock, temp_home: Path) -> None:
        """Test listing file patterns."""
        mock_config = {
            "file_patterns": {
                "include": ["*.txt", "*.md"],
                "exclude": ["*.log", "*.tmp"],
            },
            "search_settings": {"recursive": True, "case_sensitive": False},
        }
        mock_load.return_value = mock_config

        result = self.runner.invoke(cli.app, ["config", "list-patterns"])

        assert result.exit_code == 0
        assert "Include patterns:" in result.output
        assert "Exclude patterns:" in result.output
        assert "*.txt" in result.output
        assert "*.log" in result.output


class TestBackupCommands:
    """Test backup subcommands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.create_backup")
    @patch("dotz.cli.get_home_dir")
    def test_backup_create(
        self, mock_home: Mock, mock_create: Mock, temp_home: Path
    ) -> None:
        """Test creating a backup."""
        mock_home.return_value = temp_home
        test_file = temp_home / ".bashrc"
        test_file.write_text("content")
        mock_create.return_value = Path("/backup/path")

        result = self.runner.invoke(cli.app, ["backup", "create", ".bashrc"])

        assert result.exit_code == 0
        mock_create.assert_called_once()

    @patch("dotz.core.create_backup")
    @patch("dotz.core.get_home_dir")
    def test_backup_create_nonexistent(
        self, mock_home: Mock, mock_create: Mock, temp_home: Path
    ) -> None:
        """Test creating backup of non-existent file."""
        mock_home.return_value = temp_home

        result = self.runner.invoke(cli.app, ["backup", "create", ".nonexistent"])

        assert result.exit_code == 1
        mock_create.assert_not_called()

    @patch("dotz.core.list_backups")
    def test_backup_list_empty(self, mock_list: Mock, temp_home: Path) -> None:
        """Test listing when no backups exist."""
        mock_list.return_value = []

        result = self.runner.invoke(cli.app, ["backup", "list"])

        assert result.exit_code == 0
        assert "No backups found" in result.output

    @patch("dotz.cli.list_backups")
    def test_backup_list_with_backups(self, mock_list: Mock, temp_home: Path) -> None:
        """Test listing backups."""
        backup_path = Path("/backups/.bashrc_manual_20250708_143022")
        mock_list.return_value = [backup_path]

        result = self.runner.invoke(cli.app, ["backup", "list"])

        assert result.exit_code == 0
        assert ".bashrc" in result.output

    @patch("dotz.cli.restore_from_backup")
    @patch("dotz.cli.list_backups")
    @patch("typer.confirm")
    def test_backup_restore(
        self, mock_confirm: Mock, mock_list: Mock, mock_restore: Mock, temp_home: Path
    ) -> None:
        """Test restoring from backup."""
        backup_path = Path("/backups/.bashrc_manual_20250708_143022")
        mock_list.return_value = [backup_path]
        mock_confirm.return_value = True
        mock_restore.return_value = True

        result = self.runner.invoke(
            cli.app, ["backup", "restore", ".bashrc_manual_20250708_143022"]
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("dotz.core.list_backups")
    def test_backup_restore_nonexistent(self, mock_list: Mock, temp_home: Path) -> None:
        """Test restoring non-existent backup."""
        mock_list.return_value = []

        result = self.runner.invoke(
            cli.app, ["backup", "restore", "nonexistent_backup"]
        )

        assert result.exit_code == 1


class TestWatchCommand:
    """Test the watch command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.cli.watcher_main")
    def test_watch_command(self, mock_watcher: Mock, temp_home: Path) -> None:
        """Test watch command starts watcher."""
        # Mock KeyboardInterrupt to simulate stopping
        mock_watcher.side_effect = KeyboardInterrupt()

        result = self.runner.invoke(cli.app, ["watch"])

        # Should exit cleanly when interrupted
        assert result.exit_code == 0
        mock_watcher.assert_called_once()


class TestVersionCommand:
    """Test version and other utility commands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    def test_version_command(self, temp_home: Path) -> None:
        """Test version command."""
        result = self.runner.invoke(cli.app, ["version"])

        assert result.exit_code == 0
        assert "dotz version" in result.output

    def test_completion_command(self, temp_home: Path) -> None:
        """Test completion command."""
        result = self.runner.invoke(cli.app, ["completion"])

        assert result.exit_code == 0
        assert "--install-completion" in result.output


class TestDiagnoseCommand:
    """Test the diagnose command."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    def test_diagnose_no_repo(self, temp_home: Path) -> None:
        """Test diagnose when no repo exists."""
        with (
            patch("dotz.cli.DOTZ_DIR", temp_home / ".dotz"),
            patch("dotz.cli.WORK_TREE", temp_home / ".dotz" / "repo"),
        ):
            result = self.runner.invoke(cli.app, ["diagnose"])

            assert result.exit_code == 0
            assert "not initialized" in result.output

    @patch("dotz.core.Repo")
    def test_diagnose_with_repo(
        self, mock_repo_class: Mock, initialized_dotz: Path
    ) -> None:
        """Test diagnose with existing repo."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.remotes = []
        mock_repo.active_branch.name = "main"
        mock_repo.active_branch.tracking_branch.return_value = None
        mock_repo.is_dirty.return_value = False

        with (
            patch("dotz.cli.DOTZ_DIR", initialized_dotz),
            patch("dotz.cli.WORK_TREE", initialized_dotz / "repo"),
        ):
            result = self.runner.invoke(cli.app, ["diagnose"])

            assert result.exit_code == 0
            assert "Diagnosis complete" in result.output
