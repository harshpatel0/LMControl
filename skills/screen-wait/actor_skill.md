# Screen Wait — Actor Guide

## When to use

Use this skill instead of guessing or retrying when you know something is about to appear but hasn't yet. It actively polls the UI so you don't waste iterations clicking on elements that don't exist yet.

## Actions

### wait_for_element

Polls the active window's UIA tree until an element whose name contains the given string is found.

```json
{"action": "wait_for_element", "element": "Save As", "timeout": 15}
```

**Parameters:**
- `element` — the name (or substring) of the element to wait for (required)
- `timeout` — max seconds to wait, default 15 (optional)
- `poll_interval` — seconds between each poll, default 0.5 (optional)

On success, stdout confirms which element was found and how many polls it took. On timeout, stderr reports failure and the skill exits with code 1 — the orchestrator will treat this as a RETRY.

### wait_for_window

Waits until a window with a matching title is open and detectable.

```json
{"action": "wait_for_window", "title": "Notepad", "timeout": 10}
```

**Parameters:**
- `title` — substring to match against window titles (required)
- `timeout` — max seconds to wait, default 15 (optional)
- `poll_interval` — seconds between each poll, default 0.5 (optional)

## Gotchas

- Matching is case-insensitive substring, so `"element": "Save"` will match any element whose name contains "Save". If there are multiple such elements, the first one found counts — be specific enough to avoid false positives.
- `wait_for_element` only searches the **active window**. If the expected element is in a window that hasn't gained focus yet, use `wait_for_window` first.
- If the skill times out and the orchestrator retries, consider increasing `timeout` or checking whether the triggering action (launch, click, etc.) actually succeeded.
- Do NOT call this skill in a loop manually — call it once with an appropriate `timeout` and let it poll internally.
- After `wait_for_element` or `wait_for_window` succeeds, always re-read the UI tree on the next turn before acting — coordinates from before the wait are likely stale.