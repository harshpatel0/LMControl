import actor_model
from parse_action import parse_action
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
    
    for iterations in range(1, MAX_ITERATIONS_PER_STEP):
      additional_context = None
      step_result = actor_model.do_step(step, task, additional_context)
      action_result = parse_action(step_result)

      print(f"[STEP_ORCHESTRATOR] Can progress to next step? {action_result}")

      time.sleep(action_settle_time)
      if action_result == "PROCEED":
        step_count = step_count + 1
        break
      elif action_result == "STUCK":
        print(f"[STEP_ORCHESTRATOR] The Actor Model claims it is stuck, running another iteration with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
      elif action_result == "DONE":
        print("[STEP_ORCHESTRATOR] The actor model claims the task is done, hard exitting...")
        hard_exit = True
        break
      elif action_result == "RETRY":
        print(f"[STEP_ORCHESTRATOR] The actor model or action parser is requesting a retry, retrying with added context {iterations+1}/{MAX_ITERATIONS_PER_STEP}")
  
perform_steps(
{
  "task": "Open a specific YouTube video.",
  "steps": [
    {
      "id": 1,
      "instruction": "Click Microsoft Edge in the taskbar.",
      "expected_result": "Microsoft Edge window is the active window.",
      "fallback": "Press Windows Key + [Number corresponding to Edge's position in taskbar]"
    },
    {
      "id": 2,
      "instruction": "In the address bar of Microsoft Edge, type 'youtube.com' and press Enter.",
      "expected_result": "The YouTube homepage loads in the active Edge tab.",
      "fallback": "Press Alt+D to focus the address bar, then type 'youtube.com' and press Enter."
    },
    {
      "id": 3,
      "instruction": "Click the search icon (magnifying glass) or press Ctrl+K to activate the search bar, then type 'Taarak Metha ka Ooltah Chasmah Video'.",
      "expected_result": "The search query is entered into the YouTube search bar.",
      "fallback": "Press Ctrl+L to focus the address bar, type 'youtube.com/search?q=' followed by the title, and press Enter."
    },
    {
      "id": 4,
      "instruction": "Press Enter or click the search button to execute the search.",
      "expected_result": "The YouTube search results page for the specified video appear.",
      "fallback": "Press Enter key."
    },
    {
      "id": 5,
      "instruction": "Click the video link/thumbnail titled 'Taarak Metha ka Ooltah Chasmah Video' from the search results.",
      "expected_result": "The video 'Taarak Metha ka Ooltah Chasmah Video' begins playing in the active Edge tab.",
      "fallback": "If multiple links appear, click the top search result link/thumbnail."
    }
  ]
}
)