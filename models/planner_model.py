import rootutils
root = rootutils.setup_root(__file__, pythonpath=True)

import json
from context_provider import ContextProvider
from models.model_definitions import PlannerModel
from skills.skill_orchestrator import Skills
import utils.utils as utils
from utils.logger import logger

MODEL_NAME = "gemma4:e4b"
OLLAMA_SERVER = "http://192.168.68.254:11434/"
MODEL_TEMPERATURE = 0.7
KEEP_ALIVE = 0

planner_model = PlannerModel()
skill_orchestrator = Skills()

context = ContextProvider()
context.get_installed_apps()

def make_plan(task: str):
  planner_skills, actor_skills = planner_model.skill_installation_mode(task)

  logger.debug(f"Planner skills loaded: {planner_skills is not None}")
  logger.debug(f"Actor skills loaded: {actor_skills is not None}")

  response = planner_model.run(task=task, skills=planner_skills)
  logger.info(response)

  response = utils.strip_markdown_json(response)
  plan = json.loads(response)

  # Carry actor skills forward for the orchestrator
  plan["_actor_skills"] = actor_skills

  return plan

if __name__ == "__main__":
  plan = make_plan("Open a Taarak Metha ka Ooltah Chasmah Video on YouTube")
  
  # Don't print _actor_skills in the human-readable output
  display_plan = {k: v for k, v in plan.items() if k != "_actor_skills"}
  print(json.dumps(display_plan, indent=2))