from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QTextEdit, QComboBox, 
                                 QPushButton, QMessageBox, QDateEdit)
from PySide6.QtCore import Qt, QDate

class AchievementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Achievement")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        
        # Type
        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Certificate", "Hackathon", "Award", "General"])
        layout.addWidget(self.type_combo)
        
        # Date
        layout.addWidget(QLabel("Date Achieved:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)
        
        # Buttons
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
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "type": self.type_combo.currentText(),
            "date": self.date_input.date().toString("yyyy-MM-dd"),
            "description": self.desc_input.toPlainText().strip()
        }
