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
from .widgets.dashboard import DashboardWidget
from .widgets.files import FilesWidget
from .widgets.settings import SettingsWidget


class DotzMainWindow(QMainWindow):
    """Main window for the dotz GUI application."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Dotz - Dotfiles Manager")
        self.setMinimumSize(QSize(1000, 700))

        # Check if dotz is initialized
        self.dotz_initialized = self._check_dotz_initialized()

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
        except SystemExit:
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

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh)
        view_menu.addAction(refresh_action)

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
        self.status_bar.showMessage("Pushing changes...")
        self.progress_bar.setVisible(True)
        # TODO: Implement push in a separate thread
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Push completed")

    def _pull_changes(self) -> None:
        """Pull changes from remote."""
        self.status_bar.showMessage("Pulling changes...")
        self.progress_bar.setVisible(True)
        # TODO: Implement pull in a separate thread
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Pull completed")

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
            "<p>Version 0.3.0</p>"
            "<p>Built with PySide6 and Qt6</p>",
        )


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
