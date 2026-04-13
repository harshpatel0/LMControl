# Python Engine — Planner Guide

Strategic Usage
Prefer the run_python action over manual UI exploration for:

Validation: Checking if a task was successful (e.g., "Verify the file was saved").

System State: Checking active processes, volume levels, or battery status.

Data Handling: Formatting text, calculating values, or parsing strings.

## Step Sequencing

When using Python for validation, follow the Action-Verify flow:

Step N: Perform the UI action (e.g., "Save the document").

Step N+1: Use run_python to verify the state (e.g., "Run script to check if file.docx exists in /Documents").

Instruction Clarity
Your instructions for Python steps must include the logic required:

Bad: "Run a python script."

Good: "python | code=import os; print(os.path.exists('path/to/file'))"

## Expected Results

The expected_result for a Python step should define the successful output of the script (e.g., "The script returns True" or "The process list includes 'vlc.exe'").

! Python action is internally defined, meaning you can be rest assured it exists. Do not worry about it not being assigned to an action. The above example will still work. Python functionality is hard coded into the app, just the instructions are split up.
Always prioritise the use of skills!
