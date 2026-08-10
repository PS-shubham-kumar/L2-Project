# Commute Commander — Project Documentation

> Last updated: 2026-08-09
> Status: Web UI complete · Backend structured API complete · CLI preserved

---

## 1. Overview

Commute Commander is a Python application that blends natural-language understanding, specialist agents, MCP-style tool registration, and session persistence to generate a personalized morning briefing covering weather, commute, news, and breakfast.

The project started as a CLI tool and has been fully extended with a responsive web dashboard. It is structured to support continued growth into voice interfaces, mobile apps, and real MCP SDK integration.

---

## 2. Completion Status

### ✅ Done — Phase 1: CLI Core

| Item | Status |
|---|---|
| Natural-language query parser (`nlp/query_parser.py`) | ✅ Complete |
| OrchestratorAgent with `run()` | ✅ Complete |
| WeatherAgent — plain text output | ✅ Complete |
| NewsAgent — plain text output | ✅ Complete |
| BreakfastAgent — plain text output | ✅ Complete |
| CommuteAgent — plain text output | ✅ Complete |
| MCP-style tool layer (ToolRegistry, ServerRegistry, RealMCPServer) | ✅ Complete |
| JSON session persistence via SessionManager | ✅ Complete |
| CLI entry point (`main.py`) | ✅ Complete |
| Demo runner (`run_demo.py`) | ✅ Complete |
| Basic web server (`webapp.py`) with `POST /api/briefing` | ✅ Complete |
| Minimal web UI (`web/`) — single textarea, plain-text output | ✅ Complete |

---

### ✅ Done — Phase 2: Structured API + Rich Web UI (completed 2026-08-09)

#### Backend

| Item | File | Status |
|---|---|---|
| `WeatherAgent.run_structured()` — typed dict with temp, condition, high/low, uv_index, uv_label, hourly[] | `agents/weather_agent.py` | ✅ |
| `NewsAgent.run_structured()` — dict with headlines[{title, source, url, timestamp}] | `agents/news_agent.py` | ✅ |
| `CommuteAgent.run_structured()` — dict with recommended_mode, eta_minutes, alerts[], alternates[] | `agents/commute_agent.py` | ✅ |
| `BreakfastAgent.run_structured()` — dict with recipe_name, prep_time_minutes, ingredients_used, steps[], alternates[] | `agents/breakfast_agent.py` | ✅ |
| `OrchestratorAgent.run_structured()` — full structured envelope: {session_id, intent, sections{}} | `agents/orchestrator.py` | ✅ |
| `OrchestratorAgent.run_section()` — re-invoke one agent by section name using cached intent | `agents/orchestrator.py` | ✅ |
| `POST /api/briefing` returns structured JSON (session_id, intent, sections) alongside legacy briefing text | `webapp.py` | ✅ |
| `POST /api/briefing/{id}/{section}/refresh` — single-agent re-run | `webapp.py` | ✅ |
| `GET /api/briefing/{id}/{section}` — poll a single section | `webapp.py` | ✅ |
| `GET /api/history` — list past sessions from the sessions/ directory | `webapp.py` | ✅ |
| In-memory `_session_intents` cache per session for refresh calls | `webapp.py` | ✅ |

#### Frontend

| Item | File | Status |
|---|---|---|
| Full HTML rebuild matching design reference | `web/index.html` | ✅ |
| Purple SVG icon sidebar (7 nav items, active state, sign-out) | `web/index.html` | ✅ |
| Topbar (eyebrow + h1, search input, avatar) | `web/index.html` | ✅ |
| Hero card — period chips, SVG sparkline (cubic-bezier temp line + UV band), callout bubble, 3-metric footer | `web/index.html` | ✅ |
| Commute Now action card (purple, icon, ETA badge, refresh + expand buttons) | `web/index.html` | ✅ |
| Breakfast Idea action card (pink, icon, prep-time badge, swap + expand buttons) | `web/index.html` | ✅ |
| Weather & UV mini-card (floating icon, UV gradient progress bar) | `web/index.html` | ✅ |
| Headlines mini-card (floating icon, progress bar) | `web/index.html` | ✅ |
| Breakfast Prep Timer mini-card (countdown progress bar, Start/Pause button) | `web/index.html` | ✅ |
| Right panel — Ask Commander tab, History tab | `web/index.html` | ✅ |
| Query form (textarea, user-id input, submit button) | `web/index.html` | ✅ |
| Intent confirmation chips (location + section chips, appear after parse) | `web/index.html` | ✅ |
| Example prompt chips (4 clickable pre-filled queries) | `web/index.html` | ✅ |
| Dashboard controls (Re-run all, Save briefing, Edit query) | `web/index.html` | ✅ |
| Live commute map (decorative SVG with road grid, route lines, start/end pins) | `web/index.html` | ✅ |
| Detail modal (close via button, backdrop, Escape key) | `web/index.html` | ✅ |
| Toast notification | `web/index.html` | ✅ |
| Full CSS token system (--lavender, --purple, --pink, --green, --ink, --muted, --line) | `web/styles.css` | ✅ |
| Card hierarchy radii (shell 32px → cards 24px → chips 12px) | `web/styles.css` | ✅ |
| Skeleton shimmer loading state | `web/styles.css` | ✅ |
| Responsive layout — 850px breakpoint (right panel drops below, sidebar goes horizontal) | `web/styles.css` | ✅ |
| Responsive layout — 560px breakpoint (sidebar hidden, single column) | `web/styles.css` | ✅ |
| SVG sparkline renderer (cubic-bezier temp line + UV band area fill) | `web/app.js` | ✅ |
| Per-card renderers: renderWeather, renderCommute, renderBreakfast, renderNews | `web/app.js` | ✅ |
| dispatchSection router — routes payload to correct renderer | `web/app.js` | ✅ |
| Form submit handler with per-card skeleton loading | `web/app.js` | ✅ |
| data-refresh event delegation — single-card refresh | `web/app.js` | ✅ |
| data-expand event delegation — modal with detail HTML builders | `web/app.js` | ✅ |
| Breakfast swap button → refreshSection('breakfast') | `web/app.js` | ✅ |
| Breakfast prep timer (interval-based, Start/Pause/Done) | `web/app.js` | ✅ |
| Tab switching (Ask Commander / History) | `web/app.js` | ✅ |
| History loader (GET /api/history) | `web/app.js` | ✅ |
| Dashboard controls wired (Re-run, Save, Edit) | `web/app.js` | ✅ |

---

## 3. Current Project Structure

```text
commute-commander/
├── main.py                              # CLI entry point
├── webapp.py                            # HTTP server — static files + JSON API
├── run_demo.py                          # demo runner
├── README.md
├── PROJECT_DOCUMENTATION.md            # ← this file
├── requirements.txt
├── __init__.py
│
├── agents/
│   ├── orchestrator.py                  # run() [CLI] + run_structured() + run_section() [API]
│   ├── weather_agent.py                 # run() + run_structured()
│   ├── news_agent.py                    # run() + run_structured()
│   ├── commute_agent.py                 # run() + run_structured()
│   ├── breakfast_agent.py               # run() + run_structured()
│   ├── router.py                        # intent-to-agent routing
│   ├── agent_registry.py
│   ├── mcp_agent.py
│   └── tool_discovery_agent.py
│
├── mcp_tools/
│   ├── weather_tools.py                 # OpenWeather + Open-Meteo fallback
│   ├── news_tools.py                    # NewsAPI + RSS fallback
│   ├── recipe_tools.py                  # MealDB API
│   ├── commute_tools.py                 # TomTom / OpenRouteService / advice fallback
│   ├── real_mcp_server.py
│   ├── server_registry.py
│   ├── tool_registry.py
│   ├── tool_schema.py
│   ├── framework_mcp.py
│   └── mcp_server.py
│
├── nlp/
│   └── query_parser.py                  # keyword + zero-shot intent parser
│
├── services/
│   ├── config.py                        # API key management
│   ├── session_manager.py               # JSON session persistence
│   ├── mealdb.py
│   ├── news_feed.py
│   └── open_meteo.py
│
├── sessions/                            # persisted session JSON files
│
├── web/                                 # browser UI (served by webapp.py)
│   ├── index.html                       # full dashboard — rebuilt 2026-08-09
│   ├── styles.css                       # token-based CSS — rebuilt 2026-08-09
│   └── app.js                           # card renderers + API client — rebuilt 2026-08-09
│
├── docs/
│   ├── ui-spec.md
│   ├── api-contract.md
│   └── design-preferance/               # visual design reference images
│
├── examples/
│   └── agentic_flow.py
│
└── tests/
    ├── test_query_parser.py
    └── test_session_logging.py
```

---

## 4. System Flow

### Web UI flow (current)

```
User types query in browser
   ↓
POST /api/briefing  {query, user_id}
   ↓
webapp.py → OrchestratorAgent.run_structured()
   ↓
QueryParser.parse() → {location, sections, ingredients, time_constraint}
   ↓
Router.route(sections)
   ↓
[WeatherAgent | NewsAgent | BreakfastAgent | CommuteAgent].run_structured()
   ↓
Each agent calls its MCP tool (weather_tools / news_tools / recipe_tools / commute_tools)
   ↓
Typed section dicts collected into envelope {session_id, intent, sections{}}
   ↓
JSON response → browser
   ↓
dispatchSection() routes each section to its card renderer
   ↓
Hero card, action cards, mini-cards update independently
   ↓
SessionManager logs interaction to sessions/*.json
```

### Single-card refresh flow

```
User clicks Refresh on a card
   ↓
POST /api/briefing/{session_id}/{section}/refresh
   ↓
webapp.py → OrchestratorAgent.run_section(section, cached_intent)
   ↓
One agent re-runs → typed section dict
   ↓
dispatchSection() updates only that card
```

### CLI flow (preserved)

```
python main.py → OrchestratorAgent.run(query) → combined plain-text briefing → terminal
```

---

## 5. API Endpoints (current)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Serves `web/index.html` |
| `POST` | `/api/briefing` | Full briefing — returns `{session_id, intent, sections{}, briefing}` |
| `POST` | `/api/briefing/{id}/{section}/refresh` | Re-run one agent, return one section dict |
| `GET` | `/api/briefing/{id}/{section}` | Poll one section using cached intent |
| `GET` | `/api/history` | List past sessions from `sessions/` directory |

---

## 6. What Is Left — Gaps & Known Limitations

### Functional gaps

| Gap | Detail |
|---|---|
| Real commute routing | `commute_tools.py` returns advice text only; no actual map routing. TomTom / ORS keys needed to get real ETA + turn-by-turn. |
| Weather hourly data is synthetic | `weather_agent.run_structured()` generates synthetic hourly values by offsetting the current temp. Real hourly data needs the Open-Meteo hourly endpoint. |
| News without source URLs | `news_tools.py` parses from RSS; no article URLs in the RSS fallback path. NewsAPI returns real URLs when key is configured. |
| Session intents are in-memory | `_session_intents` in `webapp.py` is lost on server restart. Needs file or DB persistence. |
| No real SSE / streaming | Cards load all-at-once from one request, not progressively per agent. The API contract describes SSE but it is not implemented. |
| `/api/briefing/{id}/save` not implemented | The Save button calls this endpoint but `webapp.py` returns a 404. |
| `/api/briefing/{id}/rerun` not implemented | Re-run all currently re-submits the form from JS; a proper endpoint is missing. |
| `PATCH /api/briefing/{id}/intent` not implemented | Intent editing chips in the UI have no backend write path. |

### UI gaps

| Gap | Detail |
|---|---|
| Live map is decorative only | The commute map SVG is a static illustration; no real map library (Leaflet, Mapbox) integrated. |
| Weather sparkline uses synthetic hourly data | Will auto-correct once the weather agent returns real hourly data. |
| No dark mode | Token system is ready for it but no `@media (prefers-color-scheme: dark)` rules exist yet. |
| No audio briefing | The play button in the sidebar is wired for nav state only; no TTS integration. |

---

## 7. Future Roadmap

### Phase 3 — API completeness (next priority)

- [ ] Implement `POST /api/briefing/{id}/save` — write briefing to `sessions/` with structured data
- [ ] Implement `POST /api/briefing/{id}/rerun` — re-run orchestrator with cached intent, return fresh envelope
- [ ] Implement `PATCH /api/briefing/{id}/intent` — update and re-run on intent edits
- [ ] Persist `_session_intents` to disk alongside session JSON so they survive restarts
- [ ] Replace synthetic hourly weather with real Open-Meteo hourly endpoint call
- [ ] Pass real article URLs from NewsAPI through to the news section data

### Phase 4 — Real commute routing

- [ ] Integrate TomTom or OpenRouteService for actual route geometry and ETA
- [ ] Return real `alternates[]` with mode, ETA, and polyline for map rendering
- [ ] Replace decorative map SVG with Leaflet.js and real route overlay

### Phase 5 — Progressive loading / SSE

- [ ] Add `GET /api/briefing/{id}/stream` SSE endpoint — emit one event per section as agents complete
- [ ] Update `app.js` to listen on the event stream and render cards as events arrive
- [ ] This eliminates the wait for the slowest agent before anything appears

### Phase 6 — Persistent storage

- [ ] Replace JSON file sessions with SQLite (or PostgreSQL for production)
- [ ] Store intent, section results, and timestamps relationally
- [ ] Enable history search, filtering, and re-open of past briefings

### Phase 7 — User accounts and preferences

- [ ] Add user registration + login (JWT or session cookie)
- [ ] Store default location, units (metric/imperial), default sections, news categories per user
- [ ] `GET /api/settings` and `PUT /api/settings` endpoints from the API contract
- [ ] Pre-fill query with saved preferences on page load

### Phase 8 — Real MCP SDK migration

- [ ] Replace the custom MCP simulation layer with the official MCP Python SDK
- [ ] Register each tool server as a proper MCP-compliant server
- [ ] Enable tool discovery by an external orchestrator agent

### Phase 9 — Voice interface

- [ ] Add speech-to-text input (Web Speech API in browser, or Whisper API)
- [ ] Add text-to-speech briefing playback (Web Speech API or ElevenLabs)
- [ ] Wire the audio play button in the sidebar to trigger TTS of the current briefing

### Phase 10 — Mobile / PWA

- [ ] Add `manifest.json` and service worker for installable PWA
- [ ] Offline fallback page
- [ ] Push notifications for morning briefing reminders

---

## 8. How to Run

### Web dashboard
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

---

## 9. Environment Variables (`.env`)

| Key | Purpose | Required |
|---|---|---|
| `OPENWEATHER_API_KEY` | Real-time weather data | Optional (falls back to Open-Meteo) |
| `NEWSAPI_API_KEY` | Top headlines with URLs | Optional (falls back to RSS) |
| `TOMTOM_API_KEY` | Real commute routing | Optional (falls back to advice text) |
| `OPENROUTESERVICE_API_KEY` | Alternative routing | Optional |

---

## 10. Architecture Patterns

### Multi-agent orchestration
Each specialist agent owns its domain. The orchestrator coordinates without knowing agent internals. Adding a new domain (e.g., calendar, health) means adding one agent + one tool module — nothing else changes.

### Dual-mode agents
Every agent exposes both `run()` (plain text for CLI) and `run_structured()` (typed dict for the web API). This keeps the CLI fully functional while the web UI gets structured data it can render into cards.

### MCP-style tool layer
Tool registration, server grouping, and tool invocation are abstracted through `ToolRegistry` / `ServerRegistry` / `RealMCPServer`. Ready for migration to the official MCP Python SDK when needed.

### Session-first persistence
Every interaction is logged to `sessions/*.json` with a session ID and timestamp. This is compatible with future migration to a database without redesigning the orchestration layer.

### Token-based CSS
All colors, radii, and shadows are defined as CSS custom properties. Extending to dark mode, theming, or a design token export (Style Dictionary) requires only changes to `:root`.

---

## 11. Design Reference

The web UI was built to match the fitness dashboard design reference (stored in `docs/design-preferance/`) adapted to the commute/weather/news/breakfast content domain:

| Reference element | Commute Commander equivalent |
|---|---|
| Lavender-blue canvas | Page background |
| White rounded shell with border | `app-shell` — 32px radius, ambient shadow |
| Narrow purple icon sidebar | Navigation rail — 7 SVG icons |
| Large purple "Overview" card with sparkline | Hero card — temp/UV sparkline, 3 metrics |
| Purple accent card (top right) | Commute Now — ETA badge, mode, alerts |
| Pink accent card (top right) | Breakfast Idea — recipe name, prep time |
| Three white mini-cards with floating icons | Weather & UV, Headlines, Prep Timer |
| Right panel with list and map | Briefing panel — form, history, route map |
