import json

from models.model_definitions import ActorModel
from context_provider import ContextProvider

import utils.utils as utils
from utils.logger import logger

context = ContextProvider()
actor_model = ActorModel()

def do_step(step, task, additional_context=None, punishment_tally=None, skills=None):
  instruction = step['instruction']
  expected_result = step['expected_result']

  user_prompt = actor_model.construct_user_prompt(task=task, instruction=instruction, expected_result=expected_result)

  if additional_context != "":
    user_prompt = actor_model.return_prompt_with_additional_context(user_prompt, additional_context)
      
  if punishment_tally:
    user_prompt = actor_model.return_prompt_with_additional_context(user_prompt, 
                                                                    additional_context=punishment_tally, 
                                                                    accompanying_message="Here are the number of iterations you have made on this task")
  
  response = actor_model.run(user_prompt, attach_screenshot=True, skills=skills)
  action = json.loads(utils.strip_markdown_json(response).strip())

  if not action:
      action = {
        "action": "retry",
        "message": "Model returned an empty response, likely due to context overload. Retry with the same step."}
      logger.warning("[INTERNAL ACTOR MODEL GUARD] The model returned an empty response, instructing the Step Orchestrator to retry")
  
  logger.debug(action)
  return action