#!/usr/bin/env python3
"""Main entry point for dotz GUI application."""

import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core import ensure_repo
from .theme import theme_manager
from .widgets.backups import BackupWidget
from .widgets.dashboard import DashboardWidget
from .widgets.files import FilesWidget
from .widgets.profiles import ProfileWidget
from .widgets.repository import RepositoryWidget
from .widgets.settings import SettingsWidget
from .widgets.templates import TemplateWidget


class DotzMainWindow(QMainWindow):
    """Main window for the dotz GUI application."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Dotz - Dotfiles Manager")
        self.setMinimumSize(QSize(1000, 700))

        # Check if dotz is initialized
        self.dotz_initialized = self._check_dotz_initialized()

        # Initialize theme before setting up UI
        self._load_saved_theme()

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()

        # Load initial data if dotz is initialized
        if self.dotz_initialized:
            self._load_initial_data()

    def _check_dotz_initialized(self) -> bool:
        """Check if dotz repository is initialized."""
        try:
            ensure_repo()
            return True
        except (SystemExit, Exception):
            return False

    def _setup_ui(self) -> None:
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        if not self.dotz_initialized:
            # Show initialization widget if dotz is not set up
            self._setup_init_ui(main_layout)
        else:
            # Show main interface if dotz is initialized
            self._setup_main_ui(main_layout)

    def _setup_init_ui(self, layout: QVBoxLayout) -> None:
        """Set up the initialization interface."""
        from .widgets.init import InitWidget

        init_widget = InitWidget()
        init_widget.initialized.connect(self._on_dotz_initialized)
        layout.addWidget(init_widget)

    def _setup_main_ui(self, layout: QVBoxLayout) -> None:
        """Set up the main interface with tabs."""
        # Create tab widget
        self.tab_widget = QTabWidget()

        # Dashboard tab
        self.dashboard_widget = DashboardWidget()
        self.tab_widget.addTab(self.dashboard_widget, "Dashboard")

        # Files tab
        self.files_widget = FilesWidget()
        self.tab_widget.addTab(self.files_widget, "Files")

        # Templates tab
        self.templates_widget = TemplateWidget()
        self.tab_widget.addTab(self.templates_widget, "Templates")

        # Profiles tab
        self.profiles_widget = ProfileWidget()
        self.tab_widget.addTab(self.profiles_widget, "Profiles")

        # Backups tab
        self.backups_widget = BackupWidget()
        self.tab_widget.addTab(self.backups_widget, "Backups")

        # Repository tab
        self.repository_widget = RepositoryWidget()
        self.tab_widget.addTab(self.repository_widget, "Repository")

        # Settings tab
        self.settings_widget = SettingsWidget()
        self.tab_widget.addTab(self.settings_widget, "Settings")

        layout.addWidget(self.tab_widget)

    def _setup_menubar(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        if self.dotz_initialized:
            # Add file actions
            add_action = QAction("&Add File...", self)
            add_action.setShortcut("Ctrl+A")
            add_action.triggered.connect(self._add_file)
            file_menu.addAction(add_action)

            # Restore all action
            restore_all_action = QAction("&Restore All Files", self)
            restore_all_action.triggered.connect(self._restore_all)
            file_menu.addAction(restore_all_action)

            file_menu.addSeparator()

            # Push/Pull actions
            push_action = QAction("&Push", self)
            push_action.setShortcut("Ctrl+P")
            push_action.triggered.connect(self._push_changes)
            file_menu.addAction(push_action)

            pull_action = QAction("Pu&ll", self)
            pull_action.setShortcut("Ctrl+L")
            pull_action.triggered.connect(self._pull_changes)
            file_menu.addAction(pull_action)

            file_menu.addSeparator()

            # Clone action
            clone_action = QAction("&Clone Repository...", self)
            clone_action.triggered.connect(self._clone_repository)
            file_menu.addAction(clone_action)

            file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Templates menu
        if self.dotz_initialized:
            templates_menu = menubar.addMenu("&Templates")

            create_template_action = QAction("&Create Template...", self)
            create_template_action.triggered.connect(self._create_template)
            templates_menu.addAction(create_template_action)

            templates_menu.addSeparator()

            import_template_action = QAction("&Import Template...", self)
            import_template_action.triggered.connect(self._import_template)
            templates_menu.addAction(import_template_action)

        # Profiles menu
        if self.dotz_initialized:
            profiles_menu = menubar.addMenu("&Profiles")

            create_profile_action = QAction("&Create Profile...", self)
            create_profile_action.triggered.connect(self._create_profile)
            profiles_menu.addAction(create_profile_action)

            profiles_menu.addSeparator()

            switch_profile_action = QAction("&Switch Profile...", self)
            switch_profile_action.triggered.connect(self._switch_profile)
            profiles_menu.addAction(switch_profile_action)

        # Tools menu
        if self.dotz_initialized:
            tools_menu = menubar.addMenu("&Tools")

            validate_action = QAction("&Validate Symlinks", self)
            validate_action.triggered.connect(self._validate_symlinks)
            tools_menu.addAction(validate_action)

            validate_repair_action = QAction("Validate && &Repair", self)
            validate_repair_action.triggered.connect(self._validate_repair)
            tools_menu.addAction(validate_repair_action)

            tools_menu.addSeparator()

            backup_action = QAction("Create &Backup...", self)
            backup_action.triggered.connect(self._create_backup)
            tools_menu.addAction(backup_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        # Theme toggle action
        toggle_theme_action = QAction("Toggle &Dark Mode", self)
        toggle_theme_action.setShortcut("Ctrl+D")
        toggle_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Set up the toolbar."""
        if not self.dotz_initialized:
            return

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Add file button
        add_btn = QPushButton("Add File")
        add_btn.clicked.connect(self._add_file)
        toolbar.addWidget(add_btn)

        toolbar.addSeparator()

        # Push/Pull buttons
        push_btn = QPushButton("Push")
        push_btn.clicked.connect(self._push_changes)
        toolbar.addWidget(push_btn)

        pull_btn = QPushButton("Pull")
        pull_btn.clicked.connect(self._pull_changes)
        toolbar.addWidget(pull_btn)

        toolbar.addSeparator()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)

    def _setup_statusbar(self) -> None:
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        if self.dotz_initialized:
            self.status_bar.showMessage("Ready")
        else:
            self.status_bar.showMessage("Dotz not initialized")

    def _load_initial_data(self) -> None:
        """Load initial data for all widgets."""
        if hasattr(self, "dashboard_widget"):
            self.dashboard_widget.refresh()
        if hasattr(self, "files_widget"):
            self.files_widget.refresh()
        if hasattr(self, "templates_widget"):
            self.templates_widget.refresh()
        if hasattr(self, "profiles_widget"):
            self.profiles_widget.refresh()
        if hasattr(self, "backups_widget"):
            self.backups_widget.refresh()
        if hasattr(self, "settings_widget"):
            self.settings_widget.load_settings()

    def _on_dotz_initialized(self) -> None:
        """Handle dotz initialization completion."""
        self.dotz_initialized = True
        # Recreate the UI with the main interface
        self.setCentralWidget(QWidget())
        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self.status_bar.showMessage("Dotz initialized successfully!")

    def _add_file(self) -> None:
        """Add a file to dotz."""
        if hasattr(self, "files_widget"):
            self.files_widget.add_file()

    def _push_changes(self) -> None:
        """Push changes to remote."""
        from ..core import push_repo

        self.status_bar.showMessage("Pushing changes...")
        self.progress_bar.setVisible(True)
        try:
            success = push_repo(quiet=True)
            self.progress_bar.setVisible(False)
            if success:
                self.status_bar.showMessage("Push completed successfully")
                self._load_initial_data()  # Refresh data after push
            else:
                self.status_bar.showMessage("Push failed")
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage(f"Push error: {str(e)}")
            QMessageBox.critical(
                self, "Push Error", f"Failed to push changes:\n{str(e)}"
            )

    def _pull_changes(self) -> None:
        """Pull changes from remote."""
        from ..core import pull_repo

        self.status_bar.showMessage("Pulling changes...")
        self.progress_bar.setVisible(True)
        try:
            success = pull_repo(quiet=True)
            self.progress_bar.setVisible(False)
            if success:
                self.status_bar.showMessage("Pull completed successfully")
                self._load_initial_data()  # Refresh data after pull
            else:
                self.status_bar.showMessage("Pull failed")
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage(f"Pull error: {str(e)}")
            QMessageBox.critical(
                self, "Pull Error", f"Failed to pull changes:\n{str(e)}"
            )

    def _refresh(self) -> None:
        """Refresh all data."""
        self.status_bar.showMessage("Refreshing...")
        self._load_initial_data()
        self.status_bar.showMessage("Refreshed")

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Dotz",
            "<h3>Dotz</h3>"
            "<p>A minimal, Git-backed dotfiles manager for Linux</p>"
            "<p>Version 0.4.0</p>"
            "<p>Built with PySide6 and Qt6</p>",
        )

    def _restore_all(self) -> None:
        """Restore all tracked files."""
        if hasattr(self, "repository_widget"):
            self.repository_widget.restore_all_files()

    def _clone_repository(self) -> None:
        """Clone a repository."""
        if hasattr(self, "repository_widget"):
            self.repository_widget.clone_repository()

    def _create_template(self) -> None:
        """Create a template."""
        if hasattr(self, "templates_widget"):
            self.tab_widget.setCurrentWidget(self.templates_widget)
            self.templates_widget.create_template()

    def _import_template(self) -> None:
        """Import a template."""
        if hasattr(self, "templates_widget"):
            self.tab_widget.setCurrentWidget(self.templates_widget)
            self.templates_widget.import_template()

    def _create_profile(self) -> None:
        """Create a profile."""
        if hasattr(self, "profiles_widget"):
            self.tab_widget.setCurrentWidget(self.profiles_widget)
            self.profiles_widget.create_profile()

    def _switch_profile(self) -> None:
        """Switch to a profile."""
        if hasattr(self, "profiles_widget"):
            self.tab_widget.setCurrentWidget(self.profiles_widget)

    def _validate_symlinks(self) -> None:
        """Validate symlinks."""
        if hasattr(self, "repository_widget"):
            self.tab_widget.setCurrentWidget(self.repository_widget)
            self.repository_widget.validate_symlinks()

    def _validate_repair(self) -> None:
        """Validate and repair symlinks."""
        if hasattr(self, "repository_widget"):
            self.tab_widget.setCurrentWidget(self.repository_widget)
            self.repository_widget.validate_symlinks(repair=True)

    def _create_backup(self) -> None:
        """Create a backup."""
        if hasattr(self, "backups_widget"):
            self.tab_widget.setCurrentWidget(self.backups_widget)
            self.backups_widget.create_manual_backup()

    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        theme_manager.toggle_theme()

    def _load_saved_theme(self) -> None:
        """Load the saved theme preference."""
        if self.dotz_initialized:
            try:
                from ..core import get_config_value
                from .theme import Theme

                theme_name = get_config_value("appearance.theme", quiet=True)
                if theme_name:
                    try:
                        theme = Theme(theme_name)
                        theme_manager.set_theme(theme)
                    except ValueError:
                        pass  # Use default theme if invalid
            except Exception:
                pass  # Use default theme if any error occurs


def main() -> None:
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Dotz")
    app.setApplicationVersion("0.3.0")
    app.setOrganizationName("Dotz")

    # Set application style
    app.setStyle("Fusion")

    window = DotzMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
