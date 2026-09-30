/* FinancePro — utilitários de interface compartilhados */
(function () {
  'use strict';

  const root = document.documentElement;

  // ── Sidebar mobile ────────────────────────────────────────────────────
  function toggleSidebar(force) {
    const sb = document.getElementById('sidebar');
    const ov = document.getElementById('sidebarOverlay');
    if (!sb) return;
    const open = typeof force === 'boolean' ? force : !sb.classList.contains('open');
    sb.classList.toggle('open', open);
    if (ov) ov.classList.toggle('open', open);
  }

  document.addEventListener('keydown', e => { if (e.key === 'Escape') toggleSidebar(false); });

  // ── Formatação ────────────────────────────────────────────────────────
  const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  function fmtBRL(v) {
    const n = parseFloat(v);
    return brl.format(isNaN(n) ? 0 : n);
  }

  function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // Aceita só nomes de ícone Font Awesome (a IA devolve esses valores)
  function faIcon(name, fallback) {
    return /^fa-[a-z0-9-]+$/.test(name || '') ? name : (fallback || 'fa-circle-dot');
  }

  // Aceita só cores hex (a IA devolve esses valores)
  function safeColor(c, fallback) {
    return /^#[0-9a-fA-F]{3,8}$/.test(c || '') ? c : (fallback || 'var(--primary)');
  }

  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // ── Chart.js com as cores do design system ────────────────────────────
  function chartTheme() {
    return {
      text: cssVar('--text-secondary'),
      muted: cssVar('--text-muted'),
      grid: cssVar('--border'),
      surface: cssVar('--surface'),
      font: cssVar('--font-sans') || 'Inter',
      mono: cssVar('--font-mono') || 'monospace',
    };
  }

  function applyChartDefaults() {
    if (!window.Chart) return;
    const t = chartTheme();
    Chart.defaults.color = t.text;
    Chart.defaults.borderColor = t.grid;
    Chart.defaults.font.family = t.font;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0A0C11';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(143,160,255,.25)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.titleFont = { family: t.font, weight: '600' };
    Chart.defaults.plugins.tooltip.bodyFont = { family: t.mono };
  }

  // ── Mensagens ─────────────────────────────────────────────────────────
  document.addEventListener('click', e => {
    const btn = e.target.closest('.msg-close');
    if (btn) btn.closest('.msg').remove();
  });

  // ── Ciclo das páginas de IA: idle → loading → error | results ─────────
  //   cfg: { url, body, btn, states: {idle, loading, error, results, extra[]},
  //          errorMsg, labels: {busy, again}, onSuccess(json) }
  function aiRun(cfg) {
    const $ = id => (id ? document.getElementById(id) : null);
    const s = cfg.states;
    const btns = (Array.isArray(cfg.btn) ? cfg.btn : [cfg.btn]).map($).filter(Boolean);

    function show(which) {
      ['idle', 'loading', 'error', 'results'].forEach(k => {
        const el = $(s[k]);
        if (el) el.classList.toggle('hidden', k !== which);
      });
      (s.extra || []).forEach(id => { const el = $(id); if (el) el.classList.toggle('hidden', which !== 'results'); });
    }

    function setBtn(busy, label) {
      btns.forEach(b => {
        b.disabled = busy;
        const lbl = b.querySelector('[data-label]');
        const ico = b.querySelector('[data-icon]');
        if (!b.dataset.origLabel && lbl) b.dataset.origLabel = lbl.textContent;
        if (!b.dataset.origIcon && ico) b.dataset.origIcon = ico.className;
        if (lbl && label) lbl.textContent = label;
        if (ico) ico.className = busy ? 'spinner' : (b.dataset.done ? 'fa-solid fa-rotate' : b.dataset.origIcon);
      });
    }

    show('loading');
    setBtn(true, cfg.labels && cfg.labels.busy);

    return fetch(cfg.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN, 'Content-Type': 'application/json' },
      body: cfg.body ? JSON.stringify(cfg.body) : null,
    })
      .then(r => r.json())
      .then(data => {
        btns.forEach(b => { b.dataset.done = '1'; });
        setBtn(false, cfg.labels && cfg.labels.again);
        if (!data.success) throw new Error(data.error || 'Erro desconhecido. Tente novamente.');
        cfg.onSuccess(data);
        show('results');
        const res = $(s.results);
        if (res && cfg.scroll !== false) res.scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch(err => {
        const conn = err instanceof TypeError || err.name === 'SyntaxError';
        btns.forEach(b => {
          const lbl = b.querySelector('[data-label]');
          if (!b.dataset.done && lbl) lbl.textContent = b.dataset.origLabel;
        });
        setBtn(false);
        const msg = $(cfg.errorMsg);
        if (msg) msg.textContent = conn ? 'Erro de conexão. Verifique sua internet e tente novamente.' : err.message;
        show('error');
      });
  }

  // ── Tabs genéricas: [data-tabs] > .tab[data-tab="id"] ─────────────────
  function activateTab(group, id) {
    const container = document.querySelector(`[data-tabs="${group}"]`);
    if (!container) return;
    container.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === id));
    document.querySelectorAll(`[data-tab-group="${group}"]`).forEach(p => p.classList.toggle('active', p.id === id));
  }
  document.addEventListener('click', e => {
    const tab = e.target.closest('[data-tabs] .tab');
    if (tab) activateTab(tab.parentElement.dataset.tabs, tab.dataset.tab);
  });

  window.App = { toggleSidebar, fmtBRL, esc, faIcon, safeColor, cssVar, chartTheme, applyChartDefaults, aiRun, activateTab };
})();
