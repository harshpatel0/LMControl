# Screen Wait — Planner Guide

## When to use

- After launching an application that takes time to load before its UI is interactive
- After clicking a button that triggers a slow operation (file save, export, network request)
- When a dialog or confirmation prompt is expected but may not appear immediately
- Any step where the next action depends on a specific UI element or window being present

This skill is a targeted replacement for hoping `action_settle_time` is long enough. Use it wherever a step's success depends on something appearing rather than on a fixed wait.

## Actions

### wait_for_element

Waits until a UI element whose name **contains** the given string appears in the active window's accessibility tree. Succeeds as soon as the element is found; fails (with an error) if `timeout` seconds pass without it appearing.

```
instruction: "wait_for_element | element=Save As dialog | timeout=10"
expected_result: "The Save As dialog is visible and confirmed present in the UI tree"
fallback: "Wait 5 seconds using action_settle_time and proceed regardless"
```

**Parameters:**
- `element` — substring to match against element names (case-insensitive, required)
- `timeout` — seconds to wait before failing (optional, default 15)
- `poll_interval` — seconds between polls (optional, default 0.5)

### wait_for_window

Waits until a window whose title **contains** the given string becomes visible (either as the active window or anywhere open). Useful after launching an app or opening a new window.

```
instruction: "wait_for_window | title=Notepad | timeout=10"
expected_result: "Notepad window is confirmed open and visible"
fallback: "Press Win+S, search for Notepad, and open it manually"
```

**Parameters:**
- `title` — substring to match against window titles (case-insensitive, required)
- `timeout` — seconds to wait before failing (optional, default 15)
- `poll_interval` — seconds between polls (optional, default 0.5)

## Planning Rules

- Always plan a `wait_for_window` or `wait_for_element` step immediately after any app launch step, before the first interaction step with that app.
- Keep `timeout` realistic — 10–15s for most apps, 30s for heavy apps (Office, IDEs, browsers cold-starting).
- `wait_for_element` matches substrings, so `element=Save` will match "Save As", "Save File", "Auto-Save", etc. Be specific enough to avoid false positives.
- Do NOT use this as a replacement for every `action_settle_time` wait — only use it when you are waiting for something specific to appear.