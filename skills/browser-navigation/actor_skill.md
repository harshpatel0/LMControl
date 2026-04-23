# Browser Navigation — Actor Guide

## ⚠️ TASK COMPLETION FOR VIDEO AND CONTENT TASKS

**Seeing a video in search results, recommendations, or the home feed is NOT done.**

Done for a video task means:
- The **video's watch page** is the active window
- The video player is visible and the video is loaded/playing

Done for a page/link task means:
- The **target page is loaded** as the primary active display

You MUST click the video thumbnail or title link, then confirm the watch page has loaded before emitting done.

---

## ⚠️ SEARCH BOX PRIORITY — READ BEFORE TYPING

**When you are already on a website (YouTube, Google, etc.), ALWAYS use the site's own search box. NEVER use the browser address bar for on-site search.**

Priority order:
1. **Site search box** (YouTube search box, Google search box, etc.) — use this when you are already on the site
2. **Browser address bar** (Ctrl+L) — use ONLY for navigating to a new URL

The new tab page search box (Bing, Google widget on new tab) is a trap element — do not use it for anything.

---
## Address Bar

Use Ctrl+L to focus the address bar before typing a URL. After Ctrl+L, the bar is focused — emit the type action immediately.

Before typing, check the screenshot: if the previous URL is still visible and not highlighted, clear the field first. This prevents malformed URLs like `youtube.comhttps://`.

## YouTube and Site Search Boxes

When navigating to a site's own search box (YouTube, GitHub, etc.):
- Locate it in the ACCESSIBILITY TREE by name before acting
- Use keyboard shortcuts to focus if needed: `/` for YouTube, `/` for GitHub
- Do NOT fall back to the address bar for site search — these are different targets
- If the element is not in the tree: scroll_v to bring it into view

## open_url Action

For URL navigation, always prefer `open_url` over manual keystrokes:

```json
{"action": "open_url", "url": "https://example.com"}
```

Only fall back to manual navigation (Ctrl+T → Ctrl+L → type → Enter) if open_url is unavailable.

## Wrong Page Recovery

If the active window is a browser but the wrong page is loaded:
1. `press_hotkey ctrl+l`
2. type the correct URL
3. `press_key enter`

Never declare stuck because you are on the wrong page within the browser.

## Tab Safety

Before typing a URL, check if the active tab contains content unrelated to the current task. If it does, emit `press_hotkey ctrl+t` to open a new tab first.

## Type Submission

The type action submits automatically. If the page title does not change after a type action, emit retry to re-focus and retype. Do NOT click Refresh.

## Type Failures

If a type action fails to navigate three consecutive times:
- `/` to focus YouTube or GitHub search
- `Ctrl+L` to focus the browser address bar
- 
## Result Matching

When a step instruction says "whose title contains [X]", verify the element 
name in the accessibility tree contains that string before clicking.
If no matching element is visible, scroll_v to find one. 
Never click an element whose name does not match the constraint.


## Rules 
### WRONG SITE RECOVERY
If the active window URL contains "bing.com" or 
"google.com/search" and the task involves YouTube, immediately use 
open_url to return to youtube.com. Do not search on Bing.

### Completing the Action

Lead the user directly to the resource:

- **YouTube video**: Navigate directly to the video's watch page. Seeing the video in search results is not enough — click the title or thumbnail.
- **Section of a webpage**: Navigate directly to it, scroll if needed.
- **Shop item**: Navigate directly to the product page.
- **Form**: Fill it out using user-provided info or browser autofill suggestions.
- **Page search**: Use the site's own search box. If not visible, look for a search icon or menu.
- **Internet search**: Use the address bar only if you haven't yet reached the relevant site.