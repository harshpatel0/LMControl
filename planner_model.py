import json
from context_provider import ContextProvider
from model_definitions import PlannerModel
import utils

MODEL_NAME = "gemma4:e4b"
OLLAMA_SERVER = "http://192.168.68.254:11434/"
MODEL_TEMPERATURE = 0.7
KEEP_ALIVE = 0

planner_model = PlannerModel(model_name=MODEL_NAME, ollama_server=OLLAMA_SERVER, model_temperature=MODEL_TEMPERATURE, keep_alive=KEEP_ALIVE)

context = ContextProvider()
context.get_installed_apps()

def make_plan(task: str) -> dict:
  response = planner_model.run(task=task)
  print(response)

  response = utils.strip_markdown_json(response)
  return json.loads(response)

if __name__ == "__main__":
  plan = make_plan("Open a Taarak Metha ka Ooltah Chasmah Video on YouTube")
  print(json.dumps(plan, indent=2))