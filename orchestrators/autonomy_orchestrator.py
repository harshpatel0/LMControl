import time
import models.actor_model as actor_model
from context_provider import ContextProvider
from orchestrators.action_handlers import call_action
from skills.skill_orchestrator import skill_orchestrator
from models.model_definitions import SkillInstallationMode
from utils.logger import logger
from settings.settings import settings
from result_types import ActionResult, KodoSkillResult


class AutonomyOrchestrator:
    def __init__(self, task):
        self.task = task
        self.iterations = 0
        self.additional_context = ""
        self.context_provider = ContextProvider()
        self.skill_installation_mode = SkillInstallationMode()
        self.skill_orchestrator = skill_orchestrator
        self.hard_exit = False
        self.skills = ""

        self.punishment_tally = ""
        self.history = ""
        self.runtime_skills = None
        self.last_action = None

        self.installed_skills = []
        self.step_count = 0
        self.replan_history = []
        self.temp_task = None

    def _apply(self, ar: ActionResult) -> None:
        if ar.step_count is not None:
            self.step_count = ar.step_count
        if ar.iterations is not None:
            self.iterations = ar.iterations
        if ar.replan_history is not None:
            self.replan_history = ar.replan_history
        if ar.additional_context is not None:
            self.additional_context = ar.additional_context
        if ar.hard_exit is not None:
            self.hard_exit = ar.hard_exit
        if ar.temp_task is not None:
            self.temp_task = ar.temp_task

    def run_skill_installation_mode(self):
        actor_skills, installed_skills = self.skill_installation_mode.run(self.task)

        self.skills = actor_skills
        if isinstance(installed_skills, (list, tuple, set)):
            self.installed_skills = list(installed_skills)
        elif installed_skills is None:
            self.installed_skills = []
        else:
            self.installed_skills = [installed_skills]

    def _truncate_history(self, history: str, max_chars: int = 4000) -> str:
        """Keep only the most recent entries of the history string, dropping oldest.
        Uses ~4 chars/token heuristic to stay within context window budgets.
        """
        if not history or len(history) <= max_chars:
            return history
        entries = history.strip().split("\n")
        trimmed = []
        for entry in reversed(entries):
            candidate = "\n".join([entry] + trimmed)
            if len(candidate) > max_chars:
                break
            trimmed.insert(0, entry)
        return "\n".join(trimmed) if trimmed else ""

    def run(self):
        while not self.hard_exit:

            # Truncate history to prevent unbounded context growth
            truncated_history = self._truncate_history(self.history)

            max_iter = settings.orchestrator.autonomy_orchestrator.max_total_iterations

            logger.info(f"""
Running iteration {self.iterations+1} out of {max_iter}

Task = {self.task}

Additional Context:
{self.additional_context}

Skills:
{self.skills}

History (truncated):
{truncated_history}
""")

            if max_iter > 0 and self.iterations >= max_iter:
                self.hard_exit = True

            last_action_info = ""
            if getattr(self, "step_result", {}) and self.step_result.get("action"):
                last_action_info = (
                    f"[LAST ACTION] action='{self.step_result['action']}' "
                    f"args={{{', '.join(f'{k}={v!r}' for k, v in self.step_result.items() if k != 'action')}}}\n"
                )

            punishment_tally = None
            if max_iter > 0:
                punishment_tally = f"Iteration {self.iterations+1} out of maximum {max_iter}\n{last_action_info}"

            try:
                self.step_result = actor_model.do_step(
                    task=self.task,
                    additional_context=self.additional_context,
                    skills=self.skills,
                    runtime_skills=self.runtime_skills,
                    punishment_tally=punishment_tally,
                    history=self.history,
                    available_skill_actions=self.skill_orchestrator.list_actions(),
                )
            except KeyboardInterrupt:
                exit(1)
            except Exception as e:
                logger.error(f"Autonomy step failed: {e}")
                self.step_result = {
                    "action": "retry",
                    "message": f"Step execution error: {e}",
                }

            self.iterations += 1

            if self.step_result.get("install_skills", None):
                skills_requested = self.step_result["skills"]
                skills_not_installed = [
                    skill
                    for skill in skills_requested
                    if skill not in self.installed_skills
                ]

                skills_already_installed = [
                    skill
                    for skill in skills_requested
                    if skill not in skills_not_installed
                ]

                installable_skills = [
                    skill
                    for skill in skills_not_installed
                    if self.skill_orchestrator.has_skill(skill)
                ]
                unresolvable = [
                    skill
                    for skill in skills_requested
                    if skill not in installable_skills
                ]

                if unresolvable:
                    logger.warning(f"Requested skills not found: {unresolvable}")
                    self.additional_context = (
                        self.additional_context
                        + f"\nThe following requested skills could not be found: {unresolvable}. Proceed without them."
                    )

                if skills_already_installed:
                    logger.warning(
                        f"Not installing: {skills_already_installed}, already installed"
                    )
                    self.additional_context = (
                        self.additional_context
                        + f"\n The following skills are already installed: {skills_already_installed}, here are all available actions for a refresher: {self.skill_orchestrator.list_actions()}"
                    )

                self.runtime_skills = self.skill_orchestrator.load_all_requested_skills(
                    installable_skills, "actor"
                )

            else:
                ar = call_action(
                    action=self.step_result,
                    iterations=self.iterations,
                    in_autonomy=True,
                    additional_context=self.additional_context,
                )
                self._apply(ar)
                time.sleep(settings.orchestrator.action_settle_time)
