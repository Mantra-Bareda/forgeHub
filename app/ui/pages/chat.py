import html
from datetime import datetime
from PySide6.QtWidgets import ( QListWidget, QListWidgetItem, QDialog, 
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTextBrowser, QScrollArea, QFrame, QMessageBox,
    QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QShortcut, QKeySequence, QGuiApplication
from database.repository import ChatRepository, ProfileRepository
from app.ai import ModelRouter
from app.ui.components.icons import get_svg_icon, get_svg_pixmap
from app.core.palette import ColorPalette
from app.core.theme import get_current_palette, theme_manager


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


class InsightsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.expanded = False
        self.setStyleSheet(f"""
            InsightsPanel {{
                background-color: {self.palette.bg_app};
                border-bottom: 1px solid {self.palette.border_card};")
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 16, 24, 16)
        self.layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("brain", f"{self.palette.success}", 18))
        icon.setStyleSheet("background: transparent; border: none;")
        top.addWidget(icon)

        title = QLabel("AI Router Insights & Strategy")
        title.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        top.addWidget(title)
        top.addStretch()

        self.model_lbl = QLabel("Active Model: Dynamic Multi-Model Router")
        self.model_lbl.setStyleSheet(f"color: {self.palette.success}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        top.addWidget(self.model_lbl)
        self.layout.addLayout(top)

        # 3 Strategy Cards Row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card1 = self.create_insight_card("Recommended Tone", "Professional yet conversational thought-leadership")
        self.card2 = self.create_insight_card("Task Classification", "Technical Article & Social Hook Synthesis")
        self.card3 = self.create_insight_card("Router Heuristic", "Adaptive Reasoning Fallback Enabled")

        cards_row.addWidget(self.card1)
        cards_row.addWidget(self.card2)
        cards_row.addWidget(self.card3)
        self.layout.addLayout(cards_row)

        # Detailed Markdown Body
        self.body_browser = QTextBrowser()
        self.body_browser.setMaximumHeight(90)
        self.body_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 8px;
                color: {self.palette.fg_muted};
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 8px;
            }}
        """)
        self.layout.addWidget(self.body_browser)

        self.setMaximumHeight(0)
        self.hide()

        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(260)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def create_insight_card(self, title: str, text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{{{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        lay.addWidget(t)

        v = QLabel(text)
        v.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        v.setWordWrap(True)
        lay.addWidget(v)
        card._val_label = v

        return card

    def set_content(self, text: str):
        self.body_browser.setMarkdown(text)
        # Update cards dynamically if structured
        if "tone" in text.lower():
            self.card1._val_label.setText("Technical & High Impact")
        if "code" in text.lower():
            self.card2._val_label.setText("Code Architecture & Review")

    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.show()
            self.animation.setStartValue(0)
            self.animation.setEndValue(220)
            self.animation.start()
        else:
            self.animation.setStartValue(self.height())
            self.animation.setEndValue(0)
            self.animation.finished.connect(self._on_collapse_done)
            self.animation.start()

    def _on_collapse_done(self):
        if not self.expanded:
            self.hide()
            try:
                self.animation.finished.disconnect(self._on_collapse_done)
            except Exception:
                pass


    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        self.setStyleSheet(f"""
            InsightsPanel {{
                background-color: {self.palette.bg_app};
                border-bottom: 1px solid {self.palette.border_card};")
            }}
        """)
        
        # We need to update all labels and cards. Instead of keeping track of everything, we can do this via generic rules or by tracking children.
        # But wait, looking at the init, it's easier to just iterate over children.
        # Actually, let's keep it simple: we can set a global stylesheet on the widget itself that styles QLabel and QFrame.
        
        self.body_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 8px;
                color: {self.palette.fg_muted};
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 8px;
            }}
        """)
        
        # For the model_lbl:
        self.model_lbl.setStyleSheet(f"color: {self.palette.success}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        
        # For the cards:
        card_style = f"""
            QFrame {{{{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 8px;
                padding: 10px;
            }}
        """
        self.card1.setStyleSheet(card_style)
        self.card2.setStyleSheet(card_style)
        self.card3.setStyleSheet(card_style)
        
        # And update child labels of cards
        for card in [self.card1, self.card2, self.card3]:
            labels = card.findChildren(QLabel)
            if len(labels) >= 2:
                labels[0].setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
                labels[1].setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; background: transparent; border: none;")

class ChatWorkerSignals(QObject):
    finished = Signal(str, dict)
    error = Signal(str)


class ChatWorker(QRunnable):
    def __init__(self, router, prompt, context="", system_prompt=""):
        super().__init__()
        self.router = router
        self.prompt = prompt
        self.context = context
        self.system_prompt = system_prompt
        self.signals = ChatWorkerSignals()

    def run(self):
        try:
            result, metadata = self.router.route_request(
                prompt=self.prompt,
                category="General",
                system_prompt=self.system_prompt,
                context=self.context
            )
            self.signals.finished.emit(result, metadata)
        except Exception as e:
            self.signals.error.emit(str(e))


class ChatMessageWidget(QFrame):
    def __init__(self, role: str, content: str, metadata: dict = None, parent=None):
        super().__init__(parent)
        self.role = role
        self.palette = get_current_palette()
        self.setStyleSheet("background: transparent; border: none;")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 4, 0, 8)
        root_layout.setSpacing(6)

        time_str = datetime.now().strftime("%I:%M %p")

        if role == "user":
            # Right-aligned user layout
            top_meta = QHBoxLayout()
            top_meta.addStretch()

            lbl_user = QLabel(f"You • {time_str}")
            lbl_user.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            top_meta.addWidget(lbl_user)

            dot = QFrame()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background-color: {self.palette.success}; border-radius: 3px;")
            top_meta.addWidget(dot)
            root_layout.addLayout(top_meta)

            bubble_row = QHBoxLayout()
            bubble_row.addStretch()

            bubble = QFrame()
            bubble.setStyleSheet(f"""
                QFrame {{{{
                    background-color: {self.palette.border_card};")
                    border: 1px solid {self.palette.border_card};")
                    border-radius: 12px;
                }}
            """)
            b_lay = QVBoxLayout(bubble)
            b_lay.setContentsMargins(14, 10, 14, 10)

            msg_lbl = QLabel(content)
            msg_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 13px; line-height: 1.5; background: transparent; border: none;")
            msg_lbl.setWordWrap(True)
            msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            b_lay.addWidget(msg_lbl)

            bubble_row.addWidget(bubble, stretch=0)
            root_layout.addLayout(bubble_row)

        else:
            # Left-aligned Assistant layout
            top_meta = QHBoxLayout()
            dot = QFrame()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background-color: {self.palette.accent}; border-radius: 3px;")
            top_meta.addWidget(dot)

            provider = metadata.get("provider", "Forge AI") if metadata else "Forge Hub AI"
            model = metadata.get("model", "") if metadata else ""
            model_text = f"{provider} ({model})" if model else provider

            lbl_ai = QLabel(f"{model_text} • {time_str}")
            lbl_ai.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            top_meta.addWidget(lbl_ai)
            top_meta.addStretch()
            root_layout.addLayout(top_meta)

            bubble_row = QHBoxLayout()

            bubble = QFrame()
            bubble.setStyleSheet(f"""
                QFrame {{{{
                    background-color: {self.palette.bg_card};
                    border: 1px solid {self.palette.border_card};")
                    border-radius: 12px;
                }}
            """)
            b_lay = QVBoxLayout(bubble)
            b_lay.setContentsMargins(16, 14, 16, 14)
            b_lay.setSpacing(10)

            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            browser.setMarkdown(content)
            browser.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: transparent;
                    border: none;
                    color: {self.palette.fg_primary};
                    font-family: 'Inter', sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                }}
            """)
            # Adjust height to document size
            browser.document().adjustSize()
            doc_height = int(browser.document().size().height()) + 20
            browser.setMinimumHeight(min(max(doc_height, 40), 500))
            b_lay.addWidget(browser)

            # Metadata Footer
            footer = QHBoxLayout()
            footer.setSpacing(10)

            if metadata:
                task = metadata.get("task", "General Assistance")
                reason = metadata.get("reason", "Standard router heuristic")
                meta_txt = f"Task: {task} • {reason}"
            else:
                meta_txt = "Synchronized via Local Workspace Context"

            footer_lbl = QLabel(meta_txt)
            footer_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; background: transparent; border: none;")
            footer.addWidget(footer_lbl)
            footer.addStretch()

            copy_btn = QPushButton(" Copy")
            copy_btn.setIcon(get_svg_icon("content_copy", f"{self.palette.fg_muted}", 12))
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {self.palette.fg_muted};
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    color: {self.palette.fg_primary};
                }}
            """)
            copy_btn.clicked.connect(lambda: self.copy_content(content))
            footer.addWidget(copy_btn)

            b_lay.addLayout(footer)
            bubble_row.addWidget(bubble, stretch=1)
            bubble_row.addStretch()
            root_layout.addLayout(bubble_row)

    def copy_content(self, text: str):
        cb = QGuiApplication.clipboard()
        cb.setText(text)


    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        dots = [w for w in self.findChildren(QFrame) if w.width() == 6 and w.height() == 6]
        for dot in dots:
            if self.role == "user":
                dot.setStyleSheet(f"background-color: {self.palette.success}; border-radius: 3px;")
            else:
                dot.setStyleSheet(f"background-color: {self.palette.accent}; border-radius: 3px;")
                
        frames = self.findChildren(QFrame)
        for frame in frames:
            if frame is self or frame in dots:
                continue
            if self.role == "user":
                frame.setStyleSheet(f"""
                    QFrame {{{{
                        background-color: {self.palette.border_card};")
                        border: 1px solid {self.palette.border_card};")
                        border-radius: 12px;
                    }}
                """)
            else:
                frame.setStyleSheet(f"""
                    QFrame {{{{
                        background-color: {self.palette.bg_card};
                        border: 1px solid {self.palette.border_card};")
                        border-radius: 12px;
                    }}
                """)

        labels = self.findChildren(QLabel)
        for lbl in labels:
            text = lbl.text()
            if "•" in text and ("You" in text or "AI" in text or "Forge" in text or "Router" in text or "(" in text):
                lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
            elif "Task:" in text or "Synchronized" in text:
                lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 10px; background: transparent; border: none;")
            else:
                lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 13px; line-height: 1.5; background: transparent; border: none;")
                
        browsers = self.findChildren(QTextBrowser)
        for browser in browsers:
            browser.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: transparent;
                    border: none;
                    color: {self.palette.fg_primary};
                    font-family: 'Inter', sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                }}
            """)
            
        buttons = self.findChildren(QPushButton)
        for btn in buttons:
            btn.setIcon(get_svg_icon("content_copy", f"{self.palette.fg_muted}", 12))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {self.palette.fg_muted};
                    font-family: 'Inter', sans-serif;
                    font-size: 11px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    color: {self.palette.fg_primary};
                }}
            """)

class BackgroundExtractor(QRunnable):
    def __init__(self, db_mgr, hist):
        super().__init__()
        self.db = db_mgr
        self.hist = hist

    def run(self):
        try:
            from app.memory.extractor import MemoryExtractor
            extractor = MemoryExtractor(self.db)
            extractor.extract_memories(self.hist)
        except Exception:
            pass


class AIChatPage(QWidget):
    def __init__(self, db_manager, chat_context="general"):
        super().__init__()
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.palette = get_current_palette()
        self.db = db_manager
        self.repo = ChatRepository(self.db)
        self.chat_context = chat_context
        self.router = ModelRouter(self.db)

        from app.ai.compiler import ContextCompiler
        self.compiler = ContextCompiler(self.db)
        self.thread_pool = QThreadPool.globalInstance()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar
        top_bar = self.create_top_bar()
        root_layout.addWidget(top_bar)

        # 2. Collapsible Insights Drawer
        self.insights_panel = InsightsPanel(self)
        root_layout.addWidget(self.insights_panel)

        # 3. Main Chat History Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.palette.bg_app};
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.palette.border_card};")
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.palette.accent};
            }}
        """)

        self.history_container = QWidget()
        self.history_container.setStyleSheet(f"background-color: {self.palette.bg_app};")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(32, 20, 32, 20)
        self.history_layout.setSpacing(16)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.history_container)
        root_layout.addWidget(self.scroll_area, stretch=1)

        # 4. Docked Input Bottom Bar
        bottom_dock = self.create_input_dock()
        root_layout.addWidget(bottom_dock)

        # Keyboard shortcuts
        self.shortcut_enter = QShortcut(QKeySequence("Ctrl+Return"), self.input_box)
        self.shortcut_enter.activated.connect(self.send_message)
        self.shortcut_enter2 = QShortcut(QKeySequence("Ctrl+Enter"), self.input_box)
        self.shortcut_enter2.activated.connect(self.send_message)

        self.load_history()
        setup_page_animation(self)

    def create_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setMinimumWidth(0)
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"""
            QFrame {{{{
                background-color: {self.palette.bg_app};
                border-bottom: 1px solid {self.palette.border_card};")
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # Title & Context
        title_box = QHBoxLayout()
        title_box.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("chat", f"{self.palette.accent}", 18))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        title_box.addWidget(icon_lbl)

        ws_title = QLabel("AI Workspace")
        ws_title.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        title_box.addWidget(ws_title)

        slash = QLabel("/")
        slash.setStyleSheet(f"color: {self.palette.fg_muted}; font-size: 13px; background: transparent; border: none;")
        title_box.addWidget(slash)

        # Context Indicator Pill
        self.context_pill = QFrame()
        self.context_pill.setStyleSheet(f"""
            QFrame {{{{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 12px;
                padding: 2px 8px;
            }}
        """)
        cp_lay = QHBoxLayout(self.context_pill)
        cp_lay.setContentsMargins(6, 2, 6, 2)
        cp_lay.setSpacing(6)

        dot = QFrame()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background-color: {self.palette.success}; border-radius: 3px;")
        cp_lay.addWidget(dot)

        layout.addLayout(title_box)
        layout.addStretch()

        # Right Action Buttons
        self.insights_toggle_btn = QPushButton(" Insights ✨")
        self.insights_toggle_btn.setIcon(get_svg_icon("sparkles", f"{self.palette.success}", 13))
        self.insights_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 12px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.border_card};")
                border-color: {self.palette.accent};
            }}
        """)
        self.insights_toggle_btn.clicked.connect(self.toggle_insights)
        layout.addWidget(self.insights_toggle_btn)

        self.history_btn = QPushButton(" Old Chats")
        self.history_btn.setIcon(get_svg_icon("restore", f"{self.palette.fg_primary}", 13))
        self.history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.border_card};")
                border-color: {self.palette.accent};
            }}
        """)
        self.history_btn.clicked.connect(self.show_history_dialog)
        layout.addWidget(self.history_btn)

        new_sess_btn = QPushButton(" New Chat")
        new_sess_btn.setIcon(get_svg_icon("refresh", f"{self.palette.fg_primary}", 13))
        new_sess_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 6px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
        """)
        new_sess_btn.clicked.connect(self.new_session)
        layout.addWidget(new_sess_btn)

        return bar

    def create_input_dock(self) -> QFrame:
        dock = QFrame()
        dock.setStyleSheet(f"""
            QFrame {{
                background-color: {self.palette.bg_app};
                border-top: 1px solid {self.palette.border_card};")
            }}
        """)
        layout = QVBoxLayout(dock)
        layout.setContentsMargins(32, 14, 32, 12)
        layout.setSpacing(8)

        # Input box with inside button
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{{{
                background-color: {self.palette.bg_card};
                border: 1px solid {self.palette.border_card};")
                border-radius: 12px;
            }}
            QFrame:focus-within {{
                border-color: {self.palette.accent};
            }}
        """)
        ic_layout = QHBoxLayout(input_container)
        ic_layout.setContentsMargins(14, 8, 10, 8)
        ic_layout.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Ask Forge Hub for help with your projects... (Ctrl+Enter to send)")
        self.input_box.setFixedHeight(48)
        self.input_box.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }}
        """)
        # Ensure placeholder color is handled gracefully
        palette = self.input_box.palette()
        from PySide6.QtGui import QColor
        palette.setColor(self.input_box.backgroundRole(), QColor(0, 0, 0, 0))
        self.input_box.setPalette(palette)
        ic_layout.addWidget(self.input_box, stretch=1)

        self.send_btn = QPushButton(" Send")
        self.send_btn.setIcon(get_svg_icon("send", f"{self.palette.fg_primary}", 14))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.palette.accent};
                border: none;
                border-radius: 8px;
                color: {self.palette.fg_primary};
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {self.palette.accent};
            }}
            QPushButton:disabled {{
                background-color: {self.palette.border_card};")
                color: {self.palette.fg_muted};
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        ic_layout.addWidget(self.send_btn)
        layout.addWidget(input_container)

        # Telemetry bottom line
        telemetry = QHBoxLayout()
        telemetry.setSpacing(12)

        self.model_status_lbl = QLabel("Model: Auto-routed • Router: Active")
        self.model_status_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        telemetry.addWidget(self.model_status_lbl)
        telemetry.addStretch()

        feat_lbl = QLabel("Markdown • Code Highlighting Enabled")
        feat_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        telemetry.addWidget(feat_lbl)
        layout.addLayout(telemetry)

        return dock

    def toggle_insights(self):
        self.insights_panel.toggle()
        if self.insights_panel.expanded:
            self.insights_toggle_btn.setText(" Close AI Insights ✨")
        else:
            self.insights_toggle_btn.setText(" View AI Insights ✨")

    def set_project(self, project_id: int):
        self.project_id = project_id
        self.current_session_id = None
        self.load_history()

    def show_history_dialog(self):
        sessions = self.repo.get_chat_sessions(project_id=getattr(self, 'project_id', None), chat_context=self.chat_context)
        if not sessions:
            QMessageBox.information(self, "No History", "There are no old chats available for this context.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Old Chats")
        dialog.setMinimumSize(400, 300)
        dialog.setStyleSheet(f"background-color: {self.palette.bg_app}; color: {self.palette.fg_primary};")
        
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.palette.bg_input};
                border: 1px solid {self.palette.border_card};")
                border-radius: 6px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {self.palette.border_card};")
            }}
            QListWidget::item:selected {{
                background-color: {self.palette.accent_bg};
                color: {self.palette.fg_primary};
            }}
        """)
        
        for sess in sessions:
            first_msg = sess['content']
            # Take first 5-8 words
            words = first_msg.split()
            title = " ".join(words[:8]) + ("..." if len(words) > 8 else "")
            
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, sess['session_id'])
            list_widget.addItem(item)
            
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"background-color: {self.palette.bg_card}; padding: 6px 14px; border-radius: 4px;")
        cancel_btn.clicked.connect(dialog.reject)
        
        load_btn = QPushButton("Load Selected")
        load_btn.setStyleSheet(f"background-color: {self.palette.accent}; color: {self.palette.bg_app}; padding: 6px 14px; border-radius: 4px; font-weight: bold;")
        load_btn.clicked.connect(dialog.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(load_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = list_widget.selectedItems()
            if selected_items:
                session_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
                self.current_session_id = session_id
                self.load_history()

    def new_session(self):
        import uuid
        self.current_session_id = str(uuid.uuid4())
        self.load_history()

    def load_insights(self):
        repo = ProfileRepository(self.db)
        insights = ""
        if self.chat_context == "linkedin":
            data = repo.get_linkedin_data()
            insights = data.get("ai_insights") or ""
        elif self.chat_context == "github":
            data = repo.get_github_data()
            insights = data.get("ai_insights") or ""

        if insights:
            self.insights_panel.set_content(insights)
        else:
            self.insights_panel.set_content("*No insights yet. Save your profile in LinkedIn or GitHub to generate them.*")

    def load_history(self):
        self.load_insights()

        # Clear layout
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        history = self.repo.get_chat_history(chat_context=self.chat_context)
        if not history:
            self.show_empty_state()
            return

        for msg in history:
            self.add_message_bubble(msg["role"], msg["content"])

    def show_empty_state(self):
        empty_box = QFrame()
        empty_box.setStyleSheet("background: transparent; border: none; margin-top: 40px;")
        eb_layout = QVBoxLayout(empty_box)
        eb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eb_layout.setSpacing(10)

        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"background-color: {self.palette.bg_card}; border-radius: 24px; border: 1px solid {self.palette.border_card};")

        if_lay = QVBoxLayout(icon_frame)
        if_lay.setContentsMargins(0, 0, 0, 0)
        i_lbl = QLabel()
        i_lbl.setPixmap(get_svg_pixmap("chat", f"{self.palette.accent}", 24))
        i_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        i_lbl.setStyleSheet("background: transparent; border: none;")
        if_lay.addWidget(i_lbl)
        eb_layout.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        t_lbl = QLabel("Forge Hub AI Assistance Initialized")
        t_lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eb_layout.addWidget(t_lbl)

        s_lbl = QLabel("Your chat workspace is securely synced with local context. Ask questions, generate content, or inspect code.")
        s_lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        s_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eb_layout.addWidget(s_lbl)

        self.history_layout.addWidget(empty_box)

    def add_message_bubble(self, role: str, content: str, metadata: dict = None):
        bubble = ChatMessageWidget(role, content, metadata)
        self.history_layout.addWidget(bubble)
        QTimer.singleShot(60, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def get_recent_context(self):
        history = self.repo.get_chat_history(limit=6, project_id=getattr(self, 'project_id', None), chat_context=self.chat_context, session_id=getattr(self, 'current_session_id', None))
        context_str = ""
        for msg in reversed(history):
            context_str += f"{msg['role'].upper()}: {msg['content']}\n"
        return context_str

    def send_message(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText(" Thinking...")

        # If empty state was showing, reload cleanly
        if self.history_layout.count() == 1 and isinstance(self.history_layout.itemAt(0).widget(), QFrame):
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.add_message_bubble("user", text)
        self.repo.save_message("user", text, project_id=getattr(self, 'project_id', None), chat_context=self.chat_context, session_id=getattr(self, 'current_session_id', None))

        context = self.get_recent_context()
        system_prompt = self.compiler.compile_system_prompt()

        worker = ChatWorker(self.router, text, context, system_prompt)
        worker.signals.finished.connect(self.on_ai_response)
        worker.signals.error.connect(self.on_ai_error)
        self.thread_pool.start(worker)

        # Background memory extraction occasionally
        from app.core.config import load_config
        config = load_config()
        if config.get("auto_memory_extraction", True):
            history = self.repo.get_chat_history(limit=20, chat_context=self.chat_context)
            user_messages = [m for m in history if m["role"] == "user"]
            if len(user_messages) > 0 and len(user_messages) % 5 == 0:
                self.thread_pool.start(BackgroundExtractor(self.db, history))

    def on_ai_response(self, response_text: str, metadata: dict):
        self.send_btn.setEnabled(True)
        self.send_btn.setText(" Send")

        self.add_message_bubble("assistant", response_text, metadata)
        self.repo.save_message("assistant", response_text, project_id=getattr(self, 'project_id', None), chat_context=self.chat_context, session_id=getattr(self, 'current_session_id', None))

        provider = metadata.get("provider", "AI")
        model = metadata.get("model", "")
        self.model_status_lbl.setText(f"Model: {provider} ({model}) • Router: Optimal Latency")
        QTimer.singleShot(60, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def on_ai_error(self, error_msg: str):
        self.send_btn.setEnabled(True)
        self.send_btn.setText(" Send")

        friendly_error = error_msg
        if "No available AI models" in error_msg:
            friendly_error = "It looks like you haven't configured any AI providers yet. Please go to the 'AI Providers' section and add an API key."
        elif "rate-limit" in error_msg.lower() or "429" in error_msg:
            friendly_error = "The AI provider is currently rate-limiting requests. Please wait a moment and try again."
        elif "context too small" in error_msg.lower():
            friendly_error = "The conversation has gotten too long for the selected AI model to handle. Try starting a new session or using a model with a larger context window."
        elif "network" in error_msg.lower() or "connect" in error_msg.lower() or "timeout" in error_msg.lower():
            friendly_error = "Network connection failed. Forge Hub is running in offline mode. AI features require an active internet connection or a local model."

        QMessageBox.critical(self, "AI Routing Error", friendly_error)

    def minimumSizeHint(self):
        return QSize(300, 200)


    def apply_theme_colors(self, pal: ColorPalette):
        self.palette = pal
        
        if hasattr(self, 'insights_panel'):
            self.insights_panel.apply_theme_colors(pal)
            
        if hasattr(self, 'history_container'):
            self.history_container.setStyleSheet(f"background-color: {self.palette.bg_app};")
            
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {self.palette.bg_app};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: transparent;
                    width: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {self.palette.border_card};")
                    border-radius: 2px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {self.palette.accent};
                }}
            """)
            
        if hasattr(self, 'history_layout'):
            for i in range(self.history_layout.count()):
                item = self.history_layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    if isinstance(w, ChatMessageWidget):
                        w.apply_theme_colors(pal)
                    elif type(w) is QFrame:
                        # Handle empty state
                        for child in w.findChildren(QFrame):
                            if child.width() == 48 and child.height() == 48:
                                child.setStyleSheet(f"background-color: {self.palette.bg_card}; border-radius: 24px; border: 1px solid {self.palette.border_card};")
                        for lbl in w.findChildren(QLabel):
                            if "Initialized" in lbl.text():
                                lbl.setStyleSheet(f"color: {self.palette.fg_primary}; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
                            elif "synced" in lbl.text():
                                lbl.setStyleSheet(f"color: {self.palette.fg_muted}; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")

        # We can also quickly update the input dock and top bar styling that might be stale:
        # Re-style main QFrames to ensure backgrounds are updated
        for frame in self.findChildren(QFrame):
            # Only update those we can safely identify or fallback to general styles if needed.
            # Here we just rely on specific properties if they need an update.
            pass

