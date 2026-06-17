# Kodo — Agent Navigation Guide

This project is **Kodo**, a Windows automation framework that uses LLMs to plan and execute tasks via UI interaction, Python code execution, and custom skills.

**DO NOT USE THE OLD README.md** — it is outdated and half-useless. Use this file for navigation.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Kodo                                 │
├─────────────────────────────────────────────────────────────┤
│  main.py              → FastAPI server entry point           
│  orchestrator.py      → Planner-Actor & Autonomy orchestration│
│  context_provider.py  → UI tree extraction (pywinauto)       │
│  models/              → Ollama model wrappers                 │
│  skills/              → Executable skill modules              │
│  server/api.py        → WebSocket task execution endpoint    │
│  utils/               → Shared utilities                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

### Core Files

| File | Purpose |
|------|---------|
| `main.py` | Starts FastAPI server, opens browser to localhost |
| `orchestrator.py` | Main orchestration logic (StepOrchestrator, AutonomyOrchestrator) |
| `context_provider.py` | UI tree extraction via pywinauto, screenshot capture |
| `server/api.py` | FastAPI app with WebSocket `/run/` endpoint for task execution |
| `models/planner_model.py` | Planner model wrapper (breaks tasks into steps) |
| `models/actor_model.py` | Actor model wrapper (decides actions per step) |
| `skills/skill_orchestrator.py` | Skill discovery, loading, and execution |

### Skills Directory (`skills/`)

Each skill folder contains:
- `skill.json` — Metadata (name, description, actions, entry point, dependencies)
- `skill.py` — Executable code for the skill's actions
- `PLANNER_SKILL.md` — Guide for the planner model on when/how to use this skill
- `ACTOR_SKILL.md` — Guide for the actor model on how to invoke the skill

**Available Skills:**

| Skill | Description | Actions |
|-------|-------------|---------|
| `browser-navigation/` | Browser interaction | `open_url` |
| `python/` | Python code execution | (inline code) |
| `launch-windows-app/` | Launch installed Windows apps | `open_app` |
| `toast-notifications/` | Send toast notifications | `send_toast` |
| `word-navigation/` | Microsoft Word interface mapping | (documentation only) |

### Configuration

- `settings.json` — Runtime settings (models, orchestrator, context provider)
- `utils/globals.py` — Global constants (API port, venv name, debug flags)
- `pc_actions/perform_pc_actions.py` — Windows UI automation actions

---

## 🚀 How It Works

### Task Flow

1. **Client** sends task via WebSocket to `/run/` endpoint
2. **AutonomyOrchestrator** (or StepOrchestrator) breaks task into steps
3. **PlannerModel** generates plan with skill recommendations
4. **ActorModel** executes each step, deciding actions based on UI context
5. **ContextProvider** provides UI tree and screenshots
6. **Skills** execute specialized actions (open app, navigate browser, etc.)
7. Loop continues until task is complete or max iterations reached

### Two Modes

- **Planner-Actor Mode**: Traditional step-by-step planning + execution
- **Autonomy Mode**: Single LLM handles full task completion independently

---

## 🔧 Key Classes

### `orchestrator.py`

| Class | Purpose |
|-------|---------|
| `ActionHandlers` | Handles model responses (PROCEED, DONE, STUCK, RETRY, REPLAN) |
| `StepOrchestrator` | Orchestrates planner-actor step loop |
| `AutonomyOrchestrator` | Runs autonomy mode with skill installation |

### `context_provider.py`

| Method | Purpose |
|--------|---------|
| `get_ui_tree()` | Extracts UI element tree via pywinauto |
| `get_screenshot()` | Captures active window screenshot (base64) |
| `get_active_window()` | Returns title of foreground window |
| `request_tree_diffs()` | Returns only changed UI elements (delta) |

### `skill_orchestrator.py`

| Method | Purpose |
|--------|---------|
| `_discover()` | Scans `skills/` folder for skill.json files |
| `load_all_requested_skills()` | Loads skills for planner or actor |
| `execute(action)` | Runs a skill by action name |
| `list_actions()` | Returns all available skill actions |

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves frontend (index.html) |
| `/settings/` | GET | Returns current settings.json |
| `/settings/` | POST | Updates settings |
| `/desktop-feed` | GET | Multipart video stream of desktop |
| `/run/` | WebSocket | Execute task (required: `task`, optional: `mode_override`) |

**WebSocket Message Format:**
```json
{"type": "log", "message": "..."}
{"type": "status", "status": "done"}
{"type": "error", "message": "..."}
```

---

## 🎯 Model Configuration (`settings.json`)

| Role | Model | Temperature | Notes |
|------|-------|-------------|-------|
| `skill_installation` | gemma4:e4b | 0.1 | Deterministic package resolution |
| `planner` | gemma4:e4b | 0.7 | Breaks tasks into steps |
| `actor` | gemma4:e4b | 0.7 | Decides actions per step |
| `autonomy_actor` | gemma4:e4b | 0.5 | Full autonomy mode |

---

## 🛠️ Development Tips

### Running the Server

```bash
python main.py
# Opens http://127.0.0.1:8000 in browser
# WebSocket endpoint available at ws://127.0.0.1:8000/run/
```

### Task Execution via WebSocket

```python
import websockets

async def run_task():
    async with websockets.connect("ws://127.0.0.1:8000/run/") as ws:
        await ws.send_text('Open Notepad')
        async for msg in ws:
            print(msg)
```

### Adding a New Skill

1. Create folder in `skills/` (e.g., `my-skill/`)
2. Add `skill.json`:
   ```json
   {
     "name": "my-skill",
     "description": "My custom skill",
     "actions": ["my_action"],
     "entry": "skill.py",
     "dependencies": []
   }
   ```
3. Add `skill.py` with action handler
4. Add `PLANNER_SKILL.md` and `ACTOR_SKILL.md` guides

---

## 📦 Dependencies

- `pywinauto` — UI automation
- `pygetwindow` — Window management
- `pyautogui` — Screenshot capture
- `winapps` — Windows app enumeration
- `fastapi`, `uvicorn` — Web server
- `mss`, `opencv-python`, `numpy` — Desktop streaming
- Ollama models (gemma4:e4b)

---

## 🐛 Debugging

- Enable debug output in `utils/globals.py`:
  - `ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE = True`
  - `MODEL_DEFINITIONS_ENABLE_DEBUG_OLLAMA_REQUESTS = True`
- Check generated files:
  - `dbg_actor_model.txt` — Actor prompt construction logs
  - `dbg_make_ollama_request.txt` — Ollama request/response logs

---

## 📝 Notes

- **Always prefer skill actions over raw Python** when a skill exists
- **Python action** is a fallback for file ops, process launches, etc.
- **Autonomy mode** should be used with caution (no step-by-step oversight)
- **UI tree diffs** reduce context size by only sending changed elements

---

## 🔗 Related Documentation

- `README.md` — Outdated, ignore
- `skills/skill_orchestrator.py` — Skill loading logic
- `models/ollama/model_definitions.py` — Model configuration schemas
