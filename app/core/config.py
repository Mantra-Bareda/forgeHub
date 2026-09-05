import json
from pathlib import Path
from app.core.metadata import APP_NAME, APP_VERSION

def get_config_path():
    return Path(__file__).resolve().parent.parent.parent / "config.json"

def load_config():
    config_path = get_config_path()
    if not config_path.exists():
        default_config = {
            "theme": "system",
            "app_name": APP_NAME,
            "version": APP_VERSION
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "theme": "system",
            "app_name": APP_NAME,
            "version": APP_VERSION
        }

def save_config(config_data):
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
