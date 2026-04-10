import ollama
import json
from context_provider import ContextProvider

context = ContextProvider()

SYSTEM_PROMPT = f'''
You are an actor for a Windows PC Automation Agent.
You will receive a screenshot of the current PC screen and a single instruction to carry out.
Your only job is to look at the screenshot and return the correct JSON action to perform that instruction.

PC CONTEXT
- Windows Version: {context.WINDOWS_VERSION}
- Screen Size: {context.screen_width} x {context.screen_height}
- Current Window: {context.get_active_window()}

IMPORTANT COORDINATE RULES
- x and y are percentages of the screen (0.0 = left/top, 1.0 = right/bottom)
- Example: the Windows taskbar is near y=0.97, bottom-centre of the screen
- Always return coordinates as decimals between 0.0 and 1.0

AVAILABLE ACTION TYPES
Return exactly one of these JSON objects:

Click:
{{"action": "click", "x": 0.5, "y": 0.97, "button": "left"}}

Type text (only use after a click has focused the input):
{{"action": "type", "text": "your text here"}}

Vertical scroll:
{{"action": "scroll_v", "x": 0.5, "y": 0.5, "amount": -3}}
(negative = scroll down, positive = scroll up)

Horizontal scroll:
{{"action": "scroll_h", "x": 0.5, "y": 0.5, "amount": 3}}

Press a single key:
{{"action": "press_key", "key": "enter"}}

Press a hotkey combination:
{{"action": "press_hotkey", "keys": ["ctrl", "t"]}}

Step complete, move to next:
{{"action": "done"}}

Cannot find target element, need replanning:
{{"action": "stuck", "message": "describe what you see and why you are stuck"}}

OPERATIONAL RULES
- Output ONLY valid JSON. No explanation. No markdown fences.
- If the expected result is already visible on screen, return {{"action": "done"}}.
- If you cannot find the target element after carefully examining the screenshot, return "stuck".
- Never guess coordinates — only return a click if you can clearly see the target.
- Do not chain multiple actions in one response — return exactly one action per response.
'''

def do_step(step: dict):
    instruction = (
        f"Instruction: {step['instruction']}\n"
        f"Expected result after this action: {step['expected_result']}"
    )

    screenshot = context.get_screenshot()
    print("Taken Screenshot, initialising model")

    response = ollama.chat(
        model="qwen3-vl:2b",
        messages=[
            {
                "role": "user",
                "content": f"{SYSTEM_PROMPT}\n\n{instruction}",
                "images": [context.get_screenshot()]
            }
        ],
        think=False
    )

    raw = response["message"]["content"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)

if __name__ == "__main__":
    step = {
      "id": 1,
      "instruction": "Click Microsoft Edge in the taskbar",
      "expected_result": "Edge browser opens",
      "fallback": "Search for Microsoft Edge in the Start menu and open it"
    }

    print(do_step(step=step))