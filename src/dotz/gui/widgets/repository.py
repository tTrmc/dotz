"""Repository operations widget for dotz."""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core import (
    clone_repo,
    commit_repo,
    diff_files,
    list_tracked_files,
    restore_dotfile,
    validate_symlinks,
)


class OperationWorker(QThread):
    """Worker thread for long-running repository operations."""

    finished = Signal(bool, str)  # success, message
    progress = Signal(str)  # progress message

    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self) -> None:
        """Run the operation."""
        try:
            if self.operation == "clone":
                self.progress.emit("Cloning repository...")
                success = clone_repo(self.kwargs["remote_url"], quiet=True)
                message = (
                    "Repository cloned successfully!" if success else "Clone failed"
                )

            elif self.operation == "validate":
                self.progress.emit("Validating symlinks...")
                results = validate_symlinks(
                    repair=self.kwargs.get("repair", False), quiet=True
                )
                if results:
                    total_issues = (
                        len(results.get("broken", []))
                        + len(results.get("missing", []))
                        + len(results.get("wrong_target", []))
                        + len(results.get("not_symlink", []))
                    )
                    if total_issues == 0:
                        success = True
                        message = "All symlinks are valid!"
                    else:
                        repair_failures = len(results.get("repair_failed", []))
                        if self.kwargs.get("repair", False) and repair_failures == 0:
                            success = True
                            message = f"Fixed {total_issues} symlink issues!"
                        else:
                            success = False
                            message = f"Found {total_issues} symlink issues"
                            if self.kwargs.get("repair", False) and repair_failures > 0:
                                message += f" ({repair_failures} could not be fixed)"
                else:
                    success = False
                    message = "Validation failed"

            elif self.operation == "restore_all":
                self.progress.emit("Restoring all tracked files...")
                tracked_files = list_tracked_files()
                if not tracked_files:
                    success = True
                    message = "No tracked files to restore"
                else:
                    success_count = 0
                    failed_count = 0

                    for tracked_file in tracked_files:
                        self.progress.emit(f"Restoring {tracked_file}...")
                        try:
                            if restore_dotfile(tracked_file, quiet=True, push=False):
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception:
                            failed_count += 1

                    total = success_count + failed_count
                    if failed_count == 0:
                        success = True
                        message = f"Successfully restored all {total} files!"
                    else:
                        success = failed_count < success_count
                        message = f"Restored {success_count}/{total} files ({failed_count} failed)"
            else:
                success = False
                message = f"Unknown operation: {self.operation}"

            self.finished.emit(success, message)

        except Exception as e:
            self.finished.emit(False, f"Error during {self.operation}: {str(e)}")


class RepositoryWidget(QWidget):
    """Widget for repository operations."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Clone repository group
        clone_group = QGroupBox("Clone Repository")
        clone_layout = QFormLayout(clone_group)

        self.clone_url_edit = QLineEdit()
        self.clone_url_edit.setPlaceholderText(
            "https://github.com/username/dotfiles.git"
        )
        clone_layout.addRow("Remote URL:", self.clone_url_edit)

        clone_buttons = QHBoxLayout()
        self.clone_btn = QPushButton("Clone Repository")
        self.clone_btn.clicked.connect(self.clone_repository)
        clone_buttons.addWidget(self.clone_btn)
        clone_buttons.addStretch()

        clone_layout.addRow(clone_buttons)
        layout.addWidget(clone_group)

        # Repository operations group
        operations_group = QGroupBox("Repository Operations")
        operations_layout = QVBoxLayout(operations_group)

        # Restore all files
        restore_layout = QHBoxLayout()
        self.restore_all_btn = QPushButton("Restore All Files")
        self.restore_all_btn.clicked.connect(self.restore_all_files)
        restore_layout.addWidget(self.restore_all_btn)

        restore_info = QLabel("Restore all tracked dotfiles to home directory")
        restore_info.setStyleSheet("color: gray; font-style: italic;")
        restore_layout.addWidget(restore_info)
        restore_layout.addStretch()

        operations_layout.addLayout(restore_layout)

        # Validate symlinks
        validate_layout = QHBoxLayout()
        self.validate_btn = QPushButton("Validate Symlinks")
        self.validate_btn.clicked.connect(self.validate_symlinks)
        validate_layout.addWidget(self.validate_btn)

        self.validate_repair_btn = QPushButton("Validate & Repair")
        self.validate_repair_btn.clicked.connect(
            lambda: self.validate_symlinks(repair=True)
        )
        validate_layout.addWidget(self.validate_repair_btn)

        validate_info = QLabel("Check and fix broken symlinks")
        validate_info.setStyleSheet("color: gray; font-style: italic;")
        validate_layout.addWidget(validate_info)
        validate_layout.addStretch()

        operations_layout.addLayout(validate_layout)

        layout.addWidget(operations_group)

        # Git operations group
        git_group = QGroupBox("Git Operations")
        git_layout = QVBoxLayout(git_group)

        # Commit changes
        commit_layout = QHBoxLayout()
        self.commit_btn = QPushButton("Commit Changes...")
        self.commit_btn.clicked.connect(self.commit_changes)
        commit_layout.addWidget(self.commit_btn)

        commit_info = QLabel("Commit modified files with custom message")
        commit_info.setStyleSheet("color: gray; font-style: italic;")
        commit_layout.addWidget(commit_info)
        commit_layout.addStretch()

        git_layout.addLayout(commit_layout)

        # Show diff
        diff_layout = QHBoxLayout()
        self.diff_btn = QPushButton("Show Differences")
        self.diff_btn.clicked.connect(self.show_diff)
        diff_layout.addWidget(self.diff_btn)

        diff_info = QLabel("Show changes in modified files")
        diff_info.setStyleSheet("color: gray; font-style: italic;")
        diff_layout.addWidget(diff_info)
        diff_layout.addStretch()

        git_layout.addLayout(diff_layout)

        layout.addWidget(git_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        # Progress label
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.progress_label)

        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        self.results_text.setVisible(False)
        layout.addWidget(self.results_text)

        layout.addStretch()

    def _start_operation(self, operation: str, **kwargs) -> None:
        """Start a long-running operation in a worker thread."""
        # Disable buttons during operation
        self.clone_btn.setEnabled(False)
        self.restore_all_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
        self.validate_repair_btn.setEnabled(False)
        self.commit_btn.setEnabled(False)
        self.diff_btn.setEnabled(False)

        # Show progress indicators
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.results_text.setVisible(False)

        # Start worker
        self.worker = OperationWorker(operation, **kwargs)
        self.worker.finished.connect(self._on_operation_finished)
        self.worker.progress.connect(self._on_operation_progress)
        self.worker.start()

    def _on_operation_progress(self, message: str) -> None:
        """Handle operation progress updates."""
        self.progress_label.setText(message)

    def _on_operation_finished(self, success: bool, message: str) -> None:
        """Handle operation completion."""
        # Re-enable buttons
        self.clone_btn.setEnabled(True)
        self.restore_all_btn.setEnabled(True)
        self.validate_btn.setEnabled(True)
        self.validate_repair_btn.setEnabled(True)
        self.commit_btn.setEnabled(True)
        self.diff_btn.setEnabled(True)

        # Hide progress indicators
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Show result
        if success:
            QMessageBox.information(self, "Operation Complete", message)
        else:
            QMessageBox.warning(self, "Operation Failed", message)

    def clone_repository(self) -> None:
        """Clone a repository."""
        remote_url = self.clone_url_edit.text().strip()
        if not remote_url:
            QMessageBox.warning(
                self, "Invalid URL", "Please enter a remote repository URL."
            )
            return

        # Confirm clone
        reply = QMessageBox.question(
            self,
            "Confirm Clone",
            f"Clone repository from:\n{remote_url}\n\n"
            "This will replace your current dotz repository!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._start_operation("clone", remote_url=remote_url)

    def restore_all_files(self) -> None:
        """Restore all tracked files."""
        # Confirm restore
        try:
            tracked_files = list_tracked_files()
            if not tracked_files:
                QMessageBox.information(
                    self, "No Files", "No tracked files to restore."
                )
                return

            reply = QMessageBox.question(
                self,
                "Confirm Restore All",
                f"Restore all {len(tracked_files)} tracked files?\n\n"
                "This will overwrite existing files in your home directory!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._start_operation("restore_all")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to list tracked files: {str(e)}"
            )

    def validate_symlinks(self, repair: bool = False) -> None:
        """Validate symlinks."""
        action = "validate and repair" if repair else "validate"

        reply = QMessageBox.question(
            self,
            f"Confirm {action.title()}",
            f"This will {action} all symlinks managed by dotz.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._start_operation("validate", repair=repair)

    def commit_changes(self) -> None:
        """Commit changes with a custom message."""
        message, ok = QInputDialog.getText(
            self,
            "Commit Changes",
            "Enter commit message:",
            text="Update dotfiles",
        )

        if ok and message.strip():
            try:
                success = commit_repo(message=message.strip(), quiet=True)
                if success:
                    QMessageBox.information(
                        self, "Success", "Changes committed successfully!"
                    )
                else:
                    QMessageBox.warning(self, "Failed", "Failed to commit changes")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Error committing changes: {str(e)}"
                )

    def show_diff(self) -> None:
        """Show differences in modified files."""
        try:
            # Capture diff output
            success = diff_files(quiet=True)
            if success:
                # For now, just show a message since diff_files prints to console
                # In a real implementation, we'd need to modify diff_files to return the diff
                QMessageBox.information(
                    self,
                    "Differences",
                    "Differences have been printed to the console.\n\n"
                    "Check the terminal for detailed diff output.",
                )
            else:
                QMessageBox.information(self, "No Changes", "No changes to show.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error showing diff: {str(e)}")
