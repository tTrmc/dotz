import os
import shutil
import subprocess
from pathlib import Path

import pytest

@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Set up a temporary HOME and XDG environment for isolation."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    # Remove any existing .dotkeep
    dotkeep = home / ".dotkeep"
    if dotkeep.exists():
        shutil.rmtree(dotkeep)
    return home

def run_dotkeep(*args, env=None):
    """Run the dotkeep CLI with given arguments."""
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
    result = run_dotkeep("add", ".notfound", env=env)
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "not found" in output

def test_status_untracked(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)
    # Create a file but don't add it
    dotfile = temp_home / ".zshrc"
    dotfile.write_text("export ZSH=1\n")
    result = run_dotkeep("status", env=env)
    assert "✓ No changes" in result.stdout

def test_help_and_version(temp_home):
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    result = run_dotkeep("--help", env=env)
    assert result.returncode == 0
    assert "dotkeep - a Git-backed dot-files manager" in result.stdout