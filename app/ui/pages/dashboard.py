from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QScrollArea, QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QVariantAnimation
from PySide6.QtGui import QCursor

from database.repository import ProjectRepository, ProfileRepository
from app.ui.components.icons import get_svg_pixmap, get_svg_icon
from app.ui.components.achievement_dialog import AchievementDialog


class StatCard(QFrame):
    clicked = Signal()

    def __init__(self, icon_name, icon_color, title, badge_text, target_value, bottom_html):
        super().__init__()
        self.target_value = int(target_value)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(180)
        self.setStyleSheet("""
            #statCard {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            #statCard:hover {
                background-color: #182338;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Top Row: Icon + Title on left, Badge on right
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap(icon_name, icon_color, 18))
        top_layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #cbd5e1;")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()

        badge_lbl = QLabel(badge_text)
        badge_lbl.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 500;
            color: #94a3b8;
        """)
        top_layout.addWidget(badge_lbl)
        layout.addLayout(top_layout)

        # Middle: Animated Big Number
        self.val_lbl = QLabel("0")
        self.val_lbl.setStyleSheet("font-size: 32px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.5px;")
        layout.addWidget(self.val_lbl)

        # Bottom Row: Subtitle + Arrow
        bot_layout = QHBoxLayout()
        bot_layout.setContentsMargins(0, 4, 0, 0)

        bot_lbl = QLabel(bottom_html)
        bot_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        bot_layout.addWidget(bot_lbl)
        bot_layout.addStretch()

        self.arrow_lbl = QLabel("→")
        self.arrow_lbl.setStyleSheet("font-size: 14px; color: #64748b; font-weight: bold;")
        bot_layout.addWidget(self.arrow_lbl)

        layout.addLayout(bot_layout)

        # Smooth counter animation
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(550)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.valueChanged.connect(self._on_count_step)
        self._anim.finished.connect(lambda: self.val_lbl.setText(str(self.target_value)))

    def enterEvent(self, event):
        self.arrow_lbl.setStyleSheet("font-size: 14px; color: #cbd5e1; font-weight: bold;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.arrow_lbl.setStyleSheet("font-size: 14px; color: #64748b; font-weight: bold;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def start_counter(self):
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(float(self.target_value))
        self._anim.start()

    def _on_count_step(self, val):
        self.val_lbl.setText(str(round(val)))


class ProjectRowWidget(QFrame):
    clicked = Signal(int)

    def __init__(self, project_data, icon_name="layers", icon_color="#38bdf8"):
        super().__init__()
        self.project_id = project_data.get("id", 0)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("projRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(54)
        self.setStyleSheet("""
            #projRow {
                background-color: rgba(15, 23, 42, 0.45);
                border: 1px solid transparent;
                border-radius: 8px;
            }
            #projRow:hover {
                background-color: #1e293b;
                border: 1px solid #334155;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(10)

        # Icon box
        icon_box = QFrame()
        icon_box.setFixedSize(34, 34)
        icon_box.setStyleSheet("background-color: #1e293b; border-radius: 6px;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap(icon_name, icon_color, 18))
        ib_layout.addWidget(icon_lbl)
        layout.addWidget(icon_box)

        # Name & Description
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name = project_data.get("name", "Unnamed Project")
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #f1f5f9;")
        info_layout.addWidget(name_lbl)

        desc = project_data.get("description") or "No description provided."
        if len(desc) > 50:
            desc = desc[:47] + "..."
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        info_layout.addWidget(desc_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Tech stack badge + timestamp/status
        stack_text = project_data.get("technology_stack") or "General"
        if len(stack_text) > 18:
            stack_text = stack_text[:16] + ".."
        badge = QLabel(stack_text)
        badge.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 500;
            color: #cbd5e1;
        """)
        layout.addWidget(badge)

        status_str = project_data.get("status") or "Active"
        time_lbl = QLabel(status_str)
        time_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(time_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_id)
        super().mousePressEvent(event)


class AchievementRowWidget(QFrame):
    def __init__(self, ach_data):
        super().__init__()
        self.setObjectName("achRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(68)
        self.setStyleSheet("""
            #achRow {
                background-color: rgba(15, 23, 42, 0.45);
                border: 1px solid transparent;
                border-radius: 8px;
            }
            #achRow:hover {
                background-color: #1e293b;
                border: 1px solid #334155;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(10)

        ach_type = ach_data.get("type", "Certificate")
        if ach_type == "Certificate":
            icon_name = "award"
            icon_color = "#34d399"
            badge_style = "background-color: rgba(6, 78, 59, 0.5); color: #6ee7b7; border: 1px solid rgba(4, 120, 87, 0.4);"
        elif ach_type == "Hackathon":
            icon_name = "trophy"
            icon_color = "#60a5fa"
            badge_style = "background-color: rgba(30, 58, 138, 0.5); color: #93c5fd; border: 1px solid rgba(37, 99, 235, 0.4);"
        else:
            icon_name = "star"
            icon_color = "#818cf8"
            badge_style = "background-color: rgba(49, 46, 129, 0.5); color: #c7d2fe; border: 1px solid rgba(67, 56, 202, 0.4);"

        # Icon box
        icon_box = QFrame()
        icon_box.setFixedSize(34, 34)
        icon_box.setStyleSheet("background-color: #1e293b; border-radius: 6px;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap(icon_name, icon_color, 18))
        ib_layout.addWidget(icon_lbl)
        layout.addWidget(icon_box)

        # Content column
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # Top subrow: Badge + Date
        top_row = QHBoxLayout()
        type_badge = QLabel(ach_type)
        type_badge.setStyleSheet(f"{badge_style} border-radius: 4px; padding: 1px 7px; font-size: 11px; font-weight: 500;")
        top_row.addWidget(type_badge)
        top_row.addStretch()

        date_lbl = QLabel(str(ach_data.get("date_achieved") or "")[:10])
        date_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        top_row.addWidget(date_lbl)
        content_layout.addLayout(top_row)

        # Title
        title_lbl = QLabel(ach_data.get("title", "Achievement Title"))
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #f1f5f9;")
        content_layout.addWidget(title_lbl)

        # Description
        desc_text = ach_data.get("description") or "Recognized milestone."
        if len(desc_text) > 60:
            desc_text = desc_text[:57] + "..."
        desc_lbl = QLabel(desc_text)
        desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        content_layout.addWidget(desc_lbl)

        layout.addLayout(content_layout, stretch=1)


class DashboardPage(QWidget):
    navigate_requested = Signal(int)
    new_project_requested = Signal()
    open_project_requested = Signal(int)

    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.setObjectName("dashboardRoot")
        self.setStyleSheet("background-color: #0b0f17;")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for responsive sizing
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background-color: #0b0f17; border: none; }
            QScrollBar:vertical {
                background-color: #0b0f17;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #1e293b;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #334155;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 20, 24, 24)
        self.content_layout.setSpacing(16)

        # Build visual layers
        self._build_header()
        self._build_stats_section()
        self._build_activity_section()
        self._build_bottom_banner()

        self.scroll_area.setWidget(self.content_widget)
        root_layout.addWidget(self.scroll_area)

        # Entrance motion effect (Opacity 0 -> 1 over 280ms)
        self._opacity_effect = QGraphicsOpacityEffect(self.content_widget)
        self.content_widget.setGraphicsEffect(self._opacity_effect)
        self._entrance_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._entrance_anim.setDuration(280)
        self._entrance_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
        self._entrance_anim.stop()
        self._opacity_effect.setOpacity(0.0)
        self._entrance_anim.setStartValue(0.0)
        self._entrance_anim.setEndValue(1.0)
        self._entrance_anim.start()

    def _build_header(self):
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 4)
        header_row.setSpacing(12)

        # Left: Title + Badge + Subtitle
        left_box = QVBoxLayout()
        left_box.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title_lbl = QLabel("Dashboard")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.5px;")
        title_row.addWidget(title_lbl)

        v_badge = QLabel("v2.4")
        v_badge.setStyleSheet("""
            background-color: #1e293b;
            color: #94a3b8;
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 500;
        """)
        title_row.addWidget(v_badge)
        title_row.addStretch()
        left_box.addLayout(title_row)

        subtitle = QLabel("Welcome to Forge Hub — Your Personal Professional AI Manager")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        left_box.addWidget(subtitle)
        header_row.addLayout(left_box, 1)

        # Right: Quick action toolbar
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        # Synced status pill
        synced_pill = QFrame()
        synced_pill.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 6px;
        """)
        synced_pill.setFixedHeight(32)
        sp_layout = QHBoxLayout(synced_pill)
        sp_layout.setContentsMargins(10, 0, 10, 0)
        sp_layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet("background-color: #34d399; border-radius: 3px;")
        sp_layout.addWidget(dot)

        sp_text = QLabel("Synced")
        sp_text.setStyleSheet("font-size: 12px; font-weight: 500; color: #cbd5e1;")
        sp_layout.addWidget(sp_text)
        actions_row.addWidget(synced_pill)

        # Quick Action button
        quick_btn = QPushButton("Quick Action  ⌘K")
        quick_btn.setIcon(get_svg_icon("terminal", "#94a3b8", 14))
        quick_btn.setFixedHeight(32)
        quick_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        quick_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(51, 65, 85, 0.5);
                color: #e2e8f0;
                font-size: 12px;
                font-weight: 500;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #273549;
                border-color: #475569;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #131b2a;
            }
        """)
        actions_row.addWidget(quick_btn)

        # New Project button
        new_proj_btn = QPushButton("New Project")
        new_proj_btn.setIcon(get_svg_icon("plus", "#ffffff", 14))
        new_proj_btn.setFixedHeight(32)
        new_proj_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        new_proj_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                border: none;
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        new_proj_btn.clicked.connect(self.new_project_requested.emit)
        actions_row.addWidget(new_proj_btn)

        header_row.addLayout(actions_row, 0)
        self.content_layout.addLayout(header_row)

    def _build_stats_section(self):
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(14)
        self.stat_cards = []
        self.content_layout.addLayout(self.stats_layout)

    def _build_activity_section(self):
        self.split_activity_layout = QHBoxLayout()
        self.split_activity_layout.setSpacing(14)

        # Left Column: Recent Projects
        self.proj_pane = QFrame()
        self.proj_pane.setStyleSheet("""
            QFrame#projPane {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        self.proj_pane.setObjectName("projPane")
        self.proj_pane_layout = QVBoxLayout(self.proj_pane)
        self.proj_pane_layout.setContentsMargins(14, 14, 14, 14)
        self.proj_pane_layout.setSpacing(10)

        # Header for projects pane
        proj_hdr = QHBoxLayout()
        proj_title_lbl = QLabel("Recent Projects")
        proj_title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9;")
        proj_hdr.addWidget(proj_title_lbl)

        self.proj_count_badge = QLabel("0")
        self.proj_count_badge.setStyleSheet("background-color: #1e293b; color: #cbd5e1; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: 500;")
        proj_hdr.addWidget(self.proj_count_badge)
        proj_hdr.addStretch()

        view_all_btn = QPushButton("View all →")
        view_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_all_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #60a5fa;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #93c5fd;
            }
        """)
        view_all_btn.clicked.connect(lambda: self.navigate_requested.emit(1))
        proj_hdr.addWidget(view_all_btn)
        self.proj_pane_layout.addLayout(proj_hdr)

        self.proj_rows_layout = QVBoxLayout()
        self.proj_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.proj_rows_layout.setSpacing(6)
        self.proj_pane_layout.addLayout(self.proj_rows_layout)
        self.proj_pane_layout.addStretch()

        # Right Column: Recent Achievements
        self.ach_pane = QFrame()
        self.ach_pane.setStyleSheet("""
            QFrame#achPane {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        self.ach_pane.setObjectName("achPane")
        self.ach_pane_layout = QVBoxLayout(self.ach_pane)
        self.ach_pane_layout.setContentsMargins(14, 14, 14, 14)
        self.ach_pane_layout.setSpacing(10)

        # Header for achievements pane
        ach_hdr = QHBoxLayout()
        ach_title_lbl = QLabel("Recent Achievements")
        ach_title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9;")
        ach_hdr.addWidget(ach_title_lbl)

        self.ach_count_badge = QLabel("0")
        self.ach_count_badge.setStyleSheet("background-color: #1e293b; color: #cbd5e1; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: 500;")
        ach_hdr.addWidget(self.ach_count_badge)
        ach_hdr.addStretch()

        manage_btn = QPushButton("Manage")
        manage_btn.setIcon(get_svg_icon("tune", "#94a3b8", 14))
        manage_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        manage_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #f1f5f9;
            }
        """)
        manage_btn.clicked.connect(lambda: self.navigate_requested.emit(2))
        ach_hdr.addWidget(manage_btn)
        self.ach_pane_layout.addLayout(ach_hdr)

        self.ach_rows_layout = QVBoxLayout()
        self.ach_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ach_rows_layout.setSpacing(6)
        self.ach_pane_layout.addLayout(self.ach_rows_layout)
        self.ach_pane_layout.addStretch()

        # Dashed Add Entry Row at the bottom of achievements pane
        add_entry_card = QFrame()
        add_entry_card.setFixedHeight(40)
        add_entry_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_entry_card.setStyleSheet("""
            QFrame {
                border: 1px dashed #334155;
                border-radius: 8px;
                background-color: rgba(15, 23, 42, 0.3);
            }
            QFrame:hover {
                border-color: #475569;
                background-color: rgba(30, 41, 59, 0.4);
            }
        """)
        ae_layout = QHBoxLayout(add_entry_card)
        ae_layout.setContentsMargins(12, 0, 12, 0)
        ae_layout.setSpacing(8)

        plus_icon = QLabel()
        plus_icon.setPixmap(get_svg_pixmap("add_circle", "#64748b", 16))
        ae_layout.addWidget(plus_icon)

        ae_text = QLabel("Add new certification, award, or milestone...")
        ae_text.setStyleSheet("font-size: 12px; color: #94a3b8;")
        ae_layout.addWidget(ae_text)
        ae_layout.addStretch()

        ae_btn_label = QLabel("Add Entry")
        ae_btn_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #64748b;")
        ae_layout.addWidget(ae_btn_label)

        add_entry_card.mousePressEvent = lambda e: self._on_add_achievement_clicked()
        self.ach_pane_layout.addWidget(add_entry_card)

        self.split_activity_layout.addWidget(self.proj_pane, 1)
        self.split_activity_layout.addWidget(self.ach_pane, 1)
        self.content_layout.addLayout(self.split_activity_layout)

    def _build_bottom_banner(self):
        banner = QFrame()
        banner.setStyleSheet("""
            background-color: #131b2a;
            border: 1px solid #1e293b;
            border-radius: 8px;
        """)
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(16, 10, 16, 10)
        b_layout.setSpacing(10)

        info_icon = QLabel()
        info_icon.setPixmap(get_svg_pixmap("info", "#94a3b8", 18))
        b_layout.addWidget(info_icon)

        info_text = QLabel("Navigate using the sidebar to manage your projects, professional profile, AI providers, and knowledge base.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 12px; color: #94a3b8;")
        b_layout.addWidget(info_text, stretch=1)

        # Keyboard shortcuts
        kbd_layout = QHBoxLayout()
        kbd_layout.setSpacing(6)

        def make_kbd(key):
            lbl = QLabel(key)
            lbl.setStyleSheet("""
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px 7px;
                font-size: 11px;
                color: #cbd5e1;
            """)
            return lbl

        kbd_layout.addWidget(make_kbd("Ctrl"))
        p1 = QLabel("+")
        p1.setStyleSheet("color: #64748b; font-size: 11px;")
        kbd_layout.addWidget(p1)
        kbd_layout.addWidget(make_kbd("K"))
        t1 = QLabel("Palette")
        t1.setStyleSheet("color: #94a3b8; font-size: 11px;")
        kbd_layout.addWidget(t1)

        dot = QLabel("•")
        dot.setStyleSheet("color: #475569; font-size: 12px; margin: 0 4px;")
        kbd_layout.addWidget(dot)

        kbd_layout.addWidget(make_kbd("Ctrl"))
        p2 = QLabel("+")
        p2.setStyleSheet("color: #64748b; font-size: 11px;")
        kbd_layout.addWidget(p2)
        kbd_layout.addWidget(make_kbd("P"))
        t2 = QLabel("Switch")
        t2.setStyleSheet("color: #94a3b8; font-size: 11px;")
        kbd_layout.addWidget(t2)

        b_layout.addLayout(kbd_layout)
        self.content_layout.addWidget(banner)

    def _on_add_achievement_clicked(self):
        if not self.db: return
        dlg = AchievementDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            prof_repo = ProfileRepository(self.db)
            prof_repo.add_achievement(data["title"], data["description"], data["date"], data["type"])
            self.refresh_data()

    def refresh_data(self):
        projects = []
        skills = []
        achievements = []

        if self.db:
            try:
                proj_repo = ProjectRepository(self.db)
                projects = proj_repo.get_projects()
                prof_repo = ProfileRepository(self.db)
                skills = prof_repo.get_skills()
                achievements = prof_repo.get_achievements()
            except Exception:
                pass

        # 1. Update Stat Cards
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.stat_cards.clear()

        # Compute breakdowns
        active_proj = sum(1 for p in projects if p.get("status") in ("In Progress", "Planning", "Active", None))
        other_proj = len(projects) - active_proj

        verified_skills = sum(1 for s in skills if s.get("level") in ("Advanced", "Expert"))
        dev_skills = len(skills) - verified_skills

        latest_ach_title = achievements[0].get("title", "None") if achievements else "No entries yet"
        if len(latest_ach_title) > 24:
            latest_ach_title = latest_ach_title[:22] + "..."

        c1 = StatCard(
            "folder", "#60a5fa", "Total Projects", "Active",
            len(projects),
            f"<span style='color:#34d399;'>●</span> {active_proj} Active <span style='color:#475569;'>•</span> {other_proj} Other"
        )
        c1.clicked.connect(lambda: self.navigate_requested.emit(1))

        c2 = StatCard(
            "brain", "#a78bfa", "Skills Tracked", "Verified",
            len(skills),
            f"<span style='color:#60a5fa;'>●</span> {verified_skills} Verified <span style='color:#475569;'>•</span> {dev_skills} Developing"
        )
        c2.clicked.connect(lambda: self.navigate_requested.emit(2))

        c3 = StatCard(
            "verified", "#34d399", "Achievements", "Honors",
            len(achievements),
            f"Latest: <span style='color:#f1f5f9; font-weight:500;'>{latest_ach_title}</span>"
        )
        c3.clicked.connect(lambda: self.navigate_requested.emit(2))

        self.stats_layout.addWidget(c1)
        self.stats_layout.addWidget(c2)
        self.stats_layout.addWidget(c3)
        self.stat_cards = [c1, c2, c3]

        for card in self.stat_cards:
            card.start_counter()

        # 2. Update Projects List
        while self.proj_rows_layout.count():
            item = self.proj_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.proj_count_badge.setText(str(len(projects)))

        icon_cycle = [("layers", "#38bdf8"), ("database", "#34d399"), ("sync", "#818cf8"), ("share", "#60a5fa"), ("analytics", "#f43f5e")]
        if not projects:
            empty_lbl = QLabel("No projects created yet. Click '+ New Project' to get started.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 12px; padding: 20px; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.proj_rows_layout.addWidget(empty_lbl)
        else:
            for idx, p in enumerate(projects[:5]):
                iname, icolor = icon_cycle[idx % len(icon_cycle)]
                row = ProjectRowWidget(p, iname, icolor)
                row.clicked.connect(self.open_project_requested.emit)
                self.proj_rows_layout.addWidget(row)

        # 3. Update Achievements List
        while self.ach_rows_layout.count():
            item = self.ach_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.ach_count_badge.setText(str(len(achievements)))

        if not achievements:
            empty_ach = QLabel("No achievements recorded yet. Click below to add an entry.")
            empty_ach.setStyleSheet("color: #64748b; font-size: 12px; padding: 20px; font-style: italic;")
            empty_ach.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ach_rows_layout.addWidget(empty_ach)
        else:
            for a in achievements[:4]:
                row = AchievementRowWidget(a)
                self.ach_rows_layout.addWidget(row)
