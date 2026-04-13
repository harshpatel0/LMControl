# LMControl

LMControl allows an LLM to perform actions on your PC using Local Models. (Windows only)

## Installation

1. Download the Repo on your PC.
2. Run `pip install -r requirements.txt` to install all required packages

## Setup

1. Download Ollama
2. Pull down a model(s) you would like to use. I personally like using `gemma4:e4b`
3. Run `ollama serve` in a terminal window
4. Change the IP addresses listed in the code to `localhost` or where the Ollama instance is hosted.
   1. Change the IP in `actor_model.py`
   2. Change the IP in `planner_model.py`
5. Use `orchestrator.py` to run a task.

You can also configure the model you want to use in `actor_model.py` and `planner_model.py`.

It will get better.

## Features

### Skills!

Skills allow you to extend LMControl's capabilities through direct Python Functions, and Markdown Files detailing their usage.

Skills allow the actor and the planner to learn how to do a specific task, without crowding the system prompt. Selectively learning what it needs to be able to complete the task.

#### How to install a skill

1. Drag and Drop the Folder into /skills

#### How to Create a skill

1. Add a `skill.json` file to define settings for the Skills Orchestrator to use
2. Define documentation for the `actor` and the `planner` on what to do with this skill
3. Optional: Add a entry file that allows the agent to run a Python function

#### `skills.json` schema

``` json
{
  "name": "browser-navigation",
  "description": "Use when interacting with a browser",
  "actions": ["open_url"],
  "entry": "skill.py"
}
```
