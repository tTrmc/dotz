"""Settings widget for dotz configuration."""

import json

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from ...core import (
    add_file_pattern,
    get_config_value,
    load_config,
    remove_file_pattern,
    reset_config,
    save_config,
    set_config_value,
)
from ..theme import Theme, theme_manager


class SettingsWidget(QWidget):
    """Widget for managing dotz settings."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Appearance Settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", Theme.LIGHT.value)
        self.theme_combo.addItem("Dark", Theme.DARK.value)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_layout.addRow("Theme:", self.theme_combo)

        layout.addWidget(appearance_group)

        # Search Settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)

        self.recursive_check = QCheckBox()
        search_layout.addRow("Recursive Search:", self.recursive_check)

        self.case_sensitive_check = QCheckBox()
        search_layout.addRow("Case Sensitive:", self.case_sensitive_check)

        self.follow_symlinks_check = QCheckBox()
        search_layout.addRow("Follow Symlinks:", self.follow_symlinks_check)

        layout.addWidget(search_group)

        # File Patterns
        patterns_group = QGroupBox("File Patterns")
        patterns_layout = QHBoxLayout(patterns_group)

        # Include patterns
        include_layout = QVBoxLayout()
        include_label = QLabel("Include Patterns:")
        include_layout.addWidget(include_label)

        self.include_list = QListWidget()
        include_layout.addWidget(self.include_list)

        include_buttons = QHBoxLayout()
        self.add_include_btn = QPushButton("Add")
        self.add_include_btn.clicked.connect(self._add_include_pattern)
        include_buttons.addWidget(self.add_include_btn)

        self.remove_include_btn = QPushButton("Remove")
        self.remove_include_btn.clicked.connect(self._remove_include_pattern)
        include_buttons.addWidget(self.remove_include_btn)

        include_layout.addLayout(include_buttons)
        patterns_layout.addLayout(include_layout)

        # Exclude patterns
        exclude_layout = QVBoxLayout()
        exclude_label = QLabel("Exclude Patterns:")
        exclude_layout.addWidget(exclude_label)

        self.exclude_list = QListWidget()
        exclude_layout.addWidget(self.exclude_list)

        exclude_buttons = QHBoxLayout()
        self.add_exclude_btn = QPushButton("Add")
        self.add_exclude_btn.clicked.connect(self._add_exclude_pattern)
        exclude_buttons.addWidget(self.add_exclude_btn)

        self.remove_exclude_btn = QPushButton("Remove")
        self.remove_exclude_btn.clicked.connect(self._remove_exclude_pattern)
        exclude_buttons.addWidget(self.remove_exclude_btn)

        exclude_layout.addLayout(exclude_buttons)
        patterns_layout.addLayout(exclude_layout)

        layout.addWidget(patterns_group)

        # Configuration editor
        config_group = QGroupBox("Raw Configuration")
        config_layout = QVBoxLayout(config_group)

        self.config_editor = QTextEdit()
        self.config_editor.setMaximumHeight(200)
        config_layout.addWidget(self.config_editor)

        config_buttons = QHBoxLayout()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        config_buttons.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_settings)
        config_buttons.addWidget(self.reset_btn)

        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self.load_settings)
        config_buttons.addWidget(self.reload_btn)

        config_layout.addLayout(config_buttons)
        layout.addWidget(config_group)

        # Advanced configuration group
        advanced_group = QGroupBox("Advanced Configuration")
        advanced_layout = QVBoxLayout(advanced_group)

        # Key-value editor
        kv_layout = QHBoxLayout()

        kv_left = QVBoxLayout()
        kv_left.addWidget(QLabel("Configuration Key:"))
        self.config_key_edit = QLineEdit()
        self.config_key_edit.setPlaceholderText("e.g., search_settings.recursive")
        kv_left.addWidget(self.config_key_edit)

        kv_left.addWidget(QLabel("Value:"))
        self.config_value_edit = QLineEdit()
        self.config_value_edit.setPlaceholderText(
            'e.g., true, false, "string", ["list"]'
        )
        kv_left.addWidget(self.config_value_edit)

        kv_buttons = QHBoxLayout()
        self.get_config_btn = QPushButton("Get Value")
        self.get_config_btn.clicked.connect(self._get_config_value)
        kv_buttons.addWidget(self.get_config_btn)

        self.set_config_btn = QPushButton("Set Value")
        self.set_config_btn.clicked.connect(self._set_config_value)
        kv_buttons.addWidget(self.set_config_btn)

        kv_left.addLayout(kv_buttons)
        kv_layout.addLayout(kv_left)

        # Config value display
        kv_right = QVBoxLayout()
        kv_right.addWidget(QLabel("Current Value:"))
        self.config_result_text = QTextEdit()
        self.config_result_text.setMaximumHeight(100)
        self.config_result_text.setReadOnly(True)
        kv_right.addWidget(self.config_result_text)

        kv_layout.addLayout(kv_right)
        advanced_layout.addLayout(kv_layout)

        layout.addWidget(advanced_group)

    def load_settings(self) -> None:
        """Load settings from configuration."""
        try:
            config = load_config()

            # Load appearance settings
            appearance_settings = config.get("appearance", {})
            theme_name = appearance_settings.get("theme", "light")

            # Set theme combo without triggering the change event
            self.theme_combo.blockSignals(True)
            if theme_name == "dark":
                self.theme_combo.setCurrentText("Dark")
            else:
                self.theme_combo.setCurrentText("Light")
            self.theme_combo.blockSignals(False)

            # Apply the theme
            try:
                theme = Theme(theme_name)
                theme_manager.set_theme(theme)
            except ValueError:
                theme_manager.set_theme(Theme.LIGHT)

            # Load search settings
            search_settings = config.get("search_settings", {})
            self.recursive_check.setChecked(search_settings.get("recursive", True))
            self.case_sensitive_check.setChecked(
                search_settings.get("case_sensitive", False)
            )
            self.follow_symlinks_check.setChecked(
                search_settings.get("follow_symlinks", False)
            )

            # Load file patterns
            file_patterns = config.get("file_patterns", {})

            # Include patterns
            self.include_list.clear()
            include_patterns = file_patterns.get("include", [])
            for pattern in include_patterns:
                self.include_list.addItem(QListWidgetItem(pattern))

            # Exclude patterns
            self.exclude_list.clear()
            exclude_patterns = file_patterns.get("exclude", [])
            for pattern in exclude_patterns:
                self.exclude_list.addItem(QListWidgetItem(pattern))

            # Load raw configuration
            self.config_editor.setPlainText(json.dumps(config, indent=2))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {str(e)}")

    def _save_settings(self) -> None:
        """Save all settings."""
        try:
            # Save search settings
            set_config_value(
                "search_settings.recursive",
                self.recursive_check.isChecked(),
                quiet=True,
            )
            set_config_value(
                "search_settings.case_sensitive",
                self.case_sensitive_check.isChecked(),
                quiet=True,
            )
            set_config_value(
                "search_settings.follow_symlinks",
                self.follow_symlinks_check.isChecked(),
                quiet=True,
            )

            # Try to save raw configuration
            try:
                raw_config = json.loads(self.config_editor.toPlainText())
                save_config(raw_config)
            except json.JSONDecodeError as e:
                QMessageBox.warning(
                    self,
                    "Invalid JSON",
                    f"Raw configuration contains invalid JSON: {str(e)}\n\n"
                    "Only basic settings were saved.",
                )

            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.load_settings()  # Reload to show current state

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                reset_config(quiet=True)
                self.load_settings()
                QMessageBox.information(self, "Success", "Settings reset to defaults!")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to reset settings: {str(e)}"
                )

    def _add_include_pattern(self) -> None:
        """Add a new include pattern."""
        pattern, ok = self._get_pattern_input("Add Include Pattern")
        if ok and pattern:
            try:
                add_file_pattern(pattern, "include", quiet=True)
                self.load_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add pattern: {str(e)}")

    def _remove_include_pattern(self) -> None:
        """Remove selected include pattern."""
        current_item = self.include_list.currentItem()
        if current_item:
            pattern = current_item.text()
            try:
                remove_file_pattern(pattern, "include", quiet=True)
                self.load_settings()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to remove pattern: {str(e)}"
                )

    def _add_exclude_pattern(self) -> None:
        """Add a new exclude pattern."""
        pattern, ok = self._get_pattern_input("Add Exclude Pattern")
        if ok and pattern:
            try:
                add_file_pattern(pattern, "exclude", quiet=True)
                self.load_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add pattern: {str(e)}")

    def _remove_exclude_pattern(self) -> None:
        """Remove selected exclude pattern."""
        current_item = self.exclude_list.currentItem()
        if current_item:
            pattern = current_item.text()
            try:
                remove_file_pattern(pattern, "exclude", quiet=True)
                self.load_settings()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to remove pattern: {str(e)}"
                )

    def _get_pattern_input(self, title: str) -> tuple[str, bool]:
        """Get pattern input from user."""
        from PySide6.QtWidgets import QInputDialog

        pattern, ok = QInputDialog.getText(
            self, title, "Enter file pattern (e.g., *.conf, .gitconfig):"
        )
        return pattern.strip(), ok

    def _get_config_value(self) -> None:
        """Get and display a configuration value."""
        key = self.config_key_edit.text().strip()
        if not key:
            QMessageBox.warning(
                self, "Invalid Key", "Please enter a configuration key."
            )
            return

        try:
            value = get_config_value(key, quiet=True)
            if value is not None:
                if isinstance(value, (list, dict)):
                    display_value = json.dumps(value, indent=2)
                else:
                    display_value = str(value)
                self.config_result_text.setPlainText(display_value)
                self.config_value_edit.setText(str(value))
            else:
                self.config_result_text.setPlainText("Key not found")
                self.config_value_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get config value: {str(e)}")
            self.config_result_text.setPlainText(f"Error: {str(e)}")

    def _set_config_value(self) -> None:
        """Set a configuration value."""
        key = self.config_key_edit.text().strip()
        value_str = self.config_value_edit.text().strip()

        if not key:
            QMessageBox.warning(
                self, "Invalid Key", "Please enter a configuration key."
            )
            return

        if not value_str:
            QMessageBox.warning(self, "Invalid Value", "Please enter a value.")
            return

        try:
            success = set_config_value(key, value_str, quiet=True)
            if success:
                QMessageBox.information(self, "Success", f"Set {key} = {value_str}")
                self.load_settings()  # Reload settings to show changes
                self._get_config_value()  # Update the display
            else:
                QMessageBox.warning(self, "Failed", "Failed to set configuration value")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set config value: {str(e)}")

    def _on_theme_changed(self, theme_text: str) -> None:
        """Handle theme selection change."""
        try:
            theme_value = "dark" if theme_text == "Dark" else "light"
            theme = Theme(theme_value)

            # Apply theme immediately
            theme_manager.set_theme(theme)

            # Save theme preference to config
            set_config_value("appearance.theme", theme_value, quiet=True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change theme: {str(e)}")
