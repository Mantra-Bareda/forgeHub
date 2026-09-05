from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QComboBox, QPushButton, QTextEdit, QMessageBox, 
                                 QScrollArea, QFrame, QSplitter)
from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject
from app.ai.generator import ContentGenerator
from app.ai.compiler import ContextCompiler
from database.repository import ProjectRepository, ProfileRepository, CertificateRepository, HackathonRepository

class GenWorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)

class ContentGenWorker(QRunnable):
    def __init__(self, generator, mode, source_type, item_id, instructions):
        super().__init__()
        self.generator = generator
        self.mode = mode
        self.source_type = source_type
        self.item_id = item_id
        self.instructions = instructions
        self.signals = GenWorkerSignals()
        
    def run(self):
        try:
            if self.mode == "GitHub README":
                res = self.generator.generate_github_readme(self.item_id, self.instructions)
            elif self.mode == "LinkedIn Post":
                res = self.generator.generate_linkedin_post(self.source_type, self.item_id, self.instructions)
            else:
                res = "Custom generation not fully supported yet."
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))

class AdvisorWorkerSignals(QObject):
    finished = Signal(object) # PostingAdvisorResult
    error = Signal(str)

class AdvisorWorker(QRunnable):
    def __init__(self, generator, source_type, content_data):
        super().__init__()
        self.generator = generator
        self.source_type = source_type
        self.content_data = content_data
        self.signals = AdvisorWorkerSignals()
        
    def run(self):
        try:
            res = self.generator.evaluate_posting_advisor(self.source_type, self.content_data)
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))

class ContentPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        self.proj_repo = ProjectRepository(self.db)
        self.prof_repo = ProfileRepository(self.db)
        self.cert_repo = CertificateRepository(self.db)
        self.hack_repo = HackathonRepository(self.db)
        
        self.compiler = ContextCompiler(self.db)
        self.generator = ContentGenerator(self.db, self.compiler)
        self.thread_pool = QThreadPool.globalInstance()
        
        # UI
        main_layout = QVBoxLayout(self)
        
        header = QLabel("Content Generation")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side: Controls and Advisor
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        left_layout.addWidget(QLabel("<b>Content Type:</b>"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["GitHub README", "LinkedIn Post"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        left_layout.addWidget(self.type_combo)
        
        self.source_type_label = QLabel("<b>Source Type:</b>")
        left_layout.addWidget(self.source_type_label)
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["Project", "Certificate", "Hackathon", "Achievement"])
        self.source_type_combo.currentTextChanged.connect(self.load_items)
        left_layout.addWidget(self.source_type_combo)
        
        left_layout.addWidget(QLabel("<b>Item:</b>"))
        self.item_combo = QComboBox()
        left_layout.addWidget(self.item_combo)
        
        left_layout.addWidget(QLabel("<b>Additional Instructions:</b>"))
        self.instructions_input = QTextEdit()
        self.instructions_input.setMaximumHeight(80)
        left_layout.addWidget(self.instructions_input)
        
        # Advisor Panel
        self.advisor_panel = QFrame()
        self.advisor_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 5px; margin-top: 10px;")
        advisor_layout = QVBoxLayout(self.advisor_panel)
        advisor_layout.addWidget(QLabel("<b>Posting Advisor</b>"))
        
        self.advisor_status = QLabel("Ready to analyze...")
        self.advisor_status.setWordWrap(True)
        advisor_layout.addWidget(self.advisor_status)
        
        self.advisor_btn = QPushButton("Analyze with Advisor")
        self.advisor_btn.clicked.connect(self.run_advisor)
        advisor_layout.addWidget(self.advisor_btn)
        
        left_layout.addWidget(self.advisor_panel)
        left_layout.addStretch()
        
        # Right side: Output Editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.generate_btn = QPushButton("Generate Content")
        self.generate_btn.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white; padding: 10px;")
        self.generate_btn.clicked.connect(self.generate_content)
        right_layout.addWidget(self.generate_btn)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Generated content will appear here...")
        right_layout.addWidget(self.editor)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        right_layout.addWidget(copy_btn)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        self.on_type_changed("GitHub README")
        
    def showEvent(self, event):
        super().showEvent(event)
        self.load_items()
        
    def on_type_changed(self, text):
        if text == "GitHub README":
            self.source_type_label.hide()
            self.source_type_combo.hide()
            self.advisor_panel.hide()
        else:
            self.source_type_label.show()
            self.source_type_combo.show()
            self.advisor_panel.show()
        self.load_items()
            
    def load_items(self):
        self.item_combo.clear()
        
        content_type = self.type_combo.currentText()
        source_type = self.source_type_combo.currentText()
        
        if content_type == "GitHub README" or source_type == "Project":
            items = self.proj_repo.get_projects()
            for p in items: self.item_combo.addItem(p["name"], p["id"])
        elif source_type == "Certificate":
            items = self.cert_repo.get_certificates()
            for i in items: self.item_combo.addItem(i["title"], i["id"])
        elif source_type == "Hackathon":
            items = self.hack_repo.get_hackathons()
            for i in items: self.item_combo.addItem(i["event_name"], i["id"])
        elif source_type == "Achievement":
            items = self.prof_repo.get_achievements()
            for i in items: self.item_combo.addItem(i["title"], i["id"])
            
    def get_selected_item_data(self):
        item_id = self.item_combo.currentData()
        if not item_id: return None
        
        source_type = self.source_type_combo.currentText()
        if self.type_combo.currentText() == "GitHub README":
            source_type = "Project"
            
        data_str = ""
        if source_type == "Project":
            p = self.proj_repo.get_project(item_id)
            if p: data_str = f"Project '{p['name']}' using {p['technology_stack']}. Status: {p['status']}. {p['description']}"
        elif source_type == "Certificate":
            c = self.cert_repo.get_certificate(item_id)
            if c: data_str = f"Certificate '{c['title']}' from {c['issuer']}, earned {c['issue_date']}."
        elif source_type == "Hackathon":
            h = self.hack_repo.get_hackathon(item_id)
            if h: data_str = f"Hackathon '{h['event_name']}', Project: {h['project_submitted']}, Standing: {h['standing']}."
        else:
            a = self.prof_repo.get_achievement(item_id)
            if a: data_str = f"Achievement '{a['title']}' ({a['type']}): {a['description']} on {a['date_achieved']}."
            
        return source_type, data_str

    def run_advisor(self):
        if not self.item_combo.currentData(): return
        
        source_type, data_str = self.get_selected_item_data()
        
        self.advisor_btn.setEnabled(False)
        self.advisor_status.setText("Analyzing professional value...")
        self.advisor_status.setStyleSheet("color: orange;")
        
        worker = AdvisorWorker(self.generator, source_type, data_str)
        worker.signals.finished.connect(self.on_advisor_done)
        worker.signals.error.connect(self.on_advisor_error)
        self.thread_pool.start(worker)
        
    def on_advisor_done(self, result):
        self.advisor_btn.setEnabled(True)
        
        color = "green"
        if result.recommendation == "NOT RECOMMENDED": color = "red"
        elif result.recommendation == "RECOMMENDED WITH CHANGES": color = "orange"
        
        self.advisor_status.setText(f"<b>{result.recommendation}</b><br><br>{result.reason}")
        self.advisor_status.setStyleSheet(f"color: {color};")
        
    def on_advisor_error(self, err):
        self.advisor_btn.setEnabled(True)
        self.advisor_status.setText(f"Analysis failed: {err}")
        self.advisor_status.setStyleSheet("color: red;")
        
    def generate_content(self):
        mode = self.type_combo.currentText()
        item_id = self.item_combo.currentData()
        source_type = self.source_type_combo.currentText()
        inst = self.instructions_input.toPlainText()
        
        if not item_id:
            QMessageBox.warning(self, "Warning", "Please select an item first.")
            return
            
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Generating...")
        self.editor.clear()
        
        worker = ContentGenWorker(self.generator, mode, source_type, item_id, inst)
        worker.signals.finished.connect(self.on_generate_done)
        worker.signals.error.connect(self.on_generate_error)
        self.thread_pool.start(worker)
        
    def on_generate_done(self, result):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate Content")
        self.editor.setPlainText(result)
        
    def on_generate_error(self, err):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate Content")
        QMessageBox.critical(self, "Generation Failed", str(err))
        
    def copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        cb = QGuiApplication.clipboard()
        cb.setText(self.editor.toPlainText())
        QMessageBox.information(self, "Copied", "Content copied to clipboard.")
