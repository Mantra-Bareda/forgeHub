from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
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
        
        project_count = 0
        skill_count = 0
        achievement_count = 0
        
        if self.db:
            try:
                proj_repo = ProjectRepository(self.db)
                projects = proj_repo.get_projects()
                project_count = len(projects)
                
                prof_repo = ProfileRepository(self.db)
                skills = prof_repo.get_skills()
                skill_count = len(skills)
                achievements = prof_repo.get_achievements()
                achievement_count = len(achievements)
            except Exception:
                pass
        
        stats_layout.addWidget(StatCard("Total Projects", project_count))
        stats_layout.addWidget(StatCard("Skills Tracked", skill_count))
        stats_layout.addWidget(StatCard("Achievements", achievement_count))
        layout.addLayout(stats_layout)
        
        # Quick info
        info = QLabel("Navigate using the sidebar to manage your projects, professional profile, AI providers, and more.")
        info.setWordWrap(True)
        info.setStyleSheet("margin-top: 20px; font-size: 13px;")
        layout.addWidget(info)
        
        layout.addStretch()
