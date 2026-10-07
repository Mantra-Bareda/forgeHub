from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton,
    QCheckBox, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
import os

from app.ui.components.icons import get_svg_icon
from app.core.palette import ColorPalette
from app.core.theme import get_current_palette, theme_manager


class ProjectFormWidget(QWidget):
    saved = Signal(int)
    cancelled = Signal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.palette = get_current_palette()
        self.setObjectName("projectFormRoot")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 24)
        main_layout.setSpacing(16)

        # Top Header Bar
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        # Back / Cancel button
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setText(" Cancel")
        self.back_btn.setFixedHeight(32)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(self.back_btn)

        self.sep = QFrame()
        self.sep.setObjectName("sep")
        self.sep.setFixedWidth(1)
        self.sep.setFixedHeight(24)
        header_layout.addWidget(self.sep)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        self.header_title = QLabel("Create New Project Workspace")
        self.header_title.setObjectName("headerTitle")
        title_col.addWidget(self.header_title)

        self.header_sub = QLabel("Configure repository metadata and features.")
        self.header_sub.setObjectName("headerSub")
        title_col.addWidget(self.header_sub)

        header_layout.addLayout(title_col, 1)

        # Save Button on Header
        self.save_header_btn = QPushButton()
        self.save_header_btn.setObjectName("saveHeaderBtn")
        self.save_header_btn.setText(" Save Project")
        self.save_header_btn.setFixedHeight(32)
        self.save_header_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_header_btn.clicked.connect(self.save_project)
        header_layout.addWidget(self.save_header_btn)

        main_layout.addWidget(self.header_frame)

        # Scroll area for form
        self.scroll = QScrollArea()
        self.scroll.setObjectName("scrollArea")
        self.scroll.setWidgetResizable(True)

        self.form_card = QFrame()
        self.form_card.setObjectName("formCard")
        
        self.layout = QVBoxLayout(self.form_card)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(14)

        # Core details
        self.layout.addWidget(QLabel("PROJECT NAME *"))
        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText("e.g. Distributed Task Orchestrator")
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("DESCRIPTION *"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(85)
        self.desc_input.setPlaceholderText("A concise summary of the workspace and intended system goals...")
        self.layout.addWidget(self.desc_input)

        self.layout.addWidget(QLabel("TECHNOLOGY STACK (COMMA SEPARATED) *"))
        self.tech_input = QLineEdit()
        self.tech_input.setFixedHeight(36)
        self.tech_input.setPlaceholderText("e.g. Python, PySide6, SQLite, Redis")
        self.layout.addWidget(self.tech_input)


        self.layout.addWidget(QLabel("KEY FEATURES (OPTIONAL)"))
        self.features_input = QTextEdit()
        self.features_input.setMaximumHeight(80)
        self.features_input.setPlaceholderText("- Local SQLite storage with hot backup\n- Asynchronous prompt generation\n- Cross-platform desktop interface")
        self.layout.addWidget(self.features_input)

        self.layout.addWidget(QLabel("LIVE APP LINK (OPTIONAL)"))
        self.link_input = QLineEdit()
        self.link_input.setFixedHeight(36)
        self.link_input.setPlaceholderText("https://github.com/user/repo or live web demo")
        self.layout.addWidget(self.link_input)

        # Integrations
        self.sep_int = QFrame()
        self.sep_int.setObjectName("sepInt")
        self.sep_int.setFixedHeight(1)
        self.layout.addWidget(self.sep_int)

        self.int_title = QLabel("CROSS-PLATFORM INTEGRATIONS")
        self.int_title.setObjectName("intTitle")
        self.layout.addWidget(self.int_title)

        self.github_cb = QCheckBox("Track and sync in GitHub repository summary")
        self.layout.addWidget(self.github_cb)

        self.linkedin_cb = QCheckBox("Create LinkedIn launch post")
        self.linkedin_cb.toggled.connect(self.toggle_linkedin_post)
        self.layout.addWidget(self.linkedin_cb)

        self.linkedin_post_label = QLabel("LINKEDIN POST DRAFT CONTENT:")
        self.linkedin_post_input = QTextEdit()
        self.linkedin_post_input.setMaximumHeight(90)
        self.linkedin_post_input.setPlaceholderText("Excited to share my new open source project...")
        self.linkedin_post_label.hide()
        self.linkedin_post_input.hide()

        self.linkedin_media_label = QLabel("LINKEDIN MEDIA ATTACHMENT DESCRIPTION:")
        self.linkedin_media_input = QLineEdit()
        self.linkedin_media_input.setFixedHeight(36)
        self.linkedin_media_input.setPlaceholderText("e.g. Architecture diagram of core worker threads")
        self.linkedin_media_label.hide()
        self.linkedin_media_input.hide()

        self.layout.addWidget(self.linkedin_post_label)
        self.layout.addWidget(self.linkedin_post_input)
        self.layout.addWidget(self.linkedin_media_label)
        self.layout.addWidget(self.linkedin_media_input)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 16, 0, 0)
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.cancelled.emit)

        self.save_btn = QPushButton("Save Project Workspace")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_project)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        self.layout.addLayout(btn_layout)

        self.scroll.setWidget(self.form_card)
        main_layout.addWidget(self.scroll, 1)

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.back_btn.setIcon(get_svg_icon("arrow_back", pal.fg_muted, 16))
        self.save_header_btn.setIcon(get_svg_icon("save", "#ffffff", 14))

        self.setStyleSheet(f"""
            QWidget#projectFormRoot {{
                background-color: {self.palette.bg_app};
            }}
            QFrame#headerFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
                padding: 12px 16px;
            }}
            QPushButton#backBtn, QPushButton#cancelBtn {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }}
            QPushButton#backBtn:hover, QPushButton#cancelBtn:hover {{
                background-color: {self.palette.bg_card};
                border-color: {self.palette.accent};
                color: {self.palette.fg_primary};
            }}
            QFrame#sep {{
                background-color: {self.palette.border_card};
            }}
            QLabel#headerTitle {{
                font-size: 18px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: -0.3px;
                background: transparent;
            }}
            QLabel#headerSub {{
                font-size: 12px; color: {self.palette.fg_muted};
                background: transparent;
            }}
            QPushButton#saveHeaderBtn, QPushButton#saveBtn {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton#saveHeaderBtn:hover, QPushButton#saveBtn:hover {{
                background-color: {self.palette.accent};
            }}
            QScrollArea#scrollArea {{
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
            QFrame#formCard {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QFrame#formCard QLabel {{
                background: transparent;
                color: {self.palette.fg_muted};
                font-size: 12px;
                font-weight: 600;
            }}
            QFrame#formCard QLineEdit, QFrame#formCard QTextEdit {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 13px;
                padding: 8px 12px;
            }}
            QFrame#formCard QLineEdit:focus, QFrame#formCard QTextEdit:focus {{
                border-color: {self.palette.accent};
            }}
            QFrame#formCard QCheckBox {{
                color: {self.palette.fg_primary};
                font-size: 13px;
                background: transparent;
                spacing: 8px;
            }}
            QFrame#formCard QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {self.palette.border_subtle};
                background-color: {self.palette.bg_input};
            }}
            QFrame#formCard QCheckBox::indicator:checked {{
                background-color: {self.palette.accent};
                border-color: {self.palette.accent};
            }}
            QFrame#sepInt {{
                background-color: {self.palette.border_card}; margin-top: 10px; margin-bottom: 6px;
            }}
            QLabel#intTitle {{
                font-size: 13px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: 0.5px;
            }}
        """)

    def toggle_linkedin_post(self, checked):
        self.linkedin_post_label.setVisible(checked)
        self.linkedin_post_input.setVisible(checked)
        self.linkedin_media_label.setVisible(checked)
        self.linkedin_media_input.setVisible(checked)

    def save_project(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        tech = self.tech_input.text().strip()

        # Validation
        if not name or not desc or not tech:
            QMessageBox.warning(
                self, "Validation Error", 
                "Please fill in all mandatory fields:\n• Project Name\n• Description\n• Tech Stack"
            )
            return

        features = self.features_input.toPlainText().strip()
        link = self.link_input.text().strip()

        github_added = self.github_cb.isChecked()
        linkedin_added = self.linkedin_cb.isChecked()
        linkedin_post = self.linkedin_post_input.toPlainText().strip() if linkedin_added else ""
        linkedin_media = self.linkedin_media_input.text().strip() if linkedin_added else ""

        from database.repository import ProjectRepository, ProfileRepository
        proj_repo = ProjectRepository(self.db)
        prof_repo = ProfileRepository(self.db)

        # Save project
        pid = proj_repo.create_project(name, desc, tech, "Planning", features, link, github_added, linkedin_added, linkedin_post)
        if hasattr(self, 'media_widget'):
            self.media_widget.save_pending_files(pid)

        # Cross-pollinate to GitHub
        if github_added:
            gh_data = prof_repo.get_github_data()
            curr_gh = gh_data.get("projects_summary") or ""
            new_gh = f"{curr_gh}\n\n- {name}: {desc}".strip()
            prof_repo.update_github_data({"projects_summary": new_gh})

        # Cross-pollinate to LinkedIn
        if linkedin_added:
            prof_repo.add_linkedin_project(name, desc)
            if linkedin_post or linkedin_media:
                media_desc = linkedin_media if linkedin_media else f"Media related to project: {name}"
                prof_repo.add_linkedin_post(linkedin_post, media_desc)

        # Trigger Memory Update
        from PySide6.QtCore import QThreadPool
        from app.ui.pages.memory import ProfileSyncWorker
        pool = QThreadPool.globalInstance()
        pool.start(ProfileSyncWorker(self.db))

        QMessageBox.information(self, "Success", "Project saved successfully. Integrations and memory updated.")
        self.clear_form()
        self.saved.emit(pid)

    def clear_form(self):
        self.name_input.clear()
        self.desc_input.clear()
        self.tech_input.clear()
        self.features_input.clear()
        self.link_input.clear()
        self.github_cb.setChecked(False)
        self.linkedin_cb.setChecked(False)
        self.linkedin_post_input.clear()
        self.linkedin_media_input.clear()
