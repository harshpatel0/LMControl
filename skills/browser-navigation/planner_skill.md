---
name: browser-navigation-planner
description: Use when the task involves opening a browser, navigating to a URL, or performing searches on the web. Provides correct step sequencing for browser navigation.
---

# Browser Navigation — Planner Guide

## URL Navigation Sequence

Every URL navigation must follow this exact four-step sequence. No steps may be
combined or skipped:

1. Press Ctrl+T        — opens a new tab
2. Press Ctrl+L        — focuses the address bar  
3. Type [full URL] into the address bar
4. Press Enter

## New Tab Behaviour

After Ctrl+T, the new tab page shows a Bing search box. This must be ignored.
Ctrl+L must always follow Ctrl+T before any typing. Never type a URL into the
Bing search box.

## Search Flows

Split every search into three atomic steps:

1. Type [query] into the [site-specific] search box
2. Press Enter
3. Click [specific result]

The search type step must only appear AFTER the preceding navigation step's
expected_result confirms the page is loaded. Never plan a search box interaction
before the page is confirmed open.

## Type Targets

Every type step must name the specific UI element:

- URL navigation: "Type [url] into the address bar"
- Site search: "Type [query] into the [site name] search box"

Never use generic names like "search bar" or "address bar" without the site context.

## Tab Safety

Never navigate an existing tab unless the task explicitly says to modify the
current page. Always open a new tab with Ctrl+T first.

## Page Confirmation

Any step that types into a page-level search box must be preceded by a navigation
step whose expected_result confirms that page is loaded.

## Fallbacks

- Address bar fallback: "Press Ctrl+L to focus the address bar"
- Search box fallback: "Press / to focus the [site] search bar" (where supported)
- Never fall back to the address bar for a page-level search field

## Skill

The skill allows you to open the default web browser on the PC pointing to a specific url.
The actor has the ability to use this skill and use it, unless the manual method fails.

## Assumptions

Never assume the user is an Edge user, you will be wrong about 86 percent of the time.
You don't need to care what browser it is unless you need to do it manually.
open_url skill OPENS THE DEFAULT BROWSER!
