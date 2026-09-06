from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from database.repository import ProfileRepository

class LinkedInPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.repo = ProfileRepository(db_manager)
        layout = QVBoxLayout(self)
        
        header = QLabel("LinkedIn Integration")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        layout.addWidget(QLabel("<b>LinkedIn Preferences (Style, formats, tags):</b>"))
        self.linkedin_input = QTextEdit()
        self.linkedin_input.setPlaceholderText("e.g., Use professional tone, avoid emojis, always add #softwareengineering")
        layout.addWidget(self.linkedin_input)
        
        save_btn = QPushButton("Save Preferences")
        save_btn.setStyleSheet("font-weight: bold; padding: 8px; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_preferences)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        self.load_data()

    def load_data(self):
        profile = self.repo.get_profile()
        self.linkedin_input.setText(profile.get("linkedin_preferences") or "")
        
    def save_preferences(self):
        data = {
            "linkedin_preferences": self.linkedin_input.toPlainText().strip()
        }
        self.repo.update_profile(data)
        QMessageBox.information(self, "Success", "LinkedIn preferences saved.")
