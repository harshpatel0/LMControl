from interactions.direct_app_control.direct_app_control import DirectAppController
from interactions.direct_app_control.types import *


class DirectAppControlHandler:
    def __init__(self) -> None:
        self.direct_app_controller = DirectAppController()

    def handle_direct_action(self, action: dict):
        if action["action"] not in ["list_processes", "connect"]:
            try:
                control_id = action["control_id"]
            except Exception:
                return DirectAppInteractionResult(
                    success=False,
                    message=f"Control ID is a missing required parameter for action: {action["action"]}",
                )

        match action["action"]:
            case "list_processes":
                return self.direct_app_controller.list_processes()

            case "connect":
                try:
                    process_id = action["process_id"]
                except Exception:
                    return DirectAppConnectionResult(
                        success=False,
                        message="Process ID is a missing required parameter",
                    )

                return self.direct_app_controller.connect(process_id=process_id)

            case "list_controls":
                return self.direct_app_controller.list_controls()

            case "interact":
                return self.direct_app_controller.interact(control_id=control_id)

            case "expand":
                return self.direct_app_controller.expand(control_id=control_id)

            case "collapse":
                return self.direct_app_controller.collapse(control_id=control_id)

            case "set_value":
                try:
                    value = action["value"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Value 'value' is a missing required parameter for action: {action["action"]}",
                    )
                return self.direct_app_controller.set_value(
                    control_id=control_id, value=value
                )

            case "scroll":
                try:
                    amount = action["amount"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Amount 'amount' is a missing required parameter for action: {action["action"]}",
                    )

                if amount not in ["line", "page"]:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Amount 'amount' for action: {action["action"]} can only be 'line' or 'page'",
                    )

                try:
                    direction = action["direction"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Scroll direction 'direction' is a missing required parameter for action: {action["action"]}",
                    )

                if direction not in ["up", "down", "left", "right"]:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Scroll direction 'direction' for action: {action["action"]} can only be 'up', 'down', 'left', or 'right'",
                    )

                return self.direct_app_controller.scroll(
                    control_id=control_id, amount=amount, direction=direction
                )

            case "set_range_value":
                try:
                    value = action["value"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"value 'value' is a missing required parameter for action: {action["action"]}",
                    )

                try:
                    value = float(value)
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"value 'value' for action: {action["action"]} has to be a floating point number",
                    )

                return self.direct_app_controller.set_range_value(
                    control_id=control_id, value=value
                )

            case "minimize_window":
                return self.direct_app_controller.minimize_window(control_id=control_id)

            case "maximize_window":
                return self.direct_app_controller.maximize_window(control_id=control_id)

            case "close_window":
                return self.direct_app_controller.close_window(control_id=control_id)

            case "restore_window":
                return self.direct_app_controller.restore_window(control_id=control_id)

            case "get_grid_item":
                try:
                    row = action["row"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Row 'row' is a missing required parameter for action: {action["action"]}",
                    )

                try:
                    col = action["col"]
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Column 'col' is a missing required parameter for action: {action["action"]}",
                    )

                try:
                    row = int(row)
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Row 'row' for action: {action["action"]} has to be a number",
                    )

                try:
                    col = int(col)
                except Exception:
                    return DirectAppInteractionResult(
                        success=False,
                        message=f"Column 'col' for action: {action["action"]} has to be a number",
                    )

                return self.direct_app_controller.get_grid_item(
                    control_id=control_id, row=row, col=col
                )

            case _:
                return DirectAppInteractionResult(
                    success=False,
                    message=f"Action: {action["action"]} does not exist",
                )


direct_app_handler = DirectAppControlHandler()
