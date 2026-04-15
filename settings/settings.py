import json
import os
from types import SimpleNamespace

class Settings:
  def __init__(self, file_path):
    self.file_path = file_path
    
    try:
      with open(file_path, 'r') as f:
        data = json.load(f)
    except FileNotFoundError:
      data = {
        "models": {
          "ollama_server": "localhost:11434",
          "planner": {
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.7
          },
          "actor": {
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.1
          }
        },
        "orchestrator": {
          "max_iterations_per_step": 10,
          "max_autonomy_steps": 10,
          "action_settle_time": 2,
          "max_replan_loop": 7
        },
        "context_provider": {
          "waiting_period": 4
        }
      }

      with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

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