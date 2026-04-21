# LMControl

LMControl allows an LLM to perform actions on your PC using Local Models. (Windows only)

## Installation

1. Clone the repo to your PC.
2. Run `pip install -r requirements.txt` to install all required packages

## Setup

1. Download Ollama
2. Pull down a model(s) you would like to use. I personally like using `gemma4:e4b`
3. Run `ollama serve` in a terminal window
4. Change the IP addresses to where the Ollama instance is hosted.
   1. Change the IP in the settings page
5. Use `orchestrator.py` to run a task.

Define the models you would like to use in the `settings.json` file.

You can also configure the model you want to use in `actor_model.py` and `planner_model.py`.

## Features

### Skills!

Skills allow you to extend LMControl's capabilities through direct Python Functions and Markdown files that provide context to the LLM on how to do a particular task.

Skills allow the actor and the planner to learn how to perform a specific task without crowding the system prompt and selectively learning only what is needed to complete it.

#### How to install a skill

1. Drag and drop the Folder into /skills

#### How to Create a Skill

1. Add a `skill.json` file to define settings for the Skills Orchestrator to use
2. Define documentation for the `actor` and the `planner` on what to do with this skill
3. Optional: Add an entry file that allows the agent to run a Python function

#### `skills.json` schema

``` json
{
  "name": "browser-navigation",
  "description": "Use when interacting with a browser",
  "actions": ["open_url"],
  "entry": "skill.py"
}
```
