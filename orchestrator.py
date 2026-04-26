import models.actor_model as actor_model
from parse_action import parse_action
import time
import models.planner_model
from context_provider import ContextProvider
from pc_actions.perform_pc_actions import PCActions
import json
from utils.logger import logger
from settings.settings import settings

from models.ollama.model_definitions import SkillInstallationMode 
from skills.skill_orchestrator import Skills

pc_actions = PCActions()

MAX_ITERATIONS_PER_STEP = settings.orchestrator.planner_architecture.max_iterations_per_step
MAX_AUTONOMY_STEPS = settings.orchestrator.planner_architecture.max_autonomy_steps
ACTION_SETTLE_TIME = settings.orchestrator.action_settle_time
MAX_REPLAN_LOOP = settings.orchestrator.planner_architecture.max_replan_loop

class ActionHandlers:
  def __init__(self, orchestrator, in_autonomy=False):
    self.orchestrator = orchestrator
    self.in_autonomy = in_autonomy

  def handleProceed(self):
    if not self.in_autonomy:
      self.orchestrator.step_count += 1
      self.orchestrator.iterations = 0
    else:
      self.orchestrator.iterations += 1

    self.orchestrator.replan_history = []
    self.orchestrator.additional_context = ""
    

    return "BREAK"

  def handleDone(self):
    logger.info("The actor model claims the task is done, hard exiting...")
    window_after = self.orchestrator.context_provider.get_active_window()
    element = self.orchestrator.step_result.get('element', '')

    if element and element not in window_after:
      logger.warning(f"Actor claimed DONE, but '{element}' not in Window. Forcing retry.")
      self.orchestrator.additional_context += (
        f"You claimed to be done, but I cannot see '{element}' in the active window. "
        "Please ensure the action completed correctly.\n"
      )
      return "CONTINUE"

    self.orchestrator.hard_exit = True
    return "BREAK"

  def handleStuck(self):
    logger.info(f"The Actor Model claims it is stuck, running another iteration with added context {self.orchestrator.iterations+1}/{MAX_ITERATIONS_PER_STEP}")
    self.orchestrator.additional_context = self.orchestrator.additional_context + f"{self.orchestrator.step_result['message']}" + "\n"
    return "CONTINUE"

  def handleReplan(self):
    next_action = self.step_result.get('next', '')
    self.orchestrator.replan_history.append(next_action)

    if len(self.orchestrator.replan_history) >= MAX_REPLAN_LOOP and len(set(self.orchestrator.replan_history[-MAX_REPLAN_LOOP:])) == 1:
      logger.critical(f"Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit.")
      self.orchestrator.hard_exit = True

    logger.info(f"[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")

    self.orchestrator.temp_task = next_action
    self.orchestrator.additional_context = self.orchestrator.additional_context + "The current task is from the previous actor, instructing you what to do, when you are done with it, call an action and do not emit done under any circumstances" + "\n"
    return "CONTINUE"
  
  def handleRetry(self):
    logger.warning(f"[STEP_ORCHESTRATOR] Retrying with added context {self.iterations+1}/{MAX_ITERATIONS_PER_STEP}")
    try:
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"{self.orchestrator.step_result['message']}" + "\n"
    except Exception:
      self.orchestrator.additional_context = self.orchestrator.additional_context + "The Action Parser was not able to parse your action. Be more careful with the format in this run." + "\n"
    return "CONTINUE"

  def handle_skill_invocations(self, action_result):
    logger.debug(action_result)
    action_result_type = action_result.get('result')
    action_result_stderr = action_result.get('stderr', "No errors!")
    action_result_stdout = action_result.get('stdout', "Script / Skill outputted nothing")

    logger.debug(f"Action Result Type for Custom Actions: {action_result_type}\nAction Result stderr: {action_result_stderr}\nAction Result stdout: {action_result_stdout}")

    if action_result_type == "IMPORT_DISCOVERY_ERROR":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"The modules in the code/skill could not be discovered, and so cannot be run without errors\nHere are the errors returned: {action_result_stderr}" + "\n"
      return "CONTINUE"
    
    elif action_result_type == "PACKAGE_INSTALL_ERROR":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"The modules in the code/skill could not be installed, and so the code/skill cannot be run without errors\nHere are the errors returned: {action_result_stderr}" + "\n"
      return "CONTINUE"

    
    elif action_result_type == "TIMEOUT":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"""
The code/skill took too long to run and was killed prematurely. Here are the logs of its output.

## Output
{action_result_stdout}

## Errors
{action_result_stderr}
""" + "\n"
      return "CONTINUE"
      
    elif action_result_type == "PY_EXCEPTION":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"The subprocess running your code/skill produced an exception\n{action_result_stderr}"
      return "CONTINUE"

    elif action_result_type == "ERROR":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"The code/skill ran with errors\n{action_result_stderr}"
      return "CONTINUE"
    
    elif action_result_type == "SUCCESS":
      self.orchestrator.additional_context = self.orchestrator.additional_context + f"""
The code/skill ran successfully, here are the logs of the Output and Error Stream

## Output
{action_result_stdout}
""" + "\n"
      if not self.in_autonomy:
        self.orchestrator.step_count += 1
      else:
        self.orchestrator.iterations += 1

      self.orchestrator.replan_history = []
      self.orchestrator.additional_context = ""
      return "BREAK"
    
    else:
      logger.error(f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type.")
      raise Exception(f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type.")
    
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
    self.action_handler = ActionHandlers(orchestrator=self)

    self.temp_task = None

    self.handlers = {
      "PROCEED": self.action_handler.handleProceed,
      "DONE": self.action_handler.handleDone,
      "STUCK": self.action_handler.handleStuck,
      "REPLAN": self.action_handler.handleReplan,
      "RETRY": self.action_handler.handleRetry,
    }

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

        self.step_result = actor_model.do_step(step, self.task if not self.temp_task else self.temp_task, self.additional_context, punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step", skills=self.skills)
        action_result = parse_action(self.step_result)

        logger.debug(f"Action Result: {action_result}")
        time.sleep(settings.orchestrator.action_settle_time)

        if isinstance(action_result, str):
          handler = self.handlers[action_result]
          signal = handler()
        elif isinstance(action_result, dict):
          signal = self.action_handler.handle_skill_invocations(action_result)

        if signal == "BREAK":
          break
        if signal == "CONTINUE" or signal == None:
          continue

class AutonomyOrchestrator:
  def __init__(self, task):
    self.task = task
    self.iterations = 0
    self.additional_context = ""
    self.context_provider = ContextProvider()
    self.skill_installation_mode = SkillInstallationMode()
    self.skill_orchestrator = Skills()
    self.hard_exit = False
    self.skills = ""

    self.punishment_tally = ""
    self.history = ""
    self.runtime_skills = None

    self.installed_skills = []

    self.action_handler = ActionHandlers(orchestrator=self, in_autonomy=True)
    self.handlers = {
      "PROCEED": self.action_handler.handleProceed,
      "DONE": self.action_handler.handleDone,
      "RETRY": self.action_handler.handleRetry,
    }

  def run_skill_installation_mode(self):
    actor_skills, installed_skills = self.skill_installation_mode.run(self.task, use_autonomy_mode=True)

    self.skills = actor_skills
    self.installed_skills = installed_skills

  def run(self):
    while not self.hard_exit:

      logger.info(f"""
Running iteraton {self.iterations} out of {settings.orchestrator.autonomy_orchestrator.max_total_iterations}
Enforcing Iteration Limit: {settings.orchestrator.autonomy_orchestrator.enforce_max_total_iterations}

Task = {self.task}

Additional Context:
{self.additional_context}

Skills:
{self.skills}

Runtime Skills:
{self.runtime_skills}

Punishment Tally:
f"{self.iterations} out of maximum {settings.orchestrator.autonomy_orchestrator.max_total_iterations}"

History:
{self.history}

Available Skill Actions: 
{self.skill_orchestrator.list_actions()}
""")

      if settings.orchestrator.autonomy_orchestrator.enforce_max_total_iterations:
        if self.iterations >= settings.orchestrator.autonomy_orchestrator.max_total_iterations:
          self.hard_exit = True
      
      self.step_result = actor_model.do_autonomy_step(
        task=self.task, 
        additional_context=self.additional_context, 
        skills=self.skills, 
        runtime_skills=self.runtime_skills, 
        punishment_tally=f"{self.iterations} out of maximum {settings.orchestrator.autonomy_orchestrator.max_total_iterations}", 
        history=self.history,
        available_skill_actions=self.skill_orchestrator.list_actions()
        )
      
      self.iterations += 1

      if self.step_result.get('install_skills', None):
        skills_requested = self.step_result['skills']
        skills_not_installed = [skill for skill in skills_requested if skill not in self.installed_skills]

        skills_already_installed = [skill for skill in skills_requested if skill not in skills_not_installed]

        installable_skills = [skill for skill in skills_not_installed if self.skill_orchestrator.has_skill(skill)]
        unresolvable = [skill for skill in skills_requested if skill not in installable_skills]

        if unresolvable:
          logger.warning(f"Requested skills not found: {unresolvable}")
          self.additional_context = self.additional_context + f"\nThe following requested skills could not be found: {unresolvable}. Proceed without them."
        
        if skills_already_installed:
          logger.warning(f"Not installing: {skills_already_installed}, already installed")
          self.additional_context = self.additional_context + f'\n The following skills are already installed: {skills_already_installed}, here are all available actions for a refresher: {self.skill_orchestrator.list_actions()}'

        self.runtime_skills = self.skill_orchestrator.load_all_requested_skills(installable_skills, 'actor')
      
      else:
        action_result = parse_action(self.step_result)
        logger.info(f"""
Output of Iteration: {self.iterations}

{action_result}
""")
        time.sleep(settings.orchestrator.action_settle_time)

        successful_run = False

        if isinstance(action_result, dict):
          self.action_handler.handle_skill_invocations(action_result)
          successful_run = True
        elif action_result in self.handlers.keys():
          handler = self.handlers[action_result]
          handler()
          successful_run = True
        else:
          logger.warning(f"Unhandled action result: {action_result}")
          self.additional_context = self.additional_context + f"\n Unhandled action result: {action_result}. You may have hallucinated it. Proceeding without handling it, and history not appended."

      if successful_run:
        self.history = self.history + f"\n {self.step_result.get('history', "")}"
        self.runtime_skills = None

if __name__ == "__main__":
  task = "Open a blank document in Microsoft Word and type a full comprehensive report on dinosaurs, all of what you know, neatly formatted with headings and bullet points."

  if not settings.orchestrator.use_experimental_autonomy_mode:
    plan = models.planner_model.make_plan(task)
    printed_plan = json.dumps(plan, indent=2)
    print(printed_plan)

    step_orchestrator = StepOrchestrator(steps=plan, skills=plan.get("_actor_skills"))
    step_orchestrator.run()
  else:
    autonomy_orchestrator = AutonomyOrchestrator(task=task)
    autonomy_orchestrator.run_skill_installation_mode()
    autonomy_orchestrator.run()