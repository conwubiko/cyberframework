'use strict';

// ── State ────────────────────────────────────────────────────────────────
let lastStatus = null;
let autoRefreshTimer = null;

// ── DOM helpers ──────────────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function setHTML(sel, html) {
  const el = $(sel);
  if (el) el.innerHTML = html;
}

function setText(sel, text) {
  const el = $(sel);
  if (el) el.textContent = text;
}

function setClass(sel, ...classes) {
  const el = $(sel);
  if (el) { el.className = ''; el.classList.add(...classes.filter(Boolean)); }
}

// ── Status banner ────────────────────────────────────────────────────────
function showBanner(msg, type = 'ok') {
  const el = $('#status-banner');
  if (!el) return;
  el.textContent = msg;
  el.className = `show ${type}`;
  setTimeout(() => el.classList.remove('show'), 5000);
}

// ── Colour helpers ───────────────────────────────────────────────────────
function vixColor(value) {
  if (value === null || value === undefined) return '';
  if (value >= 30) return 'alert';
  if (value >= 20) return 'warning';
  return 'safe';
}

function fgColor(score) {
  if (score === null || score === undefined) return '';
  if (score < 12) return 'alert';
  if (score < 25) return 'warning';
  return 'safe';
}

function rsiColor(rsi) {
  if (rsi === null || rsi === undefined) return '';
  if (rsi < 30) return 'alert';
  if (rsi < 40) return 'warning';
  return 'safe';
}

function scoreColor(score) {
  if (score >= 50) return 'alert';
  if (score >= 25) return 'warning';
  return 'safe';
}

function badgeForLevel(level) {
  const map = {
    Low: 'badge-green',
    Normal: 'badge-green',
    Elevated: 'badge-yellow',
    High: 'badge-red',
    Extreme: 'badge-red',
  };
  return `<span class="badge ${map[level] || 'badge-blue'}">${level || '—'}</span>`;
}

function changeChip(pct) {
  if (pct === null || pct === undefined) return '';
  const sign = pct >= 0 ? '+' : '';
  const cls = pct >= 0 ? 'badge-green' : 'badge-red';
  return `<span class="badge ${cls}">${sign}${pct.toFixed(2)}%</span>`;
}

// ── Gauge bar ────────────────────────────────────────────────────────────
function gaugeBar(pct, colorClass) {
  const colorMap = { safe: '#2ecc71', warning: '#f39c12', alert: '#e74c3c' };
  const fill = colorMap[colorClass] || '#3498db';
  return `
    <div class="gauge-bar">
      <div class="gauge-fill" style="width:${Math.min(100, Math.max(0, pct))}%;background:${fill}"></div>
    </div>`;
}

// ── Render VIX card ──────────────────────────────────────────────────────
function renderVix(data) {
  const card = $('#vix-card');
  if (!card) return;

  if (data.error) {
    card.querySelector('.metric-value').innerHTML = '<span class="metric-error">Error</span>';
    card.querySelector('.metric-sub').textContent = data.error;
    return;
  }

  const color = vixColor(data.value);
  card.classList.toggle('triggered', !!data.triggered);
  card.classList.toggle('warning', color === 'warning');

  setHTML('#vix-value', `<span class="metric-value ${color}">${data.value ?? '—'}</span>`);
  setHTML('#vix-sub', `
    ${badgeForLevel(data.level)}
    ${changeChip(data.change_pct)}
    <span>Threshold: ${data.threshold}</span>
  `);
  // gauge: 0–60 range
  card.querySelector('.gauge-bar .gauge-fill').style.width = `${Math.min(100, (data.value / 60) * 100)}%`;
  card.querySelector('.gauge-bar .gauge-fill').style.background =
    { safe: '#2ecc71', warning: '#f39c12', alert: '#e74c3c' }[color] || '#8b949e';
}

// ── Render Fear & Greed card ─────────────────────────────────────────────
function renderFG(data) {
  const card = $('#fg-card');
  if (!card) return;

  if (data.error) {
    card.querySelector('.metric-value').innerHTML = '<span class="metric-error">Error</span>';
    card.querySelector('.metric-sub').textContent = data.error;
    return;
  }

  const color = fgColor(data.score);
  card.classList.toggle('triggered', !!data.triggered);
  card.classList.toggle('warning', color === 'warning');

  setHTML('#fg-value', `<span class="metric-value ${color}">${data.score ?? '—'}</span>`);
  const ratingBadge = `<span class="badge ${color === 'alert' ? 'badge-red' : color === 'warning' ? 'badge-yellow' : 'badge-green'}">${data.rating || '—'}</span>`;
  setHTML('#fg-sub', `${ratingBadge} <span>Threshold: ${data.threshold}</span>`);

  const fill = card.querySelector('.gauge-bar .gauge-fill');
  fill.style.width = `${Math.min(100, data.score)}%`;
  fill.style.background = { safe: '#2ecc71', warning: '#f39c12', alert: '#e74c3c' }[color] || '#8b949e';
}

// ── Render RSI card ──────────────────────────────────────────────────────
function renderRSI(data) {
  const card = $('#rsi-card');
  if (!card) return;

  if (data.error) {
    card.querySelector('.metric-value').innerHTML = '<span class="metric-error">Error</span>';
    return;
  }

  const rsi = data.rsi;
  const color = rsiColor(rsi);
  card.classList.toggle('triggered', !!data.rsi_triggered);
  card.classList.toggle('warning', color === 'warning');

  setHTML('#rsi-value', `<span class="metric-value ${color}">${rsi ?? '—'}</span>`);
  setHTML('#rsi-sub', `
    ${changeChip(data.day_change)} SPY 1d
    <span>Threshold: ${data.rsi_threshold}</span>
  `);

  const fill = card.querySelector('.gauge-bar .gauge-fill');
  fill.style.width = `${Math.min(100, rsi ?? 50)}%`;
  fill.style.background = { safe: '#2ecc71', warning: '#f39c12', alert: '#e74c3c' }[color] || '#8b949e';
}

// ── Render Capitulation panel ────────────────────────────────────────────
const ALL_SIGNALS = [
  { key: 'rsi',   label: (d) => `SPY RSI oversold (${d.rsi?.toFixed(1)} < ${d.rsi_threshold})` },
  { key: 'day',   label: (d) => `SPY 1-day drop (${d.day_change?.toFixed(1)}%)` },
  { key: 'week',  label: (d) => `SPY 5-day drop (${d.week_change?.toFixed(1)}%)` },
  { key: 'vix_s', label: (d) => `VIX spike (${d.vix_spike_pct?.toFixed(1)}%)` },
];

function renderCapitulation(data) {
  const panel = $('#cap-panel');
  if (!panel) return;

  if (data.error) {
    setHTML('#cap-score', '<span class="metric-error">Error</span>');
    return;
  }

  const color = scoreColor(data.score);
  panel.classList.toggle('triggered', !!data.capitulation);

  setHTML('#cap-score', `<span class="score-big ${color}">${data.score ?? 0}<span style="font-size:1.2rem;font-weight:400;color:var(--text-muted)">/100</span></span>`);

  const activeSet = new Set((data.signals || []).map(s => s.toLowerCase()));
  const items = ALL_SIGNALS.map(sig => {
    const isActive = [...activeSet].some(s => s.includes(sig.key.replace('_s', '')));
    return `<li class="signal-item ${isActive ? 'active' : ''}">
      <span class="dot"></span>
      ${sig.label(data)}
    </li>`;
  }).join('');

  setHTML('#cap-signals', items);

  const fill = panel.querySelector('.gauge-bar .gauge-fill');
  fill.style.width = `${Math.min(100, data.score)}%`;
  fill.style.background = { safe: '#2ecc71', warning: '#f39c12', alert: '#e74c3c' }[color] || '#8b949e';
}

// ── Render alert history table ────────────────────────────────────────────
function renderAlerts(alerts) {
  const tbody = $('#alerts-tbody');
  if (!tbody) return;

  if (!alerts.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="no-alerts">No alerts recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = alerts.slice(0, 20).map(a => {
    const ts = new Date(a.timestamp);
    const dateStr = ts.toLocaleDateString();
    const timeStr = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const notifiedBadge = a.notified
      ? '<span class="badge badge-green">Sent</span>'
      : '<span class="badge badge-yellow">Logged</span>';
    return `
      <tr>
        <td>${dateStr}<br><small style="color:var(--text-muted)">${timeStr}</small></td>
        <td><span class="badge badge-blue">${a.alert_type}</span></td>
        <td>${a.value !== null ? a.value : '—'}</td>
        <td style="max-width:300px;word-break:break-word">${a.message}</td>
        <td>${notifiedBadge}</td>
      </tr>`;
  }).join('');
}

// ── Fetch & render full status ────────────────────────────────────────────
async function fetchStatus(isManual = false) {
  const btn = $('#check-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Checking…';
  }

  try {
    const endpoint = isManual ? '/api/check' : '/api/status';
    const method   = isManual ? 'POST' : 'GET';
    const res = await fetch(endpoint, { method });
    const json = await res.json();

    if (!json.ok) throw new Error(json.error || 'Unknown error');

    const data = json.data;
    lastStatus = data;

    renderVix(data.vix || {});
    renderFG(data.fear_greed || {});
    renderCapitulation(data.capitulation || {});

    setText('#last-checked', `Last checked: ${new Date(data.checked_at).toLocaleTimeString()}`);

    const fired = data.alerts_fired || [];
    if (fired.length) {
      const types = fired.map(a => a.type).join(', ');
      showBanner(`Alerts fired: ${types}`, 'warn');
    } else if (isManual) {
      showBanner('Check complete — no thresholds breached.', 'ok');
    }

    // Refresh history after manual check
    if (isManual) fetchAlerts();

  } catch (err) {
    showBanner(`Error: ${err.message}`, 'err');
    console.error('fetchStatus error:', err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '&#128269; Check Now';
    }
  }
}

// ── Fetch alert history ──────────────────────────────────────────────────
async function fetchAlerts() {
  try {
    const res = await fetch('/api/alerts?limit=20');
    const json = await res.json();
    if (json.ok) renderAlerts(json.data);
  } catch (err) {
    console.error('fetchAlerts error:', err);
  }
}

// ── Test notification ────────────────────────────────────────────────────
async function sendTestNotification() {
  const btn = $('#test-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Sending…';
  }

  try {
    const res = await fetch('/api/test-notification', { method: 'POST' });
    const json = await res.json();

    const parts = [];
    if (json.sms_sent)   parts.push('SMS sent');
    if (json.email_sent) parts.push('Email sent');
    if (!parts.length)   parts.push('No notifications sent (check credentials)');

    showBanner(parts.join(' · '), json.sms_sent || json.email_sent ? 'ok' : 'warn');
  } catch (err) {
    showBanner(`Test failed: ${err.message}`, 'err');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '&#128276; Send Test Alert';
    }
  }
}

// ── Settings ─────────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    const json = await res.json();
    if (!json.ok) return;
    const d = json.data;
    const fields = {
      'cfg-vix':        d.VIX_THRESHOLD,
      'cfg-fg':         d.FEAR_GREED_THRESHOLD,
      'cfg-rsi':        d.RSI_THRESHOLD,
      'cfg-cap':        d.CAPITULATION_SCORE_THRESHOLD,
      'cfg-cooldown':   d.ALERT_COOLDOWN_HOURS,
      'cfg-interval':   d.CHECK_INTERVAL_MINUTES,
    };
    Object.entries(fields).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    });
  } catch (err) {
    console.error('loadConfig error:', err);
  }
}

async function saveConfig() {
  const payload = {
    VIX_THRESHOLD:                parseFloat($('#cfg-vix')?.value),
    FEAR_GREED_THRESHOLD:         parseFloat($('#cfg-fg')?.value),
    RSI_THRESHOLD:                parseFloat($('#cfg-rsi')?.value),
    CAPITULATION_SCORE_THRESHOLD: parseFloat($('#cfg-cap')?.value),
    ALERT_COOLDOWN_HOURS:         parseInt($('#cfg-cooldown')?.value),
    CHECK_INTERVAL_MINUTES:       parseInt($('#cfg-interval')?.value),
  };

  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const json = await res.json();
    if (json.ok) showBanner('Settings saved successfully.', 'ok');
    else showBanner('Failed to save settings.', 'err');
  } catch (err) {
    showBanner(`Save error: ${err.message}`, 'err');
  }
}

// ── Auto-refresh ─────────────────────────────────────────────────────────
function startAutoRefresh(intervalMs = 5 * 60 * 1000) {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(() => {
    fetchStatus(false);
    fetchAlerts();
  }, intervalMs);
}

// ── Init ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Bind buttons
  $('#check-btn')?.addEventListener('click', () => fetchStatus(true));
  $('#test-btn')?.addEventListener('click', sendTestNotification);
  $('#save-cfg-btn')?.addEventListener('click', saveConfig);

  // Initial data load
  fetchStatus(false);
  fetchAlerts();
  loadConfig();

  // Auto-refresh every 5 min
  startAutoRefresh(5 * 60 * 1000);
});
