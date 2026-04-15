from winotify import Notification

import sys
import json

def show_toast(title, body):
  toast = Notification(app_id = "LMControl Toast Notifier Skill", title=title, msg=body)
  toast.show()

if __name__ == "__main__":
  # Args passed as JSON via environment or stdin
  args = json.loads(sys.argv[1])
  show_toast(args.get("title"), args.get("body"))   