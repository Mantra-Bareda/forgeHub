from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDialog, QScrollArea, QFrame,
    QMessageBox, QGraphicsOpacityEffect, QButtonGroup
)
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Signal, QObject, QPropertyAnimation, QEasingCurve
from database.repository import MemoryRepository, ChatRepository
from app.memory.extractor import MemoryExtractor
from app.ui.components.icons import get_svg_icon, get_svg_pixmap


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


class ExtractorSignals(QObject):
    finished = Signal()
    error = Signal(str)


class ExtractorWorker(QRunnable):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.signals = ExtractorSignals()

    def run(self):
        try:
            repo = ChatRepository(self.db)
            history = repo.get_chat_history(limit=20)
            if not history:
                self.signals.finished.emit()
                return

            extractor = MemoryExtractor(self.db)
            extractor.extract_memories(history)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))


class ProfileSyncWorker(QRunnable):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.signals = ExtractorSignals()

    def run(self):
        try:
            extractor = MemoryExtractor(self.db)
            extractor.sync_from_profile()
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))


class EditMemoryDialog(QDialog):
    def __init__(self, memory: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Memory")
        self.setMinimumWidth(500)
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
            QLineEdit, QTextEdit, QComboBox {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #2196f3;
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
            QPushButton {
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Category and Importance Row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(14)

        cat_box = QVBoxLayout()
        cat_box.addWidget(QLabel("Category"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Profile", "Profile Sync", "Projects", "Achievements", "Conversations", "Other"])
        cur_cat = memory.get("category", "Other")
        idx = self.cat_combo.findText(cur_cat)
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        cat_box.addWidget(self.cat_combo)
        meta_row.addLayout(cat_box)

        imp_box = QVBoxLayout()
        imp_box.addWidget(QLabel("Importance"))
        self.imp_combo = QComboBox()
        self.imp_combo.addItems(["High", "Medium", "Normal"])
        cur_imp = memory.get("importance", "Normal")
        idx_imp = self.imp_combo.findText(cur_imp)
        if idx_imp >= 0:
            self.imp_combo.setCurrentIndex(idx_imp)
        imp_box.addWidget(self.imp_combo)
        meta_row.addLayout(imp_box)
        layout.addLayout(meta_row)

        # Content
        layout.addWidget(QLabel("Memory Content / Fact"))
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(110)
        self.content_input.setPlainText(memory.get("content", ""))
        layout.addWidget(self.content_input)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("background-color: #2196f3; color: #ffffff; border: none;")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "category": self.cat_combo.currentText(),
            "importance": self.imp_combo.currentText(),
            "content": self.content_input.toPlainText().strip()
        }


class MemoryCard(QFrame):
    def __init__(self, memory: dict, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.memory = memory
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.setStyleSheet("""
            MemoryCard {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
            MemoryCard:hover {
                border-color: rgba(33, 150, 243, 0.4);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        # Icon box based on category
        cat = memory.get("category", "Other")
        icon_name, icon_color = self.get_category_icon_meta(cat)

        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("background-color: #191b22; border-radius: 8px; border: 1px solid #1e293b;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap(icon_name, icon_color, 20))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        ib_layout.addWidget(icon_lbl)
        layout.addWidget(icon_box, alignment=Qt.AlignmentFlag.AlignTop)

        # Middle info column
        mid = QVBoxLayout()
        mid.setSpacing(8)

        # Badges row
        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)

        # Importance badge
        imp = memory.get("importance", "Normal")
        imp_badge = QLabel(f"{imp} Importance")
        if imp == "High":
            imp_badge.setStyleSheet("""
                color: #f87171;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        elif imp == "Medium":
            imp_badge.setStyleSheet("""
                color: #60a5fa;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(33, 150, 243, 0.15);
                border: 1px solid rgba(33, 150, 243, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        else:
            imp_badge.setStyleSheet("""
                color: #94a3b8;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 500;
                background-color: rgba(148, 163, 184, 0.12);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 4px;
                padding: 2px 8px;
            """)
        badges_row.addWidget(imp_badge)

        # Category badge
        cat_badge = QLabel(cat)
        cat_badge.setStyleSheet("""
            color: #cbd5e1;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background-color: #191b22;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 2px 8px;
        """)
        badges_row.addWidget(cat_badge)

        # Memory ID
        mem_id = memory.get("id", 0)
        id_lbl = QLabel(f"ID: mem_{mem_id:04x}" if isinstance(mem_id, int) else f"ID: mem_{mem_id}")
        id_lbl.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        badges_row.addWidget(id_lbl)
        badges_row.addStretch()
        mid.addLayout(badges_row)

        # Content text
        content_lbl = QLabel(memory.get("content", ""))
        content_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; background: transparent; border: none;")
        content_lbl.setWordWrap(True)
        mid.addWidget(content_lbl)

        layout.addLayout(mid, stretch=1)

        # Right action buttons
        actions = QHBoxLayout()
        actions.setSpacing(6)

        edit_btn = QPushButton()
        edit_btn.setIcon(get_svg_icon("edit", "#94a3b8", 16))
        edit_btn.setFixedSize(32, 32)
        edit_btn.setToolTip("Edit Memory")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QPushButton:hover {
                border-color: #2196f3;
            }
        """)
        edit_btn.clicked.connect(lambda: self.on_edit(self.memory))
        actions.addWidget(edit_btn)

        del_btn = QPushButton()
        del_btn.setIcon(get_svg_icon("delete", "#94a3b8", 16))
        del_btn.setFixedSize(32, 32)
        del_btn.setToolTip("Delete Memory")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b0f17;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                border-color: rgba(239, 68, 68, 0.4);
            }
        """)
        del_btn.clicked.connect(lambda: self.on_delete(self.memory["id"]))
        actions.addWidget(del_btn)

        layout.addLayout(actions)

    def get_category_icon_meta(self, category: str):
        c = category.lower()
        if "profile sync" in c:
            return "sync", "#4edea3"
        elif "profile" in c:
            return "badge", "#2196f3"
        elif "project" in c:
            return "folder_open", "#99cbff"
        elif "achievement" in c:
            return "award", "#fbbf24"
        elif "conversation" in c:
            return "chat", "#a78bfa"
        else:
            return "brain", "#2196f3"


class MemoryPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.repo = MemoryRepository(self.db_manager)
        self.thread_pool = QThreadPool.globalInstance()

        self.current_category = "all"
        self.all_memories = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll area for clean responsive layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0b0f17; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0b0f17;")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(32, 28, 32, 40)
        self.layout.setSpacing(24)

        # 1. Header Bar
        header_bar = self.create_header_bar()
        self.layout.addLayout(header_bar)

        # 2. Search & Metrics Toolbar
        toolbar = self.create_toolbar()
        self.layout.addLayout(toolbar)

        # 3. Category Filter Tabs
        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setSpacing(8)
        self.tabs_btn_group = QButtonGroup(self)
        self.tab_buttons = {}
        self.init_category_tabs()
        self.layout.addLayout(self.tabs_layout)

        # 4. Memories List Grid
        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(12)
        self.layout.addLayout(self.cards_container)

        # 5. Empty State Box
        self.empty_box = self.create_empty_state()
        self.layout.addWidget(self.empty_box)

        self.layout.addStretch()

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        self.load_memories()
        setup_page_animation(self)

    def create_header_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        top_title = QHBoxLayout()
        top_title.setSpacing(10)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("brain", "#2196f3", 24))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        top_title.addWidget(icon_lbl)

        title_lbl = QLabel("Persistent Memory Core")
        title_lbl.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 26px; font-weight: 700; background: transparent; border: none;")
        top_title.addWidget(title_lbl)
        top_title.addStretch()
        title_box.addLayout(top_title)

        sub_lbl = QLabel("The Context Compiler continuously extracts and deduplicates facts from your conversations.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        title_box.addWidget(sub_lbl)
        bar.addLayout(title_box)

        bar.addStretch()

        # Right Compiler Status Pill
        compiler_pill = QFrame()
        compiler_pill.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px 12px;
            }
        """)
        cp_layout = QHBoxLayout(compiler_pill)
        cp_layout.setContentsMargins(8, 6, 10, 6)
        cp_layout.setSpacing(8)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #4edea3; border-radius: 4px;")
        cp_layout.addWidget(dot)

        cp_text = QLabel("Compiler: Active")
        cp_text.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        cp_layout.addWidget(cp_text)
        bar.addWidget(compiler_pill)

        # Sync Button
        self.sync_profile_btn = QPushButton(" Sync from Profile && Projects")
        self.sync_profile_btn.setIcon(get_svg_icon("sync", "#ffffff", 16))
        self.sync_profile_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.sync_profile_btn.clicked.connect(self.trigger_profile_sync)
        bar.addWidget(self.sync_profile_btn)

        return bar

    def create_toolbar(self) -> QHBoxLayout:
        tb = QHBoxLayout()
        tb.setSpacing(16)

        # Search Bar
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #2196f3;
            }
        """)
        sf_layout = QHBoxLayout(search_frame)
        sf_layout.setContentsMargins(12, 0, 12, 0)
        sf_layout.setSpacing(8)

        s_icon = QLabel()
        s_icon.setPixmap(get_svg_pixmap("search", "#64748b", 16))
        s_icon.setStyleSheet("background: transparent; border: none;")
        sf_layout.addWidget(s_icon)

        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("background: transparent; border: none; color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 13px; padding: 8px 0;")
        self.search_input.setPlaceholderText("Search memories by keyword, fact, or tag...")
        self.search_input.textChanged.connect(self.on_search_changed)
        sf_layout.addWidget(self.search_input)

        clear_btn = QPushButton()
        clear_btn.setIcon(get_svg_icon("close", "#64748b", 14))
        clear_btn.setFixedSize(20, 20)
        clear_btn.setStyleSheet("background: transparent; border: none;")
        clear_btn.clicked.connect(self.search_input.clear)
        sf_layout.addWidget(clear_btn)

        tb.addWidget(search_frame, stretch=1)

        # Metric 1: Total Memories
        m1 = QFrame()
        m1.setStyleSheet("background-color: #131b2a; border: 1px solid #1e293b; border-radius: 8px; padding: 4px 12px;")
        m1_lay = QHBoxLayout(m1)
        m1_lay.setContentsMargins(10, 6, 10, 6)
        m1_lay.setSpacing(6)
        m1_lbl = QLabel("Total Memories:")
        m1_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        self.total_count_lbl = QLabel("0")
        self.total_count_lbl.setStyleSheet("color: #f1f5f9; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; background: transparent; border: none;")
        m1_lay.addWidget(m1_lbl)
        m1_lay.addWidget(self.total_count_lbl)
        tb.addWidget(m1)

        # Metric 2: Sync Status
        m2 = QFrame()
        m2.setStyleSheet("background-color: #131b2a; border: 1px solid #1e293b; border-radius: 8px; padding: 4px 12px;")
        m2_lay = QHBoxLayout(m2)
        m2_lay.setContentsMargins(10, 6, 10, 6)
        m2_lay.setSpacing(6)
        m2_lbl = QLabel("Sync Status:")
        m2_lbl.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 12px; background: transparent; border: none;")
        self.sync_status_lbl = QLabel("Up to date")
        self.sync_status_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        m2_lay.addWidget(m2_lbl)
        m2_lay.addWidget(self.sync_status_lbl)
        tb.addWidget(m2)

        return tb

    def init_category_tabs(self):
        categories = [
            ("all", "All Categories"),
            ("profile", "Profile"),
            ("profile sync", "Profile Sync"),
            ("projects", "Projects"),
            ("achievements", "Achievements"),
            ("conversations", "Conversations"),
            ("other", "Other")
        ]

        for code, label in categories:
            btn = QPushButton(f"{label} (0)")
            btn.setCheckable(True)
            btn.setProperty("cat_code", code)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #131b2a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    color: #94a3b8;
                    font-family: 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    color: #f1f5f9;
                    background-color: #1e293b;
                }
                QPushButton:checked {
                    background-color: #2196f3;
                    border-color: #2196f3;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda _, c=code: self.set_category_filter(c))
            self.tabs_btn_group.addButton(btn)
            self.tab_buttons[code] = btn
            self.tabs_layout.addWidget(btn)

        self.tab_buttons["all"].setChecked(True)
        self.tabs_layout.addStretch()

    def create_empty_state(self) -> QFrame:
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background-color: #131b2a;
                border: 1px dashed #1e293b;
                border-radius: 12px;
                padding: 40px;
            }
        """)
        layout = QVBoxLayout(box)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("search", "#64748b", 32))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        title = QLabel("No memories extracted yet")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #f1f5f9; font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(title)

        sub = QLabel("No memories match your search criteria or the compiler hasn't ingested items for this filter yet.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(sub)

        box.hide()
        return box

    def set_category_filter(self, code: str):
        self.current_category = code
        self.render_cards()

    def on_search_changed(self, text: str):
        self.render_cards()

    def load_memories(self):
        self.all_memories = self.repo.get_memories()
        self.update_tab_counts()
        self.render_cards()

    def update_tab_counts(self):
        total = len(self.all_memories)
        self.total_count_lbl.setText(str(total))

        counts = {
            "all": total,
            "profile": 0,
            "profile sync": 0,
            "projects": 0,
            "achievements": 0,
            "conversations": 0,
            "other": 0
        }

        for m in self.all_memories:
            c = (m.get("category") or "other").strip().lower()
            matched = False
            for key in ["profile sync", "profile", "projects", "achievements", "conversations"]:
                if key in c:
                    counts[key] += 1
                    matched = True
                    break
            if not matched:
                counts["other"] += 1

        labels = {
            "all": "All Categories",
            "profile": "Profile",
            "profile sync": "Profile Sync",
            "projects": "Projects",
            "achievements": "Achievements",
            "conversations": "Conversations",
            "other": "Other"
        }

        for code, btn in self.tab_buttons.items():
            btn.setText(f"{labels[code]} ({counts.get(code, 0)})")

    def render_cards(self):
        # Clear existing cards
        while self.cards_container.count():
            item = self.cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_input.text().strip().lower()

        filtered = []
        for m in self.all_memories:
            cat = (m.get("category") or "other").strip().lower()
            content = (m.get("content") or "").lower()

            # Category filter
            if self.current_category != "all":
                if self.current_category not in cat:
                    continue

            # Query filter
            if query and query not in content and query not in cat:
                continue

            filtered.append(m)

        if not filtered:
            self.empty_box.show()
        else:
            self.empty_box.hide()
            for m in filtered:
                card = MemoryCard(m, on_edit=self.edit_memory, on_delete=self.delete_memory)
                self.cards_container.addWidget(card)

    def edit_memory(self, memory: dict):
        dialog = EditMemoryDialog(memory, self)
        if dialog.exec():
            data = dialog.get_data()
            if data["content"]:
                self.repo.update_memory(
                    memory["id"],
                    data["category"],
                    data["content"],
                    data["importance"]
                )
                self.load_memories()

    def delete_memory(self, mem_id):
        reply = QMessageBox.question(
            self, "Delete Memory",
            "Are you sure you want to delete this memory item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_memory(mem_id)
            self.load_memories()

    def trigger_profile_sync(self):
        self.sync_profile_btn.setEnabled(False)
        self.sync_profile_btn.setText(" Syncing...")
        self.sync_status_lbl.setText("Syncing...")
        self.sync_status_lbl.setStyleSheet("color: #60a5fa; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; background: transparent; border: none;")

        worker = ProfileSyncWorker(self.db_manager)
        worker.signals.finished.connect(self.on_profile_sync_done)
        worker.signals.error.connect(self.on_profile_sync_error)
        self.thread_pool.start(worker)

    def on_profile_sync_done(self):
        self.sync_profile_btn.setEnabled(True)
        self.sync_profile_btn.setText(" Sync from Profile & Projects")
        self.sync_status_lbl.setText("Up to date")
        self.sync_status_lbl.setStyleSheet("color: #4edea3; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        self.load_memories()

    def on_profile_sync_error(self, err):
        self.sync_profile_btn.setEnabled(True)
        self.sync_profile_btn.setText(" Sync from Profile & Projects")
        self.sync_status_lbl.setText("Error")
        self.sync_status_lbl.setStyleSheet("color: #f87171; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        QMessageBox.warning(self, "Sync Failed", f"Could not sync from profile: {err}")
