from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QGridLayout
from PySide6.QtCore import Qt
from database.repository import ProjectRepository, ProfileRepository

class StatCard(QFrame):
    def __init__(self, title, value):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2196F3;")
        layout.addWidget(self.value_label)

class DashboardPage(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        subtitle = QLabel("Welcome to Forge Hub — Your Personal Professional AI Manager")
        subtitle.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(subtitle)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        projects = []
        achievements = []
        
        if self.db:
            try:
                proj_repo = ProjectRepository(self.db)
                projects = proj_repo.get_projects()
                
                prof_repo = ProfileRepository(self.db)
                skills = prof_repo.get_skills()
                achievements = prof_repo.get_achievements()
                
                stats_layout.addWidget(StatCard("Total Projects", len(projects)))
                stats_layout.addWidget(StatCard("Skills Tracked", len(skills)))
                stats_layout.addWidget(StatCard("Achievements", len(achievements)))
            except Exception:
                stats_layout.addWidget(StatCard("Total Projects", 0))
                stats_layout.addWidget(StatCard("Skills Tracked", 0))
                stats_layout.addWidget(StatCard("Achievements", 0))
        
        layout.addLayout(stats_layout)
        
        lists_layout = QHBoxLayout()
        
        # Recent Projects
        recent_proj_layout = QVBoxLayout()
        recent_proj_layout.addWidget(QLabel("<b>Recent Projects</b>"))
        proj_list = QListWidget()
        for p in projects[:5]:
            proj_list.addItem(QListWidgetItem(p.get("name", "Unnamed Project")))
        if not projects:
            proj_list.addItem(QListWidgetItem("No projects found."))
        recent_proj_layout.addWidget(proj_list)
        
        # Recent Achievements
        recent_ach_layout = QVBoxLayout()
        recent_ach_layout.addWidget(QLabel("<b>Recent Achievements</b>"))
        ach_list = QListWidget()
        for a in achievements[:5]:
            ach_list.addItem(QListWidgetItem(f"{a.get('type', 'Achievement')}: {a.get('title', 'Unknown')}"))
        if not achievements:
            ach_list.addItem(QListWidgetItem("No achievements found."))
        recent_ach_layout.addWidget(ach_list)
        
        lists_layout.addLayout(recent_proj_layout)
        lists_layout.addLayout(recent_ach_layout)
        layout.addLayout(lists_layout)
        
        # Quick info
        info = QLabel("Navigate using the sidebar to manage your projects, professional profile, AI providers, and more.")
        info.setWordWrap(True)
        info.setStyleSheet("margin-top: 20px; font-size: 13px;")
        layout.addWidget(info)
        
        layout.addStretch()
