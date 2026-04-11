import json
from model_definitions import ActorModel
from context_provider import ContextProvider
import utils
from hijack import print

ACTOR_MODEL_NAME = "gemma4:e4b"
OLLAMA_SERVER = "http://192.168.68.254:11434"

context = ContextProvider()
actor_model = ActorModel(ACTOR_MODEL_NAME, OLLAMA_SERVER)

def do_step(step, task, additional_context=None, punishment_tally=None):
    active_window = context.get_active_window()
    taskbar = context.get_taskbar_elements()
    ui_tree = context.get_ui_tree(active_window)

    if ui_tree.startswith("Could not read"):
        short_title = active_window.split(" - ")[-1].strip()
        ui_tree = context.get_ui_tree(short_title)

    print(f"Active window: {active_window}")
    print(f"UI elements found: {len(ui_tree.splitlines())}")

    instruction = step['instruction']
    expected_result = step['expected_result']

    # prompt = build_prompt(step, ui_tree, taskbar, active_window, task)
    user_prompt = actor_model.construct_user_prompt(task=task, instruction=instruction, expected_result=expected_result, active_window=active_window, ui_tree=ui_tree, taskbar=taskbar)

    if additional_context:
        actor_model.inject_additonal_context(user_prompt, additional_context)
        
    if punishment_tally:
        actor_model.inject_additonal_context(user_prompt, punishment_tally, "Here are the number of iterations you have made on this task")
    
    response = actor_model.run(user_prompt, attach_screenshot=True)

    action = json.loads(utils.strip_markdown_json(response).strip())

    if not action:
        action = {
            "action": "retry",
            "message": "Model returned an empty response, likely due to context overload. Retry with the same step."}
        print("[INTERNAL ACTOR MODEL GUARD] The model returned an empty response, instructing the Step Orchestrator to retry")
    
    print(action)
    return action