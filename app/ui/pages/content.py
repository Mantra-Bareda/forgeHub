import re
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QTextBrowser, QMessageBox,
    QFrame, QSplitter, QFileDialog, QGraphicsOpacityEffect,
    QButtonGroup, QStackedWidget
)
from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication
from app.ai.generator import ContentGenerator
from app.ai.compiler import ContextCompiler
from database.repository import ProjectRepository, ProfileRepository, CertificateRepository, HackathonRepository
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


def setup_page_animation(widget: QWidget):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(280)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._page_entrance_anim = anim


class GenWorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class ContentGenWorker(QRunnable):
    def __init__(self, generator, mode, source_type, item_id, instructions):
        super().__init__()
        self.generator = generator
        self.mode = mode
        self.source_type = source_type
        self.item_id = item_id
        self.instructions = instructions
        self.signals = GenWorkerSignals()

    def run(self):
        try:
            if self.mode == "GitHub README":
                res = self.generator.generate_github_readme(self.item_id, self.instructions)
            elif self.mode == "LinkedIn Post":
                res = self.generator.generate_linkedin_post(self.source_type, self.item_id, self.instructions)
            else:
                res = "Custom generation not fully supported yet."
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))


class AdvisorWorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class AdvisorWorker(QRunnable):
    def __init__(self, generator, source_type, content_data):
        super().__init__()
        self.generator = generator
        self.source_type = source_type
        self.content_data = content_data
        self.signals = AdvisorWorkerSignals()

    def run(self):
        try:
            res = self.generator.evaluate_posting_advisor(self.source_type, self.content_data)
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))


class PolishWorker(QRunnable):
    def __init__(self, db_manager, text):
        super().__init__()
        self.db = db_manager
        self.text = text
        self.signals = GenWorkerSignals()

    def run(self):
        try:
            from app.ai.router import ModelRouter
            router = ModelRouter(self.db)
            prompt = (
                "Please polish and enhance the tone of the following technical content for maximum clarity, "
                "authority, and developer engagement. Maintain all core technical details while eliminating buzzwords:\n\n"
                f"{self.text}"
            )
            polished = router.route_request(
                prompt=prompt,
                category="General",
                system_prompt="You are an expert technical editor and developer advocate. Return polished content in Markdown.",
                max_tokens=1500
            )
            self.signals.finished.emit(polished)
        except Exception as e:
            self.signals.error.emit(str(e))


class ContentPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

        self.proj_repo = ProjectRepository(self.db)
        self.prof_repo = ProfileRepository(self.db)
        self.cert_repo = CertificateRepository(self.db)
        self.hack_repo = HackathonRepository(self.db)

        self.compiler = ContextCompiler(self.db)
        self.generator = ContentGenerator(self.db, self.compiler)
        self.thread_pool = QThreadPool.globalInstance()

        self.current_mode = "LinkedIn Post"
        self.current_source_category = "Project"

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Workspace Header Banner
        header_banner = self.create_top_header()
        root_layout.addWidget(header_banner)

        # 2. Main Workspace Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e293b;
                width: 1px;
            }
        """)

        # Left: Configuration Panel
        left_panel = self.create_config_panel()
        splitter.addWidget(left_panel)

        # Right: Editor & Live Workspace
        right_panel = self.create_editor_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([380, 820])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter, stretch=1)

        self.load_items()
        setup_page_animation(self)

    def create_top_header(self) -> QFrame:
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border-bottom: 1px solid #1e293b;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(16)

        # Left Icon & Title
        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet("background-color: rgba(33, 150, 243, 0.15); border-radius: 8px;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("article", "#2196f3", 20))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        ib_layout.addWidget(icon_lbl)
        layout.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        title_lbl = QLabel("Content Engine Workspace")
        title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 700; background: transparent; border: none;")
        top_row.addWidget(title_lbl)

        core_badge = QLabel("v2.4-Core")
        core_badge.setStyleSheet("""
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            background-color: #131b2a;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 1px 6px;
        """)
        top_row.addWidget(core_badge)
        top_row.addStretch()
        title_box.addLayout(top_row)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(6)
        sub_lbl = QLabel("Powered by Multi-Model Context Routing")
        sub_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        sub_row.addWidget(sub_lbl)

        sep = QLabel("•")
        sep.setStyleSheet("color: #475569; font-size: 12px; background: transparent; border: none;")
        sub_row.addWidget(sep)

        dot = QFrame()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 3px;")
        sub_row.addWidget(dot)

        synced_lbl = QLabel("Local Memory Graph Synchronized")
        synced_lbl.setStyleSheet("color: #4edea3; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        sub_row.addWidget(synced_lbl)
        sub_row.addStretch()
        title_box.addLayout(sub_row)

        layout.addLayout(title_box)
        layout.addStretch()

        # Telemetry chips
        chip1 = QFrame()
        chip1.setStyleSheet("background-color: #131b2a; border: 1px solid #1e293b; border-radius: 6px; padding: 3px 10px;")
        c1_lay = QHBoxLayout(chip1)
        c1_lay.setContentsMargins(6, 3, 6, 3)
        c1_lay.setSpacing(6)
        i1 = QLabel()
        i1.setPixmap(get_svg_pixmap("memory", "#2196f3", 14))
        i1.setStyleSheet("background: transparent; border: none;")
        c1_lay.addWidget(i1)
        t1 = QLabel("Context: Adaptive Cache")
        t1.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        c1_lay.addWidget(t1)
        layout.addWidget(chip1)

        chip2 = QFrame()
        chip2.setStyleSheet("background-color: #131b2a; border: 1px solid #1e293b; border-radius: 6px; padding: 3px 10px;")
        c2_lay = QHBoxLayout(chip2)
        c2_lay.setContentsMargins(6, 3, 6, 3)
        c2_lay.setSpacing(6)
        i2 = QLabel()
        i2.setPixmap(get_svg_pixmap("bolt", "#4edea3", 14))
        i2.setStyleSheet("background: transparent; border: none;")
        c2_lay.addWidget(i2)
        t2 = QLabel("Latency: <15ms (SQLite-WAL)")
        t2.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        c2_lay.addWidget(t2)
        layout.addWidget(chip2)

        reset_btn = QPushButton(" Reset Form")
        reset_btn.setIcon(get_svg_icon("refresh", "#94a3b8", 14))
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f1f5f9;
            }
        """)
        reset_btn.clicked.connect(self.reset_form)
        layout.addWidget(reset_btn)

        return banner

    def create_config_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #0e131f;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Panel Header
        p_head = QHBoxLayout()
        h_box = QVBoxLayout()
        h_box.setSpacing(2)
        h_title = QLabel("Configuration")
        h_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        h_sub = QLabel("Generation source parameters & prompt tuning")
        h_sub.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        h_box.addWidget(h_title)
        h_box.addWidget(h_sub)
        p_head.addLayout(h_box)
        p_head.addStretch()

        t_icon = QLabel()
        t_icon.setPixmap(get_svg_pixmap("tune", "#64748b", 18))
        t_icon.setStyleSheet("background: transparent; border: none;")
        p_head.addWidget(t_icon)
        layout.addLayout(p_head)

        # 1. Target Format Segmented Cards
        fmt_box = QVBoxLayout()
        fmt_box.setSpacing(6)
        fmt_lbl = QLabel("TARGET FORMAT")
        fmt_lbl.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        fmt_box.addWidget(fmt_lbl)

        btn_seg_frame = QFrame()
        btn_seg_frame.setStyleSheet("background-color: #131b2a; border: 1px solid #1e293b; border-radius: 8px; padding: 3px;")
        bs_layout = QHBoxLayout(btn_seg_frame)
        bs_layout.setContentsMargins(3, 3, 3, 3)
        bs_layout.setSpacing(6)

        self.btn_linkedin = QPushButton(" LinkedIn Post")
        self.btn_linkedin.setIcon(get_svg_icon("share", "#ffffff", 14))
        self.btn_linkedin.setCheckable(True)
        self.btn_linkedin.setChecked(True)
        self.btn_linkedin.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:checked {
                background-color: #2196f3;
                color: #ffffff;
            }
        """)
        self.btn_linkedin.clicked.connect(lambda: self.set_target_format("LinkedIn Post"))
        bs_layout.addWidget(self.btn_linkedin)

        self.btn_readme = QPushButton(" GitHub README")
        self.btn_readme.setIcon(get_svg_icon("terminal", "#94a3b8", 14))
        self.btn_readme.setCheckable(True)
        self.btn_readme.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:checked {
                background-color: #2196f3;
                color: #ffffff;
            }
        """)
        self.btn_readme.clicked.connect(lambda: self.set_target_format("GitHub README"))
        bs_layout.addWidget(self.btn_readme)

        fmt_box.addWidget(btn_seg_frame)
        layout.addLayout(fmt_box)

        # 2. Source Classification (4 Buttons Grid)
        self.source_cat_container = QWidget()
        self.source_cat_container.setStyleSheet("background: transparent; border: none;")
        sc_box = QVBoxLayout(self.source_cat_container)
        sc_box.setContentsMargins(0, 0, 0, 0)
        sc_box.setSpacing(6)

        sc_head = QHBoxLayout()
        sc_lbl = QLabel("SOURCE CLASSIFICATION")
        sc_lbl.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        sc_head.addWidget(sc_lbl)
        sc_head.addStretch()
        auto_lbl = QLabel("Auto-linked")
        auto_lbl.setStyleSheet("color: #2196f3; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500; background: transparent; border: none;")
        sc_head.addWidget(auto_lbl)
        sc_box.addLayout(sc_head)

        cat_grid = QHBoxLayout()
        cat_grid.setSpacing(6)
        self.cat_btn_group = QButtonGroup(self)
        self.cat_buttons = {}

        for cat_name in ["Project", "Certificate", "Hackathon", "Achievement"]:
            btn = QPushButton(cat_name if cat_name != "Achievement" else "Milestone")
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    color: #94a3b8;
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 6px 8px;
                }
                QPushButton:hover {
                    color: #f1f5f9;
                    background-color: #1e293b;
                }
                QPushButton:checked {
                    background-color: rgba(33, 150, 243, 0.2);
                    border-color: #2196f3;
                    color: #99cbff;
                }
            """)
            btn.clicked.connect(lambda _, c=cat_name: self.set_source_category(c))
            self.cat_btn_group.addButton(btn)
            self.cat_buttons[cat_name] = btn
            cat_grid.addWidget(btn)

        self.cat_buttons["Project"].setChecked(True)
        sc_box.addLayout(cat_grid)
        layout.addWidget(self.source_cat_container)

        # 3. Active Artifact Source Selector
        item_box = QVBoxLayout()
        item_box.setSpacing(6)

        item_head = QHBoxLayout()
        item_lbl = QLabel("ACTIVE ARTIFACT SOURCE")
        item_lbl.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        item_head.addWidget(item_lbl)
        item_head.addStretch()

        cache_lbl = QLabel("LOCAL CACHE")
        cache_lbl.setStyleSheet("color: #2196f3; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; background: transparent; border: none;")
        item_head.addWidget(cache_lbl)
        item_box.addLayout(item_head)

        self.item_combo = QComboBox()
        self.item_combo.setStyleSheet("""
            QComboBox {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                padding: 8px 12px;
            }
            QComboBox:focus {
                border-color: #2196f3;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #131b2a;
                color: #f1f5f9;
                selection-background-color: #1e293b;
                selection-color: #ffffff;
                border: 1px solid #1e293b;
            }
        """)
        self.item_combo.currentIndexChanged.connect(self.update_item_metadata)
        item_box.addWidget(self.item_combo)

        self.item_meta_lbl = QLabel("Select an artifact source above")
        self.item_meta_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        item_box.addWidget(self.item_meta_lbl)
        layout.addLayout(item_box)

        # 4. Target Directives (Instructions)
        inst_box = QVBoxLayout()
        inst_box.setSpacing(6)

        inst_head = QHBoxLayout()
        inst_lbl = QLabel("TARGET DIRECTIVES")
        inst_lbl.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        inst_head.addWidget(inst_lbl)
        inst_head.addStretch()

        self.inst_tok_lbl = QLabel("~0 tokens")
        self.inst_tok_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        inst_head.addWidget(self.inst_tok_lbl)
        inst_box.addLayout(inst_head)

        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText("e.g. Emphasize local SQLite architecture, target senior AI systems engineers, include a concise hook...")
        self.instructions_input.setPlainText("Highlight why local-first execution beats latency issues in cloud-only pipelines. Target principal AI systems engineers and maintain an authoritative, developer-centric tone.")
        self.instructions_input.setStyleSheet("""
            QTextEdit {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 10px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #2196f3;
            }
        """)
        self.instructions_input.setMaximumHeight(85)
        self.instructions_input.textChanged.connect(self.update_inst_token_count)
        self.update_inst_token_count()
        inst_box.addWidget(self.instructions_input)

        inst_foot = QHBoxLayout()
        inst_style = QLabel("Style: High-impact technical hook")
        inst_style.setStyleSheet("color: #64748b; font-family: 'Inter', sans-serif; font-size: 11px; background: transparent; border: none;")
        inst_foot.addWidget(inst_style)
        inst_foot.addStretch()

        clear_inst_btn = QPushButton("Reset")
        clear_inst_btn.setStyleSheet("background: transparent; border: none; color: #2196f3; font-family: 'Inter', sans-serif; font-size: 11px; padding: 0;")
        clear_inst_btn.clicked.connect(self.instructions_input.clear)
        inst_foot.addWidget(clear_inst_btn)
        inst_box.addLayout(inst_foot)

        layout.addLayout(inst_box)

        # 5. Posting Advisor Panel (Conditional LinkedIn)
        self.advisor_panel = QFrame()
        self.advisor_panel.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        adv_lay = QVBoxLayout(self.advisor_panel)
        adv_lay.setContentsMargins(12, 12, 12, 12)
        adv_lay.setSpacing(10)

        adv_head = QHBoxLayout()
        adv_icon = QLabel()
        adv_icon.setPixmap(get_svg_pixmap("brain", "#2196f3", 16))
        adv_icon.setStyleSheet("background: transparent; border: none;")
        adv_head.addWidget(adv_icon)

        adv_title = QLabel("Posting Advisor Engine")
        adv_title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        adv_head.addWidget(adv_title)
        adv_head.addStretch()

        self.advisor_btn = QPushButton(" Re-evaluate")
        self.advisor_btn.setIcon(get_svg_icon("refresh", "#2196f3", 12))
        self.advisor_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #2196f3;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.advisor_btn.clicked.connect(self.run_advisor)
        adv_head.addWidget(self.advisor_btn)
        adv_lay.addLayout(adv_head)

        # Verdict Badge
        self.advisor_verdict_badge = QLabel("READY TO EVALUATE")
        self.advisor_verdict_badge.setStyleSheet("""
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            background-color: #0b0f17;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 4px 8px;
        """)
        adv_lay.addWidget(self.advisor_verdict_badge)

        # Editorial Feedback Box
        self.advisor_feedback = QLabel("Click 'Re-evaluate' to generate AI critique and strategic angle.")
        self.advisor_feedback.setStyleSheet("""
            color: #94a3b8;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            line-height: 1.4;
            background-color: #0b0f17;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 8px;
        """)
        self.advisor_feedback.setWordWrap(True)
        adv_lay.addWidget(self.advisor_feedback)

        layout.addWidget(self.advisor_panel)

        layout.addStretch()
        return panel

    def create_editor_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #0b0f17;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Top Action Toolbar
        action_bar = QFrame()
        action_bar.setStyleSheet("background-color: #0c0e14; border: 1px solid #1e293b; border-radius: 8px; padding: 6px;")
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(8, 4, 8, 4)
        ab_layout.setSpacing(10)

        # Primary Generate Button
        self.generate_btn = QPushButton(" Generate Content")
        self.generate_btn.setIcon(get_svg_icon("sparkles", "#ffffff", 16))
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_content)
        ab_layout.addWidget(self.generate_btn)

        # Polish Tone Button
        self.polish_btn = QPushButton(" Polish Tone")
        self.polish_btn.setIcon(get_svg_icon("auto_fix_high", "#99cbff", 14))
        self.polish_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 7px 14px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                border-color: #2196f3;
            }
        """)
        self.polish_btn.clicked.connect(self.polish_tone)
        ab_layout.addWidget(self.polish_btn)

        # Wipe Buffer Button
        clear_btn = QPushButton()
        clear_btn.setIcon(get_svg_icon("delete", "#94a3b8", 14))
        clear_btn.setFixedSize(32, 32)
        clear_btn.setToolTip("Wipe Draft Buffer")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                border-color: rgba(239, 68, 68, 0.4);
            }
        """)
        clear_btn.clicked.connect(self.clear_editor)
        ab_layout.addWidget(clear_btn)

        ab_layout.addStretch()

        self.save_status_lbl = QLabel("Draft ready")
        self.save_status_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        ab_layout.addWidget(self.save_status_lbl)

        layout.addWidget(action_bar)

        # Document Surface Container
        doc_surface = QFrame()
        doc_surface.setStyleSheet("""
            QFrame {
                background-color: #0c0e14;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        ds_layout = QVBoxLayout(doc_surface)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        ds_layout.setSpacing(0)

        # Tabs Header
        tab_header = QFrame()
        tab_header.setFixedHeight(40)
        tab_header.setStyleSheet("background-color: #131b2a; border-bottom: 1px solid #1e293b; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        th_layout = QHBoxLayout(tab_header)
        th_layout.setContentsMargins(12, 4, 12, 4)
        th_layout.setSpacing(8)

        self.btn_tab_raw = QPushButton(" Markdown Editor")
        self.btn_tab_raw.setIcon(get_svg_icon("code", "#ffffff", 14))
        self.btn_tab_raw.setCheckable(True)
        self.btn_tab_raw.setChecked(True)
        self.btn_tab_raw.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 10px;
            }
            QPushButton:checked {
                background-color: #0b0f17;
                color: #2196f3;
            }
        """)
        self.btn_tab_raw.clicked.connect(lambda: self.switch_editor_tab(0))
        th_layout.addWidget(self.btn_tab_raw)

        self.btn_tab_preview = QPushButton(" Rich Preview")
        self.btn_tab_preview.setIcon(get_svg_icon("description", "#94a3b8", 14))
        self.btn_tab_preview.setCheckable(True)
        self.btn_tab_preview.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 10px;
            }
            QPushButton:checked {
                background-color: #0b0f17;
                color: #2196f3;
            }
        """)
        self.btn_tab_preview.clicked.connect(lambda: self.switch_editor_tab(1))
        th_layout.addWidget(self.btn_tab_preview)

        th_layout.addStretch()

        self.editor_stats_lbl = QLabel("0 words • 0 chars • 0 min read")
        self.editor_stats_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        th_layout.addWidget(self.editor_stats_lbl)

        ds_layout.addWidget(tab_header)

        # Editor & Preview Stack
        self.editor_stack = QStackedWidget()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Generated markdown content will appear here...")
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #0c0e14;
                border: none;
                color: #f1f5f9;
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 16px;
                line-height: 1.6;
            }
        """)
        self.editor.textChanged.connect(self.update_editor_stats)
        self.editor_stack.addWidget(self.editor)

        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)
        self.preview_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #0c0e14;
                border: none;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                padding: 20px;
                line-height: 1.6;
            }
        """)
        self.editor_stack.addWidget(self.preview_browser)

        ds_layout.addWidget(self.editor_stack, stretch=1)
        layout.addWidget(doc_surface, stretch=1)

        # Bottom Quick Utilities Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        copy_btn = QPushButton(" Copy to Clipboard")
        copy_btn.setIcon(get_svg_icon("content_copy", "#2196f3", 14))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding: 7px 14px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        bottom_bar.addWidget(copy_btn)

        export_md_btn = QPushButton(" Export .md")
        export_md_btn.setIcon(get_svg_icon("download", "#94a3b8", 14))
        export_md_btn.setStyleSheet("""
            QPushButton {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #94a3b8;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                color: #f1f5f9;
                border-color: #2196f3;
            }
        """)
        export_md_btn.clicked.connect(self.export_markdown)
        bottom_bar.addWidget(export_md_btn)

        bottom_bar.addStretch()

        self.tokens_lbl = QLabel("~0 output tokens")
        self.tokens_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        bottom_bar.addWidget(self.tokens_lbl)

        encoding_lbl = QLabel("UTF-8 • LF")
        encoding_lbl.setStyleSheet("""
            color: #64748b;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background-color: #131b2a;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 2px 6px;
        """)
        bottom_bar.addWidget(encoding_lbl)

        layout.addLayout(bottom_bar)
        return panel

    def set_target_format(self, mode: str):
        self.current_mode = mode
        if mode == "GitHub README":
            self.btn_linkedin.setChecked(False)
            self.btn_readme.setChecked(True)
            self.source_cat_container.hide()
            self.advisor_panel.hide()
            self.current_source_category = "Project"
        else:
            self.btn_linkedin.setChecked(True)
            self.btn_readme.setChecked(False)
            self.source_cat_container.show()
            self.advisor_panel.show()

        self.load_items()

    def set_source_category(self, cat_name: str):
        self.current_source_category = cat_name
        for name, btn in self.cat_buttons.items():
            btn.setChecked(name == cat_name)
        self.load_items()

    def load_items(self):
        self.item_combo.blockSignals(True)
        self.item_combo.clear()

        if self.current_mode == "GitHub README" or self.current_source_category == "Project":
            items = self.proj_repo.get_projects()
            for p in items:
                self.item_combo.addItem(p["name"], p["id"])
        elif self.current_source_category == "Certificate":
            items = self.cert_repo.get_certificates()
            for i in items:
                self.item_combo.addItem(i["title"], i["id"])
        elif self.current_source_category == "Hackathon":
            items = self.hack_repo.get_hackathons()
            for i in items:
                self.item_combo.addItem(i["event_name"], i["id"])
        elif self.current_source_category == "Achievement":
            items = self.prof_repo.get_achievements()
            for i in items:
                self.item_combo.addItem(i["title"], i["id"])

        self.item_combo.blockSignals(False)
        self.update_item_metadata()

    def update_item_metadata(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            self.item_meta_lbl.setText("No active items found in database")
            return

        source_type = "Project" if self.current_mode == "GitHub README" else self.current_source_category

        if source_type == "Project":
            p = self.proj_repo.get_project(item_id)
            if p:
                stack = p.get("technology_stack") or "N/A"
                status = p.get("status") or "Active"
                self.item_meta_lbl.setText(f"✓ {stack} • Status: {status} • Synced")
        elif source_type == "Certificate":
            c = self.cert_repo.get_certificate(item_id)
            if c:
                self.item_meta_lbl.setText(f"✓ Issuer: {c.get('issuer', 'N/A')} • Earned: {c.get('issue_date', 'N/A')}")
        elif source_type == "Hackathon":
            h = self.hack_repo.get_hackathon(item_id)
            if h:
                self.item_meta_lbl.setText(f"✓ Standing: {h.get('standing', 'Participant')} • Date: {h.get('date', 'N/A')}")
        else:
            a = self.prof_repo.get_achievement(item_id)
            if a:
                self.item_meta_lbl.setText(f"✓ Type: {a.get('type', 'Milestone')} • Date: {a.get('date_achieved', 'N/A')}")

    def update_inst_token_count(self):
        text = self.instructions_input.toPlainText().strip()
        tokens = len(text) // 4 if text else 0
        self.inst_tok_lbl.setText(f"~{tokens} tokens")

    def update_editor_stats(self):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        read_time = max(1, round(words / 200)) if words > 0 else 0
        self.editor_stats_lbl.setText(f"{words:,} words • {chars:,} chars • {read_time} min read")
        self.tokens_lbl.setText(f"~{chars // 4} output tokens")

    def switch_editor_tab(self, index: int):
        self.editor_stack.setCurrentIndex(index)
        if index == 0:
            self.btn_tab_raw.setChecked(True)
            self.btn_tab_preview.setChecked(False)
        else:
            self.btn_tab_raw.setChecked(False)
            self.btn_tab_preview.setChecked(True)
            self.preview_browser.setMarkdown(self.editor.toPlainText())

    def get_selected_item_data(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            return None, ""

        source_type = "Project" if self.current_mode == "GitHub README" else self.current_source_category
        data_str = ""

        if source_type == "Project":
            p = self.proj_repo.get_project(item_id)
            if p:
                data_str = f"Project '{p['name']}' using {p.get('technology_stack')}. Status: {p.get('status')}. {p.get('description')}"
        elif source_type == "Certificate":
            c = self.cert_repo.get_certificate(item_id)
            if c:
                data_str = f"Certificate '{c['title']}' from {c.get('issuer')}, earned {c.get('issue_date')}."
        elif source_type == "Hackathon":
            h = self.hack_repo.get_hackathon(item_id)
            if h:
                data_str = f"Hackathon '{h['event_name']}', Project: {h.get('project_submitted')}, Standing: {h.get('standing')}."
        else:
            a = self.prof_repo.get_achievement(item_id)
            if a:
                data_str = f"Achievement '{a['title']}' ({a.get('type')}): {a.get('description')} on {a.get('date_achieved')}."

        return source_type, data_str

    def run_advisor(self):
        source_type, data_str = self.get_selected_item_data()
        if not data_str:
            QMessageBox.warning(self, "Warning", "Please select an artifact item to evaluate.")
            return

        self.advisor_btn.setEnabled(False)
        self.advisor_verdict_badge.setText("ANALYZING REPUTATIONAL VALUE...")
        self.advisor_verdict_badge.setStyleSheet("""
            color: #fbbf24;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            background-color: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 4px;
            padding: 4px 8px;
        """)

        worker = AdvisorWorker(self.generator, source_type, data_str)
        worker.signals.finished.connect(self.on_advisor_done)
        worker.signals.error.connect(self.on_advisor_error)
        self.thread_pool.start(worker)

    def on_advisor_done(self, result):
        self.advisor_btn.setEnabled(True)
        rec = getattr(result, "recommendation", "EVALUATED")
        reason = getattr(result, "reason", "")

        if rec == "RECOMMENDED":
            self.advisor_verdict_badge.setText("RECOMMENDED: HIGH VALUE")
            self.advisor_verdict_badge.setStyleSheet("""
                color: #4edea3;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(78, 222, 163, 0.1);
                border: 1px solid rgba(78, 222, 163, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            """)
        elif "CHANGES" in rec:
            self.advisor_verdict_badge.setText("RECOMMENDED WITH CHANGES")
            self.advisor_verdict_badge.setStyleSheet("""
                color: #fbbf24;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(251, 191, 36, 0.1);
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            """)
        else:
            self.advisor_verdict_badge.setText("NOT RECOMMENDED")
            self.advisor_verdict_badge.setStyleSheet("""
                color: #f87171;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            """)

        self.advisor_feedback.setText(reason or "Evaluation finished. Check suggestions above before deploying.")

    def on_advisor_error(self, err):
        self.advisor_btn.setEnabled(True)
        self.advisor_verdict_badge.setText("ANALYSIS ERROR")
        self.advisor_feedback.setText(f"Analysis failed: {err}")

    def generate_content(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            QMessageBox.warning(self, "Warning", "Please select an artifact source item first.")
            return

        source_type = "Project" if self.current_mode == "GitHub README" else self.current_source_category
        inst = self.instructions_input.toPlainText()

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText(" Generating...")
        self.save_status_lbl.setText("Generating...")
        self.save_status_lbl.setStyleSheet("color: #fbbf24; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")

        worker = ContentGenWorker(self.generator, self.current_mode, source_type, item_id, inst)
        worker.signals.finished.connect(self.on_generate_done)
        worker.signals.error.connect(self.on_generate_error)
        self.thread_pool.start(worker)

    def on_generate_done(self, result):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText(" Generate Content")
        self.save_status_lbl.setText("Generated successfully")
        self.save_status_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        self.editor.setPlainText(result)
        if self.editor_stack.currentIndex() == 1:
            self.preview_browser.setMarkdown(result)

    def on_generate_error(self, err):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText(" Generate Content")
        self.save_status_lbl.setText("Generation error")
        self.save_status_lbl.setStyleSheet("color: #f87171; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        QMessageBox.critical(self, "Generation Failed", str(err))

    def polish_tone(self):
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Editor buffer is empty. Generate or write content first.")
            return

        self.polish_btn.setEnabled(False)
        self.polish_btn.setText(" Polishing...")
        worker = PolishWorker(self.db, text)
        worker.signals.finished.connect(self.on_polish_done)
        worker.signals.error.connect(self.on_polish_error)
        self.thread_pool.start(worker)

    def on_polish_done(self, polished_text):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText(" Polish Tone")
        self.editor.setPlainText(polished_text)
        if self.editor_stack.currentIndex() == 1:
            self.preview_browser.setMarkdown(polished_text)
        self.save_status_lbl.setText("Polished with AI")

    def on_polish_error(self, err):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText(" Polish Tone")
        QMessageBox.critical(self, "Polish Failed", str(err))

    def clear_editor(self):
        if self.editor.toPlainText().strip():
            reply = QMessageBox.question(
                self, "Wipe Buffer",
                "Are you sure you want to wipe the editor draft buffer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.editor.clear()
                self.preview_browser.clear()
                self.save_status_lbl.setText("Buffer wiped")

    def reset_form(self):
        self.instructions_input.setPlainText("Highlight why local-first execution beats latency issues in cloud-only pipelines. Target principal AI systems engineers and maintain an authoritative, developer-centric tone.")
        self.load_items()
        self.save_status_lbl.setText("Form reset")

    def copy_to_clipboard(self):
        text = self.editor.toPlainText()
        if not text.strip():
            return
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        self.save_status_lbl.setText("Copied to clipboard")
        QMessageBox.information(self, "Copied", "Content copied to clipboard.")

    def export_markdown(self):
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Warning", "Editor buffer is empty.")
            return

        default_name = "linkedin_post.md" if self.current_mode == "LinkedIn Post" else "README.md"
        path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", default_name, "Markdown Files (*.md);;All Files (*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.save_status_lbl.setText(f"Exported to {Path(path).name}")
                QMessageBox.information(self, "Exported", f"Successfully saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
