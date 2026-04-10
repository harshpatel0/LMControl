import ollama
import json
from context_provider import ContextProvider
 
context = ContextProvider()
context.get_installed_apps()

client = ollama.Client(host='http://192.168.68.254:11434/')
 
SYSTEM_PROMPT = f'''
You are the Architect for a Windows 11 Automation System. 
Your goal is to decompose a user's request into a strict sequence of logical steps for a downstream execution agent.

PC ENVIRONMENT:
- OS: {context.WINDOWS_VERSION}
- Screen: {context.screen_width}x{context.screen_height}
- Pinned Apps: {context.get_pinned_apps()}
- Installed Apps: {context.installed_apps}
- Active Window: "{context.get_active_window()}"

PLANNING RULES:
1. ATOMICITY: Each step must contain exactly one action. 
2. SMART START: If the required app is already the "Active Window," skip the "Open App" step.
3. PINNED APPS: If an app is pinned, the instruction should be "Click [App Name] in the taskbar".
4. FALLBACKS: Provide a keyboard shortcut or alternative UI path for every step (e.g., if clicking a URL bar fails, use Ctrl+L).
5. FORMAT: Return ONLY a valid JSON object. No prose, no markdown fences.

OUTPUT SCHEMA:
{{
  "task": "description",
  "steps": [
    {{
      "id": 1,
      "instruction": "Specific action string",
      "expected_result": "Visual state to confirm success",
      "fallback": "Alternative action if element is missing"
    }}
  ]
}}
'''
 
def make_plan(task: str) -> dict:
    response = client.chat(
      model="gemma4:e4b",
      messages=[
          {"role": "system", "content": SYSTEM_PROMPT},
          {"role": "user", "content": task}
      ],
      keep_alive=0
    )
 
    raw = response["message"]["content"].strip()
    # Strip markdown fences if the model wraps output in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
 
    return json.loads(raw)
 
 
if __name__ == "__main__":
    plan = make_plan("Open a Taarak Metha ka Ooltah Chasmah Video on YouTube")
    print(json.dumps(plan, indent=2))