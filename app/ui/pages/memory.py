from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, 
                                 QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Signal, QObject
from database.repository import MemoryRepository, ChatRepository
from app.memory.extractor import MemoryExtractor

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

class MemoryPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.repo = MemoryRepository(self.db_manager)
        self.thread_pool = QThreadPool.globalInstance()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Header layout
        header_layout = QHBoxLayout()
        header = QLabel("Persistent Memory Core")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.sync_profile_btn = QPushButton("Sync from Profile & Projects")
        self.sync_profile_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.sync_profile_btn.clicked.connect(self.trigger_profile_sync)
        header_layout.addWidget(self.sync_profile_btn)
        
        self.layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("The Context Compiler continuously extracts and deduplicates facts from your conversations.")
        subtitle.setStyleSheet("color: #888; font-style: italic;")
        self.layout.addWidget(subtitle)
        
        # Search bar
        from PySide6.QtWidgets import QLineEdit
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search memories...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)
        
        # Tabs for categories
        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        self.categories = ["Profile", "Profile Sync", "Projects", "Achievements", "Conversations", "Other"]
        self.lists = {}
        for cat in self.categories:
            list_w = QListWidget()
            list_w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            list_w.customContextMenuRequested.connect(self.show_context_menu)
            self.lists[cat] = list_w
            self.tabs.addTab(list_w, cat)
            
        self.empty_state_label = QLabel("No memories extracted yet.")
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setStyleSheet("color: #888; font-style: italic;")
        self.layout.addWidget(self.empty_state_label)
        
        self.load_memories()
        
    def on_search_changed(self, text):
        self.load_memories(query=text)

    def load_memories(self, query=""):
        for list_w in self.lists.values():
            list_w.clear()
            
        if query:
            memories = self.repo.search_memories(query)
        else:
            memories = self.repo.get_memories()
        if not memories:
            self.empty_state_label.show()
            self.tabs.hide()
            return
            
        self.empty_state_label.hide()
        self.tabs.show()
        
        for m in memories:
            cat = m['category'] if m['category'] in self.lists else "Other"
            item = QListWidgetItem(f"[{m['importance']}] {m['content']}")
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            if m["importance"] == "High":
                item.setForeground(Qt.GlobalColor.red)
            elif m["importance"] == "Medium":
                item.setForeground(Qt.GlobalColor.darkYellow)
                
            self.lists[cat].addItem(item)
            

    def trigger_profile_sync(self):
        self.sync_profile_btn.setEnabled(False)
        self.sync_profile_btn.setText("Syncing...")
        
        worker = ProfileSyncWorker(self.db_manager)
        worker.signals.finished.connect(self.on_profile_sync_done)
        worker.signals.error.connect(self.on_profile_sync_error)
        self.thread_pool.start(worker)
        
    def on_profile_sync_done(self):
        self.sync_profile_btn.setEnabled(True)
        self.sync_profile_btn.setText("Sync from Profile & Projects")
        self.load_memories()
        
    def on_profile_sync_error(self, err):
        self.sync_profile_btn.setEnabled(True)
        self.sync_profile_btn.setText("Sync from Profile & Projects")
        QMessageBox.warning(self, "Sync Failed", f"Could not sync from profile: {err}")
        
    def show_context_menu(self, position):
        from PySide6.QtWidgets import QMenu, QInputDialog
        list_w = self.sender()
        if not list_w: return
        
        item = list_w.itemAt(position)
        if not item: return
        
        menu = QMenu()
        edit_action = menu.addAction("Edit Memory")
        delete_action = menu.addAction("Delete Memory")
        action = menu.exec(list_w.mapToGlobal(position))
        
        mem_id = item.data(Qt.ItemDataRole.UserRole)
        
        if action == delete_action:
            self.repo.delete_memory(mem_id)
            self.load_memories()
        elif action == edit_action:
            # We need to parse out the category/importance or just let them edit the content.
            # E.g. text is "[Medium] user likes apples"
            current_text = item.text()
            bracket_end = current_text.find("]")
            if bracket_end != -1:
                content = current_text[bracket_end+2:]
            else:
                content = current_text
                
            new_text, ok = QInputDialog.getText(self, "Edit Memory", "New Content:", text=content)
            if ok and new_text:
                # Find the existing record to get its category and importance
                for mem in self.repo.get_memories():
                    if mem["id"] == mem_id:
                        self.repo.update_memory(mem_id, mem["category"], new_text, mem["importance"])
                        break
                self.load_memories()
