# Commute Commander — Project Documentation

> Last updated: 2026-08-09
> Status: Phases 1–7 complete · Phase 8 planned

---

## 1. Overview

Commute Commander is a Python application that blends natural-language understanding, specialist agents, MCP-style tool registration, and session persistence to generate a personalised morning briefing covering weather, commute, news, and breakfast.

It runs as both a CLI tool and a full responsive web dashboard. The web UI is served by a pure-Python HTTP server with no framework dependencies. Sessions are stored in a WAL-mode SQLite database. Cards render progressively via Server-Sent Events as each agent completes.

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
| `POST` | `/api/briefing` | Full briefing — `{session_id, intent, sections{}}` | ✅ |
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
commute-commander/
├── main.py                        # CLI entry point
├── webapp.py                      # HTTP server — static files + full JSON API
├── run_demo.py
├── README.md
├── PROJECT_DOCUMENTATION.md
├── requirements.txt
│
├── agents/
│   ├── orchestrator.py            # run() · run_structured() · run_section()
│   ├── weather_agent.py           # run() · run_structured() — real hourly data
│   ├── news_agent.py              # run() · run_structured() — real URLs
│   ├── commute_agent.py           # run() · run_structured(location, destination)
│   ├── breakfast_agent.py         # run() · run_structured()
│   ├── router.py                  # Maps section names → agent names
│   └── agent_registry.py
│
├── mcp_tools/
│   ├── weather_tools.py           # Open-Meteo geocoding + current + hourly
│   ├── news_tools.py              # NewsAPI + 3 RSS feeds, structured dicts with URLs
│   ├── commute_tools.py           # TomTom Search + Routing, advisory fallback
│   ├── recipe_tools.py            # MealDB API
│   ├── framework_mcp.py           # MCPToolRegistry — decorator-based tool registration
│   ├── real_mcp_server.py         # RealMCPServer — register + call tools by name
│   ├── server_registry.py         # Registry of named MCP servers
│   ├── tool_registry.py           # Registry of named tool callables
│   └── tool_schema.py             # ToolSchema dataclass
│
├── nlp/
│   └── query_parser.py            # Keyword + regex parser — no ML model
│
├── services/
│   ├── db.py                      # SQLiteSessionManager — Phase 6 persistence
│   ├── session_manager.py         # JSON-file SessionManager — kept for CLI / tests
│   ├── settings_manager.py        # SettingsManager — Phase 7 user preferences
│   ├── config.py                  # Env-var config loader (OPENWEATHER / NEWSAPI / TOMTOM)
│   ├── mealdb.py                  # TheMealDB API client
│   ├── news_feed.py               # RSS / NewsAPI client
│   └── open_meteo.py              # Open-Meteo API client
│
├── sessions/
│   └── sessions.db                # SQLite database (WAL mode)
│
├── web/
│   ├── index.html                 # Leaflet CDN · 3-view layout (Ask/History/Settings)
│   ├── styles.css                 # Token CSS · Leaflet map styles
│   └── app.js                     # SSE streaming · Leaflet map · card renderers · settings
│
└── docs/
    ├── api-contract.md
    └── ui-spec.md

tests/
├── test_query_parser.py           # NLP parser tests
├── test_session_logging.py        # JSON SessionManager tests
└── test_phase6_7.py               # SQLiteSessionManager + SettingsManager tests
```

---

## 6. Data Flow (current)

```
User query (browser)
   ↓
POST /api/briefing
   ↓
OrchestratorAgent.run_structured(query, session_id)
   ↓  ┌──────────────────────────────────────────────────────┐
   ↓  │ QueryParser → {location, sections, ingredients, ...} │
   ↓  └──────────────────────────────────────────────────────┘
   ↓
Router.route(sections)
   ↓
┌─────────────────────────────────────────────────────────────┐
│ WeatherAgent.run_structured(location)                        │
│   → WeatherTool → _geocode() → Open-Meteo current + hourly  │
│                                                             │
│ NewsAgent.run_structured()                                  │
│   → NewsTool → NewsAPI | RSS (with URLs)                    │
│                                                             │
│ CommuteAgent.run_structured(location, destination)          │
│   → CommuteTool → TomTom geocoding → TomTom Routing API     │
│                   → polyline + ETA + alternates             │
│                                                             │
│ BreakfastAgent.run_structured(ingredients, time)            │
│   → RecipeTool → MealDB API                                 │
└─────────────────────────────────────────────────────────────┘
   ↓
{session_id, intent, sections{weather,news,commute,breakfast}}
   ↓
SQLiteSessionManager.save_intent(session_id, intent)   ← SQLite
   ↓
JSON response → browser (POST /api/briefing)
   ↓
dispatchSection() → renders immediately-available cards
   ↓
EventSource /api/briefing/{id}/stream
   ↓  (parallel agent threads emit events as they complete)
dispatchSection() → renders remaining cards progressively
```

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
| `OPENWEATHER_API_KEY` | `weather_tools.py` — current conditions | Optional (falls back to Open-Meteo) |
| `NEWSAPI_API_KEY` | `news_tools.py` — top headlines with URLs | Optional (falls back to RSS) |
| `TOMTOM_API_KEY` | `commute_tools.py` — routing + geocoding | Optional (falls back to advisory) |
| `OPENROUTESERVICE_API_KEY` | `commute_tools.py` — future alternative | Not yet used |

---

## 10. Known Gaps

| Gap | Detail |
|---|---|
| Transit routing | TomTom free tier excludes public transit; transit ETA is drive+12 min synthetic |
| Weather condition label | Derived from temperature range only; no precipitation or cloud-cover data |
| Breakfast `steps[]` | MealDB sometimes omits steps; fallback generates generic steps |
| Map on mobile | Leaflet container is 160px and works but is not resizable / full-screen |
| Dark mode | CSS token system is ready; no `prefers-color-scheme` media query yet |

---

## 11. Future Roadmap

### Phase 8 — Official MCP SDK Migration
- Replace custom `MCPToolRegistry` / `RealMCPServer` with the official MCP Python SDK
- Register each tool server as a proper MCP-compliant server
- Enable external orchestrator discovery of tools

### Phase 9 — Voice Interface
- Web Speech API speech-to-text input in browser
- Text-to-speech briefing playback (Web Speech API or ElevenLabs)
- Wire the audio play button in the sidebar

### Phase 10 — Mobile / PWA
- `manifest.json` + service worker for installable PWA
- Offline fallback page
- Push notifications for morning briefing reminders

---

## 12. How to Run

```bash
# Web dashboard
python webapp.py
# Open http://localhost:8000

# CLI
python main.py

# Tests
python -m pytest tests/
```
