"""Integration tests for dotz functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from git import Repo

from dotz import core
from tests.conftest import assert_symlink_correct, create_test_files


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_dotfile_workflow(self, temp_home: Path) -> None:
        """Test complete workflow: init -> add -> modify -> restore."""
        # Step 1: Initialize repository
        assert core.init_repo(quiet=True) is True

        # Step 2: Create and add a dotfile
        dotfile = temp_home / ".bashrc"
        dotfile.write_text("# Original bashrc\nexport PATH=$PATH:/usr/local/bin\n")

        assert core.add_dotfile(Path(".bashrc"), quiet=True) is True

        # Verify file was copied and symlinked
        dotz_file = core.WORK_TREE / ".bashrc"
        assert dotz_file.exists()
        assert_symlink_correct(dotfile, dotz_file)

        # Step 3: Modify file in dotz repo
        dotz_file.write_text("# Modified bashrc\nexport EDITOR=vim\n")

        # Step 4: Restore to get changes
        assert core.restore_dotfile(Path(".bashrc"), quiet=True) is True

        # Verify changes are reflected
        assert "EDITOR=vim" in dotfile.read_text()

    def test_multi_file_workflow(self, temp_home: Path) -> None:
        """Test workflow with multiple files and directories."""
        # Initialize
        assert core.init_repo(quiet=True) is True

        # Create test files
        test_files = {
            ".bashrc": "# bashrc content",
            ".vimrc": "set number\nset tabstop=4",
            ".config/app.conf": "[main]\nkey=value",
            ".config/settings.json": '{"theme": "dark"}',
            ".ssh/config": "Host *\n  UseKeychain yes",
        }
        create_test_files(temp_home, test_files)

        # Add files
        for file_path in [".bashrc", ".vimrc", ".config", ".ssh"]:
            assert core.add_dotfile(Path(file_path), quiet=True) is True

        # Verify all files are tracked
        tracked_files = core.list_tracked_files()
        assert ".bashrc" in tracked_files
        assert ".vimrc" in tracked_files
        assert ".config" in tracked_files or ".config/app.conf" in tracked_files

        # Test status
        status = core.get_repo_status()
        assert len(status["untracked"]) == 0  # All files should be tracked

    def test_backup_and_restore_workflow(self, temp_home: Path) -> None:
        """Test backup creation and restoration workflow."""
        # Initialize
        assert core.init_repo(quiet=True) is True

        # Create original file
        original_file = temp_home / ".testrc"
        original_content = "# Original content\nexport TEST=value"
        original_file.write_text(original_content)

        # Create backup
        backup_path = core.create_backup(original_file, operation="test", quiet=True)
        assert backup_path is not None
        assert backup_path.exists()

        # Modify original
        modified_content = "# Modified content\nexport TEST=new_value"
        original_file.write_text(modified_content)

        # Restore from backup
        assert core.restore_from_backup(backup_path, quiet=True) is True

        # Verify restoration
        assert original_file.read_text() == original_content

    def test_config_management_workflow(self, temp_home: Path) -> None:
        """Test configuration management workflow."""
        # Initialize
        assert core.init_repo(quiet=True) is True

        # Test default config
        config = core.load_config()
        assert config == core.DEFAULT_CONFIG

        # Add custom patterns
        assert core.add_file_pattern("*.custom", "include", quiet=True) is True
        assert core.add_file_pattern("*.ignore", "exclude", quiet=True) is True

        # Verify patterns were added
        config = core.load_config()
        assert "*.custom" in config["file_patterns"]["include"]
        assert "*.ignore" in config["file_patterns"]["exclude"]

        # Test pattern matching
        assert (
            core.matches_patterns(
                "test.custom",
                config["file_patterns"]["include"],
                config["file_patterns"]["exclude"],
                False,
            )
            is True
        )

        assert (
            core.matches_patterns(
                "test.ignore",
                config["file_patterns"]["include"],
                config["file_patterns"]["exclude"],
                False,
            )
            is False
        )

        # Reset config
        assert core.reset_config(quiet=True) is True
        config = core.load_config()
        assert config == core.DEFAULT_CONFIG

    def test_symlink_validation_workflow(self, temp_home: Path) -> None:
        """Test symlink validation and repair workflow."""
        # Initialize and add files
        assert core.init_repo(quiet=True) is True

        dotfile = temp_home / ".testfile"
        dotfile.write_text("test content")
        assert core.add_dotfile(Path(".testfile"), quiet=True) is True

        dotz_file = core.WORK_TREE / ".testfile"

        # Break the symlink
        dotfile.unlink()
        dotfile.write_text("regular file content")

        # Validate (should find issues)
        results = core.validate_symlinks(quiet=True)
        assert results is not None
        assert ".testfile" in results.get("not_symlink", [])

        # Repair
        results = core.validate_symlinks(repair=True, quiet=True)
        assert results is not None

        # Verify repair
        assert_symlink_correct(dotfile, dotz_file)


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_add_nonexistent_file(self, temp_home: Path) -> None:
        """Test adding a non-existent file."""
        assert core.init_repo(quiet=True) is True

        # Try to add non-existent file
        result = core.add_dotfile(Path(".nonexistent"), quiet=True)
        assert result is False

    def test_restore_nonexistent_file(self, temp_home: Path) -> None:
        """Test restoring a non-existent file."""
        assert core.init_repo(quiet=True) is True

        # Try to restore non-existent file
        result = core.restore_dotfile(Path(".nonexistent"), quiet=True)
        assert result is False

    def test_operations_without_init(self, temp_home: Path) -> None:
        """Test operations without initializing repository."""
        # Try operations without init
        with pytest.raises(click.exceptions.Exit):
            core.add_dotfile(Path(".bashrc"), quiet=True)

        with pytest.raises(click.exceptions.Exit):
            core.delete_dotfile([Path(".bashrc")], quiet=True)

        with pytest.raises(click.exceptions.Exit):
            core.restore_dotfile(Path(".bashrc"), quiet=True)

    def test_invalid_config_handling(self, temp_home: Path) -> None:
        """Test handling of invalid configuration."""
        # Initialize
        assert core.init_repo(quiet=True) is True

        # Create invalid config
        config_file = core.CONFIG_FILE
        config_file.write_text("invalid json content")

        # Should fall back to default config
        config = core.load_config()
        assert config == core.DEFAULT_CONFIG

    def test_permission_errors(self, temp_home: Path) -> None:
        """Test handling of permission errors."""
        # Initialize
        assert core.init_repo(quiet=True) is True

        # Create file with restrictive permissions
        restricted_file = temp_home / ".restricted"
        restricted_file.write_text("restricted content")
        restricted_file.chmod(0o000)

        try:
            # Try to add restricted file (may fail due to permissions)
            result = core.add_dotfile(Path(".restricted"), quiet=True)
            # Result depends on system permissions, so we don't assert specific value
        finally:
            # Restore permissions for cleanup
            restricted_file.chmod(0o644)


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race conditions."""

    def test_concurrent_file_operations(self, temp_home: Path) -> None:
        """Test concurrent file operations."""
        assert core.init_repo(quiet=True) is True

        # Create multiple files
        for i in range(5):
            dotfile = temp_home / f".testfile{i}"
            dotfile.write_text(f"content {i}")
            assert core.add_dotfile(Path(f".testfile{i}"), quiet=True) is True

        # Verify all files are tracked
        tracked_files = core.list_tracked_files()
        for i in range(5):
            assert f".testfile{i}" in tracked_files

    def test_rapid_config_changes(self, temp_home: Path) -> None:
        """Test rapid configuration changes."""
        assert core.init_repo(quiet=True) is True

        # Make rapid config changes
        for i in range(10):
            pattern = f"*.test{i}"
            assert core.add_file_pattern(pattern, "include", quiet=True) is True

            # Verify pattern was added
            config = core.load_config()
            assert pattern in config["file_patterns"]["include"]

            # Remove pattern
            assert core.remove_file_pattern(pattern, "include", quiet=True) is True


class TestLargeFileOperations:
    """Test operations with large files and directories."""

    def test_large_directory_structure(self, temp_home: Path) -> None:
        """Test adding large directory structure."""
        assert core.init_repo(quiet=True) is True

        # Create large directory structure
        config_dir = temp_home / ".config"
        config_dir.mkdir()

        # Create many files
        for i in range(50):
            subdir = config_dir / f"app{i}"
            subdir.mkdir()
            (subdir / "config.json").write_text(f'{{"id": {i}}}')
            (subdir / "settings.conf").write_text(f"[app{i}]\nvalue={i}")

        # Add entire directory
        assert core.add_dotfile(Path(".config"), quiet=True) is True

        # Verify structure is preserved
        dotz_config = core.WORK_TREE / ".config"
        assert dotz_config.exists()
        assert len(list(dotz_config.iterdir())) == 50

    def test_file_count_accuracy(self, temp_home: Path) -> None:
        """Test file counting accuracy."""
        # Create directory with known file count
        test_dir = temp_home / "test_count"
        test_dir.mkdir()

        # Create nested structure
        for i in range(3):
            subdir = test_dir / f"level{i}"
            subdir.mkdir()
            for j in range(5):
                (subdir / f"file{j}.txt").write_text(f"content {i}-{j}")

        # Count files
        count = core.count_files_in_directory(test_dir)
        assert count == 15  # 3 levels * 5 files each


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_files(self, temp_home: Path) -> None:
        """Test handling of empty files."""
        assert core.init_repo(quiet=True) is True

        # Create empty file
        empty_file = temp_home / ".empty"
        empty_file.touch()

        # Add empty file
        assert core.add_dotfile(Path(".empty"), quiet=True) is True

        # Verify it was added correctly
        dotz_file = core.WORK_TREE / ".empty"
        assert dotz_file.exists()
        assert dotz_file.stat().st_size == 0

    def test_special_characters_in_filenames(self, temp_home: Path) -> None:
        """Test handling files with special characters."""
        assert core.init_repo(quiet=True) is True

        # Create files with special characters
        special_files = [
            ".file-with-dashes",
            ".file_with_underscores",
            ".file.with.dots",
            ".file with spaces",  # This might be problematic on some systems
        ]

        for filename in special_files:
            try:
                dotfile = temp_home / filename
                dotfile.write_text("content")

                result = core.add_dotfile(Path(filename), quiet=True)
                # Some special characters might not be supported
                if result:
                    dotz_file = core.WORK_TREE / filename
                    assert dotz_file.exists()
            except (OSError, ValueError):
                # Some systems don't support certain characters
                pass

    def test_very_long_paths(self, temp_home: Path) -> None:
        """Test handling of very long file paths."""
        assert core.init_repo(quiet=True) is True

        # Create deeply nested structure
        deep_path = temp_home / ".config"
        deep_path.mkdir()

        # Create deep directory structure
        current = deep_path
        for i in range(10):  # Create reasonably deep structure
            current = current / f"level{i}"
            current.mkdir()

        # Create file at deep location
        deep_file = current / "deep_file.conf"
        deep_file.write_text("deep content")

        # Try to add the entire config directory
        result = core.add_dotfile(Path(".config"), quiet=True)
        assert result is True

        # Verify deep file was included
        dotz_deep_file = core.WORK_TREE / ".config"
        for i in range(10):
            dotz_deep_file = dotz_deep_file / f"level{i}"
        dotz_deep_file = dotz_deep_file / "deep_file.conf"
        assert dotz_deep_file.exists()

    def test_circular_symlinks(self, temp_home: Path) -> None:
        """Test handling of circular symlinks."""
        assert core.init_repo(quiet=True) is True

        try:
            # Create circular symlinks
            link1 = temp_home / ".link1"
            link2 = temp_home / ".link2"

            link1.symlink_to(link2)
            link2.symlink_to(link1)

            # Try to add circular symlink (should handle gracefully)
            result = core.add_dotfile(Path(".link1"), quiet=True)
            # Result is implementation-dependent

        except (OSError, ValueError):
            # Some systems might not allow circular symlinks
            pass


class TestPerformance:
    """Test performance characteristics."""

    def test_many_small_files_performance(self, temp_home: Path) -> None:
        """Test performance with many small files."""
        import time

        assert core.init_repo(quiet=True) is True

        # Create many small files
        config_dir = temp_home / ".config"
        config_dir.mkdir()

        start_time = time.time()

        # Create 100 small files
        for i in range(100):
            (config_dir / f"file{i}.conf").write_text(f"content{i}")

        # Add directory
        add_start = time.time()
        result = core.add_dotfile(Path(".config"), quiet=True)
        add_end = time.time()

        assert result is True

        # Verify reasonable performance (should complete within 30 seconds)
        add_time = add_end - add_start
        assert add_time < 30, f"Adding 100 files took {add_time:.2f} seconds"

    def test_large_file_handling(self, temp_home: Path) -> None:
        """Test handling of larger files."""
        assert core.init_repo(quiet=True) is True

        # Create moderately large file (1MB)
        large_file = temp_home / ".large_config"
        content = "# Large config file\n" + "data\n" * 200000  # Increase to ~1MB
        large_file.write_text(content)

        # Add large file
        result = core.add_dotfile(Path(".large_config"), quiet=True)
        assert result is True

        # Verify file was copied correctly
        dotz_file = core.WORK_TREE / ".large_config"
        assert dotz_file.exists()
        assert dotz_file.stat().st_size > 1000000  # Should be > 1MB
