from typing import Any, Callable, Dict, List

from mcp_tools.tool_schema import ToolSchema


class MCPToolRegistry:
    """A lightweight decorator-based registry that mimics MCP tool exposure."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSchema] = {}

    def tool(self, name: str | None = None, description: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__
            self._tools[tool_name] = ToolSchema(
                name=tool_name,
                description=description or func.__doc__ or "No description provided.",
                function=func,
            )
            return func

        return decorator

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_tool(self, name: str) -> ToolSchema:
        return self._tools[name]

    def call(self, name: str, *args, **kwargs) -> Any:
        return self.get_tool(name).function(*args, **kwargs)

    def describe(self, name: str) -> ToolSchema:
        return self.get_tool(name)
