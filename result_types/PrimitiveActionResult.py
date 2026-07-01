from dataclasses import dataclass
from typing import Literal


@dataclass
class PrimitiveActionResult:
    action: dict
    command: Literal["PROCEED", "DONE", "STUCK", "REPLAN", "RETRY"] = "PROCEED"
    error_message: str = ""
