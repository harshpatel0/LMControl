# Kodo AGENTS.md

Hey agent, I can't be asked to maintain this file, so here is what is important, you figure out the rest

Orchestrators are the ones that do the lifecycle stuff of the model. There are 2 types of orchestrators

- Autonomy Mode Orchestrator is the default one
- Planner-Actor Orchestrator Model

The Models are defined in `models/` where the corresponding file is used based on what mode it is currently running in. Where the system and user prompts are made based on the orchestrators command to the corresponding class

Then once we are done, we call run on that class to actually go and make the call.

Since multiple providers are allowed, the run command will first get the provider the user has chosen, and makes a request to it, then the raw custom ChatResponse data class is returned, which is then parsed and sent back to the orchestrator to handle it's action.

Actions are what the LLM wants to do on the PC

Orchestrators handle actions through external files, the main one is `parse_action.py` which will route the action to the correct destination.


Raw PC actions are handled internally, where the action is matched and the corresponding function in `pc_actions/perform_pc_actions.py` with the required arguments.

Skills are forwarded to the `skills/skill_orchestrator.py`

MCP Tool Calls are forwarded to the `mcps/mcp_client.py`

What they return is sent to `orchestrators/action_handlers.py` file. Which populates the orchestrator's context and history and what not.

Then we go again.

The other relevant system is Context Provider, which gets the PC's context, and for supported models, it will diff the UI tree to reduce the number of tokens used.

Thats it. The rest you can figure out.

Thanks!

Btw if you are an agent, please read CONTRIBUTING.md, and please make sure your work is readable and follows the current coding conventions.

Use Black Python formatting, and don't use 2 tab spaces if some functions do, those functions are old and the project uses 4 now because of Black formatting.

Skills are additions to Kodo, they can either just be documentation, or executable. Read the `skills/AGENTS.md`, the Skill Protocol is constant now so that is updated.
