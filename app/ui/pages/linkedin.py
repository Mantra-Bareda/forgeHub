from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QLineEdit, QScrollArea, QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Qt
from database.repository import ProfileRepository

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

class LinkedInPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.repo = ProfileRepository(db_manager)
        
        main_layout = QVBoxLayout(self)
        
        header = QLabel("LinkedIn Integration")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
        from PySide6.QtWidgets import QSplitter
        from app.ui.pages.chat import AIChatPage
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, stretch=1)
        
        # Left side: Form
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 10, 0)
        
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
        self.layout.addWidget(QLabel("<b>Certificates Uploaded to LinkedIn:</b>"))
        self.certs_input = QTextEdit()
        self.certs_input.setMaximumHeight(80)
        self.layout.addWidget(self.certs_input)
        
        # Projects
        self.layout.addWidget(QLabel("<b>Projects Listed on LinkedIn:</b>"))
        self.projects_input = QTextEdit()
        self.projects_input.setMaximumHeight(100)
        self.layout.addWidget(self.projects_input)
        
        # Languages & Skills
        self.layout.addWidget(QLabel("<b>Spoken Languages:</b>"))
        self.languages_input = QLineEdit()
        self.layout.addWidget(self.languages_input)
        
        self.layout.addWidget(QLabel("<b>Skills (As listed on LinkedIn):</b>"))
        self.skills_input = QTextEdit()
        self.skills_input.setMaximumHeight(80)
        self.layout.addWidget(self.skills_input)
        
        self.layout.addStretch()
        scroll.setWidget(content_widget)
        form_layout.addWidget(scroll)
        
        save_btn = QPushButton("Save LinkedIn Profile")
        save_btn.setStyleSheet("font-weight: bold; padding: 10px; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_preferences)
        form_layout.addWidget(save_btn)
        
        splitter.addWidget(form_container)
        
        # Right side: AI Chat
        self.chat_page = AIChatPage(db_manager, chat_context="linkedin")
        splitter.addWidget(self.chat_page)
        
        # Give chat more space by default
        splitter.setSizes([400, 600])
        
        self.load_data()

    def load_data(self):
        data = self.repo.get_linkedin_data()
        self.username_input.setText(data.get("username") or "")
        self.bio_input.setText(data.get("bio") or "")
        self.about_input.setText(data.get("about") or "")
        self.certs_input.setText(data.get("certificates") or "")
        self.projects_input.setText(data.get("projects") or "")
        self.languages_input.setText(data.get("languages") or "")
        self.skills_input.setText(data.get("skills") or "")
        self.load_posts()
        
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
        from PySide6.QtWidgets import QMenu
        item = self.post_list.itemAt(position)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("Delete Post")
        action = menu.exec(self.post_list.mapToGlobal(position))
        if action == delete_action:
            self.repo.delete_linkedin_post(item.data(Qt.ItemDataRole.UserRole))
            self.load_posts()

    def save_preferences(self):
        data = {
            "username": self.username_input.text().strip(),
            "bio": self.bio_input.text().strip(),
            "about": self.about_input.toPlainText().strip(),
            "certificates": self.certs_input.toPlainText().strip(),
            "projects": self.projects_input.toPlainText().strip(),
            "languages": self.languages_input.text().strip(),
            "skills": self.skills_input.toPlainText().strip()
        }
        self.repo.update_linkedin_data(data)
        QMessageBox.information(self, "Success", "LinkedIn profile data saved.")
