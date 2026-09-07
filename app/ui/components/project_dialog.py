from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor


class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Project" if project_data else "New Project")
        self.setMinimumWidth(460)
        self.project_data = project_data

        self.setStyleSheet("""
            QDialog {
                background-color: #101623;
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
                padding: 6px 10px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #2196f3;
            }
            QComboBox {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                padding: 6px 10px;
            }
            QComboBox:focus {
                border-color: #2196f3;
            }
            QComboBox QAbstractItemView {
                background-color: #191b22;
                color: #f1f5f9;
                selection-background-color: #2196f3;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header Title
        dlg_title = QLabel("Edit Project Details" if project_data else "Create New Project")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f1f5f9; margin-bottom: 4px;")
        layout.addWidget(dlg_title)

        # Name
        layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(34)
        self.name_input.setPlaceholderText("e.g. Forge Hub")
        layout.addWidget(self.name_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(90)
        self.desc_input.setPlaceholderText("Brief description of the project...")
        layout.addWidget(self.desc_input)

        # Technology Stack
        layout.addWidget(QLabel("Technology Stack (comma separated):"))
        self.tech_input = QLineEdit()
        self.tech_input.setFixedHeight(34)
        self.tech_input.setPlaceholderText("e.g. Python, PySide6, SQLite")
        layout.addWidget(self.tech_input)

        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(34)
        self.status_combo.addItems(["Planning", "In Progress", "Completed", "Archived"])
        layout.addWidget(self.status_combo)

        # Pre-fill if editing
        if self.project_data:
            self.name_input.setText(self.project_data.get("name") or "")
            self.desc_input.setText(self.project_data.get("description") or "")
            self.tech_input.setText(self.project_data.get("technology_stack") or "")
            status = self.project_data.get("status") or "Planning"
            idx = self.status_combo.findText(status)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(10)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 500;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #283548;
                color: #ffffff;
            }
        """)

        self.save_btn = QPushButton("Save Changes" if project_data else "Create Project")
        self.save_btn.setFixedHeight(34)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0 18px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "tech_stack": self.tech_input.text().strip(),
            "status": self.status_combo.currentText()
        }
