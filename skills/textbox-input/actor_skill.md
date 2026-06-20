## Textbox Input Skill — Actor Guide

### Purpose
Pause automation and ask the user a question via a Tkinter popup textbox. The user's response is captured and returned to the LLM for further processing.

### When to Use
- You need human input to proceed with a task (e.g., "What folder should I save this to?")
- A decision requires confirmation from the user
- Information is not available in the UI and must come from the user

### Action: `prompt_user`

#### JSON Format
```json
{
  "action": "prompt_user",
  "title": "Window Title",
  "body": "Question or prompt text to show the user"
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | No | Window title (defaults to "Kodo") |
| `body` | string | No | The prompt text shown to the user (defaults to "Enter your response:") |

#### Example
```json
{
  "action": "prompt_user",
  "title": "Save Confirmation",
  "body": "Enter the filename for the report:"
}
```

### Response Handling
The user's text input is printed to stdout. Treat it as a string that can be used in subsequent actions.

### Failure Modes
- **User cancels the dialog**: The action exits with an error. Handle this by re-prompting or using a fallback.
- **Tkinter not available**: Unlikely on Windows, but the action will fail with a clear error to stderr.

### Recovery
If the user cancels, acknowledge the cancellation and either:
1. Re-prompt with different wording or context
2. Use a sensible default value
3. Stop the task and explain why user input was needed
