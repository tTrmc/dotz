"""Tests for the settings widget."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import (
    QCheckBox,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
)

from dotz.gui.widgets.settings import SettingsWidget


@pytest.mark.gui
class TestSettingsWidget:
    """Test the settings widget."""

    def test_widget_initialization(self, qapp, mock_core_functions):
        """Test that the settings widget initializes correctly."""
        widget = SettingsWidget()

        # Check that essential UI components exist
        assert widget.recursive_check is not None
        assert widget.case_sensitive_check is not None
        assert widget.follow_symlinks_check is not None
        assert isinstance(widget.recursive_check, QCheckBox)
        assert isinstance(widget.case_sensitive_check, QCheckBox)
        assert isinstance(widget.follow_symlinks_check, QCheckBox)

    def test_ui_components_exist(self, qapp, mock_core_functions):
        """Test that all UI components are created."""
        widget = SettingsWidget()

        # Check list widgets
        assert widget.include_list is not None
        assert widget.exclude_list is not None
        assert isinstance(widget.include_list, QListWidget)
        assert isinstance(widget.exclude_list, QListWidget)

        # Check buttons
        assert widget.save_btn is not None
        assert widget.reset_btn is not None
        assert widget.reload_btn is not None
        assert isinstance(widget.save_btn, QPushButton)
        assert isinstance(widget.reset_btn, QPushButton)
        assert isinstance(widget.reload_btn, QPushButton)

        # Check config editor
        assert widget.config_editor is not None
        assert isinstance(widget.config_editor, QTextEdit)

    def test_load_settings_default_config(self, qapp, mock_core_functions):
        """Test loading default settings."""
        mock_config = {
            "search_settings": {
                "recursive": True,
                "case_sensitive": False,
                "follow_symlinks": False,
            },
            "file_patterns": {
                "include": ["*.conf", ".*rc"],
                "exclude": [".git", "__pycache__"],
            },
        }
        with patch("dotz.gui.widgets.settings.load_config", return_value=mock_config):
            widget = SettingsWidget()

            # Check that settings are loaded correctly
            assert widget.recursive_check.isChecked() is True
            assert widget.case_sensitive_check.isChecked() is False
            assert widget.follow_symlinks_check.isChecked() is False

            # Check that patterns are loaded
            assert widget.include_list.count() == 2
            assert widget.exclude_list.count() == 2

    def test_load_settings_empty_config(self, qapp, mock_core_functions):
        """Test loading with empty config."""
        with patch("dotz.gui.widgets.settings.load_config", return_value={}):
            widget = SettingsWidget()

            # Should have default values
            assert (
                widget.recursive_check.isChecked() is True
            )  # Default is True for recursive
            assert widget.case_sensitive_check.isChecked() is False
            assert widget.follow_symlinks_check.isChecked() is False

    def test_save_settings(self, qapp, mock_core_functions):
        """Test saving settings."""
        widget = SettingsWidget()

        # Modify some settings
        widget.recursive_check.setChecked(True)
        widget.case_sensitive_check.setChecked(False)
        widget.config_editor.setPlainText('{"test": "value"}')

        with patch("dotz.gui.widgets.settings.set_config_value") as mock_set_config:
            with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
                widget._save_settings()

                # Should call set_config_value for each setting
                assert mock_set_config.call_count >= 3
                mock_info.assert_called_once()

    def test_save_settings_invalid_json(self, qapp, mock_core_functions):
        """Test saving with invalid JSON in config editor."""
        widget = SettingsWidget()

        # Set invalid JSON
        widget.config_editor.setPlainText('{"invalid": json}')

        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
            widget._save_settings()

            # Should show warning about invalid JSON
            mock_warning.assert_called_once()

    def test_reset_to_defaults(self, qapp, mock_core_functions):
        """Test resetting settings to defaults."""
        widget = SettingsWidget()

        # Change some settings
        widget.recursive_check.setChecked(False)
        widget.case_sensitive_check.setChecked(True)

        with patch("dotz.gui.widgets.settings.reset_config") as mock_reset:
            with patch(
                "PySide6.QtWidgets.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
                    widget._reset_settings()

                    # Should reset config and show success message
                    mock_reset.assert_called_once()
                    mock_info.assert_called_once()

    def test_reset_cancelled(self, qapp, mock_core_functions):
        """Test reset when user cancels."""
        widget = SettingsWidget()

        with patch("dotz.gui.widgets.settings.reset_config") as mock_reset:
            with patch(
                "PySide6.QtWidgets.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ):
                widget._reset_settings()

                # Should not reset when cancelled
                mock_reset.assert_not_called()

    def test_add_include_pattern(self, qapp, mock_core_functions):
        """Test adding include pattern."""
        widget = SettingsWidget()

        with patch("dotz.gui.widgets.settings.add_file_pattern") as mock_add:
            with patch.object(
                widget, "_get_pattern_input", return_value=("*.log", True)
            ):
                with patch.object(widget, "load_settings") as mock_load:
                    widget._add_include_pattern()

                    mock_add.assert_called_once_with("*.log", "include", quiet=True)
                    mock_load.assert_called_once()

    def test_add_exclude_pattern(self, qapp, mock_core_functions):
        """Test adding exclude pattern."""
        widget = SettingsWidget()

        with patch("dotz.gui.widgets.settings.add_file_pattern") as mock_add:
            with patch.object(
                widget, "_get_pattern_input", return_value=("*.tmp", True)
            ):
                with patch.object(widget, "load_settings") as mock_load:
                    widget._add_exclude_pattern()

                    mock_add.assert_called_once_with("*.tmp", "exclude", quiet=True)
                    mock_load.assert_called_once()

    def test_remove_include_pattern(self, qapp, mock_core_functions):
        """Test removing include pattern."""
        widget = SettingsWidget()

        # Clear the list and add our test item
        widget.include_list.clear()
        widget.include_list.addItem("*.log")
        widget.include_list.setCurrentRow(0)

        with patch("dotz.gui.widgets.settings.remove_file_pattern") as mock_remove:
            with patch.object(widget, "load_settings") as mock_load:
                widget._remove_include_pattern()

                mock_remove.assert_called_once_with("*.log", "include", quiet=True)
                mock_load.assert_called_once()

    def test_remove_exclude_pattern(self, qapp, mock_core_functions):
        """Test removing exclude pattern."""
        widget = SettingsWidget()

        # Add an item and select it
        widget.exclude_list.addItem("*.tmp")
        widget.exclude_list.setCurrentRow(
            widget.exclude_list.count() - 1
        )  # Select the last item (our added item)

        with patch("dotz.gui.widgets.settings.remove_file_pattern") as mock_remove:
            with patch.object(widget, "load_settings") as mock_load:
                widget._remove_exclude_pattern()

                mock_remove.assert_called_once_with("*.tmp", "exclude", quiet=True)
                mock_load.assert_called_once()

    def test_remove_pattern_no_selection(self, qapp, mock_core_functions):
        """Test removing pattern with no selection."""
        widget = SettingsWidget()

        with patch("dotz.gui.widgets.settings.remove_file_pattern") as mock_remove:
            # Don't select anything
            widget._remove_include_pattern()
            widget._remove_exclude_pattern()

            # Should not call remove_file_pattern when nothing is selected
            mock_remove.assert_not_called()

    def test_get_pattern_input(self, qapp, mock_core_functions):
        """Test getting pattern input from user."""
        widget = SettingsWidget()

        with patch(
            "PySide6.QtWidgets.QInputDialog.getText", return_value=("*.conf", True)
        ):
            pattern, ok = widget._get_pattern_input("Test Title")

            assert pattern == "*.conf"
            assert ok is True

    def test_config_error_handling(self, qapp, mock_core_functions):
        """Test error handling in config operations."""
        with patch(
            "dotz.gui.widgets.settings.load_config",
            side_effect=Exception("Config error"),
        ):
            with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_error:
                widget = SettingsWidget()
                # Widget should handle the error gracefully
            widget.load_settings()

            # Should show error message
            mock_error.assert_called()

    def test_save_error_handling(self, qapp, mock_core_functions):
        """Test error handling when saving config."""
        widget = SettingsWidget()

        with patch(
            "dotz.gui.widgets.settings.set_config_value",
            side_effect=Exception("Save error"),
        ):
            with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_error:
                widget._save_settings()

                # Should show error message
                mock_error.assert_called_once()

    def test_pattern_operation_error_handling(self, qapp, mock_core_functions):
        """Test error handling in pattern operations."""
        widget = SettingsWidget()

        with patch(
            "dotz.gui.widgets.settings.add_file_pattern",
            side_effect=Exception("Pattern error"),
        ):
            with patch.object(
                widget, "_get_pattern_input", return_value=("*.log", True)
            ):
                with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_error:
                    widget._add_include_pattern()

                    # Should show error message
                    mock_error.assert_called_once()

    def test_checkbox_toggle_behavior(self, qapp, mock_core_functions):
        """Test checkbox toggle behavior."""
        widget = SettingsWidget()

        # Test toggling checkboxes
        initial_recursive = widget.recursive_check.isChecked()
        widget.recursive_check.toggle()
        assert widget.recursive_check.isChecked() != initial_recursive

        initial_case_sensitive = widget.case_sensitive_check.isChecked()
        widget.case_sensitive_check.toggle()
        assert widget.case_sensitive_check.isChecked() != initial_case_sensitive

        initial_follow_symlinks = widget.follow_symlinks_check.isChecked()
        widget.follow_symlinks_check.toggle()
        assert widget.follow_symlinks_check.isChecked() != initial_follow_symlinks

    def test_config_editor_functionality(self, qapp, mock_core_functions):
        """Test config editor functionality."""
        widget = SettingsWidget()

        # Test setting and getting text
        test_config = '{"test": "value"}'
        widget.config_editor.setPlainText(test_config)
        assert widget.config_editor.toPlainText() == test_config

    def test_button_click_functionality(self, qapp, mock_core_functions):
        """Test that buttons trigger correct actions."""
        widget = SettingsWidget()

        # Test save button
        with patch.object(widget, "_save_settings") as mock_save:
            widget.save_btn.click()
            mock_save.assert_called_once()

        # Test reset button
        with patch.object(widget, "_reset_settings") as mock_reset:
            widget.reset_btn.click()
            mock_reset.assert_called_once()

        # Test reload button
        with patch.object(widget, "load_settings") as mock_load:
            widget.reload_btn.click()
            mock_load.assert_called_once()
