from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QTextEdit, 
                                 QPushButton, QMessageBox, QDateEdit)
from PySide6.QtCore import QDate

class CertificateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Certificate")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Issuer:"))
        self.issuer_input = QLineEdit()
        layout.addWidget(self.issuer_input)
        
        layout.addWidget(QLabel("Issue Date:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)
        
        layout.addWidget(QLabel("Credential URL (Optional):"))
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Error", "Title is required.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "issuer": self.issuer_input.text().strip(),
            "date": self.date_input.date().toString("yyyy-MM-dd"),
            "url": self.url_input.text().strip()
        }

class HackathonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Hackathon")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Event Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("Project Submitted:"))
        self.project_input = QLineEdit()
        layout.addWidget(self.project_input)
        
        layout.addWidget(QLabel("Standing / Award:"))
        self.standing_input = QLineEdit()
        layout.addWidget(self.standing_input)
        
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Event Name is required.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "event_name": self.name_input.text().strip(),
            "project": self.project_input.text().strip(),
            "standing": self.standing_input.text().strip(),
            "date": self.date_input.date().toString("yyyy-MM-dd")
        }

class PostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Post History")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Platform (e.g. LinkedIn, Twitter):"))
        self.platform_input = QLineEdit()
        layout.addWidget(self.platform_input)
        
        layout.addWidget(QLabel("Content Summary / Text:"))
        self.content_input = QTextEdit()
        layout.addWidget(self.content_input)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.platform_input.text().strip() or not self.content_input.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Platform and Content are required.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "platform": self.platform_input.text().strip(),
            "content": self.content_input.toPlainText().strip()
        }
