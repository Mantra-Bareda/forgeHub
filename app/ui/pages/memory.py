from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QScrollArea, QFrame, 
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
        
        self.extract_btn = QPushButton("Extract Memories from Recent Chat")
        self.extract_btn.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        self.extract_btn.clicked.connect(self.trigger_extraction)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.extract_btn)
        self.layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("The Context Compiler continuously extracts and deduplicates facts from your conversations.")
        subtitle.setStyleSheet("color: #888; font-style: italic;")
        self.layout.addWidget(subtitle)
        
        # List of memories
        self.memory_list = QListWidget()
        self.memory_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.memory_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.memory_list)
        
        self.load_memories()
        
    def load_memories(self):
        self.memory_list.clear()
        memories = self.repo.get_memories()
        for m in memories:
            item = QListWidgetItem(f"[{m['importance']}] {m['category']}: {m['content']}")
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            if m["importance"] == "High":
                item.setForeground(Qt.GlobalColor.red)
            elif m["importance"] == "Medium":
                item.setForeground(Qt.GlobalColor.yellow)
                
            self.memory_list.addItem(item)
            
    def trigger_extraction(self):
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("Extracting...")
        
        worker = ExtractorWorker(self.db_manager)
        worker.signals.finished.connect(self.on_extracted)
        worker.signals.error.connect(self.on_error)
        self.thread_pool.start(worker)
        
    def on_extracted(self):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("Extract Memories from Recent Chat")
        self.load_memories()
        
    def on_error(self, err):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("Extract Memories from Recent Chat")
        QMessageBox.warning(self, "Extraction Failed", f"Could not extract memories: {err}")
        
    def show_context_menu(self, position):
        from PySide6.QtWidgets import QMenu
        item = self.memory_list.itemAt(position)
        if not item: return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Memory")
        action = menu.exec(self.memory_list.mapToGlobal(position))
        
        if action == delete_action:
            self.repo.delete_memory(item.data(Qt.ItemDataRole.UserRole))
            self.load_memories()
