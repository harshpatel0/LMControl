# Browser Navigation — Planner Guide

## open_url

Always prefer `open_url` over manual navigation. Never assume the browser is Edge.

```
"instruction": "open_url | url=https://www.youtube.com"
"fallback": "Press Ctrl+T, then Ctrl+L, type the URL, press Enter"
```

If open_url is unavailable, every URL navigation is exactly three atomic steps:
1. Press Ctrl+T — open a new tab
2. Press Ctrl+L — focus the address bar
3. Type [full URL] then Press Enter

## ⚠️ Expected Results for Navigation Steps

The expected_result for any step that clicks a link, video, or search result MUST describe **arrival at the destination**, not just the click.

WRONG: "The video appears in search results"
WRONG: "The video thumbnail is visible"
RIGHT: "The video's watch page is loaded and the video player is visible"

WRONG: "The link is clicked"
RIGHT: "The [page name] page is fully loaded as the active window"

This is critical: the actor will not know to click a result if the expected_result implies success before the click.

## Search Flows

Always split into atomic steps:
1. Navigate to site (`open_url`)
2. Wait for confirmation that site is loaded (expected_result of step 1)
3. Type query into the **site-specific search box** (NOT the address bar)
4. Press Enter
5. Click the specific result title or thumbnail
6. Confirm the target page/video is the active display (expected_result of step 5)

The site search step must only appear AFTER the navigation step's expected_result confirms the page is loaded.

## ⚠️ Search Target — Address Bar vs Site Search Box

- URL navigation → address bar (via Ctrl+L or open_url)
- On-site search (YouTube, Google, GitHub, etc.) → site's own search box

Never plan a step that types a search query into the address bar when the user is already on the target site.

## Type Targets

Always name the specific element:
- URL entry: "Type [url] into the address bar"
- Site search: "Type [query] into the YouTube search box"

Never write "search bar" without site context.

## Result Selection

When clicking a search result, target the title link or thumbnail specifically:

Good: "Click the video title link for the first result"
Bad:  "Click the search result"

## Tab Safety

Never navigate an existing tab unless the task requires modifying the current page. Always open a new tab first.

## Completing the Action

Lead the user directly to the resource:

- **YouTube video**: Final step must CLICK the video title/thumbnail. Final expected_result = "The video's watch page is loaded."
- **Section of a webpage**: Final step scrolls to and confirms visibility of the section.
- **Shop item**: Final step lands on the product page.
- **Form**: Fill it as per user instructions or available autofill.
- **Page search**: Use the site's own search box. If not visible, plan a step to click the search icon first.
- **Internet search**: Use address bar only before reaching the relevant site.