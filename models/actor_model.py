from models.ollama.model_definitions import ActorModel
from context_provider import ContextProvider

import utils.utils as utils
from utils.logger import logger
from utils.globals import (
    ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE,
    ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE,
)

context = ContextProvider()
actor_model = ActorModel()

ALLOWED_ACTIONS = {
    "click", "type", "submit", "press_key", "press_hotkey",
    "clear_field", "drag", "scroll_v", "scroll_h",
    "done", "stuck", "retry", "replan", "python",
}

SKILL_ACTIONS = {}


def _validate_action(action: dict) -> tuple[dict | None, str | None]:
    """Validate an action dict has required fields for the action type.
    Returns (action, None) if valid, (None, error_message) if invalid.
    """
    action_type = action.get("action", "")

    if action_type in ("done",):
        return action, None

    if action_type == "retry":
        if "message" not in action:
            action["message"] = "No message provided"
        return action, None

    if action_type not in ALLOWED_ACTIONS and action_type not in SKILL_ACTIONS:
        return None, f"Unknown action type '{action_type}'. Allowed: {', '.join(sorted(ALLOWED_ACTIONS))}"

    if action_type in ("click",) and ("x" not in action or "y" not in action):
        return None, "click action requires 'x' and 'y' coordinates"

    return action, None


def do_step(
    task,
    history=None,
    additional_context=None,
    punishment_tally=None,
    skills=None,
    runtime_skills=None,
    available_skill_actions=None,
):
    user_prompt = actor_model.construct_user_prompt(
        task=task, instruction=None, expected_result=None
    )

    if additional_context or len(additional_context) > 0:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt, additional_context
        )

    if punishment_tally:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=punishment_tally,
            accompanying_message="Here are the number of iterations you have made on this task",
        )

    if available_skill_actions:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=available_skill_actions,
            accompanying_message="The following are the available skill actions, skill actions run like any skill, you are advised on how to run them already",
        )

    if runtime_skills:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=runtime_skills,
            accompanying_message="The following skill(s) was/were just installed and is now available to you:",
        )

    if history:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=history,
            accompanying_message="Here is a running history of everything you said you did:",
        )

    response = actor_model.run(user_prompt, skills=skills)
    raw = utils.strip_markdown_json(response).strip()

    action = None
    parse_error = None

    action, parse_error = utils.try_parse_json(raw)

    if action:
        action, validation_error = _validate_action(action)
        if validation_error:
            action = None
            parse_error = validation_error

    if not action:
        logger.warning(
            f"[ACTOR MODEL] JSON parse/validation failed: {parse_error}. "
            f"Raw response: {raw[:200]}"
        )
        action = {
            "action": "retry",
            "message": (
                f"Model returned unparseable response. {parse_error}. "
                f"Raw output was:\n{raw[:500]}"
            ),
        }

    if ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE:
        with open(
            ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE, "a", encoding="utf-8"
        ) as file:
            file.write(f"""
User Prompt
{"=" * 20}
{user_prompt}

Result
{"=" * 20}
{action}

{"=" * 20}
""")

    logger.debug(action)
    return action
