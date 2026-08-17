# Commute Commander — Project Documentation

> Last updated: 2026-08-12
> Status: Phases 1–8 complete · Phase 9 planned

---

## 1. Overview

Commute Commander is a Python application that blends natural-language understanding, specialist agents, MCP-style tool registration, and session persistence to generate a personalised morning briefing covering weather, commute, news, and breakfast.

It runs as both a CLI tool and a full responsive web dashboard. The web UI is served by a pure-Python HTTP server with no framework dependencies. Sessions are stored in a WAL-mode SQLite database. Cards render progressively via Server-Sent Events as each agent completes.

Since Phase 8, all briefings are generated via a **ReAct-style agentic loop** that iteratively discovers tools, calls them, observes results, runs a cross-section reflection pass, and synthesises a friendly natural-language summary.

---

## 2. Completion Status

### ✅ Phase 1 — CLI Core

| Item | File | Status |
|---|---|---|
| Keyword + regex query parser | `nlp/query_parser.py` | ✅ |
| `OrchestratorAgent.run()` | `agents/orchestrator.py` | ✅ |
| WeatherAgent plain-text output | `agents/weather_agent.py` | ✅ |
| NewsAgent plain-text output | `agents/news_agent.py` | ✅ |
| BreakfastAgent plain-text output | `agents/breakfast_agent.py` | ✅ |
| CommuteAgent plain-text output | `agents/commute_agent.py` | ✅ |
| MCP-style tool layer | `mcp_tools/` | ✅ |
| JSON session persistence | `services/session_manager.py` | ✅ |
| CLI entry point | `main.py` | ✅ |
| Demo runner | `run_demo.py` | ✅ |

---

### ✅ Phase 2 — Structured API + Rich Web UI

| Item | File | Status |
|---|---|---|
| `WeatherAgent.run_structured()` | `agents/weather_agent.py` | ✅ |
| `NewsAgent.run_structured()` | `agents/news_agent.py` | ✅ |
| `CommuteAgent.run_structured()` | `agents/commute_agent.py` | ✅ |
| `BreakfastAgent.run_structured()` | `agents/breakfast_agent.py` | ✅ |
| `OrchestratorAgent.run_structured()` | `agents/orchestrator.py` | ✅ |
| `OrchestratorAgent.run_section()` | `agents/orchestrator.py` | ✅ |
| `POST /api/briefing` structured JSON response | `webapp.py` | ✅ |
| `POST /api/briefing/{id}/{section}/refresh` | `webapp.py` | ✅ |
| Full web dashboard HTML | `web/index.html` | ✅ |
| Token-based CSS (lavender/purple/pink theme) | `web/styles.css` | ✅ |
| Card renderers + sparkline + timer | `web/app.js` | ✅ |
| Responsive layout (850px / 560px) | `web/styles.css` | ✅ |

---

### ✅ Phase 3 — API Completeness

| Item | File | What changed |
|---|---|---|
| `SessionManager.save_intent()` / `get_intent()` | `services/session_manager.py` | Writes/reads `intent` key — survives server restarts |
| `SessionManager.save_briefing()` / `is_saved()` | `services/session_manager.py` | Marks session as saved, persists full section payloads |
| `SessionManager.get_session()` / `list_sessions()` | `services/session_manager.py` | Full session read; list returns summaries |
| `POST /api/briefing/{id}/save` | `webapp.py` | Re-runs sections, calls `save_briefing()`, returns `{saved: true}` |
| `POST /api/briefing/{id}/rerun` | `webapp.py` | Re-runs all agents from stored intent |
| `PATCH /api/briefing/{id}/intent` | `webapp.py` | Merges any subset of intent fields, persists to disk |
| `GET /api/history` | `webapp.py` | Returns 20 most-recent session summaries |
| `GET /api/history/{session_id}` | `webapp.py` | Returns full session JSON |
| Real Open-Meteo hourly weather | `mcp_tools/weather_tools.py` | `_geocode()` → `_fetch_open_meteo()` → `_build_hourly()` (06:00–20:00 slots) |
| Weather high/low from real hourly | `agents/weather_agent.py` | Derived from `max()/min()` of hourly temps |
| News URLs in RSS path | `mcp_tools/news_tools.py` | `_parse_rss()` extracts `<link>` text (RSS) / `href` attr (Atom); 3 feed fallbacks |
| News tool returns structured dicts | `mcp_tools/news_tools.py` | Returns `[{title, source, url, published_at}]` |
| Re-run button wired to `/rerun` | `web/app.js` | Was re-submitting the form; now calls `POST /api/briefing/{id}/rerun` |

---

### ✅ Phase 4 — Real Commute Routing + Leaflet Map

| Item | File | What changed |
|---|---|---|
| TomTom Search geocoding | `mcp_tools/commute_tools.py` | `_geocode_tomtom()` resolves city name → lat/lon/label; falls back to Open-Meteo geocoding |
| TomTom Routing API | `mcp_tools/commute_tools.py` | `_call_tomtom_route()` decodes `points[]` to `[[lat,lon]]` polyline, extracts `eta_minutes`, `distance_km`, `traffic_delay_s` |
| Drive + bike + walk routing | `mcp_tools/commute_tools.py` | Calls TomTom for `car`, `bicycle`, `pedestrian` modes; synthetic transit = drive ETA + 12 min |
| Traffic delay alerts | `mcp_tools/commute_tools.py` | Alert generated when `trafficDelayInSeconds > 300` |
| Advisory fallback | `mcp_tools/commute_tools.py` | Full structured fallback dict with empty polylines when no key or API error |
| `CommuteAgent.run_structured()` | `agents/commute_agent.py` | Surfaces `polyline`, `origin`, `dest`, `distance_km`, `source` |
| Leaflet 1.9.4 CDN (SRI) | `web/index.html` | CSS in `<head>`, JS before `app.js`; SRI hashes for both |
| Leaflet map module | `web/app.js` | `_ensureMap()`, `_makePinIcon()`, `renderCommuteMap()` — main route (purple), alternates (dashed), origin/dest markers |
| Source badge | `web/app.js` | Shows "Live · TomTom" (green) or "Advisory" (amber) |
| News rows clickable | `web/app.js` | Clicking a headline row opens `item.url` in a new tab |

---

### ✅ Phase 5 — SSE Streaming

| Item | File | What changed |
|---|---|---|
| `GET /api/briefing/{id}/stream` | `webapp.py` | SSE endpoint — runs each agent in a parallel daemon thread, emits one `data:` event per section as it completes, then sends `{"event":"done"}` |
| `streamBriefing(sessionId)` | `web/app.js` | Opens `EventSource` after the initial POST; calls `dispatchSection()` for each arriving event so cards render as they come in |
| Progressive card rendering | `web/app.js` | POST response renders any immediately-available sections; SSE stream fills in the rest without blocking |

---

### ✅ Phase 6 — SQLite Persistence

| Item | File | What changed |
|---|---|---|
| `SQLiteSessionManager` | `services/db.py` | WAL-mode SQLite with `sessions` + `interactions` tables; same public API as `SessionManager` |
| `webapp.py` uses SQLite | `webapp.py` | `session_manager = SQLiteSessionManager()` — JSON file sessions replaced |
| Schema | `services/db.py` | `sessions(session_id, user_id, created_at, saved, saved_at, intent, last_sections)` + `interactions(id, session_id, data, timestamp)` |
| Timezone-aware timestamps | `services/db.py` | Uses `datetime.now(timezone.utc)` — no deprecation warnings |

---

### ✅ Phase 7 — Settings Backend

| Item | File | What changed |
|---|---|---|
| `SettingsManager` | `services/settings_manager.py` | Validates and persists `default_location`, `units`, `default_sections`, `news_categories` to `settings.json` |
| `GET /api/settings` | `webapp.py` | Returns current settings with defaults for missing keys |
| `PUT /api/settings` | `webapp.py` | Merges validated updates, rejects invalid values (e.g. unknown units) |
| Settings form wired | `web/app.js` | `loadSettings()` pre-fills form on view open; submit calls `PUT /api/settings` |

---

### ✅ Phase 8 — Agentic MCP Loop

| Item | File | What changed |
|---|---|---|
| `MCPAgent` enhanced | `agents/mcp_agent.py` | `connect()` → `list_tools()` → `invoke()` pattern; health check on connect |
| Tool discovery | `agents/orchestrator.py` | `discover_tools()` connects to all 4 MCP servers and lists available tools |
| Agentic ReAct loop | `agents/agentic_loop.py` | Iterative loop: Perceive → Plan → Act → Observe → Decide → Reflect → Respond |
| `OrchestratorAgent.run_agentic()` | `agents/orchestrator.py` | New method that drives the agentic loop; serialises trace, reflection, summary |
| Reflection engine | `agents/reflection.py` | 5 deterministic rules cross-checking weather/commute/breakfast for consistency |
| Response synthesiser | `agents/response_synthesizer.py` | Template-based NL summary referencing real data (temps, ETAs, recipe names) |
| Webapp wired to agentic loop | `scripts/webapp.py` | `POST /api/briefing` now calls `run_agentic()`; response includes `loop_trace`, `reflection`, `summary`, `tools_discovered` |
| Agentic loop tests | `tests/test_agentic_loop.py` | 18 tests: tool discovery, loop execution, trace structure, termination, multi-section |
| Reflection tests | `tests/test_reflection.py` | 10 tests: all 5 rules + edge cases + extreme data scenarios |

#### Acceptance Criteria (all satisfied)

| # | Criterion | Status |
|---|---|---|
| 1 | Tools server runs and each tool returns sensible data | ✅ |
| 2 | Agent connects to the server and can list tools | ✅ |
| 3 | Agentic loop: agent calls a tool, observes, then decides to finish | ✅ |
| 4 | Reflection changes or confirms at least one answer | ✅ |
| 5 | Responses are concise, friendly, and reference fetched data | ✅ |

#### Reflection Rules

| Rule | Trigger | Action |
|---|---|---|
| Hot weather + outdoor commute | `temp ≥ 35°C` + mode is `bike`/`walk` | Switch recommendation to `drive`, add heat alert |
| Cold weather + walking | `temp ≤ 2°C` + mode is `walk`/`bike` | Add cold weather alert |
| High UV + outdoor commute | `uv_index ≥ 8` + mode is `bike`/`walk` | Add UV protection alert |
| Long commute + slow breakfast | `eta ≥ 45 min` + `prep ≥ 15 min` | Add time-saving suggestion |
| Hot weather + hot breakfast | `temp ≥ 30°C` + recipe name contains "hot" | Suggest lighter meal |

---

## 3. Bug Fixes Applied

| Bug | File | Fix |
|---|---|---|
| `"eat"` substring matched inside `"weather"` → breakfast section triggered on every weather query | `nlp/query_parser.py` | Switched all keyword matching to `re.search()` with `\b` word boundaries |
| `"I'm"` picked as location before `"Chicago"` — apostrophe not excluded from proper-noun scan | `nlp/query_parser.py` | Fallback location scan now skips words containing `'` |
| Test asserted `"uv"` as a separate section — UV keywords map to `"weather"` | `tests/test_query_parser.py` | Fixed assertion to check `"weather"` only |

---

## 4. Current API Endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| `GET` | `/` | Serves `web/index.html` | ✅ |
| `POST` | `/api/briefing` | Agentic briefing — `{session_id, intent, sections, loop_trace, reflection, summary, tools_discovered}` | ✅ |
| `POST` | `/api/briefing/{id}/{section}/refresh` | Re-run one agent | ✅ |
| `GET` | `/api/briefing/{id}/{section}` | Poll one section | ✅ |
| `GET` | `/api/briefing/{id}/stream` | SSE stream — one event per agent as it completes | ✅ |
| `POST` | `/api/briefing/{id}/save` | Pin briefing to disk | ✅ |
| `POST` | `/api/briefing/{id}/rerun` | Re-run all agents from stored intent | ✅ |
| `PATCH` | `/api/briefing/{id}/intent` | Merge intent fields, persist | ✅ |
| `GET` | `/api/history` | List 20 most-recent sessions | ✅ |
| `GET` | `/api/history/{id}` | Full session detail | ✅ |
| `GET` | `/api/settings` | Load user settings | ✅ |
| `PUT` | `/api/settings` | Save user settings | ✅ |

---

## 5. Current Project Structure

```
L2-Project/
├── src/                             # All Python source code
│   ├── agents/
│   │   ├── orchestrator.py          # run() · run_structured() · run_agentic() · run_section()
│   │   ├── agentic_loop.py          # ★ Phase 8 — ReAct loop: perceive → act → observe → reflect
│   │   ├── reflection.py            # ★ Phase 8 — 5 cross-section reflection rules
│   │   ├── response_synthesizer.py  # ★ Phase 8 — friendly NL summary generator
│   │   ├── mcp_agent.py             # ★ Phase 8 — connect() → list_tools() → invoke()
│   │   ├── weather_agent.py         # run() · run_structured() — real hourly data
│   │   ├── news_agent.py            # run() · run_structured() — real URLs
│   │   ├── commute_agent.py         # run() · run_structured(location, destination)
│   │   ├── breakfast_agent.py       # run() · run_structured()
│   │   ├── tool_discovery_agent.py  # Discovers tools across all registries
│   │   ├── router.py                # Maps section names → agent names
│   │   └── agent_registry.py
│   │
│   ├── mcp_tools/
│   │   ├── weather_tools.py         # Open-Meteo geocoding + current + hourly
│   │   ├── news_tools.py            # NewsAPI + 3 RSS feeds, structured dicts with URLs
│   │   ├── commute_tools.py         # TomTom Search + Routing, advisory fallback
│   │   ├── recipe_tools.py          # MealDB API
│   │   ├── real_mcp_server.py       # RealMCPServer — register + call tools by name
│   │   ├── server_registry.py       # Registry of named MCP servers
│   │   ├── tool_registry.py         # Registry of named tool callables
│   │   ├── framework_mcp.py         # Deprecated stub (kept for compatibility)
│   │   └── tool_schema.py           # Deprecated stub (kept for compatibility)
│   │
│   ├── nlp/
│   │   └── query_parser.py          # Keyword + regex parser — no ML model
│   │
│   └── services/
│       ├── db.py                    # SQLiteSessionManager — Phase 6 persistence
│       ├── session_manager.py       # JSON-file SessionManager — kept for CLI / tests
│       ├── settings_manager.py      # SettingsManager — Phase 7 user preferences
│       ├── config.py                # Env-var config loader
│       ├── mealdb.py                # TheMealDB API client
│       ├── news_feed.py             # RSS / NewsAPI client
│       └── open_meteo.py            # Open-Meteo API client
│
├── scripts/
│   ├── webapp.py                    # HTTP server — agentic loop is the default path
│   ├── main.py                      # CLI entry point
│   └── run_demo.py                  # Quick demo
│
├── frontend/
│   ├── index.html                   # Leaflet CDN · 3-view layout
│   ├── styles.css                   # Token CSS · Leaflet map styles
│   └── app.js                       # SSE streaming · Leaflet map · card renderers
│
├── tests/
│   ├── test_agentic_loop.py         # ★ Phase 8 — 18 tests: discovery, loop, trace
│   ├── test_reflection.py           # ★ Phase 8 — 10 tests: all 5 reflection rules
│   ├── test_phase6_7.py             # SQLiteSessionManager + SettingsManager tests
│   ├── test_query_parser.py         # NLP parser tests
│   └── test_session_logging.py      # JSON SessionManager tests
│
├── data/
│   ├── sessions/                    # Legacy JSON session files
│   └── sessions.db                  # SQLite database (WAL mode)
│
├── config/
│   └── settings.json                # Default app settings
│
├── docs/
│   ├── PROJECT_DOCUMENTATION.md
│   ├── api-contract.md
│   └── ui-spec.md
│
├── .env                             # API keys (gitignored)
├── conftest.py                      # pytest path fix
└── requirements.txt
```

---

## 6. Data Flow — Agentic Loop (Phase 8)

```
User query (browser)
   ↓
POST /api/briefing
   ↓
OrchestratorAgent.run_agentic(query, session_id)
   ↓
AgenticLoop.run(query)
   ↓
┌──────────────────────────────────────────────────────────────┐
│ 1. PERCEIVE — QueryParser → {location, sections, ...}       │
│ 2. DISCOVER — MCPAgent.connect() → list_tools() on each     │
│              server (weather, news, recipe, commute)         │
│ 3. PLAN    — Router selects sections → pending queue         │
└──────────────────────────────────────────────────────────────┘
   ↓
┌──── AGENTIC LOOP (per section) ─────────────────────────────┐
│ THOUGHT  → "I need weather. Server has ['get_weather']"      │
│ ACTION   → MCPAgent.invoke("get_weather", location=...)      │
│              → WeatherTool → Open-Meteo current + hourly     │
│ OBSERVE  → "Got 28°C, UV 5.2, condition: Hot & Sunny"        │
│ DECIDE   → more sections pending? → loop : finish            │
├──────────────────────────────────────────────────────────────┤
│ THOUGHT  → "I need news. Server has ['get_headlines']"        │
│ ACTION   → MCPAgent.invoke("get_headlines")                   │
│              → NewsTool → NewsAPI | RSS (with URLs)           │
│ OBSERVE  → "Got 5 headlines"                                  │
│ DECIDE   → more sections pending? → loop : finish            │
├──────────────────────────────────────────────────────────────┤
│ ... (commute, breakfast — same pattern)                       │
└──────────────────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. REFLECT — ReflectionEngine cross-checks all sections:     │
│    • 38°C + bike → switch to drive + add heat alert          │
│    • 0°C + walk → add cold weather warning                   │
│    • UV ≥ 8 + bike → add UV protection alert                 │
│    • 50-min commute + 20-min breakfast → suggest quicker meal│
│    • No conflicts → confirm consistency                       │
└──────────────────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. RESPOND — synthesize_response() generates friendly NL:    │
│    "Good morning! It's 28°C and sunny in Chicago..."         │
└──────────────────────────────────────────────────────────────┘
   ↓
{session_id, intent, sections, loop_trace, reflection, summary,
 tools_discovered}   → JSON response → browser
   ↓
dispatchSection() → renders cards
   ↓
EventSource /api/briefing/{id}/stream (SSE for parallel refresh)
```

### Legacy Data Flow (CLI / run_structured)

The original `run()` and `run_structured()` paths are fully preserved for
CLI and backward compatibility. They bypass the agentic loop and call
agents directly.

---

## 7. Session Schema (SQLite)

```sql
-- sessions table
session_id    TEXT PRIMARY KEY          -- e.g. "guest-20260809180809"
user_id       TEXT NOT NULL             -- e.g. "guest"
created_at    TEXT NOT NULL             -- ISO 8601 UTC
saved         INTEGER NOT NULL DEFAULT 0
saved_at      TEXT                      -- set when pinned
intent        TEXT                      -- JSON blob: {location, sections, ingredients, ...}
last_sections TEXT                      -- JSON blob: full section payloads on save

-- interactions table
id            INTEGER PRIMARY KEY AUTOINCREMENT
session_id    TEXT NOT NULL REFERENCES sessions(session_id)
data          TEXT NOT NULL             -- JSON blob: {query, structured, sections_returned, ...}
timestamp     TEXT NOT NULL             -- ISO 8601 UTC
```

---

## 8. Settings Schema

```json
{
  "default_location": "Chicago, IL",
  "units": "metric",
  "default_sections": ["weather", "commute", "news", "breakfast"],
  "news_categories": ["general"]
}
```

Stored at `commute-commander/settings.json`. Validated on write — unknown `units` values and unknown section names are silently dropped.

---

## 9. Environment Variables

| Key | Used by | Required |
|---|---|---|
| `NVIDIA_API_KEY` | `llm_client.py` — NVIDIA NIM LLM function calling & tool decision engine | Optional (falls back to deterministic loop) |
| `NVIDIA_MODEL` | `llm_client.py` — NVIDIA model name (default: `meta/llama-3.1-8b-instruct`) | Optional |
| `GMAIL_USER` | `email_tools.py` — Gmail FastMCP Tool Server dispatch email | Optional |
| `GMAIL_APP_PASSWORD` | `email_tools.py` — Gmail 16-character App Password | Optional |
| `OPENWEATHER_API_KEY` | `weather_tools.py` — current conditions | Optional (falls back to Open-Meteo) |
| `NEWSAPI_API_KEY` | `news_tools.py` — top headlines with URLs | Optional (falls back to RSS) |
| `TOMTOM_API_KEY` | `commute_tools.py` — routing + geocoding | Optional (falls back to advisory) |

---

## 10. Known Gaps

| Gap | Detail |
|---|---|
| Transit routing | TomTom free tier excludes public transit; transit ETA is drive+12 min synthetic |
| Weather condition label | Derived from temperature range only; no precipitation or cloud-cover data |
| Breakfast `steps[]` | MealDB sometimes omits steps; fallback generates generic steps |
| Map on mobile | Leaflet container is 160px and works but is not resizable / full-screen |
| Dark mode | CSS token system is ready; no `prefers-color-scheme` media query yet |
| Loop trace in UI | `loop_trace` is returned in the API but not yet rendered in the web frontend |

---

## 11. Future Roadmap & In-Progress

### Phase 9 — NVIDIA NIM LLM Engine, Travel Itinerary Planner & Gmail MCP Tool (Completed)
- Integrate NVIDIA NIM API endpoint (`https://integrate.api.nvidia.com/v1`) with OpenAI-compatible tool calling (`llm_client.py`).
- Enable dynamic LLM-driven travel itinerary generation and natural language synthesis.
- Build dedicated `ItineraryAgent` and `itinerary_tools` FastMCP server for multi-day travel planning.
- Create official **Gmail FastMCP Tool Server** (`email_tools.py`) registering `@mcp.tool` `send_email_briefing` for LLM tool invocation.
- Add Travel Itinerary Card UI with interactive day tabs, budget breakdown, and "Send via Gmail MCP Tool" button.

### Phase 10 — Voice Interface
- Web Speech API speech-to-text input in browser
- Text-to-speech briefing playback (Web Speech API or ElevenLabs)
- Wire the audio play button in the sidebar

### Phase 11 — Mobile / PWA
- `manifest.json` + service worker for installable PWA
- Offline fallback page
- Push notifications for morning briefing reminders

---

## 12. How to Run

```bash
# Web dashboard
python scripts/webapp.py
# Open http://localhost:8000

# CLI
python scripts/main.py

# Tests
python -m pytest tests/
```
