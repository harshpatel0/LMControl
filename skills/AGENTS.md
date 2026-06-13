# AGENTS.md — Kodo Skill Authoring Guide

This document teaches AI coding agents (Claude Code, Codex, etc.) how to create skills
for the Kodo automation system. Read it fully before writing any skill files.

---

## What is a Skill?

A skill is a folder inside the `skills/` directory. It packages related capabilities —
executable actions, LLM guidance documents, or both — into a self-contained unit that
the Skill Orchestrator discovers and loads automatically at runtime.

---

## Skill Folder Structure

```
skills/
└── my-skill/
    ├── skill.json          # Required. Declares the skill's metadata.
    ├── skill.py            # Required only if the skill defines actions or dynamic context.
    ├── planner_skill.md    # Guidance injected into the Planner's prompt (see rules below).
    └── actor_skill.md      # Guidance injected into the Actor's prompt (see rules below).
```

---

## skill.json — The Manifest

Every skill must have a `skill.json`. It is the only required file.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Unique identifier matching the folder name. |
| `description` | string | Yes | One-sentence description. Used in skill summaries shown to the LLM. |
| `enabled` | boolean | No | Defaults to `true`. Set `false` to disable without deleting. |
| `actions` | string[] | No | List of action names this skill registers. Omit or use `[""]` if no actions. |
| `entry` | string | No | Filename of the entry point script (e.g. `"skill.py"`). **Required if `actions` is non-empty or `dynamic_context` is `true`.** |
| `dependencies` | string[] | No | pip packages to install before the skill runs. |
| `dynamic_context` | boolean | No | If `true`, the entry point generates guidance at runtime via `--generate`. |
| `generated_for_planner` | boolean | No | Used with `dynamic_context`. Indicates the generator produces planner guidance. |
| `generated_for_actor` | boolean | No | Used with `dynamic_context`. Indicates the generator produces actor guidance. |

### Entry Point Rules

- **No `entry` needed** when the skill has no actions and `dynamic_context` is `false`.
  Static `.md` files alone are sufficient in that case.
- **`entry` is required** when `actions` is non-empty — the entry point must handle
  every declared action name.
- **`entry` is required** when `dynamic_context` is `true` — the entry point must handle
  a `--generate` argument (see below).

---

## Communication Protocol — stdout and stderr

The entry point communicates with the Orchestrator exclusively through prints.

- **stdout** — normal output. Confirmation messages, generated context JSON, action
  results. The Orchestrator reads this to determine what happened.
- **stderr** — errors and warnings only. Use `print("...", file=sys.stderr)` for
  anything that signals a failure or unexpected condition.

```python
import sys

# Success — goes to stdout, Orchestrator sees it
print("Toast sent successfully")

# Failure — goes to stderr, Orchestrator treats it as an error
print(f"App '{app_name}' not found", file=sys.stderr)
```

**Always print a short confirmation to stdout when an action completes successfully.**
If stdout is empty after execution, the Orchestrator treats the action as failed.

---

## Skill Types

### Type 1 — Guidance Only (no entry point)

Provides `.md` files that are injected into the Planner and/or Actor system prompts.
No Python is executed. No `entry` field needed.

```json
{
  "name": "word-navigation",
  "description": "Procedural steps for operating Microsoft Word.",
  "enabled": true,
  "actions": [""],
  "entry": ""
}
```

At least one of `planner_skill.md` or `actor_skill.md` must be present — a guidance-only
skill with no `.md` files contributes nothing.

---

### Type 2 — Executable Actions

Registers one or more named actions that the Actor can invoke. The entry point receives
action arguments as a JSON string via `sys.argv[1]` and performs the work.

#### Single action — skill.json

```json
{
  "name": "toast-notifications",
  "description": "Send a Windows toast notification to the user.",
  "actions": ["send_toast"],
  "entry": "skill.py",
  "dependencies": ["winotify"]
}
```

#### Multiple actions — skill.json

List every action name in the `actions` array. Each name must be handled by the entry
point.

```json
{
  "name": "file-utils",
  "description": "Read, write, and delete files on the local filesystem.",
  "actions": ["read_file", "write_file", "delete_file"],
  "entry": "skill.py"
}
```

#### Entry point — argument handling

The Orchestrator strips the `"action"` key before invoking the entry point. By the time
`sys.argv[1]` arrives at the script, it contains **only the parameters** for that action
— there is no `"action"` key to read.

``` cmd
Actor emits:  {"action": "send_toast", "title": "Done", "body": "Task complete"}
```

**Single action (simple case):**

Because the entry point is only ever called for the one action it handles, no routing is
needed — just unpack the params directly.

```python
import sys
import json

def send_toast(title, body):
    from winotify import Notification
    toast = Notification(app_id="Kodo", title=title, msg=body)
    toast.show()
    print("Toast sent successfully")  # stdout confirmation

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    send_toast(args.get("title"), args.get("body"))
```

**Multiple actions — dispatch by parameter signature:**

All actions in a skill share one entry point. Since `"action"` is stripped before
arrival, the entry point must determine which function to call by inspecting which
parameters are present in `args`. Design each action to have a distinct required
parameter (or a unique combination) so the entry point can route unambiguously.

```python
import sys
import json
import os

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())  # stdout — content is the result
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)

def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Written to {path}")  # stdout confirmation
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)

def delete_file(path):
    try:
        os.remove(path)
        print(f"Deleted {path}")  # stdout confirmation
    except Exception as e:
        print(f"Error deleting file: {e}", file=sys.stderr)

if __name__ == "__main__":
    args = json.loads(sys.argv[1])

    # Route by which action was brought in

    if args.get("action") == "delete_file":
      delete_file(args.get("path"))

    # and so on
```

Here is a base file to start from, it is enough to get a parameter and do something

``` py
import json
import sys

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
```

> If the skill has a single registered action, you can safely ignore the action parameter.
---

### Type 3 — Dynamic Context

The entry point generates its own guidance at runtime instead of relying on static `.md`
files. Useful when guidance depends on system state (e.g. listing installed apps).
Static `.md` files are not needed — and should not be present — when context is fully
dynamic.

```json
{
  "name": "launch-windows-app",
  "description": "Launch any installed Windows application by name.",
  "actions": ["open_app"],
  "entry": "skill.py",
  "dynamic_context": true,
  "generated_for_planner": true,
  "generated_for_actor": true
}
```

**Entry point contract — `--generate` argument:**

When the Orchestrator needs guidance for this skill, it calls the entry point with
`--generate`. The script must detect this, print a JSON object to stdout, then `sys.exit`.
The `--generate` check must come **before** any action handling.

```python
import sys
import json

def generate_context():
    # Build guidance strings dynamically — e.g. query the system here
    context = {
        "planner": "## My Skill — Planner Guide\n...",
        "actor":   "## My Skill — Actor Guide\n..."
    }
    print(json.dumps(context))  # stdout — Orchestrator parses this
    sys.exit(0)

def open_app(app):
    # ... launch logic ...
    print(f"Launched {app}")  # stdout confirmation

if __name__ == "__main__":
    # --generate MUST be checked first
    if "--generate" in sys.argv:
        generate_context()

    # "action" has already been stripped by the Orchestrator — only params arrive here
    args = json.loads(sys.argv[1])
    open_app(args.get("app"))
```

- The JSON object printed during `--generate` must contain `"planner"` and/or `"actor"`
  keys whose values are markdown strings.
- Only include keys that match `generated_for_planner` / `generated_for_actor` in
  `skill.json`. A skill can generate guidance for just one consumer if needed.

---

## Guidance Documents — planner_skill.md and actor_skill.md

These files are injected verbatim into the LLM's system prompt. Write them as if
briefing a capable but context-blind agent.

### When .md files are needed

| Skill type | planner_skill.md | actor_skill.md |
|---|---|---|
| Guidance only (no entry point) | At least one must be present | At least one must be present |
| Executable actions, static guidance | Recommended | Recommended |
| Dynamic context (`dynamic_context: true`) | Not needed — generated at runtime | Not needed — generated at runtime |

A skill does not need both files. A skill that only informs the Planner (e.g. strategic
planning rules) only needs `planner_skill.md`. A skill that only teaches the Actor how
to invoke an action only needs `actor_skill.md`. Provide whichever subset is useful.

### planner_skill.md

Teaches the Planner **what** to plan and **when** to use this skill's actions.

- Describe when the skill is appropriate.
- Show the instruction format the Planner should emit for each action:
  ```
  instruction: "action_name | param=value param2=value2"
  ```
- Describe `expected_result` phrasing — it must describe a verifiable system state,
  not script output.
- Include a fallback UI path in case the action fails.

### actor_skill.md

Teaches the Actor **how** to invoke actions and recover from failure.

- Show the exact JSON the Actor should emit for each action:
  ```json
  {"action": "action_name", "param": "value"}
  ```
- Document every parameter.
- Include gotchas, failure modes, and recovery steps.

---

## Checklist Before Submitting a Skill

- [ ] `skill.json` present with `name` and `description`.
- [ ] `entry` set **if and only if** the skill defines actions or uses `dynamic_context`.
- [ ] Every action name in `actions` has a corresponding handler in the entry point.
- [ ] Multi-action entry points route by inspecting which parameters are present —
      `"action"` is stripped by the Orchestrator before the entry point is called.
- [ ] Each action in a multi-action skill has a uniquely named param or discriminator
      so routing is unambiguous.
- [ ] `--generate` branch is the **first** thing checked in `__main__` when
      `dynamic_context` is `true`.
- [ ] `generate_context()` prints valid JSON to stdout and calls `sys.exit(0)`.
- [ ] All success output goes to **stdout**; all errors go to **stderr**.
- [ ] Every action prints a confirmation string to stdout on success.
- [ ] `dependencies` lists every non-stdlib package the entry point imports.
- [ ] `.md` files are present when the skill is not dynamically generated; at minimum
      one of `planner_skill.md` or `actor_skill.md` must exist.
- [ ] Skill folder name matches the `name` field in `skill.json`.

---

## Quick Reference — skill.json Combinations

| Has actions? | Dynamic context? | Needs `entry`? | Needs `.md` files? |
|---|---|---|---|
| No | No | No | Yes — at least one of planner or actor |
| Yes | No | Yes | Recommended — whichever consumers use the skill |
| No | Yes | Yes | No — generated at runtime |
| Yes | Yes | Yes | No — generated at runtime |