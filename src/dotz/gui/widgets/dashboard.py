"""Dashboard widget showing dotz status overview."""

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core import get_repo_status, list_tracked_files


class DashboardWidget(QWidget):
    """Main dashboard widget showing repository status."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Left side - Status overview
        left_layout = QVBoxLayout()

        # Repository status group
        status_group = QGroupBox("Repository Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Loading...")
        status_layout.addWidget(self.status_label)

        left_layout.addWidget(status_group)

        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.push_btn = QPushButton("Push Changes")
        self.push_btn.clicked.connect(self._push_changes)
        actions_layout.addWidget(self.push_btn)

        self.pull_btn = QPushButton("Pull Changes")
        self.pull_btn.clicked.connect(self._pull_changes)
        actions_layout.addWidget(self.pull_btn)

        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(self.refresh_btn)

        left_layout.addWidget(actions_group)
        left_layout.addStretch()

        layout.addLayout(left_layout)

        # Right side - File lists
        right_layout = QVBoxLayout()

        # Tracked files
        tracked_group = QGroupBox("Tracked Files")
        tracked_layout = QVBoxLayout(tracked_group)

        self.tracked_list = QListWidget()
        tracked_layout.addWidget(self.tracked_list)

        right_layout.addWidget(tracked_group)

        # Modified files
        modified_group = QGroupBox("Modified Files")
        modified_layout = QVBoxLayout(modified_group)

        self.modified_list = QListWidget()
        modified_layout.addWidget(self.modified_list)

        right_layout.addWidget(modified_group)

        layout.addLayout(right_layout)

    def refresh(self) -> None:
        """Refresh the dashboard data."""
        try:
            # Get repository status
            status = get_repo_status()

            # Update status label
            status_text = []
            if status["modified"]:
                status_text.append(f"{len(status['modified'])} modified files")
            if status["staged"]:
                status_text.append(f"{len(status['staged'])} staged files")
            if status["untracked"]:
                status_text.append(f"{len(status['untracked'])} untracked files")
            if status["unpushed"]:
                status_text.append(f"{len(status['unpushed'])} unpushed changes")

            if not status_text:
                self.status_label.setText("✓ Repository is clean")
            else:
                self.status_label.setText("; ".join(status_text))

            # Update tracked files list
            self.tracked_list.clear()
            tracked_files = list_tracked_files()
            for file_path in tracked_files:
                self.tracked_list.addItem(file_path)

            # Update modified files list
            self.modified_list.clear()
            for file_path in status["modified"]:
                self.modified_list.addItem(file_path)
            for file_path in status["staged"]:
                self.modified_list.addItem(f"{file_path} (staged)")

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def _push_changes(self) -> None:
        """Push changes to remote."""
        # TODO: Implement push functionality
        print("Push changes clicked")

    def _pull_changes(self) -> None:
        """Pull changes from remote."""
        # TODO: Implement pull functionality
        print("Pull changes clicked")
