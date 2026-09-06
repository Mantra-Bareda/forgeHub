from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QLineEdit, 
                                 QScrollArea, QFrame, QGroupBox, QMessageBox, QCheckBox, QFormLayout)
from PySide6.QtCore import QThread, Signal, QObject
from database.repository import ProviderRepository
from providers import get_provider

class ProviderTestWorker(QThread):
    finished_signal = Signal(str, int, bool, str)

    def __init__(self, provider_name, api_key, slot, db_manager):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.slot = slot
        self.db_manager = db_manager
        
    def run(self):
        provider = None
        try:
            provider = get_provider(self.provider_name, self.api_key)
            is_valid = provider.test_key()
            if is_valid:
                models = provider.discover_models()
                if models:
                    from database.repository import ProviderRepository
                    repo = ProviderRepository(self.db_manager)
                    repo.save_models(self.provider_name, models)
                self.finished_signal.emit(self.provider_name, self.slot, True, "Connected & Verified")
            else:
                self.finished_signal.emit(self.provider_name, self.slot, False, provider.get_status())
        except Exception as e:
            self.finished_signal.emit(self.provider_name, self.slot, False, f"Error: {str(e)}")
        finally:
            if provider:
                provider.close()

class ProviderCard(QGroupBox):
    def __init__(self, provider_data, test_callback, remove_callback, models_callback):
        super().__init__(provider_data["name"])
        self.provider_data = provider_data
        self.test_callback = test_callback
        self.remove_callback = remove_callback
        self.models_callback = models_callback
        
        main_layout = QVBoxLayout(self)
        
        self.slots = {}
        for slot in [1, 2]:
            slot_data = provider_data["keys"].get(slot, {})
            slot_widget = self.create_slot_ui(slot, slot_data)
            main_layout.addWidget(slot_widget)
        
        models = self.models_callback(self.provider_data["name"])
        if models:
            display_models = models[:8]
            models_text = ", ".join([m["name"] for m in display_models])
            if len(models) > 8:
                models_text += f", ... and {len(models) - 8} more"
                
            models_lbl = QLabel(f"Discovered Models ({len(models)}): {models_text}")
            models_lbl.setWordWrap(True)
            models_lbl.setStyleSheet("color: #555; font-size: 10px;")
            main_layout.addWidget(models_lbl)
        
    def create_slot_ui(self, slot, slot_data):
        box = QGroupBox(f"Key Slot {slot}")
        layout = QVBoxLayout(box)
        
        self.slots[slot] = {}
        enable_cb = QCheckBox("Enable Key")
        enable_cb.setChecked(slot_data.get("enabled", 1) == 1)
        self.slots[slot]["enable_cb"] = enable_cb
        layout.addWidget(enable_cb)
        
        form = QFormLayout()
        
        disp_name_input = QLineEdit()
        disp_name_input.setText(slot_data.get("display_name", f"{self.provider_data['name']} Key {slot}"))
        form.addRow("Name:", disp_name_input)
        self.slots[slot]["display_name"] = disp_name_input
        
        key_input = QLineEdit()
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key = slot_data.get("api_key", "")
        if api_key and api_key != "••••••••":
            key_input.setText("••••••••")
        elif api_key:
            key_input.setText(api_key)
        form.addRow("API Key:", key_input)
        self.slots[slot]["api_key"] = key_input
        
        status_text = slot_data.get("status", "Not Configured")
        status_label = QLabel(f"Status: {status_text}")
        if "Valid" in status_text or "Connected" in status_text:
            status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_label.setStyleSheet("color: #888;")
        form.addRow("", status_label)
        self.slots[slot]["status_label"] = status_label
        
        last_tested = slot_data.get("last_tested", "Never")
        tested_label = QLabel(f"Last tested: {last_tested}")
        tested_label.setStyleSheet("color: #777; font-size: 10px;")
        form.addRow("", tested_label)
        self.slots[slot]["tested_label"] = tested_label
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        test_btn = QPushButton("Test & Save")
        test_btn.clicked.connect(lambda _, s=slot: self.on_test_clicked(s))
        self.slots[slot]["test_btn"] = test_btn
        btn_layout.addWidget(test_btn)
        
        if slot_data.get("id"):
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, s=slot, kid=slot_data["id"]: self.on_remove_clicked(s, kid))
            btn_layout.addWidget(remove_btn)
            
        layout.addLayout(btn_layout)
        return box
        
    def on_test_clicked(self, slot):
        key = self.slots[slot]["api_key"].text().strip()
        disp_name = self.slots[slot]["display_name"].text().strip()
        enabled = 1 if self.slots[slot]["enable_cb"].isChecked() else 0
        
        if not key:
            QMessageBox.warning(self, "Error", "API Key cannot be empty.")
            return
            
        real_key = key
        if key == "••••••••":
            real_key = self.provider_data["keys"].get(slot, {}).get("api_key", "")
            
        if not real_key or real_key == "••••••••":
             QMessageBox.warning(self, "Error", "Cannot test masked key without entering it first.")
             return

        self.slots[slot]["test_btn"].setEnabled(False)
        self.slots[slot]["status_label"].setText("Status: Testing...")
        self.slots[slot]["status_label"].setStyleSheet("color: orange;")
        self.test_callback(self.provider_data["name"], real_key, slot, disp_name, enabled, self)

    def on_remove_clicked(self, slot, key_id):
        reply = QMessageBox.question(self, "Remove Key", "Are you sure you want to remove this key?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.remove_callback(self.provider_data["name"], slot, key_id)

class AIProvidersPage(QWidget):
    status_updated = Signal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProviderRepository(self.db)
        
        self.cards = {}
        self.active_threads = set()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("AI Providers & API Keys")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(header)
        
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
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        providers = self.repo.get_providers()
        for p in providers:
            card = ProviderCard(p, self.run_test, self.remove_key, self.repo.get_models)
            self.cards[p["name"]] = card
            self.layout.addWidget(card)
            
        self.layout.addStretch()

    def run_test(self, provider_name, api_key, slot, disp_name, enabled, card_widget):
        worker = ProviderTestWorker(provider_name, api_key, slot, self.db)
        self.active_threads.add(worker)
        worker.finished_signal.connect(lambda name, slt, succ, msg: self.on_test_finished(name, api_key, slt, disp_name, enabled, succ, msg, worker))
        worker.start()
        
    def on_test_finished(self, provider_name, api_key, slot, disp_name, enabled, success, status_msg, worker):
        if worker in self.active_threads:
            self.active_threads.remove(worker)
            worker.deleteLater()
            
        card = self.cards.get(provider_name)
        if card:
            card.slots[slot]["test_btn"].setEnabled(True)
            card.slots[slot]["status_label"].setText(f"Status: {status_msg}")
            
            self.status_updated.emit(f"AI Status: {provider_name} - {status_msg}")
            
            if success:
                card.slots[slot]["status_label"].setStyleSheet("color: green; font-weight: bold;")
                self.repo.save_api_key(provider_name, api_key, status_msg, slot, disp_name, enabled)
                QMessageBox.information(self, "Success", f"Successfully authenticated with {provider_name}.")
            else:
                card.slots[slot]["status_label"].setStyleSheet("color: red; font-weight: bold;")
                QMessageBox.warning(self, "Validation Failed", f"Failed to authenticate with {provider_name}.\nError: {status_msg}")
            
            self.load_providers()
            
    def remove_key(self, provider_name, slot, key_id):
        self.repo.delete_api_key(key_id)
        self.load_providers()
