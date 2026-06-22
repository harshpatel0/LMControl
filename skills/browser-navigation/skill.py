import os
import subprocess
import webbrowser
import sys
import json

browser = None

with open("settings.json", "r", encoding="utf-8") as settings_file:
    settings = json.load(settings_file)
    try:
        default_browser = settings["skills"]["browser-navigation"]["default_browser"]
        browser = default_browser
    except Exception:
        browser = None


def get_browser_path(browser_name):
    """Dynamically locate common browser paths on Windows."""
    paths = {
        "msedge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
    }

    # Check if any of the standard paths exist
    if browser_name in paths:
        for path in paths[browser_name]:
            if os.path.exists(path):
                return path

    return browser_name  # Fallback to the raw string if not found


def open_url(url):
    if not browser:
        webbrowser.open(url)
        print("Opened Browser Window with no special modifications")
        exit(0)

    browser_executable = get_browser_path(browser)

    try:
        if browser in ["msedge", "chrome", "chromium", "google-chrome"]:
            # If the full path wasn't found, try running via shell as a last resort
            use_shell = browser_executable == browser
            subprocess.Popen([browser_executable, f"--app={url}"], shell=use_shell)
            print("Opened Browser Window in app mode with no window decorations")

        elif browser == "firefox":
            use_shell = browser_executable == browser
            subprocess.Popen(
                [browser_executable, "--new-window", "--fullscreen", url],
                shell=use_shell,
            )
            print("Opened Firefox in fullscreen mode to avoid other window decorations")

        else:
            webbrowser.open(url)
            print("Opened Browser Window with no special modifications")

    except FileNotFoundError:
        print(f"Could not find {browser}. Falling back to default system browser.")
        webbrowser.open(url)

    exit(0)


if __name__ == "__main__":
    args = json.loads(sys.argv[1])

    open_url(args.get("url"))
