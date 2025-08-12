"""Template management widget for dotz."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
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


class TemplateWidget(QWidget):
    """Widget for managing dotz templates."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Left side - Template list
        left_layout = QVBoxLayout()

        # Templates group
        templates_group = QGroupBox("Available Templates")
        templates_layout = QVBoxLayout(templates_group)

        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self._on_template_selected)
        templates_layout.addWidget(self.templates_list)

        left_layout.addWidget(templates_group)

        # Template info group
        info_group = QGroupBox("Template Information")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        left_layout.addWidget(info_group)
        layout.addLayout(left_layout)

        # Right side - Actions
        right_layout = QVBoxLayout()

        # Template actions group
        actions_group = QGroupBox("Template Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.create_btn = QPushButton("Create Template...")
        self.create_btn.clicked.connect(self.create_template)
        actions_layout.addWidget(self.create_btn)

        self.apply_btn = QPushButton("Apply Template")
        self.apply_btn.clicked.connect(self.apply_template)
        self.apply_btn.setEnabled(False)
        actions_layout.addWidget(self.apply_btn)

        self.apply_merge_btn = QPushButton("Apply Template (Merge)")
        self.apply_merge_btn.clicked.connect(lambda: self.apply_template(merge=True))
        self.apply_merge_btn.setEnabled(False)
        actions_layout.addWidget(self.apply_merge_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.export_btn = QPushButton("Export Template...")
        self.export_btn.clicked.connect(self.export_template)
        self.export_btn.setEnabled(False)
        actions_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("Import Template...")
        self.import_btn.clicked.connect(self.import_template)
        actions_layout.addWidget(self.import_btn)

        actions_layout.addWidget(QWidget())  # Spacer

        self.delete_btn = QPushButton("Delete Template")
        self.delete_btn.clicked.connect(self.delete_template)
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
        """Refresh the templates list."""
        try:
            self.templates_list.clear()
            template_list = templates.list_templates()

            for template in template_list:
                name = template.get("name", "unknown")
                description = template.get("description", "")
                file_count = template.get("file_count", 0)
                created = template.get("created", "unknown")

                # Create display text
                display_text = f"{name} ({file_count} files)"
                if description:
                    display_text += f" - {description}"

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, name)  # Store template name
                self.templates_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh templates: {str(e)}")

    def _on_template_selected(self) -> None:
        """Handle template selection."""
        current_item = self.templates_list.currentItem()
        has_selection = current_item is not None

        # Enable/disable buttons based on selection
        self.apply_btn.setEnabled(has_selection)
        self.apply_merge_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if has_selection:
            template_name = current_item.data(Qt.ItemDataRole.UserRole)
            self._show_template_info(template_name)
        else:
            self.info_text.clear()

    def _show_template_info(self, name: str) -> None:
        """Show detailed information about a template."""
        try:
            info = templates.get_template_info(name)
            if info:
                info_text = f"<b>Template:</b> {name}<br>"
                
                description = info.get("description", "")
                if description:
                    info_text += f"<b>Description:</b> {description}<br>"
                
                info_text += f"<b>Created:</b> {info.get('created', 'unknown')}<br>"
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
                
                # Show first few files
                files = info.get("files", [])
                if files:
                    info_text += "<br><b>Files included:</b><br>"
                    for file_path in files[:10]:
                        info_text += f"• {file_path}<br>"
                    if len(files) > 10:
                        info_text += f"... and {len(files) - 10} more files"
                
                self.info_text.setHtml(info_text)
            else:
                self.info_text.setText(f"Could not load information for template '{name}'")

        except Exception as e:
            self.info_text.setText(f"Error loading template info: {str(e)}")

    def create_template(self) -> None:
        """Create a new template."""
        dialog = CreateTemplateDialog(self)
        if dialog.exec():
            name, description, files = dialog.get_values()
            try:
                success = templates.create_template(
                    name=name, description=description, files=files, quiet=True
                )
                if success:
                    QMessageBox.information(self, "Success", f"Template '{name}' created successfully!")
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to create template '{name}'")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating template: {str(e)}")

    def apply_template(self, merge: bool = False) -> None:
        """Apply the selected template."""
        current_item = self.templates_list.currentItem()
        if not current_item:
            return

        template_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm application
        mode_str = "merge mode" if merge else "overwrite mode"
        reply = QMessageBox.question(
            self,
            "Confirm Apply Template",
            f"Apply template '{template_name}' in {mode_str}?\n\n"
            f"This will {'merge with' if merge else 'replace'} your current dotfiles.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = templates.apply_template(
                    name=template_name, merge=merge, backup=True, quiet=True
                )
                if success:
                    QMessageBox.information(
                        self, "Success", f"Template '{template_name}' applied successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, "Failed", f"Failed to apply template '{template_name}'"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error applying template: {str(e)}")

    def export_template(self) -> None:
        """Export the selected template."""
        current_item = self.templates_list.currentItem()
        if not current_item:
            return

        template_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Get export path
        default_filename = f"{template_name}.tar.gz"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Template",
            default_filename,
            "Archive Files (*.tar.gz *.tgz);;All Files (*)",
        )

        if file_path:
            try:
                success = templates.export_template(
                    name=template_name, output_path=file_path, quiet=True
                )
                if success:
                    QMessageBox.information(
                        self, "Success", f"Template exported to {file_path}"
                    )
                else:
                    QMessageBox.warning(self, "Failed", "Failed to export template")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exporting template: {str(e)}")

    def import_template(self) -> None:
        """Import a template from archive."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Template",
            "",
            "Archive Files (*.tar.gz *.tgz);;All Files (*)",
        )

        if file_path:
            try:
                success = templates.import_template(archive_path=file_path, quiet=True)
                if success:
                    QMessageBox.information(
                        self, "Success", f"Template imported from {file_path}"
                    )
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to import template")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error importing template: {str(e)}")

    def delete_template(self) -> None:
        """Delete the selected template."""
        current_item = self.templates_list.currentItem()
        if not current_item:
            return

        template_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete template '{template_name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = templates.delete_template(name=template_name, quiet=True)
                if success:
                    QMessageBox.information(
                        self, "Success", f"Template '{template_name}' deleted"
                    )
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to delete template")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting template: {str(e)}")


class CreateTemplateDialog(QMessageBox):
    """Dialog for creating a new template."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create Template")
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        # Create form layout
        widget = QWidget()
        layout = QFormLayout(widget)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., work-setup")
        layout.addRow("Template Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("e.g., Work environment configuration")
        layout.addRow("Description:", self.description_edit)

        # File selection
        files_layout = QVBoxLayout()
        
        self.use_all_files = QCheckBox("Use all currently tracked files")
        self.use_all_files.setChecked(True)
        self.use_all_files.toggled.connect(self._on_use_all_toggled)
        files_layout.addWidget(self.use_all_files)
        
        self.files_edit = QTextEdit()
        self.files_edit.setPlaceholderText("Enter specific file paths, one per line")
        self.files_edit.setMaximumHeight(100)
        self.files_edit.setEnabled(False)
        files_layout.addWidget(self.files_edit)
        
        files_widget = QWidget()
        files_widget.setLayout(files_layout)
        layout.addRow("Files:", files_widget)

        self.layout().addWidget(widget, 0, 0, 1, self.layout().columnCount())

    def _on_use_all_toggled(self, checked: bool) -> None:
        """Handle use all files toggle."""
        self.files_edit.setEnabled(not checked)

    def get_values(self) -> tuple[str, str, Optional[list[str]]]:
        """Get the values from the dialog."""
        name = self.name_edit.text().strip()
        description = self.description_edit.text().strip()
        
        if self.use_all_files.isChecked():
            files = None  # Use all tracked files
        else:
            files_text = self.files_edit.toPlainText().strip()
            files = [line.strip() for line in files_text.split('\n') if line.strip()] if files_text else None
        
        return name, description, files