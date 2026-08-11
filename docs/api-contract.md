# Commute Commander — API Contract

Defines every HTTP endpoint, request shape, and response shape. Maps directly onto the implementation: `QueryParser` → intent, `OrchestratorAgent` → briefing envelope, specialist agents → one section each, `SQLiteSessionManager` → persistence, `SettingsManager` → user preferences.

---

## 1. Submit Query

**`POST /api/briefing`**

Request:
```json
{
  "query": "I'm leaving from Chicago. Give me weather, news, commute, and a 10-min breakfast with eggs.",
  "user_id": "guest"
}
```

`user_id` is optional — defaults to `"guest"`. The `query` field is free-form natural language; the `QueryParser` extracts location, sections, ingredients, and time constraint automatically.

Response:
```json
{
  "session_id": "guest-20260809180809",
  "intent": {
    "location": "Chicago",
    "sections": ["weather", "news", "commute", "breakfast"],
    "ingredients": ["eggs"],
    "time_constraint": "10 minutes",
    "travel_intent": ["leaving"]
  },
  "sections": {
    "weather":   { "section": "weather",   "status": "success", "data": { ... } },
    "news":      { "section": "news",      "status": "success", "data": { ... } },
    "commute":   { "section": "commute",   "status": "success", "data": { ... } },
    "breakfast": { "section": "breakfast", "status": "success", "data": { ... } }
  },
  "briefing": "## Weather\n..."
}
```

The `sections` object contains whichever agents completed within the 30-second hard timeout. Any section that failed returns an error envelope (see §3.5) rather than crashing the whole briefing.

Error (empty query):
```json
{ "error": "Please enter what you would like in your briefing." }
```

Error (timeout):
```json
{ "error": "The briefing took too long. Check your network connection and try again." }
```

---

## 2. SSE Streaming

**`GET /api/briefing/{session_id}/stream`**

Opens a Server-Sent Events stream. Each agent runs in a parallel daemon thread; one `data:` event is emitted as each section completes. The client does not need to wait for all agents.

Event format — one per section:
```
data: {"section":"weather","status":"success","data":{...}}

data: {"section":"commute","status":"success","data":{...}}

data: {"event":"done"}
```

The terminal `{"event":"done"}` event signals the stream is finished. The client should close the `EventSource` on receipt.

Error event (agent failure):
```
data: {"section":"news","status":"error","error":{"code":"agent_error","message":"..."}}
```

Usage pattern in `app.js`:
1. `POST /api/briefing` — renders any sections already in the response
2. `GET /api/briefing/{id}/stream` — renders remaining sections as they arrive

---

## 3. Section Shapes

### 3.1 Weather
```json
{
  "section": "weather",
  "status": "success",
  "data": {
    "temp": 29.0,
    "temp_unit": "C",
    "condition": "Hot & Sunny",
    "high": 33.2,
    "low": 22.0,
    "uv_index": 4.3,
    "uv_label": "Moderate — wear sunscreen",
    "source": "openweather+open-meteo",
    "lat": 41.8781,
    "lon": -87.6298,
    "hourly": [
      { "time": "06:00", "temp": 22.0, "uv_index": 0.0 },
      { "time": "07:00", "temp": 22.5, "uv_index": 0.1 },
      { "time": "13:00", "temp": 33.2, "uv_index": 4.3 }
    ]
  }
}
```

`hourly` contains real Open-Meteo data for slots 06:00–20:00. `source` is `"openweather+open-meteo"` when the OWM key is present, `"open-meteo"` otherwise.

### 3.2 News
```json
{
  "section": "news",
  "status": "success",
  "data": {
    "headlines": [
      {
        "title": "City council approves new bike lanes downtown",
        "source": "BBC News",
        "url": "https://www.bbc.co.uk/news/...",
        "timestamp": "2026-08-09T08:42:00Z"
      }
    ]
  }
}
```

Up to 5 headlines. `url` is always present when NewsAPI or a well-formed RSS feed is used. Headlines are clickable in the UI — clicking opens the article in a new tab.

### 3.3 Commute
```json
{
  "section": "commute",
  "status": "success",
  "data": {
    "recommended_mode": "drive",
    "eta_minutes": 28,
    "alerts": ["Traffic delay of ~8 min on recommended route."],
    "alternates": [
      { "mode": "transit",  "eta_minutes": 40, "distance_km": 18.0, "polyline": [[...]] },
      { "mode": "bike",     "eta_minutes": 55, "distance_km": 12.0, "polyline": [[...]] },
      { "mode": "walk",     "eta_minutes": 90, "distance_km": 10.5, "polyline": [[...]] }
    ],
    "distance_km": 18.0,
    "polyline": [[41.883, -87.632], [41.884, -87.631], ...],
    "origin": { "lat": 41.883229, "lon": -87.632398, "label": "Chicago, IL" },
    "dest":   { "lat": 41.879399, "lon": -87.632324, "label": "Downtown Chicago, Chicago, IL" },
    "source": "tomtom",
    "mode_label": "Drive"
  }
}
```

`polyline` is `[[lat, lon], ...]` decoded from TomTom's `points[]` array — ready for Leaflet. `source` is `"tomtom"` when the API key is present and routing succeeds, `"advisory"` otherwise (polylines will be empty arrays in advisory mode). Transit ETA is synthetic (drive ETA + 12 min) because TomTom free tier excludes public transit.

### 3.4 Breakfast
```json
{
  "section": "breakfast",
  "status": "success",
  "data": {
    "recipe_name": "Scrambled Eggs",
    "prep_time_minutes": 10,
    "ingredients_used": ["eggs"],
    "steps": [
      "Gather your ingredients: eggs.",
      "Prep and measure everything before you start.",
      "Cook the Scrambled Eggs over medium heat, stirring occasionally.",
      "Plate and serve immediately."
    ],
    "alternates": [
      { "recipe_name": "Oat bowl", "prep_time_minutes": 10 }
    ]
  }
}
```

`steps` comes from MealDB when available; a 4-step generic fallback is generated when the API omits them.

### 3.5 Section-level error

Any section can fail independently without affecting the others:
```json
{
  "section": "news",
  "status": "error",
  "error": {
    "code": "agent_error",
    "message": "Connection timeout fetching RSS feed."
  }
}
```

---

## 4. Refresh a Single Card

**`POST /api/briefing/{session_id}/{section}/refresh`**

No body required. Re-invokes only that agent with the stored intent. Response shape is identical to §3 for that section.

---

## 5. Poll a Single Section

**`GET /api/briefing/{session_id}/{section}`**

Returns the current result for one section by re-running the agent with the stored intent. Same response shape as §3. Returns 404 if the session is not found.

---

## 6. Re-run All Agents

**`POST /api/briefing/{session_id}/rerun`**

No body. Re-invokes all agents from the stored intent. Response:
```json
{
  "session_id": "guest-20260809180809",
  "intent": { ... },
  "sections": { "weather": {...}, "news": {...}, "commute": {...}, "breakfast": {...} }
}
```

---

## 7. Update Intent

**`PATCH /api/briefing/{session_id}/intent`**

Merges any subset of intent fields and persists to SQLite. Recognised fields: `location`, `sections`, `ingredients`, `time_constraint`, `travel_intent`.

Request:
```json
{ "location": "Evanston, IL", "sections": ["weather", "commute"] }
```

Response:
```json
{ "session_id": "guest-20260809180809", "intent": { "location": "Evanston, IL", ... } }
```

---

## 8. Save / Pin Briefing

**`POST /api/briefing/{session_id}/save`**

No body. Re-runs all sections from stored intent, then calls `SQLiteSessionManager.save_briefing()` which sets `saved=1` and writes `last_sections` to the database.

Response:
```json
{ "saved": true, "session_id": "guest-20260809180809" }
```

Failure:
```json
{ "saved": false, "error": { "code": "write_failed", "message": "Briefing not saved — retry?" } }
```

---

## 9. History

**`GET /api/history`** — list 20 most-recent sessions, newest first:
```json
{
  "sessions": [
    {
      "session_id": "guest-20260809180809",
      "user_id": "guest",
      "created_at": "2026-08-09T18:08:09+00:00",
      "saved": false,
      "query": "Weather and commute from Chicago",
      "location": "Chicago",
      "sections": ["weather", "commute"]
    }
  ]
}
```

**`GET /api/history/{session_id}`** — full session detail:
```json
{
  "session_id": "guest-20260809180809",
  "user_id": "guest",
  "created_at": "2026-08-09T18:08:09+00:00",
  "saved": false,
  "saved_at": null,
  "intent": { "location": "Chicago", "sections": ["weather", "commute"], ... },
  "last_sections": null,
  "interactions": [
    { "query": "Weather and commute from Chicago", "structured": true, "sections_returned": ["weather","commute"], "timestamp": "..." }
  ]
}
```

Returns 404 if the session does not exist.

---

## 10. Settings

**`GET /api/settings`** — returns current settings with defaults for any missing keys:
```json
{
  "default_location": "Chicago, IL",
  "units": "metric",
  "default_sections": ["weather", "commute", "news", "breakfast"],
  "news_categories": ["general"]
}
```

**`PUT /api/settings`** — merges validated updates and persists to `settings.json`:
```json
{
  "default_location": "London",
  "units": "imperial",
  "default_sections": ["weather", "news"]
}
```

Validation rules:
- `units` must be `"metric"` or `"imperial"` — other values are silently ignored
- `default_sections` entries must be one of `weather`, `commute`, `news`, `breakfast` — unknown values are filtered out

Response: the full updated settings object (same shape as GET).

---

## 11. Common Rules

- Every section response includes `section` (string) and `status` (`"success"` | `"error"`) so the UI can route it to the right card without guessing
- Section payloads are independent — one failing never blocks or delays another
- All timestamps are ISO 8601 UTC; the UI localises for display
- `session_id` from §1 is required on every subsequent call
- All JSON responses include `Content-Type: application/json; charset=utf-8` and `Access-Control-Allow-Origin: *`
- The 30-second hard timeout on `POST /api/briefing` is enforced via a daemon thread — if it fires, a `TimeoutError` is returned as a 500 with a user-friendly message
