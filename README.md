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
