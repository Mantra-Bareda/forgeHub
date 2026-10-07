from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTextBrowser, QScrollArea, QFrame, QLineEdit, 
    QComboBox, QMessageBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QThreadPool, QRunnable, QObject
from PySide6.QtGui import QCursor

from database.repository import ProfileRepository, MemoryRepository, CertificateRepository, HackathonRepository, PostRepository
from app.ui.components.achievement_dialog import AchievementDialog
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.core.palette import ColorPalette, get_current_palette
from app.core.config import load_config, save_config
from app.core.theme import theme_manager


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
            from database.repository import ProfileRepository, MemoryRepository, ProjectRepository, PostRepository
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

    def __init__(self, skill_id, name, level, palette: ColorPalette = None):
        super().__init__()
        self.skill_id = skill_id
        self.palette = palette or get_current_palette()
        self.setObjectName("skillTag")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 6, 4)
        layout.setSpacing(6)

        self.name_lbl = QLabel(name)
        layout.addWidget(self.name_lbl)

        # Level badge styling
        level_lower = level.lower()
        if "expert" in level_lower:
            lvl_style = "background-color: rgba(16, 185, 129, 0.2); color: #059669; border: 1px solid rgba(16, 185, 129, 0.4);"
        elif "advanced" in level_lower:
            lvl_style = "background-color: rgba(33, 150, 243, 0.2); color: #9ecaff; border: 1px solid rgba(33, 150, 243, 0.4);"
        elif "intermediate" in level_lower:
            lvl_style = "background-color: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4);"
        else:
            lvl_style = "background-color: rgba(100, 116, 139, 0.2); color: #B1B7AB; border: 1px solid rgba(100, 116, 139, 0.4);"

        self.lvl_lbl = QLabel(level)
        self.lvl_lbl.setStyleSheet(f"""
            {lvl_style}
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 600;
            font-family: monospace;
        """)
        layout.addWidget(self.lvl_lbl)

        # Remove button
        self.del_btn = QPushButton("×")
        self.del_btn.setFixedSize(16, 16)
        self.del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8B9485;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.skill_id))
        layout.addWidget(self.del_btn)

        self.apply_theme_colors(self.palette)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            #skillTag {{
                background-color: {self.palette.bg_card_inner if pal.is_dark else pal.bg_badge};
                border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                border-radius: 6px;
            }}
            #skillTag:hover {{
                border-color: {self.palette.accent};
            }}
            #skillTag QLabel {{
                background: transparent;
            }}
        """)
        self.name_lbl.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {self.palette.fg_primary}; background: transparent;")


class ProfilePage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProfileRepository(self.db)
        self._initial_profile_data = {}
        self.palette = get_current_palette()
        self.setObjectName("profileRoot")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for entire page
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
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
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll, 1)

        # 3. Bottom Action Dock
        self._setup_bottom_bar(main_layout)

        # Page entrance animation
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(240)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        from app.ai.router import ModelRouter
        self.router = ModelRouter(self.db)

        # Apply active palette and connect live theme updates
        self.apply_theme_colors(self.palette)

        self.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.3)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def _setup_top_banner(self):
        self.banner = QFrame()
        self.banner.setObjectName("profileBanner")
        b_layout = QHBoxLayout(self.banner)
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
        
        self.config = load_config()
        stored_name = self.config.get("user_name", "Professional Profile")
        self.user_name_lbl = QLabel(stored_name)
        
        self.name_edit = QLineEdit(stored_name)
        self.name_edit.setVisible(False)
        self.name_edit.returnPressed.connect(self._save_user_name)
        
        self.edit_name_btn = QPushButton()
        self.edit_name_btn.setFixedSize(24, 24)
        self.edit_name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_name_btn.setToolTip("Edit Name")
        self.edit_name_btn.clicked.connect(self._toggle_name_edit)
        
        name_row.addWidget(self.user_name_lbl)
        name_row.addWidget(self.name_edit)
        name_row.addWidget(self.edit_name_btn)

        stored_role = self.config.get("user_role", "Senior AI Architect & Engineer")
        self.role_badge = QLabel(stored_role)
        
        self.role_edit = QLineEdit(stored_role)
        self.role_edit.setVisible(False)
        self.role_edit.returnPressed.connect(self._save_user_role)
        
        self.edit_role_btn = QPushButton()
        self.edit_role_btn.setFixedSize(20, 20)
        self.edit_role_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_role_btn.setToolTip("Edit Role")
        self.edit_role_btn.clicked.connect(self._toggle_role_edit)
        
        name_row.addWidget(self.role_badge)
        name_row.addWidget(self.role_edit)
        name_row.addWidget(self.edit_role_btn)
        name_row.addStretch()
        user_col.addLayout(name_row)

        # Removed user_sub_lbl as requested
        b_layout.addLayout(user_col, 1)

        # Project Overview Stats Pill
        self.stats_pill = QFrame()
        sp_layout = QHBoxLayout(self.stats_pill)
        sp_layout.setContentsMargins(14, 8, 14, 8)
        sp_layout.setSpacing(14)

        def make_stat_col(label, color):
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(1)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label.upper())
            lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #8B9485;")
            val = QLabel("0")
            val.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(val)
            return col, val

        col1, self.stat_planning = make_stat_col("Planning", "#B1B7AB")
        col2, self.stat_progress = make_stat_col("In Progress", "#fbbf24")
        col3, self.stat_completed = make_stat_col("Completed", "#34d399")

        sp_layout.addLayout(col1)
        self.sp_sep1 = QFrame()
        self.sp_sep1.setFixedWidth(1)
        sp_layout.addWidget(self.sp_sep1)

        sp_layout.addLayout(col2)
        self.sp_sep2 = QFrame()
        self.sp_sep2.setFixedWidth(1)
        sp_layout.addWidget(self.sp_sep2)

        sp_layout.addLayout(col3)
        b_layout.addWidget(self.stats_pill)

        self.content_layout.addWidget(self.banner)

    def _setup_about_card(self, parent_layout):
        self.about_card = QFrame()
        layout = QVBoxLayout(self.about_card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        self.about_icon = QLabel()
        self.about_icon.setPixmap(get_svg_pixmap("badge", "#276125", 18))
        h_row.addWidget(self.about_icon)
        self.about_title = QLabel("About & Goals")
        h_row.addWidget(self.about_title)
        h_row.addStretch()
        self.about_sub = QLabel("Markdown supported")
        h_row.addWidget(self.about_sub)
        layout.addLayout(h_row)

        self.lbl_about_hdr = QLabel("ABOUT ME")
        layout.addWidget(self.lbl_about_hdr)
        self.about_input = QTextEdit()
        self.about_input.setMaximumHeight(85)
        self.about_input.setPlaceholderText("Write a short professional bio highlighting your technical specializations...")
        layout.addWidget(self.about_input)

        self.lbl_goals_hdr = QLabel("PROFESSIONAL GOALS")
        layout.addWidget(self.lbl_goals_hdr)
        self.goals_input = QTextEdit()
        self.goals_input.setMaximumHeight(85)
        self.goals_input.setPlaceholderText("What are your current engineering and architectural objectives?")
        layout.addWidget(self.goals_input)

        parent_layout.addWidget(self.about_card)

    def _setup_skills_card(self, parent_layout):
        self.skills_card = QFrame()
        layout = QVBoxLayout(self.skills_card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        self.skills_icon = QLabel()
        self.skills_icon.setPixmap(get_svg_pixmap("brain", "#276125", 18))
        h_row.addWidget(self.skills_icon)
        self.skills_title = QLabel("Skills Management")
        h_row.addWidget(self.skills_title)
        h_row.addStretch()

        self.skill_count_lbl = QLabel("0 skills registered")
        h_row.addWidget(self.skill_count_lbl)
        layout.addLayout(h_row)

        # Add skill bar
        add_bar = QHBoxLayout()
        add_bar.setSpacing(8)

        self.new_skill_input = QLineEdit()
        self.new_skill_input.setPlaceholderText("Skill name (e.g. Python, PyTorch, Rust)...")
        self.new_skill_input.setFixedHeight(34)
        self.new_skill_input.returnPressed.connect(self.add_skill)
        add_bar.addWidget(self.new_skill_input, 1)

        self.skill_level_combo = QComboBox()
        self.skill_level_combo.setFixedHeight(34)
        self.skill_level_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        add_bar.addWidget(self.skill_level_combo)

        self.add_skill_btn = QPushButton("+ Add Skill")
        self.add_skill_btn.setFixedHeight(34)
        self.add_skill_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_skill_btn.clicked.connect(self.add_skill)
        add_bar.addWidget(self.add_skill_btn)
        layout.addLayout(add_bar)

        # Skills Flow Layout Container
        self.skills_container = QWidget()
        self.skills_container.setStyleSheet("background: transparent;")
        self.skills_flow_layout = QHBoxLayout(self.skills_container)
        self.skills_flow_layout.setContentsMargins(0, 4, 0, 4)
        self.skills_flow_layout.setSpacing(8)
        self.skills_flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.skills_scroll = QScrollArea()
        self.skills_scroll.setWidgetResizable(True)
        self.skills_scroll.setFixedHeight(54)
        self.skills_scroll.setStyleSheet("background: transparent; border: none;")
        self.skills_scroll.setWidget(self.skills_container)
        layout.addWidget(self.skills_scroll)

        parent_layout.addWidget(self.skills_card)

    def _setup_content_pref_card(self, parent_layout):
        self.content_pref_card = QFrame()
        layout = QVBoxLayout(self.content_pref_card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        self.pref_icon = QLabel()
        self.pref_icon.setPixmap(get_svg_pixmap("tune", "#276125", 18))
        h_row.addWidget(self.pref_icon)
        self.content_pref_title = QLabel("Content & AI Generation Preferences")
        h_row.addWidget(self.content_pref_title)
        h_row.addStretch()
        layout.addLayout(h_row)

        two_col = QHBoxLayout()
        two_col.setSpacing(12)

        c1 = QVBoxLayout()
        self.lbl_tone_hdr = QLabel("TONE / STYLE / FORMATS")
        c1.addWidget(self.lbl_tone_hdr)
        self.content_input = QTextEdit()
        self.content_input.setMaximumHeight(80)
        self.content_input.setPlaceholderText("E.g., Concise, technical, bullet-point oriented. Prefer clean code snippets...")
        c1.addWidget(self.content_input)
        two_col.addLayout(c1)

        c2 = QVBoxLayout()
        self.lbl_avoid_hdr = QLabel("CONTENT TO AVOID")
        c2.addWidget(self.lbl_avoid_hdr)
        self.avoid_input = QTextEdit()
        self.avoid_input.setMaximumHeight(80)
        self.avoid_input.setPlaceholderText("E.g., Corporate jargon, buzzwords, generic motivational platitudes...")
        c2.addWidget(self.avoid_input)
        two_col.addLayout(c2)

        layout.addLayout(two_col)
        parent_layout.addWidget(self.content_pref_card)

    def _setup_milestones_card(self, parent_layout):
        self.milestones_card = QFrame()
        layout = QVBoxLayout(self.milestones_card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        h_row = QHBoxLayout()
        self.milestones_icon = QLabel()
        self.milestones_icon.setPixmap(get_svg_pixmap("award", "#059669", 18))
        h_row.addWidget(self.milestones_icon)
        self.milestones_title = QLabel("Milestones & Certs")
        h_row.addWidget(self.milestones_title)
        h_row.addStretch()

        self.milestones_add_btn = QPushButton("+ Add")
        self.milestones_add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.milestones_add_btn.clicked.connect(self.add_achievement)
        h_row.addWidget(self.milestones_add_btn)
        layout.addLayout(h_row)

        self.achievements_container = QWidget()
        self.achievements_container.setStyleSheet("background: transparent;")
        self.achievements_layout = QVBoxLayout(self.achievements_container)
        self.achievements_layout.setContentsMargins(0, 0, 0, 0)
        self.achievements_layout.setSpacing(8)
        self.achievements_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ach_scroll = QScrollArea()
        self.ach_scroll.setWidgetResizable(True)
        self.ach_scroll.setFixedHeight(180)
        self.ach_scroll.setStyleSheet("background: transparent; border: none;")
        self.ach_scroll.setWidget(self.achievements_container)
        layout.addWidget(self.ach_scroll)

        parent_layout.addWidget(self.milestones_card)

    def _setup_intelligence_card(self, parent_layout):
        self.intel_card = QFrame()
        layout = QVBoxLayout(self.intel_card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)

        h_row = QHBoxLayout()
        self.intel_icon = QLabel()
        self.intel_icon.setPixmap(get_svg_pixmap("sparkles", "#9ecaff", 18))
        h_row.addWidget(self.intel_icon)
        self.intel_title = QLabel("Profile Intelligence")
        h_row.addWidget(self.intel_title)
        h_row.addStretch()

        self.run_intel_btn = QPushButton("Run Analysis")
        self.run_intel_btn.setIcon(get_svg_icon("sync", "#ffffff", 14))
        self.run_intel_btn.setFixedHeight(28)
        self.run_intel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.run_intel_btn.clicked.connect(self.run_intelligence)
        h_row.addWidget(self.run_intel_btn)
        layout.addLayout(h_row)

        self.intelligence_output = QTextBrowser()
        self.intelligence_output.setPlaceholderText("Click 'Run Analysis' to let multi-model AI analyze your skills, projects, and roadmap...")
        self.intelligence_output.setMinimumHeight(180)
        layout.addWidget(self.intelligence_output)

        parent_layout.addWidget(self.intel_card)

    def _setup_bottom_bar(self, parent_layout):
        self.bottom_bar = QFrame()
        layout = QHBoxLayout(self.bottom_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.bottom_dot = QLabel("●")
        self.bottom_dot.setStyleSheet("color: #10b981; font-size: 10px; background: transparent;")
        layout.addWidget(self.bottom_dot)

        self.status_txt = QLabel("All changes synced to local SQLite database")
        layout.addWidget(self.status_txt)
        layout.addStretch()

        self.discard_btn = QPushButton("Discard")
        self.discard_btn.setFixedHeight(34)
        self.discard_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.discard_btn.clicked.connect(self.load_data)
        layout.addWidget(self.discard_btn)

        self.save_btn = QPushButton("Save Profile")
        self.save_btn.setIcon(get_svg_icon("save", "#ffffff", 14))
        self.save_btn.setFixedHeight(34)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_profile)
        layout.addWidget(self.save_btn)

        parent_layout.addWidget(self.bottom_bar)

    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal

        self.setStyleSheet(f"""
            #profileRoot {{
                background-color: {self.palette.bg_app};
            }}
            QLabel {{
                background: transparent;
                background-color: transparent;
            }}
        """)

        if hasattr(self, "scroll"):
            self.scroll.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {self.palette.bg_app};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {self.palette.scrollbar_track};
                    width: 6px;
                    margin: 0;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {self.palette.scrollbar_thumb};
                    border-radius: 3px;
                    min-height: 24px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {self.palette.scrollbar_thumb_hover};
                }}
            """)

        if hasattr(self, "content_widget"):
            self.content_widget.setStyleSheet(f"background-color: {self.palette.bg_app};")

        # Top Banner
        if hasattr(self, "banner"):
            self.banner.setStyleSheet(f"""
                #profileBanner {{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_card};
                    border-radius: 10px;
                    padding: 16px 20px;
                }}
                #profileBanner QLabel {{
                    background: transparent;
                }}
            """)

        if hasattr(self, "user_name_lbl"):
            self.user_name_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {self.palette.fg_primary}; letter-spacing: -0.3px; background: transparent;")
        if hasattr(self, "user_sub_lbl"):
            self.user_sub_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")
        if hasattr(self, "role_badge"):
            self.role_badge.setStyleSheet(f"""
                background-color: {self.palette.accent_bg};
                border: 1px solid {self.palette.border_focus};
                color: {self.palette.accent};
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            """)

        if hasattr(self, "stats_pill"):
            self.stats_pill.setStyleSheet(f"""
                background-color: {self.palette.bg_card_inner if pal.is_dark else pal.bg_badge};
                border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                border-radius: 8px;
            """)
        if hasattr(self, "sp_sep1"):
            self.sp_sep1.setStyleSheet(f"background-color: {self.palette.border_card};")
        if hasattr(self, "sp_sep2"):
            self.sp_sep2.setStyleSheet(f"background-color: {self.palette.border_card};")

        # Generic Card styling
        card_qss = f"""
            QFrame {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """
        for card_w in [getattr(self, "about_card", None),
                       getattr(self, "skills_card", None),
                       getattr(self, "content_pref_card", None),
                       getattr(self, "milestones_card", None),
                       getattr(self, "intel_card", None)]:
            if card_w:
                card_w.setStyleSheet(card_qss)

        # Card Headings & Secondary Labels
        title_qss = f"font-size: 15px; font-weight: 600; color: {self.palette.fg_primary}; background: transparent;"
        for t in [getattr(self, "about_title", None),
                  getattr(self, "skills_title", None),
                  getattr(self, "content_pref_title", None),
                  getattr(self, "milestones_title", None),
                  getattr(self, "intel_title", None)]:
            if t:
                t.setStyleSheet(title_qss)

        sub_qss = f"font-size: 11px; color: {self.palette.fg_muted}; background: transparent;"
        if hasattr(self, "about_sub"):
            self.about_sub.setStyleSheet(sub_qss)
        if hasattr(self, "skill_count_lbl"):
            self.skill_count_lbl.setStyleSheet(sub_qss)

        hdr_qss = f"font-size: 11px; font-weight: 600; color: {self.palette.fg_muted}; background: transparent;"
        for h in [getattr(self, "lbl_about_hdr", None),
                  getattr(self, "lbl_goals_hdr", None),
                  getattr(self, "lbl_tone_hdr", None),
                  getattr(self, "lbl_avoid_hdr", None)]:
            if h:
                h.setStyleSheet(hdr_qss)

        # Text Inputs
        input_qss = f"""
            QTextEdit {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-size: 13px;
                line-height: 1.4;
                padding: 10px;
            }}
            QTextEdit:focus {{
                border-color: {self.palette.accent};
            }}
        """
        for inp in [getattr(self, "about_input", None),
                    getattr(self, "goals_input", None),
                    getattr(self, "content_input", None),
                    getattr(self, "avoid_input", None)]:
            if inp:
                inp.setStyleSheet(input_qss)

        # Skills line edit & combo
        if hasattr(self, "new_skill_input"):
            self.new_skill_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {self.palette.bg_input};
                    border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_primary};
                    font-size: 13px;
                    padding-left: 10px;
                }}
                QLineEdit:focus {{
                    border-color: {self.palette.accent};
                }}
            """)

        if hasattr(self, "skill_level_combo"):
            self.skill_level_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {self.palette.bg_input};
                    border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_primary};
                    font-size: 12px;
                    padding-left: 8px;
                    padding-right: 8px;
                }}
            """)

        if hasattr(self, "add_skill_btn"):
            self.add_skill_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.accent};
                    border: none;
                    border-radius: 6px;
                    color: {self.palette.accent_fg};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background-color: {self.palette.accent_hover};
                }}
            """)

        # Milestones Add button
        if hasattr(self, "milestones_add_btn"):
            self.milestones_add_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {self.palette.accent};
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    color: {self.palette.accent_hover};
                }}
            """)

        # Intelligence
        if hasattr(self, "run_intel_btn"):
            self.run_intel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.bg_card_inner if pal.is_dark else pal.bg_badge};
                    border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_primary};
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background-color: {self.palette.bg_surface_hover};
                    border-color: {self.palette.accent};
                }}
            """)

        if hasattr(self, "intelligence_output"):
            self.intelligence_output.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: {self.palette.bg_input};
                    border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_primary};
                    font-size: 12px;
                    line-height: 1.4;
                    padding: 10px;
                }}
            """)

        # Bottom Bar
        if hasattr(self, "bottom_bar"):
            self.bottom_bar.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.palette.bg_card};
                    border-top: 1px solid {self.palette.border_card};
                    padding: 10px 24px;
                }}
                QLabel {{
                    background: transparent;
                }}
            """)
        if hasattr(self, "status_txt"):
            self.status_txt.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_muted}; background: transparent;")

        if hasattr(self, "discard_btn"):
            self.discard_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.bg_card_inner if pal.is_dark else pal.bg_badge};
                    border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                    border-radius: 6px;
                    color: {self.palette.fg_secondary};
                    font-size: 12px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {self.palette.bg_surface_hover};
                    color: {self.palette.fg_primary};
                }}
            """)

        if hasattr(self, "save_btn"):
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.palette.accent};
                    border: none;
                    border-radius: 6px;
                    color: {self.palette.accent_fg};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.palette.accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.palette.accent_pressed};
                }}
            """)

        # Re-apply theme to active skill tags
        if hasattr(self, "skills_flow_layout"):
            for i in range(self.skills_flow_layout.count()):
                item = self.skills_flow_layout.itemAt(i)
                if item and item.widget() and hasattr(item.widget(), "apply_theme_colors"):
                    item.widget().apply_theme_colors(pal)


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

        pal = getattr(self, 'palette', get_current_palette())
        if not skills:
            na_lbl = QLabel("No skills added yet.")
            na_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 12px; background: transparent;")
            self.skills_flow_layout.addWidget(na_lbl)
        else:
            for s in skills:
                tag = SkillTagWidget(s["id"], s["name"], s.get("level", "Advanced"), palette=pal)
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
        pal = getattr(self, 'palette', get_current_palette())
        if not achievements:
            na_lbl = QLabel("No milestones or certificates registered yet.")
            na_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 12px; padding: 10px 0; background: transparent;")
            self.achievements_layout.addWidget(na_lbl)
        else:
            for a in achievements:
                row = QFrame()
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {self.palette.bg_card_inner if pal.is_dark else pal.bg_badge};
                        border: 1px solid {self.palette.border_card if pal.is_dark else pal.border_subtle};
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        border-color: {self.palette.border_focus};
                    }}
                """)
                rl = QHBoxLayout(row)
                rl.setContentsMargins(10, 8, 10, 8)
                rl.setSpacing(8)

                date_lbl = QLabel(a.get("date_achieved") or "Recent")
                date_lbl.setStyleSheet("font-size: 11px; font-family: monospace; color: #059669; background: transparent;")
                rl.addWidget(date_lbl)

                type_badge = QLabel(a.get("type") or "Achievement")
                type_badge.setStyleSheet(f"""
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_subtle};
                    border-radius: 4px;
                    padding: 1px 5px;
                    font-size: 10px;
                    color: {self.palette.fg_muted};
                """)
                rl.addWidget(type_badge)

                title_lbl = QLabel(a.get("title") or "")
                title_lbl.setStyleSheet(f"font-size: 12px; color: {self.palette.fg_primary}; background: transparent;")
                title_lbl.setWordWrap(True)
                title_lbl.setMinimumWidth(1)
                rl.addWidget(title_lbl, 1)

                del_btn = QPushButton("×")
                del_btn.setFixedSize(16, 16)
                del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                del_btn.setStyleSheet(f"background: transparent; border: none; color: {self.palette.fg_muted}; font-size: 13px;")
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


    def _toggle_name_edit(self):
        if self.user_name_lbl.isVisible():
            self.user_name_lbl.setVisible(False)
            self.name_edit.setVisible(True)
            self.name_edit.setText(self.user_name_lbl.text())
            self.name_edit.setFocus()
            self.edit_name_btn.setIcon(get_svg_icon("check_circle", self.palette.success, 14))
        else:
            self._save_user_name()

    def _save_user_name(self):
        new_name = self.name_edit.text().strip()
        if new_name:
            self.user_name_lbl.setText(new_name)
            self.config["user_name"] = new_name
            save_config(self.config)
            
            self._sync_identity_memory()
            
        self.name_edit.setVisible(False)
        self.user_name_lbl.setVisible(True)
        self.edit_name_btn.setIcon(get_svg_icon("edit_note", self.palette.fg_muted, 14))


    def _toggle_role_edit(self):
        if self.role_badge.isVisible():
            self.role_badge.setVisible(False)
            self.role_edit.setVisible(True)
            self.role_edit.setText(self.role_badge.text())
            self.role_edit.setFocus()
            self.edit_role_btn.setIcon(get_svg_icon("check_circle", self.palette.success, 12))
        else:
            self._save_user_role()

    def _save_user_role(self):
        new_role = self.role_edit.text().strip()
        if new_role:
            self.role_badge.setText(new_role)
            self.config["user_role"] = new_role
            from app.core.config import save_config
            save_config(self.config)
            self._sync_identity_memory()
            
        self.role_edit.setVisible(False)
        self.role_badge.setVisible(True)
        self.edit_role_btn.setIcon(get_svg_icon("edit_note", self.palette.fg_muted, 12))

    def _sync_identity_memory(self):
        try:
            name = self.config.get("user_name", "Professional Profile")
            role = self.config.get("user_role", "Senior AI Architect & Engineer")
            
            from database.repository import MemoryRepository
            mem_repo = MemoryRepository(self.db)
            mems = mem_repo.get_memories(category="Identity")
            mem_text = f"User's name is {name} and role is {role}."
            
            found_id = None
            for m in mems:
                if m['content'].startswith("User's name is "):
                    found_id = m['id']
                    break
            
            if found_id:
                mem_repo.update_memory(found_id, mem_text, category="Identity", importance="High")
            else:
                mem_repo.add_memory(mem_text, category="Identity", importance="High")
        except Exception as e:
            import logging
            logging.getLogger("ForgeHub").error(f"Failed to sync identity to memory: {e}")

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
