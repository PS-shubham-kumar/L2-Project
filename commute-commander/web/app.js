'use strict';
/* ============================================================
   Commute Commander — app.js  (refined agentic UI)
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
const timerSub        = $('timer-sub');
const timerFoot       = $('timer-foot');
const timerProgress   = $('timer-progress');
const timerPct        = $('timer-pct');
const timerStartBtn   = $('timer-start-btn');

// News panel
const newsFeedPanel  = $('news-feed-panel');

// Modal
const detailModal   = $('detail-modal');
const modalTitle    = $('modal-title');
const modalBody     = $('modal-body');
const modalClose    = $('modal-close');
const modalBackdrop = $('modal-backdrop');

// Toast
const toastEl = $('toast');

/* ── State ── */
let state = {
  sessionId: null,
  intent: null,
  sections: {},
  timerTotal: 0,
  timerElapsed: 0,
  timerHandle: null,
};

/* ── Utilities ── */
function showToast(msg, type = '') {
  toastEl.textContent = msg;
  toastEl.className = `toast${type ? ' toast-' + type : ''}`;
  toastEl.classList.remove('hidden');
  clearTimeout(toastEl._t);
  toastEl._t = setTimeout(() => toastEl.classList.add('hidden'), 3000);
}

function openModal(title, html) {
  modalTitle.textContent = title;
  modalBody.innerHTML = html;
  detailModal.classList.remove('hidden');
  modalClose.focus();
}
function closeModal() { detailModal.classList.add('hidden'); }

function setLoading(on) {
  submitBtn.disabled = on;
  submitBtn.title = on ? 'Working…' : 'Create briefing';
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
  tempLinePath.setAttribute('d', d);

  const up = uvs.map((u,i) => ({x:px(i), y:pyU(u)}));
  let ud = `M ${up[0].x} ${H} L ${up[0].x} ${up[0].y}`;
  for (let i=0; i<up.length-1; i++) {
    const cx1 = up[i].x + (up[i+1].x-up[i].x)/3;
    const cx2 = up[i+1].x - (up[i+1].x-up[i].x)/3;
    ud += ` C ${cx1} ${up[i].y}, ${cx2} ${up[i+1].y}, ${up[i+1].x} ${up[i+1].y}`;
  }
  ud += ` L ${up[up.length-1].x} ${H} Z`;
  uvBandPath.setAttribute('d', ud);
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
  const mode = d.recommended_mode || 'drive';
  const modeLabel = mode.charAt(0).toUpperCase() + mode.slice(1);
  const eta = d.eta_minutes || '--';
  commuteSubtitle.textContent = d.alerts?.length ? d.alerts[0] : `${modeLabel} recommended`;
  commuteEtaBadge.textContent = `${eta} min`;
  clearSkeleton(metricEta); clearSkeleton(metricEtaSub);
  metricEta.textContent = `${eta} min`;
  metricEtaSub.textContent = modeLabel;
}

function renderBreakfast(payload) {
  const d = payload.data; if (!d) return;
  clearSkeleton(breakfastSubtitle); clearSkeleton(breakfastTimeBadge);
  breakfastSubtitle.textContent = d.recipe_name || 'Quick recipe';
  const prep = d.prep_time_minutes || 0;
  breakfastTimeBadge.textContent = `${prep} min`;
  clearSkeleton(timerSub); clearSkeleton(timerFoot);
  timerSub.textContent = `${d.recipe_name} · ${prep} min`;
  timerFoot.textContent = `0 / ${prep} min`;
  timerProgress.style.width = '0%';
  timerPct.textContent = '0%';
  state.timerTotal = prep * 60;
  state.timerElapsed = 0;
}

function renderNews(payload) {
  const d = payload.data; if (!d?.headlines) return;
  const headlines = d.headlines.slice(0, 5);
  clearSkeleton(newsMiniSub); clearSkeleton(newsMiniFoot);
  newsMiniSub.textContent = headlines[0]?.title || 'No headlines';
  newsMiniFoot.textContent = `${headlines.length} loaded`;

  // Update news progress bar to 100% once loaded
  const np = $('news-progress');
  if (np) { np.style.width = '100%'; np.setAttribute('aria-valuenow', 100); }
  $('news-pct').textContent = 'Live';

  // Render news panel feed
  newsFeedPanel.innerHTML = '';
  headlines.forEach((item, i) => {
    const row = document.createElement('div');
    row.className = 'news-row';
    row.setAttribute('role', 'article');
    row.innerHTML = `
      <span class="news-num">${i+1}</span>
      <div class="news-content">
        <b>${escHtml(item.title)}</b>
        <span>${escHtml(item.source)} · ${formatTime(item.timestamp)}</span>
      </div>`;
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
  $('chip-location').textContent = intent.location;
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

  // Skeletons on cards
  [heroTemp, heroCondition, metricTemp, metricEta, metricUv].forEach(el => setSkeleton(el, true));
  [commuteSubtitle, commuteEtaBadge, breakfastSubtitle, breakfastTimeBadge,
   weatherMiniSub, newsMiniSub, timerSub].forEach(el => setSkeleton(el));

  // Update topbar
  $('topbar-heading').textContent = 'Getting your briefing…';

  try {
    const data = await postBriefing(query, userId);
    state.sessionId = data.session_id;
    state.intent    = data.intent;

    $('topbar-heading').textContent = 'Here\'s your briefing';
    $('topbar-eyebrow').textContent = data.intent?.location || 'Commute Commander';

    renderIntentChips(data.intent);

    const sections = data.sections || {};
    ['weather','commute','breakfast','news'].forEach(sec => {
      if (sections[sec]) dispatchSection(sec, sections[sec]);
    });

    dashControls.classList.remove('hidden');
  } catch (err) {
    $('topbar-heading').textContent = 'Something went wrong';
    showToast(err.message || 'Could not create briefing.', 'error');
    ['weather','commute','breakfast','news'].forEach(sec => renderCardError(sec, null));
  } finally {
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
  const btn = e.target.closest('[data-refresh]');
  if (!btn || !state.sessionId) return;
  const section = btn.dataset.refresh;
  btn.disabled = true; btn.style.opacity = '.5';
  try {
    const payload = await refreshSection(state.sessionId, section);
    dispatchSection(section, payload);
    showToast(`${section} refreshed`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.style.opacity = '';
  }
});

/* ── Expand delegation ── */
document.addEventListener('click', e => {
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
  const mode = d.recommended_mode || 'drive';
  const alerts = (d.alerts||[]).map(a=>`<div class="alert-banner"><span>⚠</span><span>${escHtml(a)}</span></div>`).join('');
  const alts = (d.alternates||[]).map(a=>`<div class="alt-item"><b>${escHtml(a.mode)}</b><span>${escHtml(String(a.eta_minutes))} min</span></div>`).join('');
  return `<h3>Recommended</h3>
    <p>${escHtml(mode.charAt(0).toUpperCase()+mode.slice(1))} · <strong>${escHtml(String(d.eta_minutes))} min</strong></p>
    ${alerts}
    <h3>Alternatives</h3><div class="alt-list">${alts||'<p>No alternates.</p>'}</div>`;
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
  const rows = (d.headlines||[]).map(h => {
    const link = h.url ? `<a href="${escHtml(h.url)}" target="_blank" rel="noopener noreferrer">↗</a>` : '';
    return `<div class="alt-item" style="align-items:flex-start">
      <div style="flex:1;min-width:0"><b>${escHtml(h.title)}</b><br><span>${escHtml(h.source)} · ${formatTime(h.timestamp)}</span></div>${link}</div>`;
  }).join('');
  return `<h3>Top Headlines</h3><div class="alt-list">${rows||'<p>No headlines.</p>'}</div>`;
}

/* ── Breakfast swap ── */
const swapBtn = $('breakfast-swap-btn');
if (swapBtn) swapBtn.addEventListener('click', async () => {
  if (!state.sessionId) return;
  swapBtn.disabled = true;
  try {
    const payload = await refreshSection(state.sessionId, 'breakfast');
    dispatchSection('breakfast', payload);
    showToast('New recipe loaded', 'success');
  } catch(err) { showToast(err.message,'error'); }
  finally { swapBtn.disabled = false; }
});

/* ── Prep timer ── */
timerStartBtn.addEventListener('click', () => {
  if (state.timerHandle) {
    clearInterval(state.timerHandle); state.timerHandle = null;
    timerStartBtn.textContent = 'Resume'; return;
  }
  if (!state.timerTotal) return;
  timerStartBtn.textContent = 'Pause';
  state.timerHandle = setInterval(() => {
    state.timerElapsed++;
    const pct = Math.min(Math.round((state.timerElapsed/state.timerTotal)*100), 100);
    const elMin = Math.floor(state.timerElapsed/60);
    const totMin = Math.round(state.timerTotal/60);
    timerProgress.style.width = `${pct}%`;
    timerProgress.setAttribute('aria-valuenow', pct);
    timerPct.textContent = `${pct}%`;
    timerFoot.textContent = `${elMin} / ${totMin} min`;
    if (state.timerElapsed >= state.timerTotal) {
      clearInterval(state.timerHandle); state.timerHandle = null;
      timerStartBtn.textContent = 'Done!';
      showToast('Breakfast is ready! 🍳', 'success');
    }
  }, 1000);
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

rerunBtn?.addEventListener('click', () => { if (queryInput.value.trim()) form.requestSubmit(); });
editBtn?.addEventListener('click', () => { queryInput.focus(); queryInput.select(); });
saveBtn?.addEventListener('click', async () => {
  if (!state.sessionId) return;
  saveBtn.disabled = true;
  try {
    const res = await fetch(`/api/briefing/${state.sessionId}/save`, {method:'POST'});
    const d = await res.json();
    showToast(d.saved ? 'Briefing saved!' : (d.error?.message||'Not saved — retry?'), d.saved ? 'success' : 'error');
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
      item.innerHTML = `<b>${escHtml(s.query||s.session_id)}</b><span>${escHtml(s.session_id)} · ${s.created_at?formatTime(s.created_at):''}</span>`;
      list.appendChild(item);
    });
  } catch {
    list.innerHTML = '<p class="empty-state">Could not load history.</p>';
  }
}

/* ── Settings form ── */
$('settings-form')?.addEventListener('submit', e => {
  e.preventDefault();
  showToast('Preferences saved!', 'success');
});

/* ── Modal close ── */
modalClose.addEventListener('click', closeModal);
modalBackdrop.addEventListener('click', closeModal);
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !detailModal.classList.contains('hidden')) closeModal();
});
