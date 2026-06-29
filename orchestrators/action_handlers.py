from utils.logger import logger
import json
from mcp.types import CallToolResult, TextContent
from settings.settings import settings

from orchestrators.parse_action import parse_action

MAX_ITERATIONS_PER_STEP = (
    settings.orchestrator.planner_architecture.max_iterations_per_step
)
MAX_REPLAN_LOOP = settings.orchestrator.planner_architecture.max_replan_loop

from result_types import KodoSkillResult, PrimitiveActionResult, ActionResult


def handle_proceed(
    step_count: int, iterations: int, in_autonomy: bool
) -> ActionResult:
    if not in_autonomy:
        return ActionResult(
            signal="BREAK",
            step_count=step_count + 1,
            iterations=0,
            replan_history=[],
            additional_context="",
        )
    return ActionResult(
        signal="CONTINUE",
        iterations=iterations + 1,
        replan_history=[],
        additional_context="",
    )


def handle_done() -> ActionResult:
    logger.info("The actor model claims the task is done, hard exiting...")
    return ActionResult(signal="BREAK", hard_exit=True)


def handle_stuck(
    action: dict, iterations: int, in_autonomy: bool
) -> ActionResult:
    if not in_autonomy:
        logger.info(
            f"The Actor Model claims it is stuck, running another iteration with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}"
        )
    else:
        logger.info(
            "The Actor Model claims it is stuck, running another iteration with added context"
        )

    last_action = action.get("action", "")
    last_args = {k: v for k, v in action.items() if k != "action"}
    new_context = (
        f"[DIAGNOSTIC] Last action was '{last_action}' with args: {json.dumps(last_args)}.\n"
        f"{action.get('message', '')}" + "\n"
    )
    return ActionResult(
        signal="CONTINUE",
        additional_context=new_context,
        iterations=iterations + 1,
    )


def handle_replan(
    next_action: str, replan_history: list[str], additional_context: str
) -> ActionResult:
    updated_history = replan_history + [next_action]

    normalized = [a.strip().lower() for a in updated_history]
    tail = (
        normalized[-MAX_REPLAN_LOOP:]
        if len(normalized) >= MAX_REPLAN_LOOP
        else normalized
    )

    hard_exit = None
    if len(tail) == MAX_REPLAN_LOOP and len(set(tail)) == 1:
        logger.critical(
            f"Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit."
        )
        hard_exit = True

    logger.info("[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")

    new_context = (
        additional_context
        + "The current task is from the previous actor, instructing you what to do, when you are done with it, call an action and do not emit done under any circumstances"
        + "\n"
    )
    return ActionResult(
        signal="CONTINUE",
        additional_context=new_context,
        temp_task=next_action,
        replan_history=updated_history,
        hard_exit=hard_exit,
    )


def handle_retry(
    additional_context: str, error_message: str, action: dict, iterations: int
) -> ActionResult:
    logger.warning(
        f"[STEP_ORCHESTRATOR] Retrying with added context {iterations}/{MAX_ITERATIONS_PER_STEP}"
    )
    try:
        new_context = (
            additional_context
            + f"{action['message']}"
            + "\t"
            + f"{error_message}"
        )
    except Exception:
        new_context = (
            additional_context
            + "The Action Parser was not able to parse your action. Be more careful with the format in this run."
            + "\n"
            + f"{error_message}"
        )
    return ActionResult(signal="CONTINUE", additional_context=new_context)


def handle_skill_invocations(
    action_result: KodoSkillResult,
    additional_context: str,
    in_autonomy: bool,
    step_count: int,
) -> ActionResult:
    logger.debug(action_result)
    action_result_type = action_result.result
    action_result_stderr = action_result.skill_errors or "No errors!"
    action_result_stdout = (
        action_result.skill_output or "Script / Skill outputted nothing"
    )

    logger.debug(
        f"Action Result Type for Custom Actions: {action_result_type}\nAction Result stderr: {action_result_stderr}\nAction Result stdout: {action_result_stdout}"
    )

    if action_result_type == "IMPORT_DISCOVERY_ERROR":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"The modules in the code/skill could not be discovered, and so cannot be run without errors\nHere are the errors returned: {action_result_stderr}\nHint: instead of inline Python, use the installed skills if a skill can be used to perform the task"
            + "\n",
        )

    elif action_result_type == "PACKAGE_INSTALL_ERROR":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"The modules in the code/skill could not be installed, and so the code/skill cannot be run without errors\nHere are the errors returned: {action_result_stderr}"
            + "\n",
        )

    elif action_result_type == "TIMEOUT":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"""
The code/skill took too long to run and was killed prematurely. Here are the logs of its output.

## Output
{action_result_stdout}

## Errors
{action_result_stderr}
"""
            + "\n",
        )

    elif action_result_type == "PY_EXCEPTION":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"The subprocess running your code/skill produced an exception\n{action_result_stderr}",
        )

    elif action_result_type == "ERROR":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"The code/skill ran with errors\n{action_result_stderr}",
        )

    elif action_result_type == "SUCCESS":
        return ActionResult(
            signal="BREAK",
            step_count=step_count + 1 if not in_autonomy else None,
            replan_history=[],
            additional_context="",
        )

    else:
        logger.error(
            f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
        )
        raise Exception(
            f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
        )


def handle_mcp_tool_call_result(action_result: CallToolResult) -> ActionResult:
    logger.debug(msg=action_result)

    text_output = [
        block.text
        for block in action_result.content
        if isinstance(block, TextContent)
    ]

    new_context = f"""
# MCP Tool Call Result

Text Output:
    {text_output}

Has any error occurred? {action_result.isError}
"""
    return ActionResult(signal="CONTINUE", additional_context=new_context)


def call_action(
    action: dict,
    step_count: int = 0,
    iterations: int = 0,
    in_autonomy: bool = False,
    additional_context: str = "",
    replan_history: list[str] | None = None,
) -> ActionResult:
    """Parse the action and route to the appropriate handler. Pure function — returns ActionResult without side effects."""
    if replan_history is None:
        replan_history = []

    result = parse_action(action=action)

    if isinstance(result, PrimitiveActionResult):
        command = result.command
        if command == "PROCEED":
            return handle_proceed(step_count, iterations, in_autonomy)
        elif command == "DONE":
            return handle_done()
        elif command == "STUCK":
            return handle_stuck(action, iterations, in_autonomy)
        elif command == "REPLAN":
            next_action = action.get("next", "")
            return handle_replan(next_action, replan_history, additional_context)
        elif command == "RETRY":
            return handle_retry(additional_context, result.error_message, action, iterations)

    if isinstance(result, KodoSkillResult):
        return handle_skill_invocations(result, additional_context, in_autonomy, step_count)

    if isinstance(result, CallToolResult):
        return handle_mcp_tool_call_result(result)

    logger.warning("Unexpected result path in call_action")
    raise NotImplementedError(f"Unexpected result type: {type(result)}")
