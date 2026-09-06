from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QPushButton, QTabWidget, 
                                 QListWidget, QListWidgetItem, QLineEdit, 
                                 QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, Signal
from database.repository import ProjectRepository

class ProjectDetailWidget(QWidget):
    back_requested = Signal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.repo = ProjectRepository(self.db)
        self.project_id = None
        self.project_data = None
        
        self.layout = QVBoxLayout(self)
        
        # Header layout
        self.header_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.back_requested.emit)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.header_layout.addWidget(self.back_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_project)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("color: red;")
        self.delete_btn.clicked.connect(self.delete_project)
        
        self.header_layout.addWidget(self.edit_btn)
        self.header_layout.addWidget(self.delete_btn)
        self.layout.addLayout(self.header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Overview Tab
        self.overview_tab = QWidget()
        self.overview_layout = QVBoxLayout(self.overview_tab)
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.tech_label = QLabel()
        self.status_label = QLabel()
        self.overview_layout.addWidget(QLabel("<b>Description:</b>"))
        self.overview_layout.addWidget(self.desc_label)
        self.overview_layout.addWidget(QLabel("<b>Technology:</b>"))
        self.overview_layout.addWidget(self.tech_label)
        self.overview_layout.addWidget(QLabel("<b>Status:</b>"))
        self.overview_layout.addWidget(self.status_label)
        self.overview_layout.addStretch()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Tasks Tab
        self.tasks_tab = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_tab)
        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self.toggle_task_status)
        self.tasks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tasks_list.customContextMenuRequested.connect(self.show_task_context_menu)
        
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Add a new task...")
        self.new_task_input.returnPressed.connect(self.add_task)
        self.tasks_layout.addWidget(self.tasks_list)
        self.tasks_layout.addWidget(self.new_task_input)
        self.tabs.addTab(self.tasks_tab, "Tasks")
        
        # Documentation Tab
        self.docs_tab = QWidget()
        self.docs_layout = QVBoxLayout(self.docs_tab)
        self.docs_editor = QTextEdit()
        self.docs_save_btn = QPushButton("Save Documentation")
        self.docs_save_btn.clicked.connect(self.save_docs)
        self.docs_layout.addWidget(self.docs_editor)
        self.docs_layout.addWidget(self.docs_save_btn)
        self.tabs.addTab(self.docs_tab, "Documentation")
        
        # Activity Tab
        self.activity_tab = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_tab)
        self.activity_list = QListWidget()
        self.activity_layout.addWidget(self.activity_list)
        self.tabs.addTab(self.activity_tab, "Activity")
        
        # AI Actions Tab
        self.ai_tab = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_tab)
        
        self.analyze_btn = QPushButton("Analyze Project")
        self.improve_readme_btn = QPushButton("Improve README")
        self.linkedin_post_btn = QPushButton("Create LinkedIn Post")
        self.ask_ai_btn = QPushButton("Ask AI")
        
        self.analyze_btn.clicked.connect(lambda: self.handle_ai_action("Analyze Project"))
        self.improve_readme_btn.clicked.connect(lambda: self.handle_ai_action("Improve README"))
        self.linkedin_post_btn.clicked.connect(lambda: self.handle_ai_action("Create LinkedIn Post"))
        self.ask_ai_btn.clicked.connect(lambda: self.handle_ai_action("Ask AI"))
        
        self.ai_layout.addWidget(self.analyze_btn)
        self.ai_layout.addWidget(self.improve_readme_btn)
        self.ai_layout.addWidget(self.linkedin_post_btn)
        self.ai_layout.addWidget(self.ask_ai_btn)
        self.ai_layout.addStretch()
        self.tabs.addTab(self.ai_tab, "AI")
        
    def handle_ai_action(self, action_name):
        has_ai = False
        try:
            from database.repository import ProviderRepository
            provider_repo = ProviderRepository(self.db)
            if provider_repo.get_available_models():
                has_ai = True
        except Exception:
            pass
            
        if not has_ai:
            QMessageBox.warning(self, "AI Error", "AI provider not configured. Please configure an AI provider in Settings first.")
            return
            
        QMessageBox.information(self, "AI Action", f"Action '{action_name}' triggered for project '{self.project_data.get('name', 'Unknown')}'. (AI integration pending)")

    def load_project(self, project_id):
        self.project_id = project_id
        self.project_data = self.repo.get_project(project_id)
        
        if not self.project_data:
            return
            
        self.title_label.setText(self.project_data["name"])
        self.desc_label.setText(self.project_data.get("description") or "No description provided.")
        self.tech_label.setText(self.project_data.get("technology_stack") or "None")
        self.status_label.setText(self.project_data.get("status") or "Unknown")
        
        self.load_tasks()
        self.load_docs()
        self.load_activities()
        
    def load_tasks(self):
        self.tasks_list.clear()
        tasks = self.repo.get_tasks(self.project_id)
        for t in tasks:
            item = QListWidgetItem(f"[{t['status']}] {t['title']}")
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.tasks_list.addItem(item)
            
    def toggle_task_status(self, item):
        task = item.data(Qt.ItemDataRole.UserRole)
        new_status = "Completed" if task["status"] == "Pending" else "Pending"
        self.repo.update_task_status(task["id"], new_status)
        self.load_tasks()
        self.load_activities()
        
    def show_task_context_menu(self, position):
        from PySide6.QtWidgets import QMenu
        item = self.tasks_list.itemAt(position)
        if not item: return
        task = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Task")
        action = menu.exec(self.tasks_list.mapToGlobal(position))
        
        if action == delete_action:
            self.repo.delete_task(task["id"])
            self.load_tasks()
            self.load_activities()
            
    def add_task(self):
        title = self.new_task_input.text().strip()
        if title:
            self.repo.add_task(self.project_id, title)
            self.new_task_input.clear()
            self.load_tasks()
            self.load_activities()
            
    def load_docs(self):
        docs = self.repo.get_documents(self.project_id)
        if docs:
            # Assuming a primary README document for simplicity
            self.docs_editor.setPlainText(docs[0].get("content", ""))
        else:
            self.docs_editor.clear()
            
    def save_docs(self):
        content = self.docs_editor.toPlainText()
        self.repo.save_document(self.project_id, "README.md", content)
        self.load_activities()
        QMessageBox.information(self, "Success", "Documentation saved successfully.")
        
    def load_activities(self):
        self.activity_list.clear()
        activities = self.repo.get_activities(self.project_id)
        for act in activities:
            item = QListWidgetItem(f"[{act['created_at']}] {act['activity_type']}: {act['description']}")
            self.activity_list.addItem(item)
            
    def edit_project(self):
        from app.ui.components.project_dialog import ProjectDialog
        dialog = ProjectDialog(self, self.project_data)
        if dialog.exec():
            data = dialog.get_data()
            self.repo.update_project(
                self.project_id, 
                data["name"], 
                data["description"], 
                data["tech_stack"], 
                data["status"]
            )
            self.load_project(self.project_id)
            
    def delete_project(self):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this project? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_project(self.project_id)
            self.back_requested.emit()

