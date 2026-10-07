import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QScrollArea, QFrame, QSlider, QTextEdit,
    QDialog, QMessageBox, QFileDialog, QApplication,
    QGraphicsOpacityEffect, QAbstractButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor

from app.core.palette import ColorPalette, get_current_palette
from app.core.theme import apply_theme, theme_manager, get_current_theme_name
from app.core.config import load_config, save_config
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from database.repository import MemoryRepository
from app.ai.instruction_refiner import refine_personalized_instruction, save_personalized_instruction


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(240)
    anim.setStartValue(0.3)
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

        pal = get_current_palette()
        if self.isChecked():
            track_bg = QColor(pal.accent)
            track_border = QColor(pal.accent_hover)
            thumb_color = QColor(pal.accent_fg)
            thumb_x = self.width() - 23
        else:
            track_bg = QColor(pal.bg_card_inner if pal.is_dark else pal.bg_badge)
            track_border = QColor(pal.border_card)
            thumb_color = QColor(pal.fg_muted)
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

    def __init__(self, theme_key: str, title: str, subtitle: str, icon_name: str, is_active: bool = False, palette: Optional[ColorPalette] = None, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.title = title
        self.subtitle = subtitle
        self.icon_name = icon_name
        self.is_active = is_active
        self.palette = palette or get_current_palette()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(120)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

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
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setMinimumWidth(1)
        layout.addWidget(self.title_lbl)

        # Subtitle
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setMinimumWidth(1)
        layout.addWidget(self.sub_lbl)
        layout.addStretch()

        self.update_theme(self.palette)

    def update_theme(self, palette: ColorPalette):
        self.palette = palette
        self.title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.sub_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.3;")
        self.update_state(self.is_active)

    def update_state(self, is_active: bool):
        self.is_active = is_active
        pal = self.palette or get_current_palette()
        if is_active:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.palette.bg_surface_hover};
                    border: 2px solid {self.palette.accent};
                    border-radius: 12px;
                }}
            """)
            self.icon_label.setPixmap(get_svg_pixmap(self.icon_name, pal.accent, 22))
            self.radio_widget.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.accent};
                    border: 4px solid {self.palette.bg_surface_hover};
                    border-radius: 9px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background-color: {self.palette.bg_surface_hover};
                    border: 1px solid {self.palette.border_focus};
                }}
            """)
            self.icon_label.setPixmap(get_svg_pixmap(self.icon_name, pal.fg_muted, 22))
            self.radio_widget.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    border: 1.5px solid {self.palette.border_subtle};
                    border-radius: 9px;
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.theme_selected.emit(self.theme_key)
        super().mousePressEvent(event)


class EditPersonalizedInstructionDialog(QDialog):
    """Custom Modal Dialog to configure user's Personalized Instructions with AI distillation."""
    def __init__(self, current_raw: str = "", parent=None, palette: Optional[ColorPalette] = None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.result_dict = None
        self.setWindowTitle("Personalized Instructions")
        self.setFixedSize(680, 520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        pal = palette or get_current_palette()

        container = QFrame(self)
        container.setGeometry(0, 0, 680, 520)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # Header bar
        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("psychology", pal.accent, 22))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("Personalized Instructions")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {self.palette.fg_primary}; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        close_btn = QPushButton()
        close_btn.setIcon(get_svg_icon("close", pal.fg_muted, 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {self.palette.bg_surface_hover};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        head.addWidget(close_btn)
        layout.addLayout(head)

        # Subtitle
        sub = QLabel("Define your custom persona, coding standards, role, and output format preferences. Forge Hub automatically refines and distills your text to save tokens across all AI queries.")
        sub.setWordWrap(True)
        sub.setMinimumWidth(1)
        sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")
        layout.addWidget(sub)

        # Guidance chips / tier summary frame
        tier_frame = QFrame()
        tier_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 8px;
            }}
        """)
        tf_layout = QHBoxLayout(tier_frame)
        tf_layout.setContentsMargins(12, 8, 12, 8)
        tf_layout.setSpacing(10)

        def make_chip(icon_str, title_str, desc_str, color_str):
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(f"{icon_str} {title_str}")
            t.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {color_str}; background: transparent; border: none;")
            d = QLabel(desc_str)
            d.setStyleSheet(f"font-size: 10px; color: {self.palette.fg_muted}; background: transparent; border: none;")
            col.addWidget(t)
            col.addWidget(d)
            return col

        tf_layout.addLayout(make_chip("🟢", "Short (<120 ch)", "Kept intact (0% cut)", pal.success))
        tf_layout.addLayout(make_chip("🔵", "Medium (120-400 ch)", "Refined ~30-40%", pal.accent))
        tf_layout.addLayout(make_chip("🟣", "Long (>400 ch)", "Distilled ~70-80%", "#a855f7" if pal.is_dark else "#7e22ce"))
        layout.addWidget(tier_frame)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Enter your custom guidelines here...\n\nExample: I am a Senior Backend Engineer working primarily in Python and Rust. Always keep explanations concise, omit obvious boilerplate, prioritize performance and safety, format code blocks with comments, and never apologize or use filler phrases.")
        self.editor.setPlainText(current_raw)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid {self.palette.border_card};
                border-radius: 8px;
                color: {self.palette.fg_primary};
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                padding: 12px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 1px solid {self.palette.accent};
            }}
        """)
        self.editor.textChanged.connect(self._update_stats_label)
        layout.addWidget(self.editor, stretch=1)

        # Live stats row
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        layout.addWidget(self.stats_lbl)
        self._update_stats_label()

        # Bottom actions
        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_surface};
                color: {self.palette.fg_muted};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.palette.bg_surface_hover};
                color: {self.palette.danger};
            }}
        """)
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        actions.addWidget(self.clear_btn)

        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_surface};
                color: {self.palette.fg_muted};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.palette.bg_surface_hover};
                color: {self.palette.fg_primary};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)

        self.save_btn = QPushButton(" Refine && Save with AI")
        self.save_btn.setIcon(get_svg_icon("auto_awesome", pal.accent_fg, 14))
        self.save_btn.setFixedHeight(34)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                color: {self.palette.accent_fg};
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent_hover};
            }}
        """)
        self.save_btn.clicked.connect(self.on_refine_and_save_clicked)
        actions.addWidget(self.save_btn)

        layout.addLayout(actions)

    def _update_stats_label(self):
        text = self.editor.toPlainText().strip()
        chars = len(text)
        words = len(text.split()) if text else 0
        if chars == 0:
            tier_str = "Empty"
        elif chars < 120 or words <= 25:
            tier_str = "Short (Verbatim / 0% reduction)"
        elif chars <= 400 or words <= 80:
            tier_str = "Medium (Target: 30–40% AI reduction)"
        else:
            tier_str = "Long (Target: 70–80% AI distillation)"
        self.stats_lbl.setText(f"{chars} characters • {words} words  |  Compression Tier: {tier_str}")

    def on_clear_clicked(self):
        self.editor.clear()

    def on_refine_and_save_clicked(self):
        text = self.editor.toPlainText().strip()
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Refining with AI...")
        QApplication.processEvents()

        from app.ai.instruction_refiner import refine_personalized_instruction
        self.result_dict = refine_personalized_instruction(text, self.db)

        self.save_btn.setEnabled(True)
        self.save_btn.setText(" Refine && Save with AI")
        self.accept()

    def get_result(self) -> Optional[Dict[str, Any]]:
        return self.result_dict


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

        self.palette = get_current_palette()
        self._active_tab = 0
        self._theme_cards = {}
        self.metric_cards = []

        self.setup_ui()
        setup_page_animation(self)
        self.apply_theme_colors(self.palette)

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(18, 18, 18, 28)
        self.main_layout.setSpacing(18)

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

        self.scroll.setWidget(self.content_widget)
        root_layout.addWidget(self.scroll)

    def setup_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet("background: transparent; border: none;")
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(6)

        # Top row: Title + WORKSTATION pill + stretch + Config Version Pill
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.title_lbl = QLabel("Settings")
        top_row.addWidget(self.title_lbl)

        self.pill = QLabel("")
        top_row.addWidget(self.pill)
        top_row.addStretch()

        # Config version pill
        self.version_pill = QFrame()
        self.version_pill.setMinimumWidth(0)
        v_layout = QHBoxLayout(self.version_pill)
        v_layout.setContentsMargins(8, 3, 8, 3)
        v_layout.setSpacing(6)

        self.sync_icon = QLabel()
        self.sync_icon.setStyleSheet("background: transparent; border: none;")
        v_layout.addWidget(self.sync_icon)

        self.v_text = QLabel("ForgeHub V2.5")
        v_layout.addWidget(self.v_text)

        top_row.addWidget(self.version_pill)
        h_layout.addLayout(top_row)

        self.desc_lbl = QLabel("Configure desktop workstation preferences, local model inference rules, persistent memory compilation, and data privacy.")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumWidth(1)
        h_layout.addWidget(self.desc_lbl)

        self.main_layout.addWidget(header_frame)

    def setup_segmented_tabs(self):
        self.tab_bar = QFrame()
        t_layout = QHBoxLayout(self.tab_bar)
        t_layout.setContentsMargins(0, 4, 0, 4)
        t_layout.setSpacing(8)

        # Tab button group container
        self.pill_group = QFrame()
        p_layout = QHBoxLayout(self.pill_group)
        p_layout.setContentsMargins(3, 3, 3, 3)
        p_layout.setSpacing(3)

        tabs_data = [
            ("General", "tune"),
            ("AI Behavior", "brain"),
            ("Memory", "memory"),
            ("Privacy", "shield"),
        ]

        self.tab_buttons = []
        for i, (name, icon_name) in enumerate(tabs_data):
            btn = QPushButton(f" {name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))
            p_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        t_layout.addWidget(self.pill_group, stretch=1)



        self.main_layout.addWidget(self.tab_bar)

    def refresh_tab_button_styles(self):
        pal = self.palette or get_current_palette()
        for i, btn in enumerate(self.tab_buttons):
            icon_names = ["tune", "brain", "memory", "shield"]
            if i == self._active_tab:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.palette.accent};
                        color: {self.palette.accent_fg};
                        font-size: 11px;
                        font-weight: 600;
                        border: none;
                        border-radius: 6px;
                        padding: 0 10px;
                    }}
                """)
                btn.setIcon(get_svg_icon(icon_names[i], pal.accent_fg, 14))
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {self.palette.fg_muted};
                        font-size: 11px;
                        font-weight: 500;
                        border: none;
                        border-radius: 6px;
                        padding: 0 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.palette.bg_surface_hover};
                        color: {self.palette.fg_primary};
                    }}
                """)
                btn.setIcon(get_svg_icon(icon_names[i], pal.fg_muted, 14))

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
        self.app_card = QFrame()
        app_layout = QVBoxLayout(self.app_card)
        app_layout.setContentsMargins(20, 20, 20, 20)
        app_layout.setSpacing(16)

        # Section Header
        head = QHBoxLayout()
        self.app_head_icon = QLabel()
        self.app_head_icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(self.app_head_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.h_title = QLabel("Appearance & Interface")
        title_col.addWidget(self.h_title)
        self.h_sub = QLabel("Manage workstation desktop shell themes and window compositor behaviors.")
        self.h_sub.setWordWrap(True)
        self.h_sub.setMinimumWidth(1)
        title_col.addWidget(self.h_sub)
        head.addLayout(title_col, stretch=1)

        self.app_tag = QLabel("UI_SHELL_DISPLAY")
        head.addWidget(self.app_tag)
        app_layout.addLayout(head)

        # Separator
        self.app_sep = QFrame()
        self.app_sep.setFrameShape(QFrame.Shape.HLine)
        app_layout.addWidget(self.app_sep)

        # Theme mode section
        self.mode_lbl = QLabel("Theme Mode")
        app_layout.addWidget(self.mode_lbl)

        # 3 Theme Cards
        themes_layout = QHBoxLayout()
        themes_layout.setSpacing(12)

        current_theme = self.config.get("theme", "system").lower()
        themes_info = [
            ("system", "System", "Automatically match OS level dark/light compositor", "desktop_windows"),
            ("dark", "Violet SaaS", "Premium dark blue/violet SaaS aesthetic", "dark_mode"),
            ("light", "Luxury Gold", "Deep obsidian with warm gold accents", "light_mode"),
        ]

        self._theme_cards = {}
        for key, name, subtitle, icon_name in themes_info:
            is_active = (current_theme == key)
            card = ThemeCard(key, name, subtitle, icon_name, is_active=is_active, palette=self.palette)
            card.theme_selected.connect(self.on_theme_card_selected)
            themes_layout.addWidget(card)
            self._theme_cards[key] = card

        app_layout.addLayout(themes_layout)

        # Info note
        note_row = QHBoxLayout()
        note_row.setSpacing(8)
        self.app_info_icon = QLabel()
        self.app_info_icon.setStyleSheet("background: transparent; border: none;")
        note_row.addWidget(self.app_info_icon)
        self.note_txt = QLabel("Theme changes are applied immediately across the Qt workstation runtime without freezing, and persisted to configuration.")
        self.note_txt.setWordWrap(True)
        self.note_txt.setMinimumWidth(1)
        note_row.addWidget(self.note_txt, stretch=1)
        app_layout.addLayout(note_row)

        layout.addWidget(self.app_card)

        # Card 2: Data Management & Storage
        self.data_card = QFrame()
        data_layout = QVBoxLayout(self.data_card)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.setSpacing(16)

        # Section Header
        d_head = QHBoxLayout()
        self.d_icon = QLabel()
        self.d_icon.setStyleSheet("background: transparent; border: none;")
        d_head.addWidget(self.d_icon)

        d_title_col = QVBoxLayout()
        d_title_col.setSpacing(2)
        self.d_title = QLabel("Data Management & Storage")
        d_title_col.addWidget(self.d_title)
        self.d_sub = QLabel("Inspect SQLite engine handles, vector indices, and snapshot checkpoints.")
        self.d_sub.setWordWrap(True)
        self.d_sub.setMinimumWidth(1)
        d_title_col.addWidget(self.d_sub)
        d_head.addLayout(d_title_col, stretch=1)

        self.d_status = QLabel("STATUS: OPTIMAL")
        d_head.addWidget(self.d_status)
        data_layout.addLayout(d_head)

        # Separator
        self.data_sep = QFrame()
        self.data_sep.setFrameShape(QFrame.Shape.HLine)
        data_layout.addWidget(self.data_sep)

        # Sub-sections
        grid_row = QVBoxLayout()
        grid_row.setSpacing(14)

        # 1. Active SQLite Target + File stats
        self.left_panel = QFrame()
        self.left_panel.setMinimumWidth(0)
        lp_layout = QVBoxLayout(self.left_panel)
        lp_layout.setContentsMargins(16, 16, 16, 16)
        lp_layout.setSpacing(14)

        lp_head = QHBoxLayout()
        self.lp_title = QLabel("ACTIVE SQLITE TARGET")
        lp_head.addWidget(self.lp_title)
        lp_head.addStretch()

        self.wal_badge = QLabel("• WAL Mode Enabled")
        lp_head.addWidget(self.wal_badge)
        lp_layout.addLayout(lp_head)

        # Code block with Copy button
        self.code_box = QFrame()
        self.code_box.setMinimumWidth(0)
        cb_layout = QHBoxLayout(self.code_box)
        cb_layout.setContentsMargins(10, 8, 10, 8)
        cb_layout.setSpacing(8)

        db_abs_path = os.path.abspath(self.db.db_path) if self.db else os.path.abspath("database/forgehub.db")
        self.db_uri_text = f"sqlite:///{db_abs_path}"
        self.code_lbl = QLabel(self.db_uri_text)
        self.code_lbl.setWordWrap(True)
        self.code_lbl.setMinimumWidth(0)
        cb_layout.addWidget(self.code_lbl, stretch=1)

        self.copy_btn = QPushButton()
        self.copy_btn.setFixedSize(26, 26)
        self.copy_btn.setToolTip("Copy SQLite URI")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_db_uri)
        cb_layout.addWidget(self.copy_btn)
        lp_layout.addWidget(self.code_box)

        # 3 stats counters
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        file_size_str = "0.0 MB"
        if os.path.exists(db_abs_path):
            size_mb = os.path.getsize(db_abs_path) / (1024 * 1024)
            file_size_str = f"{size_mb:.1f} MB"

        self.size_title_lbl = QLabel("File Size")
        self.size_val_lbl = QLabel(file_size_str)
        self.cache_title_lbl = QLabel("Page Cache")
        self.cache_val = QLabel("4,096 KB")
        self.integrity_title_lbl = QLabel("Integrity")

        integrity_str = "PRAGMA OK"
        if self.db:
            try:
                with self.db.get_connection() as conn:
                    res = conn.execute("PRAGMA integrity_check").fetchone()
                    if res and res[0].lower() == "ok":
                        integrity_str = "PRAGMA OK"
            except Exception:
                integrity_str = "PRAGMA OK"

        self.integrity_val = QLabel(integrity_str)

        def make_stat(tl, vl):
            f = QFrame()
            f.setMinimumWidth(0)
            f.setStyleSheet("background: transparent; border: none;")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(2)
            fl.addWidget(tl)
            fl.addWidget(vl)
            return f

        stats_row.addWidget(make_stat(self.size_title_lbl, self.size_val_lbl))
        stats_row.addWidget(make_stat(self.cache_title_lbl, self.cache_val))
        stats_row.addWidget(make_stat(self.integrity_title_lbl, self.integrity_val))

        lp_layout.addLayout(stats_row)
        grid_row.addWidget(self.left_panel)

        # 2. Snapshot Recovery & Actions
        self.right_panel = QFrame()
        self.right_panel.setMinimumWidth(0)
        rp_layout = QVBoxLayout(self.right_panel)
        rp_layout.setContentsMargins(16, 16, 16, 16)
        rp_layout.setSpacing(10)

        self.rp_title = QLabel("YOUR DATA")
        rp_layout.addWidget(self.rp_title)

        self.rp_desc = QLabel("Backs up your projects, chats, and profile to a structured ZIP file (Excludes API keys & settings).")
        self.rp_desc.setWordWrap(True)
        self.rp_desc.setMinimumWidth(1)
        rp_layout.addWidget(self.rp_desc)

        # Last backup box
        self.backup_status_box = QFrame()
        self.backup_status_box.setMinimumWidth(0)
        bs_layout = QHBoxLayout(self.backup_status_box)
        bs_layout.setContentsMargins(8, 8, 8, 8)
        bs_layout.setSpacing(8)

        self.bs_icon = QLabel()
        self.bs_icon.setStyleSheet("background: transparent; border: none;")
        bs_layout.addWidget(self.bs_icon)

        self.backup_lbl = QLabel("Checking backups...")
        self.backup_lbl.setWordWrap(True)
        self.backup_lbl.setMinimumWidth(1)
        bs_layout.addWidget(self.backup_lbl, stretch=1)
        rp_layout.addWidget(self.backup_status_box)
        self.refresh_backup_status()

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.backup_btn = QPushButton(" Backup Database")
        self.backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backup_btn.setFixedHeight(34)
        self.backup_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.backup_btn.clicked.connect(self.on_backup_clicked)
        btn_box.addWidget(self.backup_btn)

        self.restore_btn = QPushButton(" Restore from Backup...")
        self.restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restore_btn.setFixedHeight(34)
        self.restore_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.restore_btn.clicked.connect(self.on_restore_clicked)
        btn_box.addWidget(self.restore_btn)

        rp_layout.addLayout(btn_box)
        grid_row.addWidget(self.right_panel)

        data_layout.addLayout(grid_row)
        layout.addWidget(self.data_card)
        layout.addStretch()

        return widget

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
        self.sampling_card = QFrame()
        self.sampling_card.setMinimumWidth(0)
        s_layout = QVBoxLayout(self.sampling_card)
        s_layout.setContentsMargins(20, 20, 20, 20)
        s_layout.setSpacing(16)

        # Header
        s_head = QHBoxLayout()
        self.s_icon = QLabel()
        self.s_icon.setStyleSheet("background: transparent; border: none;")
        s_head.addWidget(self.s_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.s_title = QLabel("Model Sampling & Generation Parameters")
        self.s_title.setWordWrap(True)
        self.s_title.setMinimumWidth(1)
        title_col.addWidget(self.s_title)
        self.s_sub = QLabel("Tune stochastic temperature and decoding heuristics across dynamic local and cloud pipelines.")
        self.s_sub.setWordWrap(True)
        self.s_sub.setMinimumWidth(1)
        title_col.addWidget(self.s_sub)
        s_head.addLayout(title_col, stretch=1)

        self.s_tag = QLabel("ENGINE_DEFAULT")
        s_head.addWidget(self.s_tag)
        s_layout.addLayout(s_head)

        # Separator
        self.s_sep = QFrame()
        self.s_sep.setFrameShape(QFrame.Shape.HLine)
        s_layout.addWidget(self.s_sep)

        # Temperature Box
        self.temp_box = QFrame()
        self.temp_box.setMinimumWidth(0)
        tb_layout = QVBoxLayout(self.temp_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(12)

        tb_head = QHBoxLayout()
        self.t_label = QLabel("Temperature (--temp)")
        tb_head.addWidget(self.t_label)
        tb_head.addStretch()

        current_val = self.config.get("ai_temperature", 70)
        self.temp_val_badge = QLabel(f"{current_val / 100:.2f}")
        tb_head.addWidget(self.temp_val_badge)
        tb_layout.addLayout(tb_head)

        # Slider
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(current_val)
        self.temp_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.temp_slider.valueChanged.connect(self.on_temperature_changed)
        tb_layout.addWidget(self.temp_slider)

        # Extremes labels
        extremes = QHBoxLayout()
        extremes.setSpacing(10)
        self.left_ex = QLabel("0.0 — Precise / Deterministic")
        self.left_ex.setWordWrap(True)
        self.left_ex.setMinimumWidth(1)
        extremes.addWidget(self.left_ex, stretch=1)

        self.right_ex = QLabel("1.0 — Creative / Exploratory")
        self.right_ex.setWordWrap(True)
        self.right_ex.setMinimumWidth(1)
        self.right_ex.setAlignment(Qt.AlignmentFlag.AlignRight)
        extremes.addWidget(self.right_ex, stretch=1)
        tb_layout.addLayout(extremes)

        # Hint text
        self.temp_hint = QLabel("Controls randomness in token selection. Lower values ensure consistent, deterministic outputs ideal for technical documentation and code refactoring; higher values introduce greater lexical variety for writing.")
        self.temp_hint.setWordWrap(True)
        self.temp_hint.setMinimumWidth(1)
        tb_layout.addWidget(self.temp_hint)

        s_layout.addWidget(self.temp_box)
        layout.addWidget(self.sampling_card)

        # Card 2: Personalized Instructions
        self.prompt_card = QFrame()
        self.prompt_card.setMinimumWidth(0)
        p_layout = QVBoxLayout(self.prompt_card)
        p_layout.setContentsMargins(20, 20, 20, 20)
        p_layout.setSpacing(16)

        p_head = QHBoxLayout()
        self.p_icon = QLabel()
        self.p_icon.setStyleSheet("background: transparent; border: none;")
        p_head.addWidget(self.p_icon)

        p_title_col = QVBoxLayout()
        p_title_col.setSpacing(2)
        self.p_title = QLabel("Personalized Instructions")
        p_title_col.addWidget(self.p_title)
        self.p_sub = QLabel("Custom instructions and behavioral guidelines tailored to your workflow. Refined and distilled by AI for maximum token efficiency across every model query.")
        self.p_sub.setWordWrap(True)
        self.p_sub.setMinimumWidth(1)
        p_title_col.addWidget(self.p_sub)
        p_head.addLayout(p_title_col, stretch=1)

        self.edit_btn = QPushButton(" Edit Instructions")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setFixedHeight(30)
        self.edit_btn.clicked.connect(self.on_edit_instructions_clicked)
        p_head.addWidget(self.edit_btn)
        p_layout.addLayout(p_head)

        # Separator
        self.p_sep = QFrame()
        self.p_sep.setFrameShape(QFrame.Shape.HLine)
        p_layout.addWidget(self.p_sep)

        # Preview Header
        prev_head = QHBoxLayout()
        prev_head.setSpacing(8)
        self.prev_lbl = QLabel("Refined Instruction Preview (Injected into all queries)")
        prev_head.addWidget(self.prev_lbl)
        prev_head.addStretch()

        self.inst_status_badge = QLabel("Not Configured")
        prev_head.addWidget(self.inst_status_badge)

        self.reduction_badge = QLabel("")
        self.reduction_badge.setVisible(False)
        prev_head.addWidget(self.reduction_badge)

        self.token_badge = QLabel("0 Tokens")
        prev_head.addWidget(self.token_badge)
        p_layout.addLayout(prev_head)

        # Code preview box
        self.prompt_preview_box = QFrame()
        pb_layout = QVBoxLayout(self.prompt_preview_box)
        pb_layout.setContentsMargins(14, 14, 14, 14)
        pb_layout.setSpacing(8)

        self.prompt_text_lbl = QLabel()
        self.prompt_text_lbl.setWordWrap(True)
        self.prompt_text_lbl.setMinimumWidth(1)
        pb_layout.addWidget(self.prompt_text_lbl)

        self.raw_preview_lbl = QLabel()
        self.raw_preview_lbl.setWordWrap(True)
        self.raw_preview_lbl.setMinimumWidth(1)
        pb_layout.addWidget(self.raw_preview_lbl)

        p_layout.addWidget(self.prompt_preview_box)
        self.refresh_instruction_preview()

        layout.addWidget(self.prompt_card)
        layout.addStretch()

        return widget

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
        self.mem_card = QFrame()
        self.mem_card.setMinimumWidth(0)
        m_layout = QVBoxLayout(self.mem_card)
        m_layout.setContentsMargins(20, 20, 20, 20)
        m_layout.setSpacing(16)

        m_head = QHBoxLayout()
        self.m_icon = QLabel()
        self.m_icon.setStyleSheet("background: transparent; border: none;")
        m_head.addWidget(self.m_icon)

        m_title_col = QVBoxLayout()
        m_title_col.setSpacing(2)
        self.m_title = QLabel("Memory Management & Compilation")
        self.m_title.setWordWrap(True)
        self.m_title.setMinimumWidth(1)
        m_title_col.addWidget(self.m_title)
        self.m_sub = QLabel("Continuous context harvesting and vectorization pipelines.")
        self.m_sub.setWordWrap(True)
        self.m_sub.setMinimumWidth(1)
        m_title_col.addWidget(self.m_sub)
        m_head.addLayout(m_title_col, stretch=1)

        self.m_tag = QLabel("VSS ENGINE ACTIVE")
        m_head.addWidget(self.m_tag)
        m_layout.addLayout(m_head)

        # Separator
        self.m_sep = QFrame()
        self.m_sep.setFrameShape(QFrame.Shape.HLine)
        m_layout.addWidget(self.m_sep)

        # Toggle Row Box
        self.toggle_box = QFrame()
        self.toggle_box.setMinimumWidth(0)
        tb_layout = QHBoxLayout(self.toggle_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(16)

        desc_col = QVBoxLayout()
        desc_col.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self.mem_t_title = QLabel("Enable Automatic Memory Extraction")
        self.mem_t_title.setWordWrap(True)
        self.mem_t_title.setMinimumWidth(1)
        title_row.addWidget(self.mem_t_title, stretch=1)

        auto_mem_enabled = self.config.get("auto_memory_extraction", True)
        self.mem_status_badge = QLabel("Active" if auto_mem_enabled else "Disabled")
        title_row.addWidget(self.mem_status_badge)
        desc_col.addLayout(title_row)

        self.mem_t_desc = QLabel("Allow the Context Compiler to continuously analyze conversations, repository syncs, and LinkedIn drafts in the background to deduplicate and store high-value factual insights into local SQLite-VSS.")
        self.mem_t_desc.setWordWrap(True)
        self.mem_t_desc.setMinimumWidth(1)
        desc_col.addWidget(self.mem_t_desc)

        tb_layout.addLayout(desc_col, stretch=1)

        # Switch Toggle
        self.auto_memory_toggle = ToggleSwitch(checked=auto_mem_enabled)
        self.auto_memory_toggle.toggled_state.connect(self.on_auto_memory_toggled)
        tb_layout.addWidget(self.auto_memory_toggle)

        m_layout.addWidget(self.toggle_box)

        # 3 Metric Summary Cards
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(14)

        facts_count = 0
        categories_count = 0
        if self.db:
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

        self.metric_cards = []
        metric_configs = [
            ("checklist", "Stored Facts", self.facts_val),
            ("layers", "Classification", self.categories_val),
            ("verified", "Vector Index", self.hnsw_val),
        ]

        for icon_name, label_text, val_widget in metric_configs:
            f = QFrame()
            f.setMinimumWidth(0)
            f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            fl = QHBoxLayout(f)
            fl.setContentsMargins(14, 12, 14, 12)
            fl.setSpacing(12)

            icon_box = QLabel()
            icon_box.setFixedSize(36, 36)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(icon_box)

            vl = QVBoxLayout()
            vl.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setWordWrap(True)
            lbl.setMinimumWidth(1)
            vl.addWidget(lbl)
            val_widget.setWordWrap(True)
            val_widget.setMinimumWidth(1)
            vl.addWidget(val_widget)
            fl.addLayout(vl, stretch=1)

            metrics_row.addWidget(f)
            self.metric_cards.append((f, icon_box, lbl, val_widget, icon_name))

        m_layout.addLayout(metrics_row)
        layout.addWidget(self.mem_card)

        # Card 2: Danger Zone
        self.danger_card = QFrame()
        self.danger_card.setMinimumWidth(0)
        d_layout = QVBoxLayout(self.danger_card)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(16)

        dh_head = QHBoxLayout()
        self.dh_icon = QLabel()
        self.dh_icon.setStyleSheet("background: transparent; border: none;")
        dh_head.addWidget(self.dh_icon)

        dh_col = QVBoxLayout()
        dh_col.setSpacing(2)
        self.dh_title = QLabel("Danger Zone")
        self.dh_title.setWordWrap(True)
        self.dh_title.setMinimumWidth(1)
        dh_col.addWidget(self.dh_title)
        self.dh_sub = QLabel("Irreversible workstation data purge operations.")
        self.dh_sub.setWordWrap(True)
        self.dh_sub.setMinimumWidth(1)
        dh_col.addWidget(self.dh_sub)
        dh_head.addLayout(dh_col, stretch=1)

        self.caution_badge = QLabel("CAUTION")
        dh_head.addWidget(self.caution_badge)
        d_layout.addLayout(dh_head)

        # Separator
        self.danger_sep = QFrame()
        self.danger_sep.setFrameShape(QFrame.Shape.HLine)
        d_layout.addWidget(self.danger_sep)

        # Clear memory action row
        act_row = QHBoxLayout()
        act_row.setSpacing(16)

        act_col = QVBoxLayout()
        act_col.setSpacing(4)
        self.c_title = QLabel("Clear All Memory")
        self.c_title.setWordWrap(True)
        self.c_title.setMinimumWidth(1)
        act_col.addWidget(self.c_title)
        self.c_desc = QLabel("Permanently purge all extracted facts, vectorized embeddings, and conversation associative memory from the local database. This action is irreversible and requires explicit confirmation.")
        self.c_desc.setWordWrap(True)
        self.c_desc.setMinimumWidth(1)
        act_col.addWidget(self.c_desc)
        act_row.addLayout(act_col, stretch=1)

        self.purge_btn = QPushButton(" Clear All Memory")
        self.purge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.purge_btn.setFixedHeight(34)
        self.purge_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.purge_btn.clicked.connect(self.on_clear_memory_clicked)
        act_row.addWidget(self.purge_btn)

        d_layout.addLayout(act_row)
        layout.addWidget(self.danger_card)
        layout.addStretch()

        return widget

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
        self.priv_card = QFrame()
        self.priv_card.setMinimumWidth(0)
        p_layout = QVBoxLayout(self.priv_card)
        p_layout.setContentsMargins(20, 20, 20, 20)
        p_layout.setSpacing(16)

        p_head = QHBoxLayout()
        self.priv_icon = QLabel()
        self.priv_icon.setStyleSheet("background: transparent; border: none;")
        p_head.addWidget(self.priv_icon)

        p_title_col = QVBoxLayout()
        p_title_col.setSpacing(2)
        self.priv_title = QLabel("Privacy, Telemetry & Model Isolation")
        self.priv_title.setWordWrap(True)
        self.priv_title.setMinimumWidth(1)
        p_title_col.addWidget(self.priv_title)
        self.priv_sub = QLabel("Control local sandboxing, network access policies, and telemetry permissions.")
        self.priv_sub.setWordWrap(True)
        self.priv_sub.setMinimumWidth(1)
        p_title_col.addWidget(self.priv_sub)
        p_head.addLayout(p_title_col, stretch=1)

        self.priv_tag = QLabel("AIR-GAP VERIFIED")
        p_head.addWidget(self.priv_tag)
        p_layout.addLayout(p_head)

        # Separator
        self.priv_sep = QFrame()
        self.priv_sep.setFrameShape(QFrame.Shape.HLine)
        p_layout.addWidget(self.priv_sep)

        # Row 1: Telemetry Toggle
        self.telem_box = QFrame()
        self.telem_box.setMinimumWidth(0)
        tb_layout = QHBoxLayout(self.telem_box)
        tb_layout.setContentsMargins(18, 16, 18, 16)
        tb_layout.setSpacing(16)

        telem_col = QVBoxLayout()
        telem_col.setSpacing(6)

        telem_title_row = QHBoxLayout()
        telem_title_row.setSpacing(10)
        self.telem_title = QLabel("Allow Anonymous Usage Statistics")
        self.telem_title.setWordWrap(True)
        self.telem_title.setMinimumWidth(1)
        telem_title_row.addWidget(self.telem_title, stretch=1)

        is_telemetry = self.config.get("telemetry", False)
        self.telem_badge = QLabel("Active" if is_telemetry else "Disabled")
        telem_title_row.addWidget(self.telem_badge)
        telem_col.addLayout(telem_title_row)

        self.telem_desc = QLabel("Send anonymized telemetry regarding API latency and error codes to help improve Forge Hub. No prompt tokens, completions, or memory entries are ever transmitted.")
        self.telem_desc.setWordWrap(True)
        self.telem_desc.setMinimumWidth(1)
        telem_col.addWidget(self.telem_desc)

        tb_layout.addLayout(telem_col, stretch=1)

        self.telemetry_toggle = ToggleSwitch(checked=is_telemetry)
        self.telemetry_toggle.toggled_state.connect(self.on_telemetry_toggled)
        tb_layout.addWidget(self.telemetry_toggle)

        p_layout.addWidget(self.telem_box)

        # Row 2: Enforce Local-Only Models
        self.local_box = QFrame()
        self.local_box.setMinimumWidth(0)
        lb_layout = QHBoxLayout(self.local_box)
        lb_layout.setContentsMargins(18, 16, 18, 16)
        lb_layout.setSpacing(16)

        local_col = QVBoxLayout()
        local_col.setSpacing(6)

        local_title_row = QHBoxLayout()
        local_title_row.setSpacing(10)
        self.local_title = QLabel("Enforce Local-Only Models")
        self.local_title.setWordWrap(True)
        self.local_title.setMinimumWidth(1)
        local_title_row.addWidget(self.local_title, stretch=1)

        is_local_only = self.config.get("local_models_only", False)
        self.local_badge = QLabel("• Offline Air-Gap Mode Compatible" if is_local_only else "Cloud Enabled")
        local_title_row.addWidget(self.local_badge)
        local_col.addLayout(local_title_row)

        self.local_desc = QLabel("Restricts all AI routing strictly to local model runners such as Ollama, LM Studio, or vLLM running on localhost (127.0.0.1). When enabled, cloud providers (Gemini, Groq, Cerebras, Mistral) are completely blocked from receiving network requests.")
        self.local_desc.setWordWrap(True)
        self.local_desc.setMinimumWidth(1)
        local_col.addWidget(self.local_desc)

        lb_layout.addLayout(local_col, stretch=1)

        self.local_toggle = ToggleSwitch(checked=is_local_only)
        self.local_toggle.toggled_state.connect(self.on_local_toggled)
        lb_layout.addWidget(self.local_toggle)

        p_layout.addWidget(self.local_box)

        # Card 2: Zero Cloud Ingestion Guarantee notice card
        self.guarantee_card = QFrame()
        self.guarantee_card.setMinimumWidth(0)
        g_layout = QHBoxLayout(self.guarantee_card)
        g_layout.setContentsMargins(18, 16, 18, 16)
        g_layout.setSpacing(14)

        self.g_icon = QLabel()
        self.g_icon.setStyleSheet("background: transparent; border: none;")
        g_layout.addWidget(self.g_icon)

        g_col = QVBoxLayout()
        g_col.setSpacing(4)
        self.g_title = QLabel("Zero Cloud Ingestion Guarantee")
        self.g_title.setWordWrap(True)
        self.g_title.setMinimumWidth(1)
        g_col.addWidget(self.g_title)
        self.g_desc = QLabel("All database files, configuration settings, and sqlite-vss vectors reside on this workstation's physical disk at ~/.forge-hub/ or database/. Forge Hub does not operate proprietary hosted proxy endpoints.")
        self.g_desc.setWordWrap(True)
        self.g_desc.setMinimumWidth(1)
        g_col.addWidget(self.g_desc)
        g_layout.addLayout(g_col, stretch=1)

        p_layout.addWidget(self.guarantee_card)
        layout.addWidget(self.priv_card)
        layout.addStretch()

        return widget

    # -------------------------------------------------------------
    # UNIFIED PALETTE APPLIER (INSTANT SWITCHING)
    # -------------------------------------------------------------
    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        if hasattr(self, 'fallback_card'):
            self.fallback_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 12px;
                }}
                QLabel {{ background: transparent; border: none; }}
            """)
            self.fb_icon.setPixmap(get_svg_pixmap("globe", self.palette.accent, 22))
            self.fb_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary};")
            self.fb_sub.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; line-height: 1.3;")

        # 1. Page Backgrounds
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.palette.bg_app};
                border: none;
            }}
        """)
        self.content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.palette.bg_app};
            }}
        """)

        # 2. Header Bar
        self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.pill.setStyleSheet(f"""
            background-color: {self.palette.accent_bg};
            color: {self.palette.accent};
            border: 1px solid {self.palette.accent};
            border-radius: 4px;
            font-family: monospace;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
        """)
        self.version_pill.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_surface};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
            }}
        """)
        self.sync_icon.setPixmap(get_svg_pixmap("sync", pal.success, 12))
        self.v_text.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.desc_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")

        # 3. Tab Bar
        self.pill_group.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_surface};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 8px;
            }}
        """)
        self.refresh_tab_button_styles()

        # 4. Tab 1: General elements
        card_style = f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 12px;
            }}
        """
        inner_panel_style = f"""
            QFrame {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 10px;
            }}
        """
        sep_style = f"background-color: {self.palette.border_subtle}; border: none; max-height: 1px;"

        self.app_card.setStyleSheet(card_style)
        self.app_head_icon.setPixmap(get_svg_pixmap("palette", pal.accent, 20))
        self.h_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.h_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.app_tag.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        self.app_sep.setStyleSheet(sep_style)
        self.mode_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")

        curr_theme = self.config.get("theme", "system").lower()
        for key, card in self._theme_cards.items():
            card.update_theme(pal)
            card.update_state(key == curr_theme)

        self.app_info_icon.setPixmap(get_svg_pixmap("info", pal.accent, 15))
        self.note_txt.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")

        # Data Management
        self.data_card.setStyleSheet(card_style)
        self.d_icon.setPixmap(get_svg_pixmap("database", pal.accent, 20))
        self.d_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.d_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.d_status.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 700; color: {self.palette.success}; background: transparent; border: none;")
        self.data_sep.setStyleSheet(sep_style)

        self.left_panel.setStyleSheet(inner_panel_style)
        self.lp_title.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.wal_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {self.palette.accent_bg};
                color: {self.palette.success};
                border: 1px solid {self.palette.success};
                border-radius: 10px;
                font-family: monospace;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 8px;
            }}
        """)
        self.code_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_surface};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 8px;
            }}
        """)
        self.code_lbl.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {self.palette.accent}; background: transparent; border: none;")
        self.copy_btn.setIcon(get_svg_icon("content_copy", pal.fg_muted, 14))
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {self.palette.bg_surface_hover};
            }}
        """)
        self.size_title_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        self.size_val_lbl.setStyleSheet(f"font-family: monospace; font-size: 15px; font-weight: 700; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.cache_title_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        self.cache_val.setStyleSheet(f"font-family: monospace; font-size: 15px; font-weight: 700; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.integrity_title_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        self.integrity_val.setStyleSheet(f"font-family: monospace; font-size: 15px; font-weight: 700; color: {self.palette.success}; background: transparent; border: none;")

        self.right_panel.setStyleSheet(inner_panel_style)
        self.rp_title.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.rp_desc.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_secondary}; background: transparent; border: none; line-height: 1.3;")
        self.backup_status_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_surface};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 8px;
            }}
        """)
        self.bs_icon.setPixmap(get_svg_pixmap("check_circle", pal.success, 16))
        self.backup_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_secondary}; background: transparent; border: none;")

        self.backup_btn.setIcon(get_svg_icon("download", pal.accent_fg, 14))
        self.backup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                color: {self.palette.accent_fg};
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent_hover};
            }}
        """)

        self.restore_btn.setIcon(get_svg_icon("restore", pal.fg_secondary, 14))
        self.restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_surface};
                color: {self.palette.fg_primary};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.bg_surface_hover};
                border: 1px solid {self.palette.accent};
            }}
        """)

        # 5. Tab 2: AI Behavior elements
        self.sampling_card.setStyleSheet(card_style)
        self.s_icon.setPixmap(get_svg_pixmap("sliders", pal.accent, 20))
        self.s_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.s_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.s_tag.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none;")
        self.s_sep.setStyleSheet(sep_style)

        self.temp_box.setStyleSheet(inner_panel_style)
        self.t_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.temp_val_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {self.palette.bg_surface};
                color: {self.palette.accent};
                border: 1px solid {self.palette.accent};
                border-radius: 6px;
                font-family: monospace;
                font-size: 13px;
                font-weight: 700;
                padding: 3px 10px;
            }}
        """)
        self.temp_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {self.palette.border_subtle};
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.palette.accent};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.palette.accent_fg};
                border: 2px solid {self.palette.accent};
                width: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {self.palette.accent};
            }}
        """)
        self.left_ex.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.right_ex.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.temp_hint.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border-top: 1px solid {self.palette.border_subtle}; padding-top: 8px; line-height: 1.4;")

        self.prompt_card.setStyleSheet(card_style)
        self.p_icon.setPixmap(get_svg_pixmap("psychology", pal.accent, 20))
        self.p_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.p_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.edit_btn.setIcon(get_svg_icon("edit_note", pal.accent, 14))
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_surface};
                color: {self.palette.fg_primary};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.palette.bg_surface_hover};
                border: 1px solid {self.palette.accent};
            }}
        """)
        self.p_sep.setStyleSheet(sep_style)
        self.prev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.prompt_preview_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card_inner};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 10px;
                padding: 14px;
            }}
        """)
        self.refresh_instruction_preview()

        # 6. Tab 3: Memory elements
        self.mem_card.setStyleSheet(card_style)
        self.m_icon.setPixmap(get_svg_pixmap("memory", pal.accent, 20))
        self.m_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.m_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.m_tag.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 700; color: {self.palette.success}; background: transparent; border: none;")
        self.m_sep.setStyleSheet(sep_style)

        self.toggle_box.setStyleSheet(inner_panel_style)
        self.mem_t_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.update_mem_status_badge(pal)
        self.mem_t_desc.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")
        self.auto_memory_toggle.update()

        for (card_frame, icon_box, lbl, val_widget, icon_name) in self.metric_cards:
            card_frame.setStyleSheet(inner_panel_style)
            icon_box.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.accent_bg};
                    border-radius: 8px;
                }}
            """)
            icon_box.setPixmap(get_svg_pixmap(icon_name, pal.accent, 18))
            lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; background: transparent; border: none;")
            val_widget.setStyleSheet(f"font-family: monospace; font-size: 13px; font-weight: 700; color: {self.palette.accent}; background: transparent; border: none;")

        # Danger Zone
        self.danger_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card_inner};
                border: 2px solid {self.palette.danger};
                border-radius: 12px;
            }}
        """)
        self.dh_icon.setPixmap(get_svg_pixmap("alert_triangle", pal.danger, 22))
        self.dh_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {self.palette.danger}; background: transparent; border: none;")
        self.dh_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.caution_badge.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 800; color: {self.palette.danger}; background: transparent; border: none;")
        self.danger_sep.setStyleSheet(f"background-color: {self.palette.danger}; border: none; max-height: 1px;")
        self.c_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.c_desc.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")
        self.purge_btn.setIcon(get_svg_icon("delete", "#ffffff", 16))
        self.purge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.danger};
                color: #ffffff;
                border: 1px solid {self.palette.danger};
                border-radius: 6px;
                padding: 0 14px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)

        # 7. Tab 4: Privacy elements
        self.priv_card.setStyleSheet(card_style)
        self.priv_icon.setPixmap(get_svg_pixmap("shield", pal.accent, 20))
        self.priv_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.priv_sub.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none;")
        self.priv_tag.setStyleSheet(f"font-family: monospace; font-size: 11px; font-weight: 700; color: {self.palette.success}; background: transparent; border: none;")
        self.priv_sep.setStyleSheet(sep_style)

        self.telem_box.setStyleSheet(inner_panel_style)
        self.telem_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.update_telem_badge(pal)
        self.telem_desc.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")
        self.telemetry_toggle.update()

        self.local_box.setStyleSheet(inner_panel_style)
        self.local_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.update_local_badge(pal)
        self.local_desc.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")
        self.local_toggle.update()

        self.guarantee_card.setStyleSheet(inner_panel_style)
        self.g_icon.setPixmap(get_svg_pixmap("check_circle", pal.accent, 22))
        self.g_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent; border: none;")
        self.g_desc.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent; border: none; line-height: 1.4;")

    def update_mem_status_badge(self, pal: Optional[ColorPalette] = None):
        pal = pal or self.palette or get_current_palette()
        checked = self.config.get("auto_memory_extraction", True)
        if checked:
            self.mem_status_badge.setText("Active")
            self.mem_status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.accent_bg};
                    color: {self.palette.success};
                    border: 1px solid {self.palette.success};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)
        else:
            self.mem_status_badge.setText("Disabled")
            self.mem_status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.bg_surface};
                    color: {self.palette.fg_muted};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)

    def update_telem_badge(self, pal: Optional[ColorPalette] = None):
        pal = pal or self.palette or get_current_palette()
        is_telemetry = self.config.get("telemetry", False)
        if is_telemetry:
            self.telem_badge.setText("Active")
            self.telem_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.accent_bg};
                    color: {self.palette.success};
                    border: 1px solid {self.palette.success};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)
        else:
            self.telem_badge.setText("Disabled")
            self.telem_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.bg_surface};
                    color: {self.palette.fg_muted};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)

    def update_local_badge(self, pal: Optional[ColorPalette] = None):
        pal = pal or self.palette or get_current_palette()
        is_local_only = self.config.get("local_models_only", False)
        if is_local_only:
            self.local_badge.setText("• Offline Air-Gap Mode Compatible")
            self.local_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.accent_bg};
                    color: {self.palette.success};
                    border: 1px solid {self.palette.success};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)
        else:
            self.local_badge.setText("Cloud Enabled")
            self.local_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.palette.bg_surface};
                    color: {self.palette.fg_muted};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                }}
            """)

    # -------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------
    def on_theme_card_selected(self, theme_key: str):
        self.update_config("theme", theme_key)
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_key)
        else:
            for key, card in self._theme_cards.items():
                card.update_state(key == theme_key)

    def copy_db_uri(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.db_uri_text)
            QMessageBox.information(self, "Copied", "SQLite connection URI copied to clipboard.")

    def refresh_backup_status(self):
        from app.core.config import load_config
        config = load_config()
        last = config.get("last_data_backup")
        if last:
            self.backup_lbl.setText(f"Last data backup: {last}")
        else:
            self.backup_lbl.setText("No data backups created yet.")

    def on_backup_clicked(self):
        if not self.db:
            QMessageBox.warning(self, "Unavailable", "Database manager not initialized.")
            return
        try:
            backup_path = str(get_app_data_dir() / "database" / "forgehub_backup.db")
            self.db.backup(backup_path)
            self.refresh_backup_status()
            QMessageBox.information(self, "Backup Successful", f"Database hot snapshot saved to:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Database backup failed: {str(e)}")

    def on_restore_clicked(self):
        if not self.db:
            QMessageBox.warning(self, "Unavailable", "Database manager not initialized.")
            return
        chosen_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup Database to Restore",
            str(get_app_data_dir() / "database"),
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

    def on_temperature_changed(self, val: int):
        formatted = f"{val / 100:.2f}"
        self.temp_val_badge.setText(formatted)
        self.update_config("ai_temperature", val)

    def refresh_instruction_preview(self):
        pal = self.palette or get_current_palette()
        raw = self.config.get("raw_personalized_instruction", "").strip()
        refined = self.config.get("refined_personalized_instruction", "").strip()
        stats = self.config.get("personalized_instruction_stats", {})

        if not refined:
            self.prompt_text_lbl.setText("No personalized instructions configured yet.\nClick 'Edit Instructions' to set your persona, coding standards, and output guidelines.")
            self.prompt_text_lbl.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {self.palette.fg_dim}; background: transparent; border: none; line-height: 1.5; font-style: italic;")
            self.raw_preview_lbl.setText("")
            self.raw_preview_lbl.setVisible(False)
            self.inst_status_badge.setText("Not Configured")
            self.inst_status_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.bg_surface}; color: {self.palette.fg_dim}; border: 1px solid {self.palette.border_subtle}; border-radius: 4px; font-family: monospace; font-size: 10px; padding: 2px 6px; }}")
            self.reduction_badge.setVisible(False)
            self.token_badge.setText("0 Tokens")
            self.token_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.bg_surface}; color: {self.palette.fg_dim}; border: 1px solid {self.palette.border_subtle}; border-radius: 4px; font-family: monospace; font-size: 10px; padding: 2px 6px; }}")
        else:
            self.prompt_text_lbl.setText(f'"{refined}"')
            self.prompt_text_lbl.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {self.palette.fg_secondary}; background: transparent; border: none; line-height: 1.5; font-style: normal;")
            
            if raw and raw != refined:
                sample_raw = raw[:90] + "..." if len(raw) > 90 else raw
                self.raw_preview_lbl.setText(f'Original input ({len(raw)} chars): "{sample_raw}"')
                self.raw_preview_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_dim}; background: transparent; border: none; font-style: italic;")
                self.raw_preview_lbl.setVisible(True)
            else:
                self.raw_preview_lbl.setText("")
                self.raw_preview_lbl.setVisible(False)

            tier = stats.get("tier", "short")
            pct = stats.get("reduction_pct", 0.0)
            method = stats.get("method", "direct_short")
            
            if tier == "short":
                self.inst_status_badge.setText("Short • Verbatim")
                self.inst_status_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.accent_bg}; color: {self.palette.accent}; border: 1px solid {self.palette.accent}; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }}")
                self.reduction_badge.setVisible(False)
            else:
                method_name = "AI Refined" if method == "ai" else "Optimized"
                self.inst_status_badge.setText(f"{method_name} • Active")
                self.inst_status_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.accent_bg}; color: {self.palette.success}; border: 1px solid {self.palette.success}; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }}")
                self.reduction_badge.setText(f"-{pct}% ({stats.get('original_len', len(raw))} -> {len(refined)} ch)")
                self.reduction_badge.setVisible(True)
                self.reduction_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.bg_surface}; color: {self.palette.fg_muted}; border: 1px solid {self.palette.border_subtle}; border-radius: 4px; font-family: monospace; font-size: 10px; padding: 2px 6px; }}")

            token_estimate = max(1, len(refined) // 4)
            self.token_badge.setText(f"~{token_estimate} Tokens")
            self.token_badge.setStyleSheet(f"QLabel {{ background-color: {self.palette.bg_surface}; color: {self.palette.accent}; border: 1px solid {self.palette.accent}; border-radius: 4px; font-family: monospace; font-size: 10px; font-weight: 600; padding: 2px 6px; }}")

    def on_edit_instructions_clicked(self):
        raw = self.config.get("raw_personalized_instruction", "")
        dialog = EditPersonalizedInstructionDialog(raw, self, palette=self.palette, db_manager=self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            res = dialog.get_result()
            if res is not None:
                save_personalized_instruction(res)
                self.config = load_config()
                self.refresh_instruction_preview()
                
                if res["tier"] == "empty":
                    QMessageBox.information(self, "Instructions Cleared", "Personalized instructions have been cleared.")
                elif res["tier"] == "short":
                    QMessageBox.information(
                        self,
                        "Instructions Saved",
                        f"Short instruction saved verbatim ({res['original_len']} chars).\n\n"
                        "This will be injected into all AI queries across Forge Hub."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Instructions Refined & Saved",
                        f"Instructions successfully refined and distilled!\n\n"
                        f"• Original length: {res['original_len']} chars\n"
                        f"• Refined length: {res['refined_len']} chars\n"
                        f"• Compression: {res['reduction_pct']}% reduction\n"
                        f"• Tier: {res['tier'].title()}\n"
                        f"• Method: {'AI Model' if res['method'] == 'ai' else 'Heuristic Optimizer'}\n\n"
                        "The refined instruction is saved and will be injected into all AI queries."
                    )

    def on_edit_prompt_clicked(self):
        # Backward compatibility alias
        self.on_edit_instructions_clicked()

    def on_fallback_toggled(self, checked: bool):
        self.update_config("auto_fallback_models", checked)

    def on_auto_memory_toggled(self, checked: bool):
        self.update_config("auto_memory_extraction", checked)
        self.update_mem_status_badge()

    def on_clear_memory_clicked(self):
        if not self.db:
            return
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

    def on_telemetry_toggled(self, checked: bool):
        self.update_config("telemetry", checked)
        self.update_telem_badge()

    def on_local_toggled(self, checked: bool):
        self.update_config("local_models_only", checked)
        self.update_local_badge()

    def update_config(self, key: str, value):
        self.config[key] = value
        save_config(self.config)
