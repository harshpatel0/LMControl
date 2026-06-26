from settings.settings import settings
from orchestrators.autonomy_orchestrator import AutonomyOrchestrator
from orchestrators.step_orchestrator import StepOrchestrator
import models.planner_model


def run_externally(task: str, mode_override: str | None = None):
    is_using_autonomy_mode = settings.orchestrator.use_autonomy_mode

    if mode_override:
        if mode_override == "planner-actor":
            is_using_autonomy_mode = False
        elif mode_override == "autonomy":
            is_using_autonomy_mode = True

    if is_using_autonomy_mode:
        autonomy_orchestrator = AutonomyOrchestrator(task=task)

        if not settings.orchestrator.autonomy_orchestrator.no_skill_installation_mode:
            autonomy_orchestrator.run_skill_installation_mode()
        autonomy_orchestrator.run()
    else:
        plan = models.planner_model.make_plan(task=task)

        step_orchestrator = StepOrchestrator(
            steps=plan, skills=plan.get("_actor_skills")
        )

        step_orchestrator.run()


if __name__ == "__main__":
    task = input("What task would you like to run?\n")
    run_externally(task=task)
