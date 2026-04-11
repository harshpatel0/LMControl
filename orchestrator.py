import models.actor_model as actor_model
from actor.parse_action import parse_action
import time

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

  while step_count < len(step_list):
    if hard_exit:
      break

    print(f"[STEP_ORCHESTRATOR] Step Location: {step_count+1}/{len(step_list)}")
    step = step_list[step_count]

    additional_context = None
    
    for iterations in range(1, MAX_ITERATIONS_PER_STEP):
      step_result = actor_model.do_step(step, task, additional_context, punishment_tally=f"Iteration {iterations}/{MAX_ITERATIONS_PER_STEP} for this step")
      action_result = parse_action(step_result)

      print(f"[STEP_ORCHESTRATOR] Can progress to next step? {action_result}")

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
      
      elif action_result == "RETRY":
        print(f"[STEP_ORCHESTRATOR] The actor model or action parser is requesting a retry, retrying with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
        try:
          additional_context = f"{step_result['message']}"
        except Exception:
          additional_context = f"The Action Parser was not able to parse your action, you might have sent in the wrong format, or not populated some fields. Be more careful in this run!"
      
      else:
        Exception("Theres a programming issue, action result cannot reach here. Maybe the LLM hallucinated an action, or you didnt deal with one")
  
perform_steps(
{
  "task": "Open a Taarak Metha ka Ooltah Chasmah Video on YouTube",
  "steps": [
    {
      "id": 1,
      "instruction": "Click Microsoft Edge in the taskbar.",
      "expected_result": "Microsoft Edge is the active window.",
      "fallback": "If Edge is not visible, press Win+S, type Microsoft Edge, and press Enter."
    },
    {
      "id": 2,
      "instruction": "Type https://www.youtube.com into the Edge address bar.",
      "expected_result": "The address bar contains 'https://www.youtube.com'.",
      "fallback": "If the address bar is not visible, click the address bar and type 'https://www.youtube.com'."
    },
    {
      "id": 3,
      "instruction": "Press Enter",
      "expected_result": "The YouTube homepage is visible in the Edge browser window.",
      "fallback": "Press Enter key."
    },
    {
      "id": 4,
      "instruction": "Click the YouTube search box and type Taarak Metha ka Ooltah Chasmah",
      "expected_result": "The search box contains 'Taarak Metha ka Ooltah Chasmah'.",
      "fallback": "Press / to focus the YouTube search bar and type 'Taarak Metha ka Ooltah Chasmah'."
    },
    {
      "id": 5,
      "instruction": "Press Enter",
      "expected_result": "The search results page for 'Taarak Metha ka Ooltah Chasmah' is visible in the Edge browser window.",
      "fallback": "Press Enter key."
    },
    {
      "id": 6,
      "instruction": "Click the first video result link titled Taarak Metha ka Ooltah Chasmah",
      "expected_result": "The video page for 'Taarak Metha ka Ooltah Chasmah' is loaded and visible in Edge.",
      "fallback": "Scroll down in the main content area to find the first video result link titled 'Taarak Metha ka Ooltah Chasmah' and click it."
    }
  ]
}
)