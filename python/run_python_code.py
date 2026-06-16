import ast
import subprocess
import sys
import os
import tempfile
import venv
import json

from utils.globals import PYTHON_RUNNER_VENV_NAME

VENV_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), PYTHON_RUNNER_VENV_NAME
)

from utils.logger import logger


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
            logger.info(f"Creating venv at {self.venv_dir}...")
            venv.create(self.venv_dir, with_pip=True)
            logger.info(f"Virtual Environment created.")

    def _extract_imports(self, code):
        """Returns a list of top-level module names imported by the code."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return None, f"Syntax error in code: {e}"

        imports = set()
        imports.add("setuptools")
        imports.add("wheel")

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

        logger.info(f"Installing: {to_install}")
        result = subprocess.run(
            [self.venv_python, "-m", "pip", "install", *to_install],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            if (
                "Could not find a version that satisfies the requirement"
                not in result.stderr
            ):
                return {
                    "result": "NOT_RUN",
                    "message": "Could not install packages from Pip into venv",
                }
            # If a dependency could not be found ignore it, as it could be a dependency that has a different name, dependencies like that should be defined in skill.json

        return None

    def prepare_environment(self, code):
        imports, error = self._extract_imports(code)
        if error:
            return {"result": "IMPORT_DISCOVERY_ERROR", "stderr": error, "stdout": ""}

        install_error = self._install_packages(imports)
        if install_error:
            return {
                "result": "PACKAGE_INSTALL_ERROR",
                "stderr": install_error,
                "stdout": "",
            }

        return None

    def execute_code(self, command, timeout=15):
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout
            )
            output = result.stdout.strip()
            errors = result.stderr.strip()

            logger.info(f"Output: {output}")
            logger.warning(f"Errors: {errors}")

            if errors:
                logger.warning(f"stderr: {errors}\nstdout: {output}")
                result = "ERROR"
            else:
                result = "SUCCESS"
            logger.info("Code ran successfully with no output.")

            return {"result": result, "stderr": errors, "stdout": output}

        except subprocess.TimeoutExpired:
            return {"result": "TIMEOUT", "stderr": errors, "stdout": output}

        except Exception as e:
            return {"result": "PY_EXCEPTION", "stderr": str(e), "stdout": output}

    def run_skill_by_path(self, entry_path, args=None):
        with open(entry_path, "r", encoding="utf-8") as file:
            skill_code = file.read()

        preparation_result = self.prepare_environment(skill_code)

        if preparation_result:
            return preparation_result

        command = [self.venv_python, entry_path]

        if args:
            command.append(json.dumps(args))

        execution_result = self.execute_code(command)
        return execution_result

    def run_skill_context_generator(self, entry_path):
        with open(entry_path, "r", encoding="utf-8") as file:
            skill_code = file.read()

        preparation_result = self.prepare_environment(skill_code)

        if preparation_result:
            return preparation_result

        command = [self.venv_python, entry_path, "--generate"]
        execution_result = self.execute_code(command)

        return execution_result["stdout"]

    def _extract_imports_fallback(self, code):
        """Regex-based import extraction when ast.parse fails."""
        import re

        imports = set()
        imports.add("setuptools")
        imports.add("wheel")
        for match in re.finditer(r"^\s*import\s+(\w+)", code, re.MULTILINE):
            imports.add(match.group(1).split(".")[0])
        for match in re.finditer(r"^\s*from\s+(\w+)", code, re.MULTILINE):
            imports.add(match.group(1).split(".")[0])
        return imports

    def run(self, code, timeout=15):
        logger.info(f"Running Python code\n{code}")

        # Write code to temp file first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        # Try extracting imports (ast with regex fallback)
        imports, error = self._extract_imports(code)
        if error:
            imports = self._extract_imports_fallback(code)

        # Install packages if any imports were found
        if imports:
            install_error = self._install_packages(imports)
            if install_error:
                os.unlink(temp_path)
                return install_error

        # Run the temp file, actual Python errors come through clearly here
        command = [self.venv_python, temp_path]
        execution_result = self.execute_code(command=command)
        os.unlink(temp_path)

        return execution_result


if __name__ == "__main__":
    pyrun = PythonRunner()
    pyrun.run("""
import webbrowser
webbrowser.open("google.com")
""")
