"""
CLI tests for loom.
Tests the command-line interface and integration with core functionality.
"""

import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import pytest


@pytest.fixture
def temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory for testing."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    loom = home / ".loom"
    if loom.exists():
        shutil.rmtree(loom)
    return home


def run_loom(
    *args: str, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess[str]:
    """Helper function to run loom CLI commands."""
    cmd = ["loom"] + list(map(str, args))
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestBasicCLICommands:
    """Test basic CLI command functionality."""

    def test_init_and_double_init(self, temp_home: Path) -> None:
        """Test init command and preventing double initialization."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("init", "--non-interactive", env=env)
        assert result.returncode == 0
        assert "Initialising loom..." in result.stdout
        assert "Created empty initial commit" in result.stdout

        # Second init should warn and exit
        result2 = run_loom("init", "--non-interactive", env=env)
        assert result2.returncode != 0
        assert "already initialised" in result2.stdout

    def test_add_and_list_and_status(self, temp_home: Path) -> None:
        """Test add, list-files, and status commands."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Create a fake dotfile
        dotfile = temp_home / ".bashrc"
        dotfile.write_text("export TEST=1\n")

        # Add the file
        result = run_loom("add", ".bashrc", env=env)
        assert result.returncode == 0
        assert "Added .bashrc" in result.stdout

        # List files
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        result2 = run_loom("list-files", env=env)
        assert ".bashrc" in result2.stdout

        # Status should show no changes
        result3 = run_loom("status", env=env)
        assert "No changes" in result3.stdout

    def test_restore_and_delete(self, temp_home: Path) -> None:
        """Test restore and delete commands."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Create and add a dotfile
        dotfile = temp_home / ".vimrc"
        dotfile.write_text("set number\n")
        run_loom("add", ".vimrc", env=env)

        # Remove the symlink to simulate accidental deletion
        symlink = temp_home / ".vimrc"
        if symlink.exists():
            symlink.unlink()

        # Restore the file
        result = run_loom("restore", ".vimrc", env=env)
        assert result.returncode == 0
        assert "✓ Restored .vimrc" in result.stdout
        assert (temp_home / ".vimrc").exists()

        # Delete the file from loom
        result2 = run_loom("delete", ".vimrc", env=env)
        assert result2.returncode == 0
        assert "✓ Removed .vimrc" in result2.stdout

        # Now restore should fail
        result3 = run_loom("restore", ".vimrc", env=env)
        assert result3.returncode != 0
        output = result3.stdout + result3.stderr
        assert "is not tracked by loom" in output

    def test_add_nonexistent_file(self, temp_home: Path) -> None:
        """Test adding a file that doesn't exist."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Try to add a file that doesn't exist
        result = run_loom("add", ".nonexistent", env=env)
        assert result.returncode != 0
        assert "not found" in result.stderr or "not found" in result.stdout


class TestConfigCLICommands:
    """Test configuration CLI commands."""

    def test_config_show_all(self, temp_home: Path) -> None:
        """Test showing all configuration."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "show", env=env)
        assert result.returncode == 0

        # Should contain JSON configuration
        assert "file_patterns" in result.stdout
        assert "search_settings" in result.stdout
        assert "include" in result.stdout
        assert "exclude" in result.stdout

    def test_config_show_specific_key(self, temp_home: Path) -> None:
        """Test showing specific configuration key."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "show", "file_patterns.include", env=env)
        assert result.returncode == 0

        # Should show the include patterns array
        assert ".*" in result.stdout
        assert "*.conf" in result.stdout

    def test_config_show_nonexistent_key(self, temp_home: Path) -> None:
        """Test showing non-existent configuration key."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "show", "nonexistent.key", env=env)
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_config_set_value(self, temp_home: Path) -> None:
        """Test setting configuration values."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Set a boolean value
        result = run_loom(
            "config", "set", "search_settings.recursive", "false", env=env
        )
        assert result.returncode == 0
        assert "✓ Set search_settings.recursive = False" in result.stdout

        # Verify the change
        result2 = run_loom("config", "show", "search_settings.recursive", env=env)
        assert "False" in result2.stdout or "false" in result2.stdout

    def test_config_add_pattern(self, temp_home: Path) -> None:
        """Test adding file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Add include pattern
        result = run_loom("config", "add-pattern", "*.py", env=env)
        assert result.returncode == 0
        assert "✓ Added '*.py' to include patterns" in result.stdout

        # Add exclude pattern
        result2 = run_loom(
            "config", "add-pattern", "*.pyc", "--type", "exclude", env=env
        )
        assert result2.returncode == 0
        assert "✓ Added '*.pyc' to exclude patterns" in result2.stdout

        # Verify the changes
        result3 = run_loom("config", "show", "file_patterns.include", env=env)
        assert "*.py" in result3.stdout

        result4 = run_loom("config", "show", "file_patterns.exclude", env=env)
        assert "*.pyc" in result4.stdout

    def test_config_remove_pattern(self, temp_home: Path) -> None:
        """Test removing file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # First add a pattern
        run_loom("config", "add-pattern", "*.test", env=env)

        # Then remove it
        result = run_loom("config", "remove-pattern", "*.test", env=env)
        assert result.returncode == 0
        assert "✓ Removed '*.test' from include patterns" in result.stdout

        # Try to remove non-existent pattern
        result2 = run_loom("config", "remove-pattern", "*.nonexistent", env=env)
        assert result2.returncode == 1  # Should fail when pattern not found
        assert "not found" in result2.stdout

    def test_config_list_patterns(self, temp_home: Path) -> None:
        """Test listing file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "list-patterns", env=env)
        assert result.returncode == 0

        # Should show patterns in readable format
        assert "Include patterns:" in result.stdout
        assert "Exclude patterns:" in result.stdout
        assert "Search settings:" in result.stdout
        assert "+ .*" in result.stdout  # Include pattern format
        assert "- .DS_Store" in result.stdout  # Exclude pattern format

    def test_config_reset(self, temp_home: Path) -> None:
        """Test resetting configuration."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        # Make some changes
        run_loom("config", "add-pattern", "*.custom", env=env)
        run_loom("config", "set", "search_settings.recursive", "false", env=env)

        # Reset with confirmation
        result = run_loom("config", "reset", "--yes", env=env)
        assert result.returncode == 0
        assert "✓ Configuration reset to defaults" in result.stdout

        # Verify reset worked
        result2 = run_loom("config", "show", "file_patterns.include", env=env)
        assert "*.custom" not in result2.stdout

        result3 = run_loom("config", "show", "search_settings.recursive", env=env)
        assert "True" in result3.stdout or "true" in result3.stdout

    def test_config_help(self, temp_home: Path) -> None:
        """Test configuration help command."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)

        result = run_loom("config", "help", env=env)
        assert result.returncode == 0

        # Should show comprehensive help
        assert "Loom Configuration Help" in result.stdout
        assert "File Patterns:" in result.stdout
        assert "Search Settings:" in result.stdout
        assert "Examples:" in result.stdout
        assert "~/.loom/config.json" in result.stdout


class TestDirectoryHandling:
    """Test directory handling with new configuration system."""

    def test_add_directory_with_custom_patterns(self, temp_home: Path) -> None:
        """Test adding directory with custom file patterns."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Add Python files to include patterns
        run_loom("config", "add-pattern", "*.py", env=env)

        # Create a directory with various files
        project_dir = temp_home / "myproject"
        project_dir.mkdir()
        (project_dir / "script.py").write_text("print('hello')")
        (project_dir / "config.conf").write_text("setting=value")
        (project_dir / "readme.txt").write_text("readme content")
        (project_dir / ".gitignore").write_text("*.pyc")

        # Add the directory
        result = run_loom("add", "myproject", env=env)
        assert result.returncode == 0

        # List files to see what was added
        result2 = run_loom("list-files", env=env)

        # Should include Python files, config files, and dotfiles
        assert "script.py" in result2.stdout
        assert "config.conf" in result2.stdout
        assert ".gitignore" in result2.stdout
        # Should not include txt files (not in patterns)
        assert "readme.txt" not in result2.stdout

    def test_add_directory_exclude_patterns(self, temp_home: Path) -> None:
        """Test that exclude patterns work correctly."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Add log files to exclude patterns
        run_loom("config", "add-pattern", "*.log", "--type", "exclude", env=env)

        # Create directory with log files
        logs_dir = temp_home / "logs"
        logs_dir.mkdir()
        (logs_dir / "app.log").write_text("log content")
        (logs_dir / "error.log").write_text("error content")
        (logs_dir / "config.conf").write_text("config content")

        # Add the directory
        result = run_loom("add", "logs", env=env)
        assert result.returncode == 0

        # List files to see what was added
        result2 = run_loom("list-files", env=env)

        # Should include config files but not log files
        assert "config.conf" in result2.stdout
        assert "app.log" not in result2.stdout
        assert "error.log" not in result2.stdout


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_python_project_workflow(self, temp_home: Path) -> None:
        """Test workflow for tracking Python project files."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Configure for Python project
        run_loom("config", "add-pattern", "*.py", env=env)
        run_loom("config", "add-pattern", "requirements*.txt", env=env)
        run_loom("config", "add-pattern", "pyproject.toml", env=env)
        run_loom("config", "add-pattern", "*.pyc", "--type", "exclude", env=env)

        # Create Python project structure
        project = temp_home / "myapp"
        project.mkdir()
        (project / "main.py").write_text("import sys")
        (project / "requirements.txt").write_text("requests==2.0.0")
        (project / "pyproject.toml").write_text("[build-system]")
        (project / "compiled.pyc").write_text("bytecode")
        (project / "README.md").write_text("readme")
        (project / ".gitignore").write_text("*.pyc")

        # Add the project
        result = run_loom("add", "myapp", env=env)
        assert result.returncode == 0

        # Verify what was tracked
        result2 = run_loom("list-files", env=env)
        assert "main.py" in result2.stdout
        assert "requirements.txt" in result2.stdout
        assert "pyproject.toml" in result2.stdout
        assert ".gitignore" in result2.stdout
        assert "compiled.pyc" not in result2.stdout  # excluded
        assert "README.md" not in result2.stdout  # not in patterns

    def test_config_files_only_workflow(self, temp_home: Path) -> None:
        """Test workflow for tracking only configuration files."""
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        run_loom("init", "--non-interactive", env=env)

        # Remove dotfiles pattern, keep only config files
        run_loom("config", "remove-pattern", ".*", env=env)

        # Create directory with mixed files
        configs = temp_home / "configs"
        configs.mkdir()
        (configs / ".bashrc").write_text("bash config")
        (configs / "app.conf").write_text("app config")
        (configs / "settings.json").write_text("{}")
        (configs / "readme.txt").write_text("readme")

        # Add the directory
        result = run_loom("add", "configs", env=env)
        assert result.returncode == 0

        # Verify only config files were tracked (not dotfiles)
        result2 = run_loom("list-files", env=env)
        assert "app.conf" in result2.stdout
        assert "settings.json" in result2.stdout
        assert ".bashrc" not in result2.stdout  # pattern removed
        assert "readme.txt" not in result2.stdout  # not in patterns


def test_add_directory_symlinks_only_dotfiles(temp_home: Path) -> None:
    """Test that adding a directory symlinks only dotfiles inside it."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create a directory with dotfiles and non-dotfiles
    config_dir = temp_home / "dotdir"
    config_dir.mkdir()
    (config_dir / ".dot1").write_text("dot1")
    (config_dir / ".dot2").write_text("dot2")
    (config_dir / "notdot").write_text("notdot")

    # Add the directory
    result = run_loom("add", "dotdir", env=env)
    assert result.returncode == 0
    assert "✓ Added dotfile dotdir/.dot1" in result.stdout
    assert "✓ Added dotfile dotdir/.dot2" in result.stdout

    # Only dotfiles should be symlinked
    assert (config_dir / ".dot1").is_symlink()
    assert (config_dir / ".dot2").is_symlink()
    assert not (config_dir / "notdot").is_symlink()

    # The symlinks should point to the repo
    loom_repo = temp_home / ".loom" / "repo"
    assert (config_dir / ".dot1").resolve() == loom_repo / "dotdir" / ".dot1"
    assert (config_dir / ".dot2").resolve() == loom_repo / "dotdir" / ".dot2"


def test_add_empty_directory(temp_home: Path) -> None:
    """Test adding an empty directory."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create an empty directory
    empty_dir = temp_home / ".empty_config"
    empty_dir.mkdir()

    # Add the empty directory
    result = run_loom("add", ".empty_config", env=env)
    assert result.returncode == 0
    assert "No config files found in .empty_config." in result.stdout

    # Directory should still exist and be empty
    assert empty_dir.exists()
    assert list(empty_dir.iterdir()) == []


def test_add_directory_with_subdirectories_symlinks_config_files(
    temp_home: Path,
) -> None:
    """
    Test adding a directory with nested subdirectories symlinks dotfiles and
    config files.
    """
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create a complex directory structure
    base_dir = temp_home / "complexapp"
    base_dir.mkdir()
    (base_dir / ".mainrc").write_text("main config\n")
    (base_dir / "main.conf").write_text("main config\n")
    (base_dir / "readme.txt").write_text("readme\n")  # Not a config file
    themes_dir = base_dir / "themes"
    themes_dir.mkdir()
    (themes_dir / ".light.theme").write_text("light theme\n")
    (themes_dir / "dark.theme").write_text("dark theme\n")
    plugins_dir = base_dir / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / ".pluginrc").write_text("plugin config\n")

    # Add the entire directory
    result = run_loom("add", "complexapp", env=env)
    assert result.returncode == 0
    assert "✓ Added dotfile complexapp/.mainrc" in result.stdout
    assert "✓ Added dotfile complexapp/main.conf" in result.stdout
    assert "✓ Added dotfile complexapp/themes/.light.theme" in result.stdout
    assert "✓ Added dotfile complexapp/plugins/.pluginrc" in result.stdout

    # Dotfiles and config files should be symlinked
    assert (base_dir / ".mainrc").is_symlink()
    assert (
        base_dir / "main.conf"
    ).is_symlink()  # Now tracked because of *.conf pattern
    assert not (base_dir / "readme.txt").is_symlink()  # Not tracked
    assert (themes_dir / ".light.theme").is_symlink()
    assert not (
        themes_dir / "dark.theme"
    ).is_symlink()  # Not a dotfile or config pattern
    assert (plugins_dir / ".pluginrc").is_symlink()


def test_add_single_file_still_works(temp_home: Path) -> None:
    """Ensure that adding single files still works as before."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create a single dotfile
    dotfile = temp_home / ".gitconfig"
    dotfile.write_text("[user]\nname = Test User\n")

    # Add the single file
    result = run_loom("add", ".gitconfig", env=env)
    assert result.returncode == 0
    assert "✓ Added .gitconfig" in result.stdout

    # Verify it's tracked and symlinked correctly
    result2 = run_loom("list-files", env=env)
    assert ".gitconfig" in result2.stdout
    assert (temp_home / ".gitconfig").is_symlink()


def test_delete_directory_symlinks(temp_home: Path) -> None:
    """Test deleting a directory managed by loom (dotfiles inside)."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create and add a directory with dotfiles
    test_dir = temp_home / "test_dir"
    test_dir.mkdir()
    (test_dir / ".file1").write_text("content1")
    (test_dir / ".file2").write_text("content2")
    run_loom("add", "test_dir", env=env)

    # Verify dotfiles are symlinked
    assert (test_dir / ".file1").is_symlink()
    assert (test_dir / ".file2").is_symlink()

    # Delete the dotfile
    result = run_loom("delete", "test_dir/.file1", env=env)
    assert result.returncode == 0
    assert "✓ Removed test_dir/.file1" in result.stdout
    assert not (test_dir / ".file1").exists()


def test_restore_directory_symlinks_dotfiles(temp_home: Path) -> None:
    """Test restoring a directory managed by loom (dotfiles inside)."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)

    # Create and add a directory with dotfiles
    test_dir = temp_home / "restore_test"
    test_dir.mkdir()
    (test_dir / ".configrc").write_text("important config")
    run_loom("add", "restore_test", env=env)

    # Remove the symlink (simulate accidental deletion)
    (test_dir / ".configrc").unlink()

    # Restore the dotfile
    result = run_loom("restore", "restore_test/.configrc", env=env)
    assert result.returncode == 0
    assert "✓ Restored restore_test/.configrc" in result.stdout

    # Verify it's restored as a symlink and file is accessible
    assert (test_dir / ".configrc").is_symlink()
    loom_repo = temp_home / ".loom" / "repo"
    assert (
        test_dir / ".configrc"
    ).resolve() == loom_repo / "restore_test" / ".configrc"
    assert (test_dir / ".configrc").read_text() == "important config"


def test_pull_no_remote(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    result = run_loom("pull", env=env)
    assert result.returncode != 0
    assert (
        "No 'origin' remote found" in result.stdout
        or "No 'origin' remote found" in result.stderr
    )


def test_push_no_remote(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    result = run_loom("push", env=env)
    assert result.returncode != 0
    assert (
        "No 'origin' remote found" in result.stdout
        or "No 'origin' remote found" in result.stderr
    )


def test_version_command(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_loom("version", env=env)
    assert result.returncode == 0
    assert "loom version" in result.stdout


def test_completion_command(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_loom("completion", env=env)
    assert result.returncode == 0
    assert "loom --install-completion" in result.stdout


def test_diagnose_command(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_loom("diagnose", env=env)
    assert result.returncode == 0
    assert "diagnostics" in result.stdout.lower()
    assert (
        "loom repo not initialized" in result.stdout
        or "No .git directory found" in result.stdout
        or "✓ Created empty initial commit" in result.stdout
        or "✓ No uncommitted changes." in result.stdout
    )


def test_add_and_status_untracked_home_dotfiles(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    # Create a dotfile but don't add it
    dotfile = temp_home / ".zshrc"
    dotfile.write_text("export ZSH=1\n")
    result = run_loom("status", env=env)
    assert ".zshrc" in result.stdout


def test_add_directory_and_delete_all_dotfiles_keeps_tracked_dir(
    temp_home: Path,
) -> None:
    """
    Test that tracked directory is kept even when all files are deleted
    individually.
    """
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    d = temp_home / "mydir"
    d.mkdir()
    (d / ".a").write_text("a")
    (d / ".b").write_text("b")
    run_loom("add", "mydir", env=env)
    # Delete both dotfiles
    run_loom("delete", "mydir/.a", env=env)
    run_loom("delete", "mydir/.b", env=env)

    # Current behavior: tracked_dirs.json still contains mydir
    # (automatic cleanup when directory becomes empty is not implemented)

    # Helper to read tracked_dirs.json
    def get_tracked_dirs() -> List[str]:
        loom_dir = temp_home / ".loom"
        tracked_dirs_file = loom_dir / "tracked_dirs.json"
        if not tracked_dirs_file.exists():
            return []
        with open(tracked_dirs_file) as f:
            content = json.load(f)
            return content if isinstance(content, list) else []

    tracked_dirs = get_tracked_dirs()
    assert str(d) in tracked_dirs  # Directory is still tracked


def test_restore_nonexistent_file(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    result = run_loom("restore", ".doesnotexist", env=env)
    assert result.returncode != 0
    assert (
        "not tracked by loom" in result.stdout or "not tracked by loom" in result.stderr
    )


def test_delete_non_symlink(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    # Create a file but don't add it
    f = temp_home / ".notalink"
    f.write_text("hi")
    result = run_loom("delete", ".notalink", env=env)
    assert result.returncode != 0
    assert (
        "is not a symlink managed by loom" in result.stdout
        or "is not a symlink managed by loom" in result.stderr
    )


def test_watcher_starts_and_exits(temp_home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_loom("init", "--non-interactive", env=env)
    # Add a tracked dir so watcher doesn't exit immediately
    d = temp_home / "watchdir"
    d.mkdir()
    run_loom("add", "watchdir", env=env)
    # Start watcher in a subprocess and kill it after a short time

    proc = subprocess.Popen(
        ["loom", "watch"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(2)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate()
    assert (
        b"Starting watcher" in out
        or b"Watcher stopped" in out
        or b"Starting watcher" in err
        or b"Watcher stopped" in err
    )
