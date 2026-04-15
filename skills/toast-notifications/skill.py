from win10toast import ToastNotifier
import sys
import json

toaster = ToastNotifier()

def show_toast(title, body, duration=4):
  toaster.show_toast(title, body, duration=duration)

if __name__ == "__main__":
  # Args passed as JSON via environment or stdin
  args = json.loads(sys.argv[1])
  show_toast(args.get("title"), args.get("body"))   