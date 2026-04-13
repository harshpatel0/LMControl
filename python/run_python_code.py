import ast
import subprocess
import sys
import os
import tempfile
import venv
import json

VENV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".lmcontrol_venv")

class PythonRunner:

  def __init__(self):
    self.venv_dir = VENV_DIR
    self.venv_python = self._get_venv_python()
    self._ensure_venv()

  def _get_venv_python(self):
    platform = sys.platform

    if platform == "win32":
      return os.path.join(self.venv_dir, "Scripts", "python.exe")
    else:
      return os.path.join(self.venv_dir, "bin", "python")

  def _ensure_venv(self):
    if not os.path.exists(self.venv_python):
      print(f"[PythonRunner] Creating venv at {self.venv_dir}...")
      venv.create(self.venv_dir, with_pip=True)
      print(f"[PythonRunner] Venv created.")

  def _extract_imports(self, code):
    """Returns a list of top-level module names imported by the code."""
    try:
      tree = ast.parse(code)
    except SyntaxError as e:
      return None, f"Syntax error in code: {e}"
    
    imports = set()
    for node in ast.walk(tree):
      if isinstance(node, ast.Import):
        for alias in node.names:
          imports.add(alias.name.split(".")[0])
      elif isinstance(node, ast.ImportFrom):
        if node.module:
          imports.add(node.module.split(".")[0])
  
    return imports, None

  def _install_packages(self, packages):
    """Installs packages into the venv. Skips stdlib modules."""
    stdlib_modules = sys.stdlib_module_names
    to_install = [package for package in packages if package not in stdlib_modules]
    
    if not to_install:
      return None
    
    print(f"[PythonRunner] Installing: {to_install}")
    result = subprocess.run(
      [self.venv_python, "-m", "pip", "install", *to_install],
      capture_output=True,
      text=True,
      timeout=60
    )
    
    if result.returncode != 0:
      return {
        "result": "NOT_RUN",
        "message": "Could not install packages from Pip into venv"
      }
    
    return None
  
  def run_skill_by_path(self, entry_path, args=None):
    with open(entry_path, 'r') as file:
      skill_code = file.read()
    
    imports, error = self._extract_imports(skill_code)
    if error:
      return {"result": "SYNTAX_ERROR", "stderr": error, "stdout": ""}
    
    install_error = self._install_packages(imports)
    if install_error:
      return install_error
  
    cmd = [self.venv_python, entry_path]

    if args:
      cmd.append(json.dumps(args))

    try:
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

      output = result.stdout.strip()
      errors = result.stderr.strip()

      print(f"Output: {output}")
      print(f"Errors: {errors}")

      if errors:
        return {"result": "ERRORS", "stderr": errors, "stdout": output}
      
      return {"result": "SUCCESS", "stderr": "", "stdout": output}
    
    except subprocess.TimeoutExpired:
      return {"result": "TIMEOUT", "stderr": "Skill timed out", "stdout": ""}
    
    except Exception as e:
      return {"result": "PY_EXCEPTION", "stderr": str(e), "stdout": ""}
    
  def run(self, code, timeout=15):
    print(f"Running Python code\n{code}")
    # Step 1 - parse imports
    imports, error = self._extract_imports(code)
    if error:
      return f"[PythonRunner] {error}"

    # Step 2 - install missing packages
    install_error = self._install_packages(imports)
    if install_error:
      return f"[PythonRunner] {install_error}"

    # Step 3 - write to temp file and run
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
      f.write(code)
      temp_path = f.name

    try:
      result = subprocess.run(
        [self.venv_python, temp_path],
        capture_output=True,
        text=True,
        timeout=timeout
      )
      output = result.stdout.strip()
      errors = result.stderr.strip()

      print(f"Output: {output}")
      print(f"Errors: {errors}")

      if errors:
        print(f"[PythonRunner] stderr: {errors}\nstdout: {output}")
        result = "ERRORS"
      else:
        result = "SUCCESS"
      print("[PythonRunner] Code ran successfully with no output.")

      return {
        "result": result,
        "stderr": errors,
        "stdout": output
      }
    
    except subprocess.TimeoutExpired:
      return {
        "result": "TIMEOUT",
        "stderr": errors,
        "stdout": output
      }
    
    except Exception as e:
      return {
        "result": "PY_EXCEPTION",
        "stderr": str(e),
        "stdout": output
      }
    
    finally:
      os.unlink(temp_path)

if __name__ == "__main__":
  pyrun = PythonRunner()
  pyrun.run("""
import webbrowser
webbrowser.open("google.com")
""")