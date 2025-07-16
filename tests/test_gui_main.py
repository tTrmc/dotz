"""Tests for the main GUI window."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTabWidget

from dotz.gui.main import DotzMainWindow


@pytest.mark.gui
class TestDotzMainWindow:
    """Test the main GUI window."""

    def test_window_initialization(self, qapp, mock_core_functions):
        """Test that the main window initializes correctly."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            assert window.windowTitle() == "Dotz - Dotfiles Manager"
            assert window.minimumSize().width() == 1000
            assert window.minimumSize().height() == 700
            assert window.dotz_initialized is True

    def test_window_initialization_not_initialized(self, qapp, mock_core_functions):
        """Test window when dotz is not initialized."""
        with patch(
            "dotz.gui.main.ensure_repo", side_effect=Exception("Not initialized")
        ):
            window = DotzMainWindow()

            assert window.dotz_initialized is False

    def test_ui_components_exist(self, qapp, mock_core_functions):
        """Test that all main UI components are created."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            # Check that central widget exists and is a tab widget
            central_widget = window.centralWidget()
            assert central_widget is not None

            # Find the tab widget
            tab_widget = window.findChild(QTabWidget)
            assert tab_widget is not None

            # Check that tabs are created
            assert tab_widget.count() >= 3  # Dashboard, Files, Settings tabs

    def test_menubar_creation(self, qapp, mock_core_functions):
        """Test that menubar is created with expected menus."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            menubar = window.menuBar()
            assert menubar is not None

            # Check for expected menus
            menu_titles = [action.text() for action in menubar.actions()]
            assert any("File" in title for title in menu_titles)

    def test_toolbar_creation(self, qapp, mock_core_functions):
        """Test that toolbar is created."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            toolbars = window.findChildren(type(window.addToolBar("test")))
            assert len(toolbars) > 0

    def test_statusbar_creation(self, qapp, mock_core_functions):
        """Test that statusbar is created."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            statusbar = window.statusBar()
            assert statusbar is not None

    def test_show_about_dialog(self, qapp, mock_core_functions):
        """Test showing about dialog."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            # This should not raise an exception
            with patch("PySide6.QtWidgets.QMessageBox.about") as mock_about:
                window._show_about()
                mock_about.assert_called_once()

    def test_close_window(self, qapp, mock_core_functions):
        """Test closing the window."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            window = DotzMainWindow()

            # This should not raise an exception
            window.close()

    def test_init_widget_shown_when_not_initialized(self, qapp, mock_core_functions):
        """Test that initialization widget is shown when dotz is not initialized."""
        with patch(
            "dotz.gui.main.ensure_repo", side_effect=Exception("Not initialized")
        ):
            window = DotzMainWindow()

            # The window should show not initialized state
            assert window.dotz_initialized is False

            # The central widget should exist
            assert window.centralWidget() is not None

    @patch("dotz.gui.main.ensure_repo", return_value=True)
    def test_window_can_be_closed(
        self, mock_ensure_repo, qapp, mock_core_functions, no_show
    ):
        """Test that the window can be closed properly."""
        window = DotzMainWindow()

        # Simulate window being shown and then closed
        window.setVisible(True)
        assert window.isVisible()

        # This should not raise an exception
        window.close()
        assert not window.isVisible()

    @patch("dotz.gui.main.ensure_repo", return_value=True)
    def test_refresh_functionality(self, mock_ensure_repo, qapp, mock_core_functions):
        """Test that refresh functionality works."""
        window = DotzMainWindow()

        # Mock the refresh methods of child widgets
        with patch.object(window, "_load_initial_data") as mock_load_data:
            window._refresh()
            mock_load_data.assert_called_once()
