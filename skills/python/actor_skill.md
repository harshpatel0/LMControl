# Python Engine — Actor Guide

## The `python` Action

Use the `python` action when a task is better accomplished with direct code execution
than UI interaction. This is always preferred over manually navigating a UI to achieve
something that Python can do in one line.

**Format:**
{"action": "python", "code": "<valid single-line or multi-line python code>"}

## When to Use

- Opening URLs or launching applications
- File system operations (read, write, move, delete)
- Clipboard manipulation
- System queries (running processes, installed apps, environment info)
- Anything where a UI interaction would take multiple steps but Python can do it in one

## When NOT to Use

- When a skill action already covers the task — always prefer skill actions over raw Python
- When the task requires visual confirmation of a UI state (screenshot-based verification)
- When interacting with elements inside a running application (use click/type instead)

## Code Rules

- Keep code to a single logical operation per action
- Use only stdlib unless you know a third-party package is available
  - The Python Runner will try it's best to install the package for you by reading your code and installing the dependency before running it.

- Always use semicolons to chain statements on one line where possible
- Never write code that blocks indefinitely (no `input()`, no infinite loops, your code will cease execution, no matter it's state after a timeout, by default `15 seconds`)
- Print a confirmation message so you and the orchestrator know the action succeeded on the next run.

## Examples

**Write to a file:**
{"action": "python", "code": "open(filepath, 'w').write('hello world'); print('File written')"}

When writing to a file, always write it to the User's download folder, such that `filepath` = %USERPROFILE%\Downloads\{filename here}

**Copy text to clipboard:**
{"action": "python", "code": "import subprocess; subprocess.run(['clip'], input='some text', text=True); print('Copied to clipboard')"}

## Output

Whatever is printed to stdout is returned to the orchestrator as context for the next
step. Always print a short confirmation so the orchestrator can verify the action ran.
If the code fails silently with no output, the orchestrator will treat it as a failed step.

## Important

This action is built into the system — it does not require an action to be declared.
Always prioritise installed skill actions first. Fall back to `python` only when no
skill covers the task.
