# Commute Commander — UI Specification

## 1. Purpose

Web dashboard for the existing CLI (natural-language query → orchestrated agent briefing: weather, news, commute, breakfast). Preserves the "single query, combined briefing" model while giving each domain a dedicated, glanceable card. Visual direction: soft lavender canvas, purple vertical icon rail, rounded white dashboard shell, purple/pink accent cards, right-side panel, soft shadows throughout.

---

## 2. Primary User Flow

```
Landing → Query Input → Parsed-Intent Confirmation (optional) → Loading (progressive) → Briefing Dashboard → (Re-run | Drill-in | History)
```

1. **Landing** — single input box, example prompts, or "Continue this morning's briefing" if a session exists.
2. **Query submitted** — free text, or guided inputs (location field + section toggles + ingredient tags + time slider).
3. **Parsed-intent confirmation** — extracted `location`, `sections`, `ingredients`, `time_constraint` shown as editable chips before/while agents run.
4. **Loading** — cards populate progressively per-agent, not blocked on the slowest one.
5. **Briefing dashboard** — all requested cards render together. User can re-run, edit query, dismiss a card, or drill into any card.
6. **History (secondary flow)** — revisit past briefings, mirrors existing JSON session logs.

---

## 3. Screens

| Screen | Role |
|---|---|
| Landing / Query | Entry point, large input + examples |
| Parsed-Intent Confirmation | Inline, editable chips — not necessarily a separate screen |
| Briefing Dashboard | Primary screen, card grid |
| Card Detail / Expanded View | Drill-in per card |
| History | Past briefings list, reopenable read-only |
| Settings | Default location, units, default sections, news preferences |

---

## 4. Page Shell & Layout

| Element | Spec |
|---|---|
| Page background | Soft lavender, full viewport |
| Dashboard shell | Large rounded rectangle (~28–32px radius), white fill, soft ambient shadow |
| Grid | Left icon rail / main content / right panel |
| Responsive | 2-column card grid desktop, 1-column mobile |

### Left Icon Rail (purple vertical sidebar)
Icon-only, no labels, active item = solid white icon tile.

| Icon | Function |
|---|---|
| Bell | Alerts (weather warnings, delays, breaking headlines) |
| Home (active) | Today's Briefing |
| Document | Saved / past briefings |
| Bar-chart | Trends (weekly weather + commute patterns) |
| Route/pin | Saved commute routes |
| Play | Audio briefing playback |
| Exit (bottom) | Sign out |

### Header
Eyebrow "Today" + title "Briefing" · search field ("Search a route, city, or headline") · circular avatar, top-right, opens account menu.

---

## 5. Cards & Buttons

### Hero — Briefing Overview (large purple card)
- Period chips: Morning / Afternoon / Evening
- Chart: temperature trend across the day, UV shown as a secondary band, one highlighted point (e.g., "72°F · UV 6")
- Footer stat row: **Departure Time** · **Commute ETA** · **UV Peak**

### Commute Now (purple accent card)
- Displays: recommended mode/route, ETA, alerts
- `Expand` → alternate routes/modes
- `Refresh` → re-check current conditions

### Breakfast Idea (pink accent card)
- Displays: prep time + recipe name
- `Expand` (circular arrow) → full recipe/steps
- `Swap suggestion` → alternate recipe, same constraints

### Weather & UV (secondary card)
- Displays: condition, UV index + plain-language risk label
- Progress bar: UV risk meter (green→red)
- `Expand` → hourly forecast
- `Refresh` → re-fetch

### Headlines (secondary card + right panel feed)
- Displays: 3–5 top headlines, source + timestamp
- Right-panel feed: tab toggle Top Stories / Local, list rows with source, title, time, open-in-new icon
- `Expand` → full headline list
- `Open source` → original article, new tab
- `Refresh` → re-fetch latest

### Breakfast Timer (secondary card)
- Progress bar: prep-time completion if recipe active
- Footer: "0 / 10 min" (left) / "Start" (pill, button)

### Live Commute Map (right panel)
- Route line, start/end pins, traffic/incident marker if relevant

### Global Dashboard Controls
- `Edit query` → back to Query screen, prior input pre-filled
- `Re-run all` → re-invoke orchestrator with same parsed intent
- `Save / Pin briefing` → persist beyond session (maps to `SessionManager`)
- `Dismiss card` (per card) → remove section from view without re-running others

---

## 6. Empty, Loading, and Error States

### Empty
| Screen | Condition | Response |
|---|---|---|
| Landing | No prior session | Example queries as clickable prompts |
| Briefing Dashboard | Zero sections detected | "I couldn't tell what you'd like — try adding weather, news, commute, or breakfast." + quick-add chips |
| Breakfast Card | No ingredients provided | Generic quick-breakfast suggestions + "Add ingredients for a personalized idea" |
| History | No past sessions | "Your morning briefings will show up here once you run your first query." |

### Loading
- Per-card skeleton loaders — cards populate independently as each agent responds.
- Query parsing: brief inline loading (animated chip placeholders) before confirmation chips appear.
- `Refresh` shows a small in-card spinner only, never a full dashboard reload.
- Skeleton shape matches eventual content to avoid layout shift.

### Error
| Scenario | Response |
|---|---|
| One agent fails (e.g., News times out) | Inline card error: "Couldn't load news right now" + `Retry`. Other cards unaffected. |
| Parser can't extract location | Inline prompt to enter location manually |
| Total orchestrator failure | Full-dashboard banner: "Something went wrong generating your briefing" + `Retry all` |
| No ingredients but breakfast requested | Non-blocking notice, falls back to generic suggestion |
| Session save fails | Toast: "Briefing not saved — retry?" — doesn't block viewing |

---

## 7. Color & Material Tokens

| Token | Use |
|---|---|
| Lavender | Page canvas only, never inside the shell |
| White | Dashboard shell, secondary cards |
| Purple (deep) | Sidebar, hero card, Commute Now card, active nav state |
| Pink (soft) | Breakfast Idea card only — single warm accent, not reused elsewhere |
| Green | UV-safe / freshness-good progress states only |
| Shadows | Soft, diffuse, consistent radius across shell, cards, floating chips |

---

## 8. State Model (per card)

```
idle → loading → success | error
```
Each card component: `status`, `data`, `onRefresh`, `onExpand`, `onDismiss`.

---

## 9. Accessibility & Interaction Notes

- All card actions (`Refresh`, `Expand`, `Dismiss`) keyboard-navigable, screen-reader labeled (e.g., `aria-label="Refresh weather card"`).
- Error and empty states never color-only — pair with icon + text.
- The circular "go deeper" arrow button is the one recurring drill-in affordance, reused consistently across Commute, Breakfast, and Headlines — not reinvented per card.
- Real-time push updates out of scope for v1 (poll or refresh-on-demand only).
- Multi-user accounts out of scope for v1 (session-based, matching current guest session model).
