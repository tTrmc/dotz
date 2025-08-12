"""
Test module for dotz templates and profiles functionality.

This module tests template and profile management including creation,
listing, application, import/export, and metadata handling.
"""

import json
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call

import pytest

from dotz import templates
from dotz.exceptions import (
    DotzArchiveError,
    DotzFileNotFoundError,
    DotzProfileError,
    DotzTemplateError,
    DotzSecurityError,
)


class TestTemplateDirectoryManagement:
    """Test suite for template directory management."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.templates_dir = self.dotz_dir / "templates"
        self.profiles_dir = self.dotz_dir / "profiles"
        
        # Update templates module paths
        templates.TEMPLATES_DIR = self.templates_dir
        templates.PROFILES_DIR = self.profiles_dir
        templates.ACTIVE_PROFILE_PATH = self.dotz_dir / "active_profile"
    
    def test_get_templates_dir_creates_directory(self):
        """Test that get_templates_dir creates the directory if it doesn't exist."""
        # Ensure directory doesn't exist initially
        assert not self.templates_dir.exists()
        
        result = templates.get_templates_dir()
        
        assert result == self.templates_dir
        assert self.templates_dir.exists()
        assert self.templates_dir.is_dir()
    
    def test_get_templates_dir_existing_directory(self):
        """Test get_templates_dir with existing directory."""
        # Create directory first
        self.templates_dir.mkdir(parents=True)
        
        result = templates.get_templates_dir()
        
        assert result == self.templates_dir
        assert self.templates_dir.exists()
    
    def test_get_profiles_dir_creates_directory(self):
        """Test that get_profiles_dir creates the directory if it doesn't exist."""
        # Ensure directory doesn't exist initially
        assert not self.profiles_dir.exists()
        
        result = templates.get_profiles_dir()
        
        assert result == self.profiles_dir
        assert self.profiles_dir.exists()
        assert self.profiles_dir.is_dir()


class TestTemplateManagement:
    """Test suite for template management functions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.templates_dir = self.dotz_dir / "templates"
        self.work_tree = self.dotz_dir / "repo"
        
        # Update templates module paths
        templates.TEMPLATES_DIR = self.templates_dir
        templates.WORK_TREE = self.work_tree
        
        # Create necessary directories
        self.dotz_dir.mkdir()
        self.templates_dir.mkdir()
        self.work_tree.mkdir()
    
    def test_list_templates_empty_directory(self):
        """Test listing templates when directory is empty."""
        result = templates.list_templates()
        
        assert result == []
    
    def test_list_templates_with_valid_templates(self):
        """Test listing templates with valid metadata."""
        # Create test templates
        template1_dir = self.templates_dir / "dev"
        template1_dir.mkdir()
        template1_metadata = {
            "name": "dev",
            "description": "Development environment",
            "created": "2024-01-01T12:00:00Z",
            "files": [".bashrc", ".vimrc"]
        }
        (template1_dir / "template.json").write_text(json.dumps(template1_metadata))
        
        template2_dir = self.templates_dir / "minimal"
        template2_dir.mkdir()
        template2_metadata = {
            "name": "minimal",
            "description": "Minimal setup",
            "created": "2024-01-02T12:00:00Z",
            "files": [".bashrc"]
        }
        (template2_dir / "template.json").write_text(json.dumps(template2_metadata))
        
        result = templates.list_templates()
        
        assert len(result) == 2
        # Should be sorted by creation date
        assert result[0]["name"] == "dev"
        assert result[1]["name"] == "minimal"
        assert "path" in result[0]
        assert "path" in result[1]
    
    def test_list_templates_with_corrupted_metadata(self):
        """Test listing templates with corrupted metadata files."""
        # Create template with corrupted metadata
        template_dir = self.templates_dir / "corrupted"
        template_dir.mkdir()
        (template_dir / "template.json").write_text("invalid json content")
        
        result = templates.list_templates()
        
        assert len(result) == 1
        assert result[0]["name"] == "corrupted"
        assert result[0]["description"] == "Template with corrupted metadata"
        assert result[0]["files"] == []
    
    def test_list_templates_ignores_non_directories(self):
        """Test that list_templates ignores non-directory files."""
        # Create a file in templates directory
        (self.templates_dir / "not_a_template.txt").write_text("content")
        
        result = templates.list_templates()
        
        assert result == []
    
    @patch("dotz.templates.ensure_repo")
    def test_create_template_from_tracked_files(self, mock_ensure_repo):
        """Test creating template from currently tracked files."""
        # Mock git repository
        mock_repo = Mock()
        mock_repo.git.ls_files.return_value = ".bashrc\\n.vimrc\\n.gitconfig"
        mock_ensure_repo.return_value = mock_repo
        
        # Create source files in work tree
        (self.work_tree / ".bashrc").write_text("bash content")
        (self.work_tree / ".vimrc").write_text("vim content")
        (self.work_tree / ".gitconfig").write_text("git content")
        
        with patch("dotz.templates.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
            
            result = templates.create_template("dev", "Development setup")
            
        assert result is True
        
        # Check template directory was created
        template_dir = self.templates_dir / "dev"
        assert template_dir.exists()
        
        # Check metadata file
        metadata_file = template_dir / "template.json"
        assert metadata_file.exists()
        metadata = json.loads(metadata_file.read_text())
        assert metadata["name"] == "dev"
        assert metadata["description"] == "Development setup"
        assert set(metadata["files"]) == {".bashrc", ".vimrc", ".gitconfig"}
        
        # Check template files were copied
        assert (template_dir / ".bashrc").exists()
        assert (template_dir / ".vimrc").exists()
        assert (template_dir / ".gitconfig").exists()
    
    def test_create_template_with_specific_files(self):
        """Test creating template with specific files."""
        # Create source files in work tree
        (self.work_tree / ".bashrc").write_text("bash content")
        (self.work_tree / ".vimrc").write_text("vim content")
        
        with patch("dotz.templates.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
            
            result = templates.create_template("minimal", "Minimal setup", files=[".bashrc"])
            
        assert result is True
        
        # Check only specified file was included
        template_dir = self.templates_dir / "minimal"
        metadata_file = template_dir / "template.json"
        metadata = json.loads(metadata_file.read_text())
        assert metadata["files"] == [".bashrc"]
        assert (template_dir / ".bashrc").exists()
        assert not (template_dir / ".vimrc").exists()
    
    def test_create_template_already_exists(self):
        """Test creating template that already exists."""
        # Create existing template
        template_dir = self.templates_dir / "existing"
        template_dir.mkdir()
        
        result = templates.create_template("existing", quiet=True)
        
        assert result is False
    
    def test_create_template_missing_source_file(self):
        """Test creating template with missing source file."""
        with pytest.raises(DotzTemplateError):
            templates.create_template("test", files=[".nonexistent"])
    
    @patch("dotz.templates.ensure_repo")
    def test_apply_template_success(self, mock_ensure_repo):
        """Test successful template application."""
        # Create template
        template_dir = self.templates_dir / "dev"
        template_dir.mkdir()
        
        # Create template metadata
        metadata = {
            "name": "dev",
            "description": "Development setup",
            "files": [".bashrc", ".vimrc"]
        }
        (template_dir / "template.json").write_text(json.dumps(metadata))
        
        # Create template files
        (template_dir / ".bashrc").write_text("bash template content")
        (template_dir / ".vimrc").write_text("vim template content")
        
        # Mock git operations
        mock_repo = Mock()
        mock_ensure_repo.return_value = mock_repo
        
        result = templates.apply_template("dev")
        
        assert result is True
        
        # Check files were copied to work tree
        assert (self.work_tree / ".bashrc").exists()
        assert (self.work_tree / ".vimrc").exists()
        assert (self.work_tree / ".bashrc").read_text() == "bash template content"
        
        # Check git operations were called
        mock_repo.index.add.assert_called()
        mock_repo.index.commit.assert_called()
    
    def test_apply_template_nonexistent(self):
        """Test applying nonexistent template."""
        with pytest.raises(DotzTemplateError):
            templates.apply_template("nonexistent")
    
    def test_apply_template_merge_mode(self):
        """Test applying template in merge mode."""
        # Create template
        template_dir = self.templates_dir / "dev"
        template_dir.mkdir()
        metadata = {"name": "dev", "files": [".bashrc"]}
        (template_dir / "template.json").write_text(json.dumps(metadata))
        (template_dir / ".bashrc").write_text("template content")
        
        # Create existing file in work tree
        (self.work_tree / ".bashrc").write_text("existing content")
        
        with patch("dotz.templates.ensure_repo") as mock_ensure_repo:
            mock_repo = Mock()
            mock_ensure_repo.return_value = mock_repo
            
            result = templates.apply_template("dev", merge=True)
            
        assert result is True
        # In merge mode, existing file should not be overwritten
        assert (self.work_tree / ".bashrc").read_text() == "existing content"
    
    def test_delete_template_success(self):
        """Test successful template deletion."""
        # Create template
        template_dir = self.templates_dir / "test"
        template_dir.mkdir()
        (template_dir / "template.json").write_text('{"name": "test"}')
        (template_dir / ".bashrc").write_text("content")
        
        result = templates.delete_template("test")
        
        assert result is True
        assert not template_dir.exists()
    
    def test_delete_template_nonexistent(self):
        """Test deleting nonexistent template."""
        with pytest.raises(DotzTemplateError):
            templates.delete_template("nonexistent")
    
    def test_get_template_info_success(self):
        """Test getting template information."""
        # Create template
        template_dir = self.templates_dir / "dev"
        template_dir.mkdir()
        metadata = {
            "name": "dev",
            "description": "Development setup",
            "created": "2024-01-01T12:00:00Z",
            "files": [".bashrc", ".vimrc"]
        }
        (template_dir / "template.json").write_text(json.dumps(metadata))
        
        result = templates.get_template_info("dev")
        
        assert result["name"] == "dev"
        assert result["description"] == "Development setup"
        assert len(result["files"]) == 2
    
    def test_get_template_info_nonexistent(self):
        """Test getting info for nonexistent template."""
        with pytest.raises(DotzTemplateError):
            templates.get_template_info("nonexistent")


class TestTemplateImportExport:
    """Test suite for template import/export functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.templates_dir = self.dotz_dir / "templates"
        
        templates.TEMPLATES_DIR = self.templates_dir
        
        self.dotz_dir.mkdir()
        self.templates_dir.mkdir()
    
    def test_export_template_success(self):
        """Test successful template export."""
        # Create template
        template_dir = self.templates_dir / "dev"
        template_dir.mkdir()
        
        metadata = {
            "name": "dev",
            "description": "Development setup",
            "files": [".bashrc", ".vimrc"]
        }
        (template_dir / "template.json").write_text(json.dumps(metadata))
        (template_dir / ".bashrc").write_text("bash content")
        (template_dir / ".vimrc").write_text("vim content")
        
        export_path = self.home_dir / "export.tar.gz"
        
        result = templates.export_template("dev", str(export_path))
        
        assert result is True
        assert export_path.exists()
        
        # Verify archive contents
        with tarfile.open(export_path, "r:gz") as tar:
            names = tar.getnames()
            assert "template.json" in names
            assert ".bashrc" in names
            assert ".vimrc" in names
    
    def test_export_template_nonexistent(self):
        """Test exporting nonexistent template."""
        export_path = self.home_dir / "export.tar.gz"
        
        with pytest.raises(DotzTemplateError):
            templates.export_template("nonexistent", str(export_path))
    
    def test_import_template_success(self):
        """Test successful template import."""
        # Create archive to import
        archive_path = self.home_dir / "import.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            # Add metadata
            metadata = {
                "name": "imported",
                "description": "Imported template",
                "files": [".bashrc"]
            }
            metadata_info = tarfile.TarInfo("template.json")
            metadata_content = json.dumps(metadata).encode()
            metadata_info.size = len(metadata_content)
            tar.addfile(metadata_info, fileobj=tempfile.BytesIO(metadata_content))
            
            # Add file
            file_info = tarfile.TarInfo(".bashrc")
            file_content = b"bash content"
            file_info.size = len(file_content)
            tar.addfile(file_info, fileobj=tempfile.BytesIO(file_content))
        
        result = templates.import_template(str(archive_path))
        
        assert result is True
        
        # Check template was created
        template_dir = self.templates_dir / "imported"
        assert template_dir.exists()
        assert (template_dir / "template.json").exists()
        assert (template_dir / ".bashrc").exists()
    
    def test_import_template_nonexistent_archive(self):
        """Test importing from nonexistent archive."""
        with pytest.raises(DotzArchiveError):
            templates.import_template("/nonexistent/archive.tar.gz")
    
    def test_import_template_invalid_archive(self):
        """Test importing from invalid archive."""
        # Create invalid archive
        invalid_archive = self.home_dir / "invalid.tar.gz"
        invalid_archive.write_text("not a tar file")
        
        with pytest.raises(DotzArchiveError):
            templates.import_template(str(invalid_archive))
    
    def test_import_template_security_check(self):
        """Test security checks during template import."""
        # Create archive with path traversal attempt
        archive_path = self.home_dir / "malicious.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            # Try to write outside template directory
            malicious_info = tarfile.TarInfo("../../../etc/passwd")
            malicious_info.size = 5
            tar.addfile(malicious_info, fileobj=tempfile.BytesIO(b"test"))
        
        with pytest.raises(DotzSecurityError):
            templates.import_template(str(archive_path))


class TestProfileManagement:
    """Test suite for profile management functions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.profiles_dir = self.dotz_dir / "profiles"
        self.active_profile_file = self.dotz_dir / "active_profile"
        
        templates.PROFILES_DIR = self.profiles_dir
        templates.ACTIVE_PROFILE_PATH = self.active_profile_file
        
        self.dotz_dir.mkdir()
        self.profiles_dir.mkdir()
    
    def test_list_profiles_empty(self):
        """Test listing profiles when directory is empty."""
        result = templates.list_profiles()
        
        assert result == []
    
    def test_list_profiles_with_valid_profiles(self):
        """Test listing profiles with valid metadata."""
        # Create test profiles
        profile1_dir = self.profiles_dir / "work"
        profile1_dir.mkdir()
        profile1_metadata = {
            "name": "work",
            "description": "Work environment",
            "template": "dev",
            "created": "2024-01-01T12:00:00Z"
        }
        (profile1_dir / "profile.json").write_text(json.dumps(profile1_metadata))
        
        profile2_dir = self.profiles_dir / "personal"
        profile2_dir.mkdir()
        profile2_metadata = {
            "name": "personal",
            "description": "Personal setup",
            "created": "2024-01-02T12:00:00Z"
        }
        (profile2_dir / "profile.json").write_text(json.dumps(profile2_metadata))
        
        result = templates.list_profiles()
        
        assert len(result) == 2
        assert result[0]["name"] == "work"
        assert result[1]["name"] == "personal"
    
    def test_create_profile_success(self):
        """Test successful profile creation."""
        with patch("dotz.templates.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
            
            result = templates.create_profile(
                "work", 
                description="Work environment",
                template="dev",
                environment={"EDITOR": "code"}
            )
            
        assert result is True
        
        # Check profile directory was created
        profile_dir = self.profiles_dir / "work"
        assert profile_dir.exists()
        
        # Check metadata
        metadata_file = profile_dir / "profile.json"
        assert metadata_file.exists()
        metadata = json.loads(metadata_file.read_text())
        assert metadata["name"] == "work"
        assert metadata["description"] == "Work environment"
        assert metadata["template"] == "dev"
        assert metadata["environment"]["EDITOR"] == "code"
    
    def test_create_profile_already_exists(self):
        """Test creating profile that already exists."""
        # Create existing profile
        profile_dir = self.profiles_dir / "existing"
        profile_dir.mkdir()
        
        result = templates.create_profile("existing", quiet=True)
        
        assert result is False
    
    def test_switch_profile_success(self):
        """Test successful profile switching."""
        # Create profile
        profile_dir = self.profiles_dir / "work"
        profile_dir.mkdir()
        metadata = {
            "name": "work",
            "template": "dev",
            "environment": {"EDITOR": "code"}
        }
        (profile_dir / "profile.json").write_text(json.dumps(metadata))
        
        with patch("dotz.templates.apply_template") as mock_apply, \
             patch("dotz.templates.datetime") as mock_datetime:
            
            mock_apply.return_value = True
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
            
            result = templates.switch_profile("work")
            
        assert result is True
        
        # Check active profile was set
        assert self.active_profile_file.exists()
        assert self.active_profile_file.read_text().strip() == "work"
        
        # Check template was applied
        mock_apply.assert_called_once_with("dev", merge=False)
    
    def test_switch_profile_nonexistent(self):
        """Test switching to nonexistent profile."""
        with pytest.raises(DotzProfileError):
            templates.switch_profile("nonexistent")
    
    def test_get_current_profile(self):
        """Test getting current active profile."""
        # Set active profile
        self.active_profile_file.write_text("work")
        
        result = templates.get_current_profile()
        
        assert result == "work"
    
    def test_get_current_profile_no_active(self):
        """Test getting current profile when none is active."""
        result = templates.get_current_profile()
        
        assert result is None
    
    def test_delete_profile_success(self):
        """Test successful profile deletion."""
        # Create profile
        profile_dir = self.profiles_dir / "test"
        profile_dir.mkdir()
        (profile_dir / "profile.json").write_text('{"name": "test"}')
        
        result = templates.delete_profile("test")
        
        assert result is True
        assert not profile_dir.exists()
    
    def test_delete_profile_active(self):
        """Test deleting currently active profile."""
        # Create and activate profile
        profile_dir = self.profiles_dir / "active"
        profile_dir.mkdir()
        (profile_dir / "profile.json").write_text('{"name": "active"}')
        self.active_profile_file.write_text("active")
        
        result = templates.delete_profile("active")
        
        assert result is True
        assert not profile_dir.exists()
        # Active profile should be cleared
        assert not self.active_profile_file.exists()
    
    def test_copy_profile_success(self):
        """Test successful profile copying."""
        # Create source profile
        source_dir = self.profiles_dir / "source"
        source_dir.mkdir()
        source_metadata = {
            "name": "source",
            "description": "Source profile",
            "template": "dev"
        }
        (source_dir / "profile.json").write_text(json.dumps(source_metadata))
        
        with patch("dotz.templates.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
            
            result = templates.copy_profile("source", "copy", "Copied profile")
            
        assert result is True
        
        # Check copy was created
        copy_dir = self.profiles_dir / "copy"
        assert copy_dir.exists()
        copy_metadata = json.loads((copy_dir / "profile.json").read_text())
        assert copy_metadata["name"] == "copy"
        assert copy_metadata["description"] == "Copied profile"
        assert copy_metadata["template"] == "dev"  # Should inherit from source
    
    def test_copy_profile_nonexistent_source(self):
        """Test copying from nonexistent profile."""
        with pytest.raises(DotzProfileError):
            templates.copy_profile("nonexistent", "copy")


class TestProfileBackupRestore:
    """Test suite for profile backup and restore functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.profiles_dir = self.dotz_dir / "profiles"
        
        templates.PROFILES_DIR = self.profiles_dir
        
        self.dotz_dir.mkdir()
        self.profiles_dir.mkdir()
    
    def test_backup_profile_success(self):
        """Test successful profile backup."""
        # Create profile with state
        profile_dir = self.profiles_dir / "work"
        profile_dir.mkdir()
        
        metadata = {"name": "work", "description": "Work profile"}
        (profile_dir / "profile.json").write_text(json.dumps(metadata))
        (profile_dir / "state.json").write_text('{"last_used": "2024-01-01"}')
        
        backup_dir = profile_dir / "backup"
        
        result = templates.backup_profile_state("work")
        
        assert result is True
        # Should create backup directory with timestamp
        backups = list(profile_dir.glob("backup_*"))
        assert len(backups) == 1
    
    def test_restore_profile_state_success(self):
        """Test successful profile state restoration."""
        # Create profile with backup
        profile_dir = self.profiles_dir / "work"
        profile_dir.mkdir()
        
        backup_dir = profile_dir / "backup_20240101_120000"
        backup_dir.mkdir()
        (backup_dir / "state.json").write_text('{"restored": true}')
        
        result = templates.restore_profile_state("work", "backup_20240101_120000")
        
        assert result is True
        # Check state was restored
        state_file = profile_dir / "state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["restored"] is True


class TestErrorHandling:
    """Test suite for error handling in templates module."""
    
    @pytest.fixture(autouse=True)
    def setup(self, isolated_home):
        """Set up test environment before each test."""
        self.home_dir = isolated_home
        self.dotz_dir = isolated_home / ".dotz"
        self.templates_dir = self.dotz_dir / "templates"
        
        templates.TEMPLATES_DIR = self.templates_dir
        
        self.dotz_dir.mkdir()
        self.templates_dir.mkdir()
    
    def test_create_template_permission_error(self):
        """Test template creation with permission errors."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(DotzTemplateError):
                templates.create_template("test")
    
    def test_apply_template_corrupted_metadata(self):
        """Test applying template with corrupted metadata."""
        # Create template with invalid metadata
        template_dir = self.templates_dir / "corrupted"
        template_dir.mkdir()
        (template_dir / "template.json").write_text("invalid json")
        
        with pytest.raises(DotzTemplateError):
            templates.apply_template("corrupted")
    
    def test_import_template_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        archive_path = self.home_dir / "malicious.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            # Create entry that tries to escape template directory
            info = tarfile.TarInfo("../../../etc/passwd")
            info.size = 4
            tar.addfile(info, fileobj=tempfile.BytesIO(b"test"))
        
        with pytest.raises(DotzSecurityError):
            templates.import_template(str(archive_path))
    
    def test_switch_profile_missing_template(self):
        """Test switching to profile with missing template."""
        # Create profile that references nonexistent template
        profile_dir = self.profiles_dir / "broken"
        profile_dir.mkdir()
        metadata = {
            "name": "broken",
            "template": "nonexistent_template"
        }
        (profile_dir / "profile.json").write_text(json.dumps(metadata))
        
        with patch("dotz.templates.apply_template") as mock_apply:
            mock_apply.side_effect = DotzTemplateError("Template not found")
            
            with pytest.raises(DotzProfileError):
                templates.switch_profile("broken")