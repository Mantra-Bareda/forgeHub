from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QLineEdit, QScrollArea
from PySide6.QtCore import Qt
from database.repository import ProfileRepository

class GitHubPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.repo = ProfileRepository(db_manager)
        
        main_layout = QVBoxLayout(self)
        
        header = QLabel("GitHub Integration")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        
        # Username
        self.layout.addWidget(QLabel("<b>GitHub Username:</b>"))
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_input)
        
        # Special Profile README
        self.layout.addWidget(QLabel("<b>Profile README (Content from your special name repo):</b>"))
        self.profile_readme_input = QTextEdit()
        self.profile_readme_input.setMaximumHeight(200)
        self.profile_readme_input.setPlaceholderText("Paste your main GitHub profile markdown here...")
        self.layout.addWidget(self.profile_readme_input)
        
        # Projects Summary
        self.layout.addWidget(QLabel("<b>Projects Listed (Include README details, if source code is posted, etc.):</b>"))
        self.projects_input = QTextEdit()
        self.projects_input.setPlaceholderText("- Project A (Source open): [Readme details...]\n- Project B (Closed source): [Readme details...]")
        self.layout.addWidget(self.projects_input)
        
        self.layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        save_btn = QPushButton("Save GitHub Profile")
        save_btn.setStyleSheet("font-weight: bold; padding: 10px; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_preferences)
        main_layout.addWidget(save_btn)
        
        self.load_data()

    def load_data(self):
        data = self.repo.get_github_data()
        self.username_input.setText(data.get("username") or "")
        self.profile_readme_input.setText(data.get("profile_readme") or "")
        self.projects_input.setText(data.get("projects_summary") or "")
        
    def save_preferences(self):
        data = {
            "username": self.username_input.text().strip(),
            "profile_readme": self.profile_readme_input.toPlainText().strip(),
            "projects_summary": self.projects_input.toPlainText().strip()
        }
        self.repo.update_github_data(data)
        QMessageBox.information(self, "Success", "GitHub profile data saved.")
