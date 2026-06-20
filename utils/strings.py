from pathlib import Path
import sys

prompts_folder = Path(__file__).parent / "prompts"


def load_prompt(file: str):
    path = prompts_folder / file

    if not path.exists():
        raise FileNotFoundError(f"Prompt file: {file} not found")

    return path.read_text(encoding="utf-8")


try:
    PLANNER_BASE_SYSTEM_PROMPT = load_prompt("planner.md")
    ACTOR_BASE_SYSTEM_PROMPT = load_prompt("actor.md")
    SKILL_INSTALLATION_PROMPT = load_prompt("skill_selector.md")
    AUTONOMY_MODE_SYSTEM_PROMPT = load_prompt("autonomy.md")
except FileNotFoundError as e:
    print(e, file=sys.__stdout__)
