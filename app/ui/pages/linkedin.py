from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QLineEdit, QScrollArea
from PySide6.QtCore import Qt
from database.repository import ProfileRepository

class LinkedInPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.repo = ProfileRepository(db_manager)
        
        main_layout = QVBoxLayout(self)
        
        header = QLabel("LinkedIn Integration")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
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
        self.layout.addWidget(QLabel("<b>Recent Posts / Activity Summary:</b>"))
        self.posts_input = QTextEdit()
        self.posts_input.setMaximumHeight(100)
        self.posts_input.setPlaceholderText("List your LinkedIn specific posts here...")
        self.layout.addWidget(self.posts_input)
        
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
        main_layout.addWidget(scroll)
        
        save_btn = QPushButton("Save LinkedIn Profile")
        save_btn.setStyleSheet("font-weight: bold; padding: 10px; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_preferences)
        main_layout.addWidget(save_btn)
        
        self.load_data()

    def load_data(self):
        data = self.repo.get_linkedin_data()
        self.username_input.setText(data.get("username") or "")
        self.bio_input.setText(data.get("bio") or "")
        self.about_input.setText(data.get("about") or "")
        self.posts_input.setText(data.get("posts") or "")
        self.certs_input.setText(data.get("certificates") or "")
        self.projects_input.setText(data.get("projects") or "")
        self.languages_input.setText(data.get("languages") or "")
        self.skills_input.setText(data.get("skills") or "")
        
    def save_preferences(self):
        data = {
            "username": self.username_input.text().strip(),
            "bio": self.bio_input.text().strip(),
            "about": self.about_input.toPlainText().strip(),
            "posts": self.posts_input.toPlainText().strip(),
            "certificates": self.certs_input.toPlainText().strip(),
            "projects": self.projects_input.toPlainText().strip(),
            "languages": self.languages_input.text().strip(),
            "skills": self.skills_input.toPlainText().strip()
        }
        self.repo.update_linkedin_data(data)
        QMessageBox.information(self, "Success", "LinkedIn profile data saved.")
