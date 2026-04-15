import rootutils
root = rootutils.setup_root(__file__, pythonpath=True)

from context_provider import ContextProvider
from skills.skill_orchestrator import Skills
import ollama
import json

from utils.strings import Strings
from utils.logger import logger

from settings.settings import settings

skill_orchestrator = Skills()

OUTPUT_FORMAT = "json"

PLANNER_KEEP_ALIVE = 0
ACTOR_KEEP_ALIVE = -1

context_provider = ContextProvider()

class PlannerModel():
  system_prompt = Strings.PLANNER_BASE_SYSTEM_PROMPT

  def __init__(self):
    self.ollama_server=settings.models.ollama_server
    self.output_format=OUTPUT_FORMAT
    self.keep_alive=PLANNER_KEEP_ALIVE
    self.model_name=settings.models.planner.model_name
    self.model_temperature=settings.models.planner.temperature
    
    self.client = ollama.Client(host=self.ollama_server)
  
  def skill_installation_mode(self, task):
    skill_mode_system_prompt = self.system_prompt
    skill_mode_system_prompt = skill_mode_system_prompt + f"""
# Skill Installation Mode

You are currently in Skill Installation Mode.
In this mode, as discussed prior, you have a list of skills available to you, to extend both
yours, and the actor's capabilities. Any installation will add functionality to you and the actor.

Even if a skill does not benefit you but it benefits the actor, install it.

Make sure to install only the skills you need for the task, if none of the skills work for you. Simply return an empty list of skills.
Installing too many skills may slow down planning and execution.

Here are the available skills
{skill_orchestrator.get_skills_summary()}

Here is how to request an install
{{
  "skills": ["skill1", "skill2"]
}}

Some skills also have actions associated with them, as also discussed prior, these actions are treated the same as the other actor's capabilities you saw for the model.
Remember, the skills you install are also installed for the actor.
"""
    
    SKILL_SELECTION_SYSTEM_PROMPT = """
You are the Skill Selector for a Windows 11 Automation System.
Your only job is to analyze a task and select which skills are needed before planning begins.

You will be given a task and a list of available skills.
Return ONLY a valid JSON array of skill name strings.
Return an empty array if no skills are needed.
Do not explain your choices. Do not return anything other than the JSON array.

Example response: ["browser-navigation"]
Example response for no skills needed: []
"""
    # Maybe a watered down skill selection system prompt can make things better. For next trial
    skills_mode_user_prompt = f"Commence skill installation mode. Return a list of skills to install as per required output scheme that you might need to complete this task: {task}"

    response = self.client.chat(
      model=self.model_name,
      messages=[
        {"role": "system", "content": skill_mode_system_prompt},
        {"role": "user", "content": SKILL_SELECTION_SYSTEM_PROMPT}
      ],
      options={
        "temperature": 0.1
      },
      keep_alive=0,
      format="json"
    )

    skills = response.message.content.strip()
    skills = json.loads(skills)
    skills = skills.get("skills", [])

    installable_skills = [skill for skill in skills if skill_orchestrator.has_skill(skill)]

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
    system_prompt = self.system_prompt

    if skills:
      logger.info("[MODEL ORCHESTRATOR] Installing Skills into System Prompt")
      system_prompt = system_prompt + f"""
## Installed Skills
The following skills have been installed and their actions are available to you.
Treat skill actions as first-class actions alongside the standard ones above.

{skills}
"""

    response = self.client.chat(
      model=self.model_name,
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ],
      options={
        "temperature": self.model_temperature
      },
      keep_alive=self.keep_alive,
      format = self.output_format
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
{context_provider.get_ui_tree()}

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
    self.ollama_server=settings.models.ollama_server
    self.output_format=OUTPUT_FORMAT
    self.keep_alive=ACTOR_KEEP_ALIVE
    self.model_name=settings.models.actor.model_name
    self.model_temperature=settings.models.actor.temperature
    
    self.client = ollama.Client(host=self.ollama_server)

  def run(self, user_prompt, attach_screenshot=True, skills=None):
    user_message = {
      "role": "user",
      "content": user_prompt
    }

    if attach_screenshot:
      user_message["images"] = [context_provider.get_screenshot(window_title=context_provider.get_active_window())]

    system_prompt = self.build_system_prompt_with_skills(skills)

    response = self.client.chat(
      model=self.model_name,
      messages=[
        {"role": "system", "content": system_prompt},
        user_message
      ],
      options={
        "temperature": self.model_temperature
      },
      keep_alive=self.keep_alive,
      format=self.output_format
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