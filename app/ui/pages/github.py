import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox,
    QLineEdit, QScrollArea, QDialog, QHBoxLayout, QFrame,
    QStackedWidget, QGraphicsOpacityEffect, QGridLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QThreadPool, QSize
from database.repository import ProfileRepository
from app.ui.components.flow_layout import FlowLayout
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.ui.pages.chat import AIChatPage


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(240)
    anim.setStartValue(0.3)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._page_entrance_anim = anim


class ModernDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("""
            QDialog {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
            QLabel {
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
            QLineEdit, QTextEdit {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #2196f3;
            }
            QPushButton {
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)


class AddRepoDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__("Add GitHub Repository", parent)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Repository Name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. forge-hub-core")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Full URL / Path"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g. github.com/username/forge-hub-core")
        layout.addWidget(self.url_input)

        layout.addWidget(QLabel("Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(70)
        self.desc_input.setPlaceholderText("Short repository summary...")
        layout.addWidget(self.desc_input)

        layout.addWidget(QLabel("Tech Stack Tags (comma-separated)"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g. Python, FastAPI, SQLite")
        layout.addWidget(self.tags_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Add Repository")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        tags = [t.strip() for t in self.tags_input.text().split(",") if t.strip()]
        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "tags": tags
        }


class AddContributionDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__("Add Contribution / Notable Project", parent)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Project / Repository Name"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. FastAPI Async Worker Pool")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Role / Standing Badge"))
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("e.g. Core Maintainer, Contributor")
        layout.addWidget(self.role_input)

        layout.addWidget(QLabel("Contribution Summary"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(70)
        self.desc_input.setPlaceholderText("Authored concurrency patches reducing memory overhead...")
        layout.addWidget(self.desc_input)

        layout.addWidget(QLabel("Tech Stack (comma-separated)"))
        self.stack_input = QLineEdit()
        self.stack_input.setPlaceholderText("e.g. Python, Asyncio, Redis")
        layout.addWidget(self.stack_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Add Contribution")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "role": self.role_input.text().strip() or "Contributor",
            "description": self.desc_input.toPlainText().strip(),
            "tech_stack": self.stack_input.text().strip()
        }


class AddPinnedRepoDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__("Pin Repository", parent)
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Repository Full Name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. username/repo-name")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(60)
        self.desc_input.setPlaceholderText("Concise repository overview...")
        layout.addWidget(self.desc_input)

        metrics = QHBoxLayout()
        s_box = QVBoxLayout()
        s_box.addWidget(QLabel("Stars"))
        self.stars_input = QLineEdit()
        self.stars_input.setPlaceholderText("e.g. 1.4k")
        s_box.addWidget(self.stars_input)
        metrics.addLayout(s_box)

        f_box = QVBoxLayout()
        f_box.addWidget(QLabel("Forks"))
        self.forks_input = QLineEdit()
        self.forks_input.setPlaceholderText("e.g. 210")
        f_box.addWidget(self.forks_input)
        metrics.addLayout(f_box)
        layout.addLayout(metrics)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Pin Repository")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "stars": self.stars_input.text().strip() or "0",
            "forks": self.forks_input.text().strip() or "0"
        }


class GitHubPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProfileRepository(db_manager)

        self.repositories = []
        self.contributions = []
        self.skills = []
        self.pinned_repos = []

        self.stacked_widget = QStackedWidget(self)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.stacked_widget)

        # Screen 0: GitHub Management Workstation
        self.form_page = QWidget()
        self.init_form_ui()
        self.stacked_widget.addWidget(self.form_page)

        # Screen 1: Dedicated AI Chat
        self.chat_container = QWidget()
        chat_layout = QVBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(24, 20, 24, 20)
        chat_layout.setSpacing(16)

        chat_top = QHBoxLayout()
        back_btn = QPushButton(" Back to GitHub Form")
        back_btn.setIcon(get_svg_icon("arrow_back", "#94a3b8", 16))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        chat_top.addWidget(back_btn)
        chat_top.addStretch()
        chat_layout.addLayout(chat_top)

        self.chat_page = AIChatPage(db_manager, chat_context="github")
        chat_layout.addWidget(self.chat_page, stretch=1)
        self.stacked_widget.addWidget(self.chat_container)

        self.load_data()
        setup_page_animation(self)

    def init_form_ui(self):
        layout = QVBoxLayout(self.form_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0b0f17; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0b0f17;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(32, 28, 32, 100) # bottom margin for fixed tray
        self.content_layout.setSpacing(24)

        # Header Banner
        header_bar = self.create_header_bar()
        self.content_layout.addLayout(header_bar)

        # Main Container Sections
        sections_container = QVBoxLayout()
        sections_container.setSpacing(24)

        # 1. GitHub Identity Section
        sections_container.addWidget(self.create_identity_section())

        # 2. GitHub Repositories Section
        sections_container.addWidget(self.create_repositories_section())

        # 3. Contributions & Notable Projects
        sections_container.addWidget(self.create_contributions_section())

        # 4. GitHub Skills (Tag System)
        sections_container.addWidget(self.create_skills_section())

        # 5. Pinned / Featured Repositories
        sections_container.addWidget(self.create_pinned_section())

        self.content_layout.addLayout(sections_container)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Docked Bottom Action Bar
        bottom_bar = self.create_bottom_bar()
        layout.addWidget(bottom_bar)

    def create_header_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        top_title = QHBoxLayout()
        top_title.setSpacing(8)
        term_icon = QLabel()
        term_icon.setPixmap(get_svg_pixmap("terminal", "#2196f3", 24))
        term_icon.setStyleSheet("background: transparent; border: none;")
        top_title.addWidget(term_icon)

        title_lbl = QLabel("GitHub Integration")
        title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 700; background: transparent; border: none;")
        top_title.addWidget(title_lbl)
        top_title.addStretch()
        title_box.addLayout(top_title)

        sub_lbl = QLabel("Manage your GitHub identity, synchronized repositories, featured codebases, and technical skills.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        title_box.addWidget(sub_lbl)
        bar.addLayout(title_box)

        bar.addStretch()

        # Right Pill & Action
        self.conn_pill = QFrame()
        self.conn_pill.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px 12px;
            }
        """)
        pill_layout = QHBoxLayout(self.conn_pill)
        pill_layout.setContentsMargins(8, 4, 10, 4)
        pill_layout.setSpacing(8)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        pill_layout.addWidget(dot)

        self.conn_text = QLabel("API Connected: @profile")
        self.conn_text.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        pill_layout.addWidget(self.conn_text)
        bar.addWidget(self.conn_pill)

        chat_btn = QPushButton(" Open GitHub AI Chat")
        chat_btn.setIcon(get_svg_icon("chat", "#ffffff", 16))
        chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 9px 18px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        chat_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        bar.addWidget(chat_btn)

        return bar

    def create_card_frame(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)
        return card

    # --- Section 1: GitHub Identity ---
    def create_identity_section(self) -> QFrame:
        card = self.create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        head = QHBoxLayout()
        badge_lbl = QLabel()
        badge_lbl.setPixmap(get_svg_pixmap("badge", "#2196f3", 20))
        badge_lbl.setStyleSheet("background: transparent; border: none;")
        head.addWidget(badge_lbl)

        title = QLabel("GitHub Identity")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        meta_lbl = QLabel("Core Metadata")
        meta_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        head.addWidget(meta_lbl)
        layout.addLayout(head)

        # Inputs Row
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(16)

        # Username
        user_box = QVBoxLayout()
        user_box.setSpacing(6)
        user_lbl = QLabel("USERNAME / VANITY URL")
        user_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        user_box.addWidget(user_lbl)

        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #2196f3;
            }
        """)
        u_lay = QHBoxLayout(user_frame)
        u_lay.setContentsMargins(10, 0, 10, 0)
        u_lay.setSpacing(4)
        prefix = QLabel("github.com/")
        prefix.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 12px; background: transparent; border: none;")
        u_lay.addWidget(prefix)

        self.username_input = QLineEdit()
        self.username_input.setStyleSheet("background: transparent; border: none; color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; padding: 8px 0;")
        self.username_input.setPlaceholderText("your-github-handle")
        self.username_input.textChanged.connect(self.on_username_changed)
        u_lay.addWidget(self.username_input)
        user_box.addWidget(user_frame)
        inputs_row.addLayout(user_box, stretch=1)

        # Bio
        bio_box = QVBoxLayout()
        bio_box.setSpacing(6)
        bio_lbl = QLabel("PROFESSIONAL HEADLINE / BIO")
        bio_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        bio_box.addWidget(bio_lbl)

        self.bio_input = QLineEdit()
        self.bio_input.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2196f3;
            }
        """)
        self.bio_input.setPlaceholderText("e.g. Senior Systems Architect & Open Source Maintainer")
        bio_box.addWidget(self.bio_input)
        inputs_row.addLayout(bio_box, stretch=1)
        layout.addLayout(inputs_row)

        # About / Readme
        readme_box = QVBoxLayout()
        readme_box.setSpacing(6)
        readme_lbl = QLabel("ABOUT / PROFILE SUMMARY (MARKDOWN)")
        readme_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        readme_box.addWidget(readme_lbl)

        self.profile_readme_input = QTextEdit()
        self.profile_readme_input.setStyleSheet("""
            QTextEdit {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                padding: 10px 12px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #2196f3;
            }
        """)
        self.profile_readme_input.setMinimumHeight(110)
        self.profile_readme_input.setPlaceholderText("Paste your main GitHub profile markdown or summary here...")
        readme_box.addWidget(self.profile_readme_input)
        layout.addLayout(readme_box)

        return card

    # --- Section 2: GitHub Repositories ---
    def create_repositories_section(self) -> QFrame:
        card = self.create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("folder_open", "#2196f3", 20))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("GitHub Repositories")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        add_btn = QPushButton(" Add Repository")
        add_btn.setIcon(get_svg_icon("plus", "#f1f5f9", 14))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_btn.clicked.connect(self.prompt_add_repository)
        head.addWidget(add_btn)
        layout.addLayout(head)

        self.repos_container = QVBoxLayout()
        self.repos_container.setSpacing(10)
        layout.addLayout(self.repos_container)

        return card

    # --- Section 3: Contributions & Notable Projects ---
    def create_contributions_section(self) -> QFrame:
        card = self.create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("brain", "#2196f3", 20))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("Contributions & Notable Projects")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        add_btn = QPushButton(" Add Contribution")
        add_btn.setIcon(get_svg_icon("plus", "#f1f5f9", 14))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_btn.clicked.connect(self.prompt_add_contribution)
        head.addWidget(add_btn)
        layout.addLayout(head)

        self.contribs_container = QVBoxLayout()
        self.contribs_container.setSpacing(10)
        layout.addLayout(self.contribs_container)

        return card

    # --- Section 4: GitHub Skills ---
    def create_skills_section(self) -> QFrame:
        card = self.create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("code", "#2196f3", 20))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("GitHub Skills")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        sub_lbl = QLabel("Indexed by AI Context Engine")
        sub_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        head.addWidget(sub_lbl)
        layout.addLayout(head)

        # Tags container with input
        tags_box = QFrame()
        tags_box.setStyleSheet("""
            QFrame {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        tb_layout = QVBoxLayout(tags_box)
        tb_layout.setContentsMargins(8, 8, 8, 8)
        tb_layout.setSpacing(10)

        self.skills_flow = QWidget()
        self.skills_flow.setStyleSheet("background: transparent; border: none;")
        self.skills_flow_layout = FlowLayout(self.skills_flow)
        self.skills_flow_layout.setSpacing(8)
        tb_layout.addWidget(self.skills_flow)

        # Add skill row
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        add_row.addStretch()

        self.new_skill_input = QLineEdit()
        self.new_skill_input.setPlaceholderText("Add skill (comma sep)...")
        self.new_skill_input.setStyleSheet("""
            QLineEdit {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 5px 10px;
                min-width: 180px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
        """)
        self.new_skill_input.returnPressed.connect(self.add_skill_from_input)
        add_row.addWidget(self.new_skill_input)

        add_s_btn = QPushButton("+ Add Skill")
        add_s_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 5px 12px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_s_btn.clicked.connect(self.add_skill_from_input)
        add_row.addWidget(add_s_btn)
        tb_layout.addLayout(add_row)

        layout.addWidget(tags_box)
        return card

    # --- Section 5: Pinned / Featured Repositories ---
    def create_pinned_section(self) -> QFrame:
        card = self.create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("push_pin", "#2196f3", 20))
        icon.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon)

        title = QLabel("Pinned / Featured Repositories")
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        head.addWidget(title)
        head.addStretch()

        pin_btn = QPushButton(" Pin Repository")
        pin_btn.setIcon(get_svg_icon("push_pin", "#f1f5f9", 14))
        pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        pin_btn.clicked.connect(self.prompt_add_pinned)
        head.addWidget(pin_btn)
        layout.addLayout(head)

        self.pinned_grid = QGridLayout()
        self.pinned_grid.setSpacing(14)
        layout.addLayout(self.pinned_grid)

        return card

    # --- Bottom Docked Bar ---
    def create_bottom_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(64)
        bar.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border-top: 1px solid #1e293b;
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(32, 0, 32, 0)

        left_info = QHBoxLayout()
        left_info.setSpacing(10)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        left_info.addWidget(dot)

        txt = QLabel("All profile changes queued for automatic bi-directional GitHub API sync.")
        txt.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        left_info.addWidget(txt)
        bar_layout.addLayout(left_info)

        bar_layout.addStretch()

        discard_btn = QPushButton("Discard Changes")
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f1f5f9;
            }
        """)
        discard_btn.clicked.connect(self.load_data)
        bar_layout.addWidget(discard_btn)

        save_btn = QPushButton(" Save GitHub Profile")
        save_btn.setIcon(get_svg_icon("sync", "#ffffff", 16))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 22px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        save_btn.clicked.connect(self.save_preferences)
        bar_layout.addWidget(save_btn)

        return bar

    def on_username_changed(self, text: str):
        uname = text.strip() or "profile"
        self.conn_text.setText(f"API Connected: @{uname}")

    # --- Data Persistence ---
    def load_data(self):
        data = self.repo.get_github_data()
        username = data.get("username") or ""
        self.username_input.setText(username)
        self.on_username_changed(username)

        self.profile_readme_input.setPlainText(data.get("profile_readme") or "")

        summary_str = data.get("projects_summary") or ""
        parsed_ok = False
        if summary_str.strip().startswith("{") and summary_str.strip().endswith("}"):
            try:
                parsed = json.loads(summary_str)
                self.bio_input.setText(parsed.get("bio") or "")
                self.repositories = parsed.get("repositories") or []
                self.contributions = parsed.get("contributions") or []
                self.skills = parsed.get("skills") or []
                self.pinned_repos = parsed.get("pinned_repos") or []
                parsed_ok = True
            except Exception:
                parsed_ok = False

        if not parsed_ok:
            self.bio_input.setText("")
            self.repositories = [
                {
                    "name": "forge-hub-core",
                    "url": f"github.com/{username or 'alexander-forge'}/forge-hub-core",
                    "description": "Modular backend orchestration service powering local AI memory and context synchronization.",
                    "tags": ["Python", "FastAPI", "SQLite"]
                }
            ] if username else []
            self.contributions = []
            self.skills = ["Python", "FastAPI", "SQLite", "Docker"]
            self.pinned_repos = []

        self.render_repositories()
        self.render_contributions()
        self.render_skills()
        self.render_pinned()

    def render_repositories(self):
        while self.repos_container.count():
            item = self.repos_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.repositories:
            empty = QLabel("No repositories connected yet.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none;")
            self.repos_container.addWidget(empty)
            return

        for idx, repo in enumerate(self.repositories):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border-color: #2196f3;
                }
            """)
            layout = QHBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(12)

            info = QVBoxLayout()
            info.setSpacing(4)

            top_line = QHBoxLayout()
            top_line.setSpacing(10)
            name_lbl = QLabel(repo.get("name", ""))
            name_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: transparent; border: none;")
            top_line.addWidget(name_lbl)

            url_lbl = QLabel(repo.get("url", ""))
            url_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            top_line.addWidget(url_lbl)
            top_line.addStretch()
            info.addLayout(top_line)

            desc = repo.get("description", "")
            if desc:
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
                desc_lbl.setWordWrap(True)
                info.addWidget(desc_lbl)

            # Tags
            tags = repo.get("tags", [])
            if tags:
                tag_row = QHBoxLayout()
                tag_row.setSpacing(6)
                for t in tags:
                    pill = QLabel(t)
                    pill.setStyleSheet("""
                        color: #4edea3;
                        font-family: 'JetBrains Mono', monospace;
                        font-size: 10px;
                        background-color: #131b2a;
                        border: 1px solid #1e293b;
                        border-radius: 4px;
                        padding: 2px 6px;
                    """)
                    tag_row.addWidget(pill)
                tag_row.addStretch()
                info.addLayout(tag_row)

            layout.addLayout(info, stretch=1)

            del_btn = QPushButton()
            del_btn.setIcon(get_svg_icon("delete", "#94a3b8", 16))
            del_btn.setFixedSize(28, 28)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.15);
                }
            """)
            del_btn.clicked.connect(lambda _, i=idx: self.delete_repository(i))
            layout.addWidget(del_btn)

            self.repos_container.addWidget(card)

    def prompt_add_repository(self):
        dialog = AddRepoDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                self.repositories.append(data)
                self.render_repositories()

    def delete_repository(self, index: int):
        if 0 <= index < len(self.repositories):
            self.repositories.pop(index)
            self.render_repositories()

    def render_contributions(self):
        while self.contribs_container.count():
            item = self.contribs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.contributions:
            empty = QLabel("No notable contributions added yet.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none;")
            self.contribs_container.addWidget(empty)
            return

        for idx, contrib in enumerate(self.contributions):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
            """)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(6)

            top = QHBoxLayout()
            title_lbl = QLabel(contrib.get("title", ""))
            title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: transparent; border: none;")
            top.addWidget(title_lbl)

            role = contrib.get("role", "Contributor")
            role_pill = QLabel(role)
            role_pill.setStyleSheet("""
                color: #4edea3;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                background-color: rgba(78, 222, 163, 0.1);
                border: 1px solid rgba(78, 222, 163, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
            top.addWidget(role_pill)
            top.addStretch()

            del_btn = QPushButton()
            del_btn.setIcon(get_svg_icon("delete", "#94a3b8", 14))
            del_btn.setFixedSize(22, 22)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.15);
                }
            """)
            del_btn.clicked.connect(lambda _, i=idx: self.delete_contribution(i))
            top.addWidget(del_btn)
            layout.addLayout(top)

            desc = contrib.get("description", "")
            if desc:
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
                desc_lbl.setWordWrap(True)
                layout.addWidget(desc_lbl)

            stack = contrib.get("tech_stack", "")
            if stack:
                stack_lbl = QLabel(f"Tech Stack: {stack}")
                stack_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
                layout.addWidget(stack_lbl)

            self.contribs_container.addWidget(card)

    def prompt_add_contribution(self):
        dialog = AddContributionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["title"]:
                self.contributions.append(data)
                self.render_contributions()

    def delete_contribution(self, index: int):
        if 0 <= index < len(self.contributions):
            self.contributions.pop(index)
            self.render_contributions()

    def render_skills(self):
        while self.skills_flow_layout.count():
            item = self.skills_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, skill in enumerate(self.skills):
            chip = QFrame()
            chip.setStyleSheet("""
                QFrame {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
            """)
            chip_l = QHBoxLayout(chip)
            chip_l.setContentsMargins(8, 4, 8, 4)
            chip_l.setSpacing(6)

            s_lbl = QLabel(skill)
            s_lbl.setStyleSheet("color: #f1f5f9; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            chip_l.addWidget(s_lbl)

            del_btn = QPushButton("×")
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0;
                }
                QPushButton:hover {
                    color: #ef4444;
                }
            """)
            del_btn.setFixedSize(14, 14)
            del_btn.clicked.connect(lambda _, i=idx: self.delete_skill(i))
            chip_l.addWidget(del_btn)

            self.skills_flow_layout.addWidget(chip)

    def add_skill_from_input(self):
        text = self.new_skill_input.text().strip()
        if text:
            parts = [p.strip() for p in text.split(",") if p.strip()]
            for p in parts:
                if p not in self.skills:
                    self.skills.append(p)
            self.new_skill_input.clear()
            self.render_skills()

    def delete_skill(self, index: int):
        if 0 <= index < len(self.skills):
            self.skills.pop(index)
            self.render_skills()

    def render_pinned(self):
        # Clear layout
        while self.pinned_grid.count():
            item = self.pinned_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.pinned_repos:
            empty = QLabel("No pinned repositories selected.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none;")
            self.pinned_grid.addWidget(empty, 0, 0)
            return

        for idx, repo in enumerate(self.pinned_repos):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(8)

            top = QHBoxLayout()
            name_lbl = QLabel(repo.get("name", ""))
            name_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            top.addWidget(name_lbl)
            top.addStretch()

            pin_icon = QLabel()
            pin_icon.setPixmap(get_svg_pixmap("push_pin", "#2196f3", 16))
            pin_icon.setStyleSheet("background: transparent; border: none;")
            top.addWidget(pin_icon)

            del_btn = QPushButton()
            del_btn.setIcon(get_svg_icon("delete", "#94a3b8", 12))
            del_btn.setFixedSize(18, 18)
            del_btn.setStyleSheet("background: transparent; border: none;")
            del_btn.clicked.connect(lambda _, i=idx: self.delete_pinned(i))
            top.addWidget(del_btn)
            card_layout.addLayout(top)

            desc = repo.get("description", "")
            if desc:
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
                desc_lbl.setWordWrap(True)
                card_layout.addWidget(desc_lbl)

            # Metrics
            meta_line = QHBoxLayout()
            meta_line.setSpacing(12)
            stars = repo.get("stars", "0")
            forks = repo.get("forks", "0")

            star_lbl = QLabel(f"⭐ {stars} stars")
            star_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            meta_line.addWidget(star_lbl)

            fork_lbl = QLabel(f"🍴 {forks} forks")
            fork_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            meta_line.addWidget(fork_lbl)
            meta_line.addStretch()
            card_layout.addLayout(meta_line)

            row = idx // 2
            col = idx % 2
            self.pinned_grid.addWidget(card, row, col)

    def prompt_add_pinned(self):
        dialog = AddPinnedRepoDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                self.pinned_repos.append(data)
                self.render_pinned()

    def delete_pinned(self, index: int):
        if 0 <= index < len(self.pinned_repos):
            self.pinned_repos.pop(index)
            self.render_pinned()

    def save_preferences(self):
        summary_payload = {
            "bio": self.bio_input.text().strip(),
            "repositories": self.repositories,
            "contributions": self.contributions,
            "skills": self.skills,
            "pinned_repos": self.pinned_repos
        }

        data = {
            "username": self.username_input.text().strip(),
            "profile_readme": self.profile_readme_input.toPlainText().strip(),
            "projects_summary": json.dumps(summary_payload, indent=2)
        }
        self.repo.update_github_data(data)

        # Launch background synchronization
        try:
            from app.ui.pages.memory import ProfileSyncWorker
            from app.ai.insights_worker import BackgroundInsightsWorker
            from app.ai import ModelRouter

            pool = QThreadPool.globalInstance()
            pool.start(ProfileSyncWorker(self.repo.db))

            router = ModelRouter(self.repo.db)
            insights_worker = BackgroundInsightsWorker(self.repo.db, router, "github")
            insights_worker.signals.finished.connect(self.chat_page.load_insights)
            pool.start(insights_worker)
        except Exception:
            pass

        QMessageBox.information(self, "Success", "GitHub profile data saved. AI is updating your memory and insights in the background!")

    def minimumSizeHint(self):
        return QSize(350, 250)

