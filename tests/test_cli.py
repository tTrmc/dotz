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

def test_add_directory(temp_home):
    """Test adding a directory with multiple files."""
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

    # Verify symlinks are created correctly
    assert (temp_home / ".config" / "myapp" / "config.yaml").is_symlink()
    assert (temp_home / ".config" / "myapp" / "app.conf").is_symlink()
    assert (temp_home / ".config" / "myapp" / "themes" / "dark.theme").is_symlink()

    # Verify symlinks point to the right place
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    assert (temp_home / ".config" / "myapp" / "config.yaml").readlink() == dotkeep_repo / ".config" / "myapp" / "config.yaml"

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
    # Should handle empty directories gracefully
    assert "✓ Added .empty_config" in result.stdout

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

    # Verify directory structure is preserved with symlinks
    assert (temp_home / ".config" / "complexapp" / "main.conf").is_symlink()
    assert (temp_home / ".config" / "complexapp" / "themes" / "light.theme").is_symlink()
    assert (temp_home / ".config" / "complexapp" / "plugins" / "enabled" / "plugin1.conf").is_symlink()

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

def test_add_directory_preserves_permissions(temp_home):
    """Test that file permissions are preserved when adding directories."""
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    run_dotkeep("init", env=env)

    # Create a directory with files having specific permissions
    scripts_dir = temp_home / ".local" / "bin"
    scripts_dir.mkdir(parents=True)
    
    # Create an executable script
    script_file = scripts_dir / "myscript.sh"
    script_file.write_text("#!/bin/bash\necho 'Hello World'\n")
    script_file.chmod(0o755)  # Make it executable
    
    # Create a regular config file
    config_file = scripts_dir / "config.txt"
    config_file.write_text("config data\n")
    config_file.chmod(0o644)  # Regular file permissions

    # Add the directory
    result = run_dotkeep("add", ".local/bin", env=env)
    assert result.returncode == 0

    # Check that permissions are preserved in the repo
    dotkeep_repo = temp_home / ".dotkeep" / "repo"
    repo_script = dotkeep_repo / ".local" / "bin" / "myscript.sh"
    repo_config = dotkeep_repo / ".local" / "bin" / "config.txt"
    
    assert oct(repo_script.stat().st_mode)[-3:] == "755"
    assert oct(repo_config.stat().st_mode)[-3:] == "644"
