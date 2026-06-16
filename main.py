import os
import subprocess
import sys
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
    return True


if __name__ == "__main__":
    if not Path("initialised.txt").exists():
        from setup import KodoSetup

        KodoSetup().run_setup_sequence()

    _run_under_venv()

    import uvicorn
    import webbrowser

    webbrowser.open_new(f"http://127.0.0.1:{API_PORT}")
    uvicorn.run("server.api:app", host=HOST, port=API_PORT, reload=False)
