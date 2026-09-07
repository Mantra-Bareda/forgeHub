from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton,
    QCheckBox, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
import os

from app.ui.components.icons import get_svg_icon


class ReadmeDropArea(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Type README Markdown content here or drag & drop a .md / .txt file...")
        self.setFont(QFont("monospace", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0c0e14;
                border: 1px dashed #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 12px;
            }
            QTextEdit:focus {
                border: 1px solid #2196f3;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.exists(path) and (path.endswith('.md') or path.endswith('.txt')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.setPlainText(f.read())
                    event.acceptProposedAction()
                except Exception as e:
                    QMessageBox.warning(self, "Read Error", f"Could not read file: {e}")
            else:
                QMessageBox.warning(self, "Invalid File", "Please drop a .md or .txt file.")
        else:
            super().dropEvent(event)


class ProjectFormWidget(QWidget):
    saved = Signal()
    cancelled = Signal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

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

        # Top Header Bar
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet("""
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
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        # Back / Cancel button
        back_btn = QPushButton()
        back_btn.setIcon(get_svg_icon("arrow_back", "#94a3b8", 16))
        back_btn.setText(" Cancel")
        back_btn.setFixedHeight(32)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("""
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
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background-color: #1e293b;")
        header_layout.addWidget(sep)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        header_title = QLabel("Create New Project Workspace")
        header_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.3px;")
        title_col.addWidget(header_title)

        header_sub = QLabel("Configure repository metadata, documentation, and automated social integrations.")
        header_sub.setStyleSheet("font-size: 12px; color: #64748b;")
        title_col.addWidget(header_sub)

        header_layout.addLayout(title_col, 1)

        # Save Button on Header
        self.save_header_btn = QPushButton()
        self.save_header_btn.setIcon(get_svg_icon("save", "#ffffff", 14))
        self.save_header_btn.setText(" Save Project")
        self.save_header_btn.setFixedHeight(32)
        self.save_header_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_header_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.save_header_btn.clicked.connect(self.save_project)
        header_layout.addWidget(self.save_header_btn)

        main_layout.addWidget(header_frame)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
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

        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
            }
            QLineEdit, QTextEdit {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #2196f3;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 13px;
                background: transparent;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #404752;
                background-color: #191b22;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
            }
        """)
        self.layout = QVBoxLayout(form_card)
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

        self.layout.addWidget(QLabel("README.MD CONTENT *"))
        self.readme_input = ReadmeDropArea()
        self.readme_input.setMinimumHeight(180)
        self.layout.addWidget(self.readme_input)

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
        sep_int = QFrame()
        sep_int.setFixedHeight(1)
        sep_int.setStyleSheet("background-color: #1e293b; margin-top: 10px; margin-bottom: 6px;")
        self.layout.addWidget(sep_int)

        int_title = QLabel("CROSS-PLATFORM INTEGRATIONS")
        int_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9; letter-spacing: 0.5px;")
        self.layout.addWidget(int_title)

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

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 500;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #283548;
                color: #ffffff;
            }
        """)
        cancel_btn.clicked.connect(self.cancelled.emit)

        save_btn = QPushButton("Save Project Workspace")
        save_btn.setFixedHeight(36)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        save_btn.clicked.connect(self.save_project)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        self.layout.addLayout(btn_layout)

        scroll.setWidget(form_card)
        main_layout.addWidget(scroll, 1)

    def toggle_linkedin_post(self, checked):
        self.linkedin_post_label.setVisible(checked)
        self.linkedin_post_input.setVisible(checked)
        self.linkedin_media_label.setVisible(checked)
        self.linkedin_media_input.setVisible(checked)

    def save_project(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        tech = self.tech_input.text().strip()
        readme = self.readme_input.toPlainText().strip()

        # Validation
        if not name or not desc or not tech or not readme:
            QMessageBox.warning(
                self, "Validation Error", 
                "Please fill in all mandatory fields:\n• Project Name\n• Description\n• Tech Stack\n• README Markdown"
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

        # Save README
        proj_repo.save_document(pid, "README.md", readme)

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
        self.saved.emit()

    def clear_form(self):
        self.name_input.clear()
        self.desc_input.clear()
        self.tech_input.clear()
        self.features_input.clear()
        self.link_input.clear()
        self.readme_input.clear()
        self.github_cb.setChecked(False)
        self.linkedin_cb.setChecked(False)
        self.linkedin_post_input.clear()
        self.linkedin_media_input.clear()
