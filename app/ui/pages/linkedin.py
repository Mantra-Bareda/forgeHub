import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox,
    QLineEdit, QScrollArea, QDialog, QHBoxLayout, QFrame, QMenu,
    QStackedWidget, QSizePolicy, QGraphicsOpacityEffect
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


class LinkedInPostDialog(ModernDialog):
    def __init__(self, parent=None, initial_content="", initial_media=""):
        super().__init__("Add LinkedIn Post", parent)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Post Content (Text)")
        header.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(header)

        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(110)
        self.content_input.setPlaceholderText("Write what you shared on LinkedIn...")
        self.content_input.setPlainText(initial_content)
        layout.addWidget(self.content_input)

        media_lbl = QLabel("Media / Link Description")
        media_lbl.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(media_lbl)

        self.media_input = QLineEdit()
        self.media_input.setPlaceholderText("e.g. Architecture diagram, GitHub demo URL, or infographic")
        self.media_input.setText(initial_media)
        layout.addWidget(self.media_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Save Post")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "content": self.content_input.toPlainText().strip(),
            "media_description": self.media_input.text().strip()
        }


class LinkedInCertificateDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__("Add LinkedIn Certificate", parent)
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Certificate Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. AWS Certified Solutions Architect")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Issuing Org / Credential ID / Date"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(80)
        self.desc_input.setPlaceholderText("e.g. Issued Oct 2023 • Credential ID AWS-98214")
        layout.addWidget(self.desc_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Add Certificate")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip()
        }


class LinkedInProjectDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__("Add LinkedIn Project", parent)
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Project Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Forge Hub Desktop Workspace")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Description / Tech Stack"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(80)
        self.desc_input.setPlaceholderText("e.g. TypeScript, PySide6, SQLite, AI Routing...")
        layout.addWidget(self.desc_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Add Project")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip()
        }


class AddItemDialog(ModernDialog):
    def __init__(self, title: str, label_text: str, placeholder: str = "", parent=None):
        super().__init__(title, parent)
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(label_text))
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        layout.addWidget(self.input_field)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Add")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_text(self):
        return self.input_field.text().strip()


class LinkedInPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProfileRepository(db_manager)

        self.stacked_widget = QStackedWidget(self)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.stacked_widget)

        # Build Screen 0: Form & Overview Workstation
        self.form_page = QWidget()
        self.init_form_ui()
        self.stacked_widget.addWidget(self.form_page)

        # Build Screen 1: Dedicated AI Chat
        self.chat_container = QWidget()
        chat_layout = QVBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(24, 20, 24, 20)
        chat_layout.setSpacing(16)

        chat_top = QHBoxLayout()
        back_btn = QPushButton(" Back to LinkedIn Form")
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

        self.chat_page = AIChatPage(db_manager, chat_context="linkedin")
        chat_layout.addWidget(self.chat_page, stretch=1)
        self.stacked_widget.addWidget(self.chat_container)

        self.load_data()
        setup_page_animation(self)

    def init_form_ui(self):
        layout = QVBoxLayout(self.form_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll Area for Form Workstation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0b0f17; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0b0f17;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(32, 28, 32, 100) # bottom margin for fixed bottom bar
        self.content_layout.setSpacing(24)

        # Header Bar
        header_bar = self.create_header_bar()
        self.content_layout.addLayout(header_bar)

        # 12-Column Split Workstation (7 left cols, 5 right cols)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(24)

        left_col = self.create_left_column()
        right_col = self.create_right_column()

        split_layout.addLayout(left_col, stretch=7)
        split_layout.addLayout(right_col, stretch=5)
        self.content_layout.addLayout(split_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Docked Bottom Action Bar
        bottom_bar = self.create_bottom_bar()
        layout.addWidget(bottom_bar)

    def create_header_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(16)

        # Left Icon Box
        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet("""
            QFrame {
                background-color: #2c96e5;
                border-radius: 12px;
            }
        """)
        icon_box_layout = QVBoxLayout(icon_box)
        icon_box_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("share", "#ffffff", 22))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_box_layout.addWidget(icon_lbl)
        bar.addWidget(icon_box)

        # Titles
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("LinkedIn Integration")
        title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 700; background: transparent; border: none;")
        sub_lbl = QLabel("Sync your personal professional metadata and AI-optimized posts directly to your LinkedIn profile.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        bar.addLayout(title_box)

        bar.addStretch()

        # Right actions: Token Synced pill + Open Chat button
        sync_pill = QFrame()
        sync_pill.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 20px;
                padding: 4px 14px;
            }
        """)
        pill_layout = QHBoxLayout(sync_pill)
        pill_layout.setContentsMargins(8, 4, 10, 4)
        pill_layout.setSpacing(8)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        pill_layout.addWidget(dot)

        pill_text = QLabel("Token Synced • SQLite Connected")
        pill_text.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        pill_layout.addWidget(pill_text)
        bar.addWidget(sync_pill)

        chat_btn = QPushButton(" Open LinkedIn AI Chat")
        chat_btn.setIcon(get_svg_icon("smart_toy", "#ffffff", 16))
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

    def create_left_column(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(20)

        # 1. LinkedIn Identity Card
        id_card = self.create_card_frame()
        id_layout = QVBoxLayout(id_card)
        id_layout.setContentsMargins(20, 20, 20, 20)
        id_layout.setSpacing(16)

        # Card Header
        card_header = QHBoxLayout()
        badge_lbl = QLabel()
        badge_lbl.setPixmap(get_svg_pixmap("badge", "#2196f3", 20))
        badge_lbl.setStyleSheet("background: transparent; border: none;")
        card_header.addWidget(badge_lbl)

        card_title = QLabel("LinkedIn Identity")
        card_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        card_header.addWidget(card_title)
        card_header.addStretch()

        public_pill = QLabel("Public Profile")
        public_pill.setStyleSheet("""
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background-color: #0b0f17;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 2px 8px;
        """)
        card_header.addWidget(public_pill)
        id_layout.addLayout(card_header)

        # Two-col row: Username & Professional Headline
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(16)

        # Username Input
        user_box = QVBoxLayout()
        user_box.setSpacing(6)
        user_lbl = QLabel("Username / Vanity URL")
        user_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        user_box.addWidget(user_lbl)

        user_input_frame = QFrame()
        user_input_frame.setStyleSheet("""
            QFrame {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #2196f3;
            }
        """)
        user_input_layout = QHBoxLayout(user_input_frame)
        user_input_layout.setContentsMargins(10, 0, 10, 0)
        user_input_layout.setSpacing(4)

        prefix_lbl = QLabel("linkedin.com/in/")
        prefix_lbl.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        user_input_layout.addWidget(prefix_lbl)

        self.username_input = QLineEdit()
        self.username_input.setStyleSheet("background: transparent; border: none; color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; padding: 8px 0;")
        self.username_input.setPlaceholderText("your-vanity-url")
        user_input_layout.addWidget(self.username_input)
        user_box.addWidget(user_input_frame)
        inputs_row.addLayout(user_box, stretch=1)

        # Professional Headline
        bio_box = QVBoxLayout()
        bio_box.setSpacing(6)
        bio_lbl = QLabel("Professional Headline")
        bio_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; background: transparent; border: none;")
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
        self.bio_input.setPlaceholderText("e.g. Senior AI Systems Engineer at Forge")
        bio_box.addWidget(self.bio_input)
        inputs_row.addLayout(bio_box, stretch=1)
        id_layout.addLayout(inputs_row)

        # About / Summary Section
        about_box = QVBoxLayout()
        about_box.setSpacing(6)
        about_header = QHBoxLayout()
        about_lbl = QLabel("About / Summary")
        about_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        about_header.addWidget(about_lbl)
        about_header.addStretch()

        self.about_count_lbl = QLabel("Markdown supported • 0 / 2,600 chars")
        self.about_count_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        about_header.addWidget(self.about_count_lbl)
        about_box.addLayout(about_header)

        self.about_input = QTextEdit()
        self.about_input.setStyleSheet("""
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
        self.about_input.setMinimumHeight(120)
        self.about_input.textChanged.connect(self.update_about_char_count)
        about_box.addWidget(self.about_input)
        id_layout.addLayout(about_box)

        col.addWidget(id_card)

        # 2. Spoken Languages Card
        lang_card = self.create_card_frame()
        lang_layout = QVBoxLayout(lang_card)
        lang_layout.setContentsMargins(20, 20, 20, 20)
        lang_layout.setSpacing(14)

        lang_header = QHBoxLayout()
        lang_icon = QLabel()
        lang_icon.setPixmap(get_svg_pixmap("language", "#4edea3", 20))
        lang_icon.setStyleSheet("background: transparent; border: none;")
        lang_header.addWidget(lang_icon)

        lang_title = QLabel("Spoken Languages")
        lang_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        lang_header.addWidget(lang_title)
        lang_header.addStretch()

        add_lang_btn = QPushButton("+ Add Language")
        add_lang_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2196f3;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #60a5fa;
                text-decoration: underline;
            }
        """)
        add_lang_btn.clicked.connect(self.prompt_add_language)
        lang_header.addWidget(add_lang_btn)
        lang_layout.addLayout(lang_header)

        self.lang_flow = QWidget()
        self.lang_flow.setStyleSheet("background: transparent; border: none;")
        self.lang_flow_layout = FlowLayout(self.lang_flow)
        self.lang_flow_layout.setSpacing(8)
        lang_layout.addWidget(self.lang_flow)

        col.addWidget(lang_card)

        # 3. LinkedIn Skills (AI Ranked) Card
        skills_card = self.create_card_frame()
        skills_layout = QVBoxLayout(skills_card)
        skills_layout.setContentsMargins(20, 20, 20, 20)
        skills_layout.setSpacing(14)

        skills_header = QHBoxLayout()
        skills_icon = QLabel()
        skills_icon.setPixmap(get_svg_pixmap("brain", "#2c96e5", 20))
        skills_icon.setStyleSheet("background: transparent; border: none;")
        skills_header.addWidget(skills_icon)

        skills_title = QLabel("LinkedIn Skills (AI Ranked)")
        skills_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        skills_header.addWidget(skills_title)
        skills_header.addStretch()

        add_skill_btn = QPushButton("+ Add Skill")
        add_skill_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2196f3;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #60a5fa;
                text-decoration: underline;
            }
        """)
        add_skill_btn.clicked.connect(self.prompt_add_skill)
        skills_header.addWidget(add_skill_btn)
        skills_layout.addLayout(skills_header)

        self.skill_flow = QWidget()
        self.skill_flow.setStyleSheet("background: transparent; border: none;")
        self.skill_flow_layout = FlowLayout(self.skill_flow)
        self.skill_flow_layout.setSpacing(8)
        skills_layout.addWidget(self.skill_flow)

        col.addWidget(skills_card)
        col.addStretch()
        return col

    def create_right_column(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(20)

        # 1. Published Posts Card
        posts_card = self.create_card_frame()
        posts_layout = QVBoxLayout(posts_card)
        posts_layout.setContentsMargins(20, 20, 20, 20)
        posts_layout.setSpacing(14)

        posts_header = QHBoxLayout()
        post_icon = QLabel()
        post_icon.setPixmap(get_svg_pixmap("article", "#4edea3", 20))
        post_icon.setStyleSheet("background: transparent; border: none;")
        posts_header.addWidget(post_icon)

        posts_title = QLabel("Published Posts")
        posts_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        posts_header.addWidget(posts_title)
        posts_header.addStretch()

        add_post_btn = QPushButton(" Add Post")
        add_post_btn.setIcon(get_svg_icon("plus", "#94a3b8", 14))
        add_post_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 10px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_post_btn.clicked.connect(self.add_post)
        posts_header.addWidget(add_post_btn)
        posts_layout.addLayout(posts_header)

        posts_sub = QLabel("Recently broadcasted items synced directly via Forge Hub Content Engine.")
        posts_sub.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        posts_sub.setWordWrap(True)
        posts_layout.addWidget(posts_sub)

        self.posts_container = QVBoxLayout()
        self.posts_container.setSpacing(10)
        posts_layout.addLayout(self.posts_container)

        col.addWidget(posts_card)

        # 2. Certificates Card
        certs_card = self.create_card_frame()
        certs_layout = QVBoxLayout(certs_card)
        certs_layout.setContentsMargins(20, 20, 20, 20)
        certs_layout.setSpacing(14)

        certs_header = QHBoxLayout()
        cert_icon = QLabel()
        cert_icon.setPixmap(get_svg_pixmap("award", "#2196f3", 20))
        cert_icon.setStyleSheet("background: transparent; border: none;")
        certs_header.addWidget(cert_icon)

        certs_title = QLabel("Certificates")
        certs_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        certs_header.addWidget(certs_title)
        certs_header.addStretch()

        add_cert_btn = QPushButton(" Add Certificate")
        add_cert_btn.setIcon(get_svg_icon("plus", "#94a3b8", 14))
        add_cert_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 10px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_cert_btn.clicked.connect(self.add_certificate)
        certs_header.addWidget(add_cert_btn)
        certs_layout.addLayout(certs_header)

        self.certs_container = QVBoxLayout()
        self.certs_container.setSpacing(8)
        certs_layout.addLayout(self.certs_container)

        col.addWidget(certs_card)

        # 3. LinkedIn Projects Card
        proj_card = self.create_card_frame()
        proj_layout = QVBoxLayout(proj_card)
        proj_layout.setContentsMargins(20, 20, 20, 20)
        proj_layout.setSpacing(14)

        proj_header = QHBoxLayout()
        proj_icon = QLabel()
        proj_icon.setPixmap(get_svg_pixmap("folder_open", "#99cbff", 20))
        proj_icon.setStyleSheet("background: transparent; border: none;")
        proj_header.addWidget(proj_icon)

        proj_title = QLabel("LinkedIn Projects")
        proj_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        proj_header.addWidget(proj_title)
        proj_header.addStretch()

        add_proj_btn = QPushButton(" Add Project")
        add_proj_btn.setIcon(get_svg_icon("plus", "#94a3b8", 14))
        add_proj_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 10px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        add_proj_btn.clicked.connect(self.add_project)
        proj_header.addWidget(add_proj_btn)
        proj_layout.addLayout(proj_header)

        self.projects_container = QVBoxLayout()
        self.projects_container.setSpacing(8)
        proj_layout.addLayout(self.projects_container)

        col.addWidget(proj_card)
        col.addStretch()
        return col

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

        # Left Info
        left_info = QHBoxLayout()
        left_info.setSpacing(10)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        left_info.addWidget(dot)

        txt = QLabel("All profile changes queued for automatic bi-directional LinkedIn API sync.")
        txt.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        left_info.addWidget(txt)
        bar_layout.addLayout(left_info)

        bar_layout.addStretch()

        # Right Action Buttons
        discard_btn = QPushButton("Discard")
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

        save_btn = QPushButton(" Save LinkedIn Profile")
        save_btn.setIcon(get_svg_icon("save", "#ffffff", 16))
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

    def update_about_char_count(self):
        chars = len(self.about_input.toPlainText())
        self.about_count_lbl.setText(f"Markdown supported • {chars:,} / 2,600 chars")

    def load_data(self):
        data = self.repo.get_linkedin_data()
        self.username_input.setText(data.get("username") or "")
        self.bio_input.setText(data.get("bio") or "")
        self.about_input.setPlainText(data.get("about") or "")
        self.update_about_char_count()

        self.load_posts()
        self.load_certificates()
        self.load_projects()
        self.load_languages()
        self.load_skills()

    # --- Posts Handling ---
    def load_posts(self):
        while self.posts_container.count():
            item = self.posts_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        posts = self.repo.get_linkedin_posts()
        if not posts:
            empty = QLabel("No published posts tracked yet.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none; padding: 10px 0;")
            self.posts_container.addWidget(empty)
            return

        for post in posts:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border-color: #334155;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)

            # Top Row: Date & Actions
            top_row = QHBoxLayout()
            date_str = str(post.get("created_at") or "Published")[:10]
            date_lbl = QLabel(f"Published • {date_str}")
            date_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            top_row.addWidget(date_lbl)
            top_row.addStretch()

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
            del_btn.clicked.connect(lambda _, pid=post["id"]: self.delete_post(pid))
            top_row.addWidget(del_btn)
            card_layout.addLayout(top_row)

            # Content preview
            content_text = post.get("content") or ""
            preview_lbl = QLabel(content_text if len(content_text) <= 140 else content_text[:140] + "...")
            preview_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
            preview_lbl.setWordWrap(True)
            card_layout.addWidget(preview_lbl)

            # Media Description
            media_text = post.get("media_description") or ""
            if media_text:
                media_lbl = QLabel(f"Media: {media_text}")
                media_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
                card_layout.addWidget(media_lbl)

            self.posts_container.addWidget(card)

    def add_post(self):
        dialog = LinkedInPostDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["content"]:
                self.repo.add_linkedin_post(data["content"], data["media_description"])
                self.load_posts()

    def delete_post(self, post_id):
        self.repo.delete_linkedin_post(post_id)
        self.load_posts()

    # --- Certificates Handling ---
    def load_certificates(self):
        while self.certs_container.count():
            item = self.certs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        certs = self.repo.get_linkedin_certificates()
        if not certs:
            empty = QLabel("No certificates recorded.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none; padding: 8px 0;")
            self.certs_container.addWidget(empty)
            return

        for cert in certs:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(12)

            icon_box = QFrame()
            icon_box.setFixedSize(32, 32)
            icon_box.setStyleSheet("background-color: #131b2a; border-radius: 6px;")
            ib_layout = QVBoxLayout(icon_box)
            ib_layout.setContentsMargins(0, 0, 0, 0)
            ib_lbl = QLabel()
            ib_lbl.setPixmap(get_svg_pixmap("verified", "#2196f3", 16))
            ib_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ib_lbl.setStyleSheet("background: transparent; border: none;")
            ib_layout.addWidget(ib_lbl)
            card_layout.addWidget(icon_box)

            info_box = QVBoxLayout()
            info_box.setSpacing(2)
            title_lbl = QLabel(cert.get("title") or "")
            title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            desc_lbl = QLabel(cert.get("description") or "")
            desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
            info_box.addWidget(title_lbl)
            info_box.addWidget(desc_lbl)
            card_layout.addLayout(info_box, stretch=1)

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
            del_btn.clicked.connect(lambda _, cid=cert["id"]: self.delete_certificate(cid))
            card_layout.addWidget(del_btn)

            self.certs_container.addWidget(card)

    def add_certificate(self):
        dialog = LinkedInCertificateDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["title"]:
                self.repo.add_linkedin_certificate(data["title"], data["description"])
                self.load_certificates()

    def delete_certificate(self, cert_id):
        self.repo.delete_linkedin_certificate(cert_id)
        self.load_certificates()

    # --- Projects Handling ---
    def load_projects(self):
        while self.projects_container.count():
            item = self.projects_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projs = self.repo.get_linkedin_projects()
        if not projs:
            empty = QLabel("No LinkedIn projects connected.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none; padding: 8px 0;")
            self.projects_container.addWidget(empty)
            return

        for proj in projs:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(12)

            icon_box = QFrame()
            icon_box.setFixedSize(32, 32)
            icon_box.setStyleSheet("background-color: rgba(33, 150, 243, 0.15); border-radius: 6px;")
            ib_layout = QVBoxLayout(icon_box)
            ib_layout.setContentsMargins(0, 0, 0, 0)
            ib_lbl = QLabel()
            ib_lbl.setPixmap(get_svg_pixmap("terminal", "#2196f3", 16))
            ib_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ib_lbl.setStyleSheet("background: transparent; border: none;")
            ib_layout.addWidget(ib_lbl)
            card_layout.addWidget(icon_box)

            info_box = QVBoxLayout()
            info_box.setSpacing(2)
            title_lbl = QLabel(proj.get("title") or "")
            title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            desc_lbl = QLabel(proj.get("description") or "")
            desc_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
            info_box.addWidget(title_lbl)
            info_box.addWidget(desc_lbl)
            card_layout.addLayout(info_box, stretch=1)

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
            del_btn.clicked.connect(lambda _, pid=proj["id"]: self.delete_project(pid))
            card_layout.addWidget(del_btn)

            self.projects_container.addWidget(card)

    def add_project(self):
        dialog = LinkedInProjectDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["title"]:
                self.repo.add_linkedin_project(data["title"], data["description"])
                self.load_projects()

    def delete_project(self, proj_id):
        self.repo.delete_linkedin_project(proj_id)
        self.load_projects()

    # --- Languages Handling ---
    def load_languages(self):
        while self.lang_flow_layout.count():
            item = self.lang_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        languages = self.repo.get_linkedin_languages()
        if not languages:
            empty = QLabel("No spoken languages specified.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none;")
            self.lang_flow_layout.addWidget(empty)
            return

        for lang in languages:
            name = lang["name"]
            tag = self.create_tag_widget(name, lambda n=name: self.delete_language(n))
            self.lang_flow_layout.addWidget(tag)

    def prompt_add_language(self):
        dialog = AddItemDialog("Add Language", "Language Name & Proficiency:", "e.g. English (Native), German (Conversational)", self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                for part in text.split(','):
                    l = part.strip()
                    if l:
                        self.repo.add_linkedin_language(l)
                self.load_languages()

    def delete_language(self, name):
        self.repo.delete_linkedin_language(name)
        self.load_languages()

    # --- Skills Handling ---
    def load_skills(self):
        while self.skill_flow_layout.count():
            item = self.skill_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        skills = self.repo.get_linkedin_skills()
        if not skills:
            empty = QLabel("No LinkedIn skills listed.")
            empty.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 12px; font-style: italic; background: transparent; border: none;")
            self.skill_flow_layout.addWidget(empty)
            return

        for skill in skills:
            name = skill["name"]
            tag = self.create_tag_widget(name, lambda n=name: self.delete_skill(n), is_primary=True)
            self.skill_flow_layout.addWidget(tag)

    def prompt_add_skill(self):
        dialog = AddItemDialog("Add LinkedIn Skill", "Skill Name(s):", "e.g. Python, Docker, PySide6 (comma-separated)", self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                for part in text.split(','):
                    s = part.strip()
                    if s:
                        self.repo.add_linkedin_skill(s)
                self.load_skills()

    def delete_skill(self, name):
        self.repo.delete_linkedin_skill(name)
        self.load_skills()

    def create_tag_widget(self, text: str, delete_callback, is_primary: bool = False) -> QFrame:
        tag = QFrame()
        if is_primary:
            tag.setStyleSheet("""
                QFrame {
                    background-color: rgba(33, 150, 243, 0.12);
                    border: 1px solid rgba(33, 150, 243, 0.35);
                    border-radius: 6px;
                }
            """)
            lbl_color = "#99cbff"
        else:
            tag.setStyleSheet("""
                QFrame {
                    background-color: #0b0f17;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
            """)
            lbl_color = "#f1f5f9"

        layout = QHBoxLayout(tag)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {lbl_color}; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(lbl)

        del_btn = QPushButton()
        del_btn.setIcon(get_svg_icon("close", "#94a3b8", 12))
        del_btn.setFixedSize(14, 14)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        del_btn.clicked.connect(delete_callback)
        layout.addWidget(del_btn)

        return tag

    def save_preferences(self):
        data = {
            "username": self.username_input.text().strip(),
            "bio": self.bio_input.text().strip(),
            "about": self.about_input.toPlainText().strip()
        }
        self.repo.update_linkedin_data(data)

        # Launch background synchronization
        try:
            from app.ui.pages.memory import ProfileSyncWorker
            from app.ai.insights_worker import BackgroundInsightsWorker
            from app.ai import ModelRouter

            pool = QThreadPool.globalInstance()
            pool.start(ProfileSyncWorker(self.repo.db))

            router = ModelRouter(self.repo.db)
            insights_worker = BackgroundInsightsWorker(self.repo.db, router, "linkedin")
            insights_worker.signals.finished.connect(self.chat_page.load_insights)
            pool.start(insights_worker)
        except Exception:
            pass

        QMessageBox.information(self, "Success", "LinkedIn profile data saved. AI is updating your memory and insights in the background!")

    def minimumSizeHint(self):
        return QSize(350, 250)

