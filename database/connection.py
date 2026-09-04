import sqlite3
from pathlib import Path
from contextlib import contextmanager
import logging

logger = logging.getLogger("ForgeHub.Database")

class DatabaseManager:
    def __init__(self, db_path="database/forgehub.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def backup(self, backup_path):
        import shutil
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
