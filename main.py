import sys
import logging
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.core.logger import setup_logger
from app.core.config import load_config
from database.connection import DatabaseManager
from database.schema import initialize_database

from app.core.theme import apply_theme

from database.repository import ProviderRepository

def main():
    setup_logger()
    logger = logging.getLogger("ForgeHub")
    logger.info("Starting Forge Hub")

    config = load_config()
    
    db_manager = DatabaseManager()
    initialize_database(db_manager)
    ProviderRepository(db_manager).initialize_providers()
    logger.info("Database initialized")
    
    app = QApplication(sys.argv)
    apply_theme(app, config.get("theme", "system"))
    
    window = MainWindow(config, db_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
