from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                                 QGroupBox, QFormLayout, QPushButton, QMessageBox)
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
        
    def change_theme(self, theme_name):
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_name)
        
        # Save to config
        config_path = Path("config.json")
        config = load_config()
        config["theme"] = theme_name
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
    def backup_database(self):
        try:
            from database.connection import DatabaseManager
            db = DatabaseManager()
            db.backup("database/forgehub_backup.db")
            QMessageBox.information(self, "Success", "Database backup created successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Backup failed: {str(e)}")
