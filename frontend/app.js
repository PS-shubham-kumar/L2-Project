'use strict';
/* ============================================================
   Commute Commander — app.js
   Production-grade agentic morning briefing UI
   ============================================================ */

const $ = id => document.getElementById(id);

/* ── DOM refs ── */
const form           = $('briefing-form');
const queryInput     = $('briefing-query');
const userIdInput    = $('user-id');
const submitBtn      = $('submit-btn');
const intentConfirm  = $('intent-confirm');
const examplePrompts = $('example-prompts');
const resultsArea    = $('results-area');
const dashControls   = $('dash-controls');

// Hero
const heroTemp       = $('hero-temp');
const heroCondition  = $('hero-condition');
const tempLinePath   = $('temp-line');
const uvBandPath     = $('uv-band');
const metricTemp     = $('metric-temp');
const metricTempSub  = $('metric-temp-sub');
const metricEta      = $('metric-eta');
const metricEtaSub   = $('metric-eta-sub');
const metricUv       = $('metric-uv');
const metricUvSub    = $('metric-uv-sub');

// Action cards
const commuteSubtitle    = $('commute-subtitle');
const commuteEtaBadge    = $('commute-eta-badge');
const breakfastSubtitle  = $('breakfast-subtitle');
const breakfastTimeBadge = $('breakfast-time-badge');

// Mini cards
const weatherMiniSub  = $('weather-mini-sub');
const weatherMiniFoot = $('weather-mini-foot');
const uvProgress      = $('uv-progress');
const uvPct           = $('uv-pct');
const newsMiniSub     = $('news-mini-sub');
const newsMiniFoot    = $('news-mini-foot');
const recipeStepsSub    = $('recipe-steps-sub');
const recipeStepsList   = $('recipe-steps-list');
const recipeStepsFoot   = $('recipe-steps-foot');

// News panel
const newsFeedPanel  = $('news-feed-panel');

// Modal — using strict references to avoid event-bubbling bugs
const detailModal   = $('detail-modal');
const modalTitle    = $('modal-title');
const modalBody     = $('modal-body');
const modalClose    = $('modal-close');
const modalBox      = $('modal-box');
const modalBackdrop = $('modal-backdrop');

// Toast
const toastEl = $('toast');

// Map Modal refs
const mapModal          = $('map-modal');
const mapModalClose     = $('map-modal-close');
const mapModalBackdrop  = $('map-modal-backdrop');
const modalMapEl        = $('modal-map');

/* ── State ── */
let state = {
  sessionId:   null,
  intent:      null,
  sections:    {},
  isModalOpen: false,
};

/* ── Utilities ── */
function showToast(msg, type = '') {
  toastEl.textContent = msg;
  toastEl.className = `toast${type ? ' toast-' + type : ''}`;
  toastEl.classList.remove('hidden');
  clearTimeout(toastEl._t);
  toastEl._t = setTimeout(() => toastEl.classList.add('hidden'), 3500);
}

/* ── Modal helpers (Bug Fix: strict event handling) ── */
function openModal(title, html) {
  modalTitle.textContent = title;
  modalBody.innerHTML = html;
  detailModal.classList.remove('hidden');
  state.isModalOpen = true;
  // Move focus to the close button for accessibility
  requestAnimationFrame(() => modalClose.focus());
}

function closeModal() {
  detailModal.classList.add('hidden');
  state.isModalOpen = false;
}

// Close button — stopPropagation prevents bubbling to data-expand delegation
modalClose.addEventListener('click', e => {
  e.stopPropagation();
  closeModal();
});

// Backdrop — only close if the user clicked the backdrop itself, not the modal box
modalBackdrop.addEventListener('click', e => {
  if (e.target === modalBackdrop) closeModal();
});

// Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (state.isModalOpen) {
      e.preventDefault();
      closeModal();
    }
    if (mapModal && !mapModal.classList.contains('hidden')) {
      e.preventDefault();
      closeMapModal();
    }
  }
});

/* ── Loading ── */
function setLoading(on) {
  submitBtn.disabled = on;
  submitBtn.title = on ? 'Working…' : 'Create briefing';
  submitBtn.setAttribute('aria-busy', on ? 'true' : 'false');
}

function setSkeleton(el, white = false) {
  if (!el) return;
  el.textContent = ' ';
  el.classList.add(white ? 'skeleton-line-white' : 'skeleton-line');
}
function clearSkeleton(el) {
  if (!el) return;
  el.classList.remove('skeleton-line', 'skeleton-line-white');
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatTime(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}); }
  catch { return ''; }
}

/* ── Sparkline ── */
function drawSparkline(hourly) {
  if (!hourly || hourly.length < 2) return;
  const W = 700, H = 120;
  const temps = hourly.map(h => parseFloat(h.temp) || 0);
  const uvs   = hourly.map(h => parseFloat(h.uv_index) || 0);
  const tMin = Math.min(...temps) - 2, tMax = Math.max(...temps) + 2;
  const uvMax = Math.max(...uvs, 1);
  const n = hourly.length;
  const px = i => (i / (n-1)) * W;
  const pyT = t => H - ((t-tMin)/(tMax-tMin))*(H*.75) - H*.1;
  const pyU = u => H - (u/uvMax)*(H*.55) - H*.05;

  const pts = temps.map((t,i) => ({x:px(i), y:pyT(t)}));
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i=0; i<pts.length-1; i++) {
    const cx1 = pts[i].x + (pts[i+1].x-pts[i].x)/3;
    const cx2 = pts[i+1].x - (pts[i+1].x-pts[i].x)/3;
    d += ` C ${cx1} ${pts[i].y}, ${cx2} ${pts[i+1].y}, ${pts[i+1].x} ${pts[i+1].y}`;
  }
  if (tempLinePath) tempLinePath.setAttribute('d', d);

  const up = uvs.map((u,i) => ({x:px(i), y:pyU(u)}));
  let ud = `M ${up[0].x} ${H} L ${up[0].x} ${up[0].y}`;
  for (let i=0; i<up.length-1; i++) {
    const cx1 = up[i].x + (up[i+1].x-up[i].x)/3;
    const cx2 = up[i+1].x - (up[i+1].x-up[i].x)/3;
    ud += ` C ${cx1} ${up[i].y}, ${cx2} ${up[i+1].y}, ${up[i+1].x} ${up[i+1].y}`;
  }
  ud += ` L ${up[up.length-1].x} ${H} Z`;
  if (uvBandPath) uvBandPath.setAttribute('d', ud);
}

/* ── Card renderers ── */
function renderWeather(payload) {
  const d = payload.data; if (!d) return;
  clearSkeleton(heroTemp); clearSkeleton(heroCondition);
  heroTemp.textContent = `${d.temp}°${d.temp_unit||'C'}`;
  heroCondition.textContent = d.condition || '--';

  clearSkeleton(metricTemp); clearSkeleton(metricTempSub);
  metricTemp.textContent = `${d.temp}°`;
  metricTempSub.textContent = d.condition || 'Current';

  clearSkeleton(metricUv); clearSkeleton(metricUvSub);
  metricUv.textContent = d.uv_index !== undefined ? String(d.uv_index) : '--';
  metricUvSub.textContent = 'UV Index';

  clearSkeleton(weatherMiniSub); clearSkeleton(weatherMiniFoot);
  weatherMiniSub.style.color = '';
  weatherMiniSub.textContent = `${d.condition} · H ${d.high}° / L ${d.low}°`;
  weatherMiniFoot.textContent = d.uv_label || '';

  const uv = parseFloat(d.uv_index) || 0;
  const pct = Math.min(Math.round((uv/11)*100), 100);
  uvProgress.style.width = `${pct}%`;
  uvProgress.setAttribute('aria-valuenow', pct);
  uvPct.textContent = `UV ${uv}`;

  if (d.hourly?.length) drawSparkline(d.hourly);
}

function renderCommute(payload) {
  const d = payload.data; if (!d) return;
  clearSkeleton(commuteSubtitle); clearSkeleton(commuteEtaBadge);
  commuteSubtitle.style.color = '';
  const mode      = d.recommended_mode || 'drive';
  const modeLabel = d.mode_label || (mode.charAt(0).toUpperCase() + mode.slice(1));
  const eta       = d.eta_minutes || '--';
  const dist      = d.distance_km ? ` · ${d.distance_km} km` : '';

  // Show origin → destination route if available, otherwise show alert or mode
  let subtitle = '';
  if (d.origin?.label && d.dest?.label) {
    const originShort = d.origin.label.split(',')[0];
    const destShort   = d.dest.label.split(',')[0];
    subtitle = `${originShort} → ${destShort}`;
    if (d.alerts?.length) subtitle += ` · ${d.alerts[0]}`;
  } else if (d.alerts?.length) {
    subtitle = d.alerts[0];
  } else {
    subtitle = `${modeLabel} recommended${dist}`;
  }

  commuteSubtitle.textContent = subtitle;
  commuteEtaBadge.textContent = `${eta} min`;

  clearSkeleton(metricEta); clearSkeleton(metricEtaSub);
  metricEta.textContent    = `${eta} min`;
  metricEtaSub.textContent = modeLabel;

  // Render Leaflet map with real polyline + markers
  renderCommuteMap(d);
}

function renderBreakfast(payload) {
  const d = payload.data; if (!d) return;
  clearSkeleton(breakfastSubtitle); clearSkeleton(breakfastTimeBadge);
  breakfastSubtitle.style.color = '';
  breakfastSubtitle.textContent = d.recipe_name || 'Quick recipe';
  const prep = d.prep_time_minutes || 0;
  breakfastTimeBadge.textContent = `${prep} min`;

  // Recipe Steps mini-card
  if (recipeStepsSub) {
    clearSkeleton(recipeStepsSub);
    recipeStepsSub.style.color = '';
    const steps = d.steps || [];
    const stepCount = steps.length;
    recipeStepsSub.textContent = stepCount
      ? `${d.recipe_name}${d.area ? ' · ' + d.area : ''}`
      : (d.recipe_name || 'Quick recipe');

    if (recipeStepsList && stepCount > 0) {
      recipeStepsList.classList.remove('hidden');
      // Show first 3 steps inline
      recipeStepsList.innerHTML = steps.slice(0, 3).map(
        s => `<li>${escHtml(String(s))}</li>`
      ).join('');
    }

    if (recipeStepsFoot) {
      recipeStepsFoot.textContent = stepCount
        ? `${stepCount} step${stepCount !== 1 ? 's' : ''} · ${prep} min prep`
        : `${prep} min prep`;
    }
  }
}

function renderNews(payload) {
  const d = payload.data; if (!d?.headlines) return;
  const headlines = d.headlines.slice(0, 5);
  clearSkeleton(newsMiniSub); clearSkeleton(newsMiniFoot);
  newsMiniSub.style.color = '';
  newsMiniSub.textContent = headlines[0]?.title || 'No headlines';
  newsMiniFoot.textContent = `${headlines.length} loaded`;

  const np = $('news-progress');
  if (np) { np.style.width = '100%'; np.setAttribute('aria-valuenow', 100); }
  $('news-pct').textContent = 'Live';

  newsFeedPanel.innerHTML = '';
  headlines.forEach((item, i) => {
    const row = document.createElement('div');
    row.className = 'news-row';
    row.setAttribute('role', item.url ? 'link' : 'article');
    if (item.url) {
      row.style.cursor = 'pointer';
      row.title = 'Open article';
      row.addEventListener('click', () => window.open(item.url, '_blank', 'noopener,noreferrer'));
    }
    row.innerHTML = `
      <span class="news-num">${i + 1}</span>
      <div class="news-content">
        <b>${escHtml(item.title)}</b>
        <span>${escHtml(item.source)} · ${formatTime(item.timestamp)}</span>
      </div>
      ${item.url ? '<span style="color:var(--muted);font-size:12px;flex-shrink:0;padding-left:4px">↗</span>' : ''}`;
    newsFeedPanel.appendChild(row);
  });
}

function renderCardError(section, message) {
  const map = {
    weather: weatherMiniSub, commute: commuteSubtitle,
    breakfast: breakfastSubtitle, news: newsMiniSub,
  };
  const el = map[section]; if (!el) return;
  clearSkeleton(el);
  el.textContent = message || `Couldn't load ${section}.`;
  el.style.color = '#b92241';
}

function renderIntentChips(intent) {
  if (!intent?.location) return;

  // Location chip
  const locChip = $('chip-location');
  if (locChip) locChip.textContent = `📍 ${intent.location}`;

  // Destination chip — show only if a destination was extracted
  const destChip = $('chip-destination');
  if (destChip) {
    if (intent.destination) {
      destChip.textContent = `→ ${intent.destination}`;
      destChip.classList.remove('hidden');
    } else {
      destChip.classList.add('hidden');
    }
  }

  // Section chips
  ['weather','commute','news','breakfast'].forEach(sec => {
    const chip = $('chip-' + sec); if (!chip) return;
    intent.sections?.includes(sec)
      ? chip.classList.remove('hidden')
      : chip.classList.add('hidden');
  });

  intentConfirm.classList.remove('hidden');
}

function dispatchSection(section, payload) {
  state.sections[section] = payload;
  if (payload.status === 'error') { renderCardError(section, payload.error?.message); return; }
  switch (section) {
    case 'weather':   renderWeather(payload);   break;
    case 'commute':   renderCommute(payload);   break;
    case 'breakfast': renderBreakfast(payload); break;
    case 'news':      renderNews(payload);      break;
  }
}

/* ════════════════════════════════════════════════════════════
   LEAFLET MAP
   Manages a single Leaflet map instance in #commute-map.
   renderCommuteMap(data) is called by renderCommute() whenever
   fresh commute data arrives.
   ════════════════════════════════════════════════════════════ */
const mapEl         = $('commute-map');
const mapEmptyState = $('map-empty-state');
const mapBadge      = $('map-source-badge');

let _leafletMap     = null;   // L.Map instance (created once)
let _routeLayer     = null;   // L.LayerGroup for route + markers
let _altLayers      = [];     // alternate route polylines

/* Tile layer — OpenStreetMap (no API key required) */
const _TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const _TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

function _ensureMap(lat, lon) {
  if (_leafletMap) return;
  // Hide the empty-state placeholder and show the map div
  if (mapEmptyState) mapEmptyState.classList.add('hidden');

  _leafletMap = L.map('commute-map', {
    zoomControl:       true,
    attributionControl: true,
    scrollWheelZoom:   false,   // don't hijack page scroll
  });

  L.tileLayer(_TILE_URL, {
    attribution: _TILE_ATTR,
    maxZoom: 19,
  }).addTo(_leafletMap);

  _leafletMap.setView([lat, lon], 12);

  // Force Leaflet to recalculate container size (needed when div was hidden/zero-size)
  setTimeout(() => { if (_leafletMap) _leafletMap.invalidateSize(); }, 200);
}

function _makePinIcon(color) {
  /* Tiny SVG circle marker — avoids the default Leaflet image dependency */
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
    <circle cx="11" cy="11" r="9" fill="${color}" stroke="white" stroke-width="2"/>
  </svg>`;
  return L.divIcon({
    html:        svg,
    className:   '',
    iconSize:    [22, 22],
    iconAnchor:  [11, 11],
    popupAnchor: [0, -14],
  });
}

let _ORIGIN_ICON = null;
let _DEST_ICON   = null;

function renderCommuteMap(data) {
  if (!data) return;

  if (!_ORIGIN_ICON) _ORIGIN_ICON = _makePinIcon('#7260c3');
  if (!_DEST_ICON)   _DEST_ICON   = _makePinIcon('#f06a9a');

  const origin   = data.origin || {};
  const dest     = data.dest   || {};
  const polyline = data.polyline || [];
  const source   = data.source   || 'advisory';

  const hasCoords = (
    typeof origin.lat === 'number' && typeof origin.lon === 'number' &&
    typeof dest.lat   === 'number' && typeof dest.lon   === 'number'
  );

  if (!hasCoords) return;

  // Initialise map centred on origin
  _ensureMap(origin.lat, origin.lon);

  // Clear previous route layer
  if (_routeLayer) {
    _routeLayer.clearLayers();
  } else {
    _routeLayer = L.layerGroup().addTo(_leafletMap);
  }
  _altLayers.forEach(l => _leafletMap.removeLayer(l));
  _altLayers = [];

  // ── Main route polyline ────────────────────────────────────
  if (polyline.length >= 2) {
    const routeLine = L.polyline(polyline, {
      color:     '#7260c3',
      weight:    4,
      opacity:   0.85,
      lineJoin:  'round',
    }).addTo(_routeLayer);

    // Fit map to the route bounds with a little padding
    _leafletMap.fitBounds(routeLine.getBounds(), { padding: [20, 20] });
    setTimeout(() => { if (_leafletMap) _leafletMap.invalidateSize(); }, 300);
  } else {
    // No polyline — just set view between the two points
    const mid = [
      (origin.lat + dest.lat) / 2,
      (origin.lon + dest.lon) / 2,
    ];
    _leafletMap.setView(mid, 12);
    setTimeout(() => { if (_leafletMap) _leafletMap.invalidateSize(); }, 300);
  }

  // ── Alternate route polylines (dimmed) ─────────────────────
  (data.alternates || []).forEach(alt => {
    if (!alt.polyline || alt.polyline.length < 2) return;
    const altLine = L.polyline(alt.polyline, {
      color:    '#b4a9dd',
      weight:   2.5,
      opacity:  0.55,
      dashArray: '6 6',
    });
    altLine.bindTooltip(
      `${alt.mode.charAt(0).toUpperCase() + alt.mode.slice(1)}: ${alt.eta_minutes} min`,
      { sticky: true }
    );
    altLine.addTo(_leafletMap);
    _altLayers.push(altLine);
  });

  // ── Origin marker ──────────────────────────────────────────
  L.marker([origin.lat, origin.lon], { icon: _ORIGIN_ICON })
    .bindPopup(`<b>Start</b><br>${origin.label || ''}`)
    .addTo(_routeLayer);

  // ── Destination marker ─────────────────────────────────────
  L.marker([dest.lat, dest.lon], { icon: _DEST_ICON })
    .bindPopup(`<b>Destination</b><br>${dest.label || ''}`)
    .addTo(_routeLayer);

  // ── Source badge ───────────────────────────────────────────
  if (mapBadge) {
    mapBadge.textContent  = source === 'tomtom' ? 'Live · TomTom' : 'Advisory';
    mapBadge.className    = `map-source-badge${source !== 'tomtom' ? ' source-advisory' : ''}`;
    mapBadge.classList.remove('hidden');
  }
}

/* ── API ── */
async function postBriefing(query, userId) {
  const res = await fetch('/api/briefing', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({query, user_id: userId}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Server error');
  return data;
}

async function refreshSection(sessionId, section) {
  const res = await fetch(`/api/briefing/${sessionId}/${section}/refresh`, {method:'POST'});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || 'Refresh failed');
  return data;
}

async function fetchHistory() {
  const res = await fetch('/api/history');
  if (!res.ok) return {sessions:[]};
  return res.json();
}

/* ── SSE streaming briefing ── */
function streamBriefing(sessionId) {
  const es = new EventSource(`/api/briefing/${sessionId}/stream`);
  es.onmessage = e => {
    try {
      const payload = JSON.parse(e.data);
      if (payload.event === 'done') {
        es.close();
        dashControls.classList.remove('hidden');
        setLoading(false);
        return;
      }
      if (payload.section) dispatchSection(payload.section, payload);
    } catch { /* ignore malformed events */ }
  };
  es.onerror = () => {
    es.close();
    dashControls.classList.remove('hidden');
    setLoading(false);
  };
}

/* ── Submit ── */
form.addEventListener('submit', async e => {
  e.preventDefault();
  const query  = queryInput.value.trim();
  const userId = userIdInput.value.trim() || 'guest';
  if (!query) return;

  setLoading(true);
  examplePrompts.classList.add('hidden');
  intentConfirm.classList.add('hidden');
  resultsArea.classList.remove('hidden');
  dashControls.classList.add('hidden');
  newsFeedPanel.innerHTML = '<p class="empty-state">Loading headlines…</p>';

  // Reset card colors to avoid stale error colors from a previous failed run
  [commuteSubtitle, weatherMiniSub, newsMiniSub, breakfastSubtitle, recipeStepsSub].forEach(el => {
    if (el) el.style.color = '';
  });

  // Skeletons on cards
  [heroTemp, heroCondition, metricTemp, metricEta, metricUv].forEach(el => setSkeleton(el, true));
  [commuteSubtitle, commuteEtaBadge, breakfastSubtitle, breakfastTimeBadge,
   weatherMiniSub, newsMiniSub, recipeStepsSub].forEach(el => setSkeleton(el));

  $('topbar-heading').textContent = 'Getting your briefing…';

  try {
    const data = await postBriefing(query, userId);
    state.sessionId = data.session_id;
    state.intent    = data.intent;

    $('topbar-heading').textContent = 'Here\'s your briefing';
    $('topbar-eyebrow').textContent = data.intent?.location || 'Commute Commander';
    renderIntentChips(data.intent);

    // Render sections from the initial POST response first (fast path),
    // then open the SSE stream so any slower agents still arrive as cards.
    const sections = data.sections || {};
    ['weather','commute','breakfast','news'].forEach(sec => {
      if (sections[sec]) dispatchSection(sec, sections[sec]);
    });

    // SSE stream picks up any sections not yet in the POST response
    streamBriefing(data.session_id);
  } catch (err) {
    $('topbar-heading').textContent = 'Something went wrong';
    showToast(err.message || 'Could not create briefing.', 'error');
    ['weather','commute','breakfast','news'].forEach(sec => renderCardError(sec, null));
    setLoading(false);
  }
});

/* ── Example chips ── */
document.querySelectorAll('.example-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    queryInput.value = btn.dataset.query;
    form.requestSubmit();
  });
});

/* ── Refresh delegation ── */
document.addEventListener('click', async e => {
  // Don't process if modal is open to avoid accidental clicks
  if (state.isModalOpen) return;
  const btn = e.target.closest('[data-refresh]');
  if (!btn || !state.sessionId) return;
  const section = btn.dataset.refresh;
  btn.disabled = true; btn.style.opacity = '.5';
  try {
    const payload = await refreshSection(state.sessionId, section);
    dispatchSection(section, payload);
    showToast(`${section} refreshed ✓`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.style.opacity = '';
  }
});

/* ── Expand delegation ── */
document.addEventListener('click', e => {
  // Skip if modal is already open
  if (state.isModalOpen) return;
  const btn = e.target.closest('[data-expand]');
  if (!btn) return;
  const section = btn.dataset.expand;
  const payload = state.sections[section];
  if (!payload) { showToast(`Run a briefing first.`); return; }
  const title = section.charAt(0).toUpperCase() + section.slice(1) + ' Details';
  openModal(title, buildDetailHtml(section, payload));
});

/* ── Modal builders ── */
function buildDetailHtml(section, payload) {
  if (payload.status === 'error') return `<div class="card-error"><span>⚠</span><span>${escHtml(payload.error?.message||'Error')}</span></div>`;
  const d = payload.data;
  switch(section) {
    case 'weather':   return buildWeatherDetail(d);
    case 'commute':   return buildCommuteDetail(d);
    case 'breakfast': return buildBreakfastDetail(d);
    case 'news':      return buildNewsDetail(d);
    default: return '<p>No detail.</p>';
  }
}

function buildWeatherDetail(d) {
  const rows = (d.hourly||[]).map(h =>
    `<div class="alt-item"><b>${escHtml(h.time)}</b><span>${escHtml(h.temp)}° · UV ${escHtml(String(h.uv_index))}</span></div>`
  ).join('');
  return `<h3>Current</h3>
    <p>${escHtml(d.condition)} · ${escHtml(String(d.temp))}°${escHtml(d.temp_unit||'C')}</p>
    <p>High <strong>${escHtml(String(d.high))}°</strong> / Low <strong>${escHtml(String(d.low))}°</strong></p>
    <h3>UV</h3><p>UV ${escHtml(String(d.uv_index))} — ${escHtml(d.uv_label||'')}</p>
    <h3>Hourly</h3><div class="alt-list">${rows||'<p>No data.</p>'}</div>`;
}

function buildCommuteDetail(d) {
  const mode     = d.recommended_mode || 'drive';
  const label    = d.mode_label || (mode.charAt(0).toUpperCase() + mode.slice(1));
  const dist     = d.distance_km ? `${d.distance_km} km` : '';
  const src      = d.source === 'tomtom' ? '🟢 Live data via TomTom' : '🟡 Advisory estimate';
  const alerts   = (d.alerts || []).map(a =>
    `<div class="alert-banner"><span>⚠</span><span>${escHtml(a)}</span></div>`).join('');
  const alts     = (d.alternates || []).map(a =>
    `<div class="alt-item">
       <b>${escHtml(a.mode.charAt(0).toUpperCase() + a.mode.slice(1))}</b>
       <span>${escHtml(String(a.eta_minutes))} min${a.distance_km ? ' · ' + a.distance_km + ' km' : ''}</span>
     </div>`).join('');
  const origin   = d.origin?.label ? `<p>From: <strong>${escHtml(d.origin.label)}</strong></p>` : '';
  const destTxt  = d.dest?.label   ? `<p>To: <strong>${escHtml(d.dest.label)}</strong></p>`     : '';

  return `
    <h3>Recommended Route</h3>
    ${origin}${destTxt}
    <p>${escHtml(label)} · <strong>${escHtml(String(d.eta_minutes))} min</strong>${dist ? ' · ' + escHtml(dist) : ''}</p>
    <p style="font-size:10px;color:var(--muted)">${src}</p>
    ${alerts}
    <h3>Alternatives</h3>
    <div class="alt-list">${alts || '<p>No alternates.</p>'}</div>`;
}

function buildBreakfastDetail(d) {
  const steps = (d.steps||[]).map(s=>`<li>${escHtml(s)}</li>`).join('');
  const alts = (d.alternates||[]).map(a=>`<div class="alt-item"><b>${escHtml(a.recipe_name)}</b><span>${escHtml(String(a.prep_time_minutes))} min</span></div>`).join('');
  const ings = (d.ingredients_used||[]).map(i=>escHtml(i)).join(', ');
  return `<h3>${escHtml(d.recipe_name||'Recipe')}</h3>
    <p>Prep: <strong>${escHtml(String(d.prep_time_minutes))} min</strong></p>
    <p>Ingredients: ${ings||'—'}</p>
    <h3>Steps</h3><ol>${steps||'<li>No steps.</li>'}</ol>
    <h3>Alternatives</h3><div class="alt-list">${alts||'<p>None.</p>'}</div>`;
}

function buildNewsDetail(d) {
  const rows = (d.headlines || []).map(h => {
    const titleHtml = h.url
      ? `<a href="${escHtml(h.url)}" target="_blank" rel="noopener noreferrer"
            style="color:var(--ink);text-decoration:none;font-weight:600">${escHtml(h.title)}</a>`
      : `<b>${escHtml(h.title)}</b>`;
    const extLink = h.url
      ? `<a href="${escHtml(h.url)}" target="_blank" rel="noopener noreferrer"
            aria-label="Open article" style="color:var(--muted);font-size:13px;flex-shrink:0">↗</a>`
      : '';
    return `<div class="alt-item" style="align-items:flex-start;gap:10px">
      <div style="flex:1;min-width:0">
        ${titleHtml}<br>
        <span style="font-size:9.5px;color:var(--muted)">${escHtml(h.source)} · ${formatTime(h.timestamp)}</span>
      </div>${extLink}
    </div>`;
  }).join('');
  return `<h3>Top Headlines</h3><div class="alt-list">${rows || '<p>No headlines.</p>'}</div>`;
}

/* ── Breakfast swap ── */
const swapBtn = $('breakfast-swap-btn');
if (swapBtn) swapBtn.addEventListener('click', async () => {
  if (!state.sessionId) return;
  swapBtn.disabled = true;
  try {
    const payload = await refreshSection(state.sessionId, 'breakfast');
    dispatchSection('breakfast', payload);
    showToast('New recipe loaded ✓', 'success');
  } catch(err) { showToast(err.message,'error'); }
  finally { swapBtn.disabled = false; }
});

/* ── Period chips ── */
document.querySelectorAll('.period-chips .chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.period-chips .chip').forEach(b => b.classList.remove('chip-active'));
    btn.classList.add('chip-active');
  });
});

/* ── Dashboard controls ── */
const rerunBtn = $('rerun-btn');
const saveBtn  = $('save-btn');
const editBtn  = $('edit-btn');

rerunBtn?.addEventListener('click', async () => {
  if (!state.sessionId) { if (queryInput.value.trim()) form.requestSubmit(); return; }
  rerunBtn.disabled = true;
  try {
    const res  = await fetch(`/api/briefing/${state.sessionId}/rerun`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Re-run failed');
    const sections = data.sections || {};
    ['weather', 'commute', 'breakfast', 'news'].forEach(sec => {
      if (sections[sec]) dispatchSection(sec, sections[sec]);
    });
    showToast('Briefing refreshed ✓', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    rerunBtn.disabled = false;
  }
});
editBtn?.addEventListener('click', () => { queryInput.focus(); queryInput.select(); });
saveBtn?.addEventListener('click', async () => {
  if (!state.sessionId) return;
  saveBtn.disabled = true;
  try {
    const res = await fetch(`/api/briefing/${state.sessionId}/save`, {method:'POST'});
    const d = await res.json();
    showToast(d.saved ? 'Briefing saved! ✓' : (d.error?.message||'Not saved — retry?'), d.saved ? 'success' : 'error');
  } catch { showToast('Save failed — retry?','error'); }
  finally { saveBtn.disabled = false; }
});

/* ── Sidebar view switching ── */
const VIEWS = ['ask','history','settings'];

function switchView(name) {
  VIEWS.forEach(v => {
    $('view-' + v)?.classList.toggle('hidden', v !== name);
    $('view-' + v)?.classList.toggle('active-view', v === name);
  });
  document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === name);
  });

  const headings = {
    ask:      ['Commute Commander', 'Good morning — what\'s your plan?'],
    history:  ['Commute Commander', 'Briefing History'],
    settings: ['Commute Commander', 'Settings'],
  };
  const [eyebrow, heading] = headings[name] || headings.ask;
  $('topbar-eyebrow').textContent = eyebrow;
  $('topbar-heading').textContent = heading;

  if (name === 'history') loadHistory();
}

document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.view === 'signout') { showToast('Signed out.'); return; }
    switchView(btn.dataset.view);
  });
});

async function deleteHistoryItem(sessionId, itemEl) {
  if (!confirm('Are you sure you want to delete this briefing from history?')) return;
  try {
    const res = await fetch(`/api/history/${sessionId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to delete');
    
    itemEl.style.opacity = '0';
    itemEl.style.transform = 'scale(0.9)';
    setTimeout(() => {
      itemEl.remove();
      const list = $('history-list');
      if (!list.querySelector('.history-item')) {
        list.innerHTML = '<p class="empty-state">Your morning briefings will show up here once you run your first query.</p>';
      }
    }, 200);
    showToast('Briefing deleted from history ✓', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function clearAllHistory() {
  if (!confirm('Are you sure you want to clear ALL briefing history? This cannot be undone.')) return;
  try {
    const res = await fetch('/api/history', { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to clear history');
    
    const list = $('history-list');
    list.innerHTML = '<p class="empty-state">Your morning briefings will show up here once you run your first query.</p>';
    showToast('Briefing history cleared ✓', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadHistory() {
  const list = $('history-list');
  list.innerHTML = '<p class="empty-state">Loading…</p>';
  try {
    const data = await fetchHistory();
    const sessions = data.sessions || [];
    if (!sessions.length) {
      list.innerHTML = '<p class="empty-state">Your morning briefings will show up here once you run your first query.</p>';
      return;
    }
    list.innerHTML = '';
    sessions.forEach(s => {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.setAttribute('role','button'); item.setAttribute('tabindex','0');
      item.innerHTML = `
        <div class="history-info">
          <b>${escHtml(s.query||s.session_id)}</b>
          <span>${escHtml(s.session_id)} · ${s.created_at?formatTime(s.created_at):''}</span>
        </div>
        <button class="history-delete-btn" aria-label="Delete history item" data-id="${s.session_id}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      `;
      
      item.addEventListener('click', e => {
        if (e.target.closest('.history-delete-btn')) return;
        queryInput.value = s.query || '';
        switchView('ask');
        form.requestSubmit();
      });
      
      item.querySelector('.history-delete-btn').addEventListener('click', e => {
        e.stopPropagation();
        deleteHistoryItem(s.session_id, item);
      });
      
      list.appendChild(item);
    });
  } catch (err) {
    list.innerHTML = '<p class="empty-state">Could not load history.</p>';
  }
}

/* ── Settings ── */
async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    if (!res.ok) return;
    const s = await res.json();
    const locEl = $('setting-location');
    const unitsEl = $('setting-units');
    if (locEl) locEl.value = s.default_location || '';
    if (unitsEl) unitsEl.value = s.units || 'metric';
    document.querySelectorAll('#settings-form input[type=checkbox]').forEach(cb => {
      cb.checked = (s.default_sections || []).includes(cb.value);
    });
  } catch { /* silently ignore */ }
}

$('settings-form')?.addEventListener('submit', async e => {
  e.preventDefault();
  const sections = [...document.querySelectorAll('#settings-form input[type=checkbox]:checked')]
    .map(cb => cb.value);
  const body = {
    default_location: $('setting-location')?.value.trim() || '',
    units:            $('setting-units')?.value || 'metric',
    default_sections: sections,
  };
  try {
    const res = await fetch('/api/settings', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    showToast(res.ok ? 'Preferences saved! ✓' : 'Save failed — retry?', res.ok ? 'success' : 'error');
  } catch { showToast('Save failed — retry?', 'error'); }
});

// Pre-fill settings when the view opens
document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
  if (btn.dataset.view === 'settings') btn.addEventListener('click', loadSettings, {once: false});
});

/* ──────────────────────────────────────────────────────────────
   COMMUTE NOW DRAWER (OLA/UBER STYLE)
────────────────────────────────────────────────────────────── */
const commuteDrawer     = $('commute-drawer');
const drawerPanel       = $('drawer-panel');
const drawerClose       = $('drawer-close');
const drawerBackdrop    = $('drawer-backdrop');
const drawerForm        = $('drawer-form');
const drawerFrom        = $('drawer-from');
const drawerTo          = $('drawer-to');
const drawerSubmit      = $('drawer-submit');
const drawerResults     = $('drawer-results');
const drawerEta         = $('drawer-eta');
const drawerDistance    = $('drawer-distance');
const drawerSource      = $('drawer-source');
const drawerAlerts      = $('drawer-alerts');

let _drawerMap          = null;
let _drawerRouteLayer   = null;
let _drawerAltLayers    = [];
let _activeCommuteMode  = 'drive';

function openCommuteDrawer() {
  if (state.intent) {
    if (state.intent.location && state.intent.location !== 'current location') {
      drawerFrom.value = state.intent.location;
    }
    if (state.intent.destination) {
      drawerTo.value = state.intent.destination;
    }
  }
  commuteDrawer.classList.remove('hidden');
  
  // Initialize map with a small delay so container size is ready
  setTimeout(() => {
    if (!_drawerMap) {
      _drawerMap = L.map('drawer-map', {
        zoomControl:       true,
        attributionControl: true,
        scrollWheelZoom:   false,
      });
      L.tileLayer(_TILE_URL, {
        attribution: _TILE_ATTR,
        maxZoom: 19,
      }).addTo(_drawerMap);
      _drawerMap.setView([20.5937, 78.9629], 5);
    }
    _drawerMap.invalidateSize();
  }, 200);
}

function closeCommuteDrawer() {
  commuteDrawer.classList.add('hidden');
}

// Click commute card to open
$('commute-card')?.addEventListener('click', e => {
  if (e.target.closest('.card-actions')) return;
  openCommuteDrawer();
});

drawerClose?.addEventListener('click', closeCommuteDrawer);
drawerBackdrop?.addEventListener('click', closeCommuteDrawer);

// Handle mode selection buttons
document.querySelectorAll('#drawer-modes .drawer-mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#drawer-modes .drawer-mode-btn').forEach(b => {
      b.classList.remove('mode-active');
      b.setAttribute('aria-checked', 'false');
    });
    btn.classList.add('mode-active');
    btn.setAttribute('aria-checked', 'true');
    _activeCommuteMode = btn.dataset.mode;

    // Auto-refresh route calculation if locations are already filled
    if (drawerFrom.value.trim() && drawerTo.value.trim()) {
      calculateDrawerRoute();
    }
  });
});

async function calculateDrawerRoute() {
  const fromVal = drawerFrom.value.trim();
  const toVal   = drawerTo.value.trim();
  if (!fromVal || !toVal) return;

  drawerSubmit.disabled = true;
  drawerSubmit.textContent = 'Calculating route…';
  
  try {
    const res = await fetch('/api/commute', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        from: fromVal,
        to: toVal,
        mode: _activeCommuteMode
      })
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || 'Failed to fetch commute path.');
    
    if (payload.status === 'error') {
      throw new Error(payload.error?.message || 'Error occurred during route calculation.');
    }

    const data = payload.data || payload;
    
    // Render text metrics
    drawerEta.textContent      = `${data.eta_minutes || '--'} min`;
    drawerDistance.textContent = `${data.distance_km || '--'} km`;
    drawerSource.textContent   = data.source || 'advisory';
    
    // Render alerts
    drawerAlerts.innerHTML = '';
    (data.alerts || []).forEach(a => {
      const banner = document.createElement('div');
      banner.className = 'alert-banner';
      banner.innerHTML = `<span>⚠</span><span>${escHtml(a)}</span>`;
      drawerAlerts.appendChild(banner);
    });

    // Show results section
    drawerResults.classList.remove('hidden');
    
    // Draw Leaflet Route Map
    setTimeout(() => {
      if (_drawerMap) {
        _drawerMap.invalidateSize();
        
        const origin   = data.origin || {};
        const dest     = data.dest   || {};
        const polyline = data.polyline || [];
        
        // Clear previous layer
        if (_drawerRouteLayer) {
          _drawerRouteLayer.clearLayers();
        } else {
          _drawerRouteLayer = L.layerGroup().addTo(_drawerMap);
        }
        _drawerAltLayers.forEach(l => _drawerMap.removeLayer(l));
        _drawerAltLayers = [];

        // Draw main route polyline
        if (polyline.length >= 2) {
          const routeLine = L.polyline(polyline, {
            color:     '#7260c3',
            weight:    5,
            opacity:   0.85,
            lineJoin:  'round',
          }).addTo(_drawerRouteLayer);
          
          _drawerMap.fitBounds(routeLine.getBounds(), { padding: [35, 35] });
        } else {
          _drawerMap.setView([origin.lat || 20, origin.lon || 78], 12);
        }

        // Draw pins
        const originIcon = _ORIGIN_ICON || _makePinIcon('#7260c3');
        const destIcon   = _DEST_ICON || _makePinIcon('#f06a9a');

        if (origin.lat && origin.lon) {
          L.marker([origin.lat, origin.lon], { icon: originIcon })
            .bindPopup(`<b>Start</b><br>${origin.label || ''}`)
            .addTo(_drawerRouteLayer);
        }
        if (dest.lat && dest.lon) {
          L.marker([dest.lat, dest.lon], { icon: destIcon })
            .bindPopup(`<b>Destination</b><br>${dest.label || ''}`)
            .addTo(_drawerRouteLayer);
        }
      }
    }, 200);
    
    showToast('Commute route updated! ✓', 'success');

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    drawerSubmit.disabled = false;
    drawerSubmit.textContent = 'Get Live Route';
  }
}

drawerForm?.addEventListener('submit', e => {
  e.preventDefault();
  calculateDrawerRoute();
});

/* ──────────────────────────────────────────────────────────────
   CENTERED POPUP MAP MODAL
   ────────────────────────────────────────────────────────────── */
let _modalMap        = null;
let _modalRouteLayer = null;
let _modalAltLayers  = [];

function openMapModal() {
  const payload = state.sections['commute'];
  if (!payload || payload.status !== 'success' || !payload.data) {
    showToast('Run a commute briefing first.');
    return;
  }
  
  const data = payload.data;
  const origin   = data.origin || {};
  const dest     = data.dest   || {};
  const polyline = data.polyline || [];

  const hasCoords = (
    typeof origin.lat === 'number' && typeof origin.lon === 'number' &&
    typeof dest.lat   === 'number' && typeof dest.lon   === 'number'
  );

  if (!hasCoords) return;

  mapModal?.classList.remove('hidden');

  setTimeout(() => {
    if (!_modalMap) {
      _modalMap = L.map('modal-map', {
        zoomControl:       true,
        attributionControl: true,
        scrollWheelZoom:   true,
      });
      L.tileLayer(_TILE_URL, {
        attribution: _TILE_ATTR,
        maxZoom: 19,
      }).addTo(_modalMap);
    }
    _modalMap.invalidateSize();

    // Clear previous layer
    if (_modalRouteLayer) {
      _modalRouteLayer.clearLayers();
    } else {
      _modalRouteLayer = L.layerGroup().addTo(_modalMap);
    }
    _modalAltLayers.forEach(l => _modalMap.removeLayer(l));
    _modalAltLayers = [];

    // Draw main route polyline
    if (polyline.length >= 2) {
      const routeLine = L.polyline(polyline, {
        color:     '#7260c3',
        weight:    5,
        opacity:   0.85,
        lineJoin:  'round',
      }).addTo(_modalRouteLayer);
      
      _modalMap.fitBounds(routeLine.getBounds(), { padding: [40, 40] });
    } else {
      _modalMap.setView([origin.lat, origin.lon], 12);
    }

    // Draw alternates
    (data.alternates || []).forEach(alt => {
      if (!alt.polyline || alt.polyline.length < 2) return;
      const altLine = L.polyline(alt.polyline, {
        color:    '#b4a9dd',
        weight:   3,
        opacity:  0.65,
        dashArray: '6 6',
      });
      altLine.bindTooltip(
        `${alt.mode.charAt(0).toUpperCase() + alt.mode.slice(1)}: ${alt.eta_minutes} min`,
        { sticky: true }
      );
      altLine.addTo(_modalMap);
      _modalAltLayers.push(altLine);
    });

    // Draw pins
    const originIcon = _ORIGIN_ICON || _makePinIcon('#7260c3');
    const destIcon   = _DEST_ICON || _makePinIcon('#f06a9a');

    L.marker([origin.lat, origin.lon], { icon: originIcon })
      .bindPopup(`<b>Start</b><br>${origin.label || ''}`)
      .addTo(_modalRouteLayer);

    L.marker([dest.lat, dest.lon], { icon: destIcon })
      .bindPopup(`<b>Destination</b><br>${dest.label || ''}`)
      .addTo(_modalRouteLayer);

  }, 200);
}

function closeMapModal() {
  mapModal?.classList.add('hidden');
}

// Click live commute map to open centered modal (uses capture phase to bypass Leaflet's stopPropagation)
mapEl?.addEventListener('click', e => {
  if (e.target.closest('.leaflet-control')) return;
  const payload = state.sections['commute'];
  if (payload && payload.status === 'success' && payload.data) {
    openMapModal();
  }
}, true);

mapModalClose?.addEventListener('click', closeMapModal);
mapModalBackdrop?.addEventListener('click', closeMapModal);

// Wire up Clear History Button
$('clear-history-btn')?.addEventListener('click', clearAllHistory);

