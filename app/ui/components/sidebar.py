from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QButtonGroup
from PySide6.QtCore import Signal, Qt

class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons = []
        
        # Primary Navigation
        self.add_button("Dashboard", 0)
        self.add_button("Projects", 1)
        self.add_button("Profile", 2)
        self.add_button("Content", 3)
        self.add_button("Memory", 4)
        self.add_button("AI Chat", 5)
        self.add_button("LinkedIn", 8)
        self.add_button("GitHub", 9)
        
        # Spacer to push settings/providers to the bottom
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Secondary Navigation
        self.add_button("AI Providers", 6)
        self.add_button("Settings", 7)
        
        if self.buttons:
            self.buttons[0].setChecked(True)

    def add_button(self, text, index):
        btn = QPushButton(text)
        btn.setCheckable(True)
        # Using a fixed height for a better professional look
        btn.setFixedHeight(35)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.clicked.connect(lambda _, idx=index: self.page_selected.emit(idx))
        self.layout.addWidget(btn)
        self.button_group.addButton(btn, index)
        self.buttons.append(btn)
