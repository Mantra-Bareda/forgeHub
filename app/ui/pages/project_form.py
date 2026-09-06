from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QLineEdit, QTextEdit, QPushButton, QComboBox, 
                                 QCheckBox, QMessageBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt, Signal
import os

class ReadmeDropArea(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Type README content here or drop a .md / .txt file...")

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
                with open(path, 'r', encoding='utf-8') as f:
                    self.setPlainText(f.read())
                event.acceptProposedAction()
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
        
        main_layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        header = QLabel("Create New Project")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        
        # Core details
        self.layout.addWidget(QLabel("<b>Project Name:</b>"))
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)
        
        self.layout.addWidget(QLabel("<b>Description (Max 200 words):</b>"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.layout.addWidget(self.desc_input)
        
        self.layout.addWidget(QLabel("<b>Tech Stack:</b>"))
        self.tech_input = QLineEdit()
        self.tech_input.setPlaceholderText("e.g. Python, React, PySide6")
        self.layout.addWidget(self.tech_input)
        
        self.layout.addWidget(QLabel("<b>Features:</b>"))
        self.features_input = QTextEdit()
        self.features_input.setMaximumHeight(100)
        self.layout.addWidget(self.features_input)
        
        self.layout.addWidget(QLabel("<b>Live App Link:</b>"))
        self.link_input = QLineEdit()
        self.layout.addWidget(self.link_input)
        
        self.layout.addWidget(QLabel("<b>README File:</b>"))
        self.readme_input = ReadmeDropArea()
        self.layout.addWidget(self.readme_input)
        
        # Integrations
        self.layout.addWidget(QLabel("<b>Integrations:</b>"))
        
        self.github_cb = QCheckBox("I have added this to GitHub")
        self.layout.addWidget(self.github_cb)
        
        self.linkedin_cb = QCheckBox("I have added this to LinkedIn")
        self.linkedin_cb.toggled.connect(self.toggle_linkedin_post)
        self.layout.addWidget(self.linkedin_cb)
        
        self.linkedin_post_label = QLabel("<b>LinkedIn Post Content:</b>")
        self.linkedin_post_input = QTextEdit()
        self.linkedin_post_input.setMaximumHeight(100)
        self.linkedin_post_label.hide()
        self.linkedin_post_input.hide()
        
        self.layout.addWidget(self.linkedin_post_label)
        self.layout.addWidget(self.linkedin_post_input)
        
        self.layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancelled.emit)
        
        save_btn = QPushButton("Save Project")
        save_btn.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 10px 20px;")
        save_btn.clicked.connect(self.save_project)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def toggle_linkedin_post(self, checked):
        self.linkedin_post_label.setVisible(checked)
        self.linkedin_post_input.setVisible(checked)
        
    def save_project(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return
            
        desc = self.desc_input.toPlainText().strip()
        tech = self.tech_input.text().strip()
        features = self.features_input.toPlainText().strip()
        link = self.link_input.text().strip()
        readme = self.readme_input.toPlainText().strip()
        github_added = self.github_cb.isChecked()
        linkedin_added = self.linkedin_cb.isChecked()
        linkedin_post = self.linkedin_post_input.toPlainText().strip() if linkedin_added else ""
        
        from database.repository import ProjectRepository, ProfileRepository
        proj_repo = ProjectRepository(self.db)
        prof_repo = ProfileRepository(self.db)
        
        # Save project
        pid = proj_repo.create_project(name, desc, tech, "Planning", features, link, github_added, linkedin_added, linkedin_post)
        
        # Save README if provided
        if readme:
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
            if linkedin_post:
                prof_repo.add_linkedin_post(linkedin_post, f"Media related to project: {name}")
                
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

