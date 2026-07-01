from dataclasses import dataclass
from typing import Literal


@dataclass
class KodoSkillResult:
    result: Literal[
        "SUCCESS",
        "ERROR",
        "TIMEOUT",
        "PY_EXCEPTION",
        "PACKAGE_INSTALL_ERROR",
        "IMPORT_DISCOVERY_ERROR",
    ]
    skill_output: str
    skill_errors: str
