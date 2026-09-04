from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QTextEdit, QComboBox, 
                                 QPushButton, QMessageBox)

class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_data=None):
        super().__init__(parent)
        self.setWindowTitle("New Project" if not project_data else "Edit Project")
        self.setMinimumWidth(400)
        self.project_data = project_data
        
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)
        
        # Technology Stack
        layout.addWidget(QLabel("Technology Stack (comma separated):"))
        self.tech_input = QLineEdit()
        layout.addWidget(self.tech_input)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Planning", "In Progress", "Completed", "Archived"])
        layout.addWidget(self.status_combo)
        
        # Pre-fill if editing
        if self.project_data:
            self.name_input.setText(self.project_data.get("name", ""))
            self.desc_input.setText(self.project_data.get("description") or "")
            self.tech_input.setText(self.project_data.get("technology_stack") or "")
            status = self.project_data.get("status") or "Planning"
            idx = self.status_combo.findText(status)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
                
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
