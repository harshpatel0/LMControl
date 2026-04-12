import models.actor_model as actor_model
from actor.parse_action import parse_action
import time
import models.planner_model

MAX_ITERATIONS_PER_STEP = 5
ACTION_SETTLE_TIME = 2

# Punishment Settings, punishments arent dealt right now. Maybe a thing in the future.
MAX_PUNISHMENT_SCORE = 500
PUNISHMENT_MODIFIER = 50

def perform_steps(steps, action_settle_time=ACTION_SETTLE_TIME):
  task = steps['task']
  step_list = steps['steps']

  # Runtime Variables
  step_count = 0
  hard_exit = False

  while step_count < len(step_list)*2:
    if hard_exit:
      break

    in_autonomy = step_count >= len(step_list)

    if in_autonomy:
      print("[STEP_ORCHESTRATOR > AUTONOMY MODE] Running in Basic Autonomy Mode")
      step = {
        "instruction": "Autonomy Mode — the planned steps are complete but the task may not be done. Continue independently and call done when finished. Your hand is not going to be held in this mode, so just complete the task how you think you can.",
        "expected_result": "The original task is fully complete."
      }
    else:
      step = step_list[step_count]

    print(f"[STEP_ORCHESTRATOR] Step Location: {step_count+1}/{len(step_list)}")

    additional_context = None
    
    for iterations in range(1, MAX_ITERATIONS_PER_STEP):
      if iterations == MAX_ITERATIONS_PER_STEP:
        print("[STEP_ORCHESTRATOR] Cutting my losses while I can, quitting.")
        hard_exit = True
        break
      
      step_result = actor_model.do_step(step, task, additional_context, punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step")
      action_result = parse_action(step_result)

      print(f"[STEP_ORCHESTRATOR] Action Result: {action_result}")

      time.sleep(action_settle_time)
      if action_result == "PROCEED":
        step_count = step_count + 1
        additional_context = None
        break

      elif action_result == "STUCK":
        print(f"[STEP_ORCHESTRATOR] The Actor Model claims it is stuck, running another iteration with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
        additional_context = f"{step_result['message']}"
      
      elif action_result == "DONE":
        print("[STEP_ORCHESTRATOR] The actor model claims the task is done, hard exitting...")
        hard_exit = True
        break

      elif action_result == "REPLAN":
        next_action = step_result.get('next', '')
        print(f"[STEP_ORCHESTRATOR] Replan requested, overriding instruction.")
        additional_context = f"Ignore the original step instruction. Execute this single atomic action only: {next_action}"
      
      elif action_result == "RETRY":
        print(f"[STEP_ORCHESTRATOR] The actor model or action parser is requesting a retry, retrying with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
        try:
          additional_context = f"{step_result['message']}"
        except Exception:
          additional_context = f"The Action Parser was not able to parse your action, you might have sent in the wrong format, or not populated some fields. Be more careful in this run!"
      
      else:
        Exception("Theres a programming issue, action result cannot reach here. Maybe the LLM hallucinated an action, or you didnt deal with one")
  
perform_steps(
  # steps=models.planner_model.make_plan("Open a Taarak Metha ka OOltah Chasmah Video on YouTube"),
  steps=models.planner_model.make_plan("Search horses on Google"),
  action_settle_time=1
)