import time
import models.actor_model as actor_model
from context_provider import ContextProvider
from orchestrators.action_handlers import call_action
from utils.logger import logger
from settings.settings import settings
from result_types import ActionResult

MAX_ITERATIONS_PER_STEP = (
    settings.orchestrator.planner_architecture.max_iterations_per_step
)
MAX_AUTONOMY_STEPS = settings.orchestrator.planner_architecture.max_autonomy_steps
ACTION_SETTLE_TIME = settings.orchestrator.action_settle_time
MAX_REPLAN_LOOP = settings.orchestrator.planner_architecture.max_replan_loop


class StepOrchestrator:
    def __init__(self, steps, skills):
        self.steps = steps["steps"]
        self.task = steps["task"]
        self.skills = skills

        self.step_list = steps["steps"]

        self.step_count = 0
        self.additional_context = ""
        self.replan_history = []

        self.in_autonomy = False
        self.hard_exit = False

        self.context_provider = ContextProvider()

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

    def run(self):
        while not self.hard_exit:
            self.in_autonomy = self.step_count >= len(self.steps)

            if self.in_autonomy:
                if self.step_count >= len(self.steps) + MAX_AUTONOMY_STEPS:
                    logger.critical("Autonomy budget exhausted, exiting.")
                    break
                logger.info(
                    "[Step Orchestrator > Basic Autonomy Mode] Running in Basic Autonomy Mode"
                )
                step = {
                    "instruction": "Autonomy Mode — the planned steps are complete but the task may not be done. Continue independently and call done when finished. Your hand is not going to be held in this mode, so just complete the task how you think you can.",
                    "expected_result": "The original task is fully complete.",
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
                    logger.info(
                        "Reached Maximum Allowed Iterations per Step, quitting."
                    )
                    self.hard_exit = True
                    break

                last_action_info = ""
                if getattr(self, "step_result", {}) and self.step_result.get("action"):
                    last_action_info = (
                        f"[LAST ACTION] action='{self.step_result['action']}' "
                        f"args={{{', '.join(f'{k}={v!r}' for k, v in self.step_result.items() if k != 'action')}}}\n"
                    )

                try:
                    self.step_result = actor_model.do_step(
                        step,
                        self.task if not self.temp_task else self.temp_task,
                        self.additional_context,
                        punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step\n{last_action_info}",
                        skills=self.skills,
                    )
                except KeyboardInterrupt:
                    exit(1)
                except Exception as e:
                    logger.error(f"Step execution failed: {e}")
                    self.step_result = {
                        "action": "retry",
                        "message": f"Step execution error: {e}",
                    }

                time.sleep(ACTION_SETTLE_TIME)

                ar = call_action(
                    action=self.step_result,
                    step_count=self.step_count,
                    iterations=self.iterations,
                    in_autonomy=self.in_autonomy,
                    additional_context=self.additional_context,
                    replan_history=self.replan_history,
                )
                self._apply(ar)

                if ar.signal == "BREAK":
                    break
