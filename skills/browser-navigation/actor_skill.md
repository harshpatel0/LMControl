---
name: browser-navigation-actor
description: Use when executing browser navigation steps, typing URLs, or interacting with web search boxes in Microsoft Edge and Google Chrome
---

# Browser Navigation — Actor Guide

## Address Bar

The Edge address bar / Google Chrome Omnibox is only reachable after Ctrl+L. Never type a URL without
a preceding Ctrl+L step having been executed. After Ctrl+L the address bar will
be focused and ready — emit the type action immediately.

## New Tab Search Box

The Edge new tab page contains a Bing search box. This is never a valid target.
The Google new tab page contains a Google search box. This is never a valid
target.
for URL navigation. Always use the address bar via Ctrl+L.

## Site Search Boxes

When a step instructs you to type into a site-specific search box (e.g. Google
search box, YouTube search box), locate that element in the ACCESSIBILITY TREE
by name before acting. The address bar is never a substitute.

If the search element is not in the tree:

- Use the fallback from the step
- Do not fall back to the address bar on your own
- Emit scroll_v to bring the element into view if the page is loaded but the
  element is not visible

## Wrong Page Recovery

If the active window is Edge but the wrong page is loaded:

1. press_hotkey ctrl+l
2. type the correct URL into the address bar
3. press_key enter

Never declare stuck because you are on the wrong page within Edge.

## Tab Safety

Before typing a URL into the address bar, check if the active tab contains
content unrelated to the current task. If it does, press Ctrl+T first.

## open_url Action

For tasks that require navigating directly to a URL, prefer the open_url action
over manual keystroke navigation:

{"action": "open_url", "url": "https://example.com"}

This is faster and more reliable than the manual Ctrl+T → Ctrl+L → type → Enter
sequence. Only fall back to manual navigation if open_url is unavailable.
