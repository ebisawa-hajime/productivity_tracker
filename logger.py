import json
import os
from datetime import datetime

class Logger:
    def __init__(self):
        today = datetime.today().strftime("%Y-%m-%d")
        self.filename = f"logs/{today}.json"
        self.settings_path = "settings.json"
        self.name_map_path = "display_names.json"
        self.display_flags_path = "display_flags.json"

    def load_log(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_log(self, data):
        os.makedirs("logs", exist_ok=True)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_settings(self, settings):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def load_name_map(self):
        if os.path.exists(self.name_map_path):
            with open(self.name_map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_name_map(self, name_map):
        with open(self.name_map_path, "w", encoding="utf-8") as f:
            json.dump(name_map, f, indent=2, ensure_ascii=False)

    def save_display_flags(self, flags):
        with open(self.display_flags_path, "w", encoding="utf-8") as f:
            json.dump(flags, f, indent=2, ensure_ascii=False)

    def load_display_flags(self):
        if os.path.exists(self.display_flags_path):
            with open(self.display_flags_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
