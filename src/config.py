"""Configuration management for NFC Sheets Logger"""

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

# Project root directory - handle both script and frozen EXE
if getattr(sys, 'frozen', False):
    # Running as compiled exe: look for config/ next to the EXE
    PROJECT_ROOT = Path(os.path.dirname(sys.executable))
else:
    # Running as script: go up from src/ to project root
    PROJECT_ROOT = Path(__file__).parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class Config:
    """Configuration manager for the application"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.config_dir = CONFIG_DIR
        self.credentials_file = CREDENTIALS_FILE
        self.config_file = CONFIG_FILE

        # Default configuration
        self.defaults = {
            "google_sheets": {
                "spreadsheet_id": "",
                "sheet_name": "NFC Logs",
                "columns": ["日時", "問い合わせ内容", "変更の有無", "備考"],
            },
            "nfc": {
                "reader_name": "SONY RC-380",
                "poll_interval": 0.5,  # seconds
            },
            "input": {
                "key_mappings": {
                    "1": "変更あり",
                    "2": "変更なし",
                    "3": "タイムアウト",
                },
                "timeout_seconds": 5,
                "default_on_timeout": "変更あり",
            },
            "gui": {
                "window_size": (600, 400),
                "theme": "DarkBlue3",
                "log_lines": 10,
            },
        }

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or use defaults"""
        import copy
        config = copy.deepcopy(self.defaults)

        print(f"[Config] Frozen: {getattr(sys, 'frozen', False)}")
        print(f"[Config] PROJECT_ROOT: {self.project_root}")
        print(f"[Config] Config file: {self.config_file}")
        print(f"[Config] Config file exists: {self.config_file.exists()}")

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                    # Deep merge user config with defaults
                    self._merge_dicts(config, user_config)
                    print(f"[Config] Loaded spreadsheet_id: {config.get('google_sheets', {}).get('spreadsheet_id', '(empty)')}")
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
                print("Using default configuration")
        else:
            print(f"[Config] WARNING: config file NOT FOUND at {self.config_file}")

        return config

    @staticmethod
    def _merge_dicts(base: Dict, update: Dict) -> None:
        """Deep merge update dict into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._merge_dicts(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation
        Example: get('google_sheets.spreadsheet_id')
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default

        return value if value is not None else default

    def load_credentials(self) -> Optional[Dict]:
        """Load Google Sheets credentials from JSON file"""
        if not self.credentials_file.exists():
            print(f"Credentials file not found: {self.credentials_file}")
            return None

        try:
            with open(self.credentials_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def save_config(self) -> bool:
        """Save current configuration to YAML file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def validate(self) -> bool:
        """Validate configuration"""
        spreadsheet_id = self.get("google_sheets.spreadsheet_id")

        if not spreadsheet_id:
            print("Error: spreadsheet_id not configured")
            return False

        if not self.credentials_file.exists():
            print(f"Error: credentials file not found at {self.credentials_file}")
            return False

        return True


# Global config instance
config = Config()
