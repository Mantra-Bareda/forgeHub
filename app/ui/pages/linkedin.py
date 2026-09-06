from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QLineEdit, QScrollArea, QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QMenu, QStackedWidget
from PySide6.QtCore import Qt
from database.repository import ProfileRepository
from app.ui.components.flow_layout import FlowLayout
from app.ui.pages.chat import AIChatPage

class LinkedInPostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add LinkedIn Post")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Post Content (Text):"))
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(100)
        layout.addWidget(self.content_input)
        
        layout.addWidget(QLabel("Media Description (Describe the image, video, or link attached):"))
        self.media_input = QTextEdit()
        self.media_input.setMinimumHeight(60)
        self.media_input.setPlaceholderText("e.g., A screenshot of my dashboard, or A link to my github repo")
        layout.addWidget(self.media_input)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "content": self.content_input.toPlainText().strip(),
            "media_description": self.media_input.toPlainText().strip()
        }

class LinkedInCertificateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add LinkedIn Certificate")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(60)
        layout.addWidget(self.desc_input)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip()
        }

class LinkedInProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add LinkedIn Project")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(60)
        layout.addWidget(self.desc_input)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip()
        }

class LinkedInPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.repo = ProfileRepository(db_manager)
        
        main_layout = QVBoxLayout(self)
        
        header = QLabel("LinkedIn Integration")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        # --- Form Page ---
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        header_actions = QHBoxLayout()
        header_actions.addStretch()
        open_chat_btn = QPushButton("Open LinkedIn AI Chat")
        open_chat_btn.setStyleSheet("font-weight: bold; padding: 5px 15px; background-color: #2196F3; color: white;")
        open_chat_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        header_actions.addWidget(open_chat_btn)
        form_layout.addLayout(header_actions)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        
        # Username
        self.layout.addWidget(QLabel("<b>LinkedIn Username / URL:</b>"))
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_input)
        
        # Bio / Headline
        self.layout.addWidget(QLabel("<b>Headline / Bio:</b>"))
        self.bio_input = QLineEdit()
        self.layout.addWidget(self.bio_input)
        
        # About Me
        self.layout.addWidget(QLabel("<b>About section (Exactly as written on LinkedIn):</b>"))
        self.about_input = QTextEdit()
        self.about_input.setMaximumHeight(100)
        self.layout.addWidget(self.about_input)
        
        # Posts
        post_header = QHBoxLayout()
        post_header.addWidget(QLabel("<b>LinkedIn Posts (Already published):</b>"))
        add_post_btn = QPushButton("+ Add Post")
        add_post_btn.clicked.connect(self.add_post)
        post_header.addStretch()
        post_header.addWidget(add_post_btn)
        self.layout.addLayout(post_header)
        
        self.post_list = QListWidget()
        self.post_list.setMaximumHeight(150)
        self.post_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.post_list.customContextMenuRequested.connect(self.post_context_menu)
        self.layout.addWidget(self.post_list)
        
        # Certificates
        cert_header = QHBoxLayout()
        cert_header.addWidget(QLabel("<b>Certificates Uploaded to LinkedIn:</b>"))
        add_cert_btn = QPushButton("+ Add Certificate")
        add_cert_btn.clicked.connect(self.add_certificate)
        cert_header.addStretch()
        cert_header.addWidget(add_cert_btn)
        self.layout.addLayout(cert_header)
        
        self.cert_list = QListWidget()
        self.cert_list.setMaximumHeight(100)
        self.cert_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cert_list.customContextMenuRequested.connect(self.cert_context_menu)
        self.layout.addWidget(self.cert_list)
        
        # Projects
        project_header = QHBoxLayout()
        project_header.addWidget(QLabel("<b>Projects Listed on LinkedIn:</b>"))
        add_project_btn = QPushButton("+ Add Project")
        add_project_btn.clicked.connect(self.add_project)
        project_header.addStretch()
        project_header.addWidget(add_project_btn)
        self.layout.addLayout(project_header)
        
        self.project_list = QListWidget()
        self.project_list.setMaximumHeight(100)
        self.project_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self.project_context_menu)
        self.layout.addWidget(self.project_list)
        
        # Languages
        self.layout.addWidget(QLabel("<b>Spoken Languages:</b>"))
        lang_input_layout = QHBoxLayout()
        self.lang_input = QLineEdit()
        add_lang_btn = QPushButton("Add Language")
        add_lang_btn.clicked.connect(self.add_language)
        lang_input_layout.addWidget(self.lang_input)
        lang_input_layout.addWidget(add_lang_btn)
        self.layout.addLayout(lang_input_layout)
        
        self.lang_flow = QWidget()
        self.lang_flow_layout = FlowLayout(self.lang_flow)
        self.layout.addWidget(self.lang_flow)
        
        # Skills
        self.layout.addWidget(QLabel("<b>Skills (As listed on LinkedIn):</b>"))
        skill_input_layout = QHBoxLayout()
        self.skill_input = QLineEdit()
        add_skill_btn = QPushButton("Add Skill")
        add_skill_btn.clicked.connect(self.add_skill)
        skill_input_layout.addWidget(self.skill_input)
        skill_input_layout.addWidget(add_skill_btn)
        self.layout.addLayout(skill_input_layout)
        
        self.skill_flow = QWidget()
        self.skill_flow_layout = FlowLayout(self.skill_flow)
        self.layout.addWidget(self.skill_flow)
        
        self.layout.addStretch()
        scroll.setWidget(content_widget)
        form_layout.addWidget(scroll)
        
        save_btn = QPushButton("Save LinkedIn Profile")
        save_btn.setStyleSheet("font-weight: bold; padding: 10px; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_preferences)
        form_layout.addWidget(save_btn)
        
        self.stacked_widget.addWidget(form_container)
        
        # --- Chat Page ---
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        back_btn = QPushButton("← Back to Form")
        back_btn.setStyleSheet("font-weight: bold; padding: 5px;")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        chat_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.chat_page = AIChatPage(db_manager, chat_context="linkedin")
        chat_layout.addWidget(self.chat_page, stretch=1)
        
        self.stacked_widget.addWidget(chat_container)
        
        self.load_data()

    def load_data(self):
        data = self.repo.get_linkedin_data()
        self.username_input.setText(data.get("username") or "")
        self.bio_input.setText(data.get("bio") or "")
        self.about_input.setText(data.get("about") or "")
        self.load_posts()
        self.load_certificates()
        self.load_projects()
        self.load_languages()
        self.load_skills()
        
    def load_posts(self):
        self.post_list.clear()
        for post in self.repo.get_linkedin_posts():
            content = str(post.get('content', ''))[:50]
            item = QListWidgetItem(f"[{post.get('created_at', '')[:10]}] {content}...")
            item.setData(Qt.ItemDataRole.UserRole, post["id"])
            self.post_list.addItem(item)
            
    def add_post(self):
        dialog = LinkedInPostDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["content"]:
                self.repo.add_linkedin_post(data["content"], data["media_description"])
                self.load_posts()

    def post_context_menu(self, position):
        item = self.post_list.itemAt(position)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("Delete Post")
        action = menu.exec(self.post_list.mapToGlobal(position))
        if action == delete_action:
            self.repo.delete_linkedin_post(item.data(Qt.ItemDataRole.UserRole))
            self.load_posts()

    def load_certificates(self):
        self.cert_list.clear()
        for cert in self.repo.get_linkedin_certificates():
            item = QListWidgetItem(cert.get('title', ''))
            item.setData(Qt.ItemDataRole.UserRole, cert["id"])
            self.cert_list.addItem(item)

    def add_certificate(self):
        dialog = LinkedInCertificateDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["title"]:
                self.repo.add_linkedin_certificate(data["title"], data["description"])
                self.load_certificates()

    def cert_context_menu(self, position):
        item = self.cert_list.itemAt(position)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("Delete Certificate")
        action = menu.exec(self.cert_list.mapToGlobal(position))
        if action == delete_action:
            self.repo.delete_linkedin_certificate(item.data(Qt.ItemDataRole.UserRole))
            self.load_certificates()

    def load_projects(self):
        self.project_list.clear()
        for proj in self.repo.get_linkedin_projects():
            item = QListWidgetItem(proj.get('title', ''))
            item.setData(Qt.ItemDataRole.UserRole, proj["id"])
            self.project_list.addItem(item)

    def add_project(self):
        dialog = LinkedInProjectDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["title"]:
                self.repo.add_linkedin_project(data["title"], data["description"])
                self.load_projects()

    def project_context_menu(self, position):
        item = self.project_list.itemAt(position)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("Delete Project")
        action = menu.exec(self.project_list.mapToGlobal(position))
        if action == delete_action:
            self.repo.delete_linkedin_project(item.data(Qt.ItemDataRole.UserRole))
            self.load_projects()

    def load_languages(self):
        while self.lang_flow_layout.count():
            item = self.lang_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for lang in self.repo.get_linkedin_languages():
            name = lang["name"]
            tag = self.create_tag_widget(name, lambda n=name: self.delete_language(n))
            self.lang_flow_layout.addWidget(tag)

    def add_language(self):
        text = self.lang_input.text()
        if text:
            for part in text.split(','):
                lang = part.strip()
                if lang:
                    self.repo.add_linkedin_language(lang)
            self.lang_input.clear()
            self.load_languages()

    def delete_language(self, name):
        self.repo.delete_linkedin_language(name)
        self.load_languages()

    def load_skills(self):
        while self.skill_flow_layout.count():
            item = self.skill_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for skill in self.repo.get_linkedin_skills():
            name = skill["name"]
            tag = self.create_tag_widget(name, lambda n=name: self.delete_skill(n))
            self.skill_flow_layout.addWidget(tag)

    def add_skill(self):
        text = self.skill_input.text()
        if text:
            for part in text.split(','):
                s = part.strip()
                if s:
                    self.repo.add_linkedin_skill(s)
            self.skill_input.clear()
            self.load_skills()

    def delete_skill(self, name):
        self.repo.delete_linkedin_skill(name)
        self.load_skills()

    def create_tag_widget(self, text, delete_callback):
        widget = QWidget()
        widget.setStyleSheet("background-color: #E0E0E0; border-radius: 10px; padding: 2px;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        label = QLabel(text)
        layout.addWidget(label)
        
        del_btn = QPushButton("X")
        del_btn.setFixedSize(16, 16)
        del_btn.setStyleSheet("background: transparent; color: #555; font-weight: bold; border: none;")
        del_btn.clicked.connect(delete_callback)
        layout.addWidget(del_btn)
        
        return widget

    def save_preferences(self):
        data = {
            "username": self.username_input.text().strip(),
            "bio": self.bio_input.text().strip(),
            "about": self.about_input.toPlainText().strip()
        }
        self.repo.update_linkedin_data(data)
        QMessageBox.information(self, "Success", "LinkedIn profile data saved.")
