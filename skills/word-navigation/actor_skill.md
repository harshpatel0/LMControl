## Task Completion Requirements

Working in Word requires three phases in order. You may not emit `done` until all three are complete:

**Phase 1 — Write.** Type all content in full before touching any formatting controls. The document must contain the complete text.

**Phase 2 — Format.** Apply heading styles using the procedure in this skill. Do not skip this — an unformatted document is not a complete document.

**Phase 3 — Save.** Save the file via the File menu. Verify the title bar shows the saved filename, not a generic name like `Document1`. An unsaved document is not a complete document.

**Do not use markdown syntax.** Word renders text literally — `#`, `##`, `**text**`, and `*text*` will appear as raw characters. Write plain prose and apply structure through Word's own formatting tools.

---

# Microsoft Word — Actor Skill

## Opening or Creating a Document

Word opens to a Start screen, not a blank document. You must explicitly open or create a document before typing anything.

**New document:** Click `Blank document` on the Start screen. If Word is already open, use `ctrl + n`.

**Existing document:** Click `Open` on the Start screen or use `ctrl + o`, then navigate to the file.

Before doing anything else, confirm the UIA tree contains `Edit | name='Page 1 content'`. If it does not, you are still on the Start screen — do not type until this node is present.

**Gotcha — Ctrl+N focus:** After `ctrl + n`, focus may not land on the document body automatically. If `Edit | name='Page 1 content'` is absent, click the center of the document area before typing.

---

## Typing Content

Always press `ctrl + end` before typing to anchor the cursor at the end of the document. This prevents content landing in the middle of existing text.

**Line breaks:**
- `\n` — single line break
- `\n\n` — new paragraph

Use `\n\n` between every paragraph and section. Never use spaces or tabs for visual separation.

**Write all content in one pass before applying any formatting.** Do not stop mid-document to apply heading styles — finish the entire document first, then format.

**Gotcha — Cursor position unknown:** If you have not explicitly moved the cursor with `ctrl + end`, you do not know where it is. Any text you type may land in the middle of existing content. Always anchor first.

**Gotcha — Autocorrect:** Word silently transforms certain character sequences as you type — `--` becomes an em dash, `(c)` becomes ©, sentence starts get auto-capitalised. If unexpected characters appear in the tree, press `ctrl + z` once immediately to undo just the autocorrect without losing the rest of the text.

**Gotcha — Auto list trigger:** If a line starts with `1.` or `-`, Word may automatically switch into list mode and begin numbering subsequent lines. If this happens, press `ctrl + z` once to remove the list formatting. The text is preserved.

**Gotcha — Mini toolbar selection trap:** If text becomes selected, Word shows a floating toolbar. Typing while this toolbar is visible sends keystrokes into the Font Search Box instead of the document — the document appears unchanged but input is lost. If the UIA tree shows `Bold`, `Italic`, or `Font Color` near your cursor coordinates, press `right` to dismiss the selection before typing.

**Gotcha — Duplicate content:** If the same sentence or idea appears twice, do not attempt to delete mid-paragraph. Press `ctrl + a` then `backspace` to clear the document, then re-anchor with `ctrl + end` and retype cleanly.

**Gotcha — UIA tree truncation:** The UIA tree truncates long text nodes. After typing a large block, scroll to verify the end of the content looks correct before continuing. Do not assume the full text landed correctly based on the truncated preview alone.

---

## Applying Heading Styles

Only apply heading styles after all content is written. Use the Apply Styles dialog (`ctrl + shift + s`) — do not use the ribbon, do not click the styles panel.

**The Apply Styles dialog** is a small floating box with a dropdown field showing the current style name. You type the style name into this field and confirm it to apply the style to the current line.

**Full sequence to apply a heading style to a line:**
1. Use `ctrl + f` to find the heading text, press `enter`, then `esc`. The cursor is now on that line.
2. Press `ctrl + shift + s` to open the Apply Styles dialog. The UIA tree will show a `ComboBox` or `Edit` field — this is the style name input.
3. Clear the current value in the field using `ctrl + a`, then type the exact style name:
   - `Heading 1`
   - `Heading 2`
   - `Heading 3`
4. Press `enter` to apply. The dialog stays open — do not close it manually.
5. Re-read the UIA tree to confirm the style was applied to the correct line before moving to the next heading.
6. Repeat from step 1 for the next heading. The dialog will still be open so you only need to clear the field and type the new style name.

**Available default styles:** Normal, No Spacing, Heading 1, Heading 2, Heading 3, Title, Subtitle, Default Paragraph Font. Type the name exactly as shown — capitalisation matters.

**Gotcha — Dialog not opening:** If `ctrl + shift + s` has no effect, the document body has lost focus. Click the center of the document body, verify `Edit | name='Page 1 content'` is present in the UIA tree, then try again.

**Gotcha — Style field not clearing:** If the existing style name does not clear with `ctrl + a`, click directly on the ComboBox field in the UIA tree first to ensure it is focused, then try `ctrl + a` again.

**Gotcha — Style applied to wrong line:** The style applies to whichever line the cursor is currently on. Always use `ctrl + f` to position the cursor precisely before opening the Apply Styles dialog.

**Gotcha — Find wraps around:** Word's `ctrl + f` wraps from the end of the document back to the beginning. If the cursor jumps to an unexpected position, Find wrapped. Press `ctrl + home` to reorient and search again.

**Gotcha — Coordinate shift after styling:** Applying a heading style shifts the `y` coordinates of all content below it. Do not rely on previously noted coordinates after a style has been applied. Always re-read the tree.

---

## Saving

Save through the File menu, not `ctrl + s`. The File menu exposes a full UIA tree which makes navigation reliable.

**Sequence:**
1. Click `Button | name='File Tab'` — this is visible in the UIA tree at the top left of the ribbon.
2. The File menu opens. Look for `Save` or `Save As` in the UIA tree and click the appropriate one.
3. If saving for the first time, `Save` will open a Save As dialog. The UIA tree will show location options, a filename field, and a `Button | name='Save'`. Fill in the filename if needed and click Save.
4. After saving, Word returns to the document. Verify the title bar no longer shows an unsaved indicator.

**Gotcha — Save vs Save As:** If the document has been saved before, clicking `Save` in the File menu saves silently and returns to the document. If it has never been saved, it opens the Save As dialog regardless of which option you click.

**Gotcha — Save As dialog location:** The Save As dialog may default to OneDrive. If a local save is required, navigate to the desired folder using the location options in the UIA tree before clicking Save.

**Gotcha — File menu does not close automatically:** After saving, the File menu may remain open. If the document body is not visible, press `esc` to return to the document.

## Applying Heading Styles (Revised — Deterministic Pass)

Formatting must be performed as a **top-down correction pass**, not ad hoc.

Before applying any styles, you must reset your position to the start of the document.

**Mandatory start anchor:**
- Press `ctrl + home` to move the cursor to the very beginning of the document.
- Confirm via the UIA tree that you are at the top (first lines visible).

Do not begin formatting unless this step has been completed.

---

### Formatting Hierarchy (Strict Order)

You must apply styles in the following order of precedence:

1. `Title` — for the main document title (only once, at the very top)
2. `Heading 1` — major sections
3. `Heading 2` — subsections
4. `Heading 3` — sub-subsections

The title must always be styled first before any headings.

---

### Formatting Strategy

You must treat formatting as a **systematic sweep from top to bottom**, correcting and applying styles as you go.

- Always locate text using `ctrl + f`
- Always ensure the cursor is positioned on the correct line before applying a style
- After each style application, re-read the UIA tree to confirm correctness
- Progress logically from the top of the document downward

---

### Strict Procedure (per heading or title)

1. Press `ctrl + f` and search for the exact text  
2. Press `enter`, then `esc` to move the cursor to that occurrence  
3. Verify via UIA tree that the cursor is on the correct line  
4. Press `ctrl + shift + s` to open Apply Styles  
5. Clear the field (`ctrl + a`) and type the correct style:
   - `Title`
   - `Heading 1`
   - `Heading 2`
   - `Heading 3`
6. Press `enter` to apply  
7. Re-read the UIA tree to confirm the style was applied correctly  

---

### Bullet Point Handling

Word automatically continues bullet lists once initiated. You must not manually type dashes (`-`) or recreate bullets for each line.

**Rules:**
- Only the first bullet in a list should trigger bullet formatting
- Subsequent bullet points must be created by pressing `enter`, not by typing `-`
- If dashes (`-`) were typed during writing:
  - Remove them
  - Convert the list into proper Word bullet formatting

**Correction behavior:**
- If a list is incorrectly formatted as plain text with dashes:
  - Convert it into a proper bullet list
- If bullet formatting is accidentally triggered mid-paragraph:
  - Undo with `ctrl + z`

---

### Correction Requirement

While formatting, you must also act as a **correction pass**:

- If a title is missing or not at the top:
  - Move or correct it before applying `Title`
- If a heading is missing, malformed, or duplicated:
  - Correct it before applying the style
- If text structure is inconsistent (e.g., missing paragraph breaks):
  - Fix it before continuing
- If bullet points are incorrectly written:
  - Normalize them into proper Word lists
- If formatting is applied to the wrong line:
  - Immediately correct it before proceeding

Do not defer corrections. Fix issues at the moment they are detected.

---

### Ordering Constraint

You must process elements in logical document order:

1. Title (top of document)
2. All Heading 1
3. All Heading 2
4. All Heading 3

If using Find:

- Be aware that Find wraps around the document

- If unexpected jumps occur:
  - Press `ctrl + home` and restart the search

---

### Stability Rules

- After applying a style, UI layout may shift — always re-check positions
- Never assume previous coordinates are still valid
- Always verify using the UIA tree before continuing