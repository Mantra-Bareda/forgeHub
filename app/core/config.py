import json
from pathlib import Path
from app.core.metadata import APP_NAME, APP_VERSION

def load_config():
    config_path = Path("config.json")
    if not config_path.exists():
        default_config = {
            "theme": "system",
            "app_name": APP_NAME,
            "version": APP_VERSION
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
        
    with open(config_path, "r") as f:
        return json.load(f)
