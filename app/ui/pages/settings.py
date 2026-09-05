from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                                 QGroupBox, QFormLayout, QPushButton, QMessageBox, 
                                 QTabWidget, QCheckBox, QSlider, QInputDialog, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from app.core.theme import apply_theme
from app.core.config import load_config, save_config

class SettingsPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.config = load_config()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel("Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.setup_general_tab()
        self.setup_ai_behavior_tab()
        self.setup_memory_tab()
        self.setup_privacy_tab()

    def update_config(self, key, value):
        self.config[key] = value
        save_config(self.config)

    def setup_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        appearance_group = QGroupBox("Appearance")
        form = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "dark", "light"])
        
        current_theme = self.config.get("theme", "system")
        idx = self.theme_combo.findText(current_theme)
        if idx >= 0: self.theme_combo.setCurrentIndex(idx)
            
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        form.addRow("Theme:", self.theme_combo)
        layout.addWidget(appearance_group)
        
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        data_layout.addWidget(backup_btn)
        
        layout.addWidget(data_group)
        layout.addStretch()
        self.tabs.addTab(tab, "General")

    def setup_ai_behavior_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("AI Behavior Settings")
        form = QFormLayout(group)
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(self.config.get("ai_temperature", 70))
        self.temp_slider.valueChanged.connect(lambda v: self.update_config("ai_temperature", v))
        form.addRow("Temperature (0-100):", self.temp_slider)
        
        system_prompt = QPushButton("Edit Base System Prompt")
        system_prompt.clicked.connect(self.edit_system_prompt)
        form.addRow("System Prompt:", system_prompt)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "AI Behavior")
        
    def edit_system_prompt(self):
        current = self.config.get("base_system_prompt", "You are Forge Hub, a professional AI manager designed to help the user with project management and professional tasks.")
        text, ok = QInputDialog.getMultiLineText(self, "Edit Base System Prompt", "Prompt:", current)
        if ok and text:
            self.update_config("base_system_prompt", text.strip())
            QMessageBox.information(self, "Saved", "Base system prompt updated.")

    def setup_memory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Memory Management")
        form = QFormLayout(group)
        
        self.auto_memory = QCheckBox("Enable Automatic Memory Extraction")
        self.auto_memory.setChecked(self.config.get("auto_memory_extraction", True))
        self.auto_memory.stateChanged.connect(lambda state: self.update_config("auto_memory_extraction", bool(state)))
        form.addRow("", self.auto_memory)
        
        clear_memory = QPushButton("Clear All Memory")
        clear_memory.setStyleSheet("background-color: #D32F2F; color: white;")
        clear_memory.clicked.connect(self.clear_memory)
        form.addRow("Danger Zone:", clear_memory)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Memory")
        
    def clear_memory(self):
        reply = QMessageBox.question(self, "Clear All Memory", "Are you sure you want to permanently delete all extracted AI memories? This cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from database.repository import MemoryRepository
            MemoryRepository(self.db).clear_all_memories()
            QMessageBox.information(self, "Cleared", "All memories have been deleted.")

    def setup_privacy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Privacy & Telemetry")
        form = QFormLayout(group)
        
        self.telemetry = QCheckBox("Allow Anonymous Usage Statistics")
        self.telemetry.setChecked(self.config.get("telemetry", False))
        self.telemetry.stateChanged.connect(lambda state: self.update_config("telemetry", bool(state)))
        form.addRow("", self.telemetry)
        
        self.local_only = QCheckBox("Enforce Local-Only Models (e.g. Ollama/LMStudio)")
        self.local_only.setChecked(self.config.get("local_models_only", False))
        self.local_only.stateChanged.connect(lambda state: self.update_config("local_models_only", bool(state)))
        form.addRow("", self.local_only)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Privacy")

    def change_theme(self, theme_name):
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_name)
        self.update_config("theme", theme_name)
            
    def backup_database(self):
        try:
            self.db.backup("database/forgehub_backup.db")
            QMessageBox.information(self, "Success", "Database backup created successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Backup failed: {str(e)}")
