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
        self.main_layout.setSpacing(0)
        
        # Window styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f17;
            }
            QStatusBar {
                background-color: #0b0f17;
                color: #94a3b8;
                border-top: 1px solid #1e293b;
                border-bottom: none;
                border-left: none;
                border-right: none;
                font-size: 11px;
                padding-left: 12px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)
        
        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #0b0f17;")
        self.main_layout.addWidget(self.stacked_widget)
        
        self.setup_pages()
        
        # Connect sidebar navigation
        self.sidebar.page_selected.connect(self.on_page_selected)
        
        # Initialize Status Bar
        self.status_bar = self.statusBar()
        self.status_label = ClickableLabel("AI Status: Ready")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        self.status_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_label.clicked.connect(lambda: self.on_page_selected(6)) # Navigate to AI Providers
        self.status_bar.addWidget(self.status_label)
        
        # Connect AI providers page to status updates
        self.providers_page.status_updated.connect(self.status_label.setText)

    def on_page_selected(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.select_page(index)

    def setup_pages(self):
        self.dashboard_page = DashboardPage(self.db_manager)
        self.dashboard_page.navigate_requested.connect(self.sidebar.page_selected.emit)
        self.dashboard_page.new_project_requested.connect(self.create_new_project)
        self.dashboard_page.open_project_requested.connect(self.open_project_from_dashboard)
        self.stacked_widget.addWidget(self.dashboard_page)

        self.projects_page = ProjectsPage(self.db_manager)
        self.stacked_widget.addWidget(self.projects_page)
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
        # Switch to list view if not already there
        self.projects_page.show_list()
        # Trigger create project
        self.projects_page.list_widget.create_project()

    def open_project_from_dashboard(self, project_id):
        self.sidebar.page_selected.emit(1)
        self.projects_page.open_project(project_id)
