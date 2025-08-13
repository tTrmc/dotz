"""Theme management for the dotz GUI application."""

from enum import Enum
from typing import Any, Dict

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class Theme(Enum):
    """Available themes."""

    LIGHT = "light"
    DARK = "dark"


class ThemeManager(QObject):
    """Manages application themes."""

    theme_changed = Signal(str)  # Emitted when theme changes

    def __init__(self) -> None:
        super().__init__()
        self._current_theme = Theme.LIGHT
        self._initialize_themes()

    def _initialize_themes(self) -> None:
        """Initialize theme definitions."""
        self._themes: Dict[Theme, Dict[str, Any]] = {
            Theme.LIGHT: {
                "stylesheet": self._get_light_stylesheet(),
                "palette": self._get_light_palette(),
            },
            Theme.DARK: {
                "stylesheet": self._get_dark_stylesheet(),
                "palette": self._get_dark_palette(),
            },
        }

    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet."""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #333333;
        }

        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: #ffffff;
        }

        QTabWidget::tab-bar {
            alignment: left;
        }

        QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            border: 1px solid #c0c0c0;
            border-bottom-color: #c0c0c0;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 8ex;
            padding: 6px 12px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom-color: #ffffff;
        }

        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #c0c0c0;
            border-radius: 5px;
            margin-top: 1ex;
            background-color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #ffffff;
        }

        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #c0c0c0;
            border-radius: 4px;
            padding: 6px 12px;
            color: #333333;
        }

        QPushButton:hover {
            background-color: #e0e0e0;
            border-color: #a0a0a0;
        }

        QPushButton:pressed {
            background-color: #d0d0d0;
        }

        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
            border-color: #d0d0d0;
        }

        QLineEdit, QTextEdit, QListWidget {
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            border-radius: 3px;
            padding: 4px;
            color: #333333;
        }

        QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
            border-color: #0078d4;
        }

        QCheckBox {
            color: #333333;
        }

        QLabel {
            color: #333333;
        }

        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #c0c0c0;
        }

        QToolBar {
            background-color: #f8f8f8;
            border-bottom: 1px solid #c0c0c0;
        }

        QMenuBar {
            background-color: #ffffff;
            color: #333333;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }

        QMenu {
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            color: #333333;
        }

        QMenu::item {
            padding: 4px 20px;
        }

        QMenu::item:selected {
            background-color: #e0e0e0;
        }
        """

    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet."""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }

        QTabWidget::tab-bar {
            alignment: left;
        }

        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            border-bottom-color: #555555;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 8ex;
            padding: 6px 12px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom-color: #2b2b2b;
        }

        QTabBar::tab:hover {
            background-color: #505050;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }

        QPushButton:hover {
            background-color: #505050;
            border-color: #666666;
        }

        QPushButton:pressed {
            background-color: #353535;
        }

        QPushButton:disabled {
            background-color: #353535;
            color: #777777;
            border-color: #444444;
        }

        QLineEdit, QTextEdit, QListWidget {
            background-color: #353535;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 4px;
            color: #ffffff;
        }

        QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
            border-color: #0078d4;
        }

        QCheckBox {
            color: #ffffff;
        }

        QLabel {
            color: #ffffff;
        }

        QStatusBar {
            background-color: #404040;
            border-top: 1px solid #555555;
            color: #ffffff;
        }

        QToolBar {
            background-color: #353535;
            border-bottom: 1px solid #555555;
        }

        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background-color: #505050;
        }

        QMenu {
            background-color: #353535;
            border: 1px solid #555555;
            color: #ffffff;
        }

        QMenu::item {
            padding: 4px 20px;
        }

        QMenu::item:selected {
            background-color: #505050;
        }

        QListWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            background-color: #353535;
            color: #ffffff;
        }

        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 2px;
        }
        """

    def _get_light_palette(self) -> QPalette:
        """Get light theme palette."""
        palette = QPalette()

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))

        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))

        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(51, 51, 51))

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        return palette

    def _get_dark_palette(self) -> QPalette:
        """Get dark theme palette."""
        palette = QPalette()

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))

        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(64, 64, 64))

        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(64, 64, 64))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        return palette

    @property
    def current_theme(self) -> Theme:
        """Get the current theme."""
        return self._current_theme

    def set_theme(self, theme: Theme) -> None:
        """Set the application theme."""
        if theme not in self._themes:
            raise ValueError(f"Unknown theme: {theme}")

        self._current_theme = theme
        app = QApplication.instance()
        if app:
            # Apply stylesheet
            app.setStyleSheet(self._themes[theme]["stylesheet"])

            # Apply palette
            app.setPalette(self._themes[theme]["palette"])

            # Emit signal
            self.theme_changed.emit(theme.value)

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        new_theme = Theme.DARK if self._current_theme == Theme.LIGHT else Theme.LIGHT
        self.set_theme(new_theme)

    def get_theme_name(self, theme: Theme) -> str:
        """Get a human-readable theme name."""
        return {Theme.LIGHT: "Light", Theme.DARK: "Dark"}.get(theme, "Unknown")


# Global theme manager instance
theme_manager = ThemeManager()
