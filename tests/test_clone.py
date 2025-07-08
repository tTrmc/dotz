"""Tests for the clone functionality."""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from git import Repo

from loom import cli
from loom.core import add_dotfile, clone_repo, init_repo, update_paths


@pytest.fixture
def temp_source_repo() -> Generator[Path, None, None]:
    """Create a temporary source repository with some dotfiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_home = Path(temp_dir) / "source_home"
        source_home.mkdir()

        # Set up the source environment
        update_paths(source_home)

        # Create some test dotfiles in source home
        (source_home / ".bashrc").write_text("# Source bashrc\nexport TEST=source")
        (source_home / ".gitconfig").write_text("[user]\n    name = Test User")
        (source_home / ".config").mkdir()
        (source_home / ".config" / "app.conf").write_text("config=test")

        # Initialize loom and add files
        init_repo(quiet=True)
        add_dotfile(Path(".bashrc"), quiet=True)
        add_dotfile(Path(".gitconfig"), quiet=True)
        add_dotfile(Path(".config"), quiet=True)

        yield source_home


class TestCloneFunction:
    """Test the clone_repo function."""

    def test_clone_basic_functionality(self, temp_source_repo: Path) -> None:
        """Test basic clone functionality."""
        # Create destination environment
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            # Update paths for destination
            update_paths(dest_home)

            # Get source repo path
            source_loom_dir = temp_source_repo / ".loom"
            source_repo_path = source_loom_dir / "repo"

            # Clone the repository
            success = clone_repo(str(source_repo_path), quiet=True)
            assert success

            # Verify loom directory structure exists
            dest_loom_dir = dest_home / ".loom"
            dest_repo_path = dest_loom_dir / "repo"
            assert dest_loom_dir.exists()
            assert dest_repo_path.exists()

            # Verify it's a valid git repository
            repo = Repo(str(dest_repo_path))
            assert not repo.bare

            # Verify files were restored as symlinks
            bashrc = dest_home / ".bashrc"
            gitconfig = dest_home / ".gitconfig"
            config_dir = dest_home / ".config"
            app_conf = dest_home / ".config" / "app.conf"

            assert bashrc.is_symlink()
            assert gitconfig.is_symlink()
            assert app_conf.is_symlink()

            # Verify symlink targets are correct
            assert bashrc.resolve() == dest_repo_path / ".bashrc"
            assert gitconfig.resolve() == dest_repo_path / ".gitconfig"
            assert app_conf.resolve() == dest_repo_path / ".config" / "app.conf"

            # Verify file contents
            assert "export TEST=source" in bashrc.read_text()
            assert "Test User" in gitconfig.read_text()
            assert "config=test" in app_conf.read_text()

    def test_clone_already_initialized(self, temp_source_repo: Path) -> None:
        """Test cloning when loom is already initialized."""
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            update_paths(dest_home)

            # Initialize loom first
            init_repo(quiet=True)

            # Try to clone - should fail
            source_repo_path = temp_source_repo / ".loom" / "repo"
            success = clone_repo(str(source_repo_path), quiet=True)
            assert not success

    def test_clone_nonexistent_repo(self) -> None:
        """Test cloning from a nonexistent repository."""
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            update_paths(dest_home)

            # Try to clone from nonexistent path
            success = clone_repo("/nonexistent/repo/path", quiet=True)
            assert not success

            # Verify cleanup - loom directory should not exist
            dest_loom_dir = dest_home / ".loom"
            assert not dest_loom_dir.exists()

    def test_clone_empty_repository(self, temp_source_repo: Path) -> None:
        """Test cloning an empty repository."""
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            update_paths(dest_home)

            # Create an empty repository
            empty_repo_path = Path(dest_temp) / "empty_repo"
            empty_repo_path.mkdir()
            Repo.init(str(empty_repo_path))

            # Clone the empty repository
            success = clone_repo(str(empty_repo_path), quiet=True)
            assert success

            # Verify structure exists but no files restored
            dest_loom_dir = dest_home / ".loom"
            assert dest_loom_dir.exists()
            assert (dest_loom_dir / "repo").exists()

    def test_clone_overwrites_existing_files(self, temp_source_repo: Path) -> None:
        """Test that clone overwrites existing files in home directory."""
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            update_paths(dest_home)

            # Create existing files that will be overwritten
            (dest_home / ".bashrc").write_text("# Existing bashrc")
            (dest_home / ".gitconfig").write_text("[user]\n    name = Existing User")

            # Clone repository
            source_repo_path = temp_source_repo / ".loom" / "repo"
            success = clone_repo(str(source_repo_path), quiet=True)
            assert success

            # Verify files were overwritten with symlinks
            bashrc = dest_home / ".bashrc"
            gitconfig = dest_home / ".gitconfig"

            assert bashrc.is_symlink()
            assert gitconfig.is_symlink()

            # Verify content is from source, not the existing files
            assert "export TEST=source" in bashrc.read_text()
            assert "Test User" in gitconfig.read_text()

    def test_clone_partial_failure_recovery(self, temp_source_repo: Path) -> None:
        """Test that clone handles partial failures gracefully."""
        with tempfile.TemporaryDirectory() as dest_temp:
            dest_home = Path(dest_temp) / "dest_home"
            dest_home.mkdir()

            update_paths(dest_home)

            # Create a file that can't be overwritten (simulate permission error)
            protected_file = dest_home / ".bashrc"
            protected_file.write_text("protected")
            protected_file.chmod(0o000)  # No permissions

            try:
                # Clone repository - should succeed but with some failures
                source_repo_path = temp_source_repo / ".loom" / "repo"
                success = clone_repo(str(source_repo_path), quiet=True)
                assert success  # Overall operation should still succeed

                # Other files should still be restored
                gitconfig = dest_home / ".gitconfig"
                app_conf = dest_home / ".config" / "app.conf"

                assert gitconfig.exists()
                assert app_conf.exists()

            finally:
                # Clean up - restore permissions so temp directory can be deleted
                if protected_file.exists():
                    protected_file.chmod(0o666)


class TestCloneCLIIntegration:
    """Test clone functionality through CLI."""

    def test_clone_command_exists(self) -> None:
        """Test that the clone command is available in CLI."""
        # Test that we can run the CLI help and see clone in the output

        # Test that the clone command exists by running --help
        result = subprocess.run(
            [sys.executable, "-m", "loom.cli", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/moustafasalem/Documents/dotkeep",
        )
        assert result.returncode == 0
        assert "clone" in result.stdout
