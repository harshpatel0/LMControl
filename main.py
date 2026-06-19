import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from utils.globals import API_BIND_TO_ALL_IPS, API_PORT

HOST = "127.0.0.1"
if API_BIND_TO_ALL_IPS:
    HOST = "0.0.0.0"


def _venv_python() -> Path:
    return Path("venv") / "Scripts" / "python.exe"


def _run_under_venv():
    venv_python = _venv_python()
    if not venv_python.exists():
        return False
    if os.path.abspath(sys.executable) == os.path.abspath(str(venv_python)):
        return False

    sys.exit(subprocess.call([str(venv_python)] + sys.argv))


def _open_browser_delayed(url: str, delay: float = 3.5):
    def _open():
        time.sleep(delay)
        webbrowser.open_new(url)

    threading.Thread(target=_open, daemon=True).start()


if __name__ == "__main__":
    if not Path("initialised.txt").exists():
        from setup import KodoSetup

        setup = KodoSetup()
        setup.check_system_compatibility()
        setup.run_setup_sequence()

    _run_under_venv()

    import uvicorn

    _open_browser_delayed(f"http://127.0.0.1:{API_PORT}")
    uvicorn.run("server.api:app", host=HOST, port=API_PORT, reload=False)
