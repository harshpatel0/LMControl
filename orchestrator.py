import models.actor_model as actor_model
from parse_action import parse_action
import time
import models.planner_model
from context_provider import ContextProvider
from pc_actions.perform_pc_actions import PCActions
import json

pc_actions = PCActions()

context_provider = ContextProvider()

MAX_ITERATIONS_PER_STEP = 10
MAX_AUTONOMY_STEPS = 10
ACTION_SETTLE_TIME = 2
MAX_REPLAN_LOOP = 7 

def perform_steps(steps, action_settle_time=ACTION_SETTLE_TIME, skills=None):
  task = steps['task']
  step_list = steps['steps']

  step_count = 0
  hard_exit = False

  while not hard_exit:
    in_autonomy = step_count >= len(step_list)

    if in_autonomy:
      if step_count >= len(step_list) + MAX_AUTONOMY_STEPS:
        print("[STEP_ORCHESTRATOR] Autonomy budget exhausted, exiting.")
        break
      print("[STEP_ORCHESTRATOR > AUTONOMY MODE] Running in Basic Autonomy Mode")
      step = {
        "instruction": "Autonomy Mode — the planned steps are complete but the task may not be done. Continue independently and call done when finished. Your hand is not going to be held in this mode, so just complete the task how you think you can.",
        "expected_result": "The original task is fully complete."
      }
    else:
      step = step_list[step_count]

    print(f"[STEP_ORCHESTRATOR] Step Location: {step_count+1}/{len(step_list)}")

    additional_context = None
    replan_history = []

    for iterations in range(1, MAX_ITERATIONS_PER_STEP + 1):
      if iterations == MAX_ITERATIONS_PER_STEP:
          print("[STEP_ORCHESTRATOR] Cutting my losses while I can, quitting.")
          hard_exit = True
          break
      
      window_before = context_provider.get_active_window()

      step_result = actor_model.do_step(step, task, additional_context, punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step", skills=skills)
      action_result = parse_action(step_result)

      print(f"[STEP_ORCHESTRATOR] Action Result: {action_result}")

      time.sleep(action_settle_time)

      if action_result == "PROCEED":
        window_after = context_provider.get_active_window()
        action_type = step_result.get('action', '')
        element = step_result.get('element')

        additional_context = None

        if not window_after or window_after.strip() == "":
          print("[STEP_ORCHESTRATOR] PROCEED but active window is empty, handling thumbnail...")
          pc_actions.dismiss_taskbar_thumbnail_overlay()
          time.sleep(2)
          additional_context = "The previous click opened a thumbnail picker. I've tried to dismiss it. Please check the state now."
          continue

        if element and element not in window_after:
          print(f"[STEP_ORCHESTRATOR] Element '{element}' not in title '{window_after}', retrying...")
          # continue
          pass

        if action_type in ('click', 'double_click') and window_before == window_after:
          print("[STEP_ORCHESTRATOR] PROCEED but window unchanged, downgrading to RETRY")
          additional_context = f"You clicked '{step_result.get('element', 'unknown')}' but the window did not change. The element may be wrong or the click had no effect. Try a different element or action."
          continue

        step_count += 1
        replan_history = []
        break

      elif action_result == "STUCK":
        print(f"[STEP_ORCHESTRATOR] The Actor Model claims it is stuck, running another iteration with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
        additional_context = f"{step_result['message']}"

      elif action_result == "DONE":
        window_after = context_provider.get_active_window()
        action_type = step_result.get('action', '')
        element = step_result.get('element', '')

        if not element in window_after:
          print("[STEP_ORCHESTRATOR] Could not find the element requested in the Window Title, assuming it is not done unless the actor flags done again, Forcing a retry")
          continue
        else:
          print("[STEP_ORCHESTRATOR] The actor model claims the task is done, hard exiting...")
          hard_exit = True
          break

      elif action_result == "REPLAN":
        next_action = step_result.get('next', '')
        replan_history.append(next_action)

        if len(replan_history) >= MAX_REPLAN_LOOP and len(set(replan_history[-MAX_REPLAN_LOOP:])) == 1:
          print(f"[STEP_ORCHESTRATOR] Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit.")
          hard_exit = True
          break

        print(f"[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")
        additional_context = f"Ignore the original step instruction. Execute this single atomic action only: {next_action}"

      elif action_result == "RETRY":
        print(f"[STEP_ORCHESTRATOR] Retrying with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
        try:
          additional_context = f"{step_result['message']}"
        except Exception:
          additional_context = "The Action Parser was not able to parse your action. Be more careful with the format in this run."

      else:
        raise Exception(f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type.")

if __name__ == "__main__":
  plan = models.planner_model.make_plan("Run a python code that prints out Hello World on the terminal")
  printed_plan = json.dumps(plan, indent=2)
  print(printed_plan)
  perform_steps(
    steps=plan,
    action_settle_time=1,
    skills=plan.get("_actor_skills")
  )