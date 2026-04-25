# 🧠 Microsoft Word Strategic Planning Guide (Planner)

## 1. Structural Integrity & Flow
* **The Newline Mandate:** You MUST explicitly plan for line breaks. Never assume the Actor will start a new line. Every new paragraph or header must be preceded by a "New Line" instruction in the plan.
* **Anchor-Point Planning:** Before any typing task, plan a "Reset Cursor" sub-step (e.g., `ctrl + end`). This prevents the model from accidentally editing the middle of the document and creating "Hallucination Soup."
* **Phase Segregation:** Separate 'Drafting' from 'Formatting'.
    * Phase A: Type raw text (headers, paragraphs).
    * Phase B: Navigate back to headers to apply bolding/sizes.

## 2. Visual State Verification
* **Word Count Monitoring:** Use the 'Word Count' element in the status bar to verify progress. If the word count doesn't increase after a 'Type' action, the action failed (likely hijacked by a menu).
* **The Mini-Toolbar Alert:** If the UIA tree shows formatting buttons (Bold, Italic) during a typing phase, the plan must immediately pivot to a "Deselection" step (Escape/Right Arrow).

## 3. Advanced Editing Strategies
* **Search-Based Navigation:** Do not plan to click on specific lines for editing. Instead, plan to use 'Find' (`ctrl + f`) to anchor the cursor to specific text strings for precise modification.
* **Sectional Drafting:** For long reports, plan to write one section at a time. After each section, plan a "Visual Audit" to ensure the text isn't repeated or garbled.

## 4. Anti-Looping Protocols
* **Repetition Detection:** If the UIA tree reveals the same sentence twice (e.g., "indelible mark on history"), the current plan is compromised. 
* **The Nuclear Option:** Plan a "Reset and Rewrite" (Select All + Delete) if the document becomes corrupted by "Inline Drift" (text typing over text).