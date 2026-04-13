# Python Engine — Actor Guide

The run_python Action

When executing Python code, ensure the code is concise and utilizes standard libraries unless specified.
Format: {"action": "python", "code": "import os; ..."}

## Usage

When the user wants to run Python code
The task will be better served if a Python code did it
The step will be better when executed by Python

! Python action is internally defined, meaning you can be rest assured it exists. Do not worry about it not being assigned to an action. The above example will still work. Python functionality is hard coded into the app, just the instructions are split up.
Always prioritise the use of skills!
