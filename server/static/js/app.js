// AI Autofill Agent Frontend Controller
let currentPlan = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initAgentConsole();
  loadUserProfile();
  loadDocuments();
  initRagPlayground();
  initModal();
});

// 1. Tab Switching
function initTabs() {
  const navButtons = document.querySelectorAll('.nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      navButtons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// 2. Logging & Status
function logMessage(msg, level = 'info') {
  const terminal = document.getElementById('log-terminal');
  const entry = document.createElement('div');
  entry.className = `log-entry log-${level}`;
  const timestamp = new Date().toLocaleTimeString();
  entry.innerText = `[${timestamp}] ${msg}`;
  terminal.appendChild(entry);
  terminal.scrollTop = terminal.scrollHeight;
}

function updateAgentStatus(text, dotColor = '#10b981') {
  const dot = document.getElementById('agent-status-dot');
  const label = document.getElementById('agent-status-text');
  if (label) label.innerText = text;
  if (dot) {
    dot.style.background = dotColor;
    dot.style.boxShadow = `0 0 8px ${dotColor}`;
  }
}

// 3. Agent Console Actions
function initAgentConsole() {
  const targetUrlInput = document.getElementById('target-url');
  const btnLoadDemo = document.getElementById('btn-load-demo');
  const btnScan = document.getElementById('btn-scan');
  const btnFill = document.getElementById('btn-fill');
  const btnSubmit = document.getElementById('btn-submit');
  const btnClearLogs = document.getElementById('btn-clear-logs');
  const checkAll = document.getElementById('check-all');

  btnLoadDemo.addEventListener('click', () => {
    targetUrlInput.value = `${window.location.origin}/demo-form`;
    logMessage('Loaded built-in demo job application URL.', 'info');
  });

  btnClearLogs.addEventListener('click', () => {
    document.getElementById('log-terminal').innerHTML = '';
  });

  // Check all / uncheck all
  checkAll.addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    if (currentPlan && currentPlan.decisions) {
      currentPlan.decisions.forEach(d => { d.approved = isChecked; });
      document.querySelectorAll('.field-approve-cb').forEach(cb => { cb.checked = isChecked; });
      logMessage(isChecked ? 'All fields marked for autofill.' : 'All fields skipped.', 'warning');
    }
  });

  // Scan & Plan Autofill
  btnScan.addEventListener('click', async () => {
    const url = targetUrlInput.value.trim();
    if (!url) {
      alert('Please specify a target URL to scan.');
      return;
    }

    const spinner = document.getElementById('scan-spinner');
    spinner.style.display = 'inline-block';
    btnScan.disabled = true;
    updateAgentStatus('Agent Scanning DOM...', '#38bdf8');
    logMessage(`Navigating to ${url} via Playwright...`, 'info');

    try {
      const resp = await fetch('/api/agent/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || 'Scan failed');
      }

      currentPlan = data.plan;
      renderHITLTable(currentPlan);

      logMessage(`Form scanned! Detected ${currentPlan.total_fields} fields. RAG context matched.`, 'success');
      updateAgentStatus('Awaiting Human Review', '#f59e0b');
      btnFill.disabled = false;
      btnSubmit.disabled = false;
    } catch (err) {
      logMessage(`Error scanning page: ${err.message}`, 'error');
      updateAgentStatus('Scan Failed', '#f43f5e');
    } finally {
      spinner.style.display = 'none';
      btnScan.disabled = false;
    }
  });

  // Execute Autofill
  btnFill.addEventListener('click', async () => {
    if (!currentPlan) return;

    const spinner = document.getElementById('fill-spinner');
    spinner.style.display = 'inline-block';
    btnFill.disabled = true;
    updateAgentStatus('Autofilling Form...', '#06b6d4');
    logMessage('Executing browser action pipeline with human-like delays and visual highlights...', 'info');

    try {
      const resp = await fetch('/api/agent/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: currentPlan })
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || 'Autofill execution failed');
      }

      const res = data.execution_result;
      logMessage(`Autofill complete! Filled: ${res.filled}, Skipped: ${res.skipped}, Failed: ${res.failed}`, 'success');
      updateAgentStatus('Form Filled Successfully', '#10b981');
    } catch (err) {
      logMessage(`Error filling form: ${err.message}`, 'error');
      updateAgentStatus('Execution Error', '#f43f5e');
    } finally {
      spinner.style.display = 'none';
      btnFill.disabled = false;
    }
  });

  // Submit Application
  btnSubmit.addEventListener('click', async () => {
    if (!confirm('Are you sure you want the AI agent to submit this application?')) {
      return;
    }
    updateAgentStatus('Submitting Application...', '#f59e0b');
    logMessage('Clicking submit button on active browser session...', 'info');

    try {
      const resp = await fetch('/api/agent/submit', { method: 'POST' });
      const data = await resp.json();
      if (data.submitted) {
        logMessage('Application successfully submitted!', 'success');
        updateAgentStatus('Application Submitted 🎉', '#10b981');
      } else {
        logMessage('Submit button not found or could not be clicked.', 'warning');
      }
    } catch (err) {
      logMessage(`Error submitting: ${err.message}`, 'error');
    }
  });
}

// 4. Render HITL Table
function renderHITLTable(plan) {
  const tbody = document.getElementById('review-table-body');
  const countPill = document.getElementById('fields-count-pill');
  countPill.innerText = `${plan.total_fields} Fields (Avg Confidence: ${Math.round(plan.average_confidence * 100)}%)`;

  if (!plan.decisions || plan.decisions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No fillable form fields detected on this page.</td></tr>`;
    return;
  }

  tbody.innerHTML = '';
  plan.decisions.forEach((d, idx) => {
    const tr = document.createElement('tr');

    // Confidence pill class
    let pillClass = 'pill-high';
    if (d.confidence < 0.75) pillClass = 'pill-low';
    else if (d.confidence < 0.90) pillClass = 'pill-med';

    tr.innerHTML = `
      <td>
        <input type="checkbox" class="field-approve-cb" data-index="${idx}" ${d.approved ? 'checked' : ''}>
      </td>
      <td>
        <div class="field-label-cell">${escapeHtml(d.field_label)}</div>
        <div style="font-size: 11px; color: #64748b;">ID: ${escapeHtml(d.field_id)}</div>
      </td>
      <td>
        <span class="field-type-badge">${escapeHtml(d.element_type)}</span>
      </td>
      <td>
        <input type="text" class="entry-input field-val-input" data-index="${idx}" value="${escapeHtml(d.proposed_value)}">
      </td>
      <td>
        <span class="pill ${pillClass}">${Math.round(d.confidence * 100)}%</span>
      </td>
      <td>
        <span class="source-badge">${escapeHtml(d.source)}</span>
      </td>
      <td>
        <span style="font-size: 12px; color: #94a3b8;">${escapeHtml(d.reasoning)}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Attach event listeners for inline editing and toggling approval
  tbody.querySelectorAll('.field-approve-cb').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const i = parseInt(e.target.dataset.index);
      currentPlan.decisions[i].approved = e.target.checked;
    });
  });

  tbody.querySelectorAll('.field-val-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const i = parseInt(e.target.dataset.index);
      currentPlan.decisions[i].proposed_value = e.target.value;
      currentPlan.decisions[i].edited = true;
    });
  });
}

// 5. User Profile Management
async function loadUserProfile() {
  try {
    const resp = await fetch('/api/profile');
    const profile = await resp.json();

    const fields = [
      'first_name', 'last_name', 'full_name', 'email', 'phone',
      'address_line1', 'city', 'postal_code', 'current_title',
      'current_company', 'years_of_experience', 'work_authorization_us',
      'require_visa_sponsorship', 'notice_period', 'linkedin',
      'github', 'portfolio_website'
    ];

    fields.forEach(f => {
      const el = document.getElementById(`prof-${f}`);
      if (el && profile[f] !== undefined) {
        el.value = profile[f];
      }
    });

    document.getElementById('btn-save-profile').addEventListener('click', async () => {
      const updates = {};
      fields.forEach(f => {
        const el = document.getElementById(`prof-${f}`);
        if (el) updates[f] = el.value;
      });

      const putResp = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (putResp.ok) {
        logMessage('User Profile successfully updated and persisted.', 'success');
        alert('Profile saved!');
      }
    });
  } catch (err) {
    console.error('Failed to load profile', err);
  }
}

// 6. Documents & RAG
async function loadDocuments() {
  try {
    const resp = await fetch('/api/documents');
    const data = await resp.json();
    const container = document.getElementById('doc-list-container');
    container.innerHTML = '';

    data.documents.forEach(doc => {
      const item = document.createElement('div');
      item.className = 'doc-item';
      item.innerHTML = `
        <div>
          <div class="doc-name">${escapeHtml(doc.filename)}</div>
          <div class="doc-meta">${doc.size_kb} KB &bull; Markdown / Text</div>
        </div>
        <span class="pill pill-high">Active Memory</span>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    console.error('Failed to load documents', err);
  }
}

function initRagPlayground() {
  const btn = document.getElementById('btn-run-rag-query');
  const input = document.getElementById('rag-query-input');
  const resultsBox = document.getElementById('rag-results-box');

  btn.addEventListener('click', async () => {
    const q = input.value.trim();
    if (!q) return;

    btn.disabled = true;
    resultsBox.innerHTML = '<span class="dim">Querying RAG memory vectors...</span>';

    try {
      const resp = await fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, top_k: 2 })
      });
      const data = await resp.json();

      if (!data.results || data.results.length === 0) {
        resultsBox.innerHTML = '<span class="dim">No matching chunks found.</span>';
        return;
      }

      resultsBox.innerHTML = '';
      data.results.forEach((r, idx) => {
        const chunkCard = document.createElement('div');
        chunkCard.className = 'rag-chunk-card';
        chunkCard.innerHTML = `
          <div class="rag-chunk-header">
            <strong>Match #${idx + 1} &bull; ${escapeHtml(r.metadata?.filename || 'Document')}</strong>
            <span class="pill pill-high">Relevance: ${Math.round(r.score * 100)}%</span>
          </div>
          <div class="rag-chunk-text">${escapeHtml(r.content)}</div>
        `;
        resultsBox.appendChild(chunkCard);
      });
    } catch (err) {
      resultsBox.innerHTML = `<span class="log-error">Error querying RAG: ${err.message}</span>`;
    } finally {
      btn.disabled = false;
    }
  });
}

// 7. Screenshot Modal
function initModal() {
  const modal = document.getElementById('screenshot-modal');
  const btnOpen = document.getElementById('btn-view-screenshot');
  const btnClose = document.getElementById('btn-close-modal');
  const img = document.getElementById('screenshot-img');

  btnOpen.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/agent/screenshot');
      const data = await resp.json();
      if (data.status === 'success' && data.screenshot_base64) {
        img.src = data.screenshot_base64;
        modal.classList.add('active');
      } else {
        alert(data.message || 'No active browser session.');
      }
    } catch (err) {
      alert('Error capturing screenshot: ' + err.message);
    }
  });

  btnClose.addEventListener('click', () => {
    modal.classList.remove('active');
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
