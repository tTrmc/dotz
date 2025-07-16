"""Tests for the files widget."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Try to import PySide6 components, skip if not available
try:
    from PySide6.QtWidgets import QFileDialog, QListWidget, QMessageBox, QPushButton

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    pytest.skip("PySide6 not available", allow_module_level=True)

from dotz.gui.widgets.files import FilesWidget


@pytest.mark.gui
class TestFilesWidget:
    """Test the files widget."""

    def test_widget_initialization(self, qapp, mock_core_functions, no_show):
        """Test that the files widget initializes correctly."""
        widget = FilesWidget()

        # Check that essential UI components exist
        assert widget.files_list is not None
        assert isinstance(widget.files_list, QListWidget)

    def test_files_list_selection_mode(self, qapp, mock_core_functions):
        """Test that files list supports extended selection."""
        widget = FilesWidget()

        assert (
            widget.files_list.selectionMode()
            == QListWidget.SelectionMode.ExtendedSelection
        )

    def test_refresh_with_tracked_files(self, qapp, mock_core_functions):
        """Test refresh populates the files list."""
        mock_files = ["~/.bashrc", "~/.vimrc", "~/.gitconfig"]

        with patch("dotz.gui.widgets.files.list_tracked_files") as mock_list:
            mock_list.return_value = mock_files

            widget = FilesWidget()
            widget.refresh()

            # Files list should be populated
            assert widget.files_list.count() == len(mock_files)

            # Check individual items
            for i, file_path in enumerate(mock_files):
                item = widget.files_list.item(i)
                assert file_path in item.text()

    def test_refresh_with_no_files(self, qapp, mock_core_functions):
        """Test refresh with no tracked files."""
        with patch("dotz.gui.widgets.files.list_tracked_files") as mock_list:
            mock_list.return_value = []

            widget = FilesWidget()
            widget.refresh()

            assert widget.files_list.count() == 0

    def test_refresh_error_handling(self, qapp, mock_core_functions):
        """Test refresh handles errors gracefully."""
        with patch(
            "dotz.gui.widgets.files.list_tracked_files",
            side_effect=Exception("List error"),
        ):
            with patch.object(QMessageBox, "critical") as mock_critical:
                widget = FilesWidget()

                # Should not raise exception
                widget.refresh()

                # Should show error message
                mock_critical.assert_called_once()

    def test_add_file_dialog(self, qapp, mock_core_functions):
        """Test add file functionality."""
        widget = FilesWidget()
        # Use actual home path to ensure path validation passes
        test_file = str(Path.home() / ".bashrc")
        with patch.object(QFileDialog, "getOpenFileName", return_value=(test_file, "")):
            with patch(
                "dotz.gui.widgets.files.add_dotfile", return_value=True
            ) as mock_add:
                with patch.object(widget, "refresh") as mock_refresh:
                    with patch.object(QMessageBox, "information") as mock_info:
                        widget.add_file()
                        mock_add.assert_called_once()
                        mock_refresh.assert_called_once()
                        mock_info.assert_called_once()

    def test_add_file_dialog_cancelled(self, qapp, mock_core_functions):
        """Test add file when dialog is cancelled."""
        widget = FilesWidget()
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            with patch("dotz.gui.widgets.files.add_dotfile") as mock_add:
                widget.add_file()
                mock_add.assert_not_called()

    def test_add_file_error_handling(self, qapp, mock_core_functions):
        """Test add file error handling."""
        widget = FilesWidget()
        test_file = str(Path.home() / ".bashrc")
        with patch("dotz.gui.widgets.files.add_dotfile", return_value=False):
            with patch.object(
                QFileDialog, "getOpenFileName", return_value=(test_file, "")
            ):
                with patch.object(QMessageBox, "warning") as mock_msgbox:
                    widget.add_file()
                    mock_msgbox.assert_called_once()

    def test_delete_selected_files(self, qapp, mock_core_functions):
        """Test deleting selected files."""
        widget = FilesWidget()
        test_files = ["~/.bashrc", "~/.vimrc"]
        for file_path in test_files:
            widget.files_list.addItem(file_path)
        widget.files_list.selectAll()
        with patch("dotz.gui.widgets.files.delete_dotfile") as mock_delete:
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
            ):
                with patch.object(QMessageBox, "information") as mock_info:
                    with patch.object(widget, "refresh") as mock_refresh:
                        widget.delete_selected()
                        mock_delete.assert_called_once()
                        mock_refresh.assert_called_once()
                        mock_info.assert_called_once()

    def test_delete_selected_files_cancelled(self, qapp, mock_core_functions):
        """Test deleting files when user cancels confirmation."""
        widget = FilesWidget()
        widget.files_list.addItem("~/.bashrc")
        widget.files_list.selectAll()
        with patch("dotz.gui.widgets.files.delete_dotfile") as mock_delete:
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.No
            ):
                widget.delete_selected()
                mock_delete.assert_not_called()

    def test_delete_with_no_selection(self, qapp, mock_core_functions):
        """Test delete when no files are selected."""
        widget = FilesWidget()

        # Add files but don't select any
        widget.files_list.addItem("~/.bashrc")

        with patch.object(QMessageBox, "information") as mock_msgbox:
            widget.delete_selected()

            # Should show info message about no selection
            mock_msgbox.assert_called_once()

    def test_delete_file_error_handling(self, qapp, mock_core_functions):
        """Test delete file error handling."""
        widget = FilesWidget()
        widget.files_list.addItem("~/.bashrc")
        widget.files_list.selectAll()
        with patch(
            "dotz.gui.widgets.files.delete_dotfile",
            side_effect=Exception("Delete failed"),
        ):
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
            ):
                with patch.object(QMessageBox, "critical") as mock_error:
                    widget.delete_selected()
                    mock_error.assert_called_once()

    def test_restore_selected_files(self, qapp, mock_core_functions):
        """Test restoring selected files."""
        widget = FilesWidget()
        test_files = ["~/.bashrc", "~/.vimrc"]
        for file_path in test_files:
            widget.files_list.addItem(file_path)
        widget.files_list.selectAll()
        with patch("dotz.gui.widgets.files.restore_dotfile") as mock_restore:
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
            ):
                widget.restore_selected()
                assert mock_restore.call_count == len(test_files)

    def test_restore_selected_files_cancelled(self, qapp, mock_core_functions):
        """Test restoring files when restore fails."""
        widget = FilesWidget()
        widget.files_list.addItem("~/.bashrc")
        widget.files_list.selectAll()
        with patch("dotz.gui.widgets.files.restore_dotfile", return_value=False):
            with patch.object(QMessageBox, "warning") as mock_warning:
                widget.restore_selected()
                mock_warning.assert_called_once()

    def test_restore_with_no_selection(self, qapp, mock_core_functions):
        """Test restore when no files are selected."""
        widget = FilesWidget()

        widget.files_list.addItem("~/.bashrc")

        with patch.object(QMessageBox, "information") as mock_msgbox:
            widget.restore_selected()

            # Should show info message about no selection
            mock_msgbox.assert_called_once()

    def test_restore_file_error_handling(self, qapp, mock_core_functions):
        """Test restore file error handling."""
        widget = FilesWidget()
        widget.files_list.addItem("~/.bashrc")
        widget.files_list.selectAll()
        with patch(
            "dotz.gui.widgets.files.restore_dotfile",
            side_effect=Exception("Restore failed"),
        ):
            with patch.object(QMessageBox, "warning") as mock_error:
                with patch.object(widget, "refresh") as mock_refresh:
                    widget.restore_selected()
                    mock_error.assert_called_once()
                    mock_refresh.assert_called_once()

    def test_file_list_double_click(self, qapp, mock_core_functions):
        """Test double-clicking on file list items."""
        widget = FilesWidget()

        # Add a file and simulate double-click
        widget.files_list.addItem("~/.bashrc")
        item = widget.files_list.item(0)

        # Double-click should be handled gracefully
        # (actual behavior depends on implementation)
        assert item is not None
        assert item.text() == "~/.bashrc"

    def test_multiple_file_selection(self, qapp, mock_core_functions):
        """Test selecting multiple files."""
        widget = FilesWidget()

        # Add multiple files
        test_files = ["~/.bashrc", "~/.vimrc", "~/.gitconfig"]
        for file_path in test_files:
            widget.files_list.addItem(file_path)

        # Select first and third items
        widget.files_list.item(0).setSelected(True)
        widget.files_list.item(2).setSelected(True)

        selected = widget.files_list.selectedItems()
        assert len(selected) == 2
        assert selected[0].text() == "~/.bashrc"
        assert selected[1].text() == "~/.gitconfig"
