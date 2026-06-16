import json
import subprocess
import sys
import venv
from pathlib import Path

from settings.default import default_settings


class KodoSetup:
    def __init__(self) -> None:
        self.default_settings = default_settings

    def check_system_compatibility(self):
        if sys.platform != "win32":
            print("Kodo can only run under a Windows Environment")
            sys.exit(1)

    def run_setup_sequence(self):
        self.introduction()

        self.set_model_provider()
        self.setup_model_provider(self.user_using_provider)

        self.set_model_names()
        self.set_thinking()

        if self.user_using_provider == "anthropic":
            self.set_anthropic_effort()

        self.setup_orchestrator()
        if self.user_has_chosen_autonomy_mode:
            self.setup_autonomy_mode_orchestrator()

        self.introduce_skills()
        self.save_settings()
        self.create_venv_and_install_deps()

    def introduction(self):
        print("Welcome to the Kodo Setup Environment")
        input("Press ENTER to continue")

    def set_model_provider(self):
        print("Model Providers")
        print("""
Kodo relies on an LLM to perform a particular task, you can choose from three different providers, Ollama, Google, and Anthropic.
Google and Anthropic will require an API key to run, and will be saved in the .env folder in the app.

Google Gemini AI Disclaimer: Google provides free access to their Gemini AI, however your data will be used to train the model and for manual human review.
    This project may expose sensitive details about you through Accessibility Trees and Screenshots of your PC. If privacy is a concern, please stick with a paid plan or use a local Ollama Instance.

The project is also very input token heavy, remember to check how you will be charged through your provider's API usage billing

You can always change the provider in the settings.json file by changing
    active_model_provider (This is the Model Provider that will be used when none is specified)
    models > skill_installation
    models > planner
    models > actor
    models > autonomy_actor

Some parameters may not have any effect based on the provider's API usage,
keep_alive only affects Ollama
temperatures will be bumped to 1.0 regardless of the set value when Thinking is enabled according to Anthropic's usage.
""")
        print("""
What provider would you like to use?
    [O]llama (Recommended)
    [A]nthropic
    [G]oogle Gemini
""")
        while True:
            user_provider = input("Provider: ").lower()

            if user_provider == "o":
                default_settings["active_model_provider"] = "ollama"

                for key in ("skill_installation", "planner", "actor", "autonomy_actor"):
                    default_settings["models"][key]["provider"] = "ollama"

                self.user_using_provider = "ollama"
                break

            if user_provider == "a":
                default_settings["active_model_provider"] = "anthropic"

                for key in ("skill_installation", "planner", "actor", "autonomy_actor"):
                    default_settings["models"][key]["provider"] = "anthropic"

                self.user_using_provider = "anthropic"
                break

            if user_provider == "g":
                default_settings["active_model_provider"] = "google"

                for key in ("skill_installation", "planner", "actor", "autonomy_actor"):
                    default_settings["models"][key]["provider"] = "google"

                self.user_using_provider = "google"
                break

            print(f"{user_provider} does not exist")

    def setup_model_provider(self, provider: str):
        if provider == "ollama":
            print(
                "Type the Ollama IP Addresses and Port, this is the server that is currently serving an Ollama Instance\nIf it is your current PC, leave the field blank"
            )
            ollama_url = input("Ollama IP Address and Port: ")

            if ollama_url == "":
                ollama_url = "localhost:11434"

            default_settings["model_providers"]["ollama"]["server_url"] = ollama_url

        if provider == "anthropic":
            anthropic_api_key = input("Type your Anthropic API key: ")

            with open(".env", "w") as env_file:
                env_file.write("ANTHROPIC_API_KEY = " + anthropic_api_key)

        if provider == "google":
            google_api_key = input("Type your Google AI API key: ")

            with open(".env", "w") as env_file:
                env_file.write("GOOGLE_API_KEY = " + google_api_key)

    def set_model_names(self):
        provider = self.user_using_provider

        print(f"\nModel Selection (using {provider})")
        print("-" * 40)

        suggestions = {
            "ollama": (
                "Enter the Ollama model name you want to use.\n"
                "Recommended: qwen2.5-coder:14b (good all-rounder) or qwen2.5:7b (lightweight)\n"
                "You can also use: llama3.2:3b, deepseek-coder-v2, gemma4:e4b"
            ),
            "anthropic": (
                "Enter the Anthropic model name.\n"
                "Recommended: [C]laude Sonnet 4-6 (claude-sonnet-4-20250514)\n"
                "             [H]aiku 4-5 (claude-haiku-4-20250507)"
            ),
            "google": (
                "Enter the Google model name.\n" "Recommended: gemini-3.1-flash-lite"
            ),
        }

        print(suggestions[provider])

        if provider == "anthropic":
            while True:
                anthro_choice = (
                    input("\nModel ([C]laude Sonnet / [H]aiku / custom): ")
                    .lower()
                    .strip()
                )
                if anthro_choice == "c":
                    model_name = "claude-sonnet-4-20250514"
                    break
                if anthro_choice == "h":
                    model_name = "claude-haiku-4-20250507"
                    break
                if anthro_choice:
                    model_name = anthro_choice
                    break
                print("Please make a selection")
        else:
            model_input = input("Model name: ").strip()
            if model_input:
                model_name = model_input
            elif provider == "google":
                model_name = "gemini-3.1-flash-lite"
            else:
                model_name = "qwen2.5-coder:14b"

        for key in ("skill_installation", "planner", "actor", "autonomy_actor"):
            default_settings["models"][key]["model_name"] = model_name

        print(f"  Using model: {model_name}\n")

    def set_thinking(self):
        print("Thinking / Reasoning")
        print("-" * 40)
        print("""
Some providers support 'thinking' (also called extended reasoning), where the
model spends extra computation to work through complex problems step-by-step
before responding. Thinking does make models more capable at performing tasks
and call skills.

DISCLAIMER: If you are using Anthropic or Google, enabling thinking will incur
additional API charges beyond normal token costs. With Ollama (local) there is
no monetary cost, but responses will take longer.

You can always change this per-model in settings.json under models > [role] > thinking.
""")

        while True:
            choice = (
                input("Enable thinking for all models? ([Y]es / [N]o): ")
                .lower()
                .strip()
            )
            if choice == "y":
                thinking = True
                break
            if choice == "n":
                thinking = False
                break
            print("Please enter 'y' or 'n'")

        for key in ("skill_installation", "planner", "actor", "autonomy_actor"):
            default_settings["models"][key]["thinking"] = thinking

        print(f"  Thinking set to: {'enabled' if thinking else 'disabled'}\n")

    def set_anthropic_effort(self):
        print("Anthropic Effort Level")
        print("-" * 40)
        print("""
Anthropic supports different effort levels for thinking / extended thinking:
    [L]ow (Recommended) — fast and cost-effective
    [M]edium — balanced
    [H]igh — best for complex reasoning, most expensive

This is stored in model_providers > anthropic > effort.
""")

        while True:
            choice = input("Effort level ([L]ow / [M]edium / [H]igh): ").lower().strip()
            if choice == "l":
                default_settings["model_providers"]["anthropic"]["effort"] = "low"
                break
            if choice == "m":
                default_settings["model_providers"]["anthropic"]["effort"] = "medium"
                break
            if choice == "h":
                default_settings["model_providers"]["anthropic"]["effort"] = "high"
                break
            print("Please enter 'l', 'm', or 'h'")

        print(
            f"  Effort set to: {default_settings['model_providers']['anthropic']['effort']}\n"
        )

    def setup_orchestrator(self):
        print(
            "Would you like to use the Autonomy Mode Orchestrator or the Planner-Actor Orchestrator"
        )
        print("""
Orchestrators are the harnesses that are used to control your model of choice.

Planner-Actor Model
    The Planner-Actor Mode will first create a plan for the task and then use another instance of the model to follow the plan.
    The Actor is allowed to deviate from the plan for a few steps incase something goes wrong.

Autonomy Mode Orchestrator
    This is the new type of orchestrator, skipping the Planner Entirely, the Autonomy Mode Orchestrator would make decisions on it's own.
""")
        print("""

Choose your orchestrator, you can always change this in the settings.json file under orchestrator > use_autonomy_mode

    [P]lanner-Actor Model
    [A]utonomy Mode (Recommended)
""")
        while True:
            user_choice = input("").lower()

            if user_choice == "p":
                self.default_settings["orchestrator"]["use_autonomy_mode"] = False
                self.user_has_chosen_autonomy_mode = False
                break
            if user_choice == "a":
                self.default_settings["orchestrator"]["use_autonomy_mode"] = True
                self.user_has_chosen_autonomy_mode = True
                break

            print(
                "The input is incorrect, it can only be 'p' or 'a' for the corresponding mode."
            )

    def setup_autonomy_mode_orchestrator(self):
        print("Iteration Limits")
        print("-" * 40)
        print("""
Since the Autonomy Mode Orchestrator can run until it deems that the task is complete,
you can enforce a total number of iterations. The model will be provided with the
enforced limits.

Enter 0 for unlimited iterations (the loop runs until the model decides the task is done).
Enter any positive number to cap the total iterations.
""")
        while True:
            user_limits = input("Iteration Limit (0 = unlimited): ")
            try:
                user_limits = int(user_limits)
                break
            except Exception:
                print("Iteration Limits can only be a number")

        default_settings["orchestrator"]["autonomy_orchestrator"][
            "max_total_iterations"
        ] = user_limits
        print(f"  Max total iterations set to: {user_limits}\n")

    def introduce_skills(self):
        print("\nSkills — Extending Kodo's Capabilities")
        print("=" * 50)
        print("""
Skills are plug-and-play modules that teach Kodo how to do specific things.
Each skill lives in its own folder under skills/ and is auto-discovered at startup.

Installing a Skill:
    Simply add a new folder under skills/ with a skill.json manifest.
    The Skill Orchestrator will discover it automatically on next start.
    See: skills/AGENTS.md for the full guide.

Uninstalling a Skill:
    Option A — Set "enabled": false in the skill's skill.json to disable it.
    Option B — Delete the skill's folder entirely.

Creating a Skill:
    Read skills/AGENTS.md — it covers all the details to create a skill:
    - skill.json manifest fields
    - Communication between skills and the orchestrator
    - Action parameter handling
    - Dynamic context generation
    - Planner/Actor guidance documents

Refer to existing skills as examples — they all follow the same pattern.
        """)

    def save_settings(self):
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=2)
        print("\nSettings saved to settings.json")

    def create_venv_and_install_deps(self):
        venv_path = Path("venv")
        venv_python = venv_path / "Scripts" / "python.exe"

        print(f"\nCreating virtual environment: {"venv"}")
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created.\n")

        print("Installing dependencies from requirements.txt...")
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"pip install failed:\n{result.stderr}")
            sys.exit(1)

        print("Dependencies installed successfully.\n")

        file_path = Path("initialised.txt")
        file_path.touch()


if __name__ == "__main__":
    qs = KodoSetup()
    qs.run_setup_sequence()
