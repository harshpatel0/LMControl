import rootutils

root = rootutils.setup_root(__file__, pythonpath=True)

import json
from models.model_definitions import PlannerModel, SkillInstallationMode
from skills.skill_orchestrator import skill_orchestrator
import utils.utils as utils
from utils.logger import logger

from settings.settings import settings

from server.log_stream import web_emitter

planner_model = PlannerModel()
skill_installation = SkillInstallationMode()


def make_plan(task: str):
    planner_skills, actor_skills = skill_installation.run(task)

    logger.debug(f"Planner skills loaded: {planner_skills is not None}")
    logger.debug(f"Actor skills loaded: {actor_skills is not None}")

    chat_response = planner_model.run(task=task, skills=planner_skills)
    response = chat_response.content

    web_emitter.metrics(
        {
            "tokens_in": chat_response.input_tokens,
            "tokens_out": chat_response.output_tokens,
            "elapsed_ms": chat_response.total_duration_ms,
            "model": settings.models.planner.model_name,
            "provider": settings.models.planner.provider,
            "mode": "autonomy" if settings.orchestrator.use_autonomy_mode else "actor",
        }
    )

    plan, parse_error = utils.try_parse_json(response)

    if plan is None:
        logger.error(f"Planner model returned unparseable JSON: {parse_error}")
        logger.error(f"Raw response: {response[:500]}")
        plan = {"task": task, "steps": [], "_parse_error": parse_error}

    plan.setdefault("_actor_skills", actor_skills)

    web_emitter.plan(plan)
    web_emitter.thinking(chat_response.thinking)

    return plan
