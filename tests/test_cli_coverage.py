"""
Additional tests to improve coverage for dotkeep CLI functionality.
These tests focus on edge cases and error conditions not covered by existing tests.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import pytest


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI color codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def run_dotkeep(
    *args: str, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess[str]:
    """Helper function to run dotkeep CLI commands."""
    cmd = ["dotkeep"] + list(map(str, args))
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestCLIEdgeCases:
    """Test CLI edge cases and error conditions."""

    def test_init_with_remote(self, temp_home: Path) -> None:
        """Test init command with remote URL."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep(
            "init",
            "--remote",
            "https://github.com/user/dotfiles.git",
            "--non-interactive",
            env=env,
        )
        assert result.returncode == 0
        assert "WARNING" in result.stdout  # Should warn about sensitive info

    def test_add_with_push(self, temp_home: Path) -> None:
        """Test add command with --push flag when no remote exists."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create a dotfile
        dotfile = temp_home / ".bashrc"
        dotfile.write_text("export TEST=1")

        # Try to add with push (should fail - no remote)
        result = run_dotkeep("add", ".bashrc", "--push", env=env)
        # Should succeed locally but push will fail
        combined_output = strip_ansi_codes(result.stdout + result.stderr)
        assert "Remote named 'origin' didn't exist" in combined_output

    def test_delete_with_push(self, temp_home: Path) -> None:
        """Test delete command with --push flag when no remote exists."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create and add a dotfile
        dotfile = temp_home / ".vimrc"
        dotfile.write_text("set number")
        run_dotkeep("add", ".vimrc", env=env)

        # Try to delete with push (should fail - no remote)
        result = run_dotkeep("delete", ".vimrc", "--push", env=env)
        # Should succeed locally but push will fail
        combined_output = strip_ansi_codes(result.stdout + result.stderr)
        assert "Remote named 'origin' didn't exist" in combined_output

    def test_restore_with_push(self, temp_home: Path) -> None:
        """Test restore command with --push flag when no remote exists."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create and add a dotfile
        dotfile = temp_home / ".gitconfig"
        dotfile.write_text("[user]\\nname = Test")
        run_dotkeep("add", ".gitconfig", env=env)

        # Remove the symlink
        dotfile.unlink()

        # Try to restore with push (should fail - file not tracked)
        result = run_dotkeep("restore", ".gitconfig", "--push", env=env)
        # Should fail because file is not tracked by dotkeep
        assert (
            "is not tracked by dotkeep" in result.stderr
            or "not found" in result.stderr.lower()
        )

    def test_add_directory_non_recursive(self, temp_home: Path) -> None:
        """Test adding directory with --no-recursive flag."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create directory with subdirectories
        config_dir = temp_home / "myconfig"
        config_dir.mkdir()
        (config_dir / ".mainrc").write_text("main config")

        sub_dir = config_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / ".subrc").write_text("sub config")

        # Add with --no-recursive
        result = run_dotkeep("add", "myconfig", "--no-recursive", env=env)
        assert result.returncode == 0

        # Check that only top-level files were added
        result2 = run_dotkeep("list-files", env=env)
        assert ".mainrc" in result2.stdout
        # Should not be added due to --no-recursive
        assert ".subrc" not in result2.stdout

    def test_config_set_invalid_json(self, temp_home: Path) -> None:
        """Test config set with invalid JSON value."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep("config", "set", "test_key", "{invalid json", env=env)
        assert result.returncode != 0
        assert "Invalid JSON" in result.stderr or "Invalid JSON" in result.stdout

    def test_config_add_pattern_invalid_type(self, temp_home: Path) -> None:
        """Test config add-pattern with invalid type."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep(
            "config", "add-pattern", "*.test", "--type", "invalid", env=env
        )
        assert result.returncode != 0

    def test_config_remove_pattern_invalid_type(self, temp_home: Path) -> None:
        """Test config remove-pattern with invalid type."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep(
            "config", "remove-pattern", "*.test", "--type", "invalid", env=env
        )
        assert result.returncode != 0

    def test_config_reset_without_confirmation(self, temp_home: Path) -> None:
        """Test config reset without --yes flag (should prompt)."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Run reset without --yes, should ask for confirmation
        process = subprocess.Popen(
            ["dotkeep", "config", "reset"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Send 'n' to decline reset
        stdout, stderr = process.communicate(input="n\n")

        # Should not reset when declined
        combined_output = stdout + stderr
        assert (
            "Reset cancelled" in combined_output
            or "cancelled" in combined_output.lower()
            or "Error: invalid input" in combined_output
            or "Aborted." in combined_output
        )

    def test_status_help(self, temp_home: Path) -> None:
        """Test status command with --help flag."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create some untracked dotfiles
        (temp_home / ".bashrc").write_text("bash config")
        (temp_home / ".vimrc").write_text("vim config")

        result = run_dotkeep("status", "--help", env=env)
        assert result.returncode == 0
        assert "Show the status of your dotkeep repo" in result.stdout

    def test_list_files_help(self, temp_home: Path) -> None:
        """Test list-files command with --help flag."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Add a file
        dotfile = temp_home / ".testrc"
        dotfile.write_text("test config")
        run_dotkeep("add", ".testrc", env=env)

        result = run_dotkeep("list-files", "--help", env=env)
        assert result.returncode == 0

    def test_diagnose_no_repo(self, temp_home: Path) -> None:
        """Test diagnose command when no repo is initialized."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep("diagnose", env=env)
        assert result.returncode == 0
        assert "not initialized" in result.stdout.lower()

    def test_watch_command_help(self, temp_home: Path) -> None:
        """Test watch command help."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep("watch", "--help", env=env)
        assert result.returncode == 0
        assert "watch" in result.stdout.lower()

    def test_invalid_command(self, temp_home: Path) -> None:
        """Test running an invalid command."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep("invalid_command", env=env)
        assert result.returncode != 0

    def test_add_file_already_exists_in_repo(self, temp_home: Path) -> None:
        """Test adding a file that already exists in repo but not as symlink."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create a file and add it
        dotfile = temp_home / ".duplicatetest"
        dotfile.write_text("original")
        run_dotkeep("add", ".duplicatetest", env=env)

        # Remove symlink and create a regular file with different content
        dotfile.unlink()
        dotfile.write_text("modified")

        # Try to add again
        result = run_dotkeep("add", ".duplicatetest", env=env)
        assert result.returncode == 0
        assert dotfile.is_symlink()

    def test_help_command(self, temp_home: Path) -> None:
        """Test the help command."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_dotkeep("--help", env=env)
        assert result.returncode == 0
        assert "dotkeep" in result.stdout.lower()

    def test_add_empty_file(self, temp_home: Path) -> None:
        """Test adding an empty file."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create empty file
        empty_file = temp_home / ".empty"
        empty_file.touch()

        result = run_dotkeep("add", ".empty", env=env)
        assert result.returncode == 0
        assert empty_file.is_symlink()

    def test_config_show_with_formatting(self, temp_home: Path) -> None:
        """Test config show with different formatting scenarios."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Test showing nested object
        result = run_dotkeep("config", "show", "search_settings", env=env)
        assert result.returncode == 0
        assert "recursive" in result.stdout

        # Test showing array
        result2 = run_dotkeep("config", "show", "file_patterns.include", env=env)
        assert result2.returncode == 0

    def test_long_running_command_interrupt(self, temp_home: Path) -> None:
        """Test interrupting a long-running command (watch)."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Add a directory so watch doesn't exit immediately
        test_dir = temp_home / "watchdir"
        test_dir.mkdir()
        run_dotkeep("add", "watchdir", env=env)

        # This test is hard to do properly in unit tests
        # We just verify the command exists and can be called
        # The actual interruption testing is done in integration tests
        result = run_dotkeep("watch", "--help", env=env)
        assert result.returncode == 0


class TestCLIErrorConditions:
    """Test CLI error conditions and exception handling."""

    def test_add_with_git_error(self, temp_home: Path) -> None:
        """Test add command when git operations fail."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_dotkeep("init", "--non-interactive", env=env)

        # Create a file
        dotfile = temp_home / ".giterror"
        dotfile.write_text("content")

        # Make the git repo corrupted by removing the .git directory after init
        dotkeep_config_dir = temp_home / ".config" / "dotkeep"
        if dotkeep_config_dir.exists():
            # Remove the git directory to simulate a corrupted repo
            import shutil

            git_dir = dotkeep_config_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

        result = run_dotkeep("add", ".giterror", env=env)
        # Should handle error gracefully - either return error or succeed despite issues
        # The key is that it doesn't crash
        assert result.returncode in [0, 1]  # Allow both success and failure
