import models.actor_model as actor_model
from parse_action import parse_action
import time
import models.planner_model
from context_provider import ContextProvider
from pc_actions.perform_pc_actions import PCActions
import json
from utils.logger import logger
from settings.settings import settings

pc_actions = PCActions()

MAX_ITERATIONS_PER_STEP = settings.orchestrator.max_iterations_per_step
MAX_AUTONOMY_STEPS = settings.orchestrator.max_autonomy_steps
ACTION_SETTLE_TIME = settings.orchestrator.action_settle_time
MAX_REPLAN_LOOP = settings.orchestrator.max_replan_loop

class StepOrchestrator:
  def __init__(self, steps, skills):
    self.steps = steps['steps']
    self.task = steps['task']
    self.skills = skills

    self.step_list = steps['steps']

    self.step_count = 0
    self.additional_context = ""
    self.replan_history = []

    self.in_autonomy = False
    self.hard_exit = False

    self.context_provider = ContextProvider()

    self.handlers = {
      "PROCEED": self.handleProceed,
      "DONE": self.handleDone,
      "STUCK": self.handleStuck,
      "REPLAN": self.handleReplan,
      "RETRY": self.handleRetry,
    }

  def handleProceed(self):
    self.step_count += 1
    self.replan_history = []
    self.additional_context = ""
    self.iterations = 0

    return "BREAK"

  def handleDone(self):
    logger.info("The actor model claims the task is done, hard exiting...")
    window_after = self.context_provider.get_active_window()
    element = self.step_result.get('element', '')

    if element and element not in window_after:
      logger.warning(f"Actor claimed DONE, but '{element}' not in Window. Forcing retry.")
      self.additional_context += (
        f"You claimed to be done, but I cannot see '{element}' in the active window. "
        "Please ensure the action completed correctly.\n"
      )
      return "CONTINUE"

    self.hard_exit = True
    return "BREAK"

  def handleStuck(self):
    logger.info(f"The Actor Model claims it is stuck, running another iteration with added context {self.iterations+1}/{MAX_ITERATIONS_PER_STEP}")
    self.additional_context = self.additional_context + f"{self.step_result['message']}" + "\n"
    return "CONTINUE"

  def handleReplan(self):
    next_action = self.step_result.get('next', '')
    self.replan_history.append(next_action)

    if len(self.replan_history) >= MAX_REPLAN_LOOP and len(set(self.replan_history[-MAX_REPLAN_LOOP:])) == 1:
      logger.critical(f"Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit.")
      self.hard_exit = True

    logger.info(f"[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")

    self.temp_task = next_action
    self.additional_context = self.additional_context + "The current task is from the previous actor, instructing you what to do" + "\n"
    return "CONTINUE"


  def handleRetry(self):
    logger.warning(f"[STEP_ORCHESTRATOR] Retrying with added context {self.iterations+1}/{MAX_ITERATIONS_PER_STEP}")
    try:
      self.additional_context = self.additional_context + f"{self.step_result['message']}" + "\n"
    except Exception:
      self.additional_context = self.additional_context + "The Action Parser was not able to parse your action. Be more careful with the format in this run." + "\n"
    return "CONTINUE"

  def handle_skill_invocations(self, action_result):
    logger.debug(action_result)
    action_result_type = action_result.get('result')
    action_result_stderr = action_result.get('stderr', "No errors!")
    action_result_stdout = action_result.get('stdout', "Script / Skill outputted nothing")

    logger.debug(f"Action Result Type for Custom Actions: {action_result_type}\nAction Result stderr: {action_result_stderr}\nAction Result stdout: {action_result_stdout}")

    if action_result_type == "IMPORT_DISCOVERY_ERROR":
      self.additional_context = self.additional_context + f"The modules in the code/skill could not be discovered, and so cannot be run without errors\nHere are the errors returned: {action_result_stderr}" + "\n"
      return "CONTINUE"
    
    elif action_result_type == "PACKAGE_INSTALL_ERROR":
      self.additional_context = self.additional_context + f"The modules in the code/skill could not be installed, and so the code/skill cannot be run without errors\nHere are the errors returned: {action_result_stderr}" + "\n"
      return "CONTINUE"

    
    elif action_result_type == "TIMEOUT":
      self.additional_context = self.additional_context + f"""
The code/skill took too long to run and was killed prematurely. Here are the logs of its output.

## Output
{action_result_stdout}

## Errors
{action_result_stderr}
""" + "\n"
      return "CONTINUE"
      
  
    elif action_result_type == "PY_EXCEPTION":
      self.additional_context = self.additional_context + f"The subprocess running your code/skill produced an exception\n{action_result_stderr}"
      return "CONTINUE"

    
    elif action_result_type == "ERROR":
      self.additional_context = self.additional_context + f"The code/skill ran with errors\n{action_result_stderr}"
      return "CONTINUE"
    
    elif action_result_type == "SUCCESS":
      self.additional_context = self.additional_context + f"""
The code/skill ran successfully, here are the logs of the Output and Error Stream

## Output
{action_result_stdout}
""" + "\n"
      self.step_count += 1
      self.replan_history = []
      self.additional_context = ""
      return "BREAK"
    
    else:
      logger.error(f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type.")
      raise Exception(f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type.")
    

  def run(self):
    while not self.hard_exit:
      self.in_autonomy = self.step_count >= len(self.steps)

      if self.in_autonomy:
        if self.step_count >= len(self.steps) + MAX_AUTONOMY_STEPS:
          logger.critical("Autonomy budget exhausted, exiting.")
          break
        logger.info("[Step Orchestrator > Basic Autonomy Mode] Running in Basic Autonomy Mode")
        step = {
          "instruction": "Autonomy Mode — the planned steps are complete but the task may not be done. Continue independently and call done when finished. Your hand is not going to be held in this mode, so just complete the task how you think you can.",
          "expected_result": "The original task is fully complete."
        }
      else:
        step = self.steps[self.step_count]

      logger.info(f"Step Location: {self.step_count+1}/{len(self.steps)}")

      self.additional_context = ""
      self.temp_task = None
      self.replan_history = []

      for iterations in range(1, MAX_ITERATIONS_PER_STEP + 1):
        self.iterations = iterations
        if iterations == MAX_ITERATIONS_PER_STEP:
          logger.info("Reached Maximum Allowed Iterations per Step, quitting.")
          self.hard_exit = True
          break

        self.step_result = actor_model.do_step(step, self.task, self.additional_context, punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step", skills=self.skills)
        action_result = parse_action(self.step_result)

        logger.debug(f"Action Result: {action_result}")
        time.sleep(settings.orchestrator.action_settle_time)

        if isinstance(action_result, str):
          handler = self.handlers[action_result]
          signal = handler()
        elif isinstance(action_result, dict):
          signal = self.handle_skill_invocations(action_result)

        if signal == "BREAK":
          break
        if signal == "CONTINUE" or signal == None:
          continue

if __name__ == "__main__":
  plan = models.planner_model.make_plan("Open gemini.google.com, and write and send a full report on dinosaurs and ask it to proof read your work.")
  printed_plan = json.dumps(plan, indent=2)
  print(printed_plan)

  step_orchestrator = StepOrchestrator(steps=plan, skills=plan.get("_actor_skills"))
  step_orchestrator.run()