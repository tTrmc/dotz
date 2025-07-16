"""Tests for the initialization widget."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QLineEdit, QMessageBox, QPushButton, QTextEdit

from dotz.gui.widgets.init import InitWidget, InitWorker


@pytest.mark.gui
class TestInitWorker:
    """Test the initialization worker thread."""

    def test_worker_initialization(self, qapp):
        """Test worker thread initialization."""
        worker = InitWorker()
        assert isinstance(worker, QThread)
        assert worker.remote_url == ""

        worker_with_remote = InitWorker("https://github.com/user/dotfiles.git")
        assert worker_with_remote.remote_url == "https://github.com/user/dotfiles.git"

    def test_worker_successful_init(self, qapp, mock_core_functions):
        """Test worker with successful initialization."""
        with patch("dotz.gui.widgets.init.init_repo", return_value=True) as mock_init:
            worker = InitWorker()

            # Mock the finished signal
            finished_calls = []
            worker.finished.connect(
                lambda success, msg: finished_calls.append((success, msg))
            )

            # Run the worker
            worker.run()

            # Check that finished signal was emitted with success
            assert len(finished_calls) == 1
            success, message = finished_calls[0]
            assert success is True
            assert "successfully" in message.lower()

    def test_worker_already_initialized(self, qapp, mock_core_functions):
        """Test worker when dotz is already initialized."""
        with patch("dotz.gui.widgets.init.init_repo", return_value=False) as mock_init:
            worker = InitWorker()

            finished_calls = []
            worker.finished.connect(
                lambda success, msg: finished_calls.append((success, msg))
            )

            worker.run()

            # Check that finished signal was emitted with failure
            assert len(finished_calls) == 1
            success, message = finished_calls[0]
            assert success is False
            assert "already initialized" in message.lower()

    def test_worker_init_error(self, qapp, mock_core_functions):
        """Test worker with initialization error."""
        with patch(
            "dotz.gui.widgets.init.init_repo", side_effect=Exception("Init failed")
        ) as mock_init:
            worker = InitWorker()

            finished_calls = []
            worker.finished.connect(
                lambda success, msg: finished_calls.append((success, msg))
            )

            worker.run()

            # Check that finished signal was emitted with error
            assert len(finished_calls) == 1
            success, message = finished_calls[0]
            assert success is False
            assert "error" in message.lower()
            assert "Init failed" in message

    def test_worker_with_remote_url(self, qapp, mock_core_functions):
        """Test worker with remote URL."""
        with patch("dotz.gui.widgets.init.init_repo", return_value=True) as mock_init:
            remote_url = "https://github.com/user/dotfiles.git"
            worker = InitWorker(remote_url)

            finished_calls = []
            worker.finished.connect(
                lambda success, msg: finished_calls.append((success, msg))
            )

            worker.run()

            # Check that init_repo was called with remote parameter
            mock_init.assert_called_once_with(remote=remote_url, quiet=True)


@pytest.mark.gui
class TestInitWidget:
    """Test the initialization widget."""

    def test_widget_initialization(self, qapp, mock_core_functions):
        """Test that the init widget initializes correctly."""
        widget = InitWidget()

        # Check that essential UI components exist
        assert widget.remote_input is not None
        assert widget.init_button is not None
        assert widget.status_text is not None

        assert isinstance(widget.remote_input, QLineEdit)
        assert isinstance(widget.init_button, QPushButton)
        assert isinstance(widget.status_text, QTextEdit)

    def test_ui_components_properties(self, qapp, mock_core_functions):
        """Test UI component properties."""
        widget = InitWidget()

        # Check button text
        assert "Initialize" in widget.init_button.text()

        # Check that status text is read-only
        assert widget.status_text.isReadOnly() is True

        # Check remote input placeholder
        assert widget.remote_input.placeholderText() != ""

    def test_initialize_without_remote(self, qapp, mock_core_functions):
        """Test initialization without remote URL."""
        widget = InitWidget()

        # Clear remote input
        widget.remote_input.setText("")

        with patch.object(widget, "_on_init_finished") as mock_finished:
            with patch("dotz.gui.widgets.init.InitWorker") as mock_worker_class:
                mock_worker = Mock()
                mock_worker_class.return_value = mock_worker

                widget._initialize()

                # Check that worker was created with empty remote URL
                mock_worker_class.assert_called_once_with("")
                mock_worker.start.assert_called_once()

                # Check that button is disabled during initialization
                assert widget.init_button.isEnabled() is False
                assert "Initializing" in widget.init_button.text()

    def test_initialize_with_remote(self, qapp, mock_core_functions):
        """Test initialization with remote URL."""
        widget = InitWidget()

        remote_url = "https://github.com/user/dotfiles.git"
        widget.remote_input.setText(remote_url)

        with patch.object(widget, "_on_init_finished") as mock_finished:
            with patch("dotz.gui.widgets.init.InitWorker") as mock_worker_class:
                mock_worker = Mock()
                mock_worker_class.return_value = mock_worker

                widget._initialize()

                # Check that worker was created with remote URL
                mock_worker_class.assert_called_once_with(remote_url)
                mock_worker.start.assert_called_once()

    def test_on_init_finished_success(self, qapp, mock_core_functions):
        """Test handling successful initialization completion."""
        widget = InitWidget()

        # Simulate button being disabled during init
        widget.init_button.setEnabled(False)
        widget.init_button.setText("Initializing...")

        # Mock the initialized signal
        initialized_calls = []
        widget.initialized.connect(lambda: initialized_calls.append(True))

        widget._on_init_finished(True, "Success!")

        # Check that button is re-enabled
        assert widget.init_button.isEnabled() is True
        assert "Initialize" in widget.init_button.text()

        # Check that success message is added to status
        assert "Success!" in widget.status_text.toPlainText()
        assert "✓" in widget.status_text.toPlainText()

        # Check that initialized signal was emitted
        assert len(initialized_calls) == 1

    def test_on_init_finished_failure(self, qapp, mock_core_functions):
        """Test handling failed initialization."""
        widget = InitWidget()

        widget.init_button.setEnabled(False)
        widget.init_button.setText("Initializing...")

        initialized_calls = []
        widget.initialized.connect(lambda: initialized_calls.append(True))

        with patch.object(QMessageBox, "warning") as mock_warning:
            widget._on_init_finished(False, "Failed!")

            # Check that button is re-enabled
            assert widget.init_button.isEnabled() is True
            assert "Initialize" in widget.init_button.text()

            # Check that failure message is added to status
            assert "Failed!" in widget.status_text.toPlainText()

            # Check that warning dialog was shown
            mock_warning.assert_called_once()

            # Check that initialized signal was NOT emitted
            assert len(initialized_calls) == 0

    def test_button_click_triggers_initialize(self, qapp, mock_core_functions):
        """Test that clicking the button triggers initialization."""
        widget = InitWidget()

        with patch.object(widget, "_initialize") as mock_init:
            widget.init_button.click()
            mock_init.assert_called_once()

    def test_remote_input_functionality(self, qapp, mock_core_functions):
        """Test remote input field functionality."""
        widget = InitWidget()

        test_url = "https://github.com/test/repo.git"
        widget.remote_input.setText(test_url)

        assert widget.remote_input.text() == test_url

    def test_status_text_updates(self, qapp, mock_core_functions):
        """Test status text updates during initialization."""
        widget = InitWidget()

        widget.remote_input.setText("https://github.com/user/repo.git")

        with patch("dotz.gui.widgets.init.InitWorker") as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            widget._initialize()

            status_text = widget.status_text.toPlainText()
            assert "Initializing dotz repository" in status_text
            assert "github.com/user/repo.git" in status_text

    def test_widget_signal_emission(self, qapp, mock_core_functions):
        """Test that the widget emits signals correctly."""
        widget = InitWidget()

        # Test initialized signal exists
        assert hasattr(widget, "initialized")

        # Test signal connection
        signal_received = []
        widget.initialized.connect(lambda: signal_received.append(True))

        # Trigger signal manually
        widget.initialized.emit()
        assert len(signal_received) == 1

    def test_worker_cleanup(self, qapp, mock_core_functions):
        """Test that worker is properly managed."""
        widget = InitWidget()

        with patch("dotz.gui.widgets.init.InitWorker") as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            widget._initialize()

            # Check that worker is stored as instance variable
            assert hasattr(widget, "worker")
            assert widget.worker == mock_worker

            # Check that worker's finished signal is connected
            mock_worker.finished.connect.assert_called_once_with(
                widget._on_init_finished
            )

    def test_multiple_initialization_attempts(self, qapp, mock_core_functions):
        """Test behavior with multiple initialization attempts."""
        widget = InitWidget()

        with patch("dotz.gui.widgets.init.InitWorker") as mock_worker_class:
            mock_worker1 = Mock()
            mock_worker2 = Mock()
            mock_worker_class.side_effect = [mock_worker1, mock_worker2]

            # First initialization
            widget._initialize()
            assert widget.init_button.isEnabled() is False

            # Second initialization (button should be disabled)
            # In real implementation, this might be prevented
            widget._initialize()

            # Both workers should be created
            assert mock_worker_class.call_count == 2
