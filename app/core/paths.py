import sys
from pathlib import Path

def get_app_data_dir() -> Path:
    """Returns the platform-specific application data directory."""
    home = Path.home()
    if sys.platform == "win32":
        return home / "AppData" / "Roaming" / "ForgeHub"
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / "ForgeHub"
    else:
        return home / ".config" / "ForgeHub"

def get_config_path() -> Path:
    return get_app_data_dir() / "config.json"

def get_db_path() -> Path:
    return get_app_data_dir() / "database" / "forgehub.db"

def ensure_dirs():
    app_dir = get_app_data_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "database").mkdir(parents=True, exist_ok=True)

# Initialize on import
ensure_dirs()
