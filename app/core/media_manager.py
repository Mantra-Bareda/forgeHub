import os
import shutil
import uuid
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QFileDialog
from app.core.paths import get_app_data_dir

def get_media_dir() -> Path:
    media_dir = get_app_data_dir() / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir

def save_media_file(source_path: str) -> str:
    """Copies a file to the internal media directory and returns the new file path."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")
        
    file_ext = source_path.suffix
    new_filename = f"{uuid.uuid4().hex}{file_ext}"
    dest_path = get_media_dir() / new_filename
    
    shutil.copy2(source_path, dest_path)
    return str(dest_path)

def delete_media_file(internal_path: str):
    """Deletes a file from the internal media directory."""
    path = Path(internal_path)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

def download_media_file(parent_widget, internal_path: str, original_filename: str):
    """Prompts user to save the file and copies it out."""
    source_path = Path(internal_path)
    if not source_path.exists():
        QMessageBox.warning(parent_widget, "Error", "File not found locally.")
        return
        
    download_dir = Path.home() / "Downloads"
    default_path = str(download_dir / original_filename)
    
    dest_path, _ = QFileDialog.getSaveFileName(parent_widget, "Download File", default_path)
    if dest_path:
        shutil.copy2(source_path, dest_path)
        QMessageBox.information(parent_widget, "Success", f"File downloaded successfully to:\n{dest_path}")
