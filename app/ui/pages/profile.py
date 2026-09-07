from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTextBrowser, QScrollArea, QFrame, QLineEdit, 
    QComboBox, QMessageBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QThreadPool, QRunnable, QObject
from PySide6.QtGui import QCursor

from database.repository import ProfileRepository, CertificateRepository, HackathonRepository, PostRepository
from app.ui.components.achievement_dialog import AchievementDialog
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


class IntelSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class IntelWorker(QRunnable):
    def __init__(self, db, router):
        super().__init__()
        self.db = db
        self.router = router
        self.signals = IntelSignals()

    def run(self):
        try:
            from database.repository import ProfileRepository, ProjectRepository, PostRepository
            prof_repo = ProfileRepository(self.db)
            proj_repo = ProjectRepository(self.db)
            post_repo = PostRepository(self.db)

            profile = prof_repo.get_profile()
            skills = [s['name'] for s in prof_repo.get_skills()]
            projects = proj_repo.get_projects()
            achievements = prof_repo.get_achievements()
            posts = post_repo.get_posts()

            prompt = f"""
            Analyze my professional profile:
            Goals: {profile.get('professional_goals', 'None')}
            Skills: {skills}
            Projects: {[p['name'] + ' (' + p.get('status', 'Planning') + '): ' + (p.get('technology_stack') or 'None') for p in projects]}
            Achievements: {[a['title'] for a in achievements]}
            Recent Posts: {[p['content'][:50] for p in posts]}

            Please provide a detailed, highly structured Markdown analysis of my profile. Use bolding, underlines, and bullet lists.
            DO NOT use any emojis. Keep the tone strictly professional.
            Include the following sections:
            ### Executive Summary
            ### Key Strengths & Strongest Projects
            ### Skill Gaps & Weaknesses
            ### Content & Career Recommendations
            ### Recommended Next Steps
            """

            system_prompt = "You are an expert technical career coach and software architect. Give an actionable, highly structured assessment formatted in Markdown. No emojis."

            res = self.router.route_request(
                prompt=prompt,
                category="Reasoning",
                system_prompt=system_prompt,
                max_tokens=2048
            )
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))


class SkillTagWidget(QFrame):
    deleted = Signal(int)

    def __init__(self, skill_id, name, level):
        super().__init__()
        self.skill_id = skill_id
        self.setObjectName("skillTag")
        self.setStyleSheet("""
            #skillTag {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            #skillTag:hover {
                border-color: #2196f3;
            }
            #skillTag QLabel {
                background: transparent;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 6, 4)
        layout.setSpacing(6)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #f1f5f9;")
        layout.addWidget(name_lbl)

        # Level badge styling
        level_lower = level.lower()
        if "expert" in level_lower:
            lvl_style = "background-color: rgba(16, 185, 129, 0.2); color: #4edea3; border: 1px solid rgba(16, 185, 129, 0.4);"
        elif "advanced" in level_lower:
            lvl_style = "background-color: rgba(33, 150, 243, 0.2); color: #9ecaff; border: 1px solid rgba(33, 150, 243, 0.4);"
        elif "intermediate" in level_lower:
            lvl_style = "background-color: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4);"
        else:
            lvl_style = "background-color: rgba(100, 116, 139, 0.2); color: #cbd5e1; border: 1px solid rgba(100, 116, 139, 0.4);"

        lvl_lbl = QLabel(level)
        lvl_lbl.setStyleSheet(f"""
            {lvl_style}
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 600;
            font-family: monospace;
        """)
        layout.addWidget(lvl_lbl)

        # Remove button
        del_btn = QPushButton("×")
        del_btn.setFixedSize(16, 16)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self.skill_id))
        layout.addWidget(del_btn)


class ProfilePage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProfileRepository(self.db)
        self._initial_profile_data = {}

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f17;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for entire page
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0b0f17;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(28, 20, 28, 24)
        self.content_layout.setSpacing(18)

        # 1. Top Header Banner
        self._setup_top_banner()

        # 2. Main Two-Column Grid
        grid_layout = QHBoxLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(18)

        # Left Column (2/3 width)
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(18)

        self._setup_about_card(left_col)
        self._setup_skills_card(left_col)
        self._setup_content_pref_card(left_col)
        grid_layout.addLayout(left_col, 2)

        # Right Column (1/3 width)
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(18)

        self._setup_milestones_card(right_col)
        self._setup_intelligence_card(right_col)
        grid_layout.addLayout(right_col, 1)

        self.content_layout.addLayout(grid_layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # 3. Bottom Action Dock
        self._setup_bottom_bar(main_layout)

        # Page entrance animation
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(280)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        from app.ai.router import ModelRouter
        self.router = ModelRouter(self.db)

        self.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(0.0)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def _setup_top_banner(self):
        banner = QFrame()
        banner.setObjectName("profileBanner")
        banner.setStyleSheet("""
            #profileBanner {
                background-color: #101623;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 16px 20px;
            }
            #profileBanner QLabel {
                background: transparent;
            }
        """)
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(16)

        # Avatar circle
        self.avatar_circle = QLabel("JD")
        self.avatar_circle.setFixedSize(54, 54)
        self.avatar_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_circle.setStyleSheet("""
            background-color: #1e3a8a;
            border: 2px solid #3b82f6;
            border-radius: 27px;
            color: #ffffff;
            font-size: 20px;
            font-weight: 700;
        """)
        b_layout.addWidget(self.avatar_circle)

        # Name & Subtitle
        user_col = QVBoxLayout()
        user_col.setContentsMargins(0, 0, 0, 0)
        user_col.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        self.user_name_lbl = QLabel("Professional Profile")
        self.user_name_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.3px;")
        name_row.addWidget(self.user_name_lbl)

        role_badge = QLabel("Senior AI Architect & Engineer")
        role_badge.setStyleSheet("""
            background-color: rgba(33, 150, 243, 0.15);
            border: 1px solid rgba(33, 150, 243, 0.3);
            color: #9ecaff;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        name_row.addWidget(role_badge)
        name_row.addStretch()
        user_col.addLayout(name_row)

        self.user_sub_lbl = QLabel("Local Developer Workstation • Configured for Multi-Model Routing")
        self.user_sub_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        user_col.addWidget(self.user_sub_lbl)
        b_layout.addLayout(user_col, 1)

        # Project Overview Stats Pill
        stats_pill = QFrame()
        stats_pill.setStyleSheet("background-color: #191b22; border: 1px solid #1e293b; border-radius: 8px;")
        sp_layout = QHBoxLayout(stats_pill)
        sp_layout.setContentsMargins(14, 8, 14, 8)
        sp_layout.setSpacing(14)

        def make_stat_col(label, color):
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(1)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label.upper())
            lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748b;")
            val = QLabel("0")
            val.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(val)
            return col, val

        col1, self.stat_planning = make_stat_col("Planning", "#94a3b8")
        col2, self.stat_progress = make_stat_col("In Progress", "#fbbf24")
        col3, self.stat_completed = make_stat_col("Completed", "#34d399")

        sp_layout.addLayout(col1)
        sp_sep1 = QFrame()
        sp_sep1.setFixedWidth(1)
        sp_sep1.setStyleSheet("background-color: #334155;")
        sp_layout.addWidget(sp_sep1)

        sp_layout.addLayout(col2)
        sp_sep2 = QFrame()
        sp_sep2.setFixedWidth(1)
        sp_sep2.setStyleSheet("background-color: #334155;")
        sp_layout.addWidget(sp_sep2)

        sp_layout.addLayout(col3)
        b_layout.addWidget(stats_pill)

        self.content_layout.addWidget(banner)

    def _setup_about_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
            QTextEdit {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                line-height: 1.4;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #2196f3;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("badge", "#2196f3", 18))
        h_row.addWidget(icon)
        title = QLabel("About & Goals")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        h_row.addWidget(title)
        h_row.addStretch()
        sub = QLabel("Markdown supported")
        sub.setStyleSheet("font-size: 11px; color: #64748b;")
        h_row.addWidget(sub)
        layout.addLayout(h_row)

        layout.addWidget(QLabel("ABOUT ME"))
        self.about_input = QTextEdit()
        self.about_input.setMaximumHeight(85)
        self.about_input.setPlaceholderText("Write a short professional bio highlighting your technical specializations...")
        layout.addWidget(self.about_input)

        layout.addWidget(QLabel("PROFESSIONAL GOALS"))
        self.goals_input = QTextEdit()
        self.goals_input.setMaximumHeight(85)
        self.goals_input.setPlaceholderText("What are your current engineering and architectural objectives?")
        layout.addWidget(self.goals_input)

        parent_layout.addWidget(card)

    def _setup_skills_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("brain", "#2196f3", 18))
        h_row.addWidget(icon)
        title = QLabel("Skills Management")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        h_row.addWidget(title)
        h_row.addStretch()

        self.skill_count_lbl = QLabel("0 skills registered")
        self.skill_count_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        h_row.addWidget(self.skill_count_lbl)
        layout.addLayout(h_row)

        # Add skill bar
        add_bar = QHBoxLayout()
        add_bar.setSpacing(8)

        self.new_skill_input = QLineEdit()
        self.new_skill_input.setPlaceholderText("Skill name (e.g. Python, PyTorch, Rust)...")
        self.new_skill_input.setFixedHeight(34)
        self.new_skill_input.setStyleSheet("""
            QLineEdit {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                padding-left: 10px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
        """)
        self.new_skill_input.returnPressed.connect(self.add_skill)
        add_bar.addWidget(self.new_skill_input, 1)

        self.skill_level_combo = QComboBox()
        self.skill_level_combo.setFixedHeight(34)
        self.skill_level_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        self.skill_level_combo.setStyleSheet("""
            QComboBox {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 12px;
                padding-left: 8px;
                padding-right: 8px;
            }
        """)
        add_bar.addWidget(self.skill_level_combo)

        add_btn = QPushButton("+ Add Skill")
        add_btn.setFixedHeight(34)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        add_btn.clicked.connect(self.add_skill)
        add_bar.addWidget(add_btn)
        layout.addLayout(add_bar)

        # Skills Flow Layout Container
        self.skills_container = QWidget()
        self.skills_container.setStyleSheet("background: transparent;")
        self.skills_flow_layout = QHBoxLayout(self.skills_container)
        self.skills_flow_layout.setContentsMargins(0, 4, 0, 4)
        self.skills_flow_layout.setSpacing(8)
        self.skills_flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Wrap in scroll or horizontal layout
        self.skills_scroll = QScrollArea()
        self.skills_scroll.setWidgetResizable(True)
        self.skills_scroll.setFixedHeight(54)
        self.skills_scroll.setStyleSheet("background: transparent; border: none;")
        self.skills_scroll.setWidget(self.skills_container)
        layout.addWidget(self.skills_scroll)

        parent_layout.addWidget(card)

    def _setup_content_pref_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
            QTextEdit {
                background-color: #191b22;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 13px;
                line-height: 1.4;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #2196f3;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("tune", "#2196f3", 18))
        h_row.addWidget(icon)
        title = QLabel("Content & AI Generation Preferences")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        h_row.addWidget(title)
        h_row.addStretch()
        layout.addLayout(h_row)

        two_col = QHBoxLayout()
        two_col.setSpacing(12)

        c1 = QVBoxLayout()
        c1.addWidget(QLabel("TONE / STYLE / FORMATS"))
        self.content_input = QTextEdit()
        self.content_input.setMaximumHeight(80)
        self.content_input.setPlaceholderText("E.g., Concise, technical, bullet-point oriented. Prefer clean code snippets...")
        c1.addWidget(self.content_input)
        two_col.addLayout(c1)

        c2 = QVBoxLayout()
        c2.addWidget(QLabel("CONTENT TO AVOID"))
        self.avoid_input = QTextEdit()
        self.avoid_input.setMaximumHeight(80)
        self.avoid_input.setPlaceholderText("E.g., Corporate jargon, buzzwords, generic motivational platitudes...")
        c2.addWidget(self.avoid_input)
        two_col.addLayout(c2)

        layout.addLayout(two_col)
        parent_layout.addWidget(card)

    def _setup_milestones_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("award", "#4edea3", 18))
        h_row.addWidget(icon)
        title = QLabel("Milestones & Certs")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        h_row.addWidget(title)
        h_row.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2196f3;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #60a5fa;
            }
        """)
        add_btn.clicked.connect(self.add_achievement)
        h_row.addWidget(add_btn)
        layout.addLayout(h_row)

        self.achievements_container = QWidget()
        self.achievements_container.setStyleSheet("background: transparent;")
        self.achievements_layout = QVBoxLayout(self.achievements_container)
        self.achievements_layout.setContentsMargins(0, 0, 0, 0)
        self.achievements_layout.setSpacing(8)
        self.achievements_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        ach_scroll = QScrollArea()
        ach_scroll.setWidgetResizable(True)
        ach_scroll.setFixedHeight(180)
        ach_scroll.setStyleSheet("background: transparent; border: none;")
        ach_scroll.setWidget(self.achievements_container)
        layout.addWidget(ach_scroll)

        parent_layout.addWidget(card)

    def _setup_intelligence_card(self, parent_layout):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)

        h_row = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("sparkles", "#9ecaff", 18))
        h_row.addWidget(icon)
        title = QLabel("Profile Intelligence")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        h_row.addWidget(title)
        h_row.addStretch()

        self.run_intel_btn = QPushButton("Run Analysis")
        self.run_intel_btn.setIcon(get_svg_icon("sync", "#ffffff", 14))
        self.run_intel_btn.setFixedHeight(28)
        self.run_intel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.run_intel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 11px;
                font-weight: 500;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #243248;
                border-color: #2196f3;
            }
        """)
        self.run_intel_btn.clicked.connect(self.run_intelligence)
        h_row.addWidget(self.run_intel_btn)
        layout.addLayout(h_row)

        self.intelligence_output = QTextBrowser()
        self.intelligence_output.setPlaceholderText("Click 'Run Analysis' to let multi-model AI analyze your skills, projects, and roadmap...")
        self.intelligence_output.setMinimumHeight(180)
        self.intelligence_output.setStyleSheet("""
            QTextBrowser {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                line-height: 1.4;
                padding: 10px;
            }
        """)
        layout.addWidget(self.intelligence_output)

        parent_layout.addWidget(card)

    def _setup_bottom_bar(self, parent_layout):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #101623;
                border-top: 1px solid #1e293b;
                padding: 10px 24px;
            }
            QLabel {
                background: transparent;
            }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        dot = QLabel("●")
        dot.setStyleSheet("color: #10b981; font-size: 10px;")
        layout.addWidget(dot)

        status_txt = QLabel("All changes synced to local SQLite database")
        status_txt.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(status_txt)
        layout.addStretch()

        discard_btn = QPushButton("Discard")
        discard_btn.setFixedHeight(34)
        discard_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #283548;
                color: #ffffff;
            }
        """)
        discard_btn.clicked.connect(self.load_data)
        layout.addWidget(discard_btn)

        save_btn = QPushButton("Save Profile")
        save_btn.setIcon(get_svg_icon("save", "#ffffff", 14))
        save_btn.setFixedHeight(34)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        save_btn.clicked.connect(self.save_profile)
        layout.addWidget(save_btn)

        parent_layout.addWidget(bar)

    def run_intelligence(self):
        self.intelligence_output.setPlainText("Analyzing projects, skills, and professional roadmap via AI...")
        worker = IntelWorker(self.db, self.router)
        worker.signals.finished.connect(self.on_intel_done)
        worker.signals.error.connect(self.on_intel_error)
        QThreadPool.globalInstance().start(worker)

    def on_intel_done(self, result):
        self.intelligence_output.setMarkdown(result)
        self.repo.save_overview(result)

    def on_intel_error(self, err):
        self.intelligence_output.setPlainText(f"AI Analysis notice: {err}\n\nConfigure an active key in AI Providers to enable automated career intelligence.")

    def load_data(self):
        profile = self.repo.get_profile()
        self.about_input.setText(profile.get("about") or "")
        self.goals_input.setText(profile.get("professional_goals") or "")
        self.content_input.setText(profile.get("content_preferences") or "")
        self.avoid_input.setText(profile.get("things_to_avoid") or "")

        self._initial_profile_data = {
            "about": profile.get("about") or "",
            "professional_goals": profile.get("professional_goals") or "",
            "content_preferences": profile.get("content_preferences") or "",
            "things_to_avoid": profile.get("things_to_avoid") or ""
        }

        overview = profile.get("ai_overview")
        if overview:
            self.intelligence_output.setMarkdown(overview)

        # Load project stats
        stats = self.repo.get_project_stats()
        self.stat_planning.setText(str(stats.get("Planning", 0)))
        self.stat_progress.setText(str(stats.get("In Progress", 0)))
        self.stat_completed.setText(str(stats.get("Completed", 0)))

        self.load_skills()
        self.load_achievements()

    def load_skills(self):
        while self.skills_flow_layout.count():
            child = self.skills_flow_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        skills = self.repo.get_skills()
        self.skill_count_lbl.setText(f"{len(skills)} skills registered")

        if not skills:
            na_lbl = QLabel("No skills added yet.")
            na_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
            self.skills_flow_layout.addWidget(na_lbl)
        else:
            for s in skills:
                tag = SkillTagWidget(s["id"], s["name"], s.get("level", "Advanced"))
                tag.deleted.connect(self._on_delete_skill)
                self.skills_flow_layout.addWidget(tag)

    def _on_delete_skill(self, skill_id):
        self.repo.delete_skill(skill_id)
        self.load_skills()

    def add_skill(self):
        name = self.new_skill_input.text().strip()
        if name:
            level = self.skill_level_combo.currentText()
            self.repo.add_skill(name, level)
            self.new_skill_input.clear()
            self.load_skills()

    def load_achievements(self):
        while self.achievements_layout.count():
            child = self.achievements_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        achievements = self.repo.get_achievements()
        if not achievements:
            na_lbl = QLabel("No milestones or certificates registered yet.")
            na_lbl.setStyleSheet("color: #64748b; font-size: 12px; padding: 10px 0;")
            self.achievements_layout.addWidget(na_lbl)
        else:
            for a in achievements:
                row = QFrame()
                row.setStyleSheet("""
                    QFrame {
                        background-color: #191b22;
                        border: 1px solid #1e293b;
                        border-radius: 6px;
                    }
                    QFrame:hover {
                        border-color: #334155;
                    }
                """)
                rl = QHBoxLayout(row)
                rl.setContentsMargins(10, 8, 10, 8)
                rl.setSpacing(8)

                date_lbl = QLabel(a.get("date_achieved") or "Recent")
                date_lbl.setStyleSheet("font-size: 11px; font-family: monospace; color: #4edea3;")
                rl.addWidget(date_lbl)

                type_badge = QLabel(a.get("type") or "Achievement")
                type_badge.setStyleSheet("""
                    background-color: #131b2a;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 1px 5px;
                    font-size: 10px;
                    color: #94a3b8;
                """)
                rl.addWidget(type_badge)

                title_lbl = QLabel(a.get("title") or "")
                title_lbl.setStyleSheet("font-size: 12px; color: #f1f5f9;")
                title_lbl.setWordWrap(True)
                rl.addWidget(title_lbl, 1)

                del_btn = QPushButton("×")
                del_btn.setFixedSize(16, 16)
                del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                del_btn.setStyleSheet("background: transparent; border: none; color: #64748b; font-size: 13px;")
                del_btn.clicked.connect(lambda _, aid=a["id"]: self._on_delete_achievement(aid))
                rl.addWidget(del_btn)

                self.achievements_layout.addWidget(row)

    def _on_delete_achievement(self, ach_id):
        self.repo.delete_achievement(ach_id)
        self.load_achievements()

    def add_achievement(self):
        dialog = AchievementDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.repo.add_achievement(data["title"], data["description"], data["date"], data["type"])
            self.load_achievements()

    def save_profile(self):
        data = {
            "about": self.about_input.toPlainText().strip(),
            "professional_goals": self.goals_input.toPlainText().strip(),
            "content_preferences": self.content_input.toPlainText().strip(),
            "things_to_avoid": self.avoid_input.toPlainText().strip()
        }

        has_changes = data != self._initial_profile_data
        self.repo.update_profile(data)

        if has_changes:
            self._initial_profile_data = data
            QMessageBox.information(self, "Success", "Profile successfully updated and synced to local database.")
            self.run_intelligence()
        else:
            QMessageBox.information(self, "Success", "Profile saved.")
