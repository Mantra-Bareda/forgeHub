"""
Universal Color Palette System for Forge Hub.

This module is the single source of truth for all application colors.
It defines:
- DarkPalette: Deep high-contrast obsidian & slate workstation theme.
- LightPalette: Soft, clean, high-contrast daylight theme with elevated cards.
- Token mappings for backgrounds, foregrounds/text, borders, accents, and status indicators.
"""

from dataclasses import dataclass
from typing import Dict
from PySide6.QtGui import QColor, QPalette, QGuiApplication
from PySide6.QtCore import Qt


@dataclass(frozen=True)
class ColorPalette:
    name: str
    is_dark: bool

    # --- Backgrounds ---
    bg_app: str             # Master application canvas & main window
    bg_sidebar: str         # Left navigation sidebar
    bg_surface: str         # Primary card and container surfaces
    bg_surface_hover: str   # Card and button hover states
    bg_surface_active: str  # Selected/pressed element fills
    bg_card: str            # Elevated content cards
    bg_card_inner: str      # Nested panels, parameter boxes, inner wells
    bg_input: str           # Line edits, text editors, dropdowns
    bg_badge: str           # Status badges and pill backgrounds
    bg_dialog: str          # Modal dialog backgrounds
    bg_tooltip: str         # Tooltip popup background

    # --- Foregrounds / Typography ---
    fg_primary: str         # High-contrast headings and primary text
    fg_secondary: str       # Subtitles, prominent labels, body text
    fg_muted: str           # Helper text, secondary descriptors, inactive icons
    fg_dim: str             # Timestamps, footnotes, subtle placeholders
    fg_inverse: str         # Text on opposing contrast backgrounds

    # --- Borders & Dividers ---
    border_subtle: str      # Subtle dividers and low-contrast borders
    border_card: str        # Standard container and card strokes
    border_focus: str       # Focus rings and active card borders
    border_divider: str     # Section divider lines

    # --- Primary Brand Accent ---
    accent: str             # Primary brand color (vibrant blue)
    accent_hover: str       # Accent button hover state
    accent_pressed: str     # Accent button pressed state
    accent_bg: str          # Subtle translucent accent wash (10-15%)
    accent_fg: str          # Text and icons rendered atop solid accent

    # --- Status / Semantic Colors ---
    success: str            # Valid / connected / active green
    success_bg: str         # Subtle green background wash
    success_border: str     # Green border accent
    warning: str            # Caution / rate-limit amber
    warning_bg: str         # Subtle amber background wash
    warning_border: str     # Amber border accent
    danger: str             # Error / irreversible purge red
    danger_bg: str          # Subtle red background wash
    danger_border: str      # Red border stroke
    danger_hover: str       # Red button hover state
    danger_fg: str          # Text rendered on danger button

    # --- Scrollbars ---
    scrollbar_track: str    # Scrollbar track background
    scrollbar_thumb: str    # Scrollbar thumb handle
    scrollbar_thumb_hover: str  # Scrollbar thumb handle hover state


# -----------------------------------------------------------------------------
# 1. Dark Palette (Workstation High-Contrast Canvas)
# -----------------------------------------------------------------------------
DARK_PALETTE = ColorPalette(
    name="dark",
    is_dark=True,

    # Backgrounds
    bg_app="#080A12",             # PRIMARY BACKGROUND
    bg_sidebar="#10131F",         # SIDEBAR / SURFACE
    bg_surface="#10131F",         # PRIMARY SURFACE
    bg_surface_hover="#1C2032",   # SURFACE HOVER
    bg_surface_active="#20253A",  # SURFACE ACTIVE
    bg_card="#10131F",            # CARD
    bg_card_inner="#080A12",      # BACKGROUND (Inner)
    bg_input="#10131F",           # SURFACE (Input)
    bg_badge="#171A29",           # ELEVATED SURFACE
    bg_dialog="#171A29",          # DIALOG_BACKGROUND
    bg_tooltip="#171A29",         # DIALOG_ELEVATED

    # Typography
    fg_primary="#F4F5F7",         # TEXT PRIMARY
    fg_secondary="#A7ACBA",       # TEXT SECONDARY
    fg_muted="#6B7280",           # TEXT MUTED
    fg_dim="#4B5060",             # TEXT DISABLED
    fg_inverse="#FFFFFF",         # TEXT ON ACCENT

    # Borders
    border_subtle="#1D2130",      # BORDER SUBTLE
    border_card="#292D42",        # BORDER
    border_focus="#6D4AFF",       # BORDER FOCUS
    border_divider="#1D2130",     # BORDER SUBTLE

    # Brand Accent
    accent="#8B5CF6",             # PRIMARY VIOLET
    accent_hover="#A78BFA",       # PRIMARY HOVER
    accent_pressed="#7C3AED",     # PRIMARY PRESSED
    accent_bg="rgba(139, 92, 246, 0.10)",  # PRIMARY SOFT (#8B5CF61A)
    accent_fg="#FFFFFF",          # TEXT ON ACCENT

    # Semantics (Strictly mapped to the new specification)
    success="#34D399",
    success_bg="rgba(52, 211, 153, 0.10)",
    success_border="#1D2130",
    warning="#FBBF24",
    warning_bg="rgba(251, 191, 36, 0.10)",
    warning_border="#1D2130",
    danger="#FB7185",
    danger_bg="rgba(251, 113, 133, 0.10)",
    danger_border="#FB7185",
    danger_hover="#e11d48",
    danger_fg="#FFFFFF",

    # Scrollbars
    scrollbar_track="transparent",
    scrollbar_thumb="#292D42",
    scrollbar_thumb_hover="#4B5060",
)


# -----------------------------------------------------------------------------
# 2. Light Palette (Soft, Daylight High-Contrast Canvas)
# -----------------------------------------------------------------------------
LIGHT_PALETTE = ColorPalette(
    name="light",
    is_dark=True, # It's visually a dark theme, despite being loaded in the 'light' slot

    # Backgrounds
    bg_app="#0B0B0D",             # BACKGROUND
    bg_sidebar="#131316",         # SURFACE
    bg_surface="#131316",         # SURFACE
    bg_surface_hover="#202025",   # SURFACE HOVER
    bg_surface_active="#25252B",  # SURFACE ACTIVE
    bg_card="#131316",            # SURFACE
    bg_card_inner="#0B0B0D",      # BACKGROUND
    bg_input="#131316",           # SURFACE
    bg_badge="#1B1B20",           # SURFACE ELEVATED
    bg_dialog="#1B1B20",          # SURFACE ELEVATED
    bg_tooltip="#1B1B20",         # SURFACE ELEVATED

    # Typography
    fg_primary="#F5F3EE",         # TEXT PRIMARY
    fg_secondary="#A6A4A0",       # TEXT SECONDARY
    fg_muted="#6F6D69",           # TEXT MUTED
    fg_dim="#4A4947",             # TEXT DISABLED
    fg_inverse="#15130F",         # TEXT ON ACCENT

    # Borders
    border_subtle="#202025",      # BORDER SUBTLE
    border_card="#2A2A30",        # BORDER
    border_focus="#C9A45C",       # BORDER FOCUS
    border_divider="#202025",     # BORDER SUBTLE

    # Brand Accent
    accent="#D4AF6A",             # PRIMARY GOLD
    accent_hover="#E5C27A",       # PRIMARY HOVER
    accent_pressed="#B89552",     # PRIMARY PRESSED
    accent_bg="rgba(212, 175, 106, 0.10)", # PRIMARY SOFT
    accent_fg="#15130F",          # TEXT ON ACCENT

    # Semantics
    success="#6FCF97",
    success_bg="rgba(111, 207, 151, 0.10)",
    success_border="#202025",
    warning="#E8B86A",
    warning_bg="rgba(232, 184, 106, 0.10)",
    warning_border="#202025",
    danger="#E57373",
    danger_bg="rgba(229, 115, 115, 0.10)",
    danger_border="#E57373",
    danger_hover="#ef5350",
    danger_fg="#F5F3EE",

    # Scrollbars
    scrollbar_track="transparent",
    scrollbar_thumb="#2A2A30",
    scrollbar_thumb_hover="#4A4947",
)


# Registry of palettes
PALETTES: Dict[str, ColorPalette] = {
    "dark": DARK_PALETTE,
    "light": LIGHT_PALETTE,
}


def resolve_system_theme() -> str:
    """Detects whether the operating system prefers dark or light mode."""
    try:
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorScheme"):
            cs = hints.colorScheme()
            if cs == Qt.ColorScheme.Light:
                return "light"
            elif cs == Qt.ColorScheme.Dark:
                return "dark"
    except Exception:
        pass
    # Workstation default
    return "dark"


def get_palette(theme_name: str = "dark") -> ColorPalette:
    """Retrieves a ColorPalette instance by theme key ('dark', 'light', 'system')."""
    normalized = (theme_name or "dark").strip().lower()
    if normalized == "system":
        resolved = resolve_system_theme()
        return PALETTES.get(resolved, DARK_PALETTE)
    return PALETTES.get(normalized, DARK_PALETTE)


def create_qpalette(palette: ColorPalette) -> QPalette:
    """Constructs a native PySide6 QPalette corresponding to the ColorPalette."""
    qp = QPalette()
    qp.setColor(QPalette.ColorRole.Window, QColor(palette.bg_app))
    qp.setColor(QPalette.ColorRole.WindowText, QColor(palette.fg_primary))
    qp.setColor(QPalette.ColorRole.Base, QColor(palette.bg_surface))
    qp.setColor(QPalette.ColorRole.AlternateBase, QColor(palette.bg_card_inner))
    qp.setColor(QPalette.ColorRole.ToolTipText, QColor(palette.fg_inverse if palette.is_dark else "#ffffff"))
    qp.setColor(QPalette.ColorRole.Text, QColor(palette.fg_primary))
    qp.setColor(QPalette.ColorRole.Button, QColor(palette.bg_surface))
    qp.setColor(QPalette.ColorRole.ButtonText, QColor(palette.fg_primary))
    qp.setColor(QPalette.ColorRole.BrightText, QColor(palette.danger))
    qp.setColor(QPalette.ColorRole.Link, QColor(palette.accent))
    qp.setColor(QPalette.ColorRole.Highlight, QColor(palette.accent))
    qp.setColor(QPalette.ColorRole.HighlightedText, QColor(palette.accent_fg))
    return qp


def get_current_palette() -> ColorPalette:
    """Convenience accessor to get the active palette from theme_manager."""
    from app.core.theme import theme_manager
    return theme_manager.current_palette
