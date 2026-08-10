# Commute Commander — API Contract

Defines exactly what the web UI sends to the backend and what it gets back, for every interaction described in `ui-spec.md`. Maps directly onto the existing architecture: `QueryParser` → intent object, `OrchestratorAgent` → briefing envelope, `WeatherAgent` / `NewsAgent` / `CommuteAgent` / `BreakfastAgent` → one section each, `SessionManager` → persistence.

---

## 1. Submit Query

**`POST /api/briefing`**

Request (free text):
```json
{
  "query": "Leaving from Chicago, give me weather, news, commute, and a 10-min breakfast with eggs"
}
```

Request (guided/structured input, bypasses NLP parsing):
```json
{
  "location": "Chicago, IL",
  "sections": ["weather", "news", "commute", "breakfast"],
  "ingredients": ["eggs"],
  "time_constraint": 10,
  "travel_intent": "leaving"
}
```

Response — envelope only, sections populate asynchronously (see §3):
```json
{
  "session_id": "guest-20260801091500",
  "intent": {
    "location": "Chicago, IL",
    "sections": ["weather", "news", "commute", "breakfast"],
    "ingredients": ["eggs"],
    "time_constraint": 10,
    "travel_intent": "leaving"
  },
  "status": "processing"
}
```

If parsing fails to extract a location:
```json
{
  "error": {
    "code": "location_not_found",
    "message": "Couldn't determine a location from that query."
  }
}
```

---

## 2. Confirm / Edit Parsed Intent

**`PATCH /api/briefing/{session_id}/intent`**

Request — any subset of fields, user-edited chips:
```json
{
  "location": "Evanston, IL",
  "sections": ["weather", "commute"]
}
```

Response: updated intent object (same shape as §1), triggers re-run of only the affected agents on next `Re-run` or immediately, per product decision.

---

## 3. Section Results (progressive load)

Each card polls or subscribes independently. Two supported patterns — pick one per implementation; shapes are identical either way.

**Poll:** `GET /api/briefing/{session_id}/{section}`
**Stream:** `GET /api/briefing/{session_id}/stream` (SSE, one event per section as it completes)

### 3.1 Weather
```json
{
  "section": "weather",
  "status": "success",
  "data": {
    "temp": 72,
    "condition": "Partly Cloudy",
    "high": 78,
    "low": 61,
    "uv_index": 6,
    "uv_label": "Moderate — wear sunscreen",
    "hourly": [
      { "time": "07:00", "temp": 64, "uv_index": 1 },
      { "time": "13:00", "temp": 78, "uv_index": 7 }
    ]
  }
}
```

### 3.2 News
```json
{
  "section": "news",
  "status": "success",
  "data": {
    "headlines": [
      {
        "title": "City council approves new bike lanes downtown",
        "source": "Chicago Tribune",
        "url": "https://example.com/article",
        "timestamp": "2026-08-01T08:42:00Z"
      }
    ]
  }
}
```

### 3.3 Commute
```json
{
  "section": "commute",
  "status": "success",
  "data": {
    "recommended_mode": "drive",
    "eta_minutes": 32,
    "alerts": ["Minor delay on I-90 near exit 12"],
    "alternates": [
      { "mode": "transit", "eta_minutes": 41 },
      { "mode": "bike", "eta_minutes": 55 }
    ]
  }
}
```

### 3.4 Breakfast
```json
{
  "section": "breakfast",
  "status": "success",
  "data": {
    "recipe_name": "Veggie Scramble",
    "prep_time_minutes": 10,
    "ingredients_used": ["eggs", "spinach", "cheese"],
    "steps": [
      "Whisk eggs in a bowl.",
      "Sauté spinach for 2 minutes.",
      "Add eggs, scramble until set, top with cheese."
    ],
    "alternates": [
      { "recipe_name": "Egg Toast", "prep_time_minutes": 8 }
    ]
  }
}
```

### 3.5 Section-level error
Any section can fail independently without affecting the others:
```json
{
  "section": "news",
  "status": "error",
  "error": {
    "code": "upstream_timeout",
    "message": "Couldn't load news right now."
  }
}
```

---

## 4. Refresh a Single Card

**`POST /api/briefing/{session_id}/{section}/refresh`**

No body required. Re-invokes only that agent (`WeatherAgent`, `NewsAgent`, `CommuteAgent`, or `BreakfastAgent`) with the existing intent. Response shape identical to §3 for that section.

---

## 5. Swap Breakfast Suggestion

**`POST /api/briefing/{session_id}/breakfast/swap`**

Request:
```json
{ "exclude": ["Veggie Scramble"] }
```
Response: same shape as §3.4, a new `data` object.

---

## 6. Re-run All

**`POST /api/briefing/{session_id}/rerun`**

No body. Re-invokes the orchestrator with the current intent object. Response: same envelope as §1, `status: "processing"`, followed by fresh section events per §3.

---

## 7. Dismiss a Card

**`PATCH /api/briefing/{session_id}/intent`**
```json
{ "sections": ["weather", "commute"] }
```
Removing a section from the intent's `sections` array is the dismiss mechanism — no separate endpoint needed.

---

## 8. Save / Pin Briefing

**`POST /api/briefing/{session_id}/save`**

No body. Persists the current briefing via `SessionManager` beyond the active session.

Response:
```json
{ "saved": true, "session_id": "guest-20260801091500" }
```
Failure:
```json
{ "saved": false, "error": { "code": "write_failed", "message": "Briefing not saved — retry?" } }
```

---

## 9. History

**`GET /api/history`** — list past sessions:
```json
{
  "sessions": [
    {
      "session_id": "guest-20260731190753",
      "created_at": "2026-07-31T19:07:53Z",
      "location": "Chicago, IL",
      "sections": ["weather", "commute"]
    }
  ]
}
```

**`GET /api/history/{session_id}`** — full read-only briefing, same shape as a completed §1 + §3 responses combined.

---

## 10. Settings

**`GET /api/settings`** / **`PUT /api/settings`**
```json
{
  "default_location": "Chicago, IL",
  "units": "imperial",
  "default_sections": ["weather", "commute"],
  "news_categories": ["local", "top"]
}
```

---

## 11. Common Envelope Rules

- Every section response includes `section` and `status` (`success` | `error` | `loading`) so the UI can route it to the right card without guessing.
- Section payloads are independent — one failing never blocks or delays another.
- All timestamps ISO 8601 UTC; UI localizes for display.
- `session_id` from §1 is required on every subsequent call in this contract.
