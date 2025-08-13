"""Profile management widget for dotz."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ... import templates


class ProfileWidget(QWidget):
    """Widget for managing dotz profiles."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Left side - Profile list
        left_layout = QVBoxLayout()

        # Current profile group
        current_group = QGroupBox("Current Profile")
        current_layout = QVBoxLayout(current_group)

        self.current_label = QLabel("No active profile")
        self.current_label.setStyleSheet("font-weight: bold; color: green;")
        current_layout.addWidget(self.current_label)

        left_layout.addWidget(current_group)

        # Profiles group
        profiles_group = QGroupBox("Available Profiles")
        profiles_layout = QVBoxLayout(profiles_group)

        self.profiles_list = QListWidget()
        self.profiles_list.itemSelectionChanged.connect(self._on_profile_selected)
        profiles_layout.addWidget(self.profiles_list)

        left_layout.addWidget(profiles_group)

        # Profile info group
        info_group = QGroupBox("Profile Information")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        left_layout.addWidget(info_group)
        layout.addLayout(left_layout)

        # Right side - Actions
        right_layout = QVBoxLayout()

        # Profile actions group
        actions_group = QGroupBox("Profile Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.create_btn = QPushButton("Create Profile...")
        self.create_btn.clicked.connect(self.create_profile)
        actions_layout.addWidget(self.create_btn)

        self.switch_btn = QPushButton("Switch to Profile")
        self.switch_btn.clicked.connect(self.switch_profile)
        self.switch_btn.setEnabled(False)
        actions_layout.addWidget(self.switch_btn)

        self.switch_no_backup_btn = QPushButton("Switch (No Backup)")
        self.switch_no_backup_btn.clicked.connect(
            lambda: self.switch_profile(no_backup=True)
        )
        self.switch_no_backup_btn.setEnabled(False)
        actions_layout.addWidget(self.switch_no_backup_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.delete_btn = QPushButton("Delete Profile")
        self.delete_btn.clicked.connect(self.delete_profile)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(self.refresh_btn)

        right_layout.addWidget(actions_group)
        right_layout.addStretch()

        layout.addLayout(right_layout)

    def refresh(self) -> None:
        """Refresh the profiles list."""
        try:
            # Update current profile
            active_profile = templates.get_active_profile()
            if active_profile:
                self.current_label.setText(f"Active: {active_profile}")
                self.current_label.setStyleSheet("font-weight: bold; color: green;")
            else:
                self.current_label.setText("No active profile")
                self.current_label.setStyleSheet("font-weight: bold; color: orange;")

            # Update profiles list
            self.profiles_list.clear()
            profile_list = templates.list_profiles()

            for profile in profile_list:
                name = profile.get("name", "unknown")
                description = profile.get("description", "")
                environment = profile.get("environment", "")
                active = profile.get("active", False)

                # Create display text
                display_text = name
                if environment:
                    display_text += f" ({environment})"
                if description:
                    display_text += f" - {description}"
                if active:
                    display_text += " ●"

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, name)  # Store profile name

                # Highlight active profile
                if active:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(Qt.GlobalColor.darkGreen)

                self.profiles_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh profiles: {str(e)}")

    def _on_profile_selected(self) -> None:
        """Handle profile selection."""
        current_item = self.profiles_list.currentItem()
        has_selection = current_item is not None

        if has_selection:
            profile_name = current_item.data(Qt.ItemDataRole.UserRole)
            active_profile = templates.get_active_profile()
            is_active = profile_name == active_profile

            # Enable/disable buttons based on selection and active status
            self.switch_btn.setEnabled(not is_active)
            self.switch_no_backup_btn.setEnabled(not is_active)
            self.delete_btn.setEnabled(not is_active)

            self._show_profile_info(profile_name)
        else:
            self.switch_btn.setEnabled(False)
            self.switch_no_backup_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.info_text.clear()

    def _show_profile_info(self, name: str) -> None:
        """Show detailed information about a profile."""
        try:
            info = templates.get_profile_info(name)
            if info:
                active = info.get("active", False)
                info_text = f"<b>Profile:</b> {name}<br>"

                if active:
                    info_text += (
                        "<b>Status:</b> <span style='color: green;'>ACTIVE</span><br>"
                    )

                description = info.get("description", "")
                if description:
                    info_text += f"<b>Description:</b> {description}<br>"

                environment = info.get("environment", "")
                if environment:
                    info_text += f"<b>Environment:</b> {environment}<br>"

                info_text += f"<b>Created:</b> {info.get('created', 'unknown')}<br>"
                info_text += f"<b>Last used:</b> {info.get('last_used', 'never')}<br>"
                info_text += f"<b>Files:</b> {info.get('file_count', 0)}<br>"

                total_size = info.get("total_size", 0)
                if total_size > 0:
                    if total_size < 1024:
                        size_str = f"{total_size} bytes"
                    elif total_size < 1024 * 1024:
                        size_str = f"{total_size / 1024:.1f} KB"
                    else:
                        size_str = f"{total_size / (1024 * 1024):.1f} MB"
                    info_text += f"<b>Size:</b> {size_str}<br>"

                version = info.get("version", "")
                if version:
                    info_text += f"<b>Version:</b> {version}<br>"

                self.info_text.setHtml(info_text)
            else:
                self.info_text.setText(
                    f"Could not load information for profile '{name}'"
                )

        except Exception as e:
            self.info_text.setText(f"Error loading profile info: {str(e)}")

    def create_profile(self) -> None:
        """Create a new profile."""
        dialog = CreateProfileDialog(self)
        if dialog.exec():
            name, description, environment, copy_from = dialog.get_values()
            try:
                success = templates.create_profile(
                    name=name,
                    description=description,
                    environment=environment,
                    copy_from=copy_from,
                    quiet=True,
                )
                if success:
                    QMessageBox.information(
                        self, "Success", f"Profile '{name}' created successfully!"
                    )
                    self.refresh()
                else:
                    QMessageBox.warning(
                        self, "Failed", f"Failed to create profile '{name}'"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating profile: {str(e)}")

    def switch_profile(self, no_backup: bool = False) -> None:
        """Switch to the selected profile."""
        current_item = self.profiles_list.currentItem()
        if not current_item:
            return

        profile_name = current_item.data(Qt.ItemDataRole.UserRole)
        current_profile = templates.get_active_profile()

        # Confirm switch
        backup_text = (
            "without saving current state" if no_backup else "and save current state"
        )
        reply = QMessageBox.question(
            self,
            "Confirm Profile Switch",
            f"Switch to profile '{profile_name}' {backup_text}?\n\n"
            f"Current profile: {current_profile or 'None'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = templates.switch_profile(
                    name=profile_name, backup=not no_backup, quiet=True
                )
                if success:
                    QMessageBox.information(
                        self, "Success", f"Switched to profile '{profile_name}'"
                    )
                    self.refresh()
                else:
                    QMessageBox.warning(
                        self, "Failed", f"Failed to switch to profile '{profile_name}'"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Error switching profile: {str(e)}"
                )

    def delete_profile(self) -> None:
        """Delete the selected profile."""
        current_item = self.profiles_list.currentItem()
        if not current_item:
            return

        profile_name = current_item.data(Qt.ItemDataRole.UserRole)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete profile '{profile_name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = templates.delete_profile(name=profile_name, quiet=True)
                if success:
                    QMessageBox.information(
                        self, "Success", f"Profile '{profile_name}' deleted"
                    )
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to delete profile")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting profile: {str(e)}")


class CreateProfileDialog(QMessageBox):
    """Dialog for creating a new profile."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create Profile")
        self.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )

        # Create form layout
        widget = QWidget()
        layout = QFormLayout(widget)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., work")
        layout.addRow("Profile Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("e.g., Work environment setup")
        layout.addRow("Description:", self.description_edit)

        self.environment_edit = QLineEdit()
        self.environment_edit.setPlaceholderText("e.g., work, personal, server")
        layout.addRow("Environment:", self.environment_edit)

        # Copy from existing profile
        copy_layout = QVBoxLayout()

        self.copy_from_check = QCheckBox("Copy from existing profile")
        self.copy_from_check.toggled.connect(self._on_copy_from_toggled)
        copy_layout.addWidget(self.copy_from_check)

        self.copy_from_edit = QLineEdit()
        self.copy_from_edit.setPlaceholderText("Enter existing profile name")
        self.copy_from_edit.setEnabled(False)
        copy_layout.addWidget(self.copy_from_edit)

        copy_widget = QWidget()
        copy_widget.setLayout(copy_layout)
        layout.addRow("Copy From:", copy_widget)

        self.layout().addWidget(widget, 0, 0, 1, self.layout().columnCount())

    def _on_copy_from_toggled(self, checked: bool) -> None:
        """Handle copy from toggle."""
        self.copy_from_edit.setEnabled(checked)

    def get_values(self) -> tuple[str, str, str, Optional[str]]:
        """Get the values from the dialog."""
        name = self.name_edit.text().strip()
        description = self.description_edit.text().strip()
        environment = self.environment_edit.text().strip()

        copy_from = None
        if self.copy_from_check.isChecked():
            copy_from_text = self.copy_from_edit.text().strip()
            copy_from = copy_from_text if copy_from_text else None

        return name, description, environment, copy_from
