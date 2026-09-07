from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QLineEdit, QTextEdit, QTextBrowser,
    QMessageBox, QFrame, QScrollArea, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThreadPool, QRunnable, QObject
from PySide6.QtGui import QCursor, QFont

from database.repository import ProjectRepository, ProviderRepository
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


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
        self.task_id = task_data["id"]
        self.status = task_data.get("status", "Pending")
        self.title = task_data.get("title", "")

        self.setObjectName("taskItem")
        self.setFixedHeight(44)
        self.setStyleSheet("""
            #taskItem {
                background-color: #191b22;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            #taskItem:hover {
                border: 1px solid #334155;
                background-color: #1c202a;
            }
            #taskItem QLabel {
                background: transparent;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(10)

        # Checkbox
        self.cb = QCheckBox()
        self.cb.setChecked(self.status == "Completed")
        self.cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #404752;
                background-color: #131b2a;
            }
            QCheckBox::indicator:hover {
                border-color: #2196f3;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
            }
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
        del_btn.setIcon(get_svg_icon("delete", "#64748b", 14))
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
            self.title_lbl.setStyleSheet("font-size: 13px; color: #64748b; text-decoration: line-through;")
        else:
            self.title_lbl.setStyleSheet("font-size: 13px; color: #f1f5f9;")

    def _update_badge_style(self):
        self.badge_lbl.setText(self.status)
        if self.status == "Completed":
            self.badge_lbl.setStyleSheet("""
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(71, 85, 105, 0.4);
                color: #94a3b8;
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
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.project_id = None
        self.project_data = None
        self.thread_pool = QThreadPool.globalInstance()

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f17;
            }
            QLabel {
                background: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 24)
        main_layout.setSpacing(16)

        # 1. Top Header Bar
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        self.header_frame.setStyleSheet("""
            #headerFrame {
                background-color: #101623;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 12px 16px;
            }
            #headerFrame QLabel {
                background: transparent;
            }
        """)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        # Back button
        self.back_btn = QPushButton()
        self.back_btn.setIcon(get_svg_icon("arrow_back", "#94a3b8", 16))
        self.back_btn.setText(" Back")
        self.back_btn.setFixedHeight(32)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #283548;
                border-color: #2196f3;
                color: #ffffff;
            }
        """)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(self.back_btn)

        # Vertical separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background-color: #1e293b;")
        header_layout.addWidget(sep)

        # Title + Status + Path column
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        title_badge_row = QHBoxLayout()
        title_badge_row.setSpacing(10)

        self.title_label = QLabel("Project Details")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.3px;")
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
        self.sub_path_label.setStyleSheet("font-size: 11px; font-family: monospace; color: #64748b;")
        title_col.addWidget(self.sub_path_label)

        header_layout.addLayout(title_col, 1)

        # Edit and Delete buttons
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(get_svg_icon("edit", "#cbd5e1", 14))
        self.edit_btn.setText(" Edit Project")
        self.edit_btn.setFixedHeight(32)
        self.edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #283548;
                border-color: #2196f3;
                color: #ffffff;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_project)
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(get_svg_icon("delete", "#f87171", 14))
        self.delete_btn.setText(" Delete")
        self.delete_btn.setFixedHeight(32)
        self.delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(147, 0, 10, 0.2);
                border: 1px solid rgba(255, 180, 171, 0.3);
                border-radius: 6px;
                color: #ffb4ab;
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: rgba(147, 0, 10, 0.35);
                border-color: #ffb4ab;
                color: #ffffff;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_project)
        header_layout.addWidget(self.delete_btn)

        main_layout.addWidget(self.header_frame)

        # 2. Modern Tab Navigation
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
                top: -1px;
            }
            QTabBar::tab {
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 500;
                padding: 10px 18px;
                margin-right: 6px;
            }
            QTabBar::tab:hover {
                color: #f1f5f9;
            }
            QTabBar::tab:selected {
                color: #2196f3;
                border-bottom: 2px solid #2196f3;
                font-weight: 600;
            }
        """)
        main_layout.addWidget(self.tabs)

        # Setup Tab Pages
        self._setup_overview_tab()
        self._setup_docs_tab()
        self._setup_tasks_tab()
        self._setup_chat_tab()
        self._setup_activity_tab()

    # --- TAB 1: OVERVIEW ---
    def _setup_overview_tab(self):
        self.overview_tab = QWidget()
        self.overview_tab.setStyleSheet("background: transparent;")
        tab_layout = QHBoxLayout(self.overview_tab)
        tab_layout.setContentsMargins(0, 12, 0, 0)
        tab_layout.setSpacing(16)

        # Left Column: Project Overview Card
        overview_card = QFrame()
        overview_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        oc_layout = QVBoxLayout(overview_card)
        oc_layout.setContentsMargins(20, 20, 20, 20)
        oc_layout.setSpacing(14)

        # Header of Overview Card
        card_header = QHBoxLayout()
        card_header.setContentsMargins(0, 0, 0, 0)

        info_icon = QLabel()
        info_icon.setPixmap(get_svg_pixmap("info", "#2196f3", 18))
        card_header.addWidget(info_icon)

        ch_title = QLabel("Project Overview")
        ch_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f1f5f9;")
        card_header.addWidget(ch_title)
        card_header.addStretch()

        self.project_id_lbl = QLabel("ID: PRJ-0000")
        self.project_id_lbl.setStyleSheet("font-size: 11px; font-family: monospace; color: #64748b;")
        card_header.addWidget(self.project_id_lbl)
        oc_layout.addLayout(card_header)

        # Divider
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: #1e293b; border: none;")
        oc_layout.addWidget(div1)

        # Description Section
        desc_title = QLabel("DESCRIPTION")
        desc_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.5px;")
        oc_layout.addWidget(desc_title)

        self.desc_label = QLabel("No description provided.")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 13px; color: #cbd5e1; line-height: 1.5;")
        oc_layout.addWidget(self.desc_label)

        # Tech Stack Section
        stack_title = QLabel("TECHNOLOGY STACK")
        stack_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.5px; margin-top: 8px;")
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
        self.features_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.5px; margin-top: 8px;")
        oc_layout.addWidget(self.features_title)

        self.features_label = QLabel("No features specified.")
        self.features_label.setWordWrap(True)
        self.features_label.setStyleSheet("font-size: 13px; color: #94a3b8; line-height: 1.4;")
        oc_layout.addWidget(self.features_label)

        oc_layout.addStretch()
        tab_layout.addWidget(overview_card, 2)

        # Right Column: Metrics & Quick Actions
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(16)

        # Metrics Card
        metrics_card = QFrame()
        metrics_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        mc_layout = QVBoxLayout(metrics_card)
        mc_layout.setContentsMargins(18, 18, 18, 18)
        mc_layout.setSpacing(12)

        mc_header = QHBoxLayout()
        m_icon = QLabel()
        m_icon.setPixmap(get_svg_pixmap("analytics", "#4edea3", 16))
        mc_header.addWidget(m_icon)

        mc_title = QLabel("Workspace Metrics")
        mc_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9;")
        mc_header.addWidget(mc_title)
        mc_header.addStretch()
        mc_layout.addLayout(mc_header)

        # Metric row helper
        def make_metric_row(label, val_widget):
            row = QFrame()
            row.setStyleSheet("background-color: #191b22; border-radius: 6px; border: 1px solid #1e293b;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(val_widget)
            return row

        self.metric_tasks = QLabel("0 / 0")
        self.metric_tasks.setStyleSheet("font-size: 12px; font-weight: 600; font-family: monospace; color: #f1f5f9; background: transparent;")
        mc_layout.addWidget(make_metric_row("Active Tasks", self.metric_tasks))

        self.metric_docs = QLabel("README.md")
        self.metric_docs.setStyleSheet("font-size: 12px; font-family: monospace; color: #4edea3; background: transparent;")
        mc_layout.addWidget(make_metric_row("Documentation", self.metric_docs))

        self.metric_status = QLabel("Planning")
        self.metric_status.setStyleSheet("font-size: 12px; font-weight: 600; color: #93c5fd; background: transparent;")
        mc_layout.addWidget(make_metric_row("Project Status", self.metric_status))

        right_col.addWidget(metrics_card)

        # Quick AI Actions Card
        ai_card = QFrame()
        ai_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        ac_layout = QVBoxLayout(ai_card)
        ac_layout.setContentsMargins(18, 18, 18, 18)
        ac_layout.setSpacing(10)

        ac_header = QHBoxLayout()
        ac_icon = QLabel()
        ac_icon.setPixmap(get_svg_pixmap("sparkles", "#9ecaff", 16))
        ac_header.addWidget(ac_icon)
        ac_title = QLabel("Quick AI Actions")
        ac_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9;")
        ac_header.addWidget(ac_title)
        ac_header.addStretch()
        ac_layout.addLayout(ac_header)

        ac_sub = QLabel("Accelerate project tasks using configured AI models.")
        ac_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        ac_layout.addWidget(ac_sub)

        # AI Action Buttons
        def make_ai_btn(text, action_func):
            btn = QPushButton(f"  {text}")
            btn.setIcon(get_svg_icon("sparkles", "#9ecaff", 14))
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #191b22;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    color: #cbd5e1;
                    font-size: 12px;
                    font-weight: 500;
                    text-align: left;
                    padding-left: 12px;
                }
                QPushButton:hover {
                    background-color: #243248;
                    border-color: #2196f3;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(action_func)
            return btn

        self.btn_ai_readme = make_ai_btn("Improve README with AI", lambda: self.trigger_ai_action("readme"))
        ac_layout.addWidget(self.btn_ai_readme)

        self.btn_ai_arch = make_ai_btn("Analyze Architecture", lambda: self.trigger_ai_action("arch"))
        ac_layout.addWidget(self.btn_ai_arch)

        self.btn_ai_post = make_ai_btn("Draft LinkedIn Post", lambda: self.trigger_ai_action("linkedin"))
        ac_layout.addWidget(self.btn_ai_post)

        right_col.addWidget(ai_card)
        right_col.addStretch()

        tab_layout.addLayout(right_col, 1)
        self.tabs.addTab(self.overview_tab, get_svg_icon("dashboard", "#94a3b8", 16), "Overview")

    # --- TAB 2: DOCUMENTATION ---
    def _setup_docs_tab(self):
        self.docs_tab = QWidget()
        self.docs_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.docs_tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        docs_card = QFrame()
        docs_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        dc_layout = QVBoxLayout(docs_card)
        dc_layout.setContentsMargins(18, 16, 18, 18)
        dc_layout.setSpacing(12)

        # Header
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        doc_icon = QLabel()
        doc_icon.setPixmap(get_svg_pixmap("description", "#2196f3", 18))
        top_bar.addWidget(doc_icon)

        doc_title = QLabel("README.md — Markdown Editor & Live Preview")
        doc_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        top_bar.addWidget(doc_title)
        top_bar.addStretch()

        # Improve with AI button
        self.doc_ai_btn = QPushButton()
        self.doc_ai_btn.setIcon(get_svg_icon("sparkles", "#9ecaff", 14))
        self.doc_ai_btn.setText(" Improve with AI")
        self.doc_ai_btn.setFixedHeight(32)
        self.doc_ai_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.doc_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #9ecaff;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #26354f;
                border-color: #2196f3;
                color: #ffffff;
            }
        """)
        self.doc_ai_btn.clicked.connect(lambda: self.trigger_ai_action("readme"))
        top_bar.addWidget(self.doc_ai_btn)

        # Save Documentation button
        self.docs_save_btn = QPushButton()
        self.docs_save_btn.setIcon(get_svg_icon("save", "#ffffff", 14))
        self.docs_save_btn.setText(" Save Documentation")
        self.docs_save_btn.setFixedHeight(32)
        self.docs_save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.docs_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.docs_save_btn.clicked.connect(self.save_docs)
        top_bar.addWidget(self.docs_save_btn)

        dc_layout.addLayout(top_bar)

        # Splitter: Source on Left, Preview on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e293b;
                width: 2px;
            }
        """)

        # Source Editor Pane
        source_container = QWidget()
        source_container.setStyleSheet("background: transparent;")
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(0, 0, 8, 0)
        source_layout.setSpacing(6)

        source_lbl = QLabel("SOURCE (MARKDOWN)")
        source_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.5px;")
        source_layout.addWidget(source_lbl)

        self.docs_editor = QTextEdit()
        self.docs_editor.setFont(QFont("monospace", 10))
        self.docs_editor.setStyleSheet("""
            QTextEdit {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 1px solid #2196f3;
            }
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
        preview_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.5px;")
        preview_layout.addWidget(preview_lbl)

        self.docs_preview = QTextBrowser()
        self.docs_preview.setStyleSheet("""
            QTextBrowser {
                background-color: #0f141f;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 13px;
                padding: 14px;
            }
        """)
        self.docs_preview.setOpenExternalLinks(True)
        preview_layout.addWidget(self.docs_preview)
        splitter.addWidget(preview_container)

        splitter.setSizes([500, 500])
        dc_layout.addWidget(splitter, 1)

        layout.addWidget(docs_card)
        self.tabs.addTab(self.docs_tab, get_svg_icon("description", "#94a3b8", 16), "Documentation")

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
        tasks_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        tc_layout = QVBoxLayout(tasks_card)
        tc_layout.setContentsMargins(20, 20, 20, 20)
        tc_layout.setSpacing(14)

        # Header
        th_layout = QHBoxLayout()
        t_icon = QLabel()
        t_icon.setPixmap(get_svg_pixmap("checklist", "#2196f3", 18))
        th_layout.addWidget(t_icon)

        th_title = QLabel("Project Tasks")
        th_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f1f5f9;")
        th_layout.addWidget(th_title)

        self.tasks_count_badge = QLabel("0")
        self.tasks_count_badge.setStyleSheet("""
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
        """)
        th_layout.addWidget(self.tasks_count_badge)
        th_layout.addStretch()

        self.tasks_summary_lbl = QLabel("0 pending, 0 completed")
        self.tasks_summary_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        th_layout.addWidget(self.tasks_summary_lbl)
        tc_layout.addLayout(th_layout)

        # Add Task Bar
        add_bar = QHBoxLayout()
        add_bar.setContentsMargins(0, 0, 0, 0)
        add_bar.setSpacing(10)

        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Add a new task (e.g. Implement SQLite WAL mode)...")
        self.new_task_input.setFixedHeight(36)
        self.new_task_input.setStyleSheet("""
            QLineEdit {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                padding-left: 12px;
                padding-right: 12px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        self.new_task_input.returnPressed.connect(self.add_task)
        add_bar.addWidget(self.new_task_input, 1)

        add_task_btn = QPushButton("+ Add Task")
        add_task_btn.setFixedHeight(36)
        add_task_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        add_task_btn.clicked.connect(self.add_task)
        add_bar.addWidget(add_task_btn)
        tc_layout.addLayout(add_bar)

        # Scroll Area for Task Items
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0b0f17;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
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
        self.tabs.addTab(self.tasks_tab, get_svg_icon("checklist", "#94a3b8", 16), "Tasks")

    # --- TAB 4: AI CHAT ---
    def _setup_chat_tab(self):
        from app.ui.pages.chat import AIChatPage
        self.chat_page = AIChatPage(self.db)
        self.tabs.addTab(self.chat_page, get_svg_icon("chat", "#94a3b8", 16), "AI Chat")

    # --- TAB 5: ACTIVITY ---
    def _setup_activity_tab(self):
        self.activity_tab = QWidget()
        self.activity_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.activity_tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        activity_card = QFrame()
        activity_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        ac_layout = QVBoxLayout(activity_card)
        ac_layout.setContentsMargins(20, 20, 20, 20)
        ac_layout.setSpacing(14)

        # Header
        ah_layout = QHBoxLayout()
        a_icon = QLabel()
        a_icon.setPixmap(get_svg_pixmap("history", "#2196f3", 18))
        ah_layout.addWidget(a_icon)

        ah_title = QLabel("Project Activity Timeline")
        ah_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f1f5f9;")
        ah_layout.addWidget(ah_title)
        ah_layout.addStretch()
        ac_layout.addLayout(ah_layout)

        # Activity List Scroll Area
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0b0f17;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
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
        self.tabs.addTab(self.activity_tab, get_svg_icon("history", "#94a3b8", 16), "Activity")

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
            dot_color = "#94a3b8"
            badge_style = "background-color: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.4); color: #94a3b8;"
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

        # Initialize chat context for this specific project
        self.chat_page.set_chat_context(f"project_{project_id}")

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
                tag.setStyleSheet("""
                    background-color: #191b22;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 12px;
                    font-family: 'JetBrains Mono', monospace;
                    color: #cbd5e1;
                """)
                self.stack_layout.addWidget(tag)
        else:
            na_tag = QLabel("N/A")
            na_tag.setStyleSheet("""
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 12px;
                color: #64748b;
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
            empty_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 20px 0;")
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

    def load_docs(self):
        docs = self.repo.get_documents(self.project_id)
        if docs:
            content = docs[0].get("content", "")
            self.docs_editor.setPlainText(content)
            self.metric_docs.setText("README.md (Synced)")
        else:
            default_md = f"# {self.project_data.get('name', 'Project')}\n\n{self.project_data.get('description', '')}\n\n## Tech Stack\n{self.project_data.get('technology_stack', '')}\n"
            self.docs_editor.setPlainText(default_md)
            self.metric_docs.setText("README.md (Draft)")
        self._update_docs_preview()

    def save_docs(self):
        content = self.docs_editor.toPlainText()
        self.repo.save_document(self.project_id, "README.md", content)
        self.load_activities()
        self.metric_docs.setText("README.md (Saved)")
        QMessageBox.information(self, "Success", "Documentation saved successfully to local database.")

    def load_activities(self):
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        activities = self.repo.get_activities(self.project_id)
        if not activities:
            empty_lbl = QLabel("No activity recorded yet.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 20px 0;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_layout.addWidget(empty_lbl)
        else:
            for act in activities:
                row = QFrame()
                row.setStyleSheet("""
                    QFrame {
                        background-color: #191b22;
                        border: 1px solid #1e293b;
                        border-radius: 6px;
                    }
                    QFrame:hover {
                        border-color: #334155;
                    }
                """)
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 10, 12, 10)
                rl.setSpacing(12)

                time_lbl = QLabel(act.get("created_at", "Recently"))
                time_lbl.setStyleSheet("font-size: 11px; font-family: monospace; color: #64748b; background: transparent;")
                rl.addWidget(time_lbl)

                type_badge = QLabel(act.get("activity_type", "Event"))
                type_badge.setStyleSheet("""
                    background-color: rgba(30, 41, 59, 0.8);
                    border: 1px solid rgba(51, 65, 85, 0.6);
                    color: #94a3b8;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 11px;
                    font-weight: 500;
                """)
                rl.addWidget(type_badge)

                desc = QLabel(act.get("description", ""))
                desc.setStyleSheet("font-size: 13px; color: #cbd5e1; background: transparent;")
                desc.setWordWrap(True)
                rl.addWidget(desc, 1)

                self.activity_layout.addWidget(row)

    def trigger_ai_action(self, action_type):
        provider_repo = ProviderRepository(self.db)
        if not provider_repo.get_available_models():
            QMessageBox.warning(
                self, "AI Provider Required",
                "No connected AI providers found. Please configure an API key in the AI Providers screen."
            )
            return

        proj_name = self.project_data.get("name", "")
        proj_desc = self.project_data.get("description", "")
        proj_stack = self.project_data.get("technology_stack", "")
        context = f"Project: {proj_name}\nDescription: {proj_desc}\nTech Stack: {proj_stack}"

        if action_type == "readme":
            prompt = "Write a comprehensive, production-grade README.md in Markdown format for this project, including overview, architecture, prerequisites, setup instructions, and features."
        elif action_type == "arch":
            prompt = "Analyze the software architecture for this project. Suggest high-level system design, modular layers, database schema optimization, and security best practices."
        elif action_type == "linkedin":
            prompt = "Write an engaging, professional LinkedIn post announcing this project, highlighting the technical challenges solved, tech stack, and future roadmap."
        else:
            prompt = "Analyze this project and suggest next steps."

        worker = AIActionWorker(self.db, action_type, prompt, context)
        worker.signals.finished.connect(self._on_ai_action_finished)
        worker.signals.error.connect(self._on_ai_action_error)
        self.thread_pool.start(worker)
        QMessageBox.information(self, "AI Operation Started", f"AI task '{action_type}' initiated in the background. The result will appear shortly.")

    def _on_ai_action_finished(self, action_type, result_text):
        if action_type == "readme":
            self.docs_editor.setPlainText(result_text)
            self._update_docs_preview()
            self.tabs.setCurrentIndex(1)  # Switch to docs tab
            QMessageBox.information(self, "AI README Generated", "The improved README has been loaded into the Documentation editor. Review and click Save!")
        else:
            # Display result in dialog
            dlg = QMessageBox(self)
            dlg.setWindowTitle("AI Analysis Result")
            dlg.setText(f"### AI {action_type.capitalize()} Output\n\nGenerated output is ready.")
            dlg.setDetailedText(result_text)
            dlg.exec()

    def _on_ai_action_error(self, error_msg):
        QMessageBox.warning(self, "AI Error", f"Failed to complete AI action: {error_msg}")

    def edit_project(self):
        from app.ui.components.project_dialog import ProjectDialog
        dialog = ProjectDialog(self, self.project_data)
        if dialog.exec():
            data = dialog.get_data()
            self.repo.update_project(
                self.project_id, 
                data["name"], 
                data["description"], 
                data["tech_stack"], 
                data["status"]
            )
            self.load_project(self.project_id)

    def delete_project(self):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{self.project_data.get('name')}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_project(self.project_id)
            self.back_requested.emit()
