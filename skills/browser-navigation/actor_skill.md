# Browser Navigation — Actor Guide

## Address Bar

Always use Ctrl+L to focus the address bar before typing a URL.
After Ctrl+L the bar is focused — emit the type action immediately.

Before typing, check the screenshot: if the previous URL is still visible and
not highlighted, emit ctrl+a then backspace to clear it. This prevents malformed
URLs like "youtube.comhttps://".

## New Tab Search Box

The new tab page contains a search box (Bing, Google, etc). This is never a
valid target for URL navigation or task-related searches. Always use the address
bar via Ctrl+L. This is a trap element — do not click it.

## Site Search Boxes

When a step targets a site-specific search box (e.g. YouTube search box, Google
search box), locate it in the ACCESSIBILITY TREE by name before acting.
The address bar is never a substitute for a page-level search field.

If the search element is not in the tree:
- Use the fallback from the step
- Do not fall back to the address bar on your own
- Emit scroll_v to bring it into view if the page is loaded but element is not visible
- Try keyboard shortcuts (e.g. "/" for YouTube, GitHub) to focus the search box

## Ambiguous Search Target

If the step says "type into the search bar" and both the address bar and a
page-level search box are visible, default to the address bar unless navigation
to a specific site is already confirmed complete.

## Wrong Page Recovery

If the active window is a browser but the wrong page is loaded:
1. press_hotkey ctrl+l
2. type the correct URL
3. press_key enter

Never declare stuck because you are on the wrong page within the browser.

## Tab Safety

Before typing a URL, check if the active tab contains content unrelated to the
current task. If it does, emit press_hotkey ctrl+t to open a new tab first.

## Search Result Recovery

If a click on a search result does not change the page title:
- Do NOT click the same coordinate again
- Try a different part of the result (e.g. thumbnail instead of text link)
- If the tree shows only one element, emit scroll_v to find a traditional results list

## Type Submission

The type action submits automatically. After a type action, if the page title
does not change within a couple of seconds, emit retry to re-focus and retype.
Do NOT click Refresh.

## Type Failures

If a type action fails to navigate three consecutive times, do not keep replanning
the same instruction. Instead try a keyboard shortcut to reset focus:
- "/" for YouTube or GitHub search
- Ctrl+L for browser address bar

## open_url Action

For navigating to a URL, prefer the open_url skill action over manual keystrokes:
{"action": "open_url", "url": "https://example.com"}

This opens the default browser directly. Only fall back to manual navigation
(Ctrl+T → Ctrl+L → type → Enter) if open_url is unavailable.