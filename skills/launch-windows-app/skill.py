import sys
import json
import os
import glob

def get_launchable_apps():
  paths = [
    os.path.join(os.environ["ProgramData"], "Microsoft", "Windows", "Start Menu", "Programs"),
    os.path.join(os.environ["AppData"], "Microsoft", "Windows", "Start Menu", "Programs")
  ]
    
  app_map = {}
  for path in paths:
    for file in glob.glob(path + "/**/*.lnk", recursive=True):
      name = os.path.basename(file).replace(".lnk", "").lower()
      app_map[name] = file
            
  return app_map

def open_app(app_name):
  if not app_name:
    print("Error: No app name.", file=sys.stderr)
  app_map = get_launchable_apps()
  target = next((path for name, path in app_map.items() if name.lower() == app_name.lower()), None)
  
  if target:
    os.startfile(target)
    print(f"Launched {app_name}")
  print(f"App {app_name} not found.", file=sys.stderr)

def get_list_of_installed_apps():
  return get_launchable_apps().keys()

def generate_context():
  app_map = get_launchable_apps()
  apps = list(app_map.keys())
  apps_str = ", ".join(apps)

  context = {
    "planner": f"""
## App Launcher — Strategic Guide
### Capability
You can bypass manual UI navigation by launching apps directly
Use this to move the task forward instantly.
### Available Apps on this PC:
{apps_str}

### Planning Rules
1. **Validation**: Only plan to open apps listed above. If an app isn't listed, search the web instead.
2. **State Transition**: A launch step is only 'Done' when the app is confirmed as the active window.
3. **Avoid the Trap**: Never plan a step to 'Click the Start Menu' if the app is in the list above.
    """,
    "actor": f"""
## App Launcher — Tactical Guide

### ⚠️ AUTONOMY MODE
If the Planner requests an app name that is slightly different from the grid below
(e.g., 'Chrome' vs 'Google Chrome'), use your autonomy to select the correct match.
### Installed Apps:
[{apps_str}]
### Execution Action
```json
{{"action": "open_app", "app": "name"}}
```
### Recovery Protocol
- If `open_app` fails: Do NOT retry. Check if the app is already running in the Taskbar.
- If multiple versions exist: Default to the one that matches the Planner's intent.
  """
  }
  print(json.dumps(context))
  sys.exit(0)

if __name__ == "__main__":
  if '--generate' in sys.argv:
    generate_context()
    
  args = json.loads(sys.argv[1])
  print(open_app(args.get("app")))