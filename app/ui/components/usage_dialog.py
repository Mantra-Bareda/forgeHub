from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton)
from PySide6.QtCore import Qt
from database.repository import ProviderRepository

class UsageStatisticsDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detailed AI Usage Statistics")
        self.setMinimumSize(800, 500)
        self.db = db_manager
        
        layout = QVBoxLayout(self)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Provider / Model", "Requests (Last Min)", "Requests (Today)", "Total Requests", "RPM Limit (API)", "RPD Limit (API)"])
        self.tree.setColumnWidth(0, 250)
        layout.addWidget(self.tree)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.load_data()
        
    def load_data(self):
        repo = ProviderRepository(self.db)
        stats = repo.get_model_usage_stats()
        
        for provider, models in stats.items():
            prov_item = QTreeWidgetItem([provider, "", "", "", "", ""])
            prov_item.setFlags(prov_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            for model_id, data in models.items():
                mod_item = QTreeWidgetItem([
                    data["display_name"],
                    str(data["req_last_min"]),
                    str(data["req_last_day"]),
                    str(data["total_requests"]),
                    data["rpm"],
                    data["rpd"]
                ])
                prov_item.addChild(mod_item)
                
            self.tree.addTopLevelItem(prov_item)
            prov_item.setExpanded(True)
