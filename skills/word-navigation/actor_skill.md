# Word for Dummies for Actors

## ⚠️ VISION-FIRST EXECUTION

Word's accessibility tree (UIA) can be inconsistent. Always prioritize the Screenshot to find the white document area if the UIA "Document" or "Edit" element is missing.

## Tactical Rules

Splash Screen Handling: Upon launch, if you see the Word "Home" gallery in the screenshot, the "Blank Document" button is usually located in the top-left quadrant. Click it to reach the typing area.

**Focus before Typing:** Before sending a type_text action, perform a click in the center of the white page area visible in the screenshot to ensure the cursor is active.

**Coordinate Guardrail:** Never send (0,0) as a coordinate. If you cannot find a target, click the center of the active Word window.

**Autonomy Mode:** If the Planner says "Type into Word" but Word is behind VS Code, you have the autonomy to click the Word Taskbar icon first.

## Recovery Protocol

**No "Edit" Element:** If the UIA tree shows no editable fields, look for the largest "Pane" or "Group" in the center and click there. Don't start typing into Search boxes or other in