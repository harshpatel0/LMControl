# LMControl

LMControl lets a local LLM take control of your Windows PC. It reads the live accessibility tree, reasons about what's on screen, and emits actions until the task is done. Clicks, keystrokes, file writes, code execution, whatever it takes. It runs entirely on your machine through [Ollama](https://ollama.com), so nothing leaves your computer.

It's not a polished product. It's a project that works well enough to be genuinely useful, built to see how far local models can go on real desktop tasks. Models get confused, occasionally do something baffling, and need hand-holding on complex apps. The architecture is designed to recover when that happens rather than just die.

**Windows only.** The UI layer is built on pywinauto and the Windows UIA accessibility tree. macOS and Linux are not supported.

**A note on the code.** The core logic and architecture are handwritten, with system prompts and user prompts being fully AI geneated. AI was also useful as a sounding board during design, helped write some of the smaller utility functions, and was involved in refactors and documentation (this README file). It's not vibe-coded, but it's not purely solo either.

## Security Disclaimer (very important!)

This is a project I started making on my own with no scope planning or safety design, and I'm not taking responsibility for what happens when you run it. Skills and the `python` action can execute arbitrary code on your machine. The venv isn't a sandbox, it's just there to keep packages off your native Python installation. 
**Prompt injection is a real risk** if the model ends up reading adversarial content mid-task. Be deliberate about what you feed it.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Setup](#setup)
- [Running LMControl](#running-lmcontrol)
- [Modes](#modes)
- [Settings](#settings)
- [Model Recommendations](#model-recommendations)
- [Skills](#skills)
  - [Skill Types](#skill-types)
  - [Installing a Skill](#installing-a-skill)
  - [Creating a Skill](#creating-a-skill)
  - [skill.json Schema](#skilljson-schema)
- [Architecture](#architecture)

---

## Project Structure

```
lmcontrol/
├── orchestrator.py              # Entry point, StepOrchestrator, AutonomyOrchestrator
├── parse_action.py              # Routes actor JSON output to PC actions or skills
├── context_provider.py          # UI tree, screenshots, window info, UITreeHandler
├── models/
│   ├── actor_model.py           # Actor call wrappers (do_step, do_autonomy_step)
│   ├── planner_model.py         # Planner call wrapper (make_plan)
│   └── ollama/
│       └── model_definitions.py # PlannerModel, ActorModel, SkillInstallationMode
├── pc_actions/
│   └── perform_pc_actions.py    # pyautogui wrappers (click, type, drag, scroll, etc.)
├── python/
│   └── run_python_code.py       # Isolated venv Python runner
├── settings/
│   ├── default.py               # Default settings
│   └── settings.py              # Settings loader (creates settings.json on first run)
├── skills/
│   ├── skill_orchestrator.py    # Skill discovery, loading, and dispatch
│   ├── browser-navigation/      # Static skill -- open_url action + actor/planner docs
│   ├── launch-windows-app/      # Dynamic skill -- generates app list at runtime
│   ├── python/                  # Documentation skill -- documents the python action
│   ├── toast-notifications/     # Static skill -- send_toast action
│   └── word-navigation/         # Documentation skill -- Microsoft Word UIA guide
└── utils/
    ├── logger.py                # Shared logger (console INFO, file DEBUG)
    ├── strings.py               # System prompts for planner, actor, autonomy, skill install
    └── utils.py                 # strip_markdown_json helper
```

---

## Installation

```bash
git clone https://github.com/harshpatel0/lmcontrol.git
cd lmcontrol
pip install -r requirements.txt
```

You'll also need [Ollama](https://ollama.com) installed and at least one model pulled. More on that in [Model Recommendations](#model-recommendations).

---

## Setup

1. **Install Ollama** and pull a model. `gemma4:e4b` is what this was built and tested on:

   ```bash
   ollama pull gemma4:e4b
   ```

2. **Start the Ollama server:**

   ```bash
   ollama serve
   ```

   By default it runs on `localhost:11434`. If you're hosting Ollama elsewhere, update `ollama_server` in `settings.json` after the first run.

3. Run `orchestrator.py` with a task and you're off.

---

## Running LMControl

Open `orchestrator.py` and set your task at the bottom of the file. There are two modes, covered in the next section.

```python
task = "Open Word and write a full report on dinosaurs"

# Planner-Actor mode
plan = models.planner_model.make_plan(task)

# Autonomy mode
autonomy_orchestrator = AutonomyOrchestrator(task)
autonomy_orchestrator.run_skill_installation_mode()
autonomy_orchestrator.run()
```

Define the settings in `settings.json` on the mode you would like to use under `settings > orchestrator > use_experimental_autonomy_mode`

Then:

```bash
python orchestrator.py
```

Keep your mouse away from the top-left corner of the screen. That's the pyautogui failsafe and straying into that corner will immediately abort the run.
You now also know what to do incase you want to stop it.

---

## Modes

### Planner-Actor Mode

A **Planner** model reads your task and produces a structured JSON plan, a list of ordered atomic steps with instructions and expected results. A separate **Actor** model then executes each step one at a time, reading the live accessibility tree on every call to figure out where to click or what to type.

This mode is more predictable. If something breaks on step 4, you know exactly where it broke. When the planned steps run out but the task is not finished, it automatically spills into a short autonomy phase to wrap up.

### Autonomy Mode

Skip the plan entirely. The actor runs in a free loop, observing the UI state each turn, deciding what to do, and acting. It keeps a running `history` string across turns as its working memory.

This mode handles open-ended tasks better. Run `run_skill_installation_mode()` before `run()` so it has the relevant skills loaded going in.

---

## In Practice

The models are inconsistent. That's just the reality of running small local models on tasks this complex. Sometimes a run goes flawlessly and you watch it open an app, navigate to the right page, and complete a multi-step task, and navigate around failures and unexpected behaviour. Other times it will do something so confidently wrong that you have to just sit back and appreciate it.

Some real examples from development:

**The Gemini incident.** The task was to open Gemini, write a comprehensive report on dinosaurs, and have Gemini proofread. The actor opened the browser, navigated to gemini.google.com, typed the task into the prompt box, and submitted it. Gemini responded with a report on dinosaurs. The actor looked at the screen, saw a report on dinosaurs, and emitted `done`. Its reasoning: *"looks like Gemini already generated a report on dinosaurs so I wouldn't need to."* It was technically correct. It was also completely wrong. Best and worst outcome simultaneously.

**Word, planner mode.** Same report task, but in Microsoft Word with the planner architecture. The actor successfully opened Word, typed out a full report, and called done. No heading styles applied. No save. Just raw text in an unsaved document and a very satisfied `done` signal. The word-navigation skill exists largely because of sessions like this.

The inconsistency is the main thing to be aware of going in. `action_settle_time`, iteration budgets, and the skill system all exist to give the model more chances to recover when it goes sideways. They help a lot, but they don't make the model reliable, they make unreliability survivable.
While on this topic, it is likely that Exceptions from invalid inputs are triggered, they sometimes happen and sometimes don't, so I am sure I haven't caught 99.9% of them.

---
### Settings

On first run, LMControl writes a `settings.json` to the project root using the defaults below. Edit it directly and restart.

```json
{
  "models": {
    "ollama_server": "localhost:11434",

    "skill_installation": {
      "model_name": "gemma4:e4b",
      "temperature": 0.1,
      "keep_alive": 0
    },

    "planner": {
      "model_name": "gemma4:e4b",
      "thinking": true,
      "temperature": 0.7,
      "keep_alive": 0
    },

    "actor": {
      "model_name": "gemma4:e4b",
      "thinking": true,
      "temperature": 0.3,
      "keep_alive": 30,
      "attach_screenshot_of_active_window": false
    },

    "autonomy_actor": {
      "model_name": "gemma4:e4b",
      "thinking": true,
      "temperature": 0.5,
      "keep_alive": 150,
      "attach_screenshot_of_active_window": false
    }
  },
  "orchestrator": {
    "action_settle_time": 4,
    "use_experimental_autonomy_mode": false,

    "planner_architecture": {
      "max_iterations_per_step": 10,
      "max_autonomy_steps": 10,
      "max_replan_loop": 7
    },

    "autonomy_orchestrator": {
      "enforce_max_total_iterations": true,
      "max_total_iterations": 50
    }
  },
  "context_provider": {
    "waiting_period": 4,
    "skip_after_ticks": 10
  }
}
```

### Setting Reference

| Setting | Default | What it does |
|---|---|---|
| `models.ollama_server` | `localhost:11434` | Where to find the Ollama API. Change this if Ollama is running on a different machine or port. |
| `models.skill_installation.model_name` | `gemma4:e4b` | Model used for the pre-planning skill selection call. Can be a smaller/faster model since the task is just picking from a list. |
| `models.skill_installation.temperature` | `0.1` | Keep this low. Skill selection should be precise. |
| `models.skill_installation.keep_alive` | `0` | Skill installation runs once per task. No reason to keep it warm. |
| `models.planner.model_name` | `gemma4:e4b` | Model used to generate the step-by-step plan in Planner-Actor mode. |
| `models.planner.thinking` | `true` | Prepends `<\|think\|>` to the system prompt. **Gemma 4 models only.** See the warning in Model Recommendations. |
| `models.planner.temperature` | `0.7` | How varied the planner's output is. 0.7 is the recommended value. |
| `models.planner.keep_alive` | `0` | The planner runs once per task so there's no reason to keep it warm. |
| `models.actor.model_name` | `gemma4:e4b` | Model used in Planner-Actor mode. Reads the live UI tree and emits a single JSON action per call. |
| `models.actor.thinking` | `true` | Same as planner thinking. **Gemma 4 only.** |
| `models.actor.temperature` | `0.3` | Keep the actor cooler than the planner. Consistent action selection matters more than variety. |
| `models.actor.keep_alive` | `30` | The actor runs many times per task. Keeping it loaded saves reload overhead between steps. |
| `models.actor.attach_screenshot_of_active_window` | `false` | Attaches a JPEG screenshot of the active window to each actor call. Only useful if your model has vision. |
| `models.autonomy_actor.model_name` | `gemma4:e4b` | Model used in Autonomy mode. Same role as the actor but handles planning and execution in one. |
| `models.autonomy_actor.thinking` | `true` | **Gemma 4 only.** More important here than in planner-actor mode since the model is doing both jobs. |
| `models.autonomy_actor.temperature` | `0.5` | Middle ground between the planner and actor temperatures since the autonomy actor does both jobs. |
| `models.autonomy_actor.keep_alive` | `150` | Autonomy mode runs many more iterations than planner-actor mode, so keeping the model loaded longer is worth it. |
| `models.autonomy_actor.attach_screenshot_of_active_window` | `false` | Same as the actor screenshot setting, independently configurable for autonomy mode. |
| `orchestrator.action_settle_time` | `4` | Seconds to wait after each action before reading the UI tree again. Reduce this if your apps respond fast. Increase it if the actor keeps acting before the UI has caught up. Applies to both orchestrators. |
| `orchestrator.use_experimental_autonomy_mode` | `false` | Switches the entire system to Autonomy mode. Changes which model configs, system prompts, and orchestrator are used. |
| `orchestrator.planner_architecture.max_iterations_per_step` | `10` | How many times the actor can retry a single step before the run aborts. Each retry feeds the previous failure message back as context. |
| `orchestrator.planner_architecture.max_autonomy_steps` | `10` | Extra steps the `StepOrchestrator` can take after the plan runs out, in its built-in fallback autonomy phase. |
| `orchestrator.planner_architecture.max_replan_loop` | `7` | If the actor replans to the same instruction this many times in a row, it's flagged as a loop and the run is killed. |
| `orchestrator.autonomy_orchestrator.enforce_max_total_iterations` | `true` | Set to `false` to let Autonomy mode run without a turn limit. Only do this if you're watching it. |
| `orchestrator.autonomy_orchestrator.max_total_iterations` | `50` | Hard cap on how many turns `AutonomyOrchestrator` can run. Ignored if `enforce_max_total_iterations` is `false`. |
| `context_provider.waiting_period` | `4` | Consecutive stable ticks required before the UI tree is considered settled and ready to read. |
| `context_provider.skip_after_ticks` | `10` | Maximum ticks to wait before reading the tree anyway. Prevents the context provider from hanging on apps that never fully settle. |

### Recommended Temperature Settings

| Mode | Skill Installation | Planner | Actor |
|---|---|---|---|
| Planner-Actor | 0.1 | 0.7 | 0.3 |
| Autonomy | 0.1 | -- | 0.5 |

---

## Model Recommendations

LMControl was built on `gemma4:e4b` and that's still the recommendation. It handles structured JSON output well, follows long system prompts reliably, and the thinking mode gives it meaningfully better reasoning on UI tasks.

| Model | Verdict |
|---|---|
| `gemma4:e4b` | The primary dev target. Everything is tuned around this. |
| `qwen3:8b` | A solid alternative. Performs well in practice. Set `thinking: false`. |
| Larger models | Likely better. Largely untested. |
| Tiny models (1-3B) | Haven't tested these seriously. The concern is that the actor receives a large, dense context on every single call -- the full UI tree, task state, accumulated history, loaded skill docs, and system prompt all at once. Small models tend to get overwhelmed by that and lose track of what they're supposed to be doing. Worth experimenting with, but don't expect reliable results. |

**Thinking mode warning.** The `thinking` flag prepends `<|think|>` to the system prompt. This is a Gemma 4 feature. Enabling it on other models will not produce the intended effect and will likely corrupt JSON output formatting.

---

## Skills

Skills are how you extend LMControl beyond basic mouse and keyboard actions. A skill can teach the planner how to approach a task, give the actor step-by-step procedural guidance for a specific application, expose new callable actions the actor can emit, or all of the above.

### Skill Types

#### Documentation Skills

Documentation skills teach a model how to operate specific UI elements or complete specific tasks. They do not have any actions or functions assigned to them, just markdown files that get loaded into the planner and/or actor system prompts when the skill is selected.

`word-navigation` is the main example. It gives the actor a full procedural guide for Microsoft Word's UIA tree, covering the Apply Styles dialog, cursor anchoring, heading application order, save flows, and every gotcha that would otherwise cause a stuck loop. Without it the actor is guessing.

`python` documents the built-in `python` action, covering when to use code over UI interaction, the expected format, constraints, and how output comes back to the orchestrator.

#### Static Skills

Have a Python entry point and register named actions the actor can emit directly. Documentation lives in static `actor_skill.md` and `planner_skill.md` files that are loaded once and injected as-is.

`browser-navigation` and `toast-notifications` are both static skills.

```json
{"action": "open_url", "url": "https://youtube.com"}
{"action": "send_toast", "title": "Done", "body": "Task complete"}
```

When the actor emits a registered action name, the skill orchestrator intercepts it and runs the entry point with the action's arguments passed as JSON.

#### Dynamic Skills

The entry point runs with a `--generate` flag at load time and produces documentation as a JSON string rather than reading from static files. The skill generates its own context based on the current system state.

`launch-windows-app` is the example here. It scans the Start Menu at runtime to find every installed `.lnk` shortcut, then injects the real list of launchable apps into both the planner and actor prompts. The model always sees your actual installed apps rather than a hardcoded list.

```json
{"action": "open_app", "app": "Microsoft Word"}
```

The `--generate` output must look like this:

```json
{
  "planner": "## My Skill\nPlanner documentation here...",
  "actor": "## My Skill\nActor documentation here..."
}
```

### Installing a Skill

Drop the skill folder into `/skills`. The orchestrator scans the directory on startup and picks it up automatically.

```
skills/
  my-skill/
    skill.json
    actor_skill.md
    planner_skill.md
    skill.py
```

### Creating a Skill

Skills live in `/skills/<skill-name>/`. The minimum requirement is a `skill.json`. Everything else depends on what type of skill you're building.

Documentation-only:
```
skills/my-app-guide/
  skill.json
  actor_skill.md
  planner_skill.md
```

Static skill with actions:
```
skills/my-tool/
  skill.json
  actor_skill.md
  planner_skill.md
  skill.py
```

Dynamic skill:
```
skills/my-dynamic-tool/
  skill.json
  skill.py      <- must handle --generate
```

When an action is invoked, the orchestrator calls the entry point as a subprocess with all action arguments (minus the `"action"` key itself) passed as a JSON string in `sys.argv[1]`:

```python
import sys, json

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    do_something(args.get("my_param"))
```

### skill.json Schema

```json
{
  "name": "my-skill",
  "description": "Short description shown to the skill installation model when deciding what to load",
  "actions": ["action_name"],
  "entry": "skill.py",
  "enabled": true,
  "dynamic_context": false,
  "generated_for_actor": true,
  "generated_for_planner": true
}
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Identifier. Should match the folder name. |
| `description` | Yes | Shown to the skill installation model. Write this clearly, because it's how the model decides whether to load this skill for a given task. Vague descriptions get missed. |
| `actions` | Yes | List of action names this skill registers. Use `[""]` for documentation-only skills. |
| `entry` | No | Entry point filename. Omit for documentation-only skills. |
| `enabled` | No | Set to `false` to disable without deleting. Defaults to `true`. |
| `dynamic_context` | No | Set to `true` to enable runtime context generation. Entry point must handle `--generate` argument. |
| `generated_for_actor` | No | Used with `dynamic_context: true`. Tells the orchestrator this skill produces actor documentation. |
| `generated_for_planner` | No | Used with `dynamic_context: true`. Tells the orchestrator this skill produces planner documentation. |

---

## Architecture

Here's what happens when you give LMControl a task.

### Skill Installation Phase

Before planning or execution starts, `SkillInstallationMode` makes a call to a model with the task description and a compact summary of all available skills. The model returns a list of skill names it thinks are relevant. Those skills get loaded and their documentation is read or generated, held ready to inject into the planner and actor prompts.

The model first sees the name and the description from `skills.json` and picks what it needs, and the full documentation is only loaded if the skill is selected. This keeps the main system prompts from bloating with content that has nothing to do with the current task.

### Planner-Actor Mode

```
Task
  -> SkillInstallationMode
  -> PlannerModel          (produces JSON plan)
  -> StepOrchestrator
  -> ActorModel (per step) (reads UI tree, emits one action)
  -> PCActions / Skills
```

The Planner gets the task alongside a snapshot of the PC environment: OS version, screen size, installed apps, pinned taskbar apps, and the current taskbar accessibility tree. It produces a JSON plan with ordered, atomic steps.

The StepOrchestrator walks the steps. For each one it calls the Actor with the current instruction, the live UI tree, taskbar elements, and any context accumulated from previous iterations on that step.

The Actor returns a single JSON action. That action gets dispatched to a `PCAction` (click, type, hotkey, scroll, drag) or to the Skill Orchestrator if it matches a registered skill action name.

The Actor also signals state. `PROCEED` moves to the next step. `DONE` ends the run. `STUCK` and `RETRY` add the failure message as context and loop again on the same step. `REPLAN` allows the actor to override its current instruction entirely, substituting a new one of its own choosing mid-execution.

`DONE` is not taken at face value. Before accepting it, the orchestrator checks whether the element the actor claimed to have acted on is actually present in the active window. If it isn't, the actor gets pushed back with a message telling it what's missing. The Gemini incident above would have been caught by this if the element check had matched -- it didn't, because the task completion condition was ambiguous.

### Autonomy Mode

```
Task
  -> SkillInstallationMode
  -> AutonomyOrchestrator
  -> ActorModel (per turn) (reads UI tree, emits one action, updates history)
  -> PCActions / Skills
```

The actor runs in a free loop without planning and a `history` string as its working memory across turns. Each turn the model reads the live UI state, reasons about what to do next, acts, and appends a one-line summary to the history.

The actor can request skill installation mid-task via `{"action": "install_skills", "skills": [...]}`. This pauses execution, loads the requested skills, and injects them into the next turn's context.

### UI Context and the Accessibility Tree

`ContextProvider` reads the active window using pywinauto's UIA backend, walking every descendant element and filtering by control type, bounds, and content. Elements with no text, no name, and no value are discarded. Elements outside the window bounds are discarded. The result is a flat list of `ControlType | name='...' | x=... y=...` strings the actor reasons over.

`UITreeHandler` sits on top of this and sends differential updates. If the tree changes by less than 20% between reads, it sends only the added and removed elements. If it changes by 20% or more (a page navigation, a new dialog, a full app switch) it sends the whole tree. This keeps the context window from filling with redundant state on every turn.

### Python Code Execution

The `python` action lets the actor write and run arbitrary Python code in-task. `PythonRunner` handles it by parsing the code's imports using Python's AST module, auto-installing any missing third-party packages into a dedicated `.lmcontrol_venv` virtual environment, and running the code in a subprocess with a configurable timeout.

The stdout, stderr, and a result type (`SUCCESS`, `ERROR`, `TIMEOUT`, `PY_EXCEPTION`) come back to the orchestrator as context for the next action. The actor can use this to write files, launch applications, manipulate the clipboard, or query system state without touching the UI at all.

### A Few Other Things Worth Knowing

The context provider attempts to auto-expand ComboBox elements while reading the tree. If a dropdown is collapsed, it calls the UIA expand interface on it before extracting its contents. This means the actor can see dropdown options without having to click them open first.

There's a `strip_markdown_json` utility that strips markdown code fences from model responses before parsing. Models occasionally wrap their JSON output in backticks regardless of what the system prompt says, so it runs on every response as a precaution.
