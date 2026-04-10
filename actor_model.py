import ollama
import json
from context_provider import ContextProvider
import re

context = ContextProvider()

def strip_markdown_json(raw: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()
    return raw.strip()

# ACTOR_MODEL = "qwen2.5:3b"
ACTOR_MODEL = "gemma4:e4b"

client = ollama.Client(host='http://192.168.68.254:11434/')

def build_prompt(step, ui_tree, taskbar, active_window, task):
    return f"""
You are a Windows 11 UI Execution Actor. Your only job is to output a single JSON action.

OUTPUT CONTRACT:
- Return ONLY a single raw JSON object. No markdown. No explanation. No extra keys.
- You will be called repeatedly. Each call = one action only.

OVERALL TASK: {task}
CURRENT STEP: "{step['instruction']}"
SUCCESS CONDITION: "{step['expected_result']}"

ACTIVE WINDOW: {active_window}

ACCESSIBILITY TREE (format: ControlType | name | center_x | center_y | w | h):
{ui_tree}

DECISION LOGIC — follow in order:
1. ALREADY DONE: If the screenshot shows the SUCCESS CONDITION is met → {{"action": "done"}}
2. ELEMENT FOUND: If the target element is in the tree or visible in the screenshot → return the appropriate action using its exact x/y from the tree.
3. NAVIGATE: If the target is not visible but you know how to reach it (open app, scroll, click menu) → return that navigation action.
4. RETRY: If you attempted an action but the screenshot shows it had no effect or the wrong effect,
   and you know what should be tried differently → {{"action": "retry", "message": "<instructions for next attempt>"}}
5. STUCK: Only if the element is completely unreachable and you have no navigation path → {{"action": "stuck", "message": "<specific reason>"}}

RULES:
- Use x/y values from the ACCESSIBILITY TREE — do not invent coordinates.
- If the ACTIVE WINDOW is unrelated to the step, your first action should reopen or focus the correct app.
- Never return "stuck" when you have found the element or a path to it.
- Never return "done" unless the SUCCESS CONDITION is visibly confirmed in the screenshot.

## Taskbar
TASKBAR (located at the bottom of the screen, y ≈ {context.screen_height - 20}):
{taskbar}

To open any app, click its taskbar icon using the x/y above.

VALID ACTIONS:
{{"action": "click", "x": 123, "y": 456, "button": "left", "element": "<name>"}}
{{"action": "double_click", "x": 123, "y": 456, "element": "<name>"}}
{{"action": "right_click", "x": 123, "y": 456, "element": "<name>"}}
{{"action": "type", "text": "<content>", "x": 123, "y": 456}}
{{"action": "press_key", "key": "<key>"}}
{{"action": "press_hotkey", "keys": ["ctrl", "c"]}}
{{"action": "scroll_v", "x": 960, "y": 540, "amount": -3}}
{{"action": "scroll_h", "x": 960, "y": 540, "amount": -3}}
{{"action": "done"}}
{{"action": "stuck", "message": "<reason>"}}
{{"action": "retry", "message": "<what was attempted, why it failed, and what the next instance should do differently>"}}

TYPE ACTION: The "type" action will automatically click x/y before typing.
Always provide x/y pointing to the input field you want to type into.
"""


def do_step(step, task, additional_context=None, punishment_tally=None):
    active_window = context.get_active_window()
    taskbar = context.get_taskbar_elements()
    ui_tree = context.get_ui_tree(active_window)

    if ui_tree.startswith("Could not read"):
        short_title = active_window.split(" - ")[-1].strip()
        ui_tree = context.get_ui_tree(short_title)

    print(f"Active window: {active_window}")
    print(f"UI elements found: {len(ui_tree.splitlines())}")

    prompt = build_prompt(step, ui_tree, taskbar, active_window, task)

    if additional_context:
        prompt = prompt + f"\n Looks like you already tried to do this task but got stuck, how would you recover from this? Here is the reason you said you were stuck\n{additional_context}"\
        
    if punishment_tally:
        prompt = prompt + f"You, as the agent, are being punished for being stuck and forced to retry, and half punished for requesting a retry, if you are past the threshold, the agents are disposed, and you failed to complete the user's task\nHere is your current standing: {punishment_tally}"

    response = client.chat(
      model=ACTOR_MODEL,
      messages=[
          {"role": "system", "content": prompt},
          {"role": "user", "content": task, "images": [context.get_screenshot()]}
      ],
      options={
          "temperature": 0.1
      },
      keep_alive=0,
      format="json"
    )

    raw = response.message.content.strip()

    action = json.loads(strip_markdown_json(raw).strip())
    print(action)
    
    return action