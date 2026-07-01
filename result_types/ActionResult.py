from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ActionResult:
    signal: Literal["CONTINUE", "BREAK"]
    step_count: int | None = None
    iterations: int | None = None
    replan_history: list[str] | None = None
    additional_context: str | None = None
    hard_exit: bool | None = None
    temp_task: str | None = None
    result: Any = None
