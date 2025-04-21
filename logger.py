import json
import os
from datetime import datetime

class Logger:
    def __init__(self, save_dir="logs", settings_file="settings.json", name_map_file="display_names.json"):
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        self.filename = os.path.join(save_dir, datetime.now().strftime("%Y-%m-%d") + ".json")
        self.settings_file = settings_file
        self.name_map_file = name_map_file

    def load_log(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_log(self, log):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_settings(self, settings):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
            
    def load_name_map(self):
        if os.path.exists(self.name_map_file):
            with open(self.name_map_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_name_map(self, name_map):
        with open(self.name_map_file, "w", encoding="utf-8") as f:
            json.dump(name_map, f, ensure_ascii=False, indent=2)
