import sys
import json
import time


def wait_for_element(name: str, timeout: int = 15, poll_interval: float = 0.5) -> None:
    """
    Poll the active window's UIA tree until an element whose name contains
    `name` appears, or until `timeout` seconds have elapsed.

    Prints a success confirmation to stdout, or an error to stderr on timeout.
    """
    try:
        import pywinauto
        import win32gui
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        sys.exit(1)

    deadline = time.time() + timeout
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        try:
            hwnd = win32gui.GetForegroundWindow()
            desktop = pywinauto.Desktop(backend="uia")
            window = desktop.window(handle=hwnd)

            for element in window.descendants():
                try:
                    element_name = element.window_text().strip()
                    if name.lower() in element_name.lower():
                        print(
                            f"Element found after {attempt} poll(s): '{element_name}'"
                        )
                        return
                except Exception:
                    continue

        except Exception as e:
            # Window may not be ready yet, keep polling for it
            pass

        time.sleep(poll_interval)

    print(
        f"Timed out after {timeout}s waiting for element containing '{name}'",
        file=sys.stderr,
    )
    sys.exit(1)


def wait_for_window(title: str, timeout: int = 15, poll_interval: float = 0.5) -> None:
    """
    Poll for a window whose title contains `title` to become the foreground window,
    or until `timeout` seconds have elapsed.
    """
    try:
        import pygetwindow as gw
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        sys.exit(1)

    deadline = time.time() + timeout
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        try:
            active = gw.getActiveWindow()
            if active and title.lower() in active.title.lower():
                print(f"Window found after {attempt} poll(s): '{active.title}'")
                return

            # Also check all open windows, not just the active one
            matches = gw.getWindowsWithTitle(title)
            if matches:
                print(f"Window '{matches[0].title}' detected after {attempt} poll(s)")
                return

        except Exception:
            pass

        time.sleep(poll_interval)

    print(
        f"Timed out after {timeout}s waiting for window containing '{title}'",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    action = args.get("action")

    timeout = int(args.get("timeout", 15))
    poll_interval = float(args.get("poll_interval", 0.5))

    if action == "wait_for_element":
        wait_for_element(args["element"], timeout=timeout, poll_interval=poll_interval)
    elif action == "wait_for_window":
        wait_for_window(args["title"], timeout=timeout, poll_interval=poll_interval)
    else:
        print(f"Invalid Action {action} provided", file=sys.stderr)
        sys.exit(1)
