import models.actor_model as actor_model
from parse_action import parse_action
import time
import models.planner_model
from context_provider import ContextProvider
from pc_actions.perform_pc_actions import PCActions
import json
from utils.logger import logger
from settings.settings import settings

from models.model_definitions import SkillInstallationMode
from skills.skill_orchestrator import Skills

pc_actions = PCActions()

MAX_ITERATIONS_PER_STEP = (
    settings.orchestrator.planner_architecture.max_iterations_per_step
)
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
        element = self.orchestrator.step_result.get("element", "")

        if element:
            ui_tree = self.orchestrator.context_provider.get_ui_tree()
            ui_text = "\n".join(ui_tree) if isinstance(ui_tree, list) else str(ui_tree)
            if element not in ui_text:
                logger.warning(
                    f"Actor claimed DONE, but '{element}' not found in UI tree. Forcing retry."
                )
                self.orchestrator.additional_context += (
                    f"You claimed to be done, but '{element}' is not present in the current UI tree. "
                    "Please ensure the action completed correctly.\n"
                )
                return "CONTINUE"

        self.orchestrator.hard_exit = True
        return "BREAK"

    def handleStuck(self):
        logger.info(
            f"The Actor Model claims it is stuck, running another iteration with added context {self.orchestrator.iterations+1}/{MAX_ITERATIONS_PER_STEP}"
        )
        # Include diagnostic info: the last action attempted and its result.
        last_action = self.orchestrator.step_result.get("action", "unknown")
        last_args = {
            k: v for k, v in self.orchestrator.step_result.items() if k != "action"
        }
        self.orchestrator.additional_context = (
            f"[DIAGNOSTIC] Last action was '{last_action}' with args: {json.dumps(last_args)}.\n"
            f"{self.orchestrator.step_result.get('message', '')}" + "\n"
        )
        return "CONTINUE"

    def handleReplan(self, step_result):
        next_action = step_result.get("next", "")
        self.orchestrator.replan_history.append(next_action)

        # Normalize replan entries by lowercasing and stripping whitespace
        # so minor wording differences don't mask a real loop.
        normalized = [a.strip().lower() for a in self.orchestrator.replan_history]
        tail = (
            normalized[-MAX_REPLAN_LOOP:]
            if len(normalized) >= MAX_REPLAN_LOOP
            else normalized
        )

        if len(tail) == MAX_REPLAN_LOOP and len(set(tail)) == 1:
            logger.critical(
                f"Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit."
            )
            self.orchestrator.hard_exit = True

        logger.info(f"[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")

        self.orchestrator.temp_task = next_action
        self.orchestrator.additional_context = (
            self.orchestrator.additional_context
            + "The current task is from the previous actor, instructing you what to do, when you are done with it, call an action and do not emit done under any circumstances"
            + "\n"
        )
        return "CONTINUE"

    def handleRetry(self):
        logger.warning(
            f"[STEP_ORCHESTRATOR] Retrying with added context {self.orchestrator.iterations+1}/{MAX_ITERATIONS_PER_STEP}"
        )
        try:
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + f"{self.orchestrator.step_result['message']}"
                + "\n"
            )
        except Exception:
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + "The Action Parser was not able to parse your action. Be more careful with the format in this run."
                + "\n"
            )
        return "CONTINUE"

    def handle_skill_invocations(self, action_result):
        logger.debug(action_result)
        action_result_type = action_result.get("result")
        action_result_stderr = action_result.get("stderr", "No errors!")
        action_result_stdout = action_result.get(
            "stdout", "Script / Skill outputted nothing"
        )

        logger.debug(
            f"Action Result Type for Custom Actions: {action_result_type}\nAction Result stderr: {action_result_stderr}\nAction Result stdout: {action_result_stdout}"
        )

        if action_result_type == "IMPORT_DISCOVERY_ERROR":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + f"The modules in the code/skill could not be discovered, and so cannot be run without errors\nHere are the errors returned: {action_result_stderr}\nHint: instead of inline Python, use the installed skills if a skill can be used to perform the task"
                + "\n"
            )
            return "CONTINUE"

        elif action_result_type == "PACKAGE_INSTALL_ERROR":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + f"The modules in the code/skill could not be installed, and so the code/skill cannot be run without errors\nHere are the errors returned: {action_result_stderr}"
                + "\n"
            )
            return "CONTINUE"

        elif action_result_type == "TIMEOUT":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context + f"""
The code/skill took too long to run and was killed prematurely. Here are the logs of its output.

## Output
{action_result_stdout}

## Errors
{action_result_stderr}
""" + "\n"
            )
            return "CONTINUE"

        elif action_result_type == "PY_EXCEPTION":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + f"The subprocess running your code/skill produced an exception\n{action_result_stderr}"
            )
            return "CONTINUE"

        elif action_result_type == "ERROR":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context
                + f"The code/skill ran with errors\n{action_result_stderr}"
            )
            return "CONTINUE"

        elif action_result_type == "SUCCESS":
            self.orchestrator.additional_context = (
                self.orchestrator.additional_context + f"""
The code/skill ran successfully, here are the logs of the Output and Error Stream

## Output
{action_result_stdout}
""" + "\n"
            )
            if not self.in_autonomy:
                self.orchestrator.step_count += 1

            self.orchestrator.replan_history = []
            self.orchestrator.additional_context = ""
            return "BREAK"

        else:
            logger.error(
                f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
            )
            raise Exception(
                f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
            )


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
                except Exception as e:
                    logger.error(f"Step execution failed: {e}")
                    self.step_result = {
                        "action": "retry",
                        "message": f"Step execution error: {e}",
                    }
                action_result = parse_action(self.step_result)

                logger.debug(f"Action Result: {action_result}")
                time.sleep(settings.orchestrator.action_settle_time)

                signal = None

                if isinstance(action_result, str):
                    handler = self.handlers[action_result]
                    if action_result == "REPLAN":
                        handler(self.step_result)
                    else:
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
        self.last_action = None

        self.installed_skills = []

        self.action_handler = ActionHandlers(orchestrator=self, in_autonomy=True)
        self.handlers = {
            "PROCEED": self.action_handler.handleProceed,
            "DONE": self.action_handler.handleDone,
            "RETRY": self.action_handler.handleRetry,
        }

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
Running iteration {self.iterations} out of {max_iter}

Task = {self.task}

Additional Context:
{self.additional_context}

Skills:
{self.skills}

Runtime Skills:
{self.runtime_skills}

History (truncated):
{truncated_history}

Available Skill Actions:
{self.skill_orchestrator.list_actions()}
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
                punishment_tally = f"Iteration {self.iterations} out of maximum {max_iter}\n{last_action_info}"

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
                    self.additional_context = (
                        self.additional_context
                        + f"\n Unhandled action result: {action_result}. You may have hallucinated it. Proceeding without handling it, and history not appended."
                    )

            if successful_run:
                skill_output = ""
                if isinstance(action_result, dict):
                    stdout = action_result.get("stdout", "")
                    stderr = action_result.get("stderr", "")
                    if stdout or stderr:
                        skill_output = (
                            f"\n[Skill Result] stdout: {stdout} | stderr: {stderr}"
                        )
                self.history = (
                    self.history
                    + f"\n {self.step_result.get('history', '')}{skill_output}"
                )
                self.runtime_skills = None

                # Guard against the actor repeating the same action — if the last
                # two actions are identical the actor is likely stuck in a loop.
                if self.last_action is not None and self.step_result.get(
                    "action"
                ) == self.last_action.get("action"):
                    # Allow one retry with the same action before bailing
                    if getattr(self, "_same_action_count", 0) == 0:
                        self._same_action_count = 1
                        self.additional_context += (
                            f"[WARNING] You just performed '{self.last_action['action']}' and nothing changed. "
                            "Try a different approach.\n"
                        )
                    else:
                        self.additional_context += (
                            f"[CRITICAL] You repeated '{self.last_action['action']}' twice without success. "
                            "Stop and try a completely different approach.\n"
                        )
                        self.hard_exit = True
                else:
                    self._same_action_count = 0
                self.last_action = self.step_result


def run_externally(task: str, mode_override: str | None = None):
    is_using_autonomy_mode = settings.orchestrator.use_autonomy_mode

    if mode_override:
        if mode_override == "planner-actor":
            is_using_autonomy_mode = False
        elif mode_override == "autonomy":
            is_using_autonomy_mode = True

    if is_using_autonomy_mode:
        autonomy_orchestrator = AutonomyOrchestrator(task=task)
        autonomy_orchestrator.run_skill_installation_mode()
        autonomy_orchestrator.run()
    else:
        plan = models.planner_model.make_plan(task=task)

        step_orchestrator = StepOrchestrator(
            steps=plan, skills=plan.get("_actor_skills")
        )

        step_orchestrator.run()


if __name__ == "__main__":
    task = "Paste my clipboard contents to a file called clipboard_contents.txt, delete the old file if it exists"
    run_externally(task=task)
