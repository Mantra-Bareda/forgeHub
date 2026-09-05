from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import Qt

class ContentPage(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("Content Generation")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        self.empty_state = QLabel("No content generated yet. Select a type and start creating!")
        self.empty_state.setStyleSheet("color: #888; font-style: italic;")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_state)
        
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Content Type:"))
        self.type_selector = QComboBox()
        self.type_selector.addItems(["GitHub README", "LinkedIn Post", "Blog Post", "Custom"])
        selector_layout.addWidget(self.type_selector)
        
        self.generate_btn = QPushButton("Generate Draft")
        selector_layout.addWidget(self.generate_btn)
        selector_layout.addStretch()
        
        layout.addLayout(selector_layout)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Your content draft will appear here...")
        layout.addWidget(self.editor)
        
        # Action row
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.save_btn = QPushButton("Save Content")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        action_layout.addWidget(self.save_btn)
        layout.addLayout(action_layout)
