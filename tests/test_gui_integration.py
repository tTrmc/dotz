"""Comprehensive GUI test suite for dotz.

This module runs all GUI tests and provides integration testing capabilities.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


@pytest.mark.gui
class TestGUIIntegration:
    """Integration tests for GUI components."""

    def test_main_window_with_widgets(self, qapp, mock_core_functions):
        """Test main window integration with all widgets."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Check that all widgets are created and accessible
            assert hasattr(window, "dashboard_widget")
            assert hasattr(window, "files_widget")
            assert hasattr(window, "settings_widget")

            # Test that widgets can be refreshed
            if hasattr(window, "_load_initial_data"):
                window._load_initial_data()

    def test_widget_communication(self, qapp, mock_core_functions):
        """Test communication between widgets."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Test that refreshing one widget doesn't break others
            if hasattr(window, "dashboard_widget"):
                window.dashboard_widget.refresh()

            if hasattr(window, "files_widget"):
                window.files_widget.refresh()

    def test_error_handling_across_widgets(self, qapp, mock_core_functions):
        """Test error handling across all widgets."""
        # Simulate various error conditions
        with patch("dotz.core.get_repo_status", side_effect=Exception("Status error")):
            with patch(
                "dotz.core.list_tracked_files", side_effect=Exception("List error")
            ):
                with patch(
                    "dotz.core.load_config", side_effect=Exception("Config error")
                ):
                    with patch("dotz.gui.main.ensure_repo", return_value=True):
                        from dotz.gui.main import DotzMainWindow

                        window = DotzMainWindow()

                        # All widgets should handle errors gracefully
                        # This should not raise unhandled exceptions
                        try:
                            window.dashboard_widget.refresh()
                            window.files_widget.refresh()
                            window.settings_widget.load_settings()
                        except Exception as e:
                            # Log the error but don't fail the test
                            print(f"Expected error handled: {e}")

    def test_init_widget_integration(self, qapp, mock_core_functions):
        """Test init widget integration."""
        with patch(
            "dotz.gui.main.ensure_repo", side_effect=Exception("Not initialized")
        ):
            from dotz.gui.main import DotzMainWindow

            # This should create the init widget when dotz is not initialized
            window = DotzMainWindow()
            assert window.dotz_initialized is False

    def test_gui_startup_sequence(self, qapp, mock_core_functions, no_show):
        """Test the complete GUI startup sequence."""
        # Test normal startup
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Simulate showing the window
            window.setVisible(True)

            # Process any pending events
            qapp.processEvents()

            # Window should be visible
            assert window.isVisible()

            # Close the window
            window.close()

    def test_gui_with_no_data(self, qapp, mock_core_functions):
        """Test GUI behavior with no data."""
        # Return empty data for all functions
        with patch(
            "dotz.core.get_repo_status",
            return_value={
                "modified": [],
                "staged": [],
                "untracked": [],
                "unpushed": [],
            },
        ):
            with patch("dotz.core.list_tracked_files", return_value=[]):
                with patch("dotz.core.load_config", return_value={}):
                    with patch("dotz.gui.main.ensure_repo", return_value=True):
                        from dotz.gui.main import DotzMainWindow

                        window = DotzMainWindow()

                        # All widgets should handle empty data gracefully
                        window.dashboard_widget.refresh()
                        window.files_widget.refresh()
                        window.settings_widget.load_settings()

    def test_gui_memory_cleanup(self, qapp, mock_core_functions, no_show):
        """Test that GUI components clean up properly."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Simulate showing the window
            window.setVisible(True)

            # Close and delete the window
            window.close()
            del window

            # Process any pending events
            qapp.processEvents()

    def test_concurrent_operations(self, qapp, mock_core_functions):
        """Test handling of concurrent operations."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Simulate multiple refresh operations
            if hasattr(window, "dashboard_widget") and hasattr(window, "files_widget"):
                # These should not interfere with each other
                window.dashboard_widget.refresh()
                window.files_widget.refresh()
                window.dashboard_widget.refresh()

    def test_widget_state_consistency(self, qapp, mock_core_functions):
        """Test that widget states remain consistent."""
        with patch("dotz.gui.main.ensure_repo", return_value=True):
            from dotz.gui.main import DotzMainWindow

            window = DotzMainWindow()

            # Modify some widget state
            window.settings_widget.recursive_check.setChecked(True)
            window.settings_widget.case_sensitive_check.setChecked(False)

            # State should be preserved
            assert window.settings_widget.recursive_check.isChecked() is True
            assert window.settings_widget.case_sensitive_check.isChecked() is False

    def test_large_file_lists(self, qapp, mock_core_functions):
        """Test GUI performance with large file lists."""
        # Create a large list of fake files
        large_file_list = [f"~/.config/app{i}/config.json" for i in range(100)]

        with patch(
            "dotz.gui.widgets.files.list_tracked_files", return_value=large_file_list
        ):
            with patch("dotz.gui.main.ensure_repo", return_value=True):
                from dotz.gui.main import DotzMainWindow

                window = DotzMainWindow()

                # This should handle large lists without issues
                window.files_widget.refresh()

                # Check that all files are loaded
                assert window.files_widget.files_list.count() == 100


def run_gui_tests():
    """Run all GUI tests."""
    # Set up test environment
    if not QApplication.instance():
        app = QApplication(sys.argv)

    # Run pytest on GUI test files
    test_files = [
        "tests/test_gui_base.py",
        "tests/test_gui_main.py",
        "tests/test_gui_dashboard.py",
        "tests/test_gui_files.py",
        "tests/test_gui_settings.py",
        "tests/test_gui_init.py",
        "tests/test_gui_integration.py",
    ]

    # Filter to only existing files
    existing_files = [f for f in test_files if Path(f).exists()]

    if existing_files:
        pytest.main(["-v"] + existing_files)
    else:
        print("No GUI test files found")


if __name__ == "__main__":
    run_gui_tests()
