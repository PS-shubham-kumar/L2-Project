import os
from typing import Any, Callable, Dict, List


class RealMCPServer:
    """A small MCP-like server that registers tools and exposes them to agents."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        self.tools[name] = func

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def call_tool(self, name: str, *args, **kwargs) -> Any:
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found on server '{self.name}'.")
        return self.tools[name](*args, **kwargs)

    def health_check(self) -> Dict[str, Any]:
        return {"server": self.name, "tool_count": len(self.tools), "status": "ok"}
