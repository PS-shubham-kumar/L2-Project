from __future__ import annotations

from typing import List

from nlp.query_parser import QueryParser
from agents.weather_agent import WeatherAgent
from agents.news_agent import NewsAgent
from agents.breakfast_agent import BreakfastAgent
from agents.commute_agent import CommuteAgent
from agents.agent_registry import AgentRegistry
from agents.router import Router
from mcp_tools.real_mcp_server import RealMCPServer
from mcp_tools.server_registry import ServerRegistry
from mcp_tools.tool_registry import ToolRegistry
from services.session_manager import SessionManager


class OrchestratorAgent:
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.parser = QueryParser()
        self.session_manager = session_manager or SessionManager()
        self.weather_agent = WeatherAgent()
        self.news_agent = NewsAgent()
        self.breakfast_agent = BreakfastAgent()
        self.commute_agent = CommuteAgent()
        self.router = Router()
        self.tool_registry = ToolRegistry()
        self.tool_registry.register("weather", self.weather_agent.tool)
        self.tool_registry.register("news", self.news_agent.tool)
        self.tool_registry.register("recipe", self.breakfast_agent.tool)
        self.tool_registry.register("commute", self.commute_agent.tool)

        self.agent_registry = AgentRegistry()
        self.agent_registry.register("weather", self.weather_agent)
        self.agent_registry.register("news", self.news_agent)
        self.agent_registry.register("breakfast", self.breakfast_agent)
        self.agent_registry.register("commute", self.commute_agent)

        # ── MCP Server Registry ────────────────────────────────────────────
        # Each domain has its own RealMCPServer exposing the canonical tool
        # from that domain's MCP module. The orchestrator calls agents directly;
        # these server objects enable external MCP tool discovery / inspection.
        self.server_registry = ServerRegistry()

        self.weather_server = RealMCPServer("weather-server")
        self.news_server = RealMCPServer("news-server")
        self.recipe_server = RealMCPServer("recipe-server")
        self.commute_server = RealMCPServer("commute-server")

        self.weather_server.register_tool("get_weather", self.weather_agent.tool.get_weather)
        self.news_server.register_tool("get_headlines", self.news_agent.tool.get_headlines)
        self.recipe_server.register_tool("get_recipe", self.breakfast_agent.tool.get_recipe)
        # Register the full routing tool (not the legacy advice shim)
        self.commute_server.register_tool("get_commute_route", self.commute_agent.tool.get_commute_route)

        self.server_registry.register("weather", self.weather_server)
        self.server_registry.register("news", self.news_server)
        self.server_registry.register("recipe", self.recipe_server)
        self.server_registry.register("commute", self.commute_server)

    # ------------------------------------------------------------------
    # Original plain-text run — preserved so CLI and existing tests work
    # ------------------------------------------------------------------
    def run(self, query: str, session_id: str | None = None) -> str:
        parsed = self.parser.parse(query)
        sections = parsed["sections"]
        location = parsed["location"]
        destination = parsed.get("destination", "")
        ingredients = parsed["ingredients"]
        time_constraint = parsed["time_constraint"]

        sections_output: List[str] = []
        routed_agents = self.router.route(sections)

        if "weather" in routed_agents:
            sections_output.append(self.weather_agent.run(location))
        if "news" in routed_agents:
            sections_output.append(self.news_agent.run())
        if "breakfast" in routed_agents:
            sections_output.append(self.breakfast_agent.run(ingredients, time_constraint))
        if "commute" in routed_agents:
            sections_output.append(self.commute_agent.run(location))

        if not sections_output:
            return "No matching sections were found. Try a request like: weather, news, commute, or breakfast."

        response = "\n\n".join(sections_output)
        if session_id:
            self.session_manager.log_interaction(session_id, {"query": query, "response": response})
        return response

    # ------------------------------------------------------------------
    # Structured run — used by the web UI for per-card JSON rendering
    # ------------------------------------------------------------------
    def run_structured(self, query: str, session_id: str | None = None) -> dict:
        """Parse the query and call each requested agent's run_structured().

        Returns::

            {
                "session_id": "...",
                "intent": {
                    "location":        str,
                    "destination":     str,   # extracted commute destination
                    "sections":        list,
                    "ingredients":     list,
                    "time_constraint": str,
                },
                "sections": {
                    "weather":   { section, status, data } | { section, status, error },
                    "news":      ...,
                    "commute":   ...,
                    "breakfast": ...,
                }
            }
        """
        parsed = self.parser.parse(query)
        location: str        = parsed.get("location", "")
        destination: str     = parsed.get("destination", "")   # ← extracted destination
        sections: list       = parsed.get("sections", [])
        ingredients: list    = parsed.get("ingredients", [])
        time_constraint      = parsed.get("time_constraint", "10 min")

        routed_agents = self.router.route(sections)
        results: dict = {}

        if "weather" in routed_agents:
            try:
                results["weather"] = self.weather_agent.run_structured(location)
            except Exception as exc:
                results["weather"] = {
                    "section": "weather",
                    "status": "error",
                    "error": {"code": "agent_error", "message": str(exc)},
                }

        if "news" in routed_agents:
            try:
                results["news"] = self.news_agent.run_structured()
            except Exception as exc:
                results["news"] = {
                    "section": "news",
                    "status": "error",
                    "error": {"code": "agent_error", "message": str(exc)},
                }

        if "commute" in routed_agents:
            try:
                # Pass the extracted destination — this is the core fix for
                # hardcoded routing. If destination is empty the commute tool
                # falls back to geocoding "{location} city centre".
                results["commute"] = self.commute_agent.run_structured(location, destination)
            except Exception as exc:
                results["commute"] = {
                    "section": "commute",
                    "status": "error",
                    "error": {"code": "agent_error", "message": str(exc)},
                }

        if "breakfast" in routed_agents:
            try:
                results["breakfast"] = self.breakfast_agent.run_structured(ingredients, time_constraint)
            except Exception as exc:
                results["breakfast"] = {
                    "section": "breakfast",
                    "status": "error",
                    "error": {"code": "agent_error", "message": str(exc)},
                }

        envelope = {
            "session_id": session_id or "",
            "intent": {
                "location":        location,
                "destination":     destination,   # ← persisted so refresh can reuse it
                "sections":        sections,
                "ingredients":     ingredients,
                "time_constraint": time_constraint,
            },
            "sections": results,
        }

        if session_id:
            self.session_manager.log_interaction(
                session_id,
                {"query": query, "structured": True, "sections_returned": list(results.keys())},
            )

        return envelope

    # ------------------------------------------------------------------
    # Re-run a single section with an existing intent dict
    # ------------------------------------------------------------------
    def run_section(self, section: str, intent: dict) -> dict:
        """Re-invoke one agent using a saved intent.  Used by /refresh."""
        location        = intent.get("location", "")
        destination     = intent.get("destination", "")   # ← carries through on refresh
        ingredients     = intent.get("ingredients", [])
        time_constraint = intent.get("time_constraint", "10 min")

        dispatch = {
            "weather":   lambda: self.weather_agent.run_structured(location),
            "news":      lambda: self.news_agent.run_structured(),
            "commute":   lambda: self.commute_agent.run_structured(location, destination),
            "breakfast": lambda: self.breakfast_agent.run_structured(ingredients, time_constraint),
        }

        handler = dispatch.get(section)
        if handler is None:
            return {
                "section": section,
                "status": "error",
                "error": {"code": "unknown_section", "message": f"No agent for section '{section}'."},
            }
        try:
            return handler()
        except Exception as exc:
            return {
                "section": section,
                "status": "error",
                "error": {"code": "agent_error", "message": str(exc)},
            }
