# Browser — Actor Guide (MCP)

Provides full browser control via the `chrome-devtools` MCP server. Covers navigation, interaction, DOM inspection, JavaScript execution, network monitoring, screenshots, and performance analysis.

---

## Calling Convention

Every tool call below must be wrapped in the dispatcher's `mcp_tool_call` envelope:

```json
{"action": "mcp_tool_call", "tool": "<tool_name>", "arguments": {...}, "history": "<what you did>"}
```

The JSON shown under each tool heading is the `arguments` payload only — never emit it as a top-level action.

---

## Snapshot First

Always call `take_snapshot` before interacting with any element. Snapshots provide `uid` values required by all interaction tools. **UIDs expire after every navigation — re-snapshot after any page change.**

---

## Navigation

### navigate_page

Navigate to a URL, or go back, forward, or reload.

```json
{"action": "mcp_tool_call", "tool": "navigate_page", "arguments": {"type": "url", "url": "https://example.com"}, "history": "Navigated to https://example.com"}
{"action": "mcp_tool_call", "tool": "navigate_page", "arguments": {"type": "back"}, "history": "Navigated back"}
{"action": "mcp_tool_call", "tool": "navigate_page", "arguments": {"type": "forward"}, "history": "Navigated forward"}
{"action": "mcp_tool_call", "tool": "navigate_page", "arguments": {"type": "reload"}, "history": "Reloaded the page"}
```

- Use `type=url` with a `url` value to navigate to a page.
- Use `type=reload` with `ignoreCache=true` to hard reload.

### new_page

Open a URL in a new tab.

```json
{"action": "mcp_tool_call", "tool": "new_page", "arguments": {"url": "https://example.com"}, "history": "Opened https://example.com in a new tab"}
```

- Use `background=true` to open without switching focus.

### list_pages / select_page / close_page

Manage open tabs.

```json
{"action": "mcp_tool_call", "tool": "list_pages", "arguments": {}, "history": "Listed open pages"}
{"action": "mcp_tool_call", "tool": "select_page", "arguments": {"pageId": 1}, "history": "Switched to page 1"}
{"action": "mcp_tool_call", "tool": "close_page", "arguments": {"pageId": 1}, "history": "Closed page 1"}
```

- Always call `list_pages` before `select_page` or `close_page` to get valid page IDs.
- The last open page cannot be closed.

---

## Interaction

### click

Click an element by its uid.

```json
{"action": "mcp_tool_call", "tool": "click", "arguments": {"uid": "<uid>"}, "history": "Clicked element <uid>"}
```

- Use `dblClick=true` for double-clicks.
- Always obtain uid from the latest `take_snapshot`.

### fill

Type into an input, textarea, or select a dropdown option.

```json
{"action": "mcp_tool_call", "tool": "fill", "arguments": {"uid": "<uid>", "value": "text to enter"}, "history": "Filled element <uid> with text"}
```

- For checkboxes and toggles: `"value": "true"` or `"value": "false"`.
- For radio buttons: `"value": "true"`.

### fill_form

Fill multiple form fields in a single call. **Prefer this over multiple `fill` or `click` calls whenever interacting with forms.**

```json
{
  "action": "mcp_tool_call",
  "tool": "fill_form",
  "arguments": {
    "elements": [
      {"uid": "<uid>", "value": "username"},
      {"uid": "<uid>", "value": "password"},
      {"uid": "<uid>", "value": "true"}
    ]
  },
  "history": "Filled login form fields"
}
```

### type_text

Type text into a previously focused element using keyboard input.

```json
{"action": "mcp_tool_call", "tool": "type_text", "arguments": {"text": "text to type", "submitKey": "Enter"}, "history": "Typed text and submitted with Enter"}
```

- Use only when `fill` cannot be used (e.g. rich text editors, custom inputs).
- `submitKey` is optional — use `"Enter"`, `"Tab"`, or `"Escape"` as needed.

### press_key

Send a key or key combination.

```json
{"action": "mcp_tool_call", "tool": "press_key", "arguments": {"key": "Control+A"}, "history": "Pressed Control+A"}
{"action": "mcp_tool_call", "tool": "press_key", "arguments": {"key": "Enter"}, "history": "Pressed Enter"}
{"action": "mcp_tool_call", "tool": "press_key", "arguments": {"key": "Control+Shift+R"}, "history": "Pressed Control+Shift+R"}
```

- Use for keyboard shortcuts or navigation keys not achievable via `fill` or `type_text`.

### hover

Hover over an element.

```json
{"action": "mcp_tool_call", "tool": "hover", "arguments": {"uid": "<uid>"}, "history": "Hovered over element <uid>"}
```

- Use to trigger tooltips or reveal hover-dependent UI before interacting.

### drag

Drag one element onto another.

```json
{"action": "mcp_tool_call", "tool": "drag", "arguments": {"from_uid": "<uid>", "to_uid": "<uid>"}, "history": "Dragged element to target"}
```

### upload_file

Upload a file via a file input element.

```json
{"action": "mcp_tool_call", "tool": "upload_file", "arguments": {"uid": "<uid>", "filePath": "C:\\Users\\harshpatel\\Documents\\file.pdf"}, "history": "Uploaded file.pdf"}
```

### handle_dialog

Handle a browser dialog (alert, confirm, prompt).

```json
{"action": "mcp_tool_call", "tool": "handle_dialog", "arguments": {"action": "accept"}, "history": "Accepted dialog"}
{"action": "mcp_tool_call", "tool": "handle_dialog", "arguments": {"action": "dismiss", "promptText": "response text"}, "history": "Dismissed dialog with response text"}
```

- Call this immediately when a dialog is triggered.

### wait_for

Wait for specific text to appear on the page.

```json
{"action": "mcp_tool_call", "tool": "wait_for", "arguments": {"text": ["Login successful", "Welcome"], "timeout": 5000}, "history": "Waited for login confirmation text"}
```

- Resolves when **any** value in the list appears.
- Use after navigation or form submission to confirm page state before continuing.

---

## DOM Inspection

### take_snapshot

Take an accessibility tree snapshot of the current page. Returns elements with their `uid` values.

```json
{"action": "mcp_tool_call", "tool": "take_snapshot", "arguments": {}, "history": "Took accessibility snapshot"}
{"action": "mcp_tool_call", "tool": "take_snapshot", "arguments": {"verbose": true}, "history": "Took verbose accessibility snapshot"}
```

- **Always call this before any interaction.**
- Prefer over `take_screenshot` for element targeting.
- Use `verbose=true` only when default snapshot is insufficient.

### evaluate_script

Execute a JavaScript function in the current page context.

```json
{"action": "mcp_tool_call", "tool": "evaluate_script", "arguments": {"function": "() => { return document.title; }"}, "history": "Read document title via script"}
{"action": "mcp_tool_call", "tool": "evaluate_script", "arguments": {"function": "() => { return document.querySelectorAll('a').length; }"}, "history": "Counted links via script"}
```

- Returns JSON-serializable values only.
- **Use only when no native MCP tool achieves the goal.** Prefer `take_snapshot`, `click`, `fill` over scripting.
- Use `filePath` to save large outputs to disk instead of inline.

---

## Screenshots

### take_screenshot

Capture a screenshot of the page or a specific element.

```json
{"action": "mcp_tool_call", "tool": "take_screenshot", "arguments": {}, "history": "Took screenshot"}
{"action": "mcp_tool_call", "tool": "take_screenshot", "arguments": {"uid": "<uid>"}, "history": "Took screenshot of element <uid>"}
{"action": "mcp_tool_call", "tool": "take_screenshot", "arguments": {"fullPage": true, "filePath": "C:\\Users\\harshpatel\\Desktop\\screenshot.png"}, "history": "Saved full-page screenshot to disk"}
```

- Use for **visual verification only** — not for element targeting (use `take_snapshot` for that).
- `uid` and `fullPage` are mutually exclusive.
- Use `filePath` to save to disk; omit to return inline.

---

## Network Inspection

### list_network_requests

List all network requests since the last navigation.

```json
{"action": "mcp_tool_call", "tool": "list_network_requests", "arguments": {}, "history": "Listed network requests"}
{"action": "mcp_tool_call", "tool": "list_network_requests", "arguments": {"resourceTypes": ["fetch", "xhr"], "pageSize": 20}, "history": "Listed fetch/xhr network requests"}
```

- Filter by `resourceTypes` to reduce noise (e.g. `"fetch"`, `"xhr"`, `"document"`, `"script"`).

### get_network_request

Get full details of a specific request including headers and body.

```json
{"action": "mcp_tool_call", "tool": "get_network_request", "arguments": {"reqid": 5}, "history": "Fetched details for request 5"}
{"action": "mcp_tool_call", "tool": "get_network_request", "arguments": {"reqid": 5, "responseFilePath": "C:\\Users\\harshpatel\\Documents\\response.json"}, "history": "Saved response body for request 5"}
```

- Use `reqid` from `list_network_requests`.
- Use `responseFilePath` to save large response bodies to disk.

### list_console_messages / get_console_message

Inspect browser console output.

```json
{"action": "mcp_tool_call", "tool": "list_console_messages", "arguments": {"types": ["error", "warning"]}, "history": "Listed console errors and warnings"}
{"action": "mcp_tool_call", "tool": "get_console_message", "arguments": {"msgid": 3}, "history": "Fetched console message 3"}
```

- Filter by `types`: `"log"`, `"error"`, `"warning"`, `"info"`.

---

## Performance

### performance_start_trace / performance_stop_trace

Record a performance trace.

```json
{"action": "mcp_tool_call", "tool": "performance_start_trace", "arguments": {"reload": true, "autoStop": true}, "history": "Started performance trace"}
```

- Navigate to the target URL **before** starting the trace.
- Use `filePath` to save raw trace data (`.json.gz` recommended).

### performance_analyze_insight

Get detailed analysis of a specific performance insight from a trace.

```json
{"action": "mcp_tool_call", "tool": "performance_analyze_insight", "arguments": {"insightSetId": "<id>", "insightName": "LCPBreakdown"}, "history": "Analyzed LCP breakdown insight"}
```

- Use IDs returned by `performance_start_trace`.

### lighthouse_audit

Run a Lighthouse audit for accessibility, SEO, and best practices.

```json
{"action": "mcp_tool_call", "tool": "lighthouse_audit", "arguments": {"mode": "navigation", "device": "desktop"}, "history": "Ran navigation Lighthouse audit"}
{"action": "mcp_tool_call", "tool": "lighthouse_audit", "arguments": {"mode": "snapshot"}, "history": "Ran snapshot Lighthouse audit"}
```

- `navigation` reloads the page before auditing.
- `snapshot` audits the current page state.
- Does **not** include performance — use `performance_start_trace` for that.

---

## Emulation

### emulate

Emulate device, network, geolocation, or viewport conditions.

```json
{"action": "mcp_tool_call", "tool": "emulate", "arguments": {"viewport": "375x812x2,mobile,touch"}, "history": "Emulated mobile viewport"}
{"action": "mcp_tool_call", "tool": "emulate", "arguments": {"colorScheme": "dark"}, "history": "Emulated dark color scheme"}
{"action": "mcp_tool_call", "tool": "emulate", "arguments": {"networkConditions": "Slow 3G"}, "history": "Emulated Slow 3G network"}
{"action": "mcp_tool_call", "tool": "emulate", "arguments": {"geolocation": "51.5074,-0.1278"}, "history": "Emulated geolocation"}
```

- Omit a parameter to clear/reset that emulation.
- Use `extraHttpHeaders` to inject auth or custom headers for all requests.

### resize_page

Resize the browser window.

```json
{"action": "mcp_tool_call", "tool": "resize_page", "arguments": {"width": 1280, "height": 800}, "history": "Resized browser window"}
```

---

## Memory

### take_heapsnapshot

Capture a JavaScript heap snapshot for memory leak analysis.

```json
{"action": "mcp_tool_call", "tool": "take_heapsnapshot", "arguments": {"filePath": "C:\\Users\\harshpatel\\Documents\\heap.heapsnapshot"}, "history": "Captured heap snapshot"}
```

- Open the `.heapsnapshot` file in Chrome DevTools Memory panel for analysis.

---

## Notes

- **Snapshot before every interaction.** UIDs are not stable across navigations.
- **Prefer `fill_form` over multiple `fill` calls** when filling more than one field.
- **Prefer native tools over `evaluate_script`.** Use JS execution only as a last resort.
- **Prefer `take_snapshot` over `take_screenshot`** for understanding page structure.
- After any navigation or page-changing action, call `wait_for` before proceeding to confirm the page has settled.
- `list_pages` before `select_page` or `close_page` — never assume page IDs.