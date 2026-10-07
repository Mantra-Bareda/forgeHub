"""
Dashboard Page for Forge Hub.
Provides overview metric cards, recent projects, recent achievements,
quick navigation shortcuts, and synchronized color palette support.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QScrollArea, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QCursor

from database.repository import ProjectRepository, ProfileRepository
from app.core.palette import ColorPalette
from app.core.theme import get_current_palette, theme_manager
from app.ui.components.icons import get_svg_pixmap, get_svg_icon
from app.ui.components.achievement_dialog import AchievementDialog


class StatCard(QFrame):
    clicked = Signal()

    def __init__(self, icon_name: str, icon_color: str, title: str, badge_text: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.default_icon_color = icon_color
        self.title_text = title
        self.badge_text = badge_text
        self.current_value = 0
        self.target_value = 0
        self.palette = get_current_palette()

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Top Row: Icon + Title on left, Badge on right
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent;")
        top_layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setMinimumWidth(0)
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()

        self.badge_lbl = QLabel(badge_text)
        self.badge_lbl.setMinimumWidth(0)
        top_layout.addWidget(self.badge_lbl)
        layout.addLayout(top_layout)

        # Middle: Animated Big Number
        self.val_lbl = QLabel("0")
        self.val_lbl.setMinimumWidth(0)
        layout.addWidget(self.val_lbl)

        # Bottom Row: Subtitle + Arrow
        bot_layout = QHBoxLayout()
        bot_layout.setContentsMargins(0, 4, 0, 0)

        self.bot_lbl = QLabel("")
        self.bot_lbl.setWordWrap(True)
        self.bot_lbl.setMinimumWidth(0)
        bot_layout.addWidget(self.bot_lbl, stretch=1)

        self.arrow_lbl = QLabel("→")
        bot_layout.addWidget(self.arrow_lbl)

        layout.addLayout(bot_layout)

        # Smooth counter animation
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.valueChanged.connect(self._on_count_step)
        self._anim.finished.connect(lambda: self.val_lbl.setText(str(self.target_value)))

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 8px;
            }}
            QFrame#statCard:hover {{
                background-color: {self.palette.bg_surface_hover};
                border: 1px solid {self.palette.border_focus};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
            }}
        """)

        self.icon_lbl.setPixmap(get_svg_pixmap(self.icon_name, self.default_icon_color, 18))
        self.title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {self.palette.fg_secondary}; background: transparent;")
        self.badge_lbl.setStyleSheet(f"""
            background-color: {self.palette.bg_badge};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 500;
            color: {self.palette.fg_muted};
        """)
        self.val_lbl.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: -0.5px; background: transparent;")
        self.bot_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")
        self.arrow_lbl.setStyleSheet(f"font-size: 14px; color: {self.palette.fg_dim}; font-weight: bold; background: transparent;")

    def enterEvent(self, event):
        self.arrow_lbl.setStyleSheet(f"font-size: 14px; color: {self.palette.fg_primary}; font-weight: bold; background: transparent;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.arrow_lbl.setStyleSheet(f"font-size: 14px; color: {self.palette.fg_dim}; font-weight: bold; background: transparent;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def update_stats(self, target_value: int, bottom_html: str, badge_text: Optional[str] = None, animate: bool = False):
        self.target_value = int(target_value)
        if badge_text:
            self.badge_lbl.setText(badge_text)
        self.bot_lbl.setText(bottom_html)

        if not animate or self.current_value == self.target_value:
            self.val_lbl.setText(str(self.target_value))
            self.current_value = self.target_value
            return

        self._anim.stop()
        self._anim.setDuration(220)
        self._anim.setStartValue(float(self.current_value))
        self._anim.setEndValue(float(self.target_value))
        self._anim.start()
        self.current_value = self.target_value

    def _on_count_step(self, val):
        self.val_lbl.setText(str(round(val)))


class ProjectRowWidget(QFrame):
    clicked = Signal(int)

    def __init__(self, project_data: Dict[str, Any], icon_name="layers", icon_color="#38bdf8", parent=None):
        super().__init__(parent)
        self.project_id = project_data.get("id", 0)
        self.icon_name = icon_name
        self.icon_color = icon_color
        self.project_data = project_data
        self.palette = get_current_palette()

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("projRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(10)

        # Icon box
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(34, 34)
        ib_layout = QVBoxLayout(self.icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent;")
        ib_layout.addWidget(self.icon_lbl)
        layout.addWidget(self.icon_box)

        # Name & Description
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name = project_data.get("name") or "Unnamed Project"
        self.name_lbl = QLabel(name)
        self.name_lbl.setMinimumWidth(0)
        info_layout.addWidget(self.name_lbl)

        desc = project_data.get("description") or "No description provided."
        desc = desc.split("\n")[0].strip()
        if len(desc) > 55:
            desc = desc[:52] + "..."
        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setMinimumWidth(0)
        info_layout.addWidget(self.desc_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Tech stack badge + status label
        stack_text = project_data.get("technology_stack") or "General"
        if len(stack_text) > 20:
            stack_text = stack_text[:18] + ".."
        self.stack_badge = QLabel(stack_text)
        self.stack_badge.setMinimumWidth(0)
        layout.addWidget(self.stack_badge)

        status_str = project_data.get("status") or "Active"
        self.status_lbl = QLabel(status_str)
        self.status_lbl.setMinimumWidth(0)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.status_lbl)

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            QFrame#projRow {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid transparent;
                border-radius: 8px;
            }}
            QFrame#projRow:hover {{
                background-color: {self.palette.bg_surface_hover};
                border: 1px solid {self.palette.border_subtle};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
                border: none;
            }}
        """)

        self.icon_box.setStyleSheet(f"background-color: {self.palette.bg_badge}; border-radius: 6px;")
        self.icon_lbl.setPixmap(get_svg_pixmap(self.icon_name, self.icon_color, 18))
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent;")
        self.desc_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")
        self.stack_badge.setStyleSheet(f"""
            background-color: {self.palette.bg_badge};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 500;
            color: {self.palette.fg_secondary};
        """)
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_id)
        super().mousePressEvent(event)


class AchievementRowWidget(QFrame):
    def __init__(self, ach_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.ach_data = ach_data
        self.palette = get_current_palette()

        self.setObjectName("achRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(10)

        ach_type = ach_data.get("type") or "Certificate"
        if ach_type == "Certificate":
            self.icon_name = "award"
            self.icon_color = "#34d399"
        elif ach_type == "Hackathon":
            self.icon_name = "trophy"
            self.icon_color = "#60a5fa"
        else:
            self.icon_name = "star"
            self.icon_color = "#818cf8"

        # Icon box
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(34, 34)
        ib_layout = QVBoxLayout(self.icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent;")
        ib_layout.addWidget(self.icon_lbl)
        layout.addWidget(self.icon_box)

        # Title & Description
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        title = ach_data.get("title") or "Untitled Achievement"
        self.title_lbl = QLabel(title)
        self.title_lbl.setMinimumWidth(0)
        info_layout.addWidget(self.title_lbl)

        desc = ach_data.get("description") or ""
        desc = desc.split("\n")[0].strip()
        if len(desc) > 55:
            desc = desc[:52] + "..."
        self.desc_lbl = QLabel(desc or "Recorded achievement milestone")
        self.desc_lbl.setMinimumWidth(0)
        info_layout.addWidget(self.desc_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Type badge + date
        self.badge_lbl = QLabel(ach_type)
        self.badge_lbl.setMinimumWidth(0)
        layout.addWidget(self.badge_lbl)

        date_str = str(ach_data.get("date_achieved") or ach_data.get("date") or "")
        self.date_lbl = QLabel(date_str)
        self.date_lbl.setMinimumWidth(0)
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.date_lbl)

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            QFrame#achRow {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid transparent;
                border-radius: 8px;
            }}
            QFrame#achRow:hover {{
                background-color: {self.palette.bg_surface_hover};
                border: 1px solid {self.palette.border_subtle};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
                border: none;
            }}
        """)

        self.icon_box.setStyleSheet(f"background-color: {self.palette.bg_badge}; border-radius: 6px;")
        self.icon_lbl.setPixmap(get_svg_pixmap(self.icon_name, self.icon_color, 18))
        self.title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent;")
        self.desc_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")

        ach_type = self.ach_data.get("type") or "Certificate"
        if ach_type == "Certificate":
            self.badge_lbl.setStyleSheet(f"background-color: {self.palette.success_bg}; color: {self.palette.success}; border: 1px solid {self.palette.success_border}; border-radius: 4px; padding: 2px 7px; font-size: 11px; font-weight: 500;")
        elif ach_type == "Hackathon":
            self.badge_lbl.setStyleSheet(f"background-color: {self.palette.accent_bg}; color: {self.palette.accent}; border: 1px solid {self.palette.accent}; border-radius: 4px; padding: 2px 7px; font-size: 11px; font-weight: 500;")
        else:
            self.badge_lbl.setStyleSheet(f"background-color: {self.palette.bg_badge}; color: {self.palette.fg_secondary}; border: 1px solid {self.palette.border_subtle}; border-radius: 4px; padding: 2px 7px; font-size: 11px; font-weight: 500;")

        self.date_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent;")


class DashboardPage(QWidget):
    navigate_requested = Signal(int)
    new_project_requested = Signal()
    open_project_requested = Signal(int)

    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.palette = get_current_palette()
        self.setObjectName("dashboardRoot")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area for responsive sizing
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 20, 24, 24)
        self.content_layout.setSpacing(16)

        # Build UI sections
        self._build_header()
        self._build_stats_section()
        self._build_activity_section()
        self._build_bottom_banner()

        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.viewport().installEventFilter(self)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(lambda min_val, max_val: self._update_content_width())
        root_layout.addWidget(self.scroll_area)

        # Apply universal palette
        self.apply_theme_colors(self.palette)

    def eventFilter(self, obj, event):
        if hasattr(self, "scroll_area") and obj == self.scroll_area.viewport() and event.type() == QEvent.Type.Resize:
            self._update_content_width()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_content_width()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
        self._update_content_width()

    def _update_content_width(self):
        if hasattr(self, "scroll_area") and hasattr(self, "content_widget"):
            vp_w = self.scroll_area.viewport().width()
            if vp_w > 50:
                self.content_widget.setMaximumWidth(vp_w)

    def _build_header(self):
        self.header_row = QHBoxLayout()
        self.header_row.setContentsMargins(0, 0, 0, 4)
        self.header_row.setSpacing(12)

        # Left: Title + Badge + Subtitle
        left_box = QVBoxLayout()
        left_box.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.title_lbl = QLabel("Dashboard")
        self.title_lbl.setMinimumWidth(0)
        title_row.addWidget(self.title_lbl)

        self.v_badge = QLabel("v2.4")
        title_row.addWidget(self.v_badge)
        title_row.addStretch()
        left_box.addLayout(title_row)

        self.subtitle_lbl = QLabel("Welcome to Forge Hub — Your Personal Professional AI Manager")
        self.subtitle_lbl.setMinimumWidth(0)
        self.subtitle_lbl.setWordWrap(True)
        self.subtitle_lbl.setMinimumWidth(1)
        left_box.addWidget(self.subtitle_lbl)
        self.header_row.addLayout(left_box, 1)

        # Right: Synced status pill + New Project button
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.synced_pill = QFrame()
        self.synced_pill.setFixedHeight(32)
        sp_layout = QHBoxLayout(self.synced_pill)
        sp_layout.setContentsMargins(10, 0, 10, 0)
        sp_layout.setSpacing(6)

        self.dot = QLabel()
        self.dot.setFixedSize(6, 6)
        sp_layout.addWidget(self.dot)

        self.sp_text = QLabel("Synced")
        sp_layout.addWidget(self.sp_text)
        actions_row.addWidget(self.synced_pill)

        self.new_proj_btn = QPushButton("New Project")
        self.new_proj_btn.setFixedHeight(32)
        self.new_proj_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.new_proj_btn.clicked.connect(self.new_project_requested.emit)
        actions_row.addWidget(self.new_proj_btn)

        self.header_row.addLayout(actions_row, 0)
        self.content_layout.addLayout(self.header_row)

    def _build_stats_section(self):
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(14)

        # Create the 3 persistent stat cards once
        self.card_projects = StatCard("folder", "#60a5fa", "Total Projects", "Active", parent=self.content_widget)
        self.card_projects.clicked.connect(lambda: self.navigate_requested.emit(1))

        self.card_skills = StatCard("brain", "#a78bfa", "Skills Tracked", "Verified", parent=self.content_widget)
        self.card_skills.clicked.connect(lambda: self.navigate_requested.emit(2))

        self.card_achievements = StatCard("verified", "#34d399", "Achievements", "Honors", parent=self.content_widget)
        self.card_achievements.clicked.connect(lambda: self.navigate_requested.emit(2))

        self.stats_layout.addWidget(self.card_projects)
        self.stats_layout.addWidget(self.card_skills)
        self.stats_layout.addWidget(self.card_achievements)
        self.content_layout.addLayout(self.stats_layout)

    def _build_activity_section(self):
        self.split_activity_layout = QHBoxLayout()
        self.split_activity_layout.setSpacing(14)

        # Left Column: Recent Projects Pane
        self.proj_pane = QFrame()
        self.proj_pane.setObjectName("projPane")
        self.proj_pane.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.proj_pane.setMinimumWidth(0)
        self.proj_pane_layout = QVBoxLayout(self.proj_pane)
        self.proj_pane_layout.setContentsMargins(14, 14, 14, 14)
        self.proj_pane_layout.setSpacing(10)

        proj_hdr = QHBoxLayout()
        self.proj_title_lbl = QLabel("Recent Projects")
        self.proj_title_lbl.setMinimumWidth(0)
        proj_hdr.addWidget(self.proj_title_lbl)

        self.proj_count_badge = QLabel("0")
        proj_hdr.addWidget(self.proj_count_badge)
        proj_hdr.addStretch()

        self.view_all_btn = QPushButton("View all →")
        self.view_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.view_all_btn.clicked.connect(lambda: self.navigate_requested.emit(1))
        proj_hdr.addWidget(self.view_all_btn)
        self.proj_pane_layout.addLayout(proj_hdr)

        self.proj_rows_layout = QVBoxLayout()
        self.proj_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.proj_rows_layout.setSpacing(6)
        self.proj_pane_layout.addLayout(self.proj_rows_layout)
        self.proj_pane_layout.addStretch()

        # Right Column: Recent Achievements Pane
        self.ach_pane = QFrame()
        self.ach_pane.setObjectName("achPane")
        self.ach_pane.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.ach_pane.setMinimumWidth(0)
        self.ach_pane_layout = QVBoxLayout(self.ach_pane)
        self.ach_pane_layout.setContentsMargins(14, 14, 14, 14)
        self.ach_pane_layout.setSpacing(10)

        ach_hdr = QHBoxLayout()
        self.ach_title_lbl = QLabel("Recent Achievements")
        self.ach_title_lbl.setMinimumWidth(0)
        ach_hdr.addWidget(self.ach_title_lbl)

        self.ach_count_badge = QLabel("0")
        ach_hdr.addWidget(self.ach_count_badge)
        ach_hdr.addStretch()

        self.manage_btn = QPushButton("Manage")
        self.manage_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.manage_btn.clicked.connect(lambda: self.navigate_requested.emit(2))
        ach_hdr.addWidget(self.manage_btn)
        self.ach_pane_layout.addLayout(ach_hdr)

        self.ach_rows_layout = QVBoxLayout()
        self.ach_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ach_rows_layout.setSpacing(6)
        self.ach_pane_layout.addLayout(self.ach_rows_layout)
        self.ach_pane_layout.addStretch()

        # Dashed Add Entry Row
        self.add_entry_card = QFrame()
        self.add_entry_card.setFixedHeight(40)
        self.add_entry_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ae_layout = QHBoxLayout(self.add_entry_card)
        ae_layout.setContentsMargins(12, 0, 12, 0)
        ae_layout.setSpacing(8)

        self.plus_icon = QLabel()
        ae_layout.addWidget(self.plus_icon)

        self.ae_text = QLabel("Add new certification, award, or milestone...")
        ae_layout.addWidget(self.ae_text)
        ae_layout.addStretch()

        self.ae_btn_label = QLabel("Add Entry")
        ae_layout.addWidget(self.ae_btn_label)

        self.add_entry_card.mousePressEvent = lambda e: self._on_add_achievement_clicked()
        self.ach_pane_layout.addWidget(self.add_entry_card)

        self.split_activity_layout.addWidget(self.proj_pane, 1)
        self.split_activity_layout.addWidget(self.ach_pane, 1)
        self.content_layout.addLayout(self.split_activity_layout)

    def _build_bottom_banner(self):
        self.banner = QFrame()
        self.banner.setMinimumWidth(0)
        b_layout = QHBoxLayout(self.banner)
        b_layout.setContentsMargins(16, 10, 16, 10)
        b_layout.setSpacing(10)

        self.info_icon = QLabel()
        self.info_icon.setStyleSheet("background: transparent;")
        b_layout.addWidget(self.info_icon)

        self.info_text = QLabel("Navigate using the sidebar to manage your projects, professional profile, AI providers, and knowledge base.")
        self.info_text.setWordWrap(True)
        self.info_text.setMinimumWidth(0)
        b_layout.addWidget(self.info_text, stretch=1)

        # Keyboard shortcuts
        self.kbd_layout = QHBoxLayout()
        self.kbd_layout.setSpacing(6)

        def make_kbd(key: str) -> QLabel:
            lbl = QLabel(key)
            lbl.setProperty("is_kbd", True)
            return lbl

        self.k1 = make_kbd("Ctrl")
        self.p1 = QLabel("+")
        self.k2 = make_kbd("K")
        self.t1 = QLabel("Palette")
        self.dot_sep = QLabel("•")
        self.k3 = make_kbd("Ctrl")
        self.p2 = QLabel("+")
        self.k4 = make_kbd("P")
        self.t2 = QLabel("Switch")

        self.kbd_layout.addWidget(self.k1)
        self.kbd_layout.addWidget(self.p1)
        self.kbd_layout.addWidget(self.k2)
        self.kbd_layout.addWidget(self.t1)
        self.kbd_layout.addWidget(self.dot_sep)
        self.kbd_layout.addWidget(self.k3)
        self.kbd_layout.addWidget(self.p2)
        self.kbd_layout.addWidget(self.k4)
        self.kbd_layout.addWidget(self.t2)

        b_layout.addLayout(self.kbd_layout)
        self.content_layout.addWidget(self.banner)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal

        self.setStyleSheet(f"""
            #dashboardRoot {{
                background-color: {self.palette.bg_app};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
            }}
        """)

        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.palette.bg_app};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.palette.scrollbar_track};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.palette.scrollbar_thumb};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.palette.scrollbar_thumb_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.content_widget.setStyleSheet(f"background-color: {self.palette.bg_app};")

        # Header
        self.title_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: -0.5px; background: transparent;")
        self.v_badge.setStyleSheet(f"""
            background-color: {self.palette.bg_badge};
            color: {self.palette.fg_muted};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 500;
        """)
        self.subtitle_lbl.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_muted}; background: transparent;")

        self.synced_pill.setStyleSheet(f"""
            background-color: {self.palette.bg_badge};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 6px;
        """)
        self.dot.setStyleSheet(f"background-color: {self.palette.success}; border-radius: 3px;")
        self.sp_text.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {self.palette.fg_secondary}; background: transparent;")

        self.new_proj_btn.setIcon(get_svg_icon("plus", pal.accent_fg, 14))
        self.new_proj_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                color: {self.palette.accent_fg};
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent_hover};
            }}
            QPushButton:pressed {{
                background-color: {self.palette.accent_pressed};
            }}
        """)

        # Stat cards
        self.card_projects.apply_theme_colors(pal)
        self.card_skills.apply_theme_colors(pal)
        self.card_achievements.apply_theme_colors(pal)

        # Activity panes
        self.proj_pane.setStyleSheet(f"""
            QFrame#projPane {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
                border: none;
            }}
        """)
        self.ach_pane.setStyleSheet(f"""
            QFrame#achPane {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
                border: none;
            }}
        """)

        badge_style = f"background-color: {self.palette.bg_badge}; color: {self.palette.fg_secondary}; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: 500; border: 1px solid {self.palette.border_subtle};"
        self.proj_title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent;")
        self.proj_count_badge.setStyleSheet(badge_style)
        self.view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {self.palette.accent};
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {self.palette.accent_hover};
            }}
        """)

        self.ach_title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent;")
        self.ach_count_badge.setStyleSheet(badge_style)
        self.manage_btn.setIcon(get_svg_icon("tune", pal.fg_muted, 14))
        self.manage_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {self.palette.fg_muted};
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {self.palette.fg_primary};
            }}
        """)

        # Dashed entry card
        self.add_entry_card.setStyleSheet(f"""
            QFrame {{
                border: 1px dashed {self.palette.border_focus};
                border-radius: 8px;
                background-color: {self.palette.bg_card_inner};
            }}
            QFrame:hover {{
                border-color: {self.palette.accent};
                background-color: {self.palette.bg_surface_hover};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
            }}
        """)
        self.plus_icon.setPixmap(get_svg_pixmap("add_circle", pal.fg_dim, 16))
        self.ae_text.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")
        self.ae_btn_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.accent}; background: transparent;")

        # Bottom banner
        self.banner.setStyleSheet(f"""
            background-color: {self.palette.bg_card};
            border: 1px solid {self.palette.border_card};
            border-radius: 8px;
        """)
        self.info_icon.setPixmap(get_svg_pixmap("info", pal.fg_muted, 18))
        self.info_text.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")

        kbd_style = f"""
            background-color: {self.palette.bg_badge};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 11px;
            color: {self.palette.fg_secondary};
        """
        for k in (self.k1, self.k2, self.k3, self.k4):
            k.setStyleSheet(kbd_style)

        sub_style = f"color: {self.palette.fg_dim}; font-size: 11px; background: transparent;"
        self.p1.setStyleSheet(sub_style)
        self.p2.setStyleSheet(sub_style)
        self.t1.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 11px; background: transparent;")
        self.t2.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 11px; background: transparent;")
        self.dot_sep.setStyleSheet(f"color: {self.palette.border_card}; font-size: 12px; margin: 0 4px; background: transparent;")

        # Update existing project and achievement rows if any
        for i in range(self.proj_rows_layout.count()):
            item = self.proj_rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), "apply_theme_colors"):
                item.widget().apply_theme_colors(pal)

        for i in range(self.ach_rows_layout.count()):
            item = self.ach_rows_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), "apply_theme_colors"):
                item.widget().apply_theme_colors(pal)

    def _on_add_achievement_clicked(self):
        if not self.db:
            return
        dlg = AchievementDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            prof_repo = ProfileRepository(self.db)
            prof_repo.add_achievement(data["title"], data["description"], data["date"], data["type"])
            self.refresh_data()

    def refresh_data(self):
        projects: List[Dict[str, Any]] = []
        skills: List[Dict[str, Any]] = []
        achievements: List[Dict[str, Any]] = []

        if self.db:
            try:
                proj_repo = ProjectRepository(self.db)
                projects = proj_repo.get_projects()
                prof_repo = ProfileRepository(self.db)
                skills = prof_repo.get_skills()
                achievements = prof_repo.get_achievements()
            except Exception:
                pass

        pal = self.palette

        # 1. Update Persistent Stat Cards without rebuilding widgets
        active_proj = sum(1 for p in projects if p.get("status") in ("In Progress", "Planning", "Active", None))
        other_proj = len(projects) - active_proj
        self.card_projects.update_stats(
            len(projects),
            f"<span style='color:{self.palette.success};'>●</span> {active_proj} Active <span style='color:{self.palette.fg_dim};'>•</span> {other_proj} Other",
            "Active"
        )

        verified_skills = sum(1 for s in skills if str(s.get("level")).lower() in ("advanced", "expert", "verified"))
        dev_skills = len(skills) - verified_skills
        self.card_skills.update_stats(
            len(skills),
            f"<span style='color:{self.palette.accent};'>●</span> {verified_skills} Verified <span style='color:{self.palette.fg_dim};'>•</span> {dev_skills} Developing",
            "Verified"
        )

        latest_ach_title = achievements[0].get("title", "None") if achievements else "No entries yet"
        if len(latest_ach_title) > 24:
            latest_ach_title = latest_ach_title[:22] + "..."
        self.card_achievements.update_stats(
            len(achievements),
            f"Latest: <span style='color:{self.palette.fg_primary}; font-weight:500;'>{latest_ach_title}</span>",
            "Honors"
        )

        # 2. Cleanly clear and populate Projects List
        while self.proj_rows_layout.count():
            item = self.proj_rows_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        self.proj_count_badge.setText(str(len(projects)))

        icon_cycle = [
            ("layers", "#38bdf8"),
            ("database", "#34d399"),
            ("sync", "#818cf8"),
            ("share", "#60a5fa"),
            ("analytics", "#f43f5e")
        ]

        if not projects:
            empty_box = QFrame()
            empty_box.setStyleSheet("background: transparent; border: none;")
            eb_layout = QVBoxLayout(empty_box)
            eb_layout.setContentsMargins(0, 30, 0, 30)
            eb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_lbl = QLabel("No projects created yet. Click '+ New Project' to get started.")
            empty_lbl.setStyleSheet(f"color: {self.palette.fg_dim}; font-size: 13px; font-style: italic; background: transparent;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            eb_layout.addWidget(empty_lbl)
            self.proj_rows_layout.addWidget(empty_box)
        else:
            for idx, p in enumerate(projects[:5]):
                iname, icolor = icon_cycle[idx % len(icon_cycle)]
                row = ProjectRowWidget(p, iname, icolor, parent=self.proj_pane)
                row.clicked.connect(self.open_project_requested.emit)
                self.proj_rows_layout.addWidget(row)

        # 3. Cleanly clear and populate Achievements List
        while self.ach_rows_layout.count():
            item = self.ach_rows_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        self.ach_count_badge.setText(str(len(achievements)))

        if not achievements:
            empty_ach = QLabel("No achievements recorded yet. Click below to add an entry.")
            empty_ach.setStyleSheet(f"color: {self.palette.fg_dim}; font-size: 13px; padding: 25px; font-style: italic; background: transparent;")
            empty_ach.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ach_rows_layout.addWidget(empty_ach)
        else:
            for a in achievements[:4]:
                row = AchievementRowWidget(a, parent=self.ach_pane)
                self.ach_rows_layout.addWidget(row)
