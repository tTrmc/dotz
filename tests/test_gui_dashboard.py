"""Tests for the dashboard widget."""

from unittest.mock import Mock, patch

import pytest

# Try to import PySide6 components, skip if not available
try:
    from PySide6.QtWidgets import QListWidget, QPushButton

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    pytest.skip("PySide6 not available", allow_module_level=True)

from dotz.gui.widgets.dashboard import DashboardWidget


@pytest.mark.gui
class TestDashboardWidget:
    """Test the dashboard widget."""

    def test_widget_initialization(self, qapp, mock_core_functions):
        """Test that the dashboard widget initializes correctly."""
        widget = DashboardWidget()

        # Check that essential UI components exist
        assert widget.status_label is not None
        assert widget.push_btn is not None
        assert widget.pull_btn is not None
        assert widget.refresh_btn is not None
        assert widget.tracked_list is not None
        assert widget.modified_list is not None

    def test_button_connections(self, qapp, mock_core_functions):
        """Test that buttons are properly connected."""
        widget = DashboardWidget()

        # Check that buttons exist and are QPushButton instances
        assert isinstance(widget.push_btn, QPushButton)
        assert isinstance(widget.pull_btn, QPushButton)
        assert isinstance(widget.refresh_btn, QPushButton)

        # Check button text
        assert "Push" in widget.push_btn.text()
        assert "Pull" in widget.pull_btn.text()
        assert "Refresh" in widget.refresh_btn.text()

    def test_list_widgets(self, qapp, mock_core_functions):
        """Test that list widgets are properly created."""
        widget = DashboardWidget()

        assert isinstance(widget.tracked_list, QListWidget)
        assert isinstance(widget.modified_list, QListWidget)

    def test_refresh_with_clean_status(self, qapp, mock_core_functions):
        """Test refresh with clean repository status."""
        with (
            patch("dotz.gui.widgets.dashboard.get_repo_status") as mock_status,
            patch("dotz.gui.widgets.dashboard.list_tracked_files") as mock_files,
        ):

            mock_status.return_value = {
                "modified": [],
                "staged": [],
                "untracked": [],
                "unpushed": [],
            }
            mock_files.return_value = ["~/.bashrc", "~/.vimrc"]

            widget = DashboardWidget()
            widget.refresh()

            # Should show clean status
            assert "clean" in widget.status_label.text().lower()

            # Lists should be populated
            assert widget.tracked_list.count() == 2
            assert widget.modified_list.count() == 0

    def test_refresh_with_modified_files(self, qapp, mock_core_functions):
        """Test refresh with modified files."""
        with (
            patch("dotz.gui.widgets.dashboard.get_repo_status") as mock_status,
            patch("dotz.gui.widgets.dashboard.list_tracked_files") as mock_files,
        ):

            mock_status.return_value = {
                "modified": ["~/.bashrc", "~/.vimrc"],
                "staged": [],
                "untracked": ["~/.profile"],
                "unpushed": [],
            }
            mock_files.return_value = ["~/.bashrc", "~/.vimrc"]

            widget = DashboardWidget()
            widget.refresh()

            # Should show modified status
            status_text = widget.status_label.text().lower()
            assert "2 modified files" in status_text
            assert "1 untracked files" in status_text

            # Modified list should be populated
            assert widget.modified_list.count() == 2

    def test_refresh_with_staged_files(self, qapp, mock_core_functions):
        """Test refresh with staged files."""
        with patch("dotz.gui.widgets.dashboard.get_repo_status") as mock_status:
            mock_status.return_value = {
                "modified": [],
                "staged": ["~/.bashrc"],
                "untracked": [],
                "unpushed": [],
            }

            widget = DashboardWidget()
            widget.refresh()

            # Should show staged status
            assert "1 staged files" in widget.status_label.text()

    def test_refresh_with_unpushed_changes(self, qapp, mock_core_functions):
        """Test refresh with unpushed changes."""
        with patch("dotz.gui.widgets.dashboard.get_repo_status") as mock_status:
            mock_status.return_value = {
                "modified": [],
                "staged": [],
                "untracked": [],
                "unpushed": ["commit1", "commit2"],
            }

            widget = DashboardWidget()
            widget.refresh()

            # Should show unpushed status
            assert "2 unpushed changes" in widget.status_label.text()

    def test_refresh_error_handling(self, qapp, mock_core_functions):
        """Test refresh handles errors gracefully."""
        with patch(
            "dotz.gui.widgets.dashboard.get_repo_status",
            side_effect=Exception("Git error"),
        ):
            widget = DashboardWidget()
            widget.refresh()

            # Should show error status
            assert "error" in widget.status_label.text().lower()

    def test_push_changes_action(self, qapp, mock_core_functions):
        """Test push changes action."""
        widget = DashboardWidget()

        with patch("dotz.core.push_repo") as mock_push:
            mock_push.return_value = True
            widget._push_changes()
            mock_push.assert_called_once()

    def test_pull_changes_action(self, qapp, mock_core_functions):
        """Test pull changes action."""
        widget = DashboardWidget()

        with patch("dotz.core.pull_repo") as mock_pull:
            mock_pull.return_value = True
            widget._pull_changes()
            mock_pull.assert_called_once()

    def test_push_changes_error_handling(self, qapp, mock_core_functions):
        """Test push changes handles errors."""
        widget = DashboardWidget()

        with patch("dotz.core.push_repo", side_effect=Exception("Push failed")):
            # Should not raise exception
            widget._push_changes()

    def test_pull_changes_error_handling(self, qapp, mock_core_functions):
        """Test pull changes handles errors."""
        widget = DashboardWidget()

        with patch("dotz.core.pull_repo", side_effect=Exception("Pull failed")):
            # Should not raise exception
            widget._pull_changes()

    def test_button_click_refresh(self, qapp, mock_core_functions):
        """Test clicking refresh button."""
        widget = DashboardWidget()

        with patch.object(widget, "refresh") as mock_refresh:
            widget.refresh_btn.click()
            mock_refresh.assert_called_once()

    def test_list_widget_selection(self, qapp, mock_core_functions):
        """Test list widget selection functionality."""
        widget = DashboardWidget()

        # Add some items to test selection
        widget.tracked_list.addItem("~/.bashrc")
        widget.tracked_list.addItem("~/.vimrc")

        # Select first item
        widget.tracked_list.setCurrentRow(0)
        selected_items = widget.tracked_list.selectedItems()

        assert len(selected_items) == 1
        assert selected_items[0].text() == "~/.bashrc"
