# Commute Commander

A Python application that combines NLP query parsing, specialist agents, real MCP tool servers (built with `FastMCP`), and session persistence to deliver a personalised morning briefing — covering weather, news, commute, and breakfast — via both a CLI and a browser-based web dashboard.

## Features

- Natural-language query parsing — extracts location, sections, ingredients, time constraints, and travel intent using keyword + regex matching (no ML model, instant startup)
- Four specialist agents: Weather · News · Commute · Breakfast — each independently callable with both plain-text (CLI) and structured JSON (web) output
- Real external data — Open-Meteo hourly weather, NewsAPI/RSS headlines with URLs, TomTom routing with live polylines, TheMealDB recipes
- Leaflet map — live commute route rendered in-browser with origin/destination markers and alternate routes
- SSE streaming — cards render progressively as each agent completes, no waiting for the slowest one
- SQLite session persistence — WAL-mode database survives server restarts
- Settings backend — `GET/PUT /api/settings` persists default location, units, and section preferences
- ReAct Agentic Loop & Reflection — iterative tool discovery, execution, cross-section reflection (e.g. extreme heat warnings), and friendly natural-language synthesis
- **MCP Tools & Server Layer** — Official **FastMCP** tools/servers (`FastMCP` from `fastmcp` SDK) wrapped by `RealMCPServer` for in-process agent execution, plus lightweight MCP-style servers (`MCPToolServer`)
- Lightweight web UI served by a built-in Python HTTP server — no framework required

## MCP Tools & Server Architecture

This project uses **real Model Context Protocol (MCP) tools and servers** built with the official `fastmcp` Python SDK, alongside in-process wrappers and lightweight MCP-style servers:

1. **Standard MCP Tools & FastMCP Servers**:
   - Tools (`get_weather`, `get_headlines`, `get_route`, `get_breakfast_recipe`) are registered using standard `@mcp.tool` decorators on `FastMCP` server instances (`FastMCP("weather-server")`, etc.) in `src/mcp_tools/`.
   - Each tool file can be executed standalone (`python src/mcp_tools/weather_tools.py`) to launch a standard FastMCP server for external MCP client connections over stdio/SSE.

2. **In-Process Real MCP Server (`RealMCPServer` & `MCPAgent`)**:
   - `RealMCPServer` (`src/mcp_tools/real_mcp_server.py`) wraps `FastMCP` servers to provide in-process tool listing (`list_tools()`), health checking (`health_check()`), and direct tool invocation (`call_tool()`).
   - `MCPAgent` (`src/agents/mcp_agent.py`) connects to these servers in memory during the ReAct agentic loop for dynamic tool discovery and execution.

3. **MCP-Style Fallback & Test Wrappers**:
   - `MCPToolServer` (`src/mcp_tools/mcp_server.py`) and `ToolRegistry` (`src/mcp_tools/tool_registry.py`) provide lightweight, framework-free MCP-style decorator and server patterns for simple unit testing and mock implementations.

## Project Structure

```
L2-Project/
├── src/                     # All Python source code
│   ├── agents/              # Orchestrator + specialist agents
│   ├── mcp_tools/           # FastMCP tool servers, RealMCPServer & MCP-style registry
│   ├── nlp/                 # Keyword + regex query parser
│   └── services/            # API clients, session manager, SQLite db, settings
│
├── frontend/                # Static web UI (HTML / CSS / JS)
├── scripts/                 # Runnable entry points
│   ├── webapp.py            # Web server  →  python scripts/webapp.py
│   ├── main.py              # CLI         →  python scripts/main.py
│   └── run_demo.py          # Quick demo  →  python scripts/run_demo.py
│
├── tests/                   # All test files
├── data/                    # Runtime-generated data (gitignored)
│   ├── sessions/            # Legacy JSON session files
│   └── sessions.db          # SQLite database
│
├── config/                  # Non-secret configuration
│   └── settings.json        # Default app settings
│
├── docs/                    # Documentation & design specs
│   ├── PROJECT_DOCUMENTATION.md
│   ├── api-contract.md
│   ├── ui-spec.md
│   └── design-preferences/
│
├── .env                     # API keys (gitignored — create from example below)
├── .env.example
├── conftest.py              # pytest path fix
└── requirements.txt
```

## Setup

```bash
git clone <repo-url>
cd L2-Project
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
OPENWEATHER_API_KEY=<your_key>
NEWSAPI_API_KEY=<your_key>
TOMTOM_API_KEY=<your_key>
```

## Running

### Web app
```bash
python scripts/webapp.py
# Open http://localhost:8000
```

### CLI
```bash
python scripts/main.py
```

### Quick demo
```bash
python scripts/run_demo.py
```

### Tests
```bash
python -m pytest tests/ -v
```

## API Keys

The default flow uses free public APIs — no key required to get started.

| Service | Variable | Required? | Notes |
|---|---|---|---|
| Open-Meteo | — | No | Weather + UV + hourly forecast |
| RSS feeds | — | No | News headlines (BBC, NDTV, NYT fallback chain) |
| TheMealDB | — | No | Breakfast recipes |
| OpenWeatherMap | `OPENWEATHER_API_KEY` | Optional | Richer current conditions |
| NewsAPI | `NEWSAPI_API_KEY` | Optional | More reliable headlines with URLs |
| TomTom | `TOMTOM_API_KEY` | Optional | Real routing + geocoding; falls back to advisory |

## Example Queries

```
I'm leaving from Chicago. Give me today's weather, quick news, commute advice, and a 10-minute breakfast idea with eggs.

Weather and commute from London today.

Full briefing from New York with toast.
```

## Implementation Phases

| Phase | Status | Description |
|---|---|---|
| 1 — CLI Core | ✅ | NLP parser, 4 agents, MCP tool layer, JSON sessions, CLI |
| 2 — Structured API + Web UI | ✅ | `run_structured()` on all agents, REST API, Leaflet map, card UI |
| 3 — API Completeness | ✅ | Intent persistence, save/rerun/patch endpoints, real hourly weather, news URLs |
| 4 — Real Commute Routing | ✅ | TomTom geocoding + routing, polylines, traffic alerts, Leaflet map |
| 5 — SSE Streaming | ✅ | `GET /api/briefing/{id}/stream` — cards render as each agent completes |
| 6 — SQLite Persistence | ✅ | `SQLiteSessionManager` replaces JSON files; WAL-mode, same public API |
| 7 — Settings Backend | ✅ | `GET/PUT /api/settings`, settings form persists to disk |
| 8 — Agentic MCP Loop | ✅ | ReAct loop, tool discovery, cross-section reflection pass, friendly response synthesis |
| 9 — Voice Interface | 🔲 | Web Speech API input + TTS playback |
| 10 — PWA / Mobile | 🔲 | Service worker, manifest, push notifications |
