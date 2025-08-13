"""Files widget for managing dotfiles."""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core import add_dotfile, delete_dotfile, list_tracked_files, restore_dotfile


class FilesWidget(QWidget):
    """Widget for managing dotfiles."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Left side - File list
        left_layout = QVBoxLayout()

        # Tracked files group
        files_group = QGroupBox("Tracked Files")
        files_layout = QVBoxLayout(files_group)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        files_layout.addWidget(self.files_list)

        left_layout.addWidget(files_group)
        layout.addLayout(left_layout)

        # Right side - Actions
        right_layout = QVBoxLayout()

        # File actions group
        actions_group = QGroupBox("File Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.add_file_btn = QPushButton("Add File...")
        self.add_file_btn.clicked.connect(self.add_file)
        actions_layout.addWidget(self.add_file_btn)

        self.add_dir_btn = QPushButton("Add Directory...")
        self.add_dir_btn.clicked.connect(self.add_directory)
        actions_layout.addWidget(self.add_dir_btn)

        # Add options
        options_layout = QVBoxLayout()
        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(True)
        self.recursive_check.setToolTip("Add directories recursively")
        options_layout.addWidget(self.recursive_check)

        self.push_after_add_check = QCheckBox("Push after add")
        self.push_after_add_check.setToolTip(
            "Automatically push to remote after adding files"
        )
        options_layout.addWidget(self.push_after_add_check)

        actions_layout.addLayout(options_layout)

        actions_layout.addWidget(QWidget())  # Spacer

        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.clicked.connect(self.restore_selected)
        actions_layout.addWidget(self.restore_btn)

        self.restore_all_btn = QPushButton("Restore All Files")
        self.restore_all_btn.clicked.connect(self.restore_all_files)
        actions_layout.addWidget(self.restore_all_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        actions_layout.addWidget(self.delete_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(self.refresh_btn)

        right_layout.addWidget(actions_group)
        right_layout.addStretch()

        layout.addLayout(right_layout)

    def refresh(self) -> None:
        """Refresh the files list."""
        try:
            self.files_list.clear()
            tracked_files = list_tracked_files()

            for file_path in tracked_files:
                item = QListWidgetItem(file_path)
                self.files_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh files: {str(e)}")

    def add_file(self) -> None:
        """Add a file to dotz."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Add", str(Path.home()), "All Files (*)"
        )

        if file_path:
            try:
                # Convert to relative path from home
                home_path = Path.home()
                abs_path = Path(file_path)

                if abs_path.is_relative_to(home_path):
                    rel_path = abs_path.relative_to(home_path)
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid File",
                        "Please select a file from your home directory.",
                    )
                    return

                success = add_dotfile(
                    rel_path,
                    push=self.push_after_add_check.isChecked(),
                    quiet=True,
                    recursive=self.recursive_check.isChecked(),
                )
                if success:
                    QMessageBox.information(self, "Success", f"Added {rel_path}")
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to add {rel_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error adding file: {str(e)}")

    def add_directory(self) -> None:
        """Add a directory to dotz."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Directory to Add", str(Path.home())
        )

        if dir_path:
            try:
                from ...core import find_config_files, load_config

                # Convert to relative path from home
                home_path = Path.home()
                abs_path = Path(dir_path)

                if abs_path.is_relative_to(home_path):
                    rel_path = abs_path.relative_to(home_path)
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Directory",
                        "Please select a directory from your home directory.",
                    )
                    return

                # Use core's file finding logic
                config = load_config()
                files_to_add = find_config_files(
                    abs_path, config, recursive=self.recursive_check.isChecked()
                )

                if not files_to_add:
                    QMessageBox.information(
                        self, "No Files", f"No matching files found in {rel_path}"
                    )
                    return

                # Ask user to confirm
                reply = QMessageBox.question(
                    self,
                    "Confirm Addition",
                    f"Found {len(files_to_add)} files in {rel_path}.\n\nAdd them all?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    success_count = 0
                    failed_count = 0
                    push_enabled = self.push_after_add_check.isChecked()

                    for i, file_path in enumerate(files_to_add):
                        try:
                            # Convert to relative path for add_dotfile
                            rel_file_path = file_path.relative_to(home_path)
                            # Only push on the last file if push is enabled
                            should_push = push_enabled and (i == len(files_to_add) - 1)
                            if add_dotfile(
                                rel_file_path,
                                quiet=True,
                                recursive=False,
                                push=should_push,
                            ):
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception:
                            failed_count += 1

                    if success_count > 0:
                        message = f"Added {success_count} files"
                        if failed_count > 0:
                            message += f" ({failed_count} failed)"
                        if push_enabled:
                            message += " and pushed to remote"
                        QMessageBox.information(self, "Success", message)
                        self.refresh()
                    else:
                        QMessageBox.warning(self, "Failed", "No files could be added")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error adding directory: {str(e)}")

    def restore_selected(self) -> None:
        """Restore selected files."""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select files to restore."
            )
            return

        failed_files = []
        for item in selected_items:
            file_path = Path(item.text())
            try:
                success = restore_dotfile(file_path, quiet=True)
                if not success:
                    failed_files.append(str(file_path))
            except Exception as e:
                failed_files.append(f"{file_path}: {str(e)}")

        if failed_files:
            QMessageBox.warning(
                self,
                "Restore Issues",
                "Failed to restore:\n" + "\n".join(failed_files),
            )
        else:
            QMessageBox.information(
                self, "Success", f"Restored {len(selected_items)} file(s)"
            )

        self.refresh()

    def restore_all_files(self) -> None:
        """Restore all tracked files."""
        try:
            tracked_files = list_tracked_files()
            if not tracked_files:
                QMessageBox.information(
                    self, "No Files", "No tracked files to restore."
                )
                return

            # Confirm restore
            reply = QMessageBox.question(
                self,
                "Confirm Restore All",
                f"Restore all {len(tracked_files)} tracked files?\n\n"
                "This will overwrite existing files in your home directory!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                success_count = 0
                failed_count = 0

                for tracked_file in tracked_files:
                    try:
                        file_path = Path(tracked_file)
                        if restore_dotfile(file_path, quiet=True, push=False):
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception:
                        failed_count += 1

                if success_count > 0:
                    message = f"Restored {success_count} files"
                    if failed_count > 0:
                        message += f" ({failed_count} failed)"
                    QMessageBox.information(self, "Success", message)
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", "No files could be restored")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error restoring files: {str(e)}")

    def delete_selected(self) -> None:
        """Delete selected files."""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select files to delete."
            )
            return

        # Confirm deletion
        file_names = [item.text() for item in selected_items]
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(file_names)} file(s)?\n\n"
            + "\n".join(file_names[:5])
            + ("..." if len(file_names) > 5 else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            paths = [Path(item.text()) for item in selected_items]
            try:
                success = delete_dotfile(paths, quiet=True)
                if success:
                    QMessageBox.information(
                        self, "Success", f"Deleted {len(paths)} file(s)"
                    )
                else:
                    QMessageBox.warning(
                        self, "Delete Issues", "Some files could not be deleted"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting files: {str(e)}")

            self.refresh()
