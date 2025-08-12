"""Backup management widget for dotz."""

from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core import (
    create_backup,
    get_home_dir,
    list_backups,
    parse_backup_filename,
    restore_from_backup,
)


class BackupWidget(QWidget):
    """Widget for managing dotz backups."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Left side - Backup list
        left_layout = QVBoxLayout()

        # Backups group
        backups_group = QGroupBox("Available Backups")
        backups_layout = QVBoxLayout(backups_group)

        self.backups_list = QListWidget()
        self.backups_list.itemSelectionChanged.connect(self._on_backup_selected)
        backups_layout.addWidget(self.backups_list)

        left_layout.addWidget(backups_group)

        # Backup info group
        info_group = QGroupBox("Backup Information")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        left_layout.addWidget(info_group)
        layout.addLayout(left_layout)

        # Right side - Actions
        right_layout = QVBoxLayout()

        # Create backup group
        create_group = QGroupBox("Create Backup")
        create_layout = QVBoxLayout(create_group)

        self.create_manual_btn = QPushButton("Create Manual Backup...")
        self.create_manual_btn.clicked.connect(self.create_manual_backup)
        create_layout.addWidget(self.create_manual_btn)

        right_layout.addWidget(create_group)

        # Backup actions group
        actions_group = QGroupBox("Backup Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.clicked.connect(self.restore_backup)
        self.restore_btn.setEnabled(False)
        actions_layout.addWidget(self.restore_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(self.refresh_btn)

        right_layout.addWidget(actions_group)

        # Cleanup group
        cleanup_group = QGroupBox("Cleanup")
        cleanup_layout = QVBoxLayout(cleanup_group)

        # Cleanup controls
        cleanup_controls = QHBoxLayout()
        cleanup_controls.addWidget(QLabel("Delete backups older than:"))
        
        self.cleanup_days = QSpinBox()
        self.cleanup_days.setMinimum(1)
        self.cleanup_days.setMaximum(365)
        self.cleanup_days.setValue(30)
        self.cleanup_days.setSuffix(" days")
        cleanup_controls.addWidget(self.cleanup_days)
        
        cleanup_layout.addLayout(cleanup_controls)

        self.cleanup_btn = QPushButton("Clean Old Backups")
        self.cleanup_btn.clicked.connect(self.clean_old_backups)
        cleanup_layout.addWidget(self.cleanup_btn)

        right_layout.addWidget(cleanup_group)
        right_layout.addStretch()

        layout.addLayout(right_layout)

    def refresh(self) -> None:
        """Refresh the backups list."""
        try:
            self.backups_list.clear()
            backups = list_backups()

            if not backups:
                item = QListWidgetItem("No backups found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
                self.backups_list.addItem(item)
                return

            for backup_path in backups:
                backup_name = backup_path.name
                original_file, operation, formatted_time = parse_backup_filename(backup_name)

                if original_file != backup_name:  # Successfully parsed
                    # Create display text
                    display_text = f"{original_file} - {operation} ({formatted_time})"
                else:
                    # Fallback for malformed backup names
                    display_text = backup_name

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, backup_path)  # Store backup path
                self.backups_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh backups: {str(e)}")

    def _on_backup_selected(self) -> None:
        """Handle backup selection."""
        current_item = self.backups_list.currentItem()
        has_selection = (current_item is not None and 
                        current_item.data(Qt.ItemDataRole.UserRole) is not None)

        # Enable/disable restore button based on selection
        self.restore_btn.setEnabled(has_selection)

        if has_selection:
            backup_path = current_item.data(Qt.ItemDataRole.UserRole)
            self._show_backup_info(backup_path)
        else:
            self.info_text.clear()

    def _show_backup_info(self, backup_path: Path) -> None:
        """Show detailed information about a backup."""
        try:
            backup_name = backup_path.name
            original_file, operation, formatted_time = parse_backup_filename(backup_name)

            info_text = f"<b>Backup File:</b> {backup_name}<br>"
            
            if original_file != backup_name:  # Successfully parsed
                info_text += f"<b>Original File:</b> {original_file}<br>"
                info_text += f"<b>Operation:</b> {operation}<br>"
                info_text += f"<b>Created:</b> {formatted_time}<br>"

            # File size
            try:
                size = backup_path.stat().st_size
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                info_text += f"<b>Size:</b> {size_str}<br>"
            except Exception:
                info_text += "<b>Size:</b> Unknown<br>"

            # Full path
            info_text += f"<b>Path:</b> {backup_path}<br>"

            self.info_text.setHtml(info_text)

        except Exception as e:
            self.info_text.setText(f"Error loading backup info: {str(e)}")

    def create_manual_backup(self) -> None:
        """Create a manual backup of a file or directory."""
        home = get_home_dir()
        
        # Get file or directory to backup
        path_str, ok = QInputDialog.getText(
            self,
            "Create Manual Backup",
            "Enter the path to backup (relative to home directory):",
            text="",
        )

        if not ok or not path_str.strip():
            return

        path_str = path_str.strip()
        file_path = home / path_str

        if not file_path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The path '{path_str}' does not exist in your home directory.",
            )
            return

        # Get operation name
        operation, ok = QInputDialog.getText(
            self,
            "Backup Operation",
            "Enter operation name for this backup:",
            text="manual",
        )

        if not ok:
            return

        operation = operation.strip() or "manual"

        try:
            backup_path = create_backup(file_path, operation=operation, quiet=True)
            if backup_path:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Backup created successfully:\n{backup_path.name}",
                )
                self.refresh()
            else:
                QMessageBox.warning(self, "Failed", "Failed to create backup")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating backup: {str(e)}")

    def restore_backup(self) -> None:
        """Restore the selected backup."""
        current_item = self.backups_list.currentItem()
        if not current_item:
            return

        backup_path = current_item.data(Qt.ItemDataRole.UserRole)
        if not backup_path:
            return

        backup_name = backup_path.name
        original_file, operation, formatted_time = parse_backup_filename(backup_name)

        # Confirm restoration
        if original_file != backup_name:  # Successfully parsed
            message = (
                f"Restore '{original_file}' from backup?\n\n"
                f"Backup: {backup_name}\n"
                f"Created: {formatted_time}\n"
                f"Operation: {operation}\n\n"
                "This will overwrite the current file!"
            )
        else:
            message = (
                f"Restore from backup '{backup_name}'?\n\n"
                "This will overwrite the current file!"
            )

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = restore_from_backup(backup_path, quiet=True)
                if success:
                    if original_file != backup_name:
                        QMessageBox.information(
                            self, "Success", f"Successfully restored '{original_file}'"
                        )
                    else:
                        QMessageBox.information(self, "Success", "Backup restored successfully")
                else:
                    QMessageBox.warning(self, "Failed", "Failed to restore backup")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error restoring backup: {str(e)}")

    def clean_old_backups(self) -> None:
        """Clean old backup files."""
        try:
            backups = list_backups()
            if not backups:
                QMessageBox.information(self, "No Backups", "No backups found to clean.")
                return

            # Filter backups older than specified days
            older_than_days = self.cleanup_days.value()
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            old_backups = []

            for backup_path in backups:
                backup_time = datetime.fromtimestamp(backup_path.stat().st_mtime)
                if backup_time < cutoff_time:
                    old_backups.append(backup_path)

            if not old_backups:
                QMessageBox.information(
                    self,
                    "No Old Backups",
                    f"No backups older than {older_than_days} days found.",
                )
                return

            # Confirm deletion
            backup_list = "\n".join([bp.name for bp in old_backups[:5]])
            if len(old_backups) > 5:
                backup_list += f"\n... and {len(old_backups) - 5} more"

            reply = QMessageBox.question(
                self,
                "Confirm Cleanup",
                f"Delete {len(old_backups)} backup(s) older than {older_than_days} days?\n\n"
                f"{backup_list}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                removed_count = 0
                failed_count = 0

                for backup_path in old_backups:
                    try:
                        backup_path.unlink()
                        removed_count += 1
                    except Exception:
                        failed_count += 1

                message = f"Successfully removed {removed_count} backup(s)"
                if failed_count > 0:
                    message += f" ({failed_count} failed)"

                QMessageBox.information(self, "Cleanup Complete", message)
                self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during cleanup: {str(e)}")