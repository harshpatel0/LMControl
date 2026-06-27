from dataclasses import dataclass


@dataclass
class PCActionResult:
    action: str
    command: str = "PROCEED"
    error_message: str = ""
