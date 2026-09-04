from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QLineEdit, 
                                 QScrollArea, QFrame, QStackedWidget)
from PySide6.QtCore import Qt
from database.repository import ProjectRepository
from app.ui.components.project_dialog import ProjectDialog
from app.ui.pages.project_detail import ProjectDetailWidget

class ProjectCard(QFrame):
    def __init__(self, project_data, open_callback):
        super().__init__()
        self.project_data = project_data
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(self)
        
        title = QLabel(project_data["name"])
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = project_data.get("description") or ""
        if len(desc) > 50: desc = desc[:47] + "..."
        layout.addWidget(QLabel(desc))
        
        layout.addWidget(QLabel(f"Stack: {project_data.get('technology_stack') or 'N/A'}"))
        layout.addWidget(QLabel(f"Status: {project_data.get('status') or 'Planning'}"))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(lambda: open_callback(self.project_data["id"]))
        btn_layout.addWidget(open_btn)
        layout.addLayout(btn_layout)


class ProjectListWidget(QWidget):
    def __init__(self, db_manager, open_project_callback):
        super().__init__()
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.open_project_callback = open_project_callback
        
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects...")
        self.search_input.textChanged.connect(self.load_projects)
        
        self.new_btn = QPushButton("+ New Project")
        self.new_btn.clicked.connect(self.create_project)
        
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.new_btn)
        self.layout.addLayout(header_layout)
        
        # Scroll area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.cards_container)
        self.layout.addWidget(self.scroll)
        
        self.load_projects()

    def load_projects(self):
        query = self.search_input.text().strip()
        
        # Clear existing
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        projects = self.repo.get_projects(query)
        if not projects:
            self.cards_layout.addWidget(QLabel("No projects found."))
        else:
            for p in projects:
                card = ProjectCard(p, self.open_project_callback)
                self.cards_layout.addWidget(card)

    def create_project(self):
        dialog = ProjectDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.repo.create_project(data["name"], data["description"], data["tech_stack"], data["status"])
            self.load_projects()


class ProjectsPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        self.list_widget = ProjectListWidget(self.db_manager, self.open_project)
        self.detail_widget = ProjectDetailWidget(self.db_manager)
        
        self.stacked_widget.addWidget(self.list_widget)
        self.stacked_widget.addWidget(self.detail_widget)
        
        self.detail_widget.back_requested.connect(self.show_list)

    def open_project(self, project_id):
        self.detail_widget.load_project(project_id)
        self.stacked_widget.setCurrentIndex(1)
        
    def show_list(self):
        self.list_widget.load_projects()
        self.stacked_widget.setCurrentIndex(0)
