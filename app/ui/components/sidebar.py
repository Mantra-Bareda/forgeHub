import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QButtonGroup, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QCursor, QPixmap
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


from app.core.palette import ColorPalette, get_current_palette
from app.core.theme import theme_manager


class NavButton(QPushButton):
    def __init__(self, text, icon_name, index, palette: ColorPalette = None):
        super().__init__()
        self.index = index
        self.icon_name = icon_name
        self.nav_text = text
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setText(f"  {text}")
        self._palette = palette or get_current_palette()
        self.update_theme(self._palette)

    def update_theme(self, palette: ColorPalette):
        self._palette = palette
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                color: {palette.fg_muted};
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
            }}
            QPushButton:hover {{
                background-color: {palette.bg_surface_hover};
                color: {palette.fg_primary};
            }}
            QPushButton:checked {{
                background-color: {palette.accent_bg};
                color: {palette.accent};
                font-weight: 600;
                border-left: 3px solid {palette.accent};
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
            }}
        """)
        self.update_icon(self.isChecked())

    def update_icon(self, is_checked):
        pal = self._palette if hasattr(self, "_palette") and self._palette else get_current_palette()
        color = pal.accent if is_checked else pal.fg_muted
        self.setIcon(get_svg_icon(self.icon_name, color, 18))


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self.setObjectName("sidebarWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(6)

        # 1. Header: Brand Logo + Version
        self.brand_box = QFrame()
        bb_layout = QHBoxLayout(self.brand_box)
        bb_layout.setContentsMargins(4, 0, 4, 4)
        bb_layout.setSpacing(10)

        self.logo_box = QFrame()
        self.logo_box.setFixedSize(40, 40)
        lb_layout = QVBoxLayout(self.logo_box)
        lb_layout.setContentsMargins(0, 0, 0, 0)
        lb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.term_icon = QLabel()
        self.term_icon.setFixedSize(36, 36)
        self.term_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lb_layout.addWidget(self.term_icon)
        bb_layout.addWidget(self.logo_box)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        self.brand_name = QLabel("ForgeHub")
        text_col.addWidget(self.brand_name)


        bb_layout.addLayout(text_col)
        bb_layout.addStretch()
        layout.addWidget(self.brand_box)

        # 2. Navigation List in Scroll Area
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons = []

        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        nav_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #60a5fa;
            }
        """)

        self.nav_scroll = nav_scroll
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        nav_items = [
            ("Dashboard", "dashboard", 0),
            ("Projects", "folder", 1),
            ("Profile", "badge", 2),
            ("LinkedIn", "share", 8),
            ("GitHub", "code", 9),
            ("Memory", "brain", 4),
            ("Content", "article", 3),
            ("AI Chat", "chat", 5),
            ("AI Providers", "hub", 6),
            ("Settings", "settings", 7),
        ]

        for text, icon_name, index in nav_items:
            btn = NavButton(text, icon_name, index)
            btn.clicked.connect(lambda _, idx=index: self._on_btn_clicked(idx))
            nav_layout.addWidget(btn)
            self.button_group.addButton(btn, index)
            self.buttons.append(btn)

        nav_layout.addStretch()
        self.nav_scroll.setWidget(nav_container)
        layout.addWidget(self.nav_scroll, stretch=1)

        # 3. Bottom Card: Personal Workspace Synced
        self.footer_card = QFrame()
        fc_layout = QHBoxLayout(self.footer_card)
        fc_layout.setContentsMargins(10, 8, 10, 8)
        fc_layout.setSpacing(10)

        self.cloud_icon = QLabel()
        self.cloud_icon.setStyleSheet("background: transparent; border: none;")
        fc_layout.addWidget(self.cloud_icon)

        ws_col = QVBoxLayout()
        ws_col.setContentsMargins(0, 0, 0, 0)
        ws_col.setSpacing(1)

        self.ws_title = QLabel("Personal Workspace")
        ws_col.addWidget(self.ws_title)

        self.ws_sub = QLabel("Synced")
        ws_col.addWidget(self.ws_sub)
        fc_layout.addLayout(ws_col, 1)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        fc_layout.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.footer_card)

        # Apply initial theme & register listener
        self.apply_theme_colors(get_current_palette())
        theme_manager.theme_changed.connect(lambda name, pal: self.apply_theme_colors(pal))

        # Default select Dashboard
        if self.buttons:
            self.buttons[0].setChecked(True)
            self.buttons[0].update_icon(True)

    def apply_theme_colors(self, palette: ColorPalette):
        self.setStyleSheet(f"""
            QWidget#sidebarWidget {{
                background-color: {palette.bg_sidebar};
                border-right: 1px solid {palette.border_subtle};
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        if hasattr(self, "brand_box"):
            self.brand_box.setStyleSheet(f"background: transparent; border-bottom: 1px solid {palette.border_subtle}; padding-bottom: 12px; margin-bottom: 4px;")
            self.logo_box.setStyleSheet(f"background: transparent;")
            logo_path = os.path.abspath("forge_hub_logo.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.term_icon.setPixmap(pixmap)
            else:
                self.term_icon.setPixmap(get_svg_pixmap("terminal", palette.accent, 16))
            self.brand_name.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {palette.fg_primary}; letter-spacing: -0.2px; background: transparent; border: none;")
        if hasattr(self, "nav_scroll"):
            self.nav_scroll.setStyleSheet(f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: transparent;
                    width: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {palette.scrollbar_thumb};
                    border-radius: 2px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {palette.accent};
                }}
            """)
        if hasattr(self, "footer_card"):
            self.footer_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {palette.bg_card_inner};
                    border: 1px solid {palette.border_subtle};
                    border-radius: 8px;
                }}
                QLabel {{
                    background: transparent;
                }}
            """)
            self.cloud_icon.setPixmap(get_svg_pixmap("cloud", palette.fg_muted, 18))
            self.ws_title.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {palette.fg_secondary}; background: transparent; border: none;")
            self.ws_sub.setStyleSheet(f"font-size: 11px; color: {palette.fg_muted}; background: transparent; border: none;")
            self.status_dot.setStyleSheet(f"background-color: {palette.success}; border-radius: 4px;")
        if hasattr(self, "buttons"):
            for btn in self.buttons:
                btn.update_theme(palette)

    def _on_btn_clicked(self, index):
        for btn in self.buttons:
            btn.update_icon(btn.isChecked())
        self.page_selected.emit(index)

    def select_page(self, index):
        for btn in self.buttons:
            if btn.index == index:
                btn.setChecked(True)
                btn.update_icon(True)
            else:
                btn.update_icon(False)

    def minimumSizeHint(self):
        return QSize(240, 180)
