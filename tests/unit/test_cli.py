"""
Test module for dotz CLI functionality.

This module tests the command-line interface including all commands,
option parsing, user interaction, and integration with core functions.
"""

import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest
import typer
from typer.testing import CliRunner

from dotz import cli
from dotz.exceptions import (
    DotzFileNotFoundError,
    DotzGitError,
    DotzRepositoryNotFoundError,
)


class TestCLIUtilities:
    """Test suite for CLI utility functions."""
    
    @pytest.mark.parametrize("size_bytes,expected", [
        (0, "0 bytes"),
        (512, "512 bytes"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1048576, "1.0 MB"),
        (1572864, "1.5 MB"),
        (2097152, "2.0 MB"),
    ])
    def test_format_file_size(self, size_bytes, expected):
        """Test file size formatting with various inputs."""
        result = cli.format_file_size(size_bytes)
        assert result == expected
    
    def test_format_file_size_edge_cases(self):
        """Test file size formatting with edge cases."""
        # Very large file
        large_size = 1024 * 1024 * 1024  # 1GB
        result = cli.format_file_size(large_size)
        assert "1024.0 MB" in result


class TestInitCommand:
    """Test suite for the init command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_init_command_basic(self, runner):
        """Test basic init command without remote."""
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.return_value = {"success": True, "message": "Repository initialized"}
            
            result = runner.invoke(cli.app, ["init", "--non-interactive"])
            
            assert result.exit_code == 0
            mock_init.assert_called_once_with("")
    
    def test_init_command_with_remote(self, runner):
        """Test init command with remote URL."""
        remote_url = "git@github.com:user/dotfiles.git"
        
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.return_value = {"success": True, "message": "Repository initialized"}
            
            result = runner.invoke(cli.app, ["init", "--remote", remote_url, "--non-interactive"])
            
            assert result.exit_code == 0
            mock_init.assert_called_once_with(remote_url)
    
    def test_init_command_interactive_with_remote(self, runner):
        """Test interactive init command with remote setup."""
        remote_url = "https://github.com/user/dotfiles.git"
        
        with patch("dotz.cli.init_repo") as mock_init, \
             patch("dotz.cli.add_dotfile") as mock_add:
            
            mock_init.return_value = {"success": True, "message": "Repository initialized"}
            mock_add.return_value = {"success": True, "files_added": []}
            
            # Simulate user input: yes to remote, provide URL, yes to auto-add files
            user_input = f"y\\n{remote_url}\\ny\\n"
            
            result = runner.invoke(cli.app, ["init"], input=user_input)
            
            assert result.exit_code == 0
            mock_init.assert_called_once_with(remote_url)
    
    def test_init_command_interactive_no_remote(self, runner):
        """Test interactive init command without remote setup."""
        with patch("dotz.cli.init_repo") as mock_init, \
             patch("dotz.cli.add_dotfile") as mock_add:
            
            mock_init.return_value = {"success": True, "message": "Repository initialized"}
            mock_add.return_value = {"success": True, "files_added": []}
            
            # Simulate user input: no to remote, yes to auto-add files
            user_input = "n\\ny\\n"
            
            result = runner.invoke(cli.app, ["init"], input=user_input)
            
            assert result.exit_code == 0
            mock_init.assert_called_once_with("")
    
    def test_init_command_handles_errors(self, runner):
        """Test init command error handling."""
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.side_effect = DotzGitError("Git initialization failed")
            
            result = runner.invoke(cli.app, ["init", "--non-interactive"])
            
            assert result.exit_code == 1
            assert "Git initialization failed" in result.output


class TestAddCommand:
    """Test suite for the add command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_add_command_single_file(self, runner):
        """Test adding a single file."""
        with patch("dotz.cli.add_dotfile") as mock_add:
            mock_add.return_value = {
                "success": True,
                "files_added": [".bashrc"],
                "message": "Added .bashrc"
            }
            
            result = runner.invoke(cli.app, ["add", ".bashrc"])
            
            assert result.exit_code == 0
            mock_add.assert_called_once_with(".bashrc", recursive=True, push=False)
            assert ".bashrc" in result.output
    
    def test_add_command_multiple_files(self, runner):
        """Test adding multiple files."""
        files = [".bashrc", ".vimrc", ".gitconfig"]
        
        with patch("dotz.cli.add_dotfile") as mock_add:
            mock_add.return_value = {
                "success": True,
                "files_added": files,
                "message": f"Added {len(files)} files"
            }
            
            result = runner.invoke(cli.app, ["add"] + files)
            
            assert result.exit_code == 0
            assert mock_add.call_count == len(files)
    
    def test_add_command_with_push(self, runner):
        """Test add command with push option."""
        with patch("dotz.cli.add_dotfile") as mock_add, \
             patch("dotz.cli.push_repo") as mock_push:
            
            mock_add.return_value = {"success": True, "files_added": [".bashrc"]}
            mock_push.return_value = {"success": True}
            
            result = runner.invoke(cli.app, ["add", ".bashrc", "--push"])
            
            assert result.exit_code == 0
            mock_add.assert_called_once_with(".bashrc", recursive=True, push=True)
    
    def test_add_command_non_recursive(self, runner):
        """Test add command with non-recursive option."""
        with patch("dotz.cli.add_dotfile") as mock_add:
            mock_add.return_value = {"success": True, "files_added": [".config"]}
            
            result = runner.invoke(cli.app, ["add", ".config", "--no-recursive"])
            
            assert result.exit_code == 0
            mock_add.assert_called_once_with(".config", recursive=False, push=False)
    
    def test_add_command_file_not_found(self, runner):
        """Test add command with nonexistent file."""
        with patch("dotz.cli.add_dotfile") as mock_add:
            mock_add.side_effect = DotzFileNotFoundError("File not found")
            
            result = runner.invoke(cli.app, ["add", ".nonexistent"])
            
            assert result.exit_code == 1
            assert "File not found" in result.output


class TestDeleteCommand:
    """Test suite for the delete command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_delete_command_single_file(self, runner):
        """Test deleting a single file."""
        with patch("dotz.cli.delete_dotfile") as mock_delete:
            mock_delete.return_value = {"success": True, "message": "Deleted .bashrc"}
            
            result = runner.invoke(cli.app, ["delete", ".bashrc"])
            
            assert result.exit_code == 0
            mock_delete.assert_called_once_with(".bashrc", push=False)
    
    def test_delete_command_with_push(self, runner):
        """Test delete command with push option."""
        with patch("dotz.cli.delete_dotfile") as mock_delete:
            mock_delete.return_value = {"success": True, "message": "Deleted .bashrc"}
            
            result = runner.invoke(cli.app, ["delete", ".bashrc", "--push"])
            
            assert result.exit_code == 0
            mock_delete.assert_called_once_with(".bashrc", push=True)
    
    def test_delete_command_confirmation(self, runner):
        """Test delete command with confirmation prompt."""
        with patch("dotz.cli.delete_dotfile") as mock_delete:
            mock_delete.return_value = {"success": True, "message": "Deleted .bashrc"}
            
            # Simulate user confirming deletion
            result = runner.invoke(cli.app, ["delete", ".bashrc"], input="y\\n")
            
            assert result.exit_code == 0
            mock_delete.assert_called_once()
    
    def test_delete_command_cancelled(self, runner):
        """Test delete command when user cancels."""
        with patch("dotz.cli.delete_dotfile") as mock_delete:
            # Simulate user cancelling deletion
            result = runner.invoke(cli.app, ["delete", ".bashrc"], input="n\\n")
            
            assert result.exit_code == 0
            mock_delete.assert_not_called()
            assert "Cancelled" in result.output


class TestRestoreCommand:
    """Test suite for the restore command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_restore_command_single_file(self, runner):
        """Test restoring a single file."""
        with patch("dotz.cli.restore_dotfile") as mock_restore:
            mock_restore.return_value = {"success": True, "message": "Restored .bashrc"}
            
            result = runner.invoke(cli.app, ["restore", ".bashrc"])
            
            assert result.exit_code == 0
            mock_restore.assert_called_once_with(".bashrc")
    
    def test_restore_command_multiple_files(self, runner):
        """Test restoring multiple files."""
        files = [".bashrc", ".vimrc"]
        
        with patch("dotz.cli.restore_dotfile") as mock_restore:
            mock_restore.return_value = {"success": True, "message": "Restored file"}
            
            result = runner.invoke(cli.app, ["restore"] + files)
            
            assert result.exit_code == 0
            assert mock_restore.call_count == len(files)


class TestStatusCommand:
    """Test suite for the status command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_status_command_clean_repo(self, runner):
        """Test status command with clean repository."""
        status_data = {
            "is_dirty": False,
            "untracked_files": [],
            "has_remote": True,
            "ahead": 0,
            "behind": 0
        }
        
        with patch("dotz.cli.get_repo_status") as mock_status:
            mock_status.return_value = status_data
            
            result = runner.invoke(cli.app, ["status"])
            
            assert result.exit_code == 0
            assert "clean" in result.output.lower()
    
    def test_status_command_dirty_repo(self, runner):
        """Test status command with dirty repository."""
        status_data = {
            "is_dirty": True,
            "untracked_files": ["file1.txt", "file2.txt"],
            "has_remote": True,
            "ahead": 2,
            "behind": 1
        }
        
        with patch("dotz.cli.get_repo_status") as mock_status:
            mock_status.return_value = status_data
            
            result = runner.invoke(cli.app, ["status"])
            
            assert result.exit_code == 0
            assert "file1.txt" in result.output
            assert "file2.txt" in result.output
    
    def test_status_command_no_repository(self, runner):
        """Test status command when no repository exists."""
        with patch("dotz.cli.get_repo_status") as mock_status:
            mock_status.side_effect = DotzRepositoryNotFoundError("No repository found")
            
            result = runner.invoke(cli.app, ["status"])
            
            assert result.exit_code == 1
            assert "No repository found" in result.output


class TestListFilesCommand:
    """Test suite for the list-files command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_list_files_command_basic(self, runner):
        """Test basic list-files command."""
        files = [".bashrc", ".vimrc", ".gitconfig", ".config/app/config.conf"]
        
        with patch("dotz.cli.list_tracked_files") as mock_list:
            mock_list.return_value = files
            
            result = runner.invoke(cli.app, ["list-files"])
            
            assert result.exit_code == 0
            for file in files:
                assert file in result.output
    
    def test_list_files_command_verbose(self, runner):
        """Test list-files command with verbose output."""
        files = [".bashrc", ".vimrc"]
        
        with patch("dotz.cli.list_tracked_files") as mock_list, \
             patch("pathlib.Path.stat") as mock_stat:
            
            mock_list.return_value = files
            mock_stat.return_value = Mock(st_size=1024, st_mtime=1640995200)  # 2022-01-01
            
            result = runner.invoke(cli.app, ["list-files", "--verbose"])
            
            assert result.exit_code == 0
            assert "1.0 KB" in result.output  # File size formatting
    
    def test_list_files_command_empty_repo(self, runner):
        """Test list-files command with empty repository."""
        with patch("dotz.cli.list_tracked_files") as mock_list:
            mock_list.return_value = []
            
            result = runner.invoke(cli.app, ["list-files"])
            
            assert result.exit_code == 0
            assert "No files" in result.output


class TestPullPushCommands:
    """Test suite for pull and push commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_pull_command_success(self, runner):
        """Test successful pull command."""
        with patch("dotz.cli.pull_repo") as mock_pull:
            mock_pull.return_value = {"success": True, "message": "Pull successful"}
            
            result = runner.invoke(cli.app, ["pull"])
            
            assert result.exit_code == 0
            assert "Pull successful" in result.output
    
    def test_pull_command_no_remote(self, runner):
        """Test pull command with no remote."""
        with patch("dotz.cli.pull_repo") as mock_pull:
            mock_pull.side_effect = DotzGitError("No remote repository")
            
            result = runner.invoke(cli.app, ["pull"])
            
            assert result.exit_code == 1
            assert "No remote repository" in result.output
    
    def test_push_command_success(self, runner):
        """Test successful push command."""
        with patch("dotz.cli.push_repo") as mock_push:
            mock_push.return_value = {"success": True, "message": "Push successful"}
            
            result = runner.invoke(cli.app, ["push"])
            
            assert result.exit_code == 0
            assert "Push successful" in result.output
    
    def test_push_command_no_changes(self, runner):
        """Test push command with no changes to push."""
        with patch("dotz.cli.push_repo") as mock_push:
            mock_push.return_value = {"success": True, "message": "Nothing to push"}
            
            result = runner.invoke(cli.app, ["push"])
            
            assert result.exit_code == 0
            assert "Nothing to push" in result.output


class TestConfigCommands:
    """Test suite for configuration commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_config_show_command(self, runner):
        """Test config show command."""
        config_data = {
            "file_patterns": {
                "include": [".*"],
                "exclude": ["*.log"]
            },
            "search_settings": {
                "recursive": True
            }
        }
        
        with patch("dotz.cli.load_config") as mock_load:
            mock_load.return_value = config_data
            
            result = runner.invoke(cli.app, ["config", "show"])
            
            assert result.exit_code == 0
            assert "file_patterns" in result.output
    
    def test_config_set_command(self, runner):
        """Test config set command."""
        with patch("dotz.cli.set_config_value") as mock_set:
            result = runner.invoke(cli.app, ["config", "set", "search_settings.recursive", "false"])
            
            assert result.exit_code == 0
            mock_set.assert_called_once_with("search_settings.recursive", False)
    
    def test_config_get_command(self, runner):
        """Test config get command."""
        with patch("dotz.cli.get_config_value") as mock_get:
            mock_get.return_value = True
            
            result = runner.invoke(cli.app, ["config", "get", "search_settings.recursive"])
            
            assert result.exit_code == 0
            assert "True" in result.output
    
    def test_config_reset_command(self, runner):
        """Test config reset command."""
        with patch("dotz.cli.reset_config") as mock_reset:
            # Simulate user confirming reset
            result = runner.invoke(cli.app, ["config", "reset"], input="y\\n")
            
            assert result.exit_code == 0
            mock_reset.assert_called_once()
    
    def test_config_add_pattern_command(self, runner):
        """Test config add-pattern command."""
        with patch("dotz.cli.add_file_pattern") as mock_add:
            result = runner.invoke(cli.app, ["config", "add-pattern", "*.py"])
            
            assert result.exit_code == 0
            mock_add.assert_called_once_with("*.py", "include")
    
    def test_config_remove_pattern_command(self, runner):
        """Test config remove-pattern command."""
        with patch("dotz.cli.remove_file_pattern") as mock_remove:
            result = runner.invoke(cli.app, ["config", "remove-pattern", "*.py"])
            
            assert result.exit_code == 0
            mock_remove.assert_called_once_with("*.py")


class TestBackupCommands:
    """Test suite for backup commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_backup_create_command(self, runner):
        """Test backup create command."""
        files = [".bashrc", ".vimrc"]
        
        with patch("dotz.cli.create_backup") as mock_backup:
            mock_backup.return_value = {
                "success": True,
                "backup_file": "/path/to/backup.tar.gz",
                "files_backed_up": files
            }
            
            result = runner.invoke(cli.app, ["backup", "create"] + files)
            
            assert result.exit_code == 0
            mock_backup.assert_called_once_with(files)
    
    def test_backup_list_command(self, runner):
        """Test backup list command."""
        backups = [
            {
                "filename": "backup_20240101_120000.tar.gz",
                "date": "2024-01-01",
                "time": "12:00:00",
                "size": 1024
            },
            {
                "filename": "backup_20240102_130000.tar.gz",
                "date": "2024-01-02",
                "time": "13:00:00",
                "size": 2048
            }
        ]
        
        with patch("dotz.cli.list_backups") as mock_list:
            mock_list.return_value = backups
            
            result = runner.invoke(cli.app, ["backup", "list"])
            
            assert result.exit_code == 0
            assert "backup_20240101_120000.tar.gz" in result.output
            assert "1.0 KB" in result.output
    
    def test_backup_restore_command(self, runner):
        """Test backup restore command."""
        backup_file = "backup_20240101_120000.tar.gz"
        
        with patch("dotz.cli.restore_from_backup") as mock_restore:
            mock_restore.return_value = {"success": True, "message": "Backup restored"}
            
            result = runner.invoke(cli.app, ["backup", "restore", backup_file])
            
            assert result.exit_code == 0
            mock_restore.assert_called_once_with(backup_file)


class TestWatchCommand:
    """Test suite for the watch command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_watch_command(self, runner):
        """Test watch command."""
        with patch("dotz.cli.watcher_main") as mock_watcher:
            mock_watcher.return_value = None
            
            # Use a timeout to prevent hanging
            result = runner.invoke(cli.app, ["watch"], catch_exceptions=False)
            
            # Note: This test might need adjustment based on watcher implementation
            mock_watcher.assert_called_once()


class TestVersionCommand:
    """Test suite for the version command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(cli.app, ["version"])
        
        assert result.exit_code == 0
        assert cli.DEFAULT_VERSION in result.output or "0.4.0" in result.output
    
    def test_version_option(self, runner):
        """Test --version option."""
        result = runner.invoke(cli.app, ["--version"])
        
        assert result.exit_code == 0
        assert cli.DEFAULT_VERSION in result.output or "0.4.0" in result.output


class TestDiagnoseCommand:
    """Test suite for the diagnose command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_diagnose_command_healthy_system(self, runner):
        """Test diagnose command with healthy system."""
        status_data = {
            "is_dirty": False,
            "untracked_files": [],
            "has_remote": True
        }
        
        with patch("dotz.cli.get_repo_status") as mock_status, \
             patch("dotz.cli.validate_symlinks") as mock_validate, \
             patch("pathlib.Path.exists") as mock_exists:
            
            mock_status.return_value = status_data
            mock_validate.return_value = {
                "valid_symlinks": [".bashrc", ".vimrc"],
                "broken_symlinks": [],
                "missing_files": []
            }
            mock_exists.return_value = True
            
            result = runner.invoke(cli.app, ["diagnose"])
            
            assert result.exit_code == 0
            assert "healthy" in result.output.lower()
    
    def test_diagnose_command_issues_found(self, runner):
        """Test diagnose command when issues are found."""
        with patch("dotz.cli.get_repo_status") as mock_status, \
             patch("dotz.cli.validate_symlinks") as mock_validate:
            
            mock_status.side_effect = DotzRepositoryNotFoundError("No repository")
            mock_validate.return_value = {
                "valid_symlinks": [],
                "broken_symlinks": [".broken_link"],
                "missing_files": [".missing_file"]
            }
            
            result = runner.invoke(cli.app, ["diagnose"])
            
            assert result.exit_code == 0
            assert "issues" in result.output.lower()
            assert ".broken_link" in result.output


class TestErrorHandling:
    """Test suite for CLI error handling."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_keyboard_interrupt_handling(self, runner):
        """Test handling of keyboard interrupts."""
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(cli.app, ["init", "--non-interactive"])
            
            assert result.exit_code == 1
            assert "interrupted" in result.output.lower()
    
    def test_unexpected_error_handling(self, runner):
        """Test handling of unexpected errors."""
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.side_effect = Exception("Unexpected error")
            
            result = runner.invoke(cli.app, ["init", "--non-interactive"])
            
            assert result.exit_code == 1
            assert "error" in result.output.lower()
    
    def test_typer_exit_handling(self, runner):
        """Test handling of Typer exits."""
        with patch("dotz.cli.init_repo") as mock_init:
            mock_init.side_effect = typer.Exit(code=2)
            
            result = runner.invoke(cli.app, ["init", "--non-interactive"])
            
            assert result.exit_code == 2


class TestGUICommand:
    """Test suite for the GUI command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_gui_command_available(self, runner):
        """Test GUI command when PySide6 is available."""
        with patch("dotz.cli.main") as mock_gui_main:
            mock_gui_main.return_value = None
            
            result = runner.invoke(cli.app, ["gui"])
            
            # Exit code depends on GUI implementation
            mock_gui_main.assert_called_once()
    
    def test_gui_command_unavailable(self, runner):
        """Test GUI command when PySide6 is not available."""
        with patch("dotz.cli.main") as mock_gui_main:
            mock_gui_main.side_effect = ImportError("PySide6 not available")
            
            result = runner.invoke(cli.app, ["gui"])
            
            assert result.exit_code == 1
            assert "GUI dependencies" in result.output or "PySide6" in result.output


class TestTemplateCommands:
    """Test suite for template-related commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_template_create_command(self, runner):
        """Test template create command."""
        with patch("dotz.cli.templates.create_template") as mock_create:
            mock_create.return_value = {"success": True, "message": "Template created"}
            
            result = runner.invoke(cli.app, ["template", "create", "dev", "--description", "Development setup"])
            
            assert result.exit_code == 0
            mock_create.assert_called_once()
    
    def test_template_list_command(self, runner):
        """Test template list command."""
        templates_data = [
            {"name": "dev", "description": "Development setup", "files": [".bashrc", ".vimrc"]},
            {"name": "minimal", "description": "Minimal setup", "files": [".bashrc"]}
        ]
        
        with patch("dotz.cli.templates.list_templates") as mock_list:
            mock_list.return_value = templates_data
            
            result = runner.invoke(cli.app, ["template", "list"])
            
            assert result.exit_code == 0
            assert "dev" in result.output
            assert "minimal" in result.output
    
    def test_template_apply_command(self, runner):
        """Test template apply command."""
        with patch("dotz.cli.templates.apply_template") as mock_apply:
            mock_apply.return_value = {"success": True, "message": "Template applied"}
            
            result = runner.invoke(cli.app, ["template", "apply", "dev"])
            
            assert result.exit_code == 0
            mock_apply.assert_called_once()


class TestValidateCommand:
    """Test suite for the validate command."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_validate_command_all_valid(self, runner):
        """Test validate command when all symlinks are valid."""
        validation_results = {
            "valid_symlinks": [".bashrc", ".vimrc"],
            "broken_symlinks": [],
            "missing_files": []
        }
        
        with patch("dotz.cli.validate_symlinks") as mock_validate:
            mock_validate.return_value = validation_results
            
            result = runner.invoke(cli.app, ["validate"])
            
            assert result.exit_code == 0
            assert "valid" in result.output.lower()
    
    def test_validate_command_issues_found(self, runner):
        """Test validate command when issues are found."""
        validation_results = {
            "valid_symlinks": [".bashrc"],
            "broken_symlinks": [".broken_link"],
            "missing_files": [".missing_file"]
        }
        
        with patch("dotz.cli.validate_symlinks") as mock_validate:
            mock_validate.return_value = validation_results
            
            result = runner.invoke(cli.app, ["validate"])
            
            assert result.exit_code == 0
            assert ".broken_link" in result.output
            assert ".missing_file" in result.output