from pc_actions.perform_pc_actions import PCActions
import skills.skill_orchestrator
from utils.logger import logger

skill_orchestrator = skills.skill_orchestrator.Skills()

pc = PCActions(failsafe=True)

import python.run_python_code
pyrun = python.run_python_code.PythonRunner()

def parse_action(action):
  return_command = "PROCEED"

  if skill_orchestrator.can_handle(action.get("action")):
    result = skill_orchestrator.execute(action)
    logger.debug(f"[SkillOrchestrator] {result}")
    return result
  
  # The rest of PC Actions
  match action["action"]:
    case "click":
      logger.debug(f"Clicking at X={action['x']}, Y={action['y']} on element={action.get('element')}")

      try:
        pc.click(
          position_x=int(action["x"]),
          position_y=int(action["y"]),
          button=action.get("button", "left")
        )
      except KeyError:
        return_command = "RETRY"

    case "type":
      pc.type_text(action["text"], action.get("x"), action.get("y"))

    case "submit":
      pc.type_text(action["text"], action.get("x"), action.get("y"))
      pc.press_key('enter')

    case "press_key":
      pc.press_key(action["key"])

    case "press_hotkey":
      pc.press_hotkey(action["keys"])

    case "scroll_v":
      pc.vscroll(
        scroll_amount=action["amount"],
        position_x=action["x"],
        position_y=action["y"]
      )

    case "scroll_h":
      pc.hscroll(
        scroll_amount=action["amount"],
        position_x=action["x"],
        position_y=action["y"]
      )
    
    case "clear_field":
      pc.click(action.get('x'), action.get("y"))
      pc.press_hotkey(['ctrl', 'a'])
      pc.press_key('backspace')
    
    case "python":
      result = pyrun.run(action['code'])
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

  return return_command