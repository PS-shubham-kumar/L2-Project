from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ToolSchema:
    name: str
    description: str
    function: Callable[..., Any]
