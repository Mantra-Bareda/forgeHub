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
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
        finally:
            conn.close()

    def backup(self, backup_path):
        """Creates a safe hot backup using SQLite's native backup API."""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(exist_ok=True, parents=True)
        source = sqlite3.connect(str(self.db_path))
        dest = sqlite3.connect(str(backup_path))
        try:
            source.backup(dest)
            logger.info(f"Database backed up to {backup_path}")
        finally:
            dest.close()
            source.close()

    def restore(self, backup_path):
        """Restores the database from a backup using SQLite's native backup API."""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        source = sqlite3.connect(str(backup_path))
        dest = sqlite3.connect(str(self.db_path))
        try:
            source.backup(dest)
            logger.info(f"Database restored from {backup_path}")
        finally:
            dest.close()
            source.close()

    def export_sql(self, dump_path):
        """Exports the entire database as a SQL dump file."""
        dump_path = Path(dump_path)
        dump_path.parent.mkdir(exist_ok=True, parents=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            with open(dump_path, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            logger.info(f"Database exported to {dump_path}")
        finally:
            conn.close()
