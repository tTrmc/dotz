"""Tests for template and profile CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from dotz import cli
from tests.conftest import create_test_files


class TestTemplateCLI:
    """Test template CLI commands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.templates.create_template")
    def test_template_create_command(self, mock_create: Mock, temp_home: Path) -> None:
        """Test template create command."""
        mock_create.return_value = True

        result = self.runner.invoke(
            cli.app,
            ["template", "create", "test-template", "--description", "Test template"],
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            name="test-template", description="Test template", files=None, quiet=False
        )

    @patch("dotz.templates.create_template")
    def test_template_create_with_files(
        self, mock_create: Mock, temp_home: Path
    ) -> None:
        """Test template create command with specific files."""
        mock_create.return_value = True

        result = self.runner.invoke(
            cli.app,
            [
                "template",
                "create",
                "test-template",
                "--file",
                ".bashrc",
                "--file",
                ".vimrc",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            name="test-template",
            description="",
            files=[".bashrc", ".vimrc"],
            quiet=True,
        )

    @patch("dotz.templates.create_template")
    def test_template_create_failure(self, mock_create: Mock, temp_home: Path) -> None:
        """Test template create command failure."""
        mock_create.return_value = False

        result = self.runner.invoke(cli.app, ["template", "create", "test-template"])

        assert result.exit_code == 1

    @patch("dotz.templates.list_templates")
    def test_template_list_command(self, mock_list: Mock, temp_home: Path) -> None:
        """Test template list command."""
        mock_templates = [
            {
                "name": "template1",
                "description": "First template",
                "created": "2025-01-01T12:00:00",
                "file_count": 5,
            },
            {
                "name": "template2",
                "description": "Second template",
                "created": "2025-01-02T12:00:00",
                "file_count": 3,
            },
        ]
        mock_list.return_value = mock_templates

        result = self.runner.invoke(cli.app, ["template", "list"])

        assert result.exit_code == 0
        assert "template1" in result.output
        assert "template2" in result.output
        assert "First template" in result.output

    @patch("dotz.templates.list_templates")
    def test_template_list_verbose(self, mock_list: Mock, temp_home: Path) -> None:
        """Test template list command with verbose output."""
        mock_templates = [
            {
                "name": "template1",
                "description": "First template",
                "created": "2025-01-01T12:00:00",
                "file_count": 5,
            }
        ]
        mock_list.return_value = mock_templates

        with patch("dotz.templates.get_template_info") as mock_info:
            mock_info.return_value = {"total_size": 1024}

            result = self.runner.invoke(cli.app, ["template", "list", "--verbose"])

            assert result.exit_code == 0
            assert "1.0 KB" in result.output

    @patch("dotz.templates.list_templates")
    def test_template_list_empty(self, mock_list: Mock, temp_home: Path) -> None:
        """Test template list command when no templates exist."""
        mock_list.return_value = []

        result = self.runner.invoke(cli.app, ["template", "list"])

        assert result.exit_code == 0
        assert "No templates found" in result.output

    @patch("dotz.templates.apply_template")
    def test_template_apply_command(self, mock_apply: Mock, temp_home: Path) -> None:
        """Test template apply command."""
        mock_apply.return_value = True

        result = self.runner.invoke(cli.app, ["template", "apply", "test-template"])

        assert result.exit_code == 0
        mock_apply.assert_called_once_with(
            name="test-template", merge=False, backup=True, quiet=False
        )

    @patch("dotz.templates.apply_template")
    def test_template_apply_merge_mode(self, mock_apply: Mock, temp_home: Path) -> None:
        """Test template apply command with merge mode."""
        mock_apply.return_value = True

        result = self.runner.invoke(
            cli.app, ["template", "apply", "test-template", "--merge", "--no-backup"]
        )

        assert result.exit_code == 0
        mock_apply.assert_called_once_with(
            name="test-template", merge=True, backup=False, quiet=False
        )

    @patch("dotz.templates.delete_template")
    def test_template_delete_command(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test template delete command."""
        mock_delete.return_value = True

        result = self.runner.invoke(
            cli.app, ["template", "delete", "test-template", "--yes"]
        )

        assert result.exit_code == 0
        mock_delete.assert_called_once_with(name="test-template", quiet=False)

    @patch("dotz.templates.export_template")
    def test_template_export_command(self, mock_export: Mock, temp_home: Path) -> None:
        """Test template export command."""
        mock_export.return_value = True

        result = self.runner.invoke(
            cli.app,
            ["template", "export", "test-template", "--output", "export.tar.gz"],
        )

        assert result.exit_code == 0
        mock_export.assert_called_once_with(
            name="test-template", output_path="export.tar.gz", quiet=False
        )

    @patch("dotz.templates.import_template")
    def test_template_import_command(self, mock_import: Mock, temp_home: Path) -> None:
        """Test template import command."""
        mock_import.return_value = True

        result = self.runner.invoke(cli.app, ["template", "import", "import.tar.gz"])

        assert result.exit_code == 0
        mock_import.assert_called_once_with(archive_path="import.tar.gz", quiet=False)

    @patch("dotz.templates.get_template_info")
    def test_template_info_command(self, mock_info: Mock, temp_home: Path) -> None:
        """Test template info command."""
        mock_info.return_value = {
            "name": "test-template",
            "description": "Test template",
            "created": "2025-01-01T12:00:00",
            "file_count": 5,
            "total_size": 2048,
            "version": "1.0",
            "files": [".bashrc", ".vimrc", ".gitconfig"],
        }

        result = self.runner.invoke(cli.app, ["template", "info", "test-template"])

        assert result.exit_code == 0
        assert "test-template" in result.output
        assert "Test template" in result.output
        assert "2.0 KB" in result.output
        assert ".bashrc" in result.output

    @patch("dotz.templates.get_template_info")
    def test_template_info_not_found(self, mock_info: Mock, temp_home: Path) -> None:
        """Test template info command for non-existent template."""
        mock_info.return_value = None

        result = self.runner.invoke(cli.app, ["template", "info", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_template_help_command(self, temp_home: Path) -> None:
        """Test template help command."""
        result = self.runner.invoke(cli.app, ["template", "help"])

        assert result.exit_code == 0
        assert "Template Management Help" in result.output
        assert "Templates:" in result.output
        assert "Use Cases:" in result.output


class TestProfileCLI:
    """Test profile CLI commands."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("dotz.templates.create_profile")
    def test_profile_create_command(self, mock_create: Mock, temp_home: Path) -> None:
        """Test profile create command."""
        mock_create.return_value = True

        result = self.runner.invoke(
            cli.app,
            [
                "profile",
                "create",
                "work",
                "--description",
                "Work environment",
                "--env",
                "work",
            ],
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            name="work",
            description="Work environment",
            environment="work",
            copy_from=None,
            quiet=False,
        )

    @patch("dotz.templates.create_profile")
    def test_profile_create_copy_from(self, mock_create: Mock, temp_home: Path) -> None:
        """Test profile create command with copy-from option."""
        mock_create.return_value = True

        result = self.runner.invoke(
            cli.app, ["profile", "create", "personal", "--copy-from", "work"]
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            name="personal",
            description="",
            environment="",
            copy_from="work",
            quiet=False,
        )

    @patch("dotz.templates.list_profiles")
    def test_profile_list_command(self, mock_list: Mock, temp_home: Path) -> None:
        """Test profile list command."""
        mock_profiles = [
            {
                "name": "work",
                "description": "Work environment",
                "environment": "work",
                "created": "2025-01-01T12:00:00",
                "last_used": "2025-01-02T12:00:00",
                "active": True,
            },
            {
                "name": "personal",
                "description": "Personal setup",
                "environment": "personal",
                "created": "2025-01-01T12:00:00",
                "last_used": "never",
                "active": False,
            },
        ]
        mock_list.return_value = mock_profiles

        result = self.runner.invoke(cli.app, ["profile", "list"])

        assert result.exit_code == 0
        assert "work" in result.output
        assert "personal" in result.output
        assert "●" in result.output  # Active indicator

    @patch("dotz.templates.list_profiles")
    def test_profile_list_verbose(self, mock_list: Mock, temp_home: Path) -> None:
        """Test profile list command with verbose output."""
        mock_profiles = [
            {
                "name": "work",
                "description": "Work environment",
                "environment": "work",
                "created": "2025-01-01T12:00:00",
                "last_used": "2025-01-02T12:00:00",
                "active": True,
            }
        ]
        mock_list.return_value = mock_profiles

        with patch("dotz.templates.get_profile_info") as mock_info:
            mock_info.return_value = {"file_count": 10, "total_size": 4096}

            result = self.runner.invoke(cli.app, ["profile", "list", "--verbose"])

            assert result.exit_code == 0
            assert "ACTIVE" in result.output
            assert "4.0 KB" in result.output

    @patch("dotz.templates.list_profiles")
    def test_profile_list_empty(self, mock_list: Mock, temp_home: Path) -> None:
        """Test profile list command when no profiles exist."""
        mock_list.return_value = []

        result = self.runner.invoke(cli.app, ["profile", "list"])

        assert result.exit_code == 0
        assert "No profiles found" in result.output

    @patch("dotz.templates.get_active_profile")
    @patch("dotz.templates.switch_profile")
    def test_profile_switch_command(
        self, mock_switch: Mock, mock_active: Mock, temp_home: Path
    ) -> None:
        """Test profile switch command."""
        mock_active.return_value = "current"
        mock_switch.return_value = True

        result = self.runner.invoke(cli.app, ["profile", "switch", "work", "--yes"])

        assert result.exit_code == 0
        mock_switch.assert_called_once_with(name="work", backup=True, quiet=False)

    @patch("dotz.templates.get_active_profile")
    def test_profile_switch_already_active(
        self, mock_active: Mock, temp_home: Path
    ) -> None:
        """Test profile switch when already using the target profile."""
        mock_active.return_value = "work"

        result = self.runner.invoke(cli.app, ["profile", "switch", "work"])

        assert result.exit_code == 0
        assert "Already using profile" in result.output

    @patch("dotz.templates.delete_profile")
    def test_profile_delete_command(self, mock_delete: Mock, temp_home: Path) -> None:
        """Test profile delete command."""
        mock_delete.return_value = True

        result = self.runner.invoke(cli.app, ["profile", "delete", "work", "--yes"])

        assert result.exit_code == 0
        mock_delete.assert_called_once_with(name="work", quiet=False)

    @patch("dotz.templates.get_active_profile")
    @patch("dotz.templates.get_profile_info")
    def test_profile_current_command(
        self, mock_info: Mock, mock_active: Mock, temp_home: Path
    ) -> None:
        """Test profile current command."""
        mock_active.return_value = "work"
        mock_info.return_value = {
            "name": "work",
            "description": "Work environment",
            "environment": "work",
            "last_used": "2025-01-02T12:00:00",
            "file_count": 5,
        }

        result = self.runner.invoke(cli.app, ["profile", "current"])

        assert result.exit_code == 0
        assert "Active profile: work" in result.output
        assert "Work environment" in result.output

    @patch("dotz.templates.get_active_profile")
    def test_profile_current_none_active(
        self, mock_active: Mock, temp_home: Path
    ) -> None:
        """Test profile current command when no profile is active."""
        mock_active.return_value = None

        result = self.runner.invoke(cli.app, ["profile", "current"])

        assert result.exit_code == 0
        assert "No active profile" in result.output

    @patch("dotz.templates.get_profile_info")
    def test_profile_info_command(self, mock_info: Mock, temp_home: Path) -> None:
        """Test profile info command."""
        mock_info.return_value = {
            "name": "work",
            "description": "Work environment",
            "environment": "work",
            "created": "2025-01-01T12:00:00",
            "last_used": "2025-01-02T12:00:00",
            "file_count": 10,
            "total_size": 8192,
            "version": "1.0",
            "active": True,
        }

        result = self.runner.invoke(cli.app, ["profile", "info", "work"])

        assert result.exit_code == 0
        assert "Profile: work" in result.output
        assert "ACTIVE" in result.output
        assert "8.0 KB" in result.output

    @patch("dotz.templates.get_profile_info")
    def test_profile_info_not_found(self, mock_info: Mock, temp_home: Path) -> None:
        """Test profile info command for non-existent profile."""
        mock_info.return_value = None

        result = self.runner.invoke(cli.app, ["profile", "info", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_profile_help_command(self, temp_home: Path) -> None:
        """Test profile help command."""
        result = self.runner.invoke(cli.app, ["profile", "help"])

        assert result.exit_code == 0
        assert "Profile Management Help" in result.output
        assert "Profiles:" in result.output
        assert "Use Cases:" in result.output


class TestCLIIntegration:
    """Test integration between CLI and template/profile systems."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    def test_full_template_workflow(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test complete template workflow through CLI."""
        # This would require actual file operations
        # For now, we'll test the command structure
        result = self.runner.invoke(cli.app, ["template", "--help"])
        assert result.exit_code == 0
        assert "Manage dotfile templates" in result.output

    def test_full_profile_workflow(
        self, initialized_dotz: Path, temp_home: Path
    ) -> None:
        """Test complete profile workflow through CLI."""
        # This would require actual file operations
        # For now, we'll test the command structure
        result = self.runner.invoke(cli.app, ["profile", "--help"])
        assert result.exit_code == 0
        assert "Manage dotfile profiles" in result.output

    def test_help_commands_exist(self, temp_home: Path) -> None:
        """Test that help commands exist and work."""
        # Test template help
        result = self.runner.invoke(cli.app, ["template", "help"])
        assert result.exit_code == 0

        # Test profile help
        result = self.runner.invoke(cli.app, ["profile", "help"])
        assert result.exit_code == 0

    def test_subcommands_exist(self, temp_home: Path) -> None:
        """Test that all expected subcommands exist."""
        # Test template subcommands
        result = self.runner.invoke(cli.app, ["template", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output
        assert "apply" in result.output
        assert "delete" in result.output
        assert "export" in result.output
        assert "import" in result.output
        assert "info" in result.output

        # Test profile subcommands
        result = self.runner.invoke(cli.app, ["profile", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output
        assert "switch" in result.output
        assert "current" in result.output
        assert "delete" in result.output
        assert "info" in result.output
