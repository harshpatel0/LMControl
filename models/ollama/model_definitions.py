import rootutils
root = rootutils.setup_root(__file__, pythonpath=True)

from context_provider import ContextProvider
from context_provider import UITreeHandler
from skills.skill_orchestrator import Skills
import ollama
import json

import utils.strings as Strings
from utils.logger import logger

from settings.settings import settings

skill_orchestrator = Skills()

OUTPUT_FORMAT = "json"

context_provider = ContextProvider()
ui_tree_handler = UITreeHandler()

class PlannerModel():
  system_prompt = Strings.PLANNER_BASE_SYSTEM_PROMPT

  def __init__(self):    
    self.client = ollama.Client(host=settings.models.ollama_server)
  
  def skill_installation_mode(self, task):
    skill_mode_system_prompt = Strings.SKILL_INSTALLATION_PROMPT
    skill_mode_system_prompt = skill_mode_system_prompt + "\n" + f"{skill_orchestrator.get_skills_summary()}"
    skills_mode_user_prompt = f"Commence skill installation mode. Return a list of skills to install as per required output scheme that you might need to complete this task: {task}"

    logger.debug(f"Skill Installation Mode System Prompt\n{skill_mode_system_prompt}")

    response = self.client.chat(
      model=settings.models.planner.modes.skill_installation.model_name,
      messages=[
        {"role": "system", "content": skill_mode_system_prompt},
        {"role": "user", "content": skills_mode_user_prompt}
      ],
      options={
        "temperature": settings.models.planner.modes.skill_installation.temperature
      },
      keep_alive=settings.models.planner.modes.skill_installation.keep_alive,
      format="json"
    )

    skills = response.message.content.strip()
    skills = json.loads(skills)
    skills = skills.get("skills", [])

    logger.debug(f"Requested Skills from Planner \n {skills}")

    installable_skills = [skill for skill in skills if skill_orchestrator.has_skill(skill)]

    logger.debug(f"Installable skills: {installable_skills}")

    planner_skills = skill_orchestrator.load_all_requested_skills(installable_skills, 'planner')
    actor_skills = skill_orchestrator.load_all_requested_skills(installable_skills, 'actor')

    return planner_skills, actor_skills
  
  def run(self, task, skills=None):
    user_prompt = f"""
# PC Environment
OS: {context_provider.WINDOWS_VERSION}
Screen: {context_provider.screen_width}x{context_provider.screen_height}
Pinned Taskbar Apps: {context_provider.get_pinned_apps()}
Installed Apps: {context_provider.installed_apps}
Active Window: "{context_provider.get_active_window()}"

Current Taskbar Setup Accessibility Tree
{context_provider.get_taskbar_elements()}

# Task (What the user wants to do)
> {task}
    """
    system_prompt = ""

    if settings.models.planner.thinking:
      system_prompt = system_prompt + "<|think|>"

    system_prompt = system_prompt + self.system_prompt

    if skills:
      logger.info("[MODEL ORCHESTRATOR] Installing Skills into System Prompt")
      system_prompt = system_prompt + f"""
## Installed Skills
The following skills have been installed and their actions are available to you.
Treat skill actions as first-class actions alongside the standard ones above.

{skills}
"""
      
    logger.debug(f"System Prompt: \n {system_prompt}")

    response = self.client.chat(
      model=settings.models.planner.model_name,
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ],
      options={
        "temperature": settings.models.planner.temperature
      },
      keep_alive=settings.models.planner.keep_alive,
      format=OUTPUT_FORMAT
    )

    logger.info(f"Thinking: {response.message.thinking}") 
    response = response.message.content.strip()
    return response

class ActorModel():
  system_prompt = Strings.ACTOR_BASE_SYSTEM_PROMPT

  def build_system_prompt_with_skills(self, skills=None):
    if not skills:
      return self.system_prompt
    return self.system_prompt + f"""
## Installed Skills
The following skills have been installed and their actions are available to you.
Treat skill actions as first-class actions alongside the standard ones above.

{skills}
"""

  def construct_user_prompt(self, task, instruction, expected_result):
    user_prompt = f"""
# Step Context
Current Task: {task}
Current Step: {instruction}
Success Condition: {expected_result}

# App Context
Active Window: {context_provider.get_active_window()}

Accessibility Tree
ControlType, name, x, y
{ui_tree_handler.request_tree_diffs()}

# System Context
TASKBAR (located at the bottom of the screen, y ≈ {context_provider.screen_height - 20}): 
Taskbar Elements
{context_provider.get_taskbar_elements()}

# Additional Context is provided below (if the orchestrator has anything to say)
"""
    return user_prompt

  def return_prompt_with_additional_context(self, user_prompt, additional_context, accompanying_message = "A previous run of this step resulted in a `STUCK` or `RETRY` handoff, the agent gave instructions to you on how to recover, execute accordingly: "):
    user_prompt = user_prompt + f"\n{accompanying_message}\n{additional_context}"
    return user_prompt

  def __init__(self):
    self.client = ollama.Client(host=settings.models.ollama_server)

  def run(self, user_prompt, skills=None):
    user_message = {
      "role": "user",
      "content": user_prompt
    }

    if settings.models.actor.attach_screenshot_of_active_window:
      user_message["images"] = [context_provider.get_screenshot(window_title=context_provider.get_active_window())]

    system_prompt = ""

    if settings.models.actor.thinking:
      system_prompt = system_prompt + "<|think|>"

    system_prompt = self.build_system_prompt_with_skills(skills)

    response = self.client.chat(
      model=settings.models.actor.model_name,
      messages=[
        {"role": "system", "content": system_prompt},
        user_message
      ],
      options={
        "temperature": settings.models.actor.temperature
      },
      keep_alive=settings.models.actor.keep_alive,
      format=OUTPUT_FORMAT
    )

    if hasattr(response.message, 'thinking') and response.message.thinking:
      logger.info(f"Thinking: {response.message.thinking}")

    response = response.message.content.strip()

    if not response:
      logger.warning("[Internal Guard] The model returned nothing, simulating a retry call from the step orchestrator")
      response = """{
"action": "retry",
"message": "Model returned an empty response, likely due to context overload. Retry with the same step."}
"""
    return response