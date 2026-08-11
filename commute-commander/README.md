# Commute Commander

A Python application that combines NLP query parsing, specialist agents, MCP-style tool servers, and session persistence to deliver a personalised morning briefing — covering weather, news, commute, and breakfast — via both a CLI and a browser-based web dashboard.

## Features

- Natural-language query parsing — extracts location, sections, ingredients, time constraints, and travel intent using keyword + regex matching (no ML model, instant startup)
- Four specialist agents: Weather · News · Commute · Breakfast — each independently callable with both plain-text (CLI) and structured JSON (web) output
- Real external data — Open-Meteo hourly weather, NewsAPI/RSS headlines with URLs, TomTom routing with live polylines, TheMealDB recipes
- Leaflet map — live commute route rendered in-browser with origin/destination markers and alternate routes
- SSE streaming — cards render progressively as each agent completes, no waiting for the slowest one
- SQLite session persistence — WAL-mode database replaces JSON files; survives server restarts
- Settings backend — `GET/PUT /api/settings` persists default location, units, and section preferences
- MCP-style tool layer — custom `MCPToolRegistry` / `RealMCPServer` with decorator-based tool registration
- Lightweight web UI served by a built-in Python HTTP server — no framework required

## Project Structure

```
L2-Project/
├── commute-commander/
│   ├── agents/              # Orchestrator + specialist agents
│   ├── mcp_tools/           # MCP-style tool servers & registry
│   ├── nlp/                 # Keyword + regex query parser
│   ├── services/            # API clients, session manager, SQLite db, settings
│   ├── web/                 # Static UI (HTML / CSS / JS)
│   ├── sessions/            # Runtime SQLite DB + legacy JSON files
│   ├── webapp.py            # HTTP server entry point (all REST endpoints)
│   ├── main.py              # Interactive CLI entry point
│   └── requirements.txt
└── tests/
    ├── test_query_parser.py
    ├── test_session_logging.py
    └── test_phase6_7.py
```

## Setup

```bash
git clone <repo-url>
cd L2-Project/commute-commander
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in any optional API keys (see below).

## Running

### Web app
```bash
python webapp.py
# Open http://localhost:8000
```

### CLI
```bash
python main.py
```

### Tests
```bash
python -m pytest tests/
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

Add optional keys to `.env`:

```
OPENWEATHER_API_KEY=<your_key>
NEWSAPI_API_KEY=<your_key>
TOMTOM_API_KEY=<your_key>
```

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
| 8 — MCP SDK Migration | 🔲 | Replace custom registry with official MCP Python SDK |
| 9 — Voice Interface | 🔲 | Web Speech API input + TTS playback |
| 10 — PWA / Mobile | 🔲 | Service worker, manifest, push notifications |
