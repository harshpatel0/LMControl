import os
import json
import rootutils

root = rootutils.setup_root(__file__, pythonpath=True)

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SKILLS_DIR)
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".lmcontrol_venv", "Scripts", "python.exe")

from python.run_python_code import PythonRunner

class Skills:
  _dispatch = {}
  _runner = PythonRunner()

  installed_skills = []
  _skills = {}

  def get_skill_doc(self, skill, consumer):
    """Gets the skill document for either `consumer`: planner | actor"""

    if not self.has_skill(skill):
      print(f"[SkillOrchestrator] Skill '{skill}' not found")
      return None

    consumer = consumer.lower()
    filename = f"{consumer}_skill.md"
    skill_path = self._skills[skill]["path"]
    doc_path = os.path.join(skill_path, filename)

    if not os.path.exists(doc_path):
      print(f"[SkillOrchestrator] No {filename} found for skill '{skill}'")
      return None

    with open(doc_path, encoding='utf-8') as skill_file:
      return skill_file.read()

  def load_all_requested_skills(self, skills, consumer):
    """Loads all requested skills for a particular consumer"""
    loaded_skills = []
    for skill in skills:
      print(f"[SKILL_ORCHESTRATOR] Installing Skill {skill}")
      skill_content = self.get_skill_doc(skill, consumer)
      
      if skill_content is None:
          continue
      
      loaded_skills.append(f"## Skill: {skill}\n{skill_content}")

    return "\n\n".join(loaded_skills) if loaded_skills else None


  def _discover(self):
    for skill_folder in os.listdir(SKILLS_DIR):
      skill_path = os.path.join(SKILLS_DIR, skill_folder)

      if not os.path.isdir(skill_path):
        continue

      skill_json = os.path.join(skill_path, "skill.json")
      
      skill_entry = {
        "name": skill_folder,
        "path": skill_path,
        "executable": False,
        "actions": [],
        "description": None,
        "has_planner_skill": os.path.exists(os.path.join(skill_path, "PLANNER_SKILL.md")),
        "has_actor_skill": os.path.exists(os.path.join(skill_path, "ACTOR_SKILL.md")),
      }

      if os.path.exists(skill_json):
        try:
          with open(skill_json) as f:
            definition = json.load(f)

          if not definition.get("enabled", True):
            continue

          entry = os.path.join(skill_path, definition["entry"])

          if not os.path.exists(entry):
            print(f"[SkillOrchestrator] Warning: entry '{entry}' not found for skill '{skill_folder}', skipping executable.")
          else:
            skill_entry["executable"] = True
            skill_entry["actions"] = definition.get("actions", [])
            skill_entry["description"] = definition.get("description")

            for action in definition.get("actions", []):
              self._dispatch[action] = entry
              print(f"[SkillOrchestrator] Registered action '{action}' → {skill_folder}")

        except Exception as e:
          print(f"[SkillOrchestrator] Failed to load skill.json for '{skill_folder}': {e}")

      self._skills[skill_folder] = skill_entry

  def get_available_skills(self):
    """Returns skill metadata for all discovered skills. Used to inform the LLM."""
    return list(self._skills.values())

  def get_skills_summary(self):
    """Returns a compact string summary suitable for injecting into a prompt."""
    lines = []
    for skill in self._skills.values():
      status = []
      if skill["executable"]:
        status.append(f"actions: {', '.join(skill['actions'])}")
      if skill["has_planner_skill"]:
        status.append("planner guide")
      if skill["has_actor_skill"]:
        status.append("actor guide")
      desc = f" — {skill['description']}" if skill["description"] else ""
      lines.append(f"- {skill['name']}{desc} [{', '.join(status)}]")
    return "\n".join(lines)

  def can_handle(self, action_name):
    return action_name in self._dispatch
  
  def has_skill(self, skill_name):
    return skill_name in self._skills

  def execute(self, action):
    action_name = action.get("action")
    entry = self._dispatch.get(action_name)
    
    if not entry:
      return f"[SkillOrchestrator] No skill registered for action '{action_name}'"
    
    # Pass everything except 'action' key as args
    args = {k: v for k, v in action.items() if k != "action"}
    
    return self._runner.run_skill_by_path(entry, args)

  def list_actions(self):
    return list(self._dispatch.keys())
  
  def __init__(self):
    self._discover()

if __name__ == "__main__":
  skills = Skills()
  print(skills.list_actions())
  print(skills.get_skills_summary())
  print(skills.get_available_skills())
  print(skills.can_handle('open_url'))