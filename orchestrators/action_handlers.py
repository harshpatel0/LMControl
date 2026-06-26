from utils.logger import logger
import json
from mcp.types import CallToolResult, TextContent
from settings.settings import settings

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
        if not self.in_autonomy:
            logger.info(
                f"The Actor Model claims it is stuck, running another iteration with added context {self.orchestrator.iterations+1}/{MAX_ITERATIONS_PER_STEP}"
            )
        else:
            logger.info(
                f"The Actor Model claims it is stuck, running another iteration with added context"
            )

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

    def handle_mcp_tool_call_result(self, action_result):
        logger.debug(msg=action_result)

        text_output = [
            block.text
            for block in action_result.content
            if isinstance(block, TextContent)
        ]

        self.orchestrator.additional_context = f"""
# MCP Tool Call Result

Text Output:
    {text_output}

Has any error occurred? {action_result.isError}
"""
        return "CONTINUE"
