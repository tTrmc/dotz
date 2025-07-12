"""Settings widget for dotz configuration."""

import json

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
    load_config,
    remove_file_pattern,
    reset_config,
    save_config,
    set_config_value,
)


class SettingsWidget(QWidget):
    """Widget for managing dotz settings."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

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

    def load_settings(self) -> None:
        """Load settings from configuration."""
        try:
            config = load_config()

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
