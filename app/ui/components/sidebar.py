from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QButtonGroup
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


class NavButton(QPushButton):
    def __init__(self, text, icon_name, index):
        super().__init__()
        self.index = index
        self.icon_name = icon_name
        self.nav_text = text
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setText(f"  {text}")
        self.update_icon(False)

        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f1f5f9;
            }
            QPushButton:checked {
                background-color: rgba(37, 99, 235, 0.15);
                color: #60a5fa;
                font-weight: 600;
            }
        """)

    def update_icon(self, is_checked):
        color = "#60a5fa" if is_checked else "#94a3b8"
        self.setIcon(get_svg_icon(self.icon_name, color, 18))


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.setObjectName("sidebarWidget")
        self.setStyleSheet("""
            QWidget#sidebarWidget {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            QLabel {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # 1. Header: Brand Logo + Version
        brand_box = QFrame()
        brand_box.setStyleSheet("background: transparent; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 6px;")
        bb_layout = QHBoxLayout(brand_box)
        bb_layout.setContentsMargins(4, 0, 4, 4)
        bb_layout.setSpacing(10)

        logo_box = QFrame()
        logo_box.setFixedSize(30, 30)
        logo_box.setStyleSheet("background-color: rgba(37, 99, 235, 0.2); border-radius: 6px;")
        lb_layout = QVBoxLayout(logo_box)
        lb_layout.setContentsMargins(0, 0, 0, 0)
        lb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        term_icon = QLabel()
        term_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        term_icon.setPixmap(get_svg_pixmap("terminal", "#60a5fa", 16))
        lb_layout.addWidget(term_icon)
        bb_layout.addWidget(logo_box)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        brand_name = QLabel("Forge Hub")
        brand_name.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.2px; background: transparent; border: none;")
        text_col.addWidget(brand_name)

        version_lbl = QLabel("v2.4.0 • Workstation")
        version_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
        text_col.addWidget(version_lbl)

        bb_layout.addLayout(text_col)
        bb_layout.addStretch()
        layout.addWidget(brand_box)

        # 2. Navigation List
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons = []

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
            layout.addWidget(btn)
            self.button_group.addButton(btn, index)
            self.buttons.append(btn)

        layout.addStretch()

        # 3. Bottom Card: Personal Workspace Synced
        footer_card = QFrame()
        footer_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(51, 65, 85, 0.4);
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
            }
        """)
        fc_layout = QHBoxLayout(footer_card)
        fc_layout.setContentsMargins(10, 8, 10, 8)
        fc_layout.setSpacing(10)

        cloud_icon = QLabel()
        cloud_icon.setPixmap(get_svg_pixmap("cloud", "#94a3b8", 18))
        cloud_icon.setStyleSheet("background: transparent; border: none;")
        fc_layout.addWidget(cloud_icon)

        ws_col = QVBoxLayout()
        ws_col.setContentsMargins(0, 0, 0, 0)
        ws_col.setSpacing(1)

        ws_title = QLabel("Personal Workspace")
        ws_title.setStyleSheet("font-size: 12px; font-weight: 500; color: #e2e8f0; background: transparent; border: none;")
        ws_col.addWidget(ws_title)

        ws_sub = QLabel("Synced")
        ws_sub.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
        ws_col.addWidget(ws_sub)
        fc_layout.addLayout(ws_col, 1)

        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet("background-color: #10b981; border-radius: 4px;")
        fc_layout.addWidget(status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(footer_card)

        # Default select Dashboard
        if self.buttons:
            self.buttons[0].setChecked(True)
            self.buttons[0].update_icon(True)

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
