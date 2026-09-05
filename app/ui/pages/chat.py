from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QTextEdit, 
                                 QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject, QTimer
from database.repository import ChatRepository
from app.ai import ModelRouter

class ChatWorkerSignals(QObject):
    finished = Signal(str)
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
            # We request a General model, ModelRouter will automatically select the best available
            result, provider, model = self.router.route_request(
                prompt=self.prompt,
                category="General",
                system_prompt=self.system_prompt,
                context=self.context
            )
            self.signals.finished.emit(f"{result}\n\n<small style='color: #888;'><i>Powered by {provider} ({model})</i></small>")
        except Exception as e:
            self.signals.error.emit(str(e))

class ChatMessageWidget(QFrame):
    def __init__(self, role, content):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        
        header = QLabel("You" if role == "user" else "Forge Hub AI")
        header.setStyleSheet("font-weight: bold; color: #4CAF50;" if role == "user" else "font-weight: bold; color: #2196F3;")
        layout.addWidget(header)
        
        msg = QLabel(content)
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(msg)
        
        if role == "user":
            self.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 8px; margin: 5px; } QLabel { color: #E0E0E0; }")
        else:
            self.setStyleSheet("QFrame { background-color: #1e1e1e; border-radius: 8px; margin: 5px; border: 1px solid #333; } QLabel { color: #E0E0E0; }")

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
        except Exception as e:
            pass

class AIChatPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ChatRepository(self.db)
        self.router = ModelRouter(self.db)
        
        from app.ai.compiler import ContextCompiler
        self.compiler = ContextCompiler(self.db)
        
        self.thread_pool = QThreadPool.globalInstance()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        self.header = QLabel("AI Workspace (Powered by Dynamic Router)")
        self.header.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.header)
        
        # Chat History Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.history_container)
        
        self.layout.addWidget(self.scroll_area, stretch=1)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setMaximumHeight(80)
        self.input_box.setPlaceholderText("Ask Forge Hub for help with your projects...")
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumHeight(80)
        self.send_btn.setMinimumWidth(80)
        self.send_btn.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white;")
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        
        self.layout.addLayout(input_layout)
        
        from PySide6.QtGui import QShortcut, QKeySequence
        self.shortcut_enter = QShortcut(QKeySequence("Ctrl+Return"), self.input_box)
        self.shortcut_enter.activated.connect(self.send_message)
        self.shortcut_enter2 = QShortcut(QKeySequence("Ctrl+Enter"), self.input_box)
        self.shortcut_enter2.activated.connect(self.send_message)
        
        self.load_history()

    def add_message_bubble(self, role, content):
        if hasattr(self, 'empty_state') and self.empty_state:
            self.empty_state.deleteLater()
            self.empty_state = None
            
        bubble = ChatMessageWidget(role, content)
        self.history_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def load_history(self):
        # Clear layout
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        history = self.repo.get_chat_history()
        if not history:
            self.empty_state = QLabel("Start a conversation! The AI context router will automatically select the best model for your queries.")
            self.empty_state.setStyleSheet("color: #888; font-style: italic; margin-top: 50px;")
            self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(self.empty_state)
            return
            
        for msg in history:
            self.add_message_bubble(msg["role"], msg["content"])
            
    def get_recent_context(self):
        """Fetches the last few messages to provide context to the AI."""
        history = self.repo.get_chat_history(limit=5)
        context_str = ""
        for msg in history:
            context_str += f"{msg['role'].upper()}: {msg['content']}\n"
        return context_str

    def send_message(self):
        text = self.input_box.toPlainText().strip()
        if not text: return
        
        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Thinking...")
        
        # Add to UI and DB
        self.add_message_bubble("user", text)
        self.repo.save_message("user", text)
        
        # Get context
        context = self.get_recent_context()
        system_prompt = self.compiler.compile_system_prompt()
        
        # Start chat worker
        worker = ChatWorker(self.router, text, context, system_prompt)
        worker.signals.finished.connect(self.on_ai_response)
        worker.signals.error.connect(self.on_ai_error)
        self.thread_pool.start(worker)
        
        # Auto-extract memories in the background occasionally
        history = self.repo.get_chat_history(limit=20)
        # If user just sent the 5th, 10th, 15th message etc.
        user_messages = [m for m in history if m["role"] == "user"]
        if len(user_messages) > 0 and len(user_messages) % 5 == 0:
            self.thread_pool.start(BackgroundExtractor(self.db, history))
        
    def on_ai_response(self, response_text):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        
        self.add_message_bubble("assistant", response_text)
        self.repo.save_message("assistant", response_text)
        
        # Scroll down again after a tiny delay to ensure UI updated
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def on_ai_error(self, error_msg):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        
        friendly_error = error_msg
        if "No available AI models" in error_msg:
            friendly_error = "It looks like you haven't configured any AI providers yet. Please go to the 'AI Providers' section and add an API key."
        elif "rate-limit" in error_msg.lower() or "429" in error_msg:
            friendly_error = "The AI provider is currently rate-limiting requests. Please wait a moment and try again."
        elif "context too small" in error_msg.lower():
            friendly_error = "The conversation has gotten too long for the selected AI model to handle. Try starting a new topic or using a model with a larger context window."
            
        QMessageBox.critical(self, "AI Routing Error", friendly_error)
