from dataclasses import dataclass


@dataclass
class MCPActionResult:
    tool_name: str
    output: str
    is_error: bool
