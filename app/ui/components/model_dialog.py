from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QTreeWidget, 
                                 QTreeWidgetItem, QLineEdit, QCheckBox, QMessageBox, QWidget)
from PySide6.QtCore import Qt

class ModelManagementDialog(QDialog):
    def __init__(self, provider_name, key_id, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Manage Models: {provider_name} (Key #{key_id})")
        self.setMinimumSize(700, 500)
        self.provider_name = provider_name
        self.key_id = key_id
        self.db = db_manager
        
        layout = QVBoxLayout(self)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Enable", "Model Name (ID)", "Category", "RPM Limit", "RPD Limit"])
        self.tree.setColumnWidth(0, 80)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 120)
        layout.addWidget(self.tree)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.save_data)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        self.items = []
        self.load_models()
        
    def load_models(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.model_id, m.name, m.category, m.is_enabled, m.rpm_limit, m.rpd_limit
                FROM models m
                WHERE m.key_id = ?
                ORDER BY m.category, m.name
            """, (self.key_id,))
            
            for row in cursor.fetchall():
                item = QTreeWidgetItem([
                    "", 
                    f"{row['name']} ({row['model_id']})", 
                    row['category'] or "General", 
                    "", 
                    ""
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, row["id"])
                item.setData(1, Qt.ItemDataRole.UserRole, row["model_id"])
                
                # Checkbox
                chk = QCheckBox()
                chk.setChecked(bool(row["is_enabled"]))
                
                # Limits
                rpm = QLineEdit(str(row["rpm_limit"]) if row["rpm_limit"] else "")
                rpm.setPlaceholderText("API Default")
                rpd = QLineEdit(str(row["rpd_limit"]) if row["rpd_limit"] else "")
                rpd.setPlaceholderText("API Default")
                
                self.tree.addTopLevelItem(item)
                self.tree.setItemWidget(item, 0, chk)
                self.tree.setItemWidget(item, 3, rpm)
                self.tree.setItemWidget(item, 4, rpd)
                
                self.items.append((item, chk, rpm, rpd))
                
    def save_data(self):
        import json
        from pathlib import Path
        
        prefs_path = Path("database/models_prefs.json")
        prefs_path.parent.mkdir(exist_ok=True)
        
        prefs = {}
        if prefs_path.exists():
            try:
                with open(prefs_path, "r") as f:
                    prefs = json.load(f)
            except:
                pass
                
        if self.provider_name not in prefs:
            prefs[self.provider_name] = {}
            
        updates = []
        for item, chk, rpm, rpd in self.items:
            m_id = item.data(0, Qt.ItemDataRole.UserRole)
            model_id_str = item.data(1, Qt.ItemDataRole.UserRole)
            is_enabled = 1 if chk.isChecked() else 0
            
            r_val = rpm.text().strip()
            d_val = rpd.text().strip()
            
            rpm_val = int(r_val) if r_val.isdigit() else None
            rpd_val = int(d_val) if d_val.isdigit() else None
            
            updates.append((is_enabled, rpm_val, rpd_val, m_id))
            
            # Save to JSON structure
            prefs[self.provider_name][model_id_str] = {
                "is_enabled": is_enabled,
                "rpm_limit": rpm_val,
                "rpd_limit": rpd_val
            }
            
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("UPDATE models SET is_enabled = ?, rpm_limit = ?, rpd_limit = ? WHERE id = ?", updates)
            conn.commit()
            
        # Write JSON to disk
        with open(prefs_path, "w") as f:
            json.dump(prefs, f, indent=4)
            
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Success", "Model preferences and limits saved successfully.")
        self.accept()
