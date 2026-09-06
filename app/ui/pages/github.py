from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class GitHubPage(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        layout = QVBoxLayout(self)
        
        label = QLabel("GitHub Integration - Coming Soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #888; font-weight: bold;")
        
        layout.addWidget(label)
