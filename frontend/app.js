// ── Init ──────────────────────────────────────────────────────────────────
mermaid.initialize({ startOnLoad: true, theme: 'default' });

let currentData = null;

const TOKEN_TYPE_CATEGORIES = {
  SELECT: 'KEYWORD', FROM: 'KEYWORD', WHERE: 'KEYWORD',
  AND: 'KEYWORD', OR: 'KEYWORD', NOT: 'KEYWORD',
  KEYWORD: 'KEYWORD',
  IDENTIFIER: 'IDENTIFIER',
  COMPARATOR: 'COMPARATOR', OPERATOR: 'OPERATOR',
  NUMBER: 'NUMBER', INTEGER: 'NUMBER', FLOAT: 'NUMBER',
  STRING: 'STRING', LITERAL: 'LITERAL',
  COMMA: 'SYMBOL', SEMICOLON: 'SYMBOL', SYMBOL: 'SYMBOL', STAR: 'SYMBOL',
};

const TAC_EXPLANATIONS = {
  SCAN: '← reads table',
  FILTER: '← applies WHERE',
  PROJECT: '← keeps columns',
  AND: '← combine AND',
  OR: '← combine OR',
};

// ── Gutter ────────────────────────────────────────────────────────────────
const sqlInput = document.getElementById('sql-input');
const gutter   = document.getElementById('editor-gutter');
const charCount = document.getElementById('char-count');

function updateGutter() {
  const lines = sqlInput.value.split('\n').length;
  gutter.textContent = Array.from({length: lines}, (_, i) => i + 1).join('\n');
  charCount.textContent = `${sqlInput.value.length} chars · ${lines} line${lines > 1 ? 's' : ''}`;
}
sqlInput.addEventListener('input', updateGutter);
updateGutter();

// ── Keyboard shortcut ─────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    document.getElementById('run-btn').click();
  }
});

// ── Tabs ──────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    btn.setAttribute('aria-selected','true');
    document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
  });
});

// ── Sample queries ────────────────────────────────────────────────────────
document.querySelectorAll('.sample-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    sqlInput.value = chip.dataset.query;
    updateGutter();
    sqlInput.focus();
  });
});

// ── Plan type toggle ──────────────────────────────────────────────────────
document.querySelectorAll('input[name="planType"]').forEach(r => {
  r.addEventListener('change', () => { if (currentData) renderPlan(currentData); });
});

// ── Copy buttons ──────────────────────────────────────────────────────────
function makeCopyBtn(btnId, getContent) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const text = getContent();
    if (!text) return;
    await navigator.clipboard.writeText(text).catch(() => {});
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = '⎘ Copy'; btn.classList.remove('copied'); }, 1800);
  });
}

makeCopyBtn('copy-tokens', () => {
  if (!currentData?.tokens) return '';
  return JSON.stringify(currentData.tokens, null, 2);
});
makeCopyBtn('copy-ast', () => {
  if (!currentData?.ast) return '';
  return JSON.stringify(currentData.ast, null, 2);
});
makeCopyBtn('copy-tac', () => {
  if (!currentData?.tac) return '';
  return currentData.tac.join('\n');
});

// ── Pipeline stages ───────────────────────────────────────────────────────
const STAGES = ['lexer','parser','semantic','tac','plan'];

function resetPipeline() {
  STAGES.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    el.classList.remove('active','done','error-stage');
  });
}

function activateStage(name) {
  // mark previous as done
  const idx = STAGES.indexOf(name);
  STAGES.slice(0, idx).forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    el.classList.remove('active'); el.classList.add('done');
  });
  const el = document.getElementById(`stage-${name}`);
  el.classList.remove('done','error-stage');
  el.classList.add('active');
}

function finishPipeline(success) {
  STAGES.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    el.classList.remove('active');
    if (success) el.classList.add('done');
  });
  if (!success) {
    document.getElementById('stage-semantic').classList.add('error-stage');
  }
}

async function animatePipeline(data) {
  resetPipeline();
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const hasSemantic = !!data.semantic;
  const hasTac = data.tac?.length > 0;
  const hasPlan = !!data.plan;

  activateStage('lexer');  await delay(300);
  activateStage('parser'); await delay(300);
  activateStage('semantic'); await delay(300);

  if (!hasTac) {
    STAGES.slice(0,2).forEach(s => { const e=document.getElementById(`stage-${s}`); e.classList.remove('active'); e.classList.add('done'); });
    document.getElementById('stage-semantic').classList.remove('active');
    document.getElementById('stage-semantic').classList.add('error-stage');
    return;
  }

  activateStage('tac'); await delay(300);
  activateStage('plan'); await delay(300);
  finishPipeline(true);
}

// ── Main compile ──────────────────────────────────────────────────────────
document.getElementById('run-btn').addEventListener('click', async () => {
  const query = sqlInput.value.trim();
  if (!query) return;

  const btn = document.getElementById('run-btn');
  const icon = btn.querySelector('.btn-icon');
  const statusBadge = document.getElementById('status-badge');

  btn.disabled = true;
  icon.textContent = '↻';
  icon.classList.add('spinning');
  statusBadge.className = 'status-badge hidden';
  resetPipeline();

  try {
    const res = await fetch('/api/compile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    currentData = data;
    await animatePipeline(data);
    renderDashboard(data);

    if (data.error && !data.tac?.length) {
      showStatus(false, data.error);
    } else {
      showStatus(true, 'Compiled successfully');
      flashSuccess();
    }
  } catch (err) {
    showStatus(false, 'Server unreachable');
    resetPipeline();
  } finally {
    btn.disabled = false;
    icon.textContent = '▶';
    icon.classList.remove('spinning');
  }
});

function showStatus(ok, msg) {
  const badge = document.getElementById('status-badge');
  badge.textContent = (ok ? '✓ ' : '✗ ') + msg;
  badge.className = `status-badge ${ok ? 'success-badge' : 'error-badge'}`;
}

function flashSuccess() {
  const el = document.getElementById('success-flash');
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 600);
}

// ── Render Dashboard ──────────────────────────────────────────────────────
function renderDashboard(data) {
  renderTokens(data);
  renderAST(data);
  renderSemantic(data);
  renderTAC(data);
  if (data.plan) renderPlan(data);
}

// Tokens
function renderTokens(data) {
  const grid = document.getElementById('tokens-grid');
  if (!data.tokens?.length) return;
  grid.innerHTML = '';
  data.tokens.forEach((t, i) => {
    const cat = TOKEN_TYPE_CATEGORIES[t.type] || t.type;
    const chip = document.createElement('div');
    chip.className = `token-chip ${cat}`;
    chip.style.animationDelay = `${i * 0.04}s`;
    chip.innerHTML = `<span class="token-type">${t.type}</span><span class="token-val">${escHtml(t.value)}</span>`;
    grid.appendChild(chip);
  });
}

// AST
function renderAST(data) {
  const out = document.getElementById('ast-output');
  if (data.ast) {
    out.textContent = JSON.stringify(data.ast, null, 2);
  } else {
    out.innerHTML = `<span class="empty-state-inline">No AST (parse error)</span>`;
  }
}

// Semantic
function renderSemantic(data) {
  const banner  = document.getElementById('semantic-status');
  const errSec  = document.getElementById('errors-section');
  const warnSec = document.getElementById('warnings-section');
  const validDet = document.getElementById('sem-valid-details');
  const errList = document.getElementById('semantic-errors');
  const warnList = document.getElementById('semantic-warnings');

  errSec.style.display = 'none';
  warnSec.style.display = 'none';
  validDet.style.display = 'none';

  if (!data.semantic) {
    banner.className = 'semantic-banner invalid';
    banner.innerHTML = `<span class="banner-icon">✗</span><span class="banner-text">Pipeline halted — ${escHtml(data.error || 'Parse error')}</span>`;
    errList.innerHTML = data.error ? `<li>${escHtml(data.error)}</li>` : '';
    errSec.style.display = 'block';
    return;
  }

  const sem = data.semantic;
  if (sem.status === 'VALID') {
    banner.className = 'semantic-banner valid';
    banner.innerHTML = `<span class="banner-icon">✓</span><span class="banner-text">Semantically valid — all checks passed</span>`;
    validDet.style.display = 'block';
  } else {
    banner.className = 'semantic-banner invalid';
    banner.innerHTML = `<span class="banner-icon">✗</span><span class="banner-text">Semantic errors found</span>`;
  }

  if (sem.errors?.length) {
    errList.innerHTML = sem.errors.map(e => `<li>${escHtml(e)}</li>`).join('');
    errSec.style.display = 'block';
  }
  if (sem.warnings?.length) {
    warnList.innerHTML = sem.warnings.map(w => `<li>${escHtml(w)}</li>`).join('');
    warnSec.style.display = 'block';
  }
}

// TAC
function renderTAC(data) {
  const container = document.getElementById('tac-container');
  if (!data.tac?.length) return;
  container.innerHTML = '';
  data.tac.forEach((line, i) => {
    let comment = '';
    for (const [kw, exp] of Object.entries(TAC_EXPLANATIONS)) {
      if (line.includes(kw)) { comment = exp; break; }
    }
    let coloredLine = escHtml(line)
      .replace(/\bSCAN\b/g, '<span class="kw-scan">SCAN</span>')
      .replace(/\bFILTER\b/g, '<span class="kw-filter">FILTER</span>')
      .replace(/\bPROJECT\b/g, '<span class="kw-project">PROJECT</span>');

    const row = document.createElement('div');
    row.className = 'tac-line';
    row.innerHTML = `<span class="tac-num">${i+1}</span><span class="tac-code">${coloredLine}</span>${comment ? `<span class="tac-comment">${comment}</span>` : ''}`;
    container.appendChild(row);
  });
}

// Plan (Mermaid)
function escMermaid(t) {
  if (t == null) return '';
  return String(t).replace(/"/g,'&quot;').replace(/>/g,'&gt;').replace(/</g,'&lt;');
}
function escHtml(t) {
  if (t == null) return '';
  const d = document.createElement('div');
  d.textContent = String(t);
  return d.innerHTML;
}

function planToMermaid(plan, id = 'N0') {
  if (!plan) return [];
  let lines = [];
  let label = plan.type;
  if (plan.type === 'SCAN') label += `\n${escMermaid(plan.table)}`;
  else if (plan.type === 'SELECT') {
    const c = plan.condition;
    if (c?.type === 'LOGICAL') label += `\n${escMermaid(c.left?.column)} ${c.operator} ...`;
    else label += `\n${escMermaid(c?.column)} ${escMermaid(c?.operator)} ${escMermaid(c?.value)}`;
  } else if (plan.type === 'PROJECT') {
    label += `\n${escMermaid(plan.columns?.join(', '))}`;
  }
  lines.push(`${id}["${label}"]`);
  if (plan.child) {
    const cid = id + 'C';
    lines = lines.concat(planToMermaid(plan.child, cid));
    lines.push(`${id} --> ${cid}`);
  }
  return lines;
}

async function renderPlan(data) {
  const isOpt = document.querySelector('input[name="planType"]:checked').value === 'optimized';
  const plan  = isOpt ? data.optimized_plan : data.plan;
  if (!plan) return;
  const code = 'graph TD\n' + planToMermaid(plan).join('\n');
  const container = document.getElementById('plan-mermaid');
  container.removeAttribute('data-processed');
  container.innerHTML = code;
  try { await mermaid.run({ nodes: [container] }); }
  catch(e) { console.error(e); }
}
