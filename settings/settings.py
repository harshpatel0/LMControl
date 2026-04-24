import json
import os
from types import SimpleNamespace
from settings.default import default_settings

class Settings:
  def __init__(self, file_path):
    self.file_path = file_path
    
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    except FileNotFoundError:
      data = default_settings

      with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    self._load_dict(self, data)

  def _load_dict(self, obj, data):
    for key, value in data.items():
      if isinstance(value, dict):
        nested_obj = SimpleNamespace()
        setattr(obj, key, nested_obj)
        self._load_dict(nested_obj, value)
      else:
        setattr(obj, key, value)

settings = Settings("settings.json")