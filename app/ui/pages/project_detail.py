from PySide6.QtWidgets import ( QDialog, QScrollArea, QLineEdit,  QComboBox,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QLineEdit, QTextEdit, QTextBrowser,
    QMessageBox, QFrame, QScrollArea, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThreadPool, QRunnable, QObject
from PySide6.QtGui import QCursor, QFont

from database.repository import ProjectRepository, ProviderRepository
from app.ui.components.media_widget import MediaUploadWidget
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.core.palette import ColorPalette
from app.core.theme import get_current_palette, theme_manager



class UpdateCardWidget(QFrame):
    def __init__(self, title, description, palette):
        super().__init__()
        self.palette = palette
        self.setObjectName("updateCard")
        self.setStyleSheet(f"""
            #updateCard {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 8px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header button
        self.header_btn = QPushButton(title)
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {self.palette.fg_primary};
                font-weight: 600;
                font-size: 14px;
                text-align: left;
                padding: 12px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.03);
            }}
        """)
        self.header_btn.clicked.connect(self.toggle_body)
        main_layout.addWidget(self.header_btn)
        
        # Body frame
        self.body_frame = QFrame()
        self.body_frame.setStyleSheet("border-top: 1px solid rgba(255, 255, 255, 0.05); background-color: transparent;")
        body_layout = QVBoxLayout(self.body_frame)
        body_layout.setContentsMargins(16, 12, 16, 16)
        
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"""
            color: {self.palette.fg_muted};
            font-size: 13px;
            line-height: 1.5;
            border: none;
        """)
        body_layout.addWidget(desc_lbl)
        
        self.body_frame.setVisible(False)
        main_layout.addWidget(self.body_frame)
        
    def toggle_body(self):
        self.body_frame.setVisible(not self.body_frame.isVisible())

class AIWorkerSignals(QObject):
    finished = Signal(str, str)  # action_type, result_text
    error = Signal(str)


class AIActionWorker(QRunnable):
    def __init__(self, db_manager, action_type, prompt, context):
        super().__init__()
        self.db = db_manager
        self.action_type = action_type
        self.prompt = prompt
        self.context = context
        self.signals = AIWorkerSignals()

    def run(self):
        try:
            from app.ai.router import ModelRouter
            router = ModelRouter(self.db)
            result = router.route_request(
                prompt=self.prompt,
                category="General",
                context=self.context,
                max_tokens=2048
            )
            self.signals.finished.emit(self.action_type, result)
        except Exception as e:
            self.signals.error.emit(str(e))


class TaskItemWidget(QFrame):
    """Custom widget for a single task with status toggle, strikethrough, and delete button."""
    status_changed = Signal(int, str)
    delete_requested = Signal(int)

    def __init__(self, task_data):
        super().__init__()
        self.palette = get_current_palette()
        self.task_id = task_data["id"]
        self.status = task_data.get("status", "Pending")
        self.title = task_data.get("title", "")

        self.setObjectName("taskItem")
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            #taskItem {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
            }}
            #taskItem:hover {{
                border: 1px solid {self.palette.border_subtle};
                background-color: #1c202a;
            }}
            #taskItem QLabel {{
                background: transparent;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(10)

        # Checkbox
        self.cb = QCheckBox()
        self.cb.setChecked(self.status == "Completed")
        self.cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #1B5C54;
                background-color: {self.palette.bg_card};
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.palette.accent};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.palette.accent};
                border-color: {self.palette.accent};
            }}
        """)
        self.cb.toggled.connect(self._on_toggled)
        layout.addWidget(self.cb)

        # Title Label
        self.title_lbl = QLabel(self.title)
        self._update_text_style()
        layout.addWidget(self.title_lbl, 1)

        # Status badge
        self.badge_lbl = QLabel(self.status)
        self._update_badge_style()
        layout.addWidget(self.badge_lbl)

        # Delete button
        del_btn = QPushButton()
        del_btn.setIcon(get_svg_icon("delete", f"{self.palette.fg_muted}", 14))
        del_btn.setFixedSize(26, 26)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))
        layout.addWidget(del_btn)

    def _on_toggled(self, checked):
        new_status = "Completed" if checked else "Pending"
        self.status = new_status
        self._update_text_style()
        self._update_badge_style()
        self.status_changed.emit(self.task_id, new_status)

    def _update_text_style(self):
        if self.status == "Completed":
            self.title_lbl.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_muted}; text-decoration: line-through;")
        else:
            self.title_lbl.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_primary};")

    def _update_badge_style(self):
        self.badge_lbl.setText(self.status)
        if self.status == "Completed":
            self.badge_lbl.setStyleSheet(f"""
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(71, 85, 105, 0.4);
                color: {self.palette.fg_muted};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            """)
        else:
            self.badge_lbl.setStyleSheet("""
                background-color: rgba(30, 58, 138, 0.35);
                border: 1px solid rgba(59, 130, 246, 0.4);
                color: #93c5fd;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            """)


class ProjectDetailWidget(QWidget):
    back_requested = Signal()

    def __init__(self, db_manager):
        super().__init__()
        self.palette = get_current_palette()
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.project_id = None
        self.project_data = None
        self.thread_pool = QThreadPool.globalInstance()
        self.active_ai_actions = [
            {"id": "readme", "label": "Improve README with AI", "prompt": None},
            {"id": "arch", "label": "Analyze Architecture", "prompt": None},
            {"id": "linkedin", "label": "Draft LinkedIn Post", "prompt": None}
        ]


        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.palette.bg_app};
            }}
            QLabel {{
                background: transparent;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 24)
        main_layout.setSpacing(16)

        # 1. Top Header Bar
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        self.header_frame.setStyleSheet(f"""
            #headerFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
                padding: 12px 16px;
            }}
            #headerFrame QLabel {{
                background: transparent;
            }}
        """)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        # Back button
        self.back_btn = QPushButton()
        self.back_btn.setIcon(get_svg_icon("arrow_back", f"{self.palette.fg_muted}", 16))
        self.back_btn.setText(" Back")
        self.back_btn.setFixedHeight(32)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.border_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_muted};
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #283548;
                border-color: {self.palette.accent};
                color: {self.palette.fg_primary};
            }}
        """)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(self.back_btn)

        # Vertical separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"background-color: {self.palette.border_card};")
        header_layout.addWidget(sep)

        # Title + Status + Path column
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        title_badge_row = QHBoxLayout()
        title_badge_row.setSpacing(10)

        self.title_label = QLabel("Project Details")
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: -0.3px;")
        title_badge_row.addWidget(self.title_label)

        self.status_badge = QLabel("Planning")
        self.status_badge.setStyleSheet("""
            background-color: rgba(30, 58, 138, 0.4);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #93c5fd;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        title_badge_row.addWidget(self.status_badge)
        title_badge_row.addStretch()
        title_col.addLayout(title_badge_row)

        self.sub_path_label = QLabel("/workspace/projects")
        self.sub_path_label.setStyleSheet(f"font-size: 11px; font-family: monospace; color: {self.palette.fg_muted};")
        title_col.addWidget(self.sub_path_label)

        header_layout.addLayout(title_col, 1)

        # Edit and Delete buttons
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(get_svg_icon("edit", f"{self.palette.fg_muted}", 14))
        self.edit_btn.setText(" Edit Project")
        self.edit_btn.setFixedHeight(32)
        self.edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.border_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_muted};
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: #283548;
                border-color: {self.palette.accent};
                color: {self.palette.fg_primary};
            }}
        """)
        self.edit_btn.clicked.connect(self.edit_project)
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(get_svg_icon("delete", f"{self.palette.danger}", 14))
        self.delete_btn.setText(" Delete")
        self.delete_btn.setFixedHeight(32)
        self.delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(147, 0, 10, 0.2);
                border: 1px solid rgba(255, 180, 171, 0.3);
                border-radius: 6px;
                color: #ffb4ab;
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(147, 0, 10, 0.35);
                border-color: #ffb4ab;
                color: {self.palette.fg_primary};
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_project)
        header_layout.addWidget(self.delete_btn)

        main_layout.addWidget(self.header_frame)

        # 2. Modern Tab Navigation
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: {self.palette.fg_muted};
                font-size: 13px;
                font-weight: 500;
                padding: 10px 18px;
                margin-right: 6px;
            }}
            QTabBar::tab:hover {{
                color: {self.palette.fg_primary};
            }}
            QTabBar::tab:selected {{
                color: {self.palette.accent};
                border-bottom: 2px solid {self.palette.accent};
                font-weight: 600;
            }}
        """)
        main_layout.addWidget(self.tabs)

        # Setup Tab Pages
        self._setup_overview_tab()
        self._setup_docs_tab()
        self._setup_tasks_tab()
        self._setup_chat_tab()
        self._setup_activity_tab()
        self._setup_media_tab()
        self._setup_research_tab()
        self._setup_updations_tab()

    # --- TAB 1: OVERVIEW ---
    def _setup_overview_tab(self):
        self.overview_tab = QWidget()
        self.overview_tab.setStyleSheet("background: transparent;")
        tab_layout = QHBoxLayout(self.overview_tab)
        tab_layout.setContentsMargins(0, 12, 0, 0)
        tab_layout.setSpacing(16)

        # Left Column: Project Overview Card
        overview_card = QFrame()
        overview_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        oc_layout_main = QVBoxLayout(overview_card)
        oc_layout_main.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        inner_widget = QWidget()
        inner_widget.setStyleSheet("background: transparent;")
        oc_layout = QVBoxLayout(inner_widget)
        oc_layout.setContentsMargins(20, 20, 20, 20)
        oc_layout.setSpacing(14)
        
        scroll.setWidget(inner_widget)
        oc_layout_main.addWidget(scroll)

        # Header of Overview Card
        card_header = QHBoxLayout()
        card_header.setContentsMargins(0, 0, 0, 0)

        info_icon = QLabel()
        info_icon.setPixmap(get_svg_pixmap("info", f"{self.palette.accent}", 18))
        card_header.addWidget(info_icon)

        ch_title = QLabel("Project Overview")
        ch_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {self.palette.fg_primary};")
        card_header.addWidget(ch_title)
        card_header.addStretch()

        self.project_id_lbl = QLabel("ID: PRJ-0000")
        self.project_id_lbl.setStyleSheet(f"font-size: 11px; font-family: monospace; color: {self.palette.fg_muted};")
        card_header.addWidget(self.project_id_lbl)
        oc_layout.addLayout(card_header)

        # Divider
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet(f"background-color: {self.palette.border_card}; border: none;")
        oc_layout.addWidget(div1)

        # Description Section
        desc_title = QLabel("DESCRIPTION")
        desc_title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; letter-spacing: 0.5px;")
        oc_layout.addWidget(desc_title)

        self.desc_label = QLabel("No description provided.")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumWidth(1)
        self.desc_label.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_muted}; line-height: 1.5;")
        oc_layout.addWidget(self.desc_label)

        # Tech Stack Section
        stack_title = QLabel("TECHNOLOGY STACK")
        stack_title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; letter-spacing: 0.5px; margin-top: 8px;")
        oc_layout.addWidget(stack_title)

        self.stack_container = QWidget()
        self.stack_container.setStyleSheet("background: transparent;")
        self.stack_layout = QHBoxLayout(self.stack_container)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(8)
        self.stack_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        oc_layout.addWidget(self.stack_container)

        # Features Section
        self.features_title = QLabel("KEY FEATURES")
        self.features_title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; letter-spacing: 0.5px; margin-top: 8px;")
        oc_layout.addWidget(self.features_title)

        self.features_label = QLabel("No features specified.")
        self.features_label.setWordWrap(True)
        self.features_label.setMinimumWidth(1)
        self.features_label.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_muted}; line-height: 1.4;")
        oc_layout.addWidget(self.features_label)

        oc_layout.addStretch()
        tab_layout.addWidget(overview_card, 2)

        # Right Column: Metrics & Quick Actions
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(16)

        # Metrics Card
        metrics_card = QFrame()
        metrics_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        mc_layout = QVBoxLayout(metrics_card)
        mc_layout.setContentsMargins(18, 18, 18, 18)
        mc_layout.setSpacing(12)

        mc_header = QHBoxLayout()
        m_icon = QLabel()
        m_icon.setPixmap(get_svg_pixmap("analytics", f"{self.palette.success}", 16))
        mc_header.addWidget(m_icon)

        mc_title = QLabel("Workspace Metrics")
        mc_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary};")
        mc_header.addWidget(mc_title)
        mc_header.addStretch()
        mc_layout.addLayout(mc_header)

        # Metric row helper
        def make_metric_row(label, val_widget):
            row = QFrame()
            row.setStyleSheet(f"background-color: {self.palette.bg_card}; border-radius: 6px; border: 1px solid {self.palette.border_card};")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(val_widget)
            return row

        self.metric_tasks = QLabel("0 / 0")
        self.metric_tasks.setStyleSheet(f"font-size: 12px; font-weight: 600; font-family: monospace; color: {self.palette.fg_primary}; background: transparent;")
        mc_layout.addWidget(make_metric_row("Active Tasks", self.metric_tasks))

        self.metric_docs = QLabel("README.md")
        self.metric_docs.setStyleSheet(f"font-size: 12px; font-family: monospace; color: {self.palette.success}; background: transparent;")
        mc_layout.addWidget(make_metric_row("Documentation", self.metric_docs))

        self.metric_status = QLabel("Planning")
        self.metric_status.setStyleSheet("font-size: 12px; font-weight: 600; color: #93c5fd; background: transparent;")
        mc_layout.addWidget(make_metric_row("Project Status", self.metric_status))

        right_col.addWidget(metrics_card)

        # Quick AI Actions Card
        ai_card = QFrame()
        ai_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        ac_layout = QVBoxLayout(ai_card)
        ac_layout.setContentsMargins(18, 18, 18, 18)
        ac_layout.setSpacing(10)

        ac_header = QHBoxLayout()
        ac_icon = QLabel()
        ac_icon.setPixmap(get_svg_pixmap("sparkles", "#9ecaff", 16))
        ac_header.addWidget(ac_icon)
        ac_title = QLabel("Quick AI Actions")
        ac_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary};")
        ac_header.addWidget(ac_title)
        ac_header.addStretch()
        ac_layout.addLayout(ac_header)

        ac_sub = QLabel("Accelerate project tasks using configured AI models.")
        ac_sub.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted};")
        ac_layout.addWidget(ac_sub)

        # Dynamic AI Action Buttons
        self.ai_actions_layout = QVBoxLayout()
        self.ai_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.ai_actions_layout.setSpacing(10)
        ac_layout.addLayout(self.ai_actions_layout)
        self._render_ai_actions()

        right_col.addWidget(ai_card)
        
        # Publishing Advisor Card
        self.pub_card = QFrame()
        self.pub_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{ background: transparent; }}
        """)
        pub_layout = QVBoxLayout(self.pub_card)
        pub_layout.setContentsMargins(18, 16, 18, 18)
        pub_layout.setSpacing(12)

        p_header = QHBoxLayout()
        p_icon = QLabel()
        p_icon.setPixmap(get_svg_pixmap("globe", f"{self.palette.accent}", 16))
        p_header.addWidget(p_icon)
        p_title = QLabel("Publishing Advisor")
        p_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.palette.fg_primary};")
        p_header.addWidget(p_title)
        p_header.addStretch()
        pub_layout.addLayout(p_header)
        
        p_sub = QLabel("AI suggestions for sharing this project.")
        p_sub.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted};")
        pub_layout.addWidget(p_sub)
        
        self.pub_gh_lbl = QLabel("GitHub: Unknown")
        self.pub_li_lbl = QLabel("LinkedIn: Unknown")
        self.pub_reason_lbl = QLabel("Run Research to generate a publishing strategy.")
        
        self.pub_gh_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {self.palette.fg_primary};")
        self.pub_li_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {self.palette.fg_primary};")
        self.pub_reason_lbl.setStyleSheet(f"font-size: 11px; color: {self.palette.fg_muted}; font-style: italic;")
        self.pub_reason_lbl.setWordWrap(True)
        
        pub_layout.addWidget(self.pub_gh_lbl)
        pub_layout.addWidget(self.pub_li_lbl)
        pub_layout.addWidget(self.pub_reason_lbl)
        
        right_col.addWidget(self.pub_card)
        right_col.addStretch()

        tab_layout.addLayout(right_col, 1)
        self.tabs.addTab(self.overview_tab, get_svg_icon("dashboard", f"{self.palette.fg_muted}", 16), "Overview")

    def _render_ai_actions(self):
        # Clear existing
        while self.ai_actions_layout.count():
            item = self.ai_actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for action in self.active_ai_actions:
            btn = QPushButton(f"  {action['label']}")
            btn.setIcon(get_svg_icon("sparkles", "#9ecaff", 14))
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_muted};
                    font-size: 12px;
                    font-weight: 500;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    background-color: #243248;
                    border-color: {self.palette.accent};
                    color: {self.palette.fg_primary};
                }}
            """)
            # Connect using default argument to capture current id
            btn.clicked.connect(lambda _, a_id=action["id"]: self.trigger_ai_action(a_id))
            self.ai_actions_layout.addWidget(btn)

    # --- TAB 2: DOCUMENTATION ---
    def _setup_docs_tab(self):
        self.docs_tab = QWidget()
        self.docs_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.docs_tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        docs_card = QFrame()
        docs_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        dc_layout = QVBoxLayout(docs_card)
        dc_layout.setContentsMargins(18, 16, 18, 18)
        dc_layout.setSpacing(12)

        # Header
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        doc_icon = QLabel()
        doc_icon.setPixmap(get_svg_pixmap("description", f"{self.palette.accent}", 18))
        top_bar.addWidget(doc_icon)

        self.doc_selector = QComboBox()
        self.doc_selector.addItems(["README.md", "PRD"])
        self.doc_selector.setStyleSheet(f"background-color: {self.palette.bg_input}; color: {self.palette.fg_primary}; border: 1px solid {self.palette.border_card}; padding: 4px; border-radius: 4px;")
        self.doc_selector.currentTextChanged.connect(self._on_doc_type_changed)
        top_bar.addWidget(self.doc_selector)
        
        doc_title = QLabel("— Markdown Editor & Live Preview")
        doc_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary};")
        top_bar.addWidget(doc_title)
        top_bar.addStretch()

        # Improve with AI button
        self.doc_ai_btn = QPushButton()
        self.doc_ai_btn.setIcon(get_svg_icon("sparkles", "#9ecaff", 14))
        self.doc_ai_btn.setText(" Improve with AI")
        self.doc_ai_btn.setFixedHeight(32)
        self.doc_ai_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.doc_ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.border_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: #9ecaff;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #26354f;
                border-color: {self.palette.accent};
                color: {self.palette.fg_primary};
            }}
        """)
        self.doc_ai_btn.clicked.connect(lambda: self.trigger_ai_action("readme"))
        top_bar.addWidget(self.doc_ai_btn)

        # Save Documentation button
        self.docs_save_btn = QPushButton()
        self.docs_save_btn.setIcon(get_svg_icon("save", f"{self.palette.fg_primary}", 14))
        self.docs_save_btn.setText(" Save Documentation")
        self.docs_save_btn.setFixedHeight(32)
        self.docs_save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.docs_save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
            QPushButton:pressed {{
                background-color: #1565c0;
            }}
        """)
        self.docs_save_btn.clicked.connect(self.save_docs)
        top_bar.addWidget(self.docs_save_btn)

        dc_layout.addLayout(top_bar)
        
        self.blank_doc_widget = QWidget()
        blank_layout = QVBoxLayout(self.blank_doc_widget)
        blank_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blank_icon = QLabel()
        blank_icon.setPixmap(get_svg_pixmap("description", f"{self.palette.fg_muted}", 48))
        blank_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blank_layout.addWidget(blank_icon)
        blank_lbl = QLabel("No documentation exists yet.")
        blank_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 14px;")
        blank_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blank_layout.addWidget(blank_lbl)
        self.blank_gen_btn = QPushButton(" Generate README")
        self.blank_gen_btn.setIcon(get_svg_icon("sparkles", "#ffffff", 14))
        self.blank_gen_btn.setFixedSize(180, 40)
        self.blank_gen_btn.setStyleSheet(f"background-color: {self.palette.accent}; color: #fff; border-radius: 6px; font-weight: 600;")
        self.blank_gen_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.blank_gen_btn.clicked.connect(self._handle_gen_btn_clicked)
        blank_layout.addWidget(self.blank_gen_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dc_layout.addWidget(self.blank_doc_widget, 1)

        # Splitter: Source on Left, Preview on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {self.palette.border_card};
                width: 2px;
            }}
        """)

        # Source Editor Pane
        source_container = QWidget()
        source_container.setStyleSheet("background: transparent;")
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(0, 0, 8, 0)
        source_layout.setSpacing(6)

        source_lbl = QLabel("SOURCE (MARKDOWN)")
        source_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; letter-spacing: 0.5px;")
        source_layout.addWidget(source_lbl)

        self.docs_editor = QTextEdit()
        self.docs_editor.setFont(QFont("monospace", 10))
        self.docs_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 10px;
            }}
            QTextEdit:focus {{
                border: 1px solid {self.palette.accent};
            }}
        """)
        self.docs_editor.textChanged.connect(self._update_docs_preview)
        source_layout.addWidget(self.docs_editor)
        splitter.addWidget(source_container)

        # Live Preview Pane
        preview_container = QWidget()
        preview_container.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(8, 0, 0, 0)
        preview_layout.setSpacing(6)

        preview_lbl = QLabel("RENDERED PREVIEW")
        preview_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; letter-spacing: 0.5px;")
        preview_layout.addWidget(preview_lbl)

        self.docs_preview = QTextBrowser()
        self.docs_preview.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #0f141f;
                border: 1px solid {self.palette.border_card};
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 13px;
                padding: 14px;
            }}
        """)
        self.docs_preview.setOpenExternalLinks(True)
        preview_layout.addWidget(self.docs_preview)
        splitter.addWidget(preview_container)

        splitter.setSizes([500, 500])
        dc_layout.addWidget(splitter, 1)

        layout.addWidget(docs_card)
        self.tabs.addTab(self.docs_tab, get_svg_icon("description", f"{self.palette.fg_muted}", 16), "Documentation")

    def _on_doc_type_changed(self, doc_title):
        self.current_doc_title = doc_title
        self.load_docs()

    def _update_docs_preview(self):
        text = self.docs_editor.toPlainText()
        self.docs_preview.setMarkdown(text)

    # --- TAB 3: TASKS ---
    def _setup_tasks_tab(self):
        self.tasks_tab = QWidget()
        self.tasks_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.tasks_tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        tasks_card = QFrame()
        tasks_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        tc_layout = QVBoxLayout(tasks_card)
        tc_layout.setContentsMargins(20, 20, 20, 20)
        tc_layout.setSpacing(14)

        # Header
        th_layout = QHBoxLayout()
        t_icon = QLabel()
        t_icon.setPixmap(get_svg_pixmap("checklist", f"{self.palette.accent}", 18))
        th_layout.addWidget(t_icon)

        th_title = QLabel("Project Tasks")
        th_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {self.palette.fg_primary};")
        th_layout.addWidget(th_title)

        self.tasks_count_badge = QLabel("0")
        self.tasks_count_badge.setStyleSheet(f"""
            background-color: {self.palette.border_card};
            border: 1px solid {self.palette.border_subtle};
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            color: {self.palette.fg_muted};
        """)
        th_layout.addWidget(self.tasks_count_badge)
        th_layout.addStretch()

        self.tasks_summary_lbl = QLabel("0 pending, 0 completed")
        self.tasks_summary_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted};")
        th_layout.addWidget(self.tasks_summary_lbl)
        tc_layout.addLayout(th_layout)

        # Add Task Bar
        add_bar = QHBoxLayout()
        add_bar.setContentsMargins(0, 0, 0, 0)
        add_bar.setSpacing(10)

        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Add a new task (e.g. Implement SQLite WAL mode)...")
        self.new_task_input.setFixedHeight(36)
        self.new_task_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 13px;
                padding-left: 12px;
                padding-right: 12px;
            }}
            QLineEdit:focus {{
                border-color: {self.palette.accent};
            }}
            QLineEdit::placeholder {{
                color: {self.palette.fg_muted};
            }}
        """)
        self.new_task_input.returnPressed.connect(self.add_task)
        add_bar.addWidget(self.new_task_input, 1)

        add_task_btn = QPushButton("+ Add Task")
        add_task_btn.setFixedHeight(36)
        add_task_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_task_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 12px;
                font-weight: 500;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
            QPushButton:pressed {{
                background-color: #1565c0;
            }}
        """)
        add_task_btn.clicked.connect(self.add_task)
        add_bar.addWidget(add_task_btn)
        tc_layout.addLayout(add_bar)

        # Scroll Area for Task Items
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.palette.bg_app};
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.palette.border_card};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.palette.border_subtle};
            }}
        """)
        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.tasks_list_layout = QVBoxLayout(self.tasks_container)
        self.tasks_list_layout.setContentsMargins(0, 4, 0, 4)
        self.tasks_list_layout.setSpacing(8)
        self.tasks_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tasks_scroll.setWidget(self.tasks_container)
        tc_layout.addWidget(self.tasks_scroll, 1)

        layout.addWidget(tasks_card)
        self.tabs.addTab(self.tasks_tab, get_svg_icon("checklist", f"{self.palette.fg_muted}", 16), "Tasks")

    # --- TAB 4: AI CHAT ---
    def _setup_chat_tab(self):
        from app.ui.pages.chat import AIChatPage
        self.chat_page = AIChatPage(self.db)
        self.tabs.addTab(self.chat_page, get_svg_icon("chat", f"{self.palette.fg_muted}", 16), "AI Chat")

    # --- TAB 5: ACTIVITY ---
    def _setup_activity_tab(self):
        self.activity_tab = QWidget()
        self.activity_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.activity_tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        activity_card = QFrame()
        activity_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        ac_layout = QVBoxLayout(activity_card)
        ac_layout.setContentsMargins(20, 20, 20, 20)
        ac_layout.setSpacing(14)

        # Header
        ah_layout = QHBoxLayout()
        a_icon = QLabel()
        a_icon.setPixmap(get_svg_pixmap("history", f"{self.palette.accent}", 18))
        ah_layout.addWidget(a_icon)

        ah_title = QLabel("Project Activity Timeline")
        ah_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {self.palette.fg_primary};")
        ah_layout.addWidget(ah_title)
        ah_layout.addStretch()
        ac_layout.addLayout(ah_layout)

        # Activity List Scroll Area
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.palette.bg_app};
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.palette.border_card};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.palette.border_subtle};
            }}
        """)

        self.activity_container = QWidget()
        self.activity_container.setStyleSheet("background: transparent;")
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 4, 0, 4)
        self.activity_layout.setSpacing(8)
        self.activity_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.activity_scroll.setWidget(self.activity_container)
        ac_layout.addWidget(self.activity_scroll, 1)

        layout.addWidget(activity_card)
        self.tabs.addTab(self.activity_tab, get_svg_icon("history", f"{self.palette.fg_muted}", 16), "Activity")

    # --- TAB 6: MEDIA ---
    def _setup_media_tab(self):
        self.media_tab = QWidget()
        layout = QVBoxLayout(self.media_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        
        media_card = QFrame()
        media_card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
        """)
        mc_layout = QVBoxLayout(media_card)
        mc_layout.setContentsMargins(20, 20, 20, 20)
        
        self.media_widget = MediaUploadWidget(self.db)
        mc_layout.addWidget(self.media_widget)
        
        layout.addWidget(media_card)
        self.tabs.addTab(self.media_tab, get_svg_icon("folder", f"{self.palette.fg_muted}", 16), "Media")

    # --- TAB 7: RESEARCH ---
    def _setup_research_tab(self):
        self.research_tab = QWidget()
        layout = QVBoxLayout(self.research_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        
        top = QHBoxLayout()
        title = QLabel("Deep Web Market Research (RAG)")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.palette.fg_primary};")
        top.addWidget(title)
        top.addStretch()
        
        self.btn_refresh_research = QPushButton(" Generate Actionable Research")
        self.btn_refresh_research.setIcon(get_svg_icon("analytics", self.palette.accent, 14))
        self.btn_refresh_research.setFixedWidth(250)
        self.btn_refresh_research.clicked.connect(lambda: self.trigger_ai_research_update("all"))
        top.addWidget(self.btn_refresh_research)
        
        c_layout.addLayout(top)
        
        self.research_progress = QLabel("")
        self.research_progress.setStyleSheet(f"color: {self.palette.accent}; font-weight: bold; margin-bottom: 10px;")
        self.research_progress.hide()
        c_layout.addWidget(self.research_progress)
        
        self.research_browser = QTextBrowser()
        self.research_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                color: {self.palette.fg_primary};
                font-size: 13px;
                line-height: 1.5;
            }}
        """)
        c_layout.addWidget(self.research_browser)
        layout.addWidget(card)
        self.tabs.addTab(self.research_tab, get_svg_icon("analytics", f"{self.palette.fg_muted}", 16), "Actionable Research")

    # --- TAB 8: UPDATIONS ---
    def _setup_updations_tab(self):
        self.updations_tab = QWidget()
        layout = QVBoxLayout(self.updations_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        
        lbl = QLabel("Suggested Updates & Unique Opportunities")
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.palette.fg_primary}; margin-bottom: 8px;")
        layout.addWidget(lbl)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self.updations_layout = QVBoxLayout(inner)
        self.updations_layout.setContentsMargins(0, 0, 0, 0)
        self.updations_layout.setSpacing(10)
        self.updations_layout.addStretch()
        
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        
        self.tabs.addTab(self.updations_tab, get_svg_icon("sparkles", f"{self.palette.fg_muted}", 16), "Updations")
        
    def _render_updations(self, updations_raw):
        # Clear existing
        while self.updations_layout.count() > 1: # keep stretch at end
            item = self.updations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        import json
        if not updations_raw:
            lbl = QLabel("No updations found. Regenerate research to populate.")
            lbl.setStyleSheet(f"color: {self.palette.fg_muted};")
            self.updations_layout.insertWidget(0, lbl)
            return
            
        try:
            updates = json.loads(updations_raw)
            if not isinstance(updates, list):
                raise ValueError("Expected JSON array")
                
            for i, up in enumerate(updates):
                title = up.get("title", f"Update {i+1}")
                desc = up.get("description", "")
                card = UpdateCardWidget(title, desc, self.palette)
                self.updations_layout.insertWidget(self.updations_layout.count() - 1, card)
                
        except Exception as e:
            # Fallback if it's still markdown or malformed
            card = UpdateCardWidget("Raw Output", str(updations_raw), self.palette)
            self.updations_layout.insertWidget(0, card)

    def _update_publishing_advisor(self):
        if not hasattr(self, 'pub_card'): return
        
        if not self.current_research_data or "publishing_strategy" not in self.current_research_data:
            self.pub_gh_lbl.setText("GitHub: ⚪ Unknown")
            self.pub_li_lbl.setText("LinkedIn: ⚪ Unknown")
            self.pub_reason_lbl.setText("Run Research to generate a publishing strategy.")
            return
            
        import json
        raw = self.current_research_data.get("publishing_strategy", "{}")
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            gh = data.get("github_suitability", "Unknown")
            li = data.get("linkedin_suitability", "Unknown")
            reason = data.get("reasoning", "No reasoning provided.")
            
            gh_icon = "🟢" if "Public" in gh else ("🟡" if "Private" in gh else "🔴")
            li_icon = "🟢" if "Recommended" in li and "Not" not in li else ("🔴" if "Not" in li else "🟡")
            
            self.pub_gh_lbl.setText(f"GitHub: {gh_icon} {gh}")
            self.pub_li_lbl.setText(f"LinkedIn: {li_icon} {li}")
            self.pub_reason_lbl.setText(reason)
        except Exception as e:
            self.pub_gh_lbl.setText("GitHub: ⚪ Error parsing")
            self.pub_li_lbl.setText("LinkedIn: ⚪ Error parsing")
            self.pub_reason_lbl.setText("Research data was malformed.")
            
    def _on_research_type_changed(self, idx=0):
        if not hasattr(self, 'current_research_data') or not self.current_research_data:
            self.research_browser.setPlainText("No research data found. Click 'Generate Actionable Research'.")
            return
            
        self.research_browser.setMarkdown(self.current_research_data.get("actionable_research", "Data not available."))

    def trigger_ai_research_update(self, mode="all"):
        from app.ai.research_worker import ResearchWorker
        
        self.btn_refresh_research.setEnabled(False)
        self.research_progress.show()
        self.research_progress.setText("Initializing RAG pipeline...")
        
        self.research_browser.setHtml(f"""
            <div style='text-align: center; margin-top: 50px; color: {self.palette.fg_muted};'>
                <h2>⚙️ Autonomous RAG Agent Running...</h2>
                <p>Generating queries, scraping the web, and synthesizing an actionable report.<br>This usually takes 30-60 seconds.</p>
                <p><i>You can safely browse other tabs while waiting.</i></p>
            </div>
        """)
        
        worker = ResearchWorker(self.db, self.project_id, self.project_data, "all")
        worker.signals.finished.connect(self._on_research_finished)
        worker.signals.error.connect(self._on_research_error)
        worker.signals.needs_decision.connect(self._on_research_needs_decision)
        worker.signals.progress.connect(self.research_progress.setText)
        self.thread_pool.start(worker)
        
    def _on_research_error(self, e):
        self.btn_refresh_research.setEnabled(True)
        
        self.research_browser.setHtml(f"<h3 style='color: #ef4444;'>Research Failed</h3><p>{str(e)}</p>")
        QMessageBox.warning(self, "Error", str(e))

    def _on_research_needs_decision(self, worker):
        reply = QMessageBox.question(
            self,
            "Rate Limit Reached",
            "Rate limit reached for your top 3 good models.\n\nDo you want to use other (low-level) available models to finish the research now, or stop and wait to try again later?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        # Change button text
        # To do this safely with standard buttons: Yes = use other, No = wait
        # Let's use custom buttons instead.
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Rate Limit Reached")
        msg_box.setText("Rate limit reached for your top 3 selected good models.")
        msg_box.setInformativeText("Do you want to use other (low-level) available models to finish the job now, or stop and wait to try again later?")
        
        btn_other = msg_box.addButton("Use Other Models", QMessageBox.ButtonRole.AcceptRole)
        btn_wait = msg_box.addButton("Wait (Stop)", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_other:
            worker.set_decision("fallback")
            # Update user preference globally so it automatically falls back next time
            from app.core.config import load_config, save_config
            cfg = load_config()
            cfg["auto_fallback_models"] = True
            save_config(cfg)
        else:
            worker.set_decision("wait")
            # Restore UI since it stopped
            self.btn_refresh_research.setEnabled(True)
            
            self._on_research_type_changed()

    def _on_research_finished(self, pid, results_dict):
        if pid == self.project_id:
            self.btn_refresh_research.setEnabled(True)
            
            self.current_research_data = results_dict
            
            # Sync in-memory project data to prevent desync
            import json
            self.project_data["research_data"] = json.dumps(results_dict)
            
            self._on_research_type_changed()
            self._render_updations(results_dict.get("updations", ""))
            self._update_publishing_advisor()
            QMessageBox.information(self, "Research Complete", "Research and Updations have been updated!")

    # --- DATA LOADING & INTERACTION ---
    def load_project(self, project_id):
        self.project_id = project_id
        self.project_data = self.repo.get_project(project_id)

        if not self.project_data:
            return

        name = self.project_data.get("name") or "Untitled Project"
        self.title_label.setText(name)
        self.project_id_lbl.setText(f"ID: PRJ-{project_id:04d}")
        
        # Path
        slug = name.lower().replace(" ", "-")
        self.sub_path_label.setText(f"/workspace/projects/{slug}")

        # Status badge
        status = (self.project_data.get("status") or "Planning").strip()
        status_lower = status.lower()

        if "progress" in status_lower:
            dot_color = "#fbbf24"
            badge_style = "background-color: rgba(120, 53, 15, 0.45); border: 1px solid rgba(245, 158, 11, 0.4); color: #fcd34d;"
        elif "active" in status_lower:
            dot_color = "#34d399"
            badge_style = "background-color: rgba(6, 78, 59, 0.45); border: 1px solid rgba(16, 185, 129, 0.4); color: #6ee7b7;"
        elif "completed" in status_lower or "done" in status_lower:
            dot_color = f"{self.palette.fg_muted}"
            badge_style = f"background-color: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.4); color: {self.palette.fg_muted};"
        else:
            dot_color = "#60a5fa"
            badge_style = "background-color: rgba(30, 58, 138, 0.45); border: 1px solid rgba(59, 130, 246, 0.4); color: #93c5fd;"

        self.status_badge.setText(f'<span style="color: {dot_color}; font-size: 11px;">●</span>  Status: {status}')
        self.status_badge.setStyleSheet(f"""
            {badge_style}
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.metric_status.setText(status)

        # Description
        self.desc_label.setText(self.project_data.get("description") or "No description provided.")

        # Features
        features = self.project_data.get("features") or ""
        if features.strip():
            self.features_label.setText(features)
            self.features_title.show()
            self.features_label.show()
        else:
            self.features_title.hide()
            self.features_label.hide()

        # Tech stack
        self._render_tech_stack(self.project_data.get("technology_stack") or "")

        # Sub-widgets
        self.load_tasks()
        self.load_docs()
        self.load_activities()
        
        # Load Media
        if hasattr(self, 'media_widget'):
            self.media_widget.load_entity("project", project_id)

        # Initialize chat context for this specific project
        self.chat_page.set_project(project_id)
        
        # Load Research Data
        import json
        r_data = self.project_data.get("research_data")
        if r_data:
            try:
                self.current_research_data = json.loads(r_data)
                self._on_research_type_changed()
                self._render_updations(self.current_research_data.get("updations", ""))
                self._update_publishing_advisor()
            except:
                self.current_research_data = None
                self.research_browser.setPlainText("Research data corrupted. Please regenerate.")
                self._render_updations("")
        else:
            self.current_research_data = None
            self.research_browser.setPlainText("No research data found. Click 'Generate Actionable Research'.")
            self._render_updations("")
            self._update_publishing_advisor()

    def _render_tech_stack(self, raw_stack):
        while self.stack_layout.count():
            child = self.stack_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if "," in raw_stack:
            techs = [t.strip() for t in raw_stack.split(",") if t.strip()]
        elif raw_stack.strip():
            techs = [t.strip() for t in raw_stack.split() if t.strip()]
        else:
            techs = []

        if techs:
            for tech in techs[:8]:
                tag = QLabel(tech)
                tag.setStyleSheet(f"""
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 12px;
                    font-family: 'JetBrains Mono', monospace;
                    color: {self.palette.fg_muted};
                """)
                self.stack_layout.addWidget(tag)
        else:
            na_tag = QLabel("N/A")
            na_tag.setStyleSheet(f"""
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 12px;
                color: {self.palette.fg_muted};
            """)
            self.stack_layout.addWidget(na_tag)

    def load_tasks(self):
        while self.tasks_list_layout.count():
            child = self.tasks_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tasks = self.repo.get_tasks(self.project_id)
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "Completed")
        pending_tasks = total_tasks - completed_tasks

        self.tasks_count_badge.setText(str(total_tasks))
        self.tasks_summary_lbl.setText(f"{pending_tasks} pending, {completed_tasks} completed")
        self.metric_tasks.setText(f"{completed_tasks} / {total_tasks}")

        if not tasks:
            empty_lbl = QLabel("No tasks yet. Add one above to start tracking progress.")
            empty_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 13px; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_list_layout.addWidget(empty_lbl)
        else:
            for t in tasks:
                item_widget = TaskItemWidget(t)
                item_widget.status_changed.connect(self._on_task_status_changed)
                item_widget.delete_requested.connect(self._on_task_deleted)
                self.tasks_list_layout.addWidget(item_widget)

    def _on_task_status_changed(self, task_id, new_status):
        self.repo.update_task_status(task_id, new_status)
        self.load_tasks()
        self.load_activities()

    def _on_task_deleted(self, task_id):
        self.repo.delete_task(task_id)
        self.load_tasks()
        self.load_activities()

    def add_task(self):
        title = self.new_task_input.text().strip()
        if title:
            self.repo.add_task(self.project_id, title)
            self.new_task_input.clear()
            self.load_tasks()
            self.load_activities()

    def _handle_gen_btn_clicked(self):
        action = getattr(self, "current_blank_doc_action", "readme")
        self.trigger_ai_action(action)

    def load_docs(self):
        docs = self.repo.get_documents(self.project_id)
        current_title = getattr(self, 'current_doc_title', "README.md")
        
        found_content = None
        for d in docs:
            if d.get("title") == current_title:
                found_content = d.get("content")
                break
                
        if found_content:
            self.docs_editor.setPlainText(found_content)
            self.metric_docs.setText(f"{current_title} (Synced)")
            self.docs_editor.setVisible(True)
            self.docs_preview.setVisible(True)
            self.blank_doc_widget.setVisible(False)
        else:
            self.docs_editor.setPlainText("")
            self.metric_docs.setText(f"{current_title} (Draft)")
            self.docs_editor.setVisible(False)
            self.docs_preview.setVisible(False)
            self.blank_doc_widget.setVisible(True)
            if current_title == "README.md":
                self.blank_gen_btn.setText(" Generate README")
                self.current_blank_doc_action = "readme"
            else:
                self.blank_gen_btn.setText(" Generate PRD")
                self.current_blank_doc_action = "prd" 
                
        self._update_docs_preview()

    def save_docs(self):
        content = self.docs_editor.toPlainText()
        current_title = getattr(self, 'current_doc_title', "README.md")
        self.repo.save_document(self.project_id, current_title, content)
        self.load_activities()
        self.metric_docs.setText(f"{current_title} (Saved)")
        QMessageBox.information(self, "Success", f"{current_title} saved successfully to local database.")

    def load_activities(self):
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        activities = self.repo.get_activities(self.project_id)
        if not activities:
            empty_lbl = QLabel("No activity recorded yet.")
            empty_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 13px; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_layout.addWidget(empty_lbl)
        else:
            for act in activities:
                row = QFrame()
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {self.palette.bg_card};
                        border: 1px solid {self.palette.border_card};
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        border-color: {self.palette.border_subtle};
                    }}
                """)
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 10, 12, 10)
                rl.setSpacing(12)

                time_lbl = QLabel(act.get("created_at", "Recently"))
                time_lbl.setStyleSheet(f"font-size: 11px; font-family: monospace; color: {self.palette.fg_muted}; background: transparent;")
                rl.addWidget(time_lbl)

                type_badge = QLabel(act.get("activity_type", "Event"))
                type_badge.setStyleSheet(f"""
                    background-color: rgba(30, 41, 59, 0.8);
                    border: 1px solid rgba(51, 65, 85, 0.6);
                    color: {self.palette.fg_muted};
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 11px;
                    font-weight: 500;
                """)
                rl.addWidget(type_badge)

                desc = QLabel(act.get("description", ""))
                desc.setStyleSheet(f"font-size: 13px; color: {self.palette.fg_muted}; background: transparent;")
                desc.setWordWrap(True)
                desc.setMinimumWidth(1)
                rl.addWidget(desc, 1)

                self.activity_layout.addWidget(row)

    def trigger_ai_action(self, action_type, old_content=None):
        # Publishing Advisor Check for LinkedIn
        if action_type == "linkedin" and not old_content:
            if hasattr(self, 'current_research_data') and self.current_research_data:
                import json
                raw = self.current_research_data.get("publishing_strategy", "{}")
                data = json.loads(raw) if isinstance(raw, str) else raw
                li = data.get("linkedin_suitability", "")
                if "Not Recommended" in li:
                    reply = QMessageBox.warning(self, "Advisor Note", "This project appears to be very basic or tutorial-level. Posting this on LinkedIn might dilute your professional portfolio.\n\nDo you still want to generate a post?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                        
        if action_type in ["readme", "prd"] and not old_content:
            self.trigger_doc_qa(action_type)
            return
        self._start_ai_worker(action_type, old_content=old_content)

    def trigger_doc_qa(self, doc_type):
        proj_name = self.project_data.get("name", "Project")
        proj_desc = self.project_data.get("description", "")
        proj_stack = self.project_data.get("technology_stack", "")
        
        prompt = f"Based on this project (Name: {proj_name}, Desc: {proj_desc}, Stack: {proj_stack}), I want to write a highly detailed {doc_type.upper()}. Please ask exactly 3 to 5 critical questions that the developer needs to answer to fill in missing gaps about core features, architecture, target audience, or goals. Format the output as plain text with one question per line, starting with a number."
        
        worker = AIActionWorker(self.db, "qa_" + doc_type, prompt, "")
        worker.signals.finished.connect(self._on_qa_generated)
        worker.signals.error.connect(self._on_ai_action_error)
        self.thread_pool.start(worker)
        QMessageBox.information(self, "Analyzing Project", f"AI is analyzing your project and generating questions for the {doc_type.upper()}...")

    def _on_qa_generated(self, action_type, result_text):
        doc_type = action_type.replace("qa_", "")
        questions = [q.strip() for q in result_text.split("\n") if q.strip() and (q[0].isdigit() or q.startswith("-") or q.startswith("Q"))]
        if not questions:
            questions = ["What are the core features?", "What is the primary technical goal?", "Who is the target audience?"]
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{doc_type.upper()} Insight Questions")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(f"background-color: {self.palette.bg_app}; color: {self.palette.fg_primary};")
        
        layout = QVBoxLayout(dialog)
        
        desc_lbl = QLabel(f"To generate a perfect {doc_type.upper()}, please answer these questions:")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        
        answer_inputs = []
        for i, q in enumerate(questions):
            q_lbl = QLabel(q)
            q_lbl.setWordWrap(True)
            q_lbl.setStyleSheet(f"font-weight: bold; margin-top: 10px;")
            inner_layout.addWidget(q_lbl)
            
            ans_in = QTextEdit()
            ans_in.setFixedHeight(60)
            ans_in.setStyleSheet(f"background-color: {self.palette.bg_input}; border: 1px solid {self.palette.border_card}; border-radius: 6px; padding: 4px;")
            inner_layout.addWidget(ans_in)
            answer_inputs.append((q, ans_in))
            
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        skip_btn = QPushButton("Skip & Generate Basic")
        skip_btn.setStyleSheet(f"background-color: {self.palette.bg_card}; padding: 8px 16px; border-radius: 4px;")
        skip_btn.clicked.connect(lambda: dialog.done(0))
        
        gen_btn = QPushButton("Generate with Answers")
        gen_btn.setStyleSheet(f"background-color: {self.palette.accent}; color: {self.palette.bg_app}; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        gen_btn.clicked.connect(lambda: dialog.done(1))
        
        btn_layout.addStretch()
        btn_layout.addWidget(skip_btn)
        btn_layout.addWidget(gen_btn)
        layout.addLayout(btn_layout)
        
        res = dialog.exec()
        
        qa_context = ""
        if res == 1:
            qa_context = "Here are the answers to the questions:\n"
            for q, ans_in in answer_inputs:
                ans_text = ans_in.toPlainText().strip()
                if ans_text:
                    qa_context += f"Q: {q}\nA: {ans_text}\n\n"
                    
        self._start_ai_worker(doc_type, qa_context)

    def _start_ai_worker(self, action_type, qa_context="", old_content=None):
        provider_repo = ProviderRepository(self.db)
        if not provider_repo.get_available_models():
            QMessageBox.warning(
                self, "AI Provider Required",
                "No connected AI providers found. Please configure an API key in the AI Providers screen."
            )
            return

        proj_name = self.project_data.get("name", "Project")
        proj_desc = self.project_data.get("description", "")
        proj_stack = self.project_data.get("technology_stack", "")
        
        link = self.project_data.get("live_link", "")
        link_text = f"\nLive Link: {link}" if link else ""
        features = self.project_data.get("features", "")
        feat_text = f"\nKey Features: {features}" if features else ""
        
        context = f"Project: {proj_name}\nDescription: {proj_desc}\nTech Stack: {proj_stack}{link_text}{feat_text}\n\n{qa_context}"

        prompt = ""
        if action_type == "readme":
            prompt = "Write a comprehensive, professional README.md for this project. Include fully formatted Github-style markdown, symbols (like python, javascript, etc), badges (e.g. ![Status](https://img.shields.io/badge/Status-Live-success)), Tech Stack, Key Features, and Live Link if provided. DO NOT USE EMOJIS."
        elif action_type == "prd":
            prompt = "Write a structured Product Requirements Document (PRD) for this project. Keep the Technical Info section small but clear. Focus heavily and properly on the main goal, core features, and user value. NO emojis, purely professional markdown structure."
        elif action_type == "arch":
            prompt = "Analyze the software architecture for this project. Suggest high-level system design, modular layers, database schema optimization, and security best practices."
        elif action_type == "linkedin":
            prompt = "Write an engaging, professional LinkedIn post announcing this project, highlighting the technical challenges solved, tech stack, and future roadmap. IMPORTANT: Include placeholders where the user should tag relevant people, organizations, or credential issuers (e.g., '<Tag the company or organization>'). Also, at the very end of the post, add a '[Suggested Media]' section recommending exactly what kind of images/videos to attach (e.g., '[Suggested Media: Post your certificate, or a screenshot of the application working, or a quick demo video]')."
        else:
            # Check dynamic actions
            for a in self.active_ai_actions:
                if a["id"] == action_type and a.get("prompt"):
                    prompt = a["prompt"]
                    break
            if not prompt:
                return

        worker = AIActionWorker(self.db, action_type, prompt, context)
        worker.signals.finished.connect(self._on_ai_action_finished)
        worker.signals.error.connect(self._on_ai_action_error)
        self.thread_pool.start(worker)
        QMessageBox.information(self, "AI Operation Started", f"AI task '{action_type}' initiated in the background. The result will appear shortly.")

    def _on_ai_action_finished(self, action_type, result_text):
        if action_type in ["readme", "prd"]:
            self.current_doc_title = "README.md" if action_type == "readme" else "PRD"
            if hasattr(self, 'doc_selector'):
                self.doc_selector.setCurrentText(self.current_doc_title)
            self.docs_editor.setVisible(True)
            self.docs_preview.setVisible(True)
            self.blank_doc_widget.setVisible(False)
            self.docs_editor.setPlainText(result_text)
            self._update_docs_preview()
            self.tabs.setCurrentIndex(1)  # Switch to docs tab
            QMessageBox.information(self, f"AI {action_type.upper()} Generated", f"The generated {action_type.upper()} has been loaded. Review and click Save!")
        else:
            if action_type == "linkedin":
                dlg = QMessageBox(self)
                dlg.setWindowTitle("LinkedIn Post Generated")
                dlg.setText("Your new LinkedIn post has been generated/updated.")
                dlg.setDetailedText(result_text)
                
                btn_save = dlg.addButton("Save & Replace Old", QMessageBox.ButtonRole.AcceptRole)
                btn_copy = dlg.addButton("Copy to Clipboard", QMessageBox.ButtonRole.ActionRole)
                btn_close = dlg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
                
                dlg.exec()
                
                if dlg.clickedButton() == btn_save:
                    with self.db.get_connection() as conn:
                        conn.execute("UPDATE projects SET linkedin_post = ? WHERE id = ?", (result_text, self.project_id))
                        conn.commit()
                    QMessageBox.information(self, "Saved", "LinkedIn post updated in database.")
                elif dlg.clickedButton() == btn_copy:
                    from PySide6.QtGui import QGuiApplication
                    QGuiApplication.clipboard().setText(result_text)
            else:
                # Display result in dialog
                dlg = QMessageBox(self)
                dlg.setWindowTitle("AI Analysis Result")
                dlg.setText(f"### AI Output\n\nGenerated output is ready.")
                dlg.setDetailedText(result_text)
                dlg.exec()
            
            # Start background worker to replace this action with a new one
            from app.ai.action_suggester import ActionSuggesterWorker
            suggester = ActionSuggesterWorker(self.db, self.project_data, self.active_ai_actions, action_type)
            suggester.signals.finished.connect(self._on_new_action_suggested)
            self.thread_pool.start(suggester)

    def _on_new_action_suggested(self, old_action_id, new_label, new_prompt):
        import uuid
        new_id = f"custom_{uuid.uuid4().hex[:6]}"
        
        # Replace old action with new one
        for i, action in enumerate(self.active_ai_actions):
            if action["id"] == old_action_id:
                self.active_ai_actions[i] = {"id": new_id, "label": new_label, "prompt": new_prompt}
                break
        self._render_ai_actions()

    def _on_ai_action_error(self, error_msg):
        QMessageBox.warning(self, "AI Error", f"Failed to complete AI action: {error_msg}")

    def edit_project(self):
        from app.ui.components.project_dialog import ProjectDialog
        dialog = ProjectDialog(self, self.project_data)
        if dialog.exec():
            data = dialog.get_data()
            
            # Check for changes
            changed = False
            if (data["name"] != self.project_data.get("name") or 
                data["description"] != self.project_data.get("description") or 
                data["features"] != self.project_data.get("features") or 
                data["tech_stack"] != self.project_data.get("technology_stack") or 
                data["status"] != self.project_data.get("status")):
                changed = True
                
            if changed:
                self.repo.update_project(
                    self.project_id, 
                    data["name"], 
                    data["description"], 
                    data["tech_stack"], 
                    data["status"],
                    data["features"]
                )
                self.load_project(self.project_id)
                
                # Check for stale content
                has_readme = False
                has_linkedin = False
                old_readme = ""
                old_linkedin = ""
                
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT content FROM project_documents WHERE project_id = ? AND title = 'README.md'", (self.project_id,))
                    row = cursor.fetchone()
                    if row:
                        has_readme = True
                        old_readme = row["content"]
                        
                    cursor.execute("SELECT linkedin_post FROM projects WHERE id = ?", (self.project_id,))
                    row = cursor.fetchone()
                    if row and row["linkedin_post"]:
                        has_linkedin = True
                        old_linkedin = row["linkedin_post"]
                
                if has_readme or has_linkedin:
                    items = []
                    if has_readme: items.append("README.md")
                    if has_linkedin: items.append("LinkedIn Post")
                    msg = f"Project updated! The following attached content may now be outdated: {', '.join(items)}.\n\nWould you like the AI to automatically update them using the new features/description while preserving the old style?"
                    reply = QMessageBox.question(self, "Stale Content Detected", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        if has_readme:
                            self.trigger_ai_action("readme", old_content=old_readme)
                        if has_linkedin:
                            self.trigger_ai_action("linkedin", old_content=old_linkedin)
                
                if hasattr(self, 'trigger_ai_research_update'):
                    self.trigger_ai_research_update()

    def delete_project(self):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{self.project_data.get('name')}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_project(self.project_id)
            self.back_requested.emit()

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        
        if self.project_id:
            # We can just reload the project to reconstruct the UI with the new palette
            self.load_project(self.project_id)
