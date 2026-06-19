import rootutils

root = rootutils.setup_root(__file__, pythonpath=True)

from context_provider import ContextProvider
from context_provider import UITreeHandler
from skills.skill_orchestrator import Skills
from models.provider import get_provider, ChatMessage, ChatResponse

import utils.utils as utils
import utils.strings as Strings
from utils.logger import logger

from settings.settings import settings

skill_orchestrator = Skills()

context_provider = ContextProvider()
ui_tree_handler = UITreeHandler()


USING_AUTONOMY_MODE = settings.orchestrator.use_autonomy_mode


def _get_actor_config():
    if USING_AUTONOMY_MODE:
        return settings.models.autonomy_actor
    return settings.models.actor


def _get_actor_system_prompt():
    if USING_AUTONOMY_MODE:
        return Strings.AUTONOMY_MODE_SYSTEM_PROMPT
    return Strings.ACTOR_BASE_SYSTEM_PROMPT


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    if estimate_tokens(text) <= max_tokens:
        return text
    max_chars = max_tokens * 4
    return text[:max_chars] + "\n...[truncated]"


class SkillInstallationMode:
    def __init__(self):
        pass

    def get_installed_skills(self):
        return skill_orchestrator.loaded_skills

    def run(self, task):
        system_prompt = Strings.SKILL_INSTALLATION_PROMPT
        system_prompt = (
            system_prompt + "\n" + f"{skill_orchestrator.get_skills_summary()}"
        )
        user_prompt = f"Commence skill installation mode. Return a list of skills to install as per required output scheme that you might need to complete this task: {task}"

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        logger.info("Resolving skill issues")

        cfg = settings.models.skill_installation
        provider = get_provider(cfg)
        response = provider.chat(
            messages=messages,
            model=cfg.model_name,
            temperature=cfg.temperature,
            keep_alive=getattr(cfg, "keep_alive", 0),
            output_format="json",
        )

        raw_content = response.content if response else ""
        skills_data, _ = (
            utils.try_parse_json(raw_content) if raw_content else ({}, None)
        )
        skills_data = skills_data or {}
        skills = skills_data.get("skills", [])

        logger.debug(f"Requested Skills from Planner \n {skills}")

        installable_skills = [
            skill for skill in skills if skill_orchestrator.has_skill(skill)
        ]

        logger.debug(f"Installable skills: {installable_skills}")

        if USING_AUTONOMY_MODE:
            actor_skills = skill_orchestrator.load_all_requested_skills(
                installable_skills, "actor"
            )
            return actor_skills, self.get_installed_skills()

        planner_skills = skill_orchestrator.load_all_requested_skills(
            installable_skills, "planner"
        )
        actor_skills = skill_orchestrator.load_all_requested_skills(
            installable_skills, "actor"
        )

        return planner_skills, actor_skills


class PlannerModel:
    system_prompt = Strings.PLANNER_BASE_SYSTEM_PROMPT

    def __init__(self):
        self.base_system_prompt = Strings.PLANNER_BASE_SYSTEM_PROMPT

    def run(self, task, skills=None):
        user_prompt = f"""
# PC Environment
Active Window: "{context_provider.get_active_window()}"

Current Taskbar Setup Accessibility Tree
{context_provider.get_taskbar_elements()}

"""
        system_prompt = ""

        if (
            settings.models.planner.thinking
            and settings.models.planner.model_name.startswith("gemma4")
        ):
            system_prompt = system_prompt + "<|think|>"

        # Populate context that stays constant

        system_prompt = system_prompt + f"""
# PC Environment
OS: {context_provider.WINDOWS_VERSION}
Screen: {context_provider.screen_width}x{context_provider.screen_height}

User Task: {task}
"""

        system_prompt = system_prompt + self.base_system_prompt

        if skills:
            logger.info("[MODEL ORCHESTRATOR] Installing Skills into System Prompt")
            system_prompt = system_prompt + f"""
## Installed Skills
The following skills have been installed and their actions are available to you.
Treat skill actions as first-class actions alongside the standard ones above.

{skills}
"""
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        cfg = settings.models.planner
        provider = get_provider(cfg)
        response = provider.chat(
            messages=messages,
            model=cfg.model_name,
            temperature=cfg.temperature,
            keep_alive=getattr(cfg, "keep_alive", 0),
            output_format="json",
        )

        if response.thinking:
            logger.info(f"Thinking: {response.thinking.strip()}")

        return response.content


class ActorModel:
    def __int__(self):
        self.system_prompt = ""

    def build_system_prompt_with_skills(self, skills=None, task=None):
        active_system_prompt = _get_actor_system_prompt()

        if not skills:
            return active_system_prompt

        return active_system_prompt + f"""
## Installed Skills
The following skills have been installed and their actions are available to you.
Treat skill actions as first-class actions alongside the standard ones above.

{skills}
"""

    def construct_system_prompt(self, task=None, skills=None):
        if self.system_prompt == "":
            system_prompt = ""

            cfg = _get_actor_config()
            thinking_enabled = getattr(cfg, "thinking", False)

            if thinking_enabled and cfg.model_name.startswith("gemma4"):
                system_prompt = system_prompt + "<|think|>"

            system_prompt = system_prompt + self.build_system_prompt_with_skills(skills)

            system_prompt = system_prompt + f"""
# PC Environment
OS: {context_provider.WINDOWS_VERSION}
Screen: {context_provider.screen_width}x{context_provider.screen_height}

    """
            if USING_AUTONOMY_MODE:
                if not task:
                    raise ValueError(
                        "Constructing a system prompt in autonomy mode requires the task"
                    )
                system_prompt = system_prompt + f"""
Task: {task}
"""
            self.system_prompt = system_prompt

        return self.system_prompt

    def construct_user_prompt(self, task, instruction, expected_result):
        user_prompt = f"""
# Step Context
Current Task: {task}
{'Instructions: ' + instruction if instruction else ''}
{'Expected Result ' + expected_result if expected_result else ''}

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

    def return_prompt_with_additional_context(
        self,
        user_prompt,
        additional_context,
        accompanying_message="A previous run of this step resulted in a `STUCK` or `RETRY` handoff, the agent gave instructions to you on how to recover, execute accordingly: ",
    ):
        user_prompt = user_prompt + f"\n{accompanying_message}\n{additional_context}"
        return user_prompt

    def run(self, user_prompt):
        cfg = _get_actor_config()
        attach_screenshot = getattr(cfg, "attach_screenshot_of_active_window", False)

        user_message = ChatMessage(role="user", content=user_prompt)

        if attach_screenshot:
            user_message.images = [
                context_provider.get_screenshot(
                    window_title=context_provider.get_active_window()
                )
            ]

        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            user_message,
        ]

        provider = get_provider(cfg)
        response = provider.chat(
            messages=messages,
            model=cfg.model_name,
            temperature=cfg.temperature,
            keep_alive=getattr(cfg, "keep_alive", 0),
            output_format="json",
        )

        if response.thinking:
            logger.info(f"Thinking: {response.thinking.strip()}")

        content_text = response.content

        if not content_text:
            logger.warning(
                "[Internal Guard] The model returned nothing, simulating a retry call from the step orchestrator"
            )
            return """{
"action": "retry",
"message": "Model returned an empty response, likely due to context overload. Retry with the same step."}
"""
        return content_text
