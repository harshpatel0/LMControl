import json
import sys
from pathlib import Path
import os
import getpass

REQUEST_PERMISSION_FOR_DANGEROUS_ACTIONS = True


def parse_path(path: str) -> str:
    system_username = getpass.getuser()
    if "%USERPROFILE%" in path:
        path = path.replace("%USERPROFILE%\\", f"C:\\Users\\{system_username}")
    if "%APPDATA%" in path:
        path = path.replace(
            "%APPDATA%\\", f"C:\\Users\\{system_username}\\AppData\\Roaming"
        )
    if "%LOCALAPPDATA%" in path:
        path = path.replace(
            "%LOCALAPPDATA%\\", f"C:\\Users\\{system_username}\\AppData\\Local"
        )
    if "%DESKTOP%" in path:
        path = path.replace("%DESKTOP%\\", f"C:\\Users\\{system_username}\\Desktop")
    if "%DOWNLOADS%" in path:
        path = path.replace("%DOWNLOADS%\\", f"C:\\Users\\{system_username}\\Downloads")
    if "%PICTURES%" in path:
        path = path.replace("%PICTURES%\\", f"C:\\Users\\{system_username}\\Pictures")
    if "%VIDEOS%" in path:
        path = path.replace("%VIDEOS%\\", f"C:\\Users\\{system_username}\\Videos")
    if "%MUSIC%" in path:
        path = path.replace("%MUSIC%\\", f"C:\\Users\\{system_username}\\Music")

    return path


def request_permission(title: str, message: str) -> bool:
    if not REQUEST_PERMISSION_FOR_DANGEROUS_ACTIONS:
        return True

    import tkinter.messagebox
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    result = tkinter.messagebox.askyesno(title, message)
    root.destroy()

    if not result:
        print("The user has blocked this file operation", file=sys.__stderr__)
        return False
    return True


def create_file(path, content=None):
    file_path = Path(path)
    file_path.touch()

    if content:
        file_path.write_text(content, encoding="utf-8")
        print("Created and written")
    else:
        print("Created")


def write_to_file(path, content):
    permission = request_permission(
        "File Operation Skill",
        f"The LLM wants to write to the file: {path}, do you accept this?",
    )
    if not permission:
        return

    file_path = Path(path)
    try:
        file_path.write_text(content, encoding="utf-8")
        print("Written")
    except Exception as e:
        print(f"Could not write to file: {e}", file=sys.__stderr__)


def read_file(path):
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
        print(f"File contents\n{content}")
    except Exception as e:
        print(f"Could not read file: {e}", file=sys.__stderr__)


def append_file(path, content):
    file_path = Path(path)

    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)
            print("Appended to file successfully")
    except Exception as e:
        print(f"Could not append to file: {e}", file=sys.__stderr__)


def present_file(path):
    file_path = Path(path)
    os.startfile(file_path)

    print("Presented (opened the file with the system default app)")


def delete_file(path):
    permission = request_permission(
        "File Operation Skill",
        f"The LLM wants to delete the file: {path}, do you accept this?",
    )

    if not permission:
        print(
            f"The user denied permission for the delete action on file: {path}",
            file=sys.__stderr__,
        )
        return

    file_path = Path(path)
    file_path.unlink(missing_ok=True)

    print(f"Deleted {path} successfully")


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    action = args.get("action", None)

    if not action:
        print(
            "The action does not exist, valid ones are read_file, append_file, create_file, write_to_file, present_file, and delete_file",
            file=sys.__stderr__,
        )
        sys.exit(1)

    file_path = args.get("path")

    file_path = parse_path(file_path)
    content = args.get("content", None)

    match action:
        case "create_file":
            create_file(file_path, content)

        case "write_to_file":
            write_to_file(file_path, content)

        case "read_file":
            read_file(file_path)

        case "append_file":
            append_file(file_path, content)

        case "present_file":
            present_file(file_path)

        case "delete_file":
            delete_file(file_path)
