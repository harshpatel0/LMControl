# Python Engine — Planner Guide

## Action Format

```
python | code=<semicolon-separated statements>
```

All dependencies are auto-installed. Code runs in an isolated venv.

## When to Use

Use `python` instead of UI steps for:

- File operations (create, move, delete, check existence)
- Process launching or system state queries
- Data transformation, calculations, string formatting
- Anything faster or more reliable done in code than via the UI

Do NOT use for anything the actor can do directly via the accessibility tree.

## Rules

- One script per step. Keep code self-contained.
- Write the actual code in the instruction — never describe what it should do.
- Chain statements with semicolons on a single line.
- `expected_result` must describe a verifiable system state, not script output.
- Every Python step needs a UI-based fallback.

## Examples

**Correct instruction:**
`python | code=import subprocess; subprocess.Popen(['notepad.exe'])`

**Correct expected_result:**
`Notepad is open and visible as the active window`

**Correct fallback:**
`Press Win+S, type Notepad, press Enter`

**Wrong instruction:**
`Run a python script to open Notepad`

**Wrong expected_result:**
`The script returns True`
