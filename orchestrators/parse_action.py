from interactions.pc_actions.perform_pc_actions import PCActions
from interactions.skills.skill_orchestrator import skill_orchestrator
from utils.logger import logger

import time

pc = PCActions(failsafe=True)

import interactions.python.run_python_code

pyrun = interactions.python.run_python_code.PythonRunner()

from interactions.mcps.mcp_registry import mcp_registry
from interactions.mcps.mcp_loop import run_async

from mcp.types import CallToolResult, TextContent
from result_types.PrimitiveActionResult import PrimitiveActionResult
from result_types.KodoSkillResult import KodoSkillResult

from interactions.direct_app_control.direct_app_control_handler import (
    direct_app_handler,
)

from interactions.direct_app_control.types import *


def parse_action(
    action: dict,
) -> (
    PrimitiveActionResult
    | CallToolResult
    | KodoSkillResult
    | DirectAppConnectionResult
    | DirectAppProcessList
    | DirectAppControlListResult
    | DirectAppInteractionResult
):
    return_command = "PROCEED"
    error_message = ""

    if skill_orchestrator.can_handle(action.get("action")):
        result = skill_orchestrator.execute(action)
        logger.debug(f"[SkillOrchestrator] {result}")
        return result

    action_type = action["action"]

    if action_type in [
        "list_processes",
        "connect",
        "list_controls",
        "interact",
        "expand",
        "collapse",
        "set_value",
        "scroll",
        "set_range_value",
        "get_grid_item",
        "minimize_window",
        "maximize_window",
        "restore_window",
        "close_window",
    ]:
        return direct_app_handler.handle_direct_action(action=action)

    match action["action"]:
        case "mcp_tool_call":

            mcp_call = getattr(mcp_registry, "call", None) or getattr(
                mcp_registry, "call_tool", None
            )

            if not mcp_registry.check_tool(action["tool"]):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Tool '{action['tool']}' does not exist in the MCP registry.",
                        )
                    ],
                    isError=True,
                )

            if mcp_call is None:
                raise AttributeError(
                    "mcps.mcp_registry has no callable 'call' or 'call_tool'"
                )
            tool_call_result: CallToolResult = run_async(
                mcp_call(action["tool"], action["arguments"])
            )
            return tool_call_result

        case "click":
            logger.debug(
                f"Clicking at X={action['x']}, Y={action['y']} on element={action.get('element')}"
            )

            try:
                pc.click(
                    position_x=int(action["x"]),
                    position_y=int(action["y"]),
                    button=action.get("button", "left"),
                )

            except KeyError:
                error_message = "Missing Arguments"
                return_command = "RETRY"

        case "double_click":
            logger.debug(
                f"Double Clicking at X={action['x']}, Y={action['y']} on element={action.get('element')}"
            )

            try:
                pc.double_click(
                    position_x=int(action["x"]),
                    position_y=int(action["y"]),
                    button=action.get("button", "left"),
                )
            except KeyError:
                error_message = "Missing Arguments"
                return_command = "RETRY"

        case "type":
            x = int(action["x"]) if action.get("x") is not None else None
            y = int(action["y"]) if action.get("y") is not None else None
            pc.type_text(action["text"], x, y)

        case "submit":
            pc.type_text(action["text"], action.get("x"), action.get("y"))
            pc.press_key("enter")

        case "press_key":
            pc.press_key(action["key"])

        case "press_hotkey":
            pc.press_hotkey(action["keys"])

        case "drag":
            pc.drag(
                from_x=int(action["from_x"]),
                from_y=int(action["from_y"]),
                to_x=int(action["to_x"]),
                to_y=int(action["to_y"]),
                button=action.get("button", "left"),
            )

        case "scroll_v":
            pc.vscroll(
                scroll_amount=action["amount"],
                position_x=action["x"],
                position_y=action["y"],
            )

        case "scroll_h":
            pc.hscroll(
                scroll_amount=action["amount"],
                position_x=action["x"],
                position_y=action["y"],
            )

        case "clear_field":
            pc.click(action.get("x"), action.get("y"))
            time.sleep(0.1)  # let the target element receive focus
            pc.press_hotkey(["ctrl", "a"])
            time.sleep(0.05)  # let select-all complete
            pc.press_key("backspace")

        case "python":
            result = pyrun.run(action["code"])
            return result

        case "done":
            return_command = "DONE"

        case "stuck":
            return_command = "STUCK"

        case "retry":
            return_command = "RETRY"

        case "replan":
            return_command = "REPLAN"

        case _:
            logger.warning(f"Unknown action: {action['action']}")
            return_command = "RETRY"

    if not skill_orchestrator.can_handle(action.get("action")):
        error_message = f"The skill {action.get("action")} does not exist."

    return PrimitiveActionResult(
        action=action, command=return_command, error_message=error_message
    )
