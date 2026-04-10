import ollama
import json
import re
from context_provider import ContextProvider

context = ContextProvider()

def locate_element(screenshot_b64: str, target: str) -> tuple[float, float] | None:
    prompt = f"Where is the {target} on the screen? Reply with only two decimal numbers between 0.0 and 1.0 representing x,y percentage position. Example: 0.45,0.92"

    response = ollama.chat(
        model="moondream:latest",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [screenshot_b64]
            }
        ]
    )

    raw = response["message"]["content"].strip()
    # Parse "0.45,0.92" or "0.45, 0.92" or "(0.45, 0.92)"
    numbers = re.findall(r"0\.\d+|\b1\.0\b|\b0\b|\b1\b", raw)
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    return None


def check_result(screenshot_b64: str, expected_result: str) -> bool:
    prompt = f"Is this visible on the screen: {expected_result}? Reply with only yes or no."

    response = ollama.chat(
        model="moondream:latest",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [screenshot_b64]
            }
        ]
    )

    return "yes" in response["message"]["content"].strip().lower()


def do_step(step: dict) -> dict:
    instruction: str = step["instruction"].lower()
    expected: str = step["expected_result"]
    active_window = context.get_active_window()

    screenshot = context.get_screenshot()
    print(f"Screenshot taken | Active window: {active_window}")

    # Check if expected result is already on screen before doing anything
    if check_result(screenshot, expected):
        return {"action": "done"}

    # --- TYPE step ---
    if instruction.startswith("type "):
        text = step["instruction"][5:]  # everything after "type "
        return {"action": "type", "text": text}

    # --- PRESS KEY step ---
    if instruction.startswith("press ") and "hotkey" not in instruction:
        key = instruction.replace("press ", "").strip()
        return {"action": "press_key", "key": key}

    # --- HOTKEY step ---
    if "hotkey" in instruction or "ctrl+" in instruction or "alt+" in instruction:
        # Extract keys from instruction e.g. "press hotkey ctrl+t"
        combo = re.findall(r"ctrl|alt|shift|win|[a-z0-9]", instruction)
        if combo:
            return {"action": "press_hotkey", "keys": combo}

    # --- SCROLL step ---
    if "scroll" in instruction:
        direction = "down" if "down" in instruction else "up"
        amount = -3 if direction == "down" else 3
        return {"action": "scroll_v", "x": 0.5, "y": 0.5, "amount": amount}

    # --- CLICK step — ask moondream to locate the target ---
    # Extract what to click from the instruction
    # e.g. "Click Microsoft Edge in the taskbar" -> "Microsoft Edge in the taskbar"
    target = re.sub(r"^click (on )?", "", instruction).strip()
    # Clean up the target before sending to moondream
    target = re.sub(r"^click (on )?", "", instruction).strip()
    # Remove location hints like "in the taskbar", "on the desktop", "at the top"
    target = re.sub(r"\s*(in|on|at|from|inside)\s+the\s+\w+", "", target).strip()

    coords = locate_element(screenshot, target)

    if coords is None:
        return {
            "action": "stuck",
            "message": f"Could not locate '{target}' on screen. Active window: {active_window}"
        }

    x, y = coords
    return {"action": "click", "x": x, "y": y, "button": "left"}


if __name__ == "__main__":
    step = {
        "id": 1,
        "instruction": "Click Microsoft Edge in the taskbar",
        "expected_result": "Edge browser opens",
        "fallback": "Search for Microsoft Edge in the Start menu and open it"
    }

    print(do_step(step=step))