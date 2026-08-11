from typing import Any


class MCPAgent:
    def __init__(self, name: str, server: Any) -> None:
        self.name = name
        self.server = server

    def invoke(self, tool_name: str, *args, **kwargs) -> Any:
        return self.server.call_tool(tool_name, *args, **kwargs)
