"""
Theme Management Engine for Forge Hub.

Coordinates active palettes, native Qt palettes, and dynamic theme switching
signals without costly application-wide style re-initialization.
"""

import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.core.palette import (
    ColorPalette,
    DARK_PALETTE,
    LIGHT_PALETTE,
    get_palette,
    create_qpalette,
    resolve_system_theme
)
from app.core.config import load_config, save_config

logger = logging.getLogger("ForgeHub.Theme")


class ThemeManager(QObject):
    """
    Singleton dispatcher that alerts UI components when the active theme changes.
    Emits (theme_name: str, palette: ColorPalette).
    """
    theme_changed = Signal(str, object)
    palette_changed = Signal(object)

    def __init__(self):
        super().__init__()
        self._current_theme_name = "dark"
        self._current_palette = DARK_PALETTE

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name

    @property
    def current_palette(self) -> ColorPalette:
        return self._current_palette

    def set_active(self, theme_name: str, palette: ColorPalette):
        self._current_theme_name = theme_name
        self._current_palette = palette
        self.theme_changed.emit(theme_name, palette)
        self.palette_changed.emit(palette)


# Global singleton instance
theme_manager = ThemeManager()


def get_current_palette() -> ColorPalette:
    """Returns the currently active ColorPalette instance."""
    return theme_manager.current_palette


def get_current_theme_name() -> str:
    """Returns the name of the current theme ('dark', 'light', 'system')."""
    return theme_manager.current_theme_name


def init_theme(app: QApplication, theme_name: str = "system") -> ColorPalette:
    """
    Called ONCE at application boot to configure Qt's Fusion style base
    and apply the stored user theme. Avoids repeated setStyle calls.
    """
    try:
        app.setStyle("Fusion")
        app.setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 0.4);
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(148, 163, 184, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(148, 163, 184, 0.4);
                border-radius: 3px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(148, 163, 184, 0.7);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
    except Exception as e:
        logger.warning(f"Failed to set Fusion style: {e}")

    return apply_theme(app, theme_name, persist=False)


def apply_theme(app: QApplication, theme_name: str, persist: bool = True) -> ColorPalette:
    """
    Switches active color theme immediately (single-digit milliseconds, 0 lag).
    Updates QPalette and broadcasts theme_changed signal to all open windows/pages.
    """
    theme_key = (theme_name or "dark").strip().lower()
    palette = get_palette(theme_key)

    # 1. Update native Qt Application Palette
    if app:
        try:
            qp = create_qpalette(palette)
            app.setPalette(qp)
        except Exception as e:
            logger.error(f"Error setting app palette: {e}")

    # 2. Dispatch theme change to all listeners
    theme_manager.set_active(theme_key, palette)

    # 3. Persist to config.json
    if persist:
        try:
            cfg = load_config()
            cfg["theme"] = theme_key
            save_config(cfg)
        except Exception as e:
            logger.warning(f"Could not persist theme config: {e}")

    logger.info(f"Theme switched to: '{theme_key}' ({'Dark' if palette.is_dark else 'Light'})")
    return palette
