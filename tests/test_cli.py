import os
import shutil
import json
import subprocess
from pathlib import Path
import pytest

from dotkeep.core import save_tracked_dir, count_files_in_directory, add_dotfile, TRACKED_DIRS_FILE
from dotkeep.watcher import get_tracked_dirs

@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    dotkeep = home / ".dotkeep"
    if dotkeep.exists():
        shutil.rmtree(dotkeep)
    return home

def run_dotkeep(*args, env=None):
    cmd = ["dotkeep"] + list(map(str, args))
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def test_init_and_double_init(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_dotkeep("init", env=env)
    assert result.returncode == 0
    assert "Initialising dotkeep..." in result.stdout
    assert "✓ Created empty initial commit" in result.stdout

    # Second init should warn and exit
    result2 = run_dotkeep("init", env=env)
    assert result2.returncode != 0
    assert "already initialised" in result2.stdout

def test_add_and_list_and_status(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a fake dotfile
    dotfile = temp_home / ".bashrc"
    dotfile.write_text("export TEST=1\n")

    # Add the file
    result = run_dotkeep("add", ".bashrc", env=env)
    assert result.returncode == 0
    assert "✓ Added .bashrc" in result.stdout

    # List files
    result2 = run_dotkeep("list-files", env=env)
    assert ".bashrc" in result2.stdout

    # Status should show no changes
    result3 = run_dotkeep("status", env=env)
    assert "✓ No changes" in result3.stdout

def test_restore_and_delete(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a dotfile
    dotfile = temp_home / ".vimrc"
    dotfile.write_text("set number\n")
    run_dotkeep("add", ".vimrc", env=env)

    # Remove the symlink to simulate accidental deletion
    symlink = temp_home / ".vimrc"
    if symlink.exists():
        symlink.unlink()

    # Restore the file
    result = run_dotkeep("restore", ".vimrc", env=env)
    assert result.returncode == 0
    assert "✓ Restored .vimrc" in result.stdout
    assert (temp_home / ".vimrc").exists()

    # Delete the file from dotkeep
    result2 = run_dotkeep("delete", ".vimrc", env=env)
    assert result2.returncode == 0
    assert "✓ Removed .vimrc" in result2.stdout

    # Now restore should fail
    result3 = run_dotkeep("restore", ".vimrc", env=env)
    assert result3.returncode != 0
    output = result3.stdout + result3.stderr
    assert "is not tracked by dotkeep" in output

def test_add_nonexistent_file(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Try to add a file that doesn't exist
    result = run_dotkeep("add", ".nonexistent", env=env)
    assert result.returncode != 0
    assert "not found" in result.stderr or "not found" in result.stdout

def test_add_directory_symlinks_only_dotfiles(temp_home):
    """Test that adding a directory symlinks only dotfiles inside it."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a directory with dotfiles and non-dotfiles
    config_dir = temp_home / "dotdir"
    config_dir.mkdir()
    (config_dir / ".dot1").write_text("dot1")
    (config_dir / ".dot2").write_text("dot2")
    (config_dir / "notdot").write_text("notdot")

    # Add the directory
    result = run_dotkeep("add", "dotdir", env=env)
    assert result.returncode == 0
    assert "✓ Added dotfile dotdir/.dot1" in result.stdout
    assert "✓ Added dotfile dotdir/.dot2" in result.stdout

    # Only dotfiles should be symlinked
    assert (config_dir / ".dot1").is_symlink()
    assert (config_dir / ".dot2").is_symlink()
    assert not (config_dir / "notdot").is_symlink()

    # The symlinks should point to the repo
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert (config_dir / ".dot1").resolve() == dotkeep_repo / "dotdir" / ".dot1"
    assert (config_dir / ".dot2").resolve() == dotkeep_repo / "dotdir" / ".dot2"

def test_add_empty_directory(temp_home):
    """Test adding an empty directory."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create an empty directory
    empty_dir = temp_home / ".empty_config"
    empty_dir.mkdir()

    # Add the empty directory
    result = run_dotkeep("add", ".empty_config", env=env)
    assert result.returncode == 0
    assert "No dotfiles found in .empty_config." in result.stdout

    # Directory should still exist and be empty
    assert empty_dir.exists()
    assert list(empty_dir.iterdir()) == []

def test_add_directory_with_subdirectories_symlinks_only_dotfiles(temp_home):
    """Test adding a directory with nested subdirectories symlinks only dotfiles."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a complex directory structure
    base_dir = temp_home / "complexapp"
    base_dir.mkdir()
    (base_dir / ".mainrc").write_text("main config\n")
    (base_dir / "main.conf").write_text("main config\n")
    themes_dir = base_dir / "themes"
    themes_dir.mkdir()
    (themes_dir / ".light.theme").write_text("light theme\n")
    (themes_dir / "dark.theme").write_text("dark theme\n")
    plugins_dir = base_dir / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / ".pluginrc").write_text("plugin config\n")

    # Add the entire directory
    result = run_dotkeep("add", "complexapp", env=env)
    assert result.returncode == 0
    assert "✓ Added dotfile complexapp/.mainrc" in result.stdout
    assert "✓ Added dotfile complexapp/themes/.light.theme" in result.stdout
    assert "✓ Added dotfile complexapp/plugins/.pluginrc" in result.stdout

    # Only dotfiles should be symlinked
    assert (base_dir / ".mainrc").is_symlink()
    assert not (base_dir / "main.conf").is_symlink()
    assert (themes_dir / ".light.theme").is_symlink()
    assert not (themes_dir / "dark.theme").is_symlink()
    assert (plugins_dir / ".pluginrc").is_symlink()

def test_add_single_file_still_works(temp_home):
    """Ensure that adding single files still works as before."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a single dotfile
    dotfile = temp_home / ".gitconfig"
    dotfile.write_text("[user]\nname = Test User\n")

    # Add the single file
    result = run_dotkeep("add", ".gitconfig", env=env)
    assert result.returncode == 0
    assert "✓ Added .gitconfig" in result.stdout

    # Verify it's tracked and symlinked correctly
    result2 = run_dotkeep("list-files", env=env)
    assert ".gitconfig" in result2.stdout
    assert (temp_home / ".gitconfig").is_symlink()

def test_delete_directory_symlinks(temp_home):
    """Test deleting a directory managed by dotkeep (dotfiles inside)."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a directory with dotfiles
    test_dir = temp_home / "test_dir"
    test_dir.mkdir()
    (test_dir / ".file1").write_text("content1")
    (test_dir / ".file2").write_text("content2")
    run_dotkeep("add", "test_dir", env=env)

    # Verify dotfiles are symlinked
    assert (test_dir / ".file1").is_symlink()
    assert (test_dir / ".file2").is_symlink()

    # Delete the dotfile
    result = run_dotkeep("delete", "test_dir/.file1", env=env)
    assert result.returncode == 0
    assert "✓ Removed test_dir/.file1" in result.stdout
    assert not (test_dir / ".file1").exists()

def test_restore_directory_symlinks_dotfiles(temp_home):
    """Test restoring a directory managed by dotkeep (dotfiles inside)."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a directory with dotfiles
    test_dir = temp_home / "restore_test"
    test_dir.mkdir()
    (test_dir / ".configrc").write_text("important config")
    run_dotkeep("add", "restore_test", env=env)

    # Remove the symlink (simulate accidental deletion)
    (test_dir / ".configrc").unlink()

    # Restore the dotfile
    result = run_dotkeep("restore", "restore_test/.configrc", env=env)
    assert result.returncode == 0
    assert "✓ Restored restore_test/.configrc" in result.stdout

    # Verify it's restored as a symlink and file is accessible
    assert (test_dir / ".configrc").is_symlink()
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert (test_dir / ".configrc").resolve() == dotkeep_repo / "restore_test" / ".configrc"
    assert (test_dir / ".configrc").read_text() == "important config"
    
def test_pull_no_remote(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    result = run_dotkeep("pull", env=env)
    assert result.returncode != 0
    assert "No 'origin' remote found" in result.stdout or "No 'origin' remote found" in result.stderr

def test_push_no_remote(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    result = run_dotkeep("push", env=env)
    assert result.returncode != 0
    assert "No 'origin' remote found" in result.stdout or "No 'origin' remote found" in result.stderr

def test_version_command(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_dotkeep("version", env=env)
    assert result.returncode == 0
    assert "dotkeep version" in result.stdout

def test_completion_command(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_dotkeep("completion", env=env)
    assert result.returncode == 0
    assert "dotkeep --install-completion" in result.stdout

def test_diagnose_command(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_dotkeep("diagnose", env=env)
    assert result.returncode == 0
    assert "diagnostics" in result.stdout.lower()
    assert "dotkeep repo not initialized" in result.stdout or "No .git directory found" in result.stdout or "✓ Created empty initial commit" in result.stdout or "✓ No uncommitted changes." in result.stdout

def test_add_and_status_untracked_home_dotfiles(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    # Create a dotfile but don't add it
    dotfile = temp_home / ".zshrc"
    dotfile.write_text("export ZSH=1\n")
    result = run_dotkeep("status", env=env)
    assert ".zshrc" in result.stdout

def test_add_directory_and_delete_all_dotfiles_removes_tracked_dir(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    d = temp_home / "mydir"
    d.mkdir()
    (d / ".a").write_text("a")
    (d / ".b").write_text("b")
    run_dotkeep("add", "mydir", env=env)
    # Delete both dotfiles
    run_dotkeep("delete", "mydir/.a", env=env)
    run_dotkeep("delete", "mydir/.b", env=env)
    # tracked_dirs.json should not contain mydir
    tracked_dirs = get_tracked_dirs()
    assert str(d) not in tracked_dirs

def test_restore_nonexistent_file(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    result = run_dotkeep("restore", ".doesnotexist", env=env)
    assert result.returncode != 0
    assert "not tracked by dotkeep" in result.stdout or "not tracked by dotkeep" in result.stderr

def test_delete_non_symlink(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    # Create a file but don't add it
    f = temp_home / ".notalink"
    f.write_text("hi")
    result = run_dotkeep("delete", ".notalink", env=env)
    assert result.returncode != 0
    assert "is not a symlink managed by dotkeep" in result.stdout or "is not a symlink managed by dotkeep" in result.stderr

def test_watcher_starts_and_exits(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    # Add a tracked dir so watcher doesn't exit immediately
    d = temp_home / "watchdir"
    d.mkdir()
    run_dotkeep("add", "watchdir", env=env)
    # Start watcher in a subprocess and kill it after a short time
    import time
    import signal
    proc = subprocess.Popen(["dotkeep", "watch"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate()
    assert b"Starting watcher" in out or b"Watcher stopped" in out or b"Starting watcher" in err or b"Watcher stopped" in err