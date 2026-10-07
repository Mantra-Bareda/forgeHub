import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from app.core.theme import get_current_palette
from app.ui.components.icons import get_svg_icon
from database.repository import MediaRepository
from app.core.media_manager import save_media_file, delete_media_file, download_media_file

class MediaUploadWidget(QWidget):
    """A reusable widget to attach files (max 10MB) to an entity."""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.media_repo = MediaRepository(self.db)
        
        self.entity_type = None
        self.entity_id = None
        self.pending_files = [] # List of tuples: (original_path, file_name, file_size, file_type)
        
        self.setup_ui()
        
    def setup_ui(self):
        palette = get_current_palette()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Header
        header_lay = QHBoxLayout()
        title = QLabel("Media Attachments")
        title.setStyleSheet(f"color: {palette.fg_primary}; font-weight: 600; font-size: 13px;")
        
        self.upload_btn = QPushButton(" Attach File")
        self.upload_btn.setIcon(get_svg_icon("upload", palette.accent, 14))
        self.upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {palette.bg_input};
                border: 1px solid {palette.border_card};
                border-radius: 6px;
                color: {palette.fg_primary};
                padding: 4px 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {palette.accent};
            }}
        """)
        self.upload_btn.clicked.connect(self.prompt_file_upload)
        
        header_lay.addWidget(title)
        header_lay.addStretch()
        header_lay.addWidget(self.upload_btn)
        self.layout.addLayout(header_lay)
        
        # Files List
        self.files_container = QVBoxLayout()
        self.files_container.setSpacing(6)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.inner_widget = QWidget()
        self.inner_widget.setLayout(self.files_container)
        scroll.setWidget(self.inner_widget)
        
        self.layout.addWidget(scroll)
        self.refresh_list()

    def load_entity(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.pending_files = []
        self.refresh_list()
        
    def prompt_file_upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", str(Path.home()), 
            "All Files (*);;Images (*.png *.jpg *.jpeg *.gif);;Documents (*.pdf *.docx *.doc *.txt)"
        )
        if not path:
            return
            
        file_stat = os.stat(path)
        file_size = file_stat.st_size
        if file_size > 10 * 1024 * 1024:
            QMessageBox.warning(self, "File Too Large", "Please select a file smaller than 10MB.")
            return
            
        file_name = os.path.basename(path)
        file_type = Path(path).suffix.lower()
        
        if self.entity_id is not None:
            # Direct save
            try:
                storage_path = save_media_file(path)
                self.media_repo.add_media(self.entity_type, self.entity_id, file_name, storage_path, file_type, file_size)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Upload Failed", str(e))
        else:
            # Pending save
            self.pending_files.append((path, file_name, file_size, file_type))
            self.refresh_list()
            
    def save_pending_files(self, entity_id: int):
        if not self.entity_type:
            return
            
        for path, file_name, file_size, file_type in self.pending_files:
            try:
                storage_path = save_media_file(path)
                self.media_repo.add_media(self.entity_type, entity_id, file_name, storage_path, file_type, file_size)
            except Exception as e:
                pass
        self.pending_files = []
        self.entity_id = entity_id
        self.refresh_list()
        
    def refresh_list(self):
        # Clear existing
        while self.files_container.count():
            item = self.files_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        palette = get_current_palette()
        
        saved_files = []
        if self.entity_id is not None:
            saved_files = self.media_repo.get_media_for_entity(self.entity_type, self.entity_id)
            
        if not saved_files and not self.pending_files:
            empty = QLabel("No media attached.")
            empty.setStyleSheet(f"color: {palette.fg_muted}; font-style: italic;")
            self.files_container.addWidget(empty)
            self.files_container.addStretch()
            return
            
        for media in saved_files:
            self._add_file_row(media, is_pending=False)
            
        for idx, pending in enumerate(self.pending_files):
            # Pending tuple: path, file_name, file_size, file_type
            media_dict = {
                "id": f"pending_{idx}",
                "file_name": pending[1],
                "file_size": pending[2],
                "file_type": pending[3],
                "storage_path": pending[0]
            }
            self._add_file_row(media_dict, is_pending=True)
            
        self.files_container.addStretch()
        
    def _add_file_row(self, media, is_pending: bool):
        palette = get_current_palette()
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {palette.bg_card};
                border: 1px solid {palette.border_subtle};
                border-radius: 6px;
            }}
        """)
        r_lay = QHBoxLayout(row)
        r_lay.setContentsMargins(10, 6, 10, 6)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_icon("description", palette.accent, 16))
        
        # Details
        size_kb = media['file_size'] / 1024
        status = "(Pending Save)" if is_pending else f"{size_kb:.1f} KB"
        
        name_lbl = QLabel(f"<b>{media['file_name']}</b> <span style='color:{palette.fg_muted}; font-size: 11px;'>{status}</span>")
        name_lbl.setStyleSheet("border: none; background: transparent;")
        
        r_lay.addWidget(icon_lbl)
        r_lay.addWidget(name_lbl, stretch=1)
        
        # Actions
        if not is_pending:
            dl_btn = QPushButton(" Download")
            dl_btn.setIcon(get_svg_icon("download", palette.success, 14))
            dl_btn.setStyleSheet(f"background: transparent; border: none; color: {palette.success};")
            dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            dl_btn.clicked.connect(lambda: download_media_file(self, media['storage_path'], media['file_name']))
            r_lay.addWidget(dl_btn)
            
            del_btn = QPushButton()
            del_btn.setIcon(get_svg_icon("delete", palette.danger, 14))
            del_btn.setStyleSheet(f"background: transparent; border: none;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda: self._delete_media(media['id'], media['storage_path']))
            r_lay.addWidget(del_btn)
        else:
            rm_btn = QPushButton(" Remove")
            rm_btn.setStyleSheet(f"background: transparent; border: none; color: {palette.danger};")
            rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rm_btn.clicked.connect(lambda: self._remove_pending(media['id']))
            r_lay.addWidget(rm_btn)
            
        self.files_container.addWidget(row)
        
    def _delete_media(self, media_id, internal_path):
        reply = QMessageBox.question(self, "Confirm Delete", "Remove this attachment permanently?")
        if reply == QMessageBox.StandardButton.Yes:
            delete_media_file(internal_path)
            self.media_repo.delete_media(media_id)
            self.refresh_list()
            
    def _remove_pending(self, pending_id_str):
        try:
            idx = int(pending_id_str.split("_")[1])
            self.pending_files.pop(idx)
            self.refresh_list()
        except Exception:
            pass
