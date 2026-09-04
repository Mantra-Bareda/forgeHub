from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QLineEdit, 
                                 QScrollArea, QFrame, QGroupBox, QMessageBox)
from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject
from database.repository import ProviderRepository
from providers import GeminiProvider, GroqProvider, MistralProvider, CerebrasProvider

class WorkerSignals(QObject):
    finished = Signal(str, bool, str, list)  # provider_name, success, status_msg, models

class ProviderTestWorker(QRunnable):
    def __init__(self, provider_name, api_key):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.signals = WorkerSignals()
        
    def run(self):
        adapter_class = None
        if self.provider_name == "Gemini": adapter_class = GeminiProvider
        elif self.provider_name == "Groq": adapter_class = GroqProvider
        elif self.provider_name == "Mistral": adapter_class = MistralProvider
        elif self.provider_name == "Cerebras": adapter_class = CerebrasProvider
        
        if not adapter_class:
            self.signals.finished.emit(self.provider_name, False, "Unknown Provider", [])
            return
            
        provider = adapter_class(self.api_key)
        
        try:
            is_valid = provider.test_key()
            if is_valid:
                models = provider.discover_models()
                self.signals.finished.emit(self.provider_name, True, "Connected & Verified", models)
            else:
                self.signals.finished.emit(self.provider_name, False, provider.get_status(), [])
        except Exception as e:
            self.signals.finished.emit(self.provider_name, False, f"Error: {str(e)}", [])

class ProviderCard(QGroupBox):
    def __init__(self, provider_data, test_callback):
        super().__init__(provider_data["name"])
        self.provider_data = provider_data
        self.test_callback = test_callback
        
        layout = QVBoxLayout(self)
        
        # Status Label
        self.status_label = QLabel(f"Status: {provider_data.get('status', 'Not Configured')}")
        if "Valid" in self.status_label.text() or "Connected" in self.status_label.text():
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #888;")
            
        layout.addWidget(self.status_label)
        
        # Key Input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setText(provider_data.get("api_key", ""))
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.test_btn = QPushButton("Test & Save Key")
        self.test_btn.clicked.connect(self.on_test_clicked)
        btn_layout.addWidget(self.test_btn)
        
        layout.addLayout(btn_layout)
        
    def on_test_clicked(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "API Key cannot be empty.")
            return
            
        self.test_btn.setEnabled(False)
        self.status_label.setText("Status: Testing...")
        self.status_label.setStyleSheet("color: orange;")
        self.test_callback(self.provider_data["name"], key, self)

class AIProvidersPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProviderRepository(self.db)
        self.thread_pool = QThreadPool.globalInstance()
        
        self.cards = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("AI Providers & API Keys")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(15)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        self.load_providers()
        
    def load_providers(self):
        # Clear existing
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        providers = self.repo.get_providers()
        for p in providers:
            card = ProviderCard(p, self.run_test)
            self.cards[p["name"]] = card
            self.layout.addWidget(card)
            
        self.layout.addStretch()

    def run_test(self, provider_name, api_key, card_widget):
        worker = ProviderTestWorker(provider_name, api_key)
        worker.signals.finished.connect(lambda name, succ, msg, models: self.on_test_finished(name, api_key, succ, msg, models))
        self.thread_pool.start(worker)
        
    def on_test_finished(self, provider_name, api_key, success, status_msg, models):
        card = self.cards.get(provider_name)
        if card:
            card.test_btn.setEnabled(True)
            card.status_label.setText(f"Status: {status_msg}")
            if success:
                card.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.repo.save_api_key(provider_name, api_key, status_msg)
                self.repo.save_models(provider_name, models)
                
                # Show popup info
                QMessageBox.information(self, "Success", f"Successfully authenticated with {provider_name}.\nDiscovered {len(models)} models.")
            else:
                card.status_label.setStyleSheet("color: red; font-weight: bold;")
                QMessageBox.warning(self, "Validation Failed", f"Failed to authenticate with {provider_name}.\nError: {status_msg}")
