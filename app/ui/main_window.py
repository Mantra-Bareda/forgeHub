from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from app.ui.components.sidebar import Sidebar
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.projects import ProjectsPage
from app.ui.pages.profile import ProfilePage
from app.ui.pages.content import ContentPage
from app.ui.pages.memory import MemoryPage
from app.ui.pages.chat import AIChatPage
from app.ui.pages.providers import AIProvidersPage
from app.ui.pages.settings import SettingsPage

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
        self.status_bar.showMessage("AI Status: Ready")

    def setup_pages(self):
        self.stacked_widget.addWidget(DashboardPage())
        self.stacked_widget.addWidget(ProjectsPage(self.db_manager))
        self.stacked_widget.addWidget(ProfilePage(self.db_manager))
        self.stacked_widget.addWidget(ContentPage())
        self.stacked_widget.addWidget(MemoryPage())
        self.stacked_widget.addWidget(AIChatPage())
        self.stacked_widget.addWidget(AIProvidersPage(self.db_manager))
        self.stacked_widget.addWidget(SettingsPage())
