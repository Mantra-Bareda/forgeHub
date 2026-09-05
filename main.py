import sys
import logging
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThreadPool
from app.ui.main_window import MainWindow
from app.core.logger import setup_logger
from app.core.config import load_config
from database.connection import DatabaseManager
from database.schema import initialize_database
from app.core.theme import apply_theme
from database.repository import ProviderRepository

def global_exception_handler(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger("ForgeHub")
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Critical Error")
    msg_box.setText("An unexpected error occurred.")
    msg_box.setDetailedText(msg)
    msg_box.exec()

def cleanup():
    logger = logging.getLogger("ForgeHub")
    logger.info("Cleaning up and waiting for thread pool...")
    QThreadPool.globalInstance().waitForDone()
    logger.info("Shutdown complete.")

def main():
    setup_logger()
    logger = logging.getLogger("ForgeHub")
    logger.info("Starting Forge Hub")
    
    sys.excepthook = global_exception_handler

    config = load_config()
    
    db_manager = DatabaseManager()
    initialize_database(db_manager)
    provider_repo = ProviderRepository(db_manager)
    provider_repo.initialize_providers()
    logger.info("Database initialized")
    
    app = QApplication(sys.argv)
    apply_theme(app, config.get("theme", "system"))
    app.aboutToQuit.connect(cleanup)
    
    window = MainWindow(config, db_manager)
    window.show()
    
    providers = provider_repo.get_providers()
    has_key = any(p.get("api_key") for p in providers)
    if not has_key:
        QMessageBox.information(window, "Welcome to Forge Hub!", "It looks like this is your first time here or you haven't set up any API keys. Please navigate to the AI Providers section to add your API keys.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
