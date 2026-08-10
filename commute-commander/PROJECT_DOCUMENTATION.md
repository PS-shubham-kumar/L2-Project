# Commute Commander — Project Documentation

> Last updated: 2026-08-09
> Status: Phase 3 complete · Phase 4 complete · CLI preserved

---

## 1. Overview

Commute Commander is a Python application that blends natural-language understanding, specialist agents, MCP-style tool registration, and session persistence to generate a personalized morning briefing covering weather, commute, news, and breakfast.

It runs as both a CLI tool and a full responsive web dashboard. The web UI is served by a pure-Python HTTP server with no framework dependencies.

---

## 2. Completion Status

### ✅ Phase 1 — CLI Core

| Item | File | Status |
|---|---|---|
| Natural-language query parser | `nlp/query_parser.py` | ✅ |
| OrchestratorAgent `run()` | `agents/orchestrator.py` | ✅ |
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

### ✅ Phase 3 — API Completeness (completed 2026-08-09)

| Item | File | What changed |
|---|---|---|
| `SessionManager.save_intent()` / `get_intent()` | `services/session_manager.py` | Writes/reads `intent` key in session JSON — survives server restarts |
| `SessionManager.save_briefing()` / `is_saved()` | `services/session_manager.py` | Marks session as saved, persists full section payloads to `last_sections` |
| `SessionManager.get_session()` / `list_sessions()` | `services/session_manager.py` | Full session read; list returns summaries (session_id, query, location, sections, saved) |
| `POST /api/briefing/{id}/save` | `webapp.py` | Re-runs sections, calls `save_briefing()`, returns `{saved: true}` |
| `POST /api/briefing/{id}/rerun` | `webapp.py` | Re-runs all agents from stored intent, returns full sections envelope |
| `PATCH /api/briefing/{id}/intent` | `webapp.py` | Merges any subset of intent fields, persists to disk |
| `GET /api/history` fix | `webapp.py` | Was broken (`data[0]` on a dict); now uses `session_manager.list_sessions()` |
| `GET /api/history/{session_id}` | `webapp.py` | Returns full session JSON for detail view |
| Intent persistence across restarts | `webapp.py` + `session_manager.py` | `_session_intents` in-memory dict removed; all lookups go through `session_manager.get_intent()` |
| Removed redundant `orchestrator.run()` call | `webapp.py` | `_handle_briefing` now calls `run_structured()` once only |
| Real Open-Meteo hourly weather | `mcp_tools/weather_tools.py` | `_geocode()` → `_fetch_open_meteo()` → `_build_hourly()` (07:00–20:00 slots) |
| Weather high/low from real hourly | `agents/weather_agent.py` | Derived from `max()/min()` of hourly temps; synthetic fallback only when hourly is empty |
| News URLs in RSS path | `mcp_tools/news_tools.py` | `_parse_rss()` extracts `<link>` text (RSS) / `href` attr (Atom); 3 feed fallbacks |
| News tool returns structured dicts | `mcp_tools/news_tools.py` | Returns `[{title, source, url, published_at}]` instead of plain strings |
| NewsAgent handles new dict format | `agents/news_agent.py` | `run_structured()` passes real URLs through; `run()` still outputs plain text |
| Re-run button wired to `/rerun` | `web/app.js` | Was re-submitting the form; now calls `POST /api/briefing/{id}/rerun` |

---

### ✅ Phase 4 — Real Commute Routing + Leaflet Map (completed 2026-08-09)

| Item | File | What changed |
|---|---|---|
| TomTom Search geocoding | `mcp_tools/commute_tools.py` | `_geocode_tomtom()` resolves city name → lat/lon/label; falls back to Open-Meteo geocoding |
| TomTom Routing API | `mcp_tools/commute_tools.py` | `_call_tomtom_route()` calls `/routing/1/calculateRoute/`, decodes `points[]` to `[[lat,lon]]` polyline, extracts `eta_minutes`, `distance_km`, `traffic_delay_s` |
| Drive + bike + walk routing | `mcp_tools/commute_tools.py` | Calls TomTom for `car`, `bicycle`, `pedestrian` modes; synthetic transit = drive ETA + 12 min |
| Traffic delay alerts | `mcp_tools/commute_tools.py` | Alert generated when `trafficDelayInSeconds > 300` |
| Advisory fallback | `mcp_tools/commute_tools.py` | Full structured fallback dict with empty polylines when no key or API error |
| `get_commute_advice()` shim | `mcp_tools/commute_tools.py` | Preserved for CLI `run()` compatibility |
| `CommuteTool.get_commute_route()` | `mcp_tools/commute_tools.py` | New primary method; `get_commute_advice()` delegates to it |
| `CommuteAgent.run_structured()` | `agents/commute_agent.py` | Calls `get_commute_route()`, surfaces `polyline`, `origin`, `dest`, `distance_km`, `source` |
| Orchestrator passes `destination` | `agents/orchestrator.py` | Both `run_structured()` and `run_section()` pass `destination=""` to commute agent |
| Leaflet 1.9.4 CDN (SRI) | `web/index.html` | CSS in `<head>`, JS before `app.js`; SRI hashes for both |
| Real Leaflet map div | `web/index.html` | Replaced decorative SVG with `#commute-map` + source badge + empty-state paragraph |
| Map CSS | `web/styles.css` | `.commute-map` 160px height, `z-index:0`; `.map-source-badge` green/amber variants |
| Leaflet map module | `web/app.js` | `_ensureMap()`, `_makePinIcon()` SVG divIcon, `renderCommuteMap()` — main route (purple), alternates (dashed), origin/dest markers with popups, `fitBounds()` |
| Source badge | `web/app.js` | Shows "Live · TomTom" (green) or "Advisory" (amber) |
| Commute modal enriched | `web/app.js` | Shows origin/dest labels, distance, data source |
| News rows clickable | `web/app.js` | Clicking a headline row opens `item.url` in a new tab when URL is present |
| News modal links | `web/app.js` | Headline titles are `<a>` tags when URL available |

---

## 3. Current API Endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| `GET` | `/` | Serves `web/index.html` | ✅ |
| `POST` | `/api/briefing` | Full briefing — `{session_id, intent, sections{}}` | ✅ |
| `POST` | `/api/briefing/{id}/{section}/refresh` | Re-run one agent | ✅ |
| `GET` | `/api/briefing/{id}/{section}` | Poll one section | ✅ |
| `POST` | `/api/briefing/{id}/save` | Pin briefing to disk | ✅ |
| `POST` | `/api/briefing/{id}/rerun` | Re-run all agents from stored intent | ✅ |
| `PATCH` | `/api/briefing/{id}/intent` | Merge intent fields, persist | ✅ |
| `GET` | `/api/history` | List 20 most-recent sessions | ✅ |
| `GET` | `/api/history/{id}` | Full session detail | ✅ |

---

## 4. Current Project Structure

```text
commute-commander/
├── main.py                        # CLI entry point
├── webapp.py                      # HTTP server — static files + full JSON API
├── run_demo.py
├── README.md
├── PROJECT_DOCUMENTATION.md       # ← this file
├── requirements.txt
│
├── agents/
│   ├── orchestrator.py            # run() · run_structured() · run_section()
│   ├── weather_agent.py           # run() · run_structured() — real hourly data
│   ├── news_agent.py              # run() · run_structured() — real URLs
│   ├── commute_agent.py           # run() · run_structured(location, destination)
│   ├── breakfast_agent.py         # run() · run_structured()
│   ├── router.py
│   └── agent_registry.py
│
├── mcp_tools/
│   ├── weather_tools.py           # Open-Meteo geocoding + current + hourly
│   ├── news_tools.py              # NewsAPI + 3 RSS feeds, structured dicts with URLs
│   ├── commute_tools.py           # TomTom Search + Routing, advisory fallback
│   ├── recipe_tools.py            # MealDB API
│   ├── real_mcp_server.py
│   ├── server_registry.py
│   ├── tool_registry.py
│   ├── tool_schema.py
│   └── framework_mcp.py
│
├── nlp/
│   └── query_parser.py
│
├── services/
│   ├── session_manager.py         # save_intent · get_intent · save_briefing
│   │                              # get_session · list_sessions
│   ├── config.py                  # OPENWEATHER / NEWSAPI / TOMTOM / ORS keys
│   ├── mealdb.py
│   ├── news_feed.py
│   └── open_meteo.py
│
├── sessions/                      # {session_id, intent, last_sections, interactions[]}
│
├── web/
│   ├── index.html                 # Leaflet CDN · 3-view layout (Ask/History/Settings)
│   ├── styles.css                 # Token CSS · Leaflet map styles
│   └── app.js                     # Leaflet map module · card renderers · /rerun wired
│
├── docs/
│   ├── ui-spec.md
│   ├── api-contract.md
│   └── design-preferance/
│
└── tests/
    ├── test_query_parser.py
    └── test_session_logging.py
```

---

## 5. Data Flow (current)

```
User query (browser)
   ↓
POST /api/briefing
   ↓
OrchestratorAgent.run_structured(query, session_id)
   ↓  ┌─────────────────────────────────────────────────────┐
   ↓  │ QueryParser → {location, sections, ingredients, ...} │
   ↓  └─────────────────────────────────────────────────────┘
   ↓
Router.route(sections)
   ↓
┌──────────────────────────────────────────────────────────┐
│ WeatherAgent.run_structured(location)                     │
│   → WeatherTool → _geocode() → Open-Meteo current+hourly │
│                                                          │
│ NewsAgent.run_structured()                               │
│   → NewsTool → NewsAPI | RSS (with URLs)                 │
│                                                          │
│ CommuteAgent.run_structured(location, destination)       │
│   → CommuteTool → _geocode() → TomTom Routing API       │
│                   → polyline + ETA + alternates          │
│                                                          │
│ BreakfastAgent.run_structured(ingredients, time)         │
│   → RecipeTool → MealDB API                              │
└──────────────────────────────────────────────────────────┘
   ↓
{session_id, intent, sections{weather,news,commute,breakfast}}
   ↓
session_manager.save_intent(session_id, intent)   ← disk
   ↓
JSON response → browser
   ↓
dispatchSection() → card renderers
   ↓ (commute)
renderCommuteMap() → Leaflet polyline + markers → #commute-map
```

---

## 6. Session File Format (current)

```json
{
  "session_id":    "guest-20260809180809",
  "user_id":       "guest",
  "created_at":    "2026-08-09T18:08:09.297101",
  "saved":         false,
  "intent":        { "location": "Chicago, IL", "sections": ["weather","commute"], ... },
  "last_sections": null,
  "interactions":  [
    { "query": "...", "structured": true, "sections_returned": [...], "timestamp": "..." }
  ]
}
```

---

## 7. Environment Variables

| Key | Used by | Required |
|---|---|---|
| `OPENWEATHER_API_KEY` | `weather_tools.py` — current conditions | Optional (falls back to Open-Meteo) |
| `NEWSAPI_API_KEY` | `news_tools.py` — top headlines with URLs | Optional (falls back to RSS) |
| `TOMTOM_API_KEY` | `commute_tools.py` — routing + geocoding | Optional (falls back to advisory) |
| `OPENROUTESERVICE_API_KEY` | `commute_tools.py` — future alternative | Not yet used |

---

## 8. What Is Left — Remaining Gaps

### Functional

| Gap | Detail |
|---|---|
| Transit routing | TomTom free tier excludes public transit; transit ETA is drive+12 min synthetic |
| Weather condition label | Derived from temperature range only; no precipitation or cloud-cover data |
| Breakfast `steps[]` | MealDB sometimes omits steps; fallback generates generic steps |
| `GET /api/briefing/{id}/stream` (SSE) | Cards still load all-at-once; no per-agent streaming |

### UI

| Gap | Detail |
|---|---|
| Map on mobile | Leaflet container is 160px and works but is not resizable / full-screen |
| Dark mode | CSS token system is ready; no `prefers-color-scheme` media query yet |
| Settings persistence | Settings form saves a toast but no `GET /api/settings` + `PUT /api/settings` backend |

---

## 9. Future Roadmap

### Phase 5 — Progressive loading / SSE

- [ ] `GET /api/briefing/{id}/stream` — Server-Sent Events endpoint emitting one JSON event per section as each agent completes
- [ ] `app.js` EventSource listener — render cards as events arrive instead of waiting for all agents
- [ ] Eliminates wait on slowest agent (currently commute TomTom call can be 1–2 s)

### Phase 6 — Persistent storage

- [ ] Replace JSON file sessions with SQLite (`services/db.py`)
- [ ] Store intent, section results, and timestamps relationally
- [ ] Enable history search and re-open of past briefings with full section data

### Phase 7 — User accounts and preferences

- [ ] `GET /api/settings` and `PUT /api/settings` endpoints
- [ ] Store default location, units, default sections, news categories per user
- [ ] Pre-fill query textarea with saved preferences on page load
- [ ] Simple session-cookie authentication (no OAuth needed for v1)

### Phase 8 — Real MCP SDK migration

- [ ] Replace custom `MCPToolRegistry` / `RealMCPServer` with the official MCP Python SDK
- [ ] Register each tool server as a proper MCP-compliant server
- [ ] Enable external orchestrator discovery of tools

### Phase 9 — Voice interface

- [ ] Web Speech API speech-to-text input in browser
- [ ] Text-to-speech briefing playback (Web Speech API or ElevenLabs)
- [ ] Wire the audio play button in the sidebar

### Phase 10 — Mobile / PWA

- [ ] `manifest.json` + service worker for installable PWA
- [ ] Offline fallback page
- [ ] Push notifications for morning briefing reminders

---

## 10. How to Run

```bash
# Web dashboard
python webapp.py
# Open http://localhost:8000

# CLI
python main.py

# Tests
python -m pytest tests/
```
