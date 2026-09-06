from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt, Signal
from app.ui.components.sidebar import Sidebar
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.projects import ProjectsPage
from app.ui.pages.profile import ProfilePage
from app.ui.pages.content import ContentPage
from app.ui.pages.memory import MemoryPage
from app.ui.pages.chat import AIChatPage
from app.ui.pages.providers import AIProvidersPage
from app.ui.pages.settings import SettingsPage
from app.ui.pages.linkedin import LinkedInPage
from app.ui.pages.github import GitHubPage

class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, config, db_manager):
        super().__init__()
        self.config = config
        self.db_manager = db_manager
        self.setWindowTitle(f"{config.get('app_name', 'Forge Hub')} v{config.get('version', '0.1.0')}")
        self.resize(1100, 750)
        
        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)
        
        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        self.setup_pages()
        
        # Connect sidebar navigation
        self.sidebar.page_selected.connect(self.stacked_widget.setCurrentIndex)
        
        # Initialize Status Bar
        self.status_bar = self.statusBar()
        self.status_label = ClickableLabel("AI Status: Ready")
        self.status_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_label.clicked.connect(lambda: self.sidebar.page_selected.emit(6)) # Navigate to AI Providers
        self.status_bar.addWidget(self.status_label)
        
        # Connect AI providers page to status updates
        self.providers_page.status_updated.connect(self.status_label.setText)

    def setup_pages(self):
        self.stacked_widget.addWidget(DashboardPage(self.db_manager))
        self.stacked_widget.addWidget(ProjectsPage(self.db_manager))
        self.stacked_widget.addWidget(ProfilePage(self.db_manager))
        self.stacked_widget.addWidget(ContentPage(self.db_manager))
        self.stacked_widget.addWidget(MemoryPage(self.db_manager))
        self.stacked_widget.addWidget(AIChatPage(self.db_manager))
        
        self.providers_page = AIProvidersPage(self.db_manager)
        self.stacked_widget.addWidget(self.providers_page)
        
        self.stacked_widget.addWidget(SettingsPage(self.db_manager))
        self.stacked_widget.addWidget(LinkedInPage(self.db_manager))
        self.stacked_widget.addWidget(GitHubPage(self.db_manager))

        # Keyboard shortcuts
        from PySide6.QtGui import QShortcut, QKeySequence
        self.new_project_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_project_shortcut.activated.connect(self.create_new_project)

    def create_new_project(self):
        # Switch to projects page
        self.sidebar.page_selected.emit(1)
        # Assuming index 1 is ProjectsPage
        projects_page = self.stacked_widget.widget(1)
        # Switch to list view if not already there
        projects_page.show_list()
        # Trigger create project
        projects_page.list_widget.create_project()
