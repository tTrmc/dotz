"""Tests for GUI components.

This module contains tests for the PySide6-based GUI components of dotz.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Set up headless mode for CI environments
if (
    "CI" in os.environ
    or "GITHUB_ACTIONS" in os.environ
    or "PYTEST_CURRENT_TEST" in os.environ
):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_LOGGING_RULES"] = "*.debug=false"
    # Disable Qt warnings that can cause hangs
    os.environ["QT_ASSUME_STDERR_HAS_CONSOLE"] = "1"

# Ensure QApplication exists for widget testing
if not QApplication.instance():
    app = QApplication(sys.argv)


@pytest.fixture(scope="session")
def qapp():
    """Fixture to provide QApplication instance for testing."""
    # Ensure only one QApplication instance exists for the entire test session
    app = QApplication.instance()
    if app is None:
        # Create QApplication with minimal settings for testing
        app = QApplication(["test"])
        app.setQuitOnLastWindowClosed(
            False
        )  # Prevent app from quitting when windows close

    yield app

    # Clean up at the end of the session
    if app:
        app.processEvents()  # Process any pending events
        # Don't call quit() as it can cause hangs in some environments


@pytest.fixture(autouse=True)
def auto_no_show():
    """Automatically prevent GUI widgets from showing in CI environments."""
    # Check if we're in a CI environment or headless mode
    is_ci = (
        "CI" in os.environ
        or "GITHUB_ACTIONS" in os.environ
        or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    )

    if is_ci:
        # Automatically mock all GUI dialogs and windows
        with (
            patch("PySide6.QtWidgets.QWidget.show") as mock_show,
            patch("PySide6.QtWidgets.QMainWindow.show") as mock_main_show,
            patch("PySide6.QtWidgets.QDialog.exec") as mock_exec,
            patch("PySide6.QtWidgets.QMessageBox.information") as mock_info,
            patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning,
            patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical,
            patch(
                "PySide6.QtWidgets.QMessageBox.question", return_value=1
            ) as mock_question,
        ):  # Return Yes
            # Make exec return immediately with accepted result
            mock_exec.return_value = 1  # QDialog.Accepted
            yield
    else:
        yield


@pytest.fixture
def no_show():
    """Fixture to prevent widgets from actually showing during tests."""
    # Always prevent windows from showing during tests to avoid hangs
    with (
        patch("PySide6.QtWidgets.QWidget.show") as mock_show,
        patch("PySide6.QtWidgets.QMainWindow.show") as mock_main_show,
        patch("PySide6.QtWidgets.QDialog.exec") as mock_exec,
        patch("PySide6.QtWidgets.QMessageBox.information") as mock_info,
        patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning,
        patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical,
        patch(
            "PySide6.QtWidgets.QMessageBox.question", return_value=1
        ) as mock_question,
    ):  # Return Accepted
        # Make exec return immediately with accepted result
        mock_exec.return_value = 1  # QDialog.Accepted
        yield {
            "show": mock_show,
            "main_show": mock_main_show,
            "exec": mock_exec,
            "info": mock_info,
            "warning": mock_warning,
            "critical": mock_critical,
            "question": mock_question,
        }


@pytest.fixture
def mock_core_functions():
    """Mock core functions that GUI widgets depend on."""
    # Create a mock repo object
    mock_repo = Mock()
    mock_repo.untracked_files = []
    mock_repo.index.diff.return_value = []
    mock_repo.git.ls_files.return_value = ""
    mock_repo.active_branch.name = "main"
    mock_repo.remotes = []

    with patch.multiple(
        "dotz.core",
        ensure_repo=Mock(return_value=mock_repo),
        get_repo_status=Mock(
            return_value={"modified": [], "staged": [], "untracked": [], "unpushed": []}
        ),
        list_tracked_files=Mock(return_value=[]),
        add_dotfile=Mock(return_value=True),
        delete_dotfile=Mock(return_value=True),
        restore_dotfile=Mock(return_value=True),
        load_config=Mock(return_value={}),
        save_config=Mock(return_value=True),
        set_config_value=Mock(return_value=True),
        add_file_pattern=Mock(return_value=True),
        remove_file_pattern=Mock(return_value=True),
        reset_config=Mock(return_value=True),
        push_repo=Mock(return_value=True),
        pull_repo=Mock(return_value=True),
    ) as mock_functions:
        yield mock_functions
