from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt

class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        self.buttons = []
        
        # Primary Navigation
        self.add_button("Dashboard", 0)
        self.add_button("Projects", 1)
        self.add_button("Profile", 2)
        self.add_button("Content", 3)
        self.add_button("Memory", 4)
        self.add_button("AI Chat", 5)
        
        # Spacer to push settings/providers to the bottom
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Secondary Navigation
        self.add_button("AI Providers", 6)
        self.add_button("Settings", 7)

    def add_button(self, text, index):
        btn = QPushButton(text)
        # Using a fixed height for a better professional look
        btn.setFixedHeight(35)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.clicked.connect(lambda _, idx=index: self.page_selected.emit(idx))
        self.layout.addWidget(btn)
        self.buttons.append(btn)
