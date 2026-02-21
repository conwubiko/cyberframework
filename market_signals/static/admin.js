'use strict';

// ── Tab switching ────────────────────────────────────────────────────────
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    const target = tab.dataset.tab;
    document.getElementById('tab-recipients').style.display = target === 'recipients' ? '' : 'none';
    document.getElementById('tab-settings').style.display   = target === 'settings'   ? '' : 'none';
  });
});

// ── Recipient helpers ────────────────────────────────────────────────────
function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

function renderRecipients(list) {
  const tbody = document.getElementById('recipients-tbody');
  const countEl = document.getElementById('recipient-count');
  if (!tbody) return;

  const activeCount = list.filter(r => r.active).length;
  if (countEl) countEl.textContent = `(${list.length} total · ${activeCount} active)`;

  if (!list.length) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <span class="icon">📭</span>
          No recipients yet — add one above.
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(r => `
    <tr id="row-${r.id}">
      <td style="color:var(--text-muted)">${r.id}</td>
      <td style="font-weight:600">${escapeHtml(r.name)}</td>
      <td style="color:var(--blue)">${escapeHtml(r.email)}</td>
      <td>
        <label class="toggle-switch" title="${r.active ? 'Click to deactivate' : 'Click to activate'}">
          <input type="checkbox" ${r.active ? 'checked' : ''}
                 onchange="toggleRecipient(${r.id}, this.checked)" />
          <span class="toggle-slider"></span>
        </label>
      </td>
      <td style="color:var(--text-muted);font-size:.8rem">${formatDate(r.created_at)}</td>
      <td>
        <button class="btn-icon" onclick="deleteRecipient(${r.id}, '${escapeHtml(r.email)}')"
                title="Remove">&#128465;</button>
      </td>
    </tr>`).join('');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Load recipients ──────────────────────────────────────────────────────
async function loadRecipients() {
  try {
    const res  = await fetch('/api/recipients');
    const json = await res.json();
    if (json.ok) renderRecipients(json.data);
    else showBanner('Failed to load recipients.', 'err');
  } catch (err) {
    showBanner('Error: ' + err.message, 'err');
  }
}

// ── Add recipient ────────────────────────────────────────────────────────
async function addRecipient() {
  const name  = document.getElementById('new-name')?.value.trim();
  const email = document.getElementById('new-email')?.value.trim();

  if (!name || !email) {
    showBanner('Name and email are required.', 'warn');
    return;
  }

  const btn = document.getElementById('add-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    const res  = await fetch('/api/recipients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email }),
    });
    const json = await res.json();

    if (json.ok) {
      document.getElementById('new-name').value  = '';
      document.getElementById('new-email').value = '';
      showBanner(`Added ${email} successfully.`, 'ok');
      loadRecipients();
    } else {
      showBanner(json.error || 'Failed to add recipient.', 'err');
    }
  } catch (err) {
    showBanner('Error: ' + err.message, 'err');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '&#43; Add';
  }
}

// ── Toggle active ────────────────────────────────────────────────────────
async function toggleRecipient(id, active) {
  try {
    const res  = await fetch(`/api/recipients/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active }),
    });
    const json = await res.json();
    if (json.ok) {
      showBanner(`Recipient ${active ? 'activated' : 'deactivated'}.`, 'ok');
      loadRecipients();
    } else {
      showBanner(json.error || 'Update failed.', 'err');
      loadRecipients(); // re-sync toggle state
    }
  } catch (err) {
    showBanner('Error: ' + err.message, 'err');
    loadRecipients();
  }
}

// ── Delete recipient ─────────────────────────────────────────────────────
async function deleteRecipient(id, email) {
  if (!confirm(`Remove ${email} from alert recipients?`)) return;

  try {
    const res  = await fetch(`/api/recipients/${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (json.ok) {
      showBanner(`Removed ${email}.`, 'ok');
      const row = document.getElementById(`row-${id}`);
      if (row) row.remove();
      loadRecipients();
    } else {
      showBanner(json.error || 'Delete failed.', 'err');
    }
  } catch (err) {
    showBanner('Error: ' + err.message, 'err');
  }
}

// ── Settings (reuse app.js functions) ────────────────────────────────────
document.getElementById('save-cfg-btn')?.addEventListener('click', saveConfig);

// ── Init ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('add-btn')?.addEventListener('click', addRecipient);

  // Allow Enter key in form fields
  ['new-name', 'new-email'].forEach(id => {
    document.getElementById(id)?.addEventListener('keydown', e => {
      if (e.key === 'Enter') addRecipient();
    });
  });

  loadRecipients();
  loadConfig();
});
