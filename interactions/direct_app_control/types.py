from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DirectAppConnectionResult:
    success: bool
    message: str


@dataclass
class Process:
    pid: int
    title: str
    class_name: str

    def __str__(self) -> str:
        return f"ProcessID: {self.pid} - Title: {self.title} - ClassName: {self.class_name}"


@dataclass
class DirectAppProcessList:
    processes: list[Process] = field(default_factory=list)

    def __str__(self) -> str:
        string = ""

        for process in self.processes:
            string += f"{str(process)}\n"

        return string


@dataclass
class ProcessControl:
    control_id: str
    type: str
    name: str
    value: str
    enabled: bool

    def __str__(self) -> str:
        return f"ControlID: {self.control_id} - Type: {self.type} - Name: {self.name} - Value: {self.value} - IsEnabled: {self.enabled}"


@dataclass
class DirectAppControlListResult:
    controls: list[ProcessControl] = field(default_factory=list)
    error: str = ""

    def __str__(self) -> str:
        string = ""

        for control in self.controls:
            string += f"{str(control)}\n"

        return string


@dataclass
class DirectAppInteractionResult:
    success: bool
    method: str = ""
    message: str = ""
