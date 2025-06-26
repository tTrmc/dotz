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

    # Try to add a file that doesn't exist
    result = run_dotkeep("add", ".nonexistent", env=env)
    assert result.returncode != 0
    assert "not found" in result.stderr or "not found" in result.stdout

def test_add_directory_creates_directory_symlink(temp_home):
    """Test that adding a directory creates a directory symlink, not individual file symlinks."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a config directory with multiple files
    config_dir = temp_home / ".config" / "myapp"
    config_dir.mkdir(parents=True)
    
    # Create files in the directory
    (config_dir / "config.yaml").write_text("setting1: value1\nsetting2: value2\n")
    (config_dir / "app.conf").write_text("[section]\noption=value\n")
    
    # Create a subdirectory with a file
    subdir = config_dir / "themes"
    subdir.mkdir()
    (subdir / "dark.theme").write_text("background: black\nforeground: white\n")

    # Add the directory
    result = run_dotkeep("add", ".config/myapp", env=env)
    assert result.returncode == 0
    assert "✓ Added .config/myapp (3 files)" in result.stdout

    # Verify all files are tracked
    result2 = run_dotkeep("list-files", env=env)
    assert ".config/myapp/config.yaml" in result2.stdout
    assert ".config/myapp/app.conf" in result2.stdout
    assert ".config/myapp/themes/dark.theme" in result2.stdout

    # THE KEY TEST: Verify the directory itself is a symlink, not individual files
    myapp_dir = temp_home / ".config" / "myapp"
    assert myapp_dir.is_symlink(), "The directory should be a symlink"
    assert not (myapp_dir / "config.yaml").is_symlink(), "Individual files should NOT be symlinks when directory is symlinked"
    assert not (myapp_dir / "app.conf").is_symlink(), "Individual files should NOT be symlinks when directory is symlinked"

    # Verify symlink points to the right place
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert myapp_dir.readlink() == dotkeep_repo / ".config" / "myapp"

def test_directory_symlink_tracks_new_files(temp_home):
    """Test that new files added to a symlinked directory are automatically tracked."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a directory
    dotfolder = temp_home / "dotfolder"
    dotfolder.mkdir()
    (dotfolder / ".dot1").write_text("original file\n")
    
    result = run_dotkeep("add", "dotfolder", env=env)
    assert result.returncode == 0

    # Verify it's a directory symlink
    assert dotfolder.is_symlink()

    # Add a new file to the directory (this should appear in the repo automatically)
    (dotfolder / ".dot2").write_text("new file\n")

    # The new file should exist in the repo because dotfolder is a symlink to the repo
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert (dotkeep_repo / "dotfolder" / ".dot2").exists()
    
    # Both files should be accessible through the symlinked directory
    assert (dotfolder / ".dot1").exists()
    assert (dotfolder / ".dot2").exists()

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
    assert "✓ Added .empty_config (empty directory)" in result.stdout

    # Verify it's a directory symlink
    assert empty_dir.is_symlink()

def test_add_directory_with_subdirectories(temp_home):
    """Test adding a directory with nested subdirectories."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a complex directory structure
    base_dir = temp_home / ".config" / "complexapp"
    base_dir.mkdir(parents=True)
    
    # Files at root level
    (base_dir / "main.conf").write_text("main config\n")
    
    # Nested subdirectories
    themes_dir = base_dir / "themes"
    themes_dir.mkdir()
    (themes_dir / "light.theme").write_text("light theme\n")
    (themes_dir / "dark.theme").write_text("dark theme\n")
    
    plugins_dir = base_dir / "plugins" / "enabled"
    plugins_dir.mkdir(parents=True)
    (plugins_dir / "plugin1.conf").write_text("plugin1 config\n")
    
    # Add the entire directory
    result = run_dotkeep("add", ".config/complexapp", env=env)
    assert result.returncode == 0
    assert "✓ Added .config/complexapp (4 files)" in result.stdout

    # Verify all files are tracked
    result2 = run_dotkeep("list-files", env=env)
    tracked_files = result2.stdout
    assert ".config/complexapp/main.conf" in tracked_files
    assert ".config/complexapp/themes/light.theme" in tracked_files
    assert ".config/complexapp/themes/dark.theme" in tracked_files
    assert ".config/complexapp/plugins/enabled/plugin1.conf" in tracked_files

    # Verify the main directory is a symlink, not subdirectories
    complexapp_dir = temp_home / ".config" / "complexapp"
    assert complexapp_dir.is_symlink(), "Main directory should be a symlink"
    assert not (complexapp_dir / "themes").is_symlink(), "Subdirectories should NOT be symlinks"
    assert not (complexapp_dir / "plugins").is_symlink(), "Subdirectories should NOT be symlinks"

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

def test_delete_directory(temp_home):
    """Test deleting a directory managed by dotkeep."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a directory
    test_dir = temp_home / ".test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    
    run_dotkeep("add", ".test_dir", env=env)
    
    # Verify it's added and is a symlink
    assert test_dir.is_symlink()
    
    # Delete the directory
    result = run_dotkeep("delete", ".test_dir", env=env)
    assert result.returncode == 0
    assert "✓ Removed .test_dir" in result.stdout
    
    # Verify directory is gone from both home and repo
    assert not test_dir.exists()
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert not (dotkeep_repo / ".test_dir").exists()

def test_restore_directory(temp_home):
    """Test restoring a directory managed by dotkeep."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create and add a directory
    test_dir = temp_home / ".restore_test"
    test_dir.mkdir()
    (test_dir / "config.txt").write_text("important config")
    
    run_dotkeep("add", ".restore_test", env=env)
    
    # Remove the symlink (simulate accidental deletion)
    test_dir.unlink()
    
    # Restore the directory
    result = run_dotkeep("restore", ".restore_test", env=env)
    assert result.returncode == 0
    assert "✓ Restored .restore_test" in result.stdout
    
    # Verify it's restored as a symlink and files are accessible
    assert test_dir.is_symlink()
    assert (test_dir / "config.txt").read_text() == "important config"
