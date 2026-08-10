from mcp_tools.framework_mcp import MCPToolRegistry
from services.config import Config

registry = MCPToolRegistry()


@registry.tool(name="get_commute_advice", description="Provide commute advice for a target location")
def get_commute_advice(location: str) -> str:
    api_key = Config.TOMTOM_API_KEY or Config.OPENROUTESERVICE_API_KEY
    if api_key and location and location.lower() != "current location":
        return f"Traffic routing is available with a configured key for {location}; plan for extra buffer time."
    if location and location.lower() != "current location":
        return f"Leave 15-20 minutes earlier for {location} traffic and plan for slower morning roads."
    return "Leave a little earlier than usual and keep an eye on weather conditions."


class CommuteTool:
    def get_commute_advice(self, location: str) -> str:
        return registry.call("get_commute_advice", location)
