import sys
import json
import tkinter as tk
from tkinter import simpledialog, messagebox


def prompt_user(title, body):
    """
    Display a Tkinter popup with a textbox asking the user a question.
    Returns the user's response to stdout for the LLM.

    Args:
        title: Window title
        body: Question/prompt text to display
    """
    try:
        root = tk.Tk()
        root.withdraw()

        user_response = simpledialog.askstring(title, body)

        root.destroy()

        if user_response is None:
            print("User cancelled the prompt", file=sys.stderr)
            sys.exit(1)

        print(user_response)

    except Exception as e:
        print(f"Error prompting user: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    title = args.get("title", "Kodo")
    body = args.get("body", "Enter your response:")
    prompt_user(title, body)
