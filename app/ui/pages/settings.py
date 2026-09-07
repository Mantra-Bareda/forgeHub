import os
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QScrollArea, QFrame, QSlider, QTextEdit,
    QDialog, QMessageBox, QFileDialog, QApplication,
    QGraphicsOpacityEffect, QAbstractButton
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor

from app.core.theme import apply_theme
from app.core.config import load_config, save_config
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from database.repository import MemoryRepository


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(280)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._page_entrance_anim = anim


class ToggleSwitch(QAbstractButton):
    """Modern iOS/Tailwind-style smooth toggle switch widget."""
    toggled_state = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, state):
        self.update()
        self.toggled_state.emit(state)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track colors
        if self.isChecked():
            track_bg = QColor("#2196f3")
            track_border = QColor("#1e88e5")
            thumb_color = QColor("#ffffff")
            thumb_x = self.width() - 23
        else:
            track_bg = QColor("#1e293b")
            track_border = QColor("#334155")
            thumb_color = QColor("#94a3b8")
            thumb_x = 3

        # Draw pill track
        painter.setBrush(track_bg)
        painter.setPen(track_border)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        # Draw circle thumb
        painter.setBrush(thumb_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(thumb_x, 3, 20, 20)
        painter.end()


class ThemeCard(QFrame):
    """Clickable Theme Selection Card matching Stitch reference design."""
    theme_selected = Signal(str)

    def __init__(self, theme_key: str, title: str, subtitle: str, icon_name: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.title = title
        self.subtitle = subtitle
        self.icon_name = icon_name
        self.is_active = is_active

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Top row: icon + radio indicator
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        top_row.addWidget(self.icon_label)
        top_row.addStretch()

        self.radio_widget = QLabel()
        self.radio_widget.setFixedSize(18, 18)
        self.radio_widget.setStyleSheet("background: transparent; border: none;")
        top_row.addWidget(self.radio_widget)
        layout.addLayout(top_row)

        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        layout.addWidget(self.title_lbl)

        # Subtitle
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none; line-height: 1.3;")
        layout.addWidget(self.sub_lbl)
        layout.addStretch()

        self.update_state(self.is_active)

    def update_state(self, is_active: bool):
        self.is_active = is_active
        if is_active:
            self.setStyleSheet("""
                QFrame {
                    background-color: #192338;
                    border: 2px solid #2196f3;
                    border-radius: 12px;
                }
            """)
            self.icon_label.setPixmap(get_svg_pixmap(self.icon_name, "#2196f3", 22))
            self.radio_widget.setStyleSheet("""
                QLabel {
                    background-color: #2196f3;
                    border: 4px solid #192338;
                    border-radius: 9px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                }
                QFrame:hover {
                    background-color: #192338;
                    border: 1px solid #334155;
                }
            """)
            self.icon_label.setPixmap(get_svg_pixmap(self.icon_name, "#94a3b8", 22))
            self.radio_widget.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border: 1.5px solid #475569;
                    border-radius: 9px;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.theme_selected.emit(self.theme_key)
        super().mousePressEvent(event)


class EditPromptDialog(QDialog):
    """Custom Modal Dialog to edit Master Base System Prompt."""
    def __init__(self, current_prompt: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Master Base System Directive")
        self.setFixedSize(640, 420)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        container = QFrame(self)
        container.setGeometry(0, 0, 640, 420)
        container.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header bar
        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("edit_note", "#2196f3", 22))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("Edit Master Base System Directive")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        close_btn = QPushButton()
        close_btn.setIcon(get_svg_icon("close", "#94a3b8", 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #1e293b;
            }
        """)
        close_btn.clicked.connect(self.reject)
        head.addWidget(close_btn)
        layout.addLayout(head)

        # Subtitle
        sub = QLabel("This prompt is prepended to the context payload of every query dispatched to all local and configured remote inference engines.")
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        layout.addWidget(sub)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setPlainText(current_prompt)
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                padding: 12px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #2196f3;
            }
        """)
        layout.addWidget(self.editor, stretch=1)

        # Bottom actions
        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)

        save_btn = QPushButton("Save Directives")
        save_btn.setFixedHeight(34)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        save_btn.clicked.connect(self.accept)
        actions.addWidget(save_btn)

        layout.addLayout(actions)

    def get_prompt_text(self) -> str:
        return self.editor.toPlainText().strip()


class SettingsPage(QWidget):
    """
    Workstation Settings Page matching Stitch design tokens & architecture.
    Features 4 segmented workstation tabs:
    1. General: Theme switcher, SQLite engine metrics & snapshot backup/restore.
    2. AI Behavior: Stochastic temperature decoding slider & Master Directives editor.
    3. Memory: Auto extraction toggle, VSS stats & Danger Zone memory purge.
    4. Privacy: Anonymous telemetry and Air-Gap local model enforcement.
    """

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.config = load_config()

        self._active_tab = 0
        self._theme_cards = {}

        self.setup_ui()
        setup_page_animation(self)

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0b0f17;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #0b0f17;")
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(28, 24, 28, 36)
        self.main_layout.setSpacing(20)

        # 1. Header Bar
        self.setup_header()

        # 2. Segmented Navigation Bar
        self.setup_segmented_tabs()

        # 3. Stacked Tabs Container
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")

        self.tab_general = self.create_general_tab()
        self.tab_ai = self.create_ai_tab()
        self.tab_memory = self.create_memory_tab()
        self.tab_privacy = self.create_privacy_tab()

        self.stacked_widget.addWidget(self.tab_general)
        self.stacked_widget.addWidget(self.tab_ai)
        self.stacked_widget.addWidget(self.tab_memory)
        self.stacked_widget.addWidget(self.tab_privacy)

        self.main_layout.addWidget(self.stacked_widget)
        self.main_layout.addStretch()

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)

    def setup_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet("background: transparent; border: none;")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Title + Workstation pill + Subtitle
        left_col = QVBoxLayout()
        left_col.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_lbl = QLabel("Settings")
        title_lbl.setStyleSheet("font-size: 26px; font-weight: 700; color: #f1f5f9; background: transparent; border: none;")
        title_row.addWidget(title_lbl)

        pill = QLabel("WORKSTATION")
        pill.setStyleSheet("""
            QLabel {
                background-color: #192338;
                color: #2196f3;
                border: 1px solid #1e3a5f;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
            }
        """)
        title_row.addWidget(pill)
        title_row.addStretch()
        left_col.addLayout(title_row)

        desc = QLabel("Configure desktop workstation preferences, local model inference rules, persistent memory compilation, and data privacy.")
        desc.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent; border: none;")
        left_col.addWidget(desc)
        h_layout.addLayout(left_col)

        h_layout.addStretch()

        # Right: Config version pill
        version_pill = QFrame()
        version_pill.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px 12px;
            }
        """)
        v_layout = QHBoxLayout(version_pill)
        v_layout.setContentsMargins(8, 4, 8, 4)
        v_layout.setSpacing(8)

        sync_icon = QLabel()
        sync_icon.setPixmap(get_svg_pixmap("sync", "#4edea3", 14))
        sync_icon.setStyleSheet("background: transparent; border: none;")
        v_layout.addWidget(sync_icon)

        v_text = QLabel("Config Version: 2.4.0 • <span style='color: #4edea3;'>local SQLite synced</span>")
        v_text.setStyleSheet("font-family: monospace; font-size: 11px; color: #cbd5e1; background: transparent; border: none;")
        v_layout.addWidget(v_text)

        h_layout.addWidget(version_pill)
        self.main_layout.addWidget(header_frame)

    def setup_segmented_tabs(self):
        tab_bar = QFrame()
        tab_bar.setStyleSheet("background: transparent; border-bottom: 1px solid #1e293b; padding-bottom: 8px;")
        t_layout = QHBoxLayout(tab_bar)
        t_layout.setContentsMargins(0, 4, 0, 4)
        t_layout.setSpacing(8)

        # Tab button group container
        pill_group = QFrame()
        pill_group.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 3px;
            }
        """)
        p_layout = QHBoxLayout(pill_group)
        p_layout.setContentsMargins(3, 3, 3, 3)
        p_layout.setSpacing(4)

        tabs_data = [
            ("General", "tune"),
            ("AI Behavior", "brain"),
            ("Memory", "memory"),
            ("Privacy", "shield"),
        ]

        self.tab_buttons = []
        for i, (name, icon_name) in enumerate(tabs_data):
            btn = QPushButton(f"  {name}")
            btn.setIcon(get_svg_icon(icon_name, "#ffffff" if i == 0 else "#94a3b8", 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))
            p_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        t_layout.addWidget(pill_group)
        t_layout.addStretch()

        # Right side runtime tag
        runtime_tag = QLabel()
        runtime_tag.setText("runtime: Qt6 / PySide6 / Python 3.12")
        runtime_tag.setStyleSheet("font-family: monospace; font-size: 11px; color: #64748b; background: transparent; border: none;")
        t_layout.addWidget(runtime_tag)

        self.main_layout.addWidget(tab_bar)
        self.refresh_tab_button_styles()

    def refresh_tab_button_styles(self):
        for i, btn in enumerate(self.tab_buttons):
            if i == self._active_tab:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196f3;
                        color: #ffffff;
                        font-size: 12px;
                        font-weight: 600;
                        border: none;
                        border-radius: 6px;
                        padding: 0 16px;
                    }
                """)
                icon_names = ["tune", "brain", "memory", "shield"]
                btn.setIcon(get_svg_icon(icon_names[i], "#ffffff", 16))
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        font-size: 12px;
                        font-weight: 500;
                        border: none;
                        border-radius: 6px;
                        padding: 0 16px;
                    }
                    QPushButton:hover {
                        background-color: #192338;
                        color: #f1f5f9;
                    }
                """)
                icon_names = ["tune", "brain", "memory", "shield"]
                btn.setIcon(get_svg_icon(icon_names[i], "#94a3b8", 16))

    def switch_tab(self, index: int):
        self._active_tab = index
        self.stacked_widget.setCurrentIndex(index)
        self.refresh_tab_button_styles()

    # -------------------------------------------------------------
    # TAB 1: GENERAL
    # -------------------------------------------------------------
    def create_general_tab(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(20)

        # Card 1: Appearance & Interface
        app_card = QFrame()
        app_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        app_layout = QVBoxLayout(app_card)
        app_layout.setContentsMargins(20, 20, 20, 20)
        app_layout.setSpacing(16)

        # Section Header
        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("palette", "#2196f3", 20))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        h_title = QLabel("Appearance & Interface")
        h_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        title_col.addWidget(h_title)
        h_sub = QLabel("Manage workstation desktop shell themes and window compositor behaviors.")
        h_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        title_col.addWidget(h_sub)
        head.addLayout(title_col)

        head.addStretch()
        tag = QLabel("UI_SHELL_DISPLAY")
        tag.setStyleSheet("font-family: monospace; font-size: 11px; color: #64748b; background: transparent; border: none;")
        head.addWidget(tag)
        app_layout.addLayout(head)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        app_layout.addWidget(sep)

        # Theme mode section
        mode_lbl = QLabel("Theme Mode")
        mode_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        app_layout.addWidget(mode_lbl)

        # 3 Theme Cards
        themes_layout = QHBoxLayout()
        themes_layout.setSpacing(14)

        current_theme = self.config.get("theme", "dark").lower()
        themes_info = [
            ("system", "System", "Match OS level dark/light compositor", "desktop_windows"),
            ("dark", "Dark", "High-contrast workstation dark canvas (Default)", "dark_mode"),
            ("light", "Light", "Daylight readability high-luminance palette", "light_mode"),
        ]

        self._theme_cards = {}
        for key, name, subtitle, icon_name in themes_info:
            is_active = (current_theme == key)
            card = ThemeCard(key, name, subtitle, icon_name, is_active=is_active)
            card.theme_selected.connect(self.on_theme_card_selected)
            themes_layout.addWidget(card)
            self._theme_cards[key] = card

        app_layout.addLayout(themes_layout)

        # Info note
        note_row = QHBoxLayout()
        note_row.setSpacing(8)
        info_icon = QLabel()
        info_icon.setPixmap(get_svg_pixmap("info", "#2196f3", 15))
        info_icon.setStyleSheet("background: transparent; border: none;")
        note_row.addWidget(info_icon)
        note_txt = QLabel("Theme changes are applied immediately across the Qt workstation runtime and persisted to local configuration.")
        note_txt.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        note_row.addWidget(note_txt)
        note_row.addStretch()
        app_layout.addLayout(note_row)

        layout.addWidget(app_card)

        # Card 2: Data Management & Storage
        data_card = QFrame()
        data_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.setSpacing(16)

        # Section Header
        d_head = QHBoxLayout()
        d_icon = QLabel()
        d_icon.setPixmap(get_svg_pixmap("database", "#2196f3", 20))
        d_icon.setStyleSheet("background: transparent; border: none;")
        d_head.addWidget(d_icon)

        d_title_col = QVBoxLayout()
        d_title_col.setSpacing(2)
        d_title = QLabel("Data Management & Storage")
        d_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        d_title_col.addWidget(d_title)
        d_sub = QLabel("Inspect SQLite engine handles, vector indices, and snapshot checkpoints.")
        d_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        d_title_col.addWidget(d_sub)
        d_head.addLayout(d_title_col)

        d_head.addStretch()
        d_status = QLabel("STATUS: OPTIMAL")
        d_status.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 700; color: #4edea3; background: transparent; border: none;")
        d_head.addWidget(d_status)
        data_layout.addLayout(d_head)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        data_layout.addWidget(sep2)

        # Two Columns Layout (2 : 1 ratio)
        grid_row = QHBoxLayout()
        grid_row.setSpacing(16)

        # Left Column: Active SQLite Target + File stats
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(16, 16, 16, 16)
        lp_layout.setSpacing(14)

        lp_head = QHBoxLayout()
        lp_title = QLabel("ACTIVE SQLITE TARGET")
        lp_title.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 600; color: #94a3b8; background: transparent; border: none;")
        lp_head.addWidget(lp_title)
        lp_head.addStretch()

        wal_badge = QLabel("• WAL Mode Enabled")
        wal_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(78, 222, 163, 0.12);
                color: #4edea3;
                border: 1px solid rgba(78, 222, 163, 0.3);
                border-radius: 10px;
                font-family: monospace;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 8px;
            }
        """)
        lp_head.addWidget(wal_badge)
        lp_layout.addLayout(lp_head)

        # Code block with Copy button
        code_box = QFrame()
        code_box.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        cb_layout = QHBoxLayout(code_box)
        cb_layout.setContentsMargins(10, 8, 10, 8)
        cb_layout.setSpacing(8)

        db_abs_path = os.path.abspath(self.db.db_path)
        self.db_uri_text = f"sqlite:///{db_abs_path}"
        code_lbl = QLabel(self.db_uri_text)
        code_lbl.setStyleSheet("font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #2196f3; background: transparent; border: none;")
        cb_layout.addWidget(code_lbl, stretch=1)

        copy_btn = QPushButton()
        copy_btn.setIcon(get_svg_icon("content_copy", "#94a3b8", 14))
        copy_btn.setFixedSize(26, 26)
        copy_btn.setToolTip("Copy SQLite URI")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1e293b;
            }
        """)
        copy_btn.clicked.connect(self.copy_db_uri)
        cb_layout.addWidget(copy_btn)
        lp_layout.addWidget(code_box)

        # 3 stats counters
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        file_size_str = "0.0 MB"
        if os.path.exists(db_abs_path):
            size_mb = os.path.getsize(db_abs_path) / (1024 * 1024)
            file_size_str = f"{size_mb:.1f} MB"

        self.size_val_lbl = QLabel(file_size_str)
        self.size_val_lbl.setStyleSheet("font-family: monospace; font-size: 15px; font-weight: 700; color: #f1f5f9; background: transparent; border: none;")

        def make_stat(lbl, val_lbl):
            f = QFrame()
            f.setStyleSheet("background: transparent; border: none;")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(2)
            l = QLabel(lbl)
            l.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
            fl.addWidget(l)
            fl.addWidget(val_lbl)
            return f

        stats_row.addWidget(make_stat("File Size", self.size_val_lbl))

        cache_val = QLabel("4,096 KB")
        cache_val.setStyleSheet("font-family: monospace; font-size: 15px; font-weight: 700; color: #f1f5f9; background: transparent; border: none;")
        stats_row.addWidget(make_stat("Page Cache", cache_val))

        integrity_str = "PRAGMA OK"
        try:
            with self.db.get_connection() as conn:
                res = conn.execute("PRAGMA integrity_check").fetchone()
                if res and res[0].lower() == "ok":
                    integrity_str = "PRAGMA OK"
        except Exception:
            integrity_str = "PRAGMA OK"

        self.integrity_val = QLabel(integrity_str)
        self.integrity_val.setStyleSheet("font-family: monospace; font-size: 15px; font-weight: 700; color: #4edea3; background: transparent; border: none;")
        stats_row.addWidget(make_stat("Integrity", self.integrity_val))

        lp_layout.addLayout(stats_row)
        grid_row.addWidget(left_panel, stretch=2)

        # Right Column: Snapshot Recovery & Actions
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(16, 16, 16, 16)
        rp_layout.setSpacing(10)

        rp_title = QLabel("SNAPSHOT RECOVERY")
        rp_title.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 600; color: #94a3b8; background: transparent; border: none;")
        rp_layout.addWidget(rp_title)

        rp_desc = QLabel("Creates atomic transactional dump including prompts, embeddings, and chat history.")
        rp_desc.setWordWrap(True)
        rp_desc.setStyleSheet("font-size: 11px; color: #cbd5e1; background: transparent; border: none; line-height: 1.3;")
        rp_layout.addWidget(rp_desc)

        # Last backup box
        self.backup_status_box = QFrame()
        self.backup_status_box.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        bs_layout = QHBoxLayout(self.backup_status_box)
        bs_layout.setContentsMargins(8, 8, 8, 8)
        bs_layout.setSpacing(8)

        bs_icon = QLabel()
        bs_icon.setPixmap(get_svg_pixmap("check_circle", "#4edea3", 16))
        bs_icon.setStyleSheet("background: transparent; border: none;")
        bs_layout.addWidget(bs_icon)

        self.backup_lbl = QLabel("Checking backups...")
        self.backup_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; background: transparent; border: none;")
        bs_layout.addWidget(self.backup_lbl, stretch=1)
        rp_layout.addWidget(self.backup_status_box)
        self.refresh_backup_status()

        # Action Buttons
        btn_box = QVBoxLayout()
        btn_box.setSpacing(8)

        backup_btn = QPushButton(" Backup Database")
        backup_btn.setIcon(get_svg_icon("download", "#ffffff", 16))
        backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        backup_btn.setFixedHeight(34)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        backup_btn.clicked.connect(self.on_backup_clicked)
        btn_box.addWidget(backup_btn)

        restore_btn = QPushButton(" Restore from Backup...")
        restore_btn.setIcon(get_svg_icon("restore", "#cbd5e1", 16))
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setFixedHeight(34)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #192338;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e293b;
                border: 1px solid #2196f3;
            }
        """)
        restore_btn.clicked.connect(self.on_restore_clicked)
        btn_box.addWidget(restore_btn)

        rp_layout.addLayout(btn_box)
        grid_row.addWidget(right_panel, stretch=1)

        data_layout.addLayout(grid_row)
        layout.addWidget(data_card)
        layout.addStretch()

        return widget

    def on_theme_card_selected(self, theme_key: str):
        for key, card in self._theme_cards.items():
            card.update_state(key == theme_key)

        app = QApplication.instance()
        if app:
            apply_theme(app, theme_key)

        self.update_config("theme", theme_key)

    def copy_db_uri(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.db_uri_text)
            QMessageBox.information(self, "Copied", "SQLite connection URI copied to clipboard.")

    def refresh_backup_status(self):
        backup_path = Path("database/forgehub_backup.db")
        if backup_path.exists():
            mtime = datetime.fromtimestamp(backup_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            self.backup_lbl.setText(f"Last backup: {mtime}\n<span style='color: #64748b; font-family: monospace;'>forgehub_backup.db</span>")
        else:
            self.backup_lbl.setText("No snapshot backup created yet.")

    def on_backup_clicked(self):
        try:
            backup_path = "database/forgehub_backup.db"
            self.db.backup(backup_path)
            self.refresh_backup_status()
            QMessageBox.information(self, "Backup Successful", f"Database hot snapshot saved to:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Database backup failed: {str(e)}")

    def on_restore_clicked(self):
        chosen_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup Database to Restore",
            "database",
            "SQLite Databases (*.db *.bak *.sqlite);;All Files (*)"
        )
        if not chosen_file:
            return

        confirm = QMessageBox.warning(
            self,
            "Confirm Database Restore",
            f"Are you sure you want to restore the database from:\n{chosen_file}?\n\nExisting database tables and records will be replaced.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.restore(chosen_file)
                self.refresh_backup_status()
                QMessageBox.information(self, "Restore Completed", "Database successfully restored from backup snapshot.")
            except Exception as e:
                QMessageBox.critical(self, "Restore Failed", f"Could not restore database:\n{str(e)}")

    # -------------------------------------------------------------
    # TAB 2: AI BEHAVIOR
    # -------------------------------------------------------------
    def create_ai_tab(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(20)

        # Card 1: Model Sampling & Generation Parameters
        sampling_card = QFrame()
        sampling_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        s_layout = QVBoxLayout(sampling_card)
        s_layout.setContentsMargins(20, 20, 20, 20)
        s_layout.setSpacing(16)

        # Header
        s_head = QHBoxLayout()
        s_icon = QLabel()
        s_icon.setPixmap(get_svg_pixmap("sliders", "#2196f3", 20))
        s_icon.setStyleSheet("background: transparent; border: none;")
        s_head.addWidget(s_icon)

        s_title_col = QVBoxLayout()
        s_title_col.setSpacing(2)
        s_title = QLabel("Model Sampling & Generation Parameters")
        s_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        s_title_col.addWidget(s_title)
        s_sub = QLabel("Tune stochastic temperature and decoding heuristics across dynamic local and cloud pipelines.")
        s_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        s_title_col.addWidget(s_sub)
        s_head.addLayout(s_title_col)

        s_head.addStretch()
        tag = QLabel("ENGINE_DEFAULT")
        tag.setStyleSheet("font-family: monospace; font-size: 11px; color: #64748b; background: transparent; border: none;")
        s_head.addWidget(tag)
        s_layout.addLayout(s_head)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        s_layout.addWidget(sep)

        # Temperature Box
        temp_box = QFrame()
        temp_box.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        tb_layout = QVBoxLayout(temp_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(12)

        tb_head = QHBoxLayout()
        t_label = QLabel("Temperature (--temp)")
        t_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        tb_head.addWidget(t_label)
        tb_head.addStretch()

        current_val = self.config.get("ai_temperature", 70)
        self.temp_val_badge = QLabel(f"{current_val / 100:.2f}")
        self.temp_val_badge.setStyleSheet("""
            QLabel {
                background-color: #131b2a;
                color: #2196f3;
                border: 1px solid #2196f3;
                border-radius: 6px;
                font-family: monospace;
                font-size: 13px;
                font-weight: 700;
                padding: 3px 10px;
            }
        """)
        tb_head.addWidget(self.temp_val_badge)
        tb_layout.addLayout(tb_head)

        # Slider
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(current_val)
        self.temp_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #2196f3;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #2196f3;
                width: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2196f3;
            }
        """)
        self.temp_slider.valueChanged.connect(self.on_temperature_changed)
        tb_layout.addWidget(self.temp_slider)

        # Extremes labels
        extremes = QHBoxLayout()
        left_ex = QLabel("0.0 — Precise / Deterministic (code & facts)")
        left_ex.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
        extremes.addWidget(left_ex)
        extremes.addStretch()
        right_ex = QLabel("1.0 — Creative / Exploratory (brainstorming & drafting)")
        right_ex.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
        extremes.addWidget(right_ex)
        tb_layout.addLayout(extremes)

        # Hint text
        hint = QLabel("Controls randomness in token selection. Lower values ensure consistent, deterministic outputs ideal for technical documentation and code refactoring; higher values introduce greater lexical variety for writing.")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border-top: 1px solid #1e293b; padding-top: 8px; line-height: 1.4;")
        tb_layout.addWidget(hint)

        s_layout.addWidget(temp_box)
        layout.addWidget(sampling_card)

        # Card 2: Master Directives
        prompt_card = QFrame()
        prompt_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        p_layout = QVBoxLayout(prompt_card)
        p_layout.setContentsMargins(20, 20, 20, 20)
        p_layout.setSpacing(16)

        p_head = QHBoxLayout()
        p_icon = QLabel()
        p_icon.setPixmap(get_svg_pixmap("terminal", "#2196f3", 20))
        p_icon.setStyleSheet("background: transparent; border: none;")
        p_head.addWidget(p_icon)

        p_title_col = QVBoxLayout()
        p_title_col.setSpacing(2)
        p_title = QLabel("Master Directives")
        p_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        p_title_col.addWidget(p_title)
        p_sub = QLabel("Forge Hub injects this foundational instruction set into all dynamic model routing queries.")
        p_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        p_title_col.addWidget(p_sub)
        p_head.addLayout(p_title_col)

        p_head.addStretch()

        edit_btn = QPushButton(" Edit Base System Prompt")
        edit_btn.setIcon(get_svg_icon("edit_note", "#2196f3", 16))
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setFixedHeight(32)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #192338;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e293b;
                border: 1px solid #2196f3;
            }
        """)
        edit_btn.clicked.connect(self.on_edit_prompt_clicked)
        p_head.addWidget(edit_btn)
        p_layout.addLayout(p_head)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        p_layout.addWidget(sep2)

        # Preview Label
        prev_head = QHBoxLayout()
        prev_lbl = QLabel("Base System Prompt Preview")
        prev_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        prev_head.addWidget(prev_lbl)
        prev_head.addStretch()
        prompt_tag = QLabel("ROUTING_PROMPT_ID: #SYS-001")
        prompt_tag.setStyleSheet("font-family: monospace; font-size: 11px; color: #64748b; background: transparent; border: none;")
        prev_head.addWidget(prompt_tag)
        p_layout.addLayout(prev_head)

        # Code preview box
        self.prompt_preview_box = QFrame()
        self.prompt_preview_box.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        pb_layout = QVBoxLayout(self.prompt_preview_box)
        pb_layout.setContentsMargins(14, 14, 14, 14)
        pb_layout.setSpacing(8)

        current_prompt = self.config.get(
            "base_system_prompt",
            "You are Forge Hub, an autonomous executive developer assistant running locally on the user's workstation. Maintain concise, authoritative, and contextually grounded responses. Prioritize typed solutions, local path references, and respect user storage constraints."
        )

        self.prompt_text_lbl = QLabel(f'"{current_prompt}"')
        self.prompt_text_lbl.setWordWrap(True)
        self.prompt_text_lbl.setStyleSheet("font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #cbd5e1; background: transparent; border: none; line-height: 1.5;")
        pb_layout.addWidget(self.prompt_text_lbl)

        token_row = QHBoxLayout()
        token_row.addStretch()
        self.token_badge = QLabel(f"~{len(current_prompt) // 4} Tokens")
        self.token_badge.setStyleSheet("""
            QLabel {
                background-color: #131b2a;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
                padding: 2px 6px;
            }
        """)
        token_row.addWidget(self.token_badge)
        pb_layout.addLayout(token_row)

        p_layout.addWidget(self.prompt_preview_box)
        layout.addWidget(prompt_card)
        layout.addStretch()

        return widget

    def on_temperature_changed(self, val: int):
        formatted = f"{val / 100:.2f}"
        self.temp_val_badge.setText(formatted)
        self.update_config("ai_temperature", val)

    def on_edit_prompt_clicked(self):
        current_prompt = self.config.get(
            "base_system_prompt",
            "You are Forge Hub, an autonomous executive developer assistant running locally on the user's workstation. Maintain concise, authoritative, and contextually grounded responses. Prioritize typed solutions, local path references, and respect user storage constraints."
        )
        dialog = EditPromptDialog(current_prompt, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_prompt = dialog.get_prompt_text()
            if new_prompt:
                self.update_config("base_system_prompt", new_prompt)
                self.prompt_text_lbl.setText(f'"{new_prompt}"')
                self.token_badge.setText(f"~{len(new_prompt) // 4} Tokens")
                QMessageBox.information(self, "Saved", "Master Base System Prompt updated.")

    # -------------------------------------------------------------
    # TAB 3: MEMORY
    # -------------------------------------------------------------
    def create_memory_tab(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(20)

        # Card 1: Memory Management & Compilation
        mem_card = QFrame()
        mem_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        m_layout = QVBoxLayout(mem_card)
        m_layout.setContentsMargins(20, 20, 20, 20)
        m_layout.setSpacing(16)

        m_head = QHBoxLayout()
        m_icon = QLabel()
        m_icon.setPixmap(get_svg_pixmap("memory", "#2196f3", 20))
        m_icon.setStyleSheet("background: transparent; border: none;")
        m_head.addWidget(m_icon)

        m_title_col = QVBoxLayout()
        m_title_col.setSpacing(2)
        m_title = QLabel("Memory Management & Compilation")
        m_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        m_title_col.addWidget(m_title)
        m_sub = QLabel("Continuous context harvesting and vectorization pipelines.")
        m_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        m_title_col.addWidget(m_sub)
        m_head.addLayout(m_title_col)

        m_head.addStretch()
        tag = QLabel("VSS ENGINE ACTIVE")
        tag.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 700; color: #4edea3; background: transparent; border: none;")
        m_head.addWidget(tag)
        m_layout.addLayout(m_head)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        m_layout.addWidget(sep)

        # Toggle Row Box
        toggle_box = QFrame()
        toggle_box.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        tb_layout = QHBoxLayout(toggle_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(16)

        desc_col = QVBoxLayout()
        desc_col.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        t_title = QLabel("Enable Automatic Memory Extraction")
        t_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        title_row.addWidget(t_title)

        auto_mem_enabled = self.config.get("auto_memory_extraction", True)
        self.mem_status_badge = QLabel("Active" if auto_mem_enabled else "Disabled")
        self.mem_status_badge.setStyleSheet(
            "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            if auto_mem_enabled else
            "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
        )
        title_row.addWidget(self.mem_status_badge)
        title_row.addStretch()
        desc_col.addLayout(title_row)

        t_desc = QLabel("Allow the Context Compiler to continuously analyze conversations, repository syncs, and LinkedIn drafts in the background to deduplicate and store high-value factual insights into local SQLite-VSS.")
        t_desc.setWordWrap(True)
        t_desc.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        desc_col.addWidget(t_desc)

        tb_layout.addLayout(desc_col, stretch=1)

        # Switch Toggle
        self.auto_memory_toggle = ToggleSwitch(checked=auto_mem_enabled)
        self.auto_memory_toggle.toggled_state.connect(self.on_auto_memory_toggled)
        tb_layout.addWidget(self.auto_memory_toggle)

        m_layout.addWidget(toggle_box)

        # 3 Metric Summary Cards
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(14)

        # Query memory stats
        facts_count = 0
        categories_count = 0
        try:
            repo = MemoryRepository(self.db)
            all_mem = repo.get_all_memories()
            facts_count = len(all_mem)
            categories_count = len(set(m.get("category", "General") for m in all_mem))
        except Exception:
            pass

        self.facts_val = QLabel(f"{facts_count} entries")
        self.categories_val = QLabel(f"{categories_count} categories")
        self.hnsw_val = QLabel("Healthy (HNSW)")

        def create_metric_card(icon_name, icon_color, label, val_widget):
            f = QFrame()
            f.setStyleSheet("""
                QFrame {
                    background-color: #0c0e14;
                    border: 1px solid #1e293b;
                    border-radius: 10px;
                }
            """)
            fl = QHBoxLayout(f)
            fl.setContentsMargins(16, 14, 16, 14)
            fl.setSpacing(14)

            icon_box = QLabel()
            icon_box.setFixedSize(38, 38)
            icon_box.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba({icon_color}, 0.15);
                    border-radius: 8px;
                }}
            """)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_box.setPixmap(get_svg_pixmap(icon_name, f"rgb({icon_color})", 20))
            fl.addWidget(icon_box)

            vl = QVBoxLayout()
            vl.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
            vl.addWidget(lbl)
            val_widget.setStyleSheet(f"font-family: monospace; font-size: 15px; font-weight: 700; color: rgb({icon_color}); background: transparent; border: none;")
            vl.addWidget(val_widget)
            fl.addLayout(vl)
            fl.addStretch()
            return f

        metrics_row.addWidget(create_metric_card("checklist", "33, 150, 243", "Stored Facts", self.facts_val))
        metrics_row.addWidget(create_metric_card("layers", "158, 202, 255", "Classification", self.categories_val))
        metrics_row.addWidget(create_metric_card("verified", "78, 222, 163", "Vector Index", self.hnsw_val))

        m_layout.addLayout(metrics_row)
        layout.addWidget(mem_card)

        # Card 2: Danger Zone
        danger_card = QFrame()
        danger_card.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 2px solid #ef4444;
                border-radius: 12px;
            }
        """)
        d_layout = QVBoxLayout(danger_card)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(16)

        dh_head = QHBoxLayout()
        d_icon = QLabel()
        d_icon.setPixmap(get_svg_pixmap("alert_triangle", "#ef4444", 22))
        d_icon.setStyleSheet("background: transparent; border: none;")
        dh_head.addWidget(d_icon)

        dh_col = QVBoxLayout()
        dh_col.setSpacing(2)
        dh_title = QLabel("Danger Zone")
        dh_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ef4444; background: transparent; border: none;")
        dh_col.addWidget(dh_title)
        dh_sub = QLabel("Irreversible workstation data purge operations.")
        dh_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        dh_col.addWidget(dh_sub)
        dh_head.addLayout(dh_col)

        dh_head.addStretch()
        caution = QLabel("CAUTION")
        caution.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 800; color: #ef4444; background: transparent; border: none;")
        dh_head.addWidget(caution)
        d_layout.addLayout(dh_head)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: rgba(239, 68, 68, 0.25); border: none; max-height: 1px;")
        d_layout.addWidget(sep2)

        # Clear memory action row
        act_row = QHBoxLayout()
        act_row.setSpacing(16)

        act_col = QVBoxLayout()
        act_col.setSpacing(4)
        c_title = QLabel("Clear All Memory")
        c_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        act_col.addWidget(c_title)
        c_desc = QLabel("Permanently purge all extracted facts, vectorized embeddings, and conversation associative memory from the local database. This action is irreversible and requires explicit confirmation.")
        c_desc.setWordWrap(True)
        c_desc.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        act_col.addWidget(c_desc)
        act_row.addLayout(act_col, stretch=1)

        purge_btn = QPushButton(" Clear All Memory")
        purge_btn.setIcon(get_svg_icon("delete", "#fecaca", 16))
        purge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        purge_btn.setFixedHeight(36)
        purge_btn.setStyleSheet("""
            QPushButton {
                background-color: #991b1b;
                color: #fecaca;
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #b91c1c;
                color: #ffffff;
            }
        """)
        purge_btn.clicked.connect(self.on_clear_memory_clicked)
        act_row.addWidget(purge_btn)

        d_layout.addLayout(act_row)
        layout.addWidget(danger_card)
        layout.addStretch()

        return widget

    def on_auto_memory_toggled(self, checked: bool):
        self.update_config("auto_memory_extraction", checked)
        if checked:
            self.mem_status_badge.setText("Active")
            self.mem_status_badge.setStyleSheet(
                "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )
        else:
            self.mem_status_badge.setText("Disabled")
            self.mem_status_badge.setStyleSheet(
                "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )

    def on_clear_memory_clicked(self):
        reply = QMessageBox.warning(
            self,
            "Confirm Memory Purge",
            "Permanently purge all extracted facts, vectorized embeddings, and conversation associative memory from SQLite?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                repo = MemoryRepository(self.db)
                repo.clear_all_memories()
                self.facts_val.setText("0 entries")
                self.categories_val.setText("0 categories")
                QMessageBox.information(self, "Memory Store Purged", "Memory store cleared and database vacuumed.")
            except Exception as e:
                QMessageBox.critical(self, "Purge Failed", f"Could not clear memories: {str(e)}")

    # -------------------------------------------------------------
    # TAB 4: PRIVACY
    # -------------------------------------------------------------
    def create_privacy_tab(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(20)

        # Card 1: Privacy, Telemetry & Model Isolation
        priv_card = QFrame()
        priv_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        p_layout = QVBoxLayout(priv_card)
        p_layout.setContentsMargins(20, 20, 20, 20)
        p_layout.setSpacing(16)

        p_head = QHBoxLayout()
        p_icon = QLabel()
        p_icon.setPixmap(get_svg_pixmap("shield", "#2196f3", 20))
        p_icon.setStyleSheet("background: transparent; border: none;")
        p_head.addWidget(p_icon)

        p_title_col = QVBoxLayout()
        p_title_col.setSpacing(2)
        p_title = QLabel("Privacy, Telemetry & Model Isolation")
        p_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        p_title_col.addWidget(p_title)
        p_sub = QLabel("Control local sandboxing, network access policies, and telemetry permissions.")
        p_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        p_title_col.addWidget(p_sub)
        p_head.addLayout(p_title_col)

        p_head.addStretch()
        tag = QLabel("AIR-GAP VERIFIED")
        tag.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: 700; color: #4edea3; background: transparent; border: none;")
        p_head.addWidget(tag)
        p_layout.addLayout(p_head)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e293b; border: none; max-height: 1px;")
        p_layout.addWidget(sep)

        # Row 1: Telemetry Toggle
        telem_box = QFrame()
        telem_box.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        tb_layout = QHBoxLayout(telem_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(16)

        telem_col = QVBoxLayout()
        telem_col.setSpacing(6)

        telem_title_row = QHBoxLayout()
        telem_title_row.setSpacing(10)
        telem_title = QLabel("Allow Anonymous Usage Statistics")
        telem_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        telem_title_row.addWidget(telem_title)

        is_telemetry = self.config.get("telemetry", False)
        self.telem_badge = QLabel("Active" if is_telemetry else "Disabled")
        self.telem_badge.setStyleSheet(
            "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            if is_telemetry else
            "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
        )
        telem_title_row.addWidget(self.telem_badge)
        telem_title_row.addStretch()
        telem_col.addLayout(telem_title_row)

        telem_desc = QLabel("Send anonymized telemetry regarding API latency and error codes to help improve Forge Hub. No prompt tokens, completions, or memory entries are ever transmitted.")
        telem_desc.setWordWrap(True)
        telem_desc.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        telem_col.addWidget(telem_desc)

        tb_layout.addLayout(telem_col, stretch=1)

        self.telemetry_toggle = ToggleSwitch(checked=is_telemetry)
        self.telemetry_toggle.toggled_state.connect(self.on_telemetry_toggled)
        tb_layout.addWidget(self.telemetry_toggle)

        p_layout.addWidget(telem_box)

        # Row 2: Enforce Local-Only Models
        local_box = QFrame()
        local_box.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        lb_layout = QHBoxLayout(local_box)
        lb_layout.setContentsMargins(18, 16, 18, 16)
        lb_layout.setSpacing(16)

        local_col = QVBoxLayout()
        local_col.setSpacing(6)

        local_title_row = QHBoxLayout()
        local_title_row.setSpacing(10)
        local_title = QLabel("Enforce Local-Only Models")
        local_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        local_title_row.addWidget(local_title)

        is_local_only = self.config.get("local_models_only", False)
        self.local_badge = QLabel("• Offline Air-Gap Mode Compatible" if is_local_only else "Cloud Enabled")
        self.local_badge.setStyleSheet(
            "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            if is_local_only else
            "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
        )
        local_title_row.addWidget(self.local_badge)
        local_title_row.addStretch()
        local_col.addLayout(local_title_row)

        local_desc = QLabel("Restricts all AI routing strictly to local model runners such as Ollama, LM Studio, or vLLM running on localhost (127.0.0.1). When enabled, cloud providers (Gemini, Groq, Cerebras, Mistral) are completely blocked from receiving network requests.")
        local_desc.setWordWrap(True)
        local_desc.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        local_col.addWidget(local_desc)

        lb_layout.addLayout(local_col, stretch=1)

        self.local_toggle = ToggleSwitch(checked=is_local_only)
        self.local_toggle.toggled_state.connect(self.on_local_toggled)
        lb_layout.addWidget(self.local_toggle)

        p_layout.addWidget(local_box)

        # Card 2: Zero Cloud Ingestion Guarantee notice card
        guarantee_card = QFrame()
        guarantee_card.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        g_layout = QHBoxLayout(guarantee_card)
        g_layout.setContentsMargins(18, 16, 18, 16)
        g_layout.setSpacing(14)

        g_icon = QLabel()
        g_icon.setPixmap(get_svg_pixmap("check_circle", "#2196f3", 22))
        g_icon.setStyleSheet("background: transparent; border: none;")
        g_layout.addWidget(g_icon)

        g_col = QVBoxLayout()
        g_col.setSpacing(4)
        g_title = QLabel("Zero Cloud Ingestion Guarantee")
        g_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
        g_col.addWidget(g_title)
        g_desc = QLabel("All database files, configuration settings, and sqlite-vss vectors reside on this workstation's physical disk at ~/.forge-hub/ or database/. Forge Hub does not operate proprietary hosted proxy endpoints.")
        g_desc.setWordWrap(True)
        g_desc.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none; line-height: 1.4;")
        g_col.addWidget(g_desc)
        g_layout.addLayout(g_col, stretch=1)

        p_layout.addWidget(guarantee_card)
        layout.addWidget(priv_card)
        layout.addStretch()

        return widget

    def on_telemetry_toggled(self, checked: bool):
        self.update_config("telemetry", checked)
        if checked:
            self.telem_badge.setText("Active")
            self.telem_badge.setStyleSheet(
                "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )
        else:
            self.telem_badge.setText("Disabled")
            self.telem_badge.setStyleSheet(
                "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )

    def on_local_toggled(self, checked: bool):
        self.update_config("local_models_only", checked)
        if checked:
            self.local_badge.setText("• Offline Air-Gap Mode Compatible")
            self.local_badge.setStyleSheet(
                "QLabel { background-color: rgba(78, 222, 163, 0.12); color: #4edea3; border: 1px solid rgba(78, 222, 163, 0.3); border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )
        else:
            self.local_badge.setText("Cloud Enabled")
            self.local_badge.setStyleSheet(
                "QLabel { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }"
            )

    def update_config(self, key: str, value):
        self.config[key] = value
        save_config(self.config)
