"""Initialization widget for setting up dotz."""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core import init_repo


class InitWorker(QThread):
    """Worker thread for dotz initialization."""

    finished = Signal(bool, str)  # success, message

    def __init__(self, remote_url: str = ""):
        super().__init__()
        self.remote_url = remote_url

    def run(self) -> None:
        """Run the initialization process."""
        try:
            success = init_repo(remote=self.remote_url, quiet=True)
            if success:
                self.finished.emit(True, "Dotz initialized successfully!")
            else:
                self.finished.emit(False, "Dotz is already initialized.")
        except Exception as e:
            self.finished.emit(False, f"Error initializing dotz: {str(e)}")


class InitWidget(QWidget):
    """Widget for initializing dotz repository."""

    initialized = Signal()  # Emitted when dotz is successfully initialized

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>Welcome to Dotz</h2>")
        title.setWordWrap(True)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Dotz is not initialized yet. Click the button below to set up "
            "your dotfiles repository."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Remote URL group
        remote_group = QGroupBox("Remote Repository (Optional)")
        remote_layout = QVBoxLayout(remote_group)

        remote_desc = QLabel(
            "You can optionally specify a remote Git repository URL to sync "
            "your dotfiles with a remote server."
        )
        remote_desc.setWordWrap(True)
        remote_layout.addWidget(remote_desc)

        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("https://github.com/username/dotfiles.git")
        remote_layout.addWidget(self.remote_input)

        layout.addWidget(remote_group)

        # Initialize button
        button_layout = QHBoxLayout()
        self.init_button = QPushButton("Initialize Dotz Repository")
        self.init_button.clicked.connect(self._initialize)
        button_layout.addWidget(self.init_button)

        layout.addLayout(button_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        layout.addStretch()

    def _initialize(self) -> None:
        """Initialize the dotz repository."""
        self.init_button.setEnabled(False)
        self.init_button.setText("Initializing...")

        remote_url = self.remote_input.text().strip()

        # Start initialization in a separate thread
        self.worker = InitWorker(remote_url)
        self.worker.finished.connect(self._on_init_finished)
        self.worker.start()

        self.status_text.append("Initializing dotz repository...")
        if remote_url:
            self.status_text.append(f"Remote URL: {remote_url}")

    def _on_init_finished(self, success: bool, message: str) -> None:
        """Handle initialization completion."""
        self.init_button.setEnabled(True)
        self.init_button.setText("Initialize Dotz Repository")

        self.status_text.append(message)

        if success:
            self.status_text.append("✓ Initialization completed successfully!")
            # Emit signal to notify main window
            self.initialized.emit()
        else:
            QMessageBox.warning(self, "Initialization Failed", message)
