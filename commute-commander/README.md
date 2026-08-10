# Commute Commander

A Python project that combines NLP parsing, specialist agents, and MCP-style tool servers to deliver a personalised morning briefing — covering weather, news, commute, and breakfast — via both a CLI and a browser-based web app.

## Features

- Natural-language query parsing (location, sections, ingredients, travel intent)
- Specialist agents: Weather · News · Commute · Breakfast
- MCP-style tool servers with a shared tool registry
- Session logging to JSON (ready to swap for a database)
- Lightweight web UI served by a built-in Python HTTP server (no framework needed)

## Project structure

```
L2-Project/
├── commute-commander/
│   ├── agents/          # Orchestrator + specialist agents
│   ├── mcp_tools/       # MCP-style tool servers & registry
│   ├── nlp/             # Query parser
│   ├── services/        # API clients (weather, news, meals) + session manager
│   ├── web/             # Static UI (HTML / CSS / JS)
│   ├── sessions/        # Runtime session JSON files (git-ignored)
│   ├── webapp.py        # Web server entry point
│   ├── main.py          # CLI entry point
│   └── requirements.txt
└── tests/
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

## API keys

The default flow uses free public APIs — no key required to get started.

| Service | Key needed? | Notes |
|---|---|---|
| Open-Meteo | No | Weather & UV |
| RSS feeds | No | News |
| TheMealDB | No | Breakfast recipes |
| OpenWeatherMap | Optional | Richer weather data |
| NewsAPI | Optional | More reliable news |
| Google Maps / TomTom | Optional | Advanced routing |

Add optional keys to your `.env` file:

```
OPENWEATHERMAP_API_KEY=<your_key>
NEWS_API_KEY=<your_key>
```

## Example query

> I'm leaving from Chicago. Give me today's weather and UV, quick news, commute advice, and a 10-minute breakfast idea with eggs.

## Tests

```bash
python -m pytest tests/
```
