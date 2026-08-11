# Commute Commander — UI Specification

## 1. Purpose

Web dashboard for the Commute Commander backend. A single natural-language query triggers four specialist agents (weather, commute, news, breakfast); results render progressively as each agent completes via SSE. Visual direction: soft lavender canvas, purple vertical icon rail, rounded white dashboard shell, purple/pink accent cards, right-side news + map panel.

---

## 2. Primary User Flow

```
Landing → Query Input → POST /api/briefing → Skeleton cards appear
       → Cards render progressively via SSE stream
       → Full briefing dashboard
       → (Refresh card | Expand detail | Re-run all | Save | Edit query)
```

1. Landing — query textarea, example prompt chips, user name field
2. Query submitted — `POST /api/briefing`; skeleton loaders appear on all cards immediately
3. Progressive rendering — `EventSource /api/briefing/{id}/stream` emits one event per agent; each card renders as its data arrives
4. Full dashboard — all cards populated; Re-run / Save / Edit controls appear
5. History (sidebar) — past sessions loaded from `GET /api/history`
6. Settings (sidebar) — preferences loaded from `GET /api/settings`, saved via `PUT /api/settings`

---

## 3. Views

| View | Route trigger | Content |
|---|---|---|
| Ask | Default / sidebar "Ask" button | Query form + results grid |
| History | Sidebar "History" button | Session list from `GET /api/history` |
| Settings | Sidebar "Settings" button | Preferences form, pre-filled from `GET /api/settings` |

Only one view is visible at a time. View switching is client-side only (no page reload).

---

## 4. Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar  │  Topbar (eyebrow + heading + avatar)            │
│  (purple) ├─────────────────────────────────────────────────┤
│           │  View: Ask                                       │
│  [Ask]    │  ┌──────────────────────┐  ┌──────────────────┐ │
│  [History]│  │  Query form          │  │  Headlines panel │ │
│  [Settings│  │  Intent chips        │  │  Live map        │ │
│  [Signout]│  │  Hero card           │  └──────────────────┘ │
│           │  │  Action row          │                        │
│           │  │  Mini cards row      │                        │
│           │  │  Dash controls       │                        │
│           │  └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

Responsive breakpoints: 850px (2-column → 1-column), 560px (compact mobile).

---

## 5. Components

### Query Form
- `<textarea>` — free-form natural language query
- User name input — sets `user_id` on the POST request (defaults to `"guest"`)
- Submit button — triggers `POST /api/briefing`
- Example prompt chips — pre-fill the textarea and auto-submit on click
- Intent chips — shown after parse: location chip + one chip per detected section (hidden if section not requested)

### Hero Card (large purple)
- Period chips: Morning / Afternoon / Evening (client-side only, no backend call)
- SVG sparkline — temperature curve (pink line) + UV band (green→pink gradient), drawn from `data.hourly[]`
- Metric row: Temperature · Commute ETA · UV Peak — populated from weather + commute sections

### Commute Card (purple accent)
- Recommended mode label + ETA badge
- Alert text if `data.alerts[]` is non-empty, otherwise "Mode recommended · X km"
- Refresh button → `POST /api/briefing/{id}/commute/refresh`
- Expand button → modal with origin/dest labels, distance, source badge, alternates list

### Breakfast Card (pink accent)
- Recipe name + prep time badge
- Swap button → `POST /api/briefing/{id}/breakfast/refresh` (re-runs breakfast agent)
- Expand button → modal with ingredients, steps list, alternates

### Weather Mini Card
- Condition + high/low line
- UV progress bar (0–11 scale, green→red)
- UV label footer
- Refresh button → `POST /api/briefing/{id}/weather/refresh`

### Headlines Mini Card
- First headline title
- Count footer ("5 loaded")
- Progress bar fills to 100% on load
- Refresh button → `POST /api/briefing/{id}/news/refresh`

### Prep Timer Card
- Recipe name + total minutes
- Progress bar — fills in real time when timer is running
- Start / Pause / Resume / Done button
- Toast notification when timer completes: "Breakfast is ready! 🍳"

### News Feed Panel (right sidebar)
- 5 headline rows, each showing: number · title (bold) · source · time · ↗ icon
- Clicking a row opens `item.url` in a new tab (when URL is present)
- Refresh button at panel header

### Live Commute Map (right sidebar, below news)
- Leaflet 1.9.4 map, OpenStreetMap tiles (no API key required)
- Main route: purple polyline, weight 4
- Alternate routes: dashed grey polylines with mode + ETA tooltip on hover
- Origin marker: purple SVG circle
- Destination marker: pink SVG circle
- Source badge: "Live · TomTom" (green) or "Advisory" (amber)
- Map initialises on first briefing with commute data; reuses the same instance on refresh

### Dashboard Controls (post-briefing)
- Re-run — `POST /api/briefing/{id}/rerun`, re-renders all cards
- Save — `POST /api/briefing/{id}/save`, shows success/error toast
- Edit query — focuses and selects the query textarea

### Detail Modal
- Triggered by any "Expand" button
- Weather detail: current conditions, high/low, UV label, hourly table
- Commute detail: origin/dest labels, distance, source badge, alerts, alternates list
- Breakfast detail: recipe name, prep time, ingredients, numbered steps, alternates
- News detail: all 5 headlines as clickable links with source + time
- Closed by: close button, backdrop click, or Escape key

### Toast Notifications
- All user feedback goes through `showToast(msg, type)` — never `alert()`
- Types: `success` (green), `error` (red), default (neutral)
- Auto-dismisses after 3 seconds

---

## 6. Settings View

Form fields:
- Default location — text input, pre-filled from `GET /api/settings`
- Units — select: Metric (°C, km) / Imperial (°F, miles)
- Default sections — checkboxes: Weather / Commute / News / Breakfast
- Save button — `PUT /api/settings`, shows success/error toast

Settings are loaded from the backend when the Settings view is opened (not on page load).

---

## 7. History View

- Session list loaded from `GET /api/history` when the view opens
- Each row shows: query text (or session ID if no query) · session ID · created time
- Empty state: "Your morning briefings will show up here once you run your first query."
- Error state: "Could not load history."

---

## 8. Loading and Error States

### Loading
- All card text elements get skeleton shimmer classes immediately on submit
- Cards clear their skeletons and render as SSE events arrive
- Refresh buttons show reduced opacity while in-flight

### Error — per card
```
Couldn't load {section}.
```
Text shown in red in the card subtitle. Other cards are unaffected.

### Error — full briefing
Topbar heading changes to "Something went wrong". All cards show error state. Toast shows the server error message.

### Empty states
| Location | Condition | Message |
|---|---|---|
| News feed panel | Before first briefing | "Headlines will appear after your first briefing." |
| Map | Before first briefing | "Run a briefing to see your route here." |
| History list | No sessions | "Your morning briefings will show up here once you run your first query." |
| History list | Load failed | "Could not load history." |

---

## 9. Accessibility

- All interactive elements have `aria-label` attributes
- Error and empty states use text + icon, never color alone
- Modal has `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Toast has `role="alert"` and `aria-live="assertive"`
- News rows have `role="link"` when a URL is present, `role="article"` otherwise
- UV progress bar has `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Keyboard: Escape closes modal; all buttons are focusable

---

## 10. XSS Prevention

All user-supplied or API-supplied strings rendered into `innerHTML` go through `escHtml()`:

```javascript
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
```

Raw API data is never interpolated directly into `innerHTML`.

---

## 11. Color Tokens

| Token | Use |
|---|---|
| Lavender | Page canvas only |
| White | Dashboard shell, secondary cards |
| Purple (deep) | Sidebar, hero card, commute card, active nav, route polyline |
| Pink (soft) | Breakfast card, destination marker, sparkline temperature line |
| Green | UV-safe / live data badge |
| Amber | Advisory data badge |
| Shadows | Soft, diffuse, consistent radius across shell and cards |
