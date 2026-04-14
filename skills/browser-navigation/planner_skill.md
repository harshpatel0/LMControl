# Browser Navigation — Planner Guide

## Skill

open_url opens the default browser to a URL in one step. Always prefer it over
manual navigation. Never assume the browser is Edge — open_url handles this by opening the default browser, or invoking a picker to choose which browser to use, just use any actual browser, if something like a text editor or mail client shows up, don't click it.

  CORRECT:  "open_url | url=https://www.youtube.com"
  FALLBACK: "Open Browser, Press Ctrl+T, press Ctrl+L, type the URL, press Enter"

## URL Navigation (manual fallback only)

If open_url is unavailable, every URL navigation requires these atomic steps:
  1. Press Ctrl+T  — open a new tab
  2. Press Ctrl+L  — focus the address bar
  3. Type [full URL] into the address bar
  4. Press Enter

Never combine these. Never type into the new tab search box.

## Tab Safety

Never navigate an existing tab unless the task explicitly requires modifying
the current page. Always open a new tab first.

## Search Flows

Split every search into atomic steps:
  1. Navigate to the site (open_url or manual)
  2. Type [query] into the [site-specific] search box
  3. Press Enter
  4. Click [specific result title or thumbnail]

The search type step must only appear AFTER the navigation step's expected_result
confirms the page is loaded.

## Type Targets

Always name the specific element:
- URL entry: "Type [url] into the address bar"
- Site search: "Type [query] into the [site name] search box"

Never use "search bar" or "address bar" without site context.

## Tab Verification

When switching tabs, expected_result must name the specific page visible:
  Bad:  "The tab is selected"
  Good: "The YouTube homepage is the active tab"

## Result Selection

When clicking a search result, target the title link or thumbnail specifically:
  Good: "Click the video title link for the first result"
  Bad:  "Click the search result for [name]"

## Page Confirmation

Any step that types into a page-level search box must be preceded by a step
whose expected_result confirms that page is loaded.

## Fallbacks

- Address bar: "Press Ctrl+L to focus the address bar"
- Site search: "Press / to focus the [site] search bar" (where supported)
- Never fall back to the address bar for a page-level search field

## Completing the Action
Lead the user to the resource directly, scenerios

If it is a YouTube Video
- Lead them directly to it

If it is a section of a webpage
- Lead them directly to it

If it is a specific item in a shop
- Lead them directly to it

Filling out forms
- Fill them out as per what the user says, or any browser autofills if you find one

Searching the page
- Search on the webpage's search box, can't find it? Must be inside a menu or a search icon visible.

Searching the internet
- Use the Address Bar / Omnibox of the page. If you have reached the relevant website to complete a task, you'll not need to touch the browsers address bar