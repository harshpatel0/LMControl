from models.model_definitions import ActorModel

import utils.utils as utils
from utils.logger import logger
from utils.globals import (
    ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE,
    ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE,
)

from server.log_stream import web_emitter
from settings.settings import settings

actor_model = ActorModel()


def log_to_debug_file(user_prompt: str, action: dict):
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


def do_step(
    task: str,
    history=None,
    additional_context: str | None = None,
    punishment_tally=None,
    skills=None,
    runtime_skills=None,
    available_skill_actions=None,
):

    cfg = (
        settings.models.autonomy_actor
        if settings.orchestrator.use_autonomy_mode
        else settings.models.actor
    )
    model_provider = cfg.provider
    model_name = cfg.model_name

    actor_model.construct_system_prompt(task=task, skills=skills)

    user_prompt = actor_model.construct_user_prompt(
        task=task, instruction=None, expected_result=None
    )

    if additional_context:
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

    chat_response = actor_model.run(user_prompt)
    response = chat_response.content

    web_emitter.metrics(
        {
            "tokens_in": chat_response.input_tokens,
            "tokens_out": chat_response.output_tokens,
            "elapsed_ms": chat_response.total_duration_ms,
            "model": model_name,
            "provider": model_provider,
            "mode": "autonomy" if settings.orchestrator.use_autonomy_mode else "actor",
        }
    )

    raw = utils.strip_markdown_json(response).strip()

    action, parse_error = utils.try_parse_json(raw)

    if not action:
        logger.warning(
            f"[ACTOR MODEL] JSON parse failed: {parse_error}. "
            f"Raw response: {raw[:200]}"
        )
        action = {
            "action": "retry",
            "message": f"Model returned unparseable response. {parse_error}. Raw output:\n{raw[:500]}",
        }

    if ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE:
        log_to_debug_file(user_prompt=user_prompt, action=action)

    logger.debug(action)

    web_emitter.action(action)
    web_emitter.thinking(chat_response.thinking if chat_response.thinking else "")

    logger.info(
        f"Tokens Used: Input: {chat_response.input_tokens} tokens, Output: {chat_response.output_tokens} tokens. Took {round((chat_response.total_duration_ms)/1000)} seconds"
    )

    logger.info(f"Thinking: \n\t{chat_response.thinking}")

    return action
