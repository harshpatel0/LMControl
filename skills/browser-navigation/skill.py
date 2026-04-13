import webbrowser
import sys
import json

def open_url(url):
  webbrowser.open(url=url)

if __name__ == "__main__":
  # Args passed as JSON via environment or stdin
  args = json.loads(sys.argv[1])
  open_url(args.get("url")) 