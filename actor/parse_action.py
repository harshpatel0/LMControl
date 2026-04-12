from actor.perform_pc_actions import PCActions

pc = PCActions(failsafe=True)

def parse_action(action):
  return_command = "PROCEED"

  match action["action"]:
    case "click":
      print(f"DEBUG: Clicking at X={action['x']}, Y={action['y']} on element={action.get('element')}")

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

    case "done":
      return_command = "DONE"

    case "stuck":
      return_command = "STUCK"

    case "retry":
      return_command = "RETRY"
    
    case "replan":
      return_command = "REPLAN"

    case _:
      print(f"Unknown action: {action['action']}")
      return_command = "RETRY"

  return return_command