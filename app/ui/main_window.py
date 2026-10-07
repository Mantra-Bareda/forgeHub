import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QGuiApplication
from app.core.palette import ColorPalette, get_current_palette
from app.core.theme import theme_manager
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

class AdaptiveStackedWidget(QStackedWidget):
    """StackedWidget that reports adaptive minimum sizes based on the active page."""
    def minimumSizeHint(self):
        cur = self.currentWidget()
        if cur:
            h = cur.minimumSizeHint()
            return QSize(min(h.width(), 350), min(h.height(), 250))
        return QSize(300, 200)

    def sizeHint(self):
        cur = self.currentWidget()
        if cur:
            return cur.sizeHint()
        return super().sizeHint()

class MainWindow(QMainWindow):
    def __init__(self, config, db_manager):
        super().__init__()
        self.config = config
        self.db_manager = db_manager
        self.setWindowTitle("ForgeHub")
        icon_path = os.path.abspath("forge_hub_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        
        # Allow shrinking down to compact laptops/screens
        self.setMinimumSize(720, 480)

        # Screen-aware initial geometry
        screen = QGuiApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            target_w = min(1180, max(750, int(avail.width() * 0.88)))
            target_h = min(780, max(480, int(avail.height() * 0.88)))
            self.resize(target_w, target_h)
            x = avail.x() + max(0, (avail.width() - target_w) // 2)
            y = avail.y() + max(0, (avail.height() - target_h) // 2)
            self.move(x, y)
        else:
            self.resize(1100, 720)

        
        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)
        
        # Stacked Widget for pages
        self.stacked_widget = AdaptiveStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        self.setup_pages()
        
        # Connect sidebar navigation
        self.sidebar.page_selected.connect(self.on_page_selected)
        
        # Initialize Status Bar
        self.status_bar = self.statusBar()
        self.status_label = ClickableLabel("AI Status: Ready")
        self.status_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_label.clicked.connect(lambda: self.on_page_selected(6)) # Navigate to AI Providers
        self.status_bar.addWidget(self.status_label)
        
        # Connect AI providers page to status updates
        self.providers_page.status_updated.connect(self.status_label.setText)

        # Apply initial color palette & connect live theme dispatcher
        self.apply_theme_colors(get_current_palette())
        theme_manager.theme_changed.connect(lambda name, pal: self.apply_theme_colors(pal))

    def apply_theme_colors(self, palette: ColorPalette):
        from PySide6.QtGui import QPalette, QColor
        p = self.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(palette.bg_app))
        self.setPalette(p)
        self.central_widget.setPalette(p)
        self.central_widget.setStyleSheet(f"background-color: {palette.bg_app};")
        self.stacked_widget.setStyleSheet(f"background-color: {palette.bg_app};")

        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {palette.bg_app};
                color: {palette.fg_muted};
                border-top: 1px solid {palette.border_subtle};
                border-bottom: none;
                border-left: none;
                border-right: none;
                font-size: 11px;
                padding-left: 12px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)
        if hasattr(self, "status_label"):
            self.status_label.setStyleSheet(f"color: {palette.fg_muted}; font-size: 11px; font-weight: 500;")

        # Dispatch theme colors to the active page immediately
        active_page = self.stacked_widget.currentWidget()
        if hasattr(active_page, "apply_theme_colors"):
            try:
                active_page.apply_theme_colors(palette)
            except Exception:
                pass
        else:
            active_page.setStyleSheet(f"background-color: {palette.bg_app};")
            
        # Store the current palette so pages can update lazily when selected
        self._pending_theme_palette = palette

    def on_page_selected(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.select_page(index)
        
        # Lazy theme update for the selected page
        if hasattr(self, "_pending_theme_palette"):
            page = self.stacked_widget.widget(index)
            # Only update if the page's palette doesn't match the pending one
            if getattr(page, "palette", None) != self._pending_theme_palette:
                if hasattr(page, "apply_theme_colors"):
                    try:
                        page.apply_theme_colors(self._pending_theme_palette)
                    except Exception:
                        pass
                else:
                    page.setStyleSheet(f"background-color: {self._pending_theme_palette.bg_app};")

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
