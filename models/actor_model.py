import json

from models.ollama.model_definitions import ActorModel
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
    user_prompt = actor_model.return_prompt_with_additional_context(
      user_prompt, 
      additional_context=punishment_tally, 
      accompanying_message="Here are the number of iterations you have made on this task"
    )
  
  response = actor_model.run(user_prompt, skills=skills)
  action = json.loads(utils.strip_markdown_json(response).strip())

  if not action:
      action = {
        "action": "retry",
        "message": "Model returned an empty response, likely due to context overload. Retry with the same step."}
      logger.warning("[INTERNAL ACTOR MODEL GUARD] The model returned an empty response, instructing the Step Orchestrator to retry")
  
  logger.debug(action)
  return action

def do_autonomy_step(task, history=None, additional_context=None, punishment_tally=None, skills=None, runtime_skills=None, available_skill_actions = None):
  user_prompt = actor_model.construct_user_prompt(task=task, instruction=None, expected_result=None)

  if additional_context or len(additional_context) > 0:
    user_prompt = actor_model.return_prompt_with_additional_context(user_prompt, additional_context)

  if punishment_tally:
    user_prompt = actor_model.return_prompt_with_additional_context(
      user_prompt,
      additional_context=punishment_tally,
      accompanying_message="Here are the number of iterations you have made on this task"
    )

  if available_skill_actions:
    user_prompt = actor_model.return_prompt_with_additional_context(
      user_prompt,
      additional_context=available_skill_actions,
      accompanying_message="The following are the available skill actions, skill actions run like any skill, you are advised on how to run them already"
    )

  if runtime_skills:
    user_prompt = actor_model.return_prompt_with_additional_context(
      user_prompt,
      additional_context=runtime_skills,
      accompanying_message="The following skill(s) was/were just installed and is now available to you:"
    )

  if history:
    user_prompt = actor_model.return_prompt_with_additional_context(
      user_prompt,
      additional_context=history,
      accompanying_message="Here is a running history of everything you said you did:"
    )

  response = actor_model.run(user_prompt, skills=skills)
  action = json.loads(utils.strip_markdown_json(response).strip())

  if not action:
    action = {
      "action": "retry",
      "message": "Model returned an empty response, likely due to context overload. Retry with the same step."
    }
    logger.warning("[INTERNAL ACTOR MODEL GUARD] The model returned an empty response, instructing the Step Orchestrator to retry")

  logger.debug(action)
  return action