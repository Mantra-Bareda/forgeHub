from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QTextEdit, 
                                 QScrollArea, QFrame, QListWidget, QListWidgetItem,
                                 QLineEdit, QComboBox, QMessageBox, QMenu)
from PySide6.QtCore import Qt
from database.repository import ProfileRepository, CertificateRepository, HackathonRepository, PostRepository
from app.ui.components.achievement_dialog import AchievementDialog

class ProfilePage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProfileRepository(self.db)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Professional Profile")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(20)
        
        # 1. Project Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.stats_label)
        
        # 2. About & Goals
        self.layout.addWidget(QLabel("<b>About Me:</b>"))
        self.about_input = QTextEdit()
        self.about_input.setMaximumHeight(80)
        self.layout.addWidget(self.about_input)
        
        self.layout.addWidget(QLabel("<b>Professional Goals:</b>"))
        self.goals_input = QTextEdit()
        self.goals_input.setMaximumHeight(80)
        self.layout.addWidget(self.goals_input)
        
        # 3. Skills
        self.layout.addWidget(QLabel("<b>Skills:</b>"))
        skills_layout = QHBoxLayout()
        self.new_skill_input = QLineEdit()
        self.new_skill_input.setPlaceholderText("New skill (e.g. Python)")
        self.skill_level_combo = QComboBox()
        self.skill_level_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        add_skill_btn = QPushButton("Add Skill")
        add_skill_btn.clicked.connect(self.add_skill)
        
        skills_layout.addWidget(self.new_skill_input)
        skills_layout.addWidget(self.skill_level_combo)
        skills_layout.addWidget(add_skill_btn)
        self.layout.addLayout(skills_layout)
        
        self.skills_list = QListWidget()
        self.skills_list.setMaximumHeight(100)
        self.skills_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.skills_list.customContextMenuRequested.connect(self.skill_context_menu)
        self.layout.addWidget(self.skills_list)
        
        # 4. Achievements
        achievements_header = QHBoxLayout()
        achievements_header.addWidget(QLabel("<b>Achievements, Certificates & Hackathons:</b>"))
        add_ach_btn = QPushButton("+ Add Achievement")
        add_ach_btn.clicked.connect(self.add_achievement)
        achievements_header.addStretch()
        achievements_header.addWidget(add_ach_btn)
        self.layout.addLayout(achievements_header)
        
        self.achievements_list = QListWidget()
        self.achievements_list.setMaximumHeight(100)
        self.achievements_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.achievements_list.customContextMenuRequested.connect(self.achievement_context_menu)
        self.layout.addWidget(self.achievements_list)
        
        # 4.1 Certificates
        self.layout.addWidget(QLabel("<b>Certificates:</b>"))
        self.cert_list = QListWidget()
        self.cert_list.setMaximumHeight(100)
        self.layout.addWidget(self.cert_list)
        
        # 4.2 Hackathons
        self.layout.addWidget(QLabel("<b>Hackathons:</b>"))
        self.hackathon_list = QListWidget()
        self.hackathon_list.setMaximumHeight(100)
        self.layout.addWidget(self.hackathon_list)
        
        # 4.3 Posting History
        self.layout.addWidget(QLabel("<b>Posting History:</b>"))
        self.post_list = QListWidget()
        self.post_list.setMaximumHeight(100)
        self.layout.addWidget(self.post_list)
        
        # 5. Professional Preferences
        self.layout.addWidget(QLabel("<b>LinkedIn Preferences (Style, formats, tags):</b>"))
        self.linkedin_input = QTextEdit()
        self.linkedin_input.setMaximumHeight(60)
        self.layout.addWidget(self.linkedin_input)
        
        self.layout.addWidget(QLabel("<b>GitHub Preferences (README styles, descriptions):</b>"))
        self.github_input = QTextEdit()
        self.github_input.setMaximumHeight(60)
        self.layout.addWidget(self.github_input)
        
        self.layout.addWidget(QLabel("<b>Content Preferences (Tone, style, formats):</b>"))
        self.content_input = QTextEdit()
        self.content_input.setMaximumHeight(60)
        self.layout.addWidget(self.content_input)
        
        self.layout.addWidget(QLabel("<b>Content to Avoid (e.g. Generic motivation):</b>"))
        self.avoid_input = QTextEdit()
        self.avoid_input.setMaximumHeight(60)
        self.layout.addWidget(self.avoid_input)
        
        self.layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Bottom Save Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        save_btn = QPushButton("Save Profile")
        save_btn.setMinimumWidth(150)
        save_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        save_btn.clicked.connect(self.save_profile)
        bottom_bar.addWidget(save_btn)
        
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_bar)
        main_layout.addWidget(bottom_container)
        
        self.load_data()

    def load_data(self):
        # Load profile text fields
        profile = self.repo.get_profile()
        self.about_input.setText(profile.get("about") or "")
        self.goals_input.setText(profile.get("professional_goals") or "")
        self.linkedin_input.setText(profile.get("linkedin_preferences") or "")
        self.github_input.setText(profile.get("github_preferences") or "")
        self.content_input.setText(profile.get("content_preferences") or "")
        self.avoid_input.setText(profile.get("things_to_avoid") or "")
        
        # Load stats
        stats = self.repo.get_project_stats()
        stats_text = " | ".join([f"{k}: {v}" for k, v in stats.items()])
        if not stats_text: stats_text = "No projects yet."
        self.stats_label.setText(f"Project Overview: {stats_text}")
        
        self.load_skills()
        self.load_achievements()
        self.load_certificates()
        self.load_hackathons()
        self.load_posts()

    def load_certificates(self):
        self.cert_list.clear()
        repo = CertificateRepository(self.db)
        for cert in repo.get_certificates():
            self.cert_list.addItem(f"{cert['title']} - {cert['issuer']} ({cert.get('issue_date','')})")

    def load_hackathons(self):
        self.hackathon_list.clear()
        repo = HackathonRepository(self.db)
        for hack in repo.get_hackathons():
            self.hackathon_list.addItem(f"{hack['event_name']} ({hack.get('date','')}) - {hack.get('standing','')}")

    def load_posts(self):
        self.post_list.clear()
        repo = PostRepository(self.db)
        for post in repo.get_posts():
            content = str(post.get('content', ''))
            self.post_list.addItem(f"[{post.get('posted_at','')}] {post.get('platform','')}: {content[:50]}...")

    def load_skills(self):
        self.skills_list.clear()
        for skill in self.repo.get_skills():
            item = QListWidgetItem(f"{skill['name']} ({skill['level']})")
            item.setData(Qt.ItemDataRole.UserRole, skill["id"])
            self.skills_list.addItem(item)
            
    def add_skill(self):
        name = self.new_skill_input.text().strip()
        if name:
            level = self.skill_level_combo.currentText()
            self.repo.add_skill(name, level)
            self.new_skill_input.clear()
            self.load_skills()
            
    def skill_context_menu(self, position):
        item = self.skills_list.itemAt(position)
        if not item: return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Skill")
        action = menu.exec(self.skills_list.mapToGlobal(position))
        
        if action == delete_action:
            self.repo.delete_skill(item.data(Qt.ItemDataRole.UserRole))
            self.load_skills()

    def load_achievements(self):
        self.achievements_list.clear()
        for ach in self.repo.get_achievements():
            item = QListWidgetItem(f"[{ach['date_achieved']}] {ach['type']}: {ach['title']}")
            item.setData(Qt.ItemDataRole.UserRole, ach["id"])
            self.achievements_list.addItem(item)
            
    def add_achievement(self):
        dialog = AchievementDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.repo.add_achievement(data["title"], data["description"], data["date"], data["type"])
            self.load_achievements()

    def achievement_context_menu(self, position):
        item = self.achievements_list.itemAt(position)
        if not item: return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Achievement")
        action = menu.exec(self.achievements_list.mapToGlobal(position))
        
        if action == delete_action:
            self.repo.delete_achievement(item.data(Qt.ItemDataRole.UserRole))
            self.load_achievements()

    def save_profile(self):
        data = {
            "about": self.about_input.toPlainText().strip(),
            "professional_goals": self.goals_input.toPlainText().strip(),
            "linkedin_preferences": self.linkedin_input.toPlainText().strip(),
            "github_preferences": self.github_input.toPlainText().strip(),
            "content_preferences": self.content_input.toPlainText().strip(),
            "things_to_avoid": self.avoid_input.toPlainText().strip()
        }
        self.repo.update_profile(data)
        QMessageBox.information(self, "Success", "Professional profile saved.")
