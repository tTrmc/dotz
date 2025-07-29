"""Tests for template and profile management functionality."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dotz import templates
from dotz.core import ensure_repo
from tests.conftest import create_test_files


class TestTemplateManagement:
    """Test template creation, application, and management."""

    def test_create_template_from_tracked_files(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test creating a template from currently tracked files."""
        # Add some test files
        test_files = {
            ".bashrc": "# bashrc content",
            ".vimrc": "set number",
            ".config/app.conf": "[main]\nkey=value",
        }
        create_test_files(temp_home, test_files)

        # Add files to dotz
        from dotz.core import add_dotfile

        for file_path in test_files.keys():
            add_dotfile(Path(file_path), quiet=True)

        # Create template
        success = templates.create_template(
            "test-template", "Test template", quiet=True
        )
        assert success

        # Verify template was created
        template_list = templates.list_templates()
        assert len(template_list) == 1
        assert template_list[0]["name"] == "test-template"
        assert template_list[0]["description"] == "Test template"

    def test_create_template_with_specific_files(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test creating a template with specific files."""
        # Add some test files
        test_files = {
            ".bashrc": "# bashrc content",
            ".vimrc": "set number",
            ".config/app.conf": "[main]\nkey=value",
        }
        create_test_files(temp_home, test_files)

        # Add files to dotz
        from dotz.core import add_dotfile

        for file_path in test_files.keys():
            add_dotfile(Path(file_path), quiet=True)

        # Create template with specific files
        success = templates.create_template(
            "partial-template",
            "Partial template",
            files=[".bashrc", ".vimrc"],
            quiet=True,
        )
        assert success

        # Verify template was created with correct files
        template_info = templates.get_template_info("partial-template")
        assert template_info is not None
        assert len(template_info["files"]) == 2
        assert ".bashrc" in template_info["files"]
        assert ".vimrc" in template_info["files"]
        assert ".config/app.conf" not in template_info["files"]

    def test_apply_template(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test applying a template to repository."""
        # Create and populate template
        test_files = {
            ".bashrc": "# template bashrc",
            ".vimrc": '" template vimrc',
        }
        create_test_files(temp_home, test_files)

        from dotz.core import add_dotfile

        for file_path in test_files.keys():
            add_dotfile(Path(file_path), quiet=True)

        templates.create_template("apply-test", quiet=True)

        # Modify files
        (temp_home / ".bashrc").write_text("# modified bashrc")
        (temp_home / ".vimrc").write_text('" modified vimrc')

        # Apply template
        success = templates.apply_template("apply-test", quiet=True)
        assert success

        # Verify files were restored
        work_tree = templates.WORK_TREE
        assert (work_tree / ".bashrc").read_text() == "# template bashrc"
        assert (work_tree / ".vimrc").read_text() == '" template vimrc'

    def test_template_merge_mode(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test applying template in merge mode."""
        # Create template with one file
        test_files = {".bashrc": "# template bashrc"}
        create_test_files(temp_home, test_files)

        from dotz.core import add_dotfile

        add_dotfile(Path(".bashrc"), quiet=True)

        templates.create_template("merge-test", quiet=True)

        # Add new file to repository
        (temp_home / ".new_file").write_text("new content")
        add_dotfile(Path(".new_file"), quiet=True)

        # Apply template in merge mode
        success = templates.apply_template("merge-test", merge=True, quiet=True)
        assert success

        # Verify existing file wasn't overwritten, new file preserved
        work_tree = templates.WORK_TREE
        assert (work_tree / ".new_file").exists()

    def test_delete_template(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test deleting a template."""
        templates.create_template("delete-test", quiet=True)

        # Verify template exists
        template_list = templates.list_templates()
        assert len(template_list) == 1

        # Delete template
        success = templates.delete_template("delete-test", quiet=True)
        assert success

        # Verify template is gone
        template_list = templates.list_templates()
        assert len(template_list) == 0

    def test_template_export_import(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test exporting and importing templates."""
        # Create template
        test_files = {".bashrc": "# export test"}
        create_test_files(temp_home, test_files)

        from dotz.core import add_dotfile

        add_dotfile(Path(".bashrc"), quiet=True)

        templates.create_template("export-test", "Export test template", quiet=True)

        # Export template
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "export-test.tar.gz"
            success = templates.export_template(
                "export-test", str(export_path), quiet=True
            )
            assert success
            assert export_path.exists()

            # Delete original template
            templates.delete_template("export-test", quiet=True)
            assert len(templates.list_templates()) == 0

            # Import template
            success = templates.import_template(str(export_path), quiet=True)
            assert success

            # Verify template was imported
            template_list = templates.list_templates()
            assert len(template_list) == 1
            assert template_list[0]["name"] == "export-test"

    def test_get_template_info(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test getting detailed template information."""
        # Create template with metadata
        test_files = {
            ".bashrc": "# bashrc content",
            ".vimrc": "set number",
        }
        create_test_files(temp_home, test_files)

        from dotz.core import add_dotfile

        for file_path in test_files.keys():
            add_dotfile(Path(file_path), quiet=True)

        templates.create_template("info-test", "Test template for info", quiet=True)

        # Get template info
        info = templates.get_template_info("info-test")
        assert info is not None
        assert info["name"] == "info-test"
        assert info["description"] == "Test template for info"
        assert info["file_count"] == 2
        assert ".bashrc" in info["files"]
        assert ".vimrc" in info["files"]
        assert info["total_size"] > 0


class TestProfileManagement:
    """Test profile creation, switching, and management."""

    def test_create_profile(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test creating a new profile."""
        success = templates.create_profile(
            "test-profile", "Test profile", "development", quiet=True
        )
        assert success

        # Verify profile was created
        profile_list = templates.list_profiles()
        assert len(profile_list) == 1
        assert profile_list[0]["name"] == "test-profile"
        assert profile_list[0]["description"] == "Test profile"
        assert profile_list[0]["environment"] == "development"

    def test_create_profile_copy_from(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test creating a profile by copying from another."""
        # Create first profile with some content
        templates.create_profile("source-profile", quiet=True)

        # Add some files to simulate profile content
        profile_files_dir = templates.PROFILES_DIR / "source-profile" / "files"
        profile_files_dir.mkdir(parents=True, exist_ok=True)
        (profile_files_dir / ".bashrc").write_text("# source bashrc")

        # Create second profile copying from first
        success = templates.create_profile(
            "copy-profile", copy_from="source-profile", quiet=True
        )
        assert success

        # Verify copied content
        copy_files_dir = templates.PROFILES_DIR / "copy-profile" / "files"
        assert (copy_files_dir / ".bashrc").exists()
        assert (copy_files_dir / ".bashrc").read_text() == "# source bashrc"

    def test_switch_profile(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test switching between profiles."""
        # Create profiles
        templates.create_profile("profile1", quiet=True)
        templates.create_profile("profile2", quiet=True)

        # Switch to profile1
        success = templates.switch_profile("profile1", quiet=True)
        assert success
        assert templates.get_active_profile() == "profile1"

        # Switch to profile2
        success = templates.switch_profile("profile2", quiet=True)
        assert success
        assert templates.get_active_profile() == "profile2"

    def test_switch_profile_with_state_saving(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test profile switching saves current state."""
        # Create profiles
        templates.create_profile("save-test1", quiet=True)
        templates.create_profile("save-test2", quiet=True)

        # Switch to first profile and add content
        templates.switch_profile("save-test1", quiet=True)

        # Add files to repository
        test_files = {".bashrc": "# profile1 bashrc"}
        create_test_files(temp_home, test_files)

        from dotz.core import add_dotfile

        add_dotfile(Path(".bashrc"), quiet=True)

        # Switch to second profile (should save state)
        success = templates.switch_profile("save-test2", backup=True, quiet=True)
        assert success

        # Verify state was saved to profile1
        profile1_files = templates.PROFILES_DIR / "save-test1" / "files"
        assert (profile1_files / ".bashrc").exists()
        assert (profile1_files / ".bashrc").read_text() == "# profile1 bashrc"

    def test_delete_profile(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test deleting a profile."""
        templates.create_profile("delete-profile", quiet=True)

        # Verify profile exists
        profile_list = templates.list_profiles()
        assert len(profile_list) == 1

        # Delete profile
        success = templates.delete_profile("delete-profile", quiet=True)
        assert success

        # Verify profile is gone
        profile_list = templates.list_profiles()
        assert len(profile_list) == 0

    def test_cannot_delete_active_profile(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test that active profile cannot be deleted."""
        templates.create_profile("active-profile", quiet=True)
        templates.switch_profile("active-profile", quiet=True)

        # Try to delete active profile
        success = templates.delete_profile("active-profile", quiet=True)
        assert not success

        # Verify profile still exists
        profile_list = templates.list_profiles()
        assert len(profile_list) == 1

    def test_get_profile_info(self, initialized_dotz: Path, temp_home: Path) -> None:
        """Test getting detailed profile information."""
        templates.create_profile(
            "info-profile", "Profile for info test", "testing", quiet=True
        )

        # Add some content to profile
        profile_files_dir = templates.PROFILES_DIR / "info-profile" / "files"
        profile_files_dir.mkdir(parents=True, exist_ok=True)
        (profile_files_dir / ".bashrc").write_text("# info test bashrc")
        (profile_files_dir / ".vimrc").write_text('" info test vimrc')

        # Get profile info
        info = templates.get_profile_info("info-profile")
        assert info is not None
        assert info["name"] == "info-profile"
        assert info["description"] == "Profile for info test"
        assert info["environment"] == "testing"
        assert info["file_count"] >= 2
        assert info["total_size"] > 0
        assert not info["active"]

    def test_profile_active_status(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test profile active status tracking."""
        templates.create_profile("active-test", quiet=True)

        # Profile should not be active initially
        info = templates.get_profile_info("active-test")
        assert not info["active"]

        # Switch to profile
        templates.switch_profile("active-test", quiet=True)

        # Profile should now be active
        info = templates.get_profile_info("active-test")
        assert info["active"]

        # Check in list as well
        profile_list = templates.list_profiles()
        assert profile_list[0]["active"]


class TestErrorHandling:
    """Test error handling in template and profile operations."""

    def test_create_duplicate_template(self, initialized_dotz: Path) -> None:
        """Test creating template with duplicate name."""
        templates.create_template("duplicate", quiet=True)

        # Try to create another with same name
        success = templates.create_template("duplicate", quiet=True)
        assert not success

    def test_apply_nonexistent_template(self, initialized_dotz: Path) -> None:
        """Test applying template that doesn't exist."""
        success = templates.apply_template("nonexistent", quiet=True)
        assert not success

    def test_delete_nonexistent_template(self, initialized_dotz: Path) -> None:
        """Test deleting template that doesn't exist."""
        success = templates.delete_template("nonexistent", quiet=True)
        assert not success

    def test_create_duplicate_profile(self, initialized_dotz: Path) -> None:
        """Test creating profile with duplicate name."""
        templates.create_profile("duplicate", quiet=True)

        # Try to create another with same name
        success = templates.create_profile("duplicate", quiet=True)
        assert not success

    def test_switch_nonexistent_profile(self, initialized_dotz: Path) -> None:
        """Test switching to profile that doesn't exist."""
        success = templates.switch_profile("nonexistent", quiet=True)
        assert not success

    def test_get_info_nonexistent_template(self, initialized_dotz: Path) -> None:
        """Test getting info for template that doesn't exist."""
        info = templates.get_template_info("nonexistent")
        assert info is None

    def test_get_info_nonexistent_profile(self, initialized_dotz: Path) -> None:
        """Test getting info for profile that doesn't exist."""
        info = templates.get_profile_info("nonexistent")
        assert info is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_template_no_files(self, initialized_dotz: Path) -> None:
        """Test creating template when no files are tracked."""
        success = templates.create_template("empty", quiet=True)
        assert not success

    def test_template_with_empty_name(self, initialized_dotz: Path) -> None:
        """Test creating template with empty name."""
        success = templates.create_template("", quiet=True)
        assert not success

    def test_profile_with_empty_name(self, initialized_dotz: Path) -> None:
        """Test creating profile with empty name."""
        success = templates.create_profile("", quiet=True)
        assert not success

    def test_list_templates_empty(self, initialized_dotz: Path) -> None:
        """Test listing templates when none exist."""
        template_list = templates.list_templates()
        assert template_list == []

    def test_list_profiles_empty(self, initialized_dotz: Path) -> None:
        """Test listing profiles when none exist."""
        profile_list = templates.list_profiles()
        assert profile_list == []

    def test_get_active_profile_none(self, initialized_dotz: Path) -> None:
        """Test getting active profile when none is set."""
        active = templates.get_active_profile()
        assert active is None
