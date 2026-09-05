from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                                 QGroupBox, QFormLayout, QPushButton, QMessageBox, QTabWidget, QCheckBox, QSlider, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from app.core.theme import apply_theme
from app.core.config import load_config
import json
from pathlib import Path

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
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

    def setup_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance Group
        appearance_group = QGroupBox("Appearance")
        form = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "dark", "light"])
        
        config = load_config()
        current_theme = config.get("theme", "system")
        idx = self.theme_combo.findText(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
            
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        form.addRow("Theme:", self.theme_combo)
        layout.addWidget(appearance_group)
        
        # Data Group
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
        
        temp_slider = QSlider(Qt.Orientation.Horizontal)
        temp_slider.setRange(0, 100)
        temp_slider.setValue(70)
        form.addRow("Temperature:", temp_slider)
        
        system_prompt = QPushButton("Edit Base System Prompt")
        form.addRow("System Prompt:", system_prompt)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "AI Behavior")

    def setup_memory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Memory Management")
        form = QFormLayout(group)
        
        auto_memory = QCheckBox("Enable Automatic Memory Extraction")
        auto_memory.setChecked(True)
        form.addRow("", auto_memory)
        
        clear_memory = QPushButton("Clear All Memory")
        form.addRow("Danger Zone:", clear_memory)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Memory")

    def setup_privacy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Privacy & Telemetry")
        form = QFormLayout(group)
        
        telemetry = QCheckBox("Allow Anonymous Usage Statistics")
        telemetry.setChecked(False)
        form.addRow("", telemetry)
        
        local_only = QCheckBox("Enforce Local-Only Models")
        local_only.setChecked(False)
        form.addRow("", local_only)
        
        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Privacy")

    def change_theme(self, theme_name):
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_name)
        
        # Save to config
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.json"
        config = load_config()
        config["theme"] = theme_name
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass
            
    def backup_database(self):
        try:
            from database.connection import DatabaseManager
            db = DatabaseManager()
            db.backup("database/forgehub_backup.db")
            QMessageBox.information(self, "Success", "Database backup created successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Backup failed: {str(e)}")
