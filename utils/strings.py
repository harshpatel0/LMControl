from pathlib import Path
import sys

prompts_folder = Path(__file__).parent.parent / "prompts"


def load_prompt(file: str):
    path = prompts_folder / file

    if not path.exists():
        raise FileNotFoundError(f"Prompt file: {file} not found")

    return path.read_text(encoding="utf-8")


try:
    PLANNER_BASE_SYSTEM_PROMPT = load_prompt("planner.md")
    ACTOR_BASE_SYSTEM_PROMPT = load_prompt("actor.md")
    SKILL_INSTALLATION_PROMPT = load_prompt("skill_installation.md")
    AUTONOMY_MODE_SYSTEM_PROMPT = load_prompt("autonomy.md")

    custom_instructions_path = prompts_folder / "custom_instructions.md"

    if custom_instructions_path.exists():
        custom_instructions = (
            "\n#These are the user's instructions on how you (Kodo) should operate\n"
        )
        custom_instructions += custom_instructions_path.read_text()

        PLANNER_BASE_SYSTEM_PROMPT += custom_instructions
        ACTOR_BASE_SYSTEM_PROMPT += custom_instructions
        SKILL_INSTALLATION_PROMPT += custom_instructions
        AUTONOMY_MODE_SYSTEM_PROMPT += custom_instructions

except FileNotFoundError as e:
    print(e, file=sys.__stdout__)
    exit(1)
