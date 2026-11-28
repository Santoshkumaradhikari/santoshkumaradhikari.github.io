/* Canon Score Engine page: reads the form, calls CanonEngine.scoreCompany(),
   shows the result, saves companies in this browser, and exports/imports files. */
(function () {
  'use strict';
  var page = document.querySelector('.ce-page');
  if (!page || !window.CanonEngine) { return; }
  var E = window.CanonEngine;
  var KEY = 'canon-engine-v1';
  var bar = page.querySelector('.ce-bar');
  var nameInput = document.getElementById('ce-company');
  var saved = document.getElementById('ce-saved');
  var summary = page.querySelector('.ce-summary');
  var resultBox = page.querySelector('.ce-result');
  var tbody = page.querySelector('.ce-tbody');
  var sizeBox = page.querySelector('.ce-size');
  var answerBox = page.querySelector('.ce-answer');
  var fields = Array.prototype.slice.call(page.querySelectorAll('[data-k]'));
  var statuses = Array.prototype.slice.call(page.querySelectorAll('[data-status]'));
  bar.hidden = false;

  var header = document.querySelector('.site-header');
  function setTop() { document.documentElement.style.setProperty('--ce-top', Math.round(header ? header.getBoundingClientRect().height : 0) + 'px'); }
  setTop(); window.addEventListener('resize', setTop);

  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function rs(v) { return 'Rs ' + Math.round(v).toLocaleString('en-IN'); }
  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function store() { try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) { /* private mode */ } }
  var db = load(); db.companies = db.companies || {};
  var current = db.last || '';

  /* ---------- read and write the form ---------- */
  function readForm() {
    var o = { status: {} };
    fields.forEach(function (el) {
      var k = el.getAttribute('data-k'), i = el.getAttribute('data-i');
      var v = el.type === 'checkbox' ? el.checked : el.value;
      if (i !== null) { o[k] = o[k] || []; o[k][+i] = v; } else { o[k] = v; }
    });
    statuses.forEach(function (s) { o.status[s.getAttribute('data-status')] = s.value; });
    return o;
  }
  function writeForm(o) {
    o = o || {};
    fields.forEach(function (el) {
      var k = el.getAttribute('data-k'), i = el.getAttribute('data-i');
      var v = i !== null ? (o[k] || [])[+i] : o[k];
      if (el.type === 'checkbox') {
        el.checked = v === undefined ? el.defaultChecked : !!v;
      } else if (el.tagName === 'SELECT') {
        el.value = v === undefined || v === null ? el.options[0].value : v;
      } else { el.value = v === undefined || v === null ? '' : v; }
    });
    statuses.forEach(function (s) { s.value = (o.status && o.status[s.getAttribute('data-status')]) || 'verified'; });
  }

  /* ---------- show only the questions that apply to this type of company ---------- */
  function applies(token, sec, inp) {
    var c = E.CLASSES[sec] || {};
    switch (token) {
      case 'lender': return !!c.lender;
      case 'insurer': return !!c.insurer;
      case 'nonfin': return !c.lender && !c.insurer;
      case 'hydro': return !!c.hydro;
      case 'precod': return !!c.precod;
      case 'notprecod': return !c.precod;
      case 'nonlender': return !c.lender;
      case 'cet1': return !!(c.lender && c.cet1);
      case 'conc': return !c.hydro || inp.single_buyer === false;
      default: return true;
    }
  }
  function applyVisibility(inp) {
    Array.prototype.slice.call(page.querySelectorAll('[data-show]')).forEach(function (el) {
      el.hidden = !el.getAttribute('data-show').split(/\s+/).some(function (t) { return applies(t, inp.sector, inp); });
    });
  }

  /* ---------- clean the raw form into engine inputs ---------- */
  function toEngine(f) {
    var o = {};
    Object.keys(f).forEach(function (k) { o[k] = f[k]; });
    var c = E.CLASSES[f.sector] || {};
    /* hidden fields must not leak from another company type */
    if (!c.lender) { ['car', 'tier1', 'cet1', 'writeback_max', 'loan_cagr', 'system_cagr', 'deposit_cagr', 'gross_npl', 'class_npl', 'adj_npl', 'adj_npl_prev', 'restructured'].forEach(function (k) { delete o[k]; }); o.npl_ok = 'yes'; }
    if (!c.insurer) { delete o.solvency; delete o.solvency_wt; delete o.gain_max; }
    if (c.lender || c.insurer) { delete o.cash_conversion; }
    if (!(c.lender && c.cet1)) { delete o.cet1; }
    if (c.hydro) { o.single_buyer = !!f.single_buyer; }
    o.system_verified = !!f.system_verified;
    o.div_cash = (f.div_cash || []).slice(0, 5).map(function (x) { return !!x; });
    while (o.div_cash.length < 5) { o.div_cash.push(false); }
    var anyDiv = (f.div_cash || []).some(Boolean) || (f.div_payout || []).some(function (x) { return x !== '' && x !== undefined; });
    if (f.div_none) { o.div_cash = [false, false, false, false, false]; } else if (!anyDiv) { delete o.div_cash; }
    o.div_payout = f.div_payout || [];
    return o;
  }

  /* ---------- run ---------- */
  var DIMS = { fin: ['Financial Strength', 20], gov: ['Governance', 15], liq: ['Liquidity', 10], val: ['Valuation', 15], dur: ['Durability', 15], gro: ['Growth', 15], div: ['Dividends', 10] };
  function run() {
    var f = readForm();
    applyVisibility(f);
    var r;
    try { r = E.scoreCompany(toEngine(f)); } catch (err) { resultBox.innerHTML = '<p>Check the figures: ' + esc(err.message) + '</p>'; return; }

    /* per-part outputs beside each question */
    r.parts.forEach(function (p) {
      var out = page.querySelector('[data-out="' + p.key + '"]');
      if (out) { out.textContent = p.status === 'missing' ? '—' : p.pts + ' / ' + p.max; out.className = 'ce-part-score' + (p.status === 'missing' ? ' is-missing' : p.flagged ? ' is-flagged' : ''); }
    });
    Object.keys(DIMS).forEach(function (d) {
      var el = page.querySelector('[data-dim="' + d + '"]');
      var miss = r.parts.some(function (p) { return p.dim === d && p.status === 'missing'; });
      if (el) { el.textContent = (miss ? '… ' : '') + r.dims[d] + ' / ' + DIMS[d][1]; }
    });

    var done = r.parts.filter(function (p) { return p.status !== 'missing'; }).length;
    var html;
    if (r.excluded) {
      html = '<p class="ce-big ce-bad">Excluded</p><p>A final finding of fraud excludes the company, whatever else it scores.</p>';
    } else {
      html = '<p class="ce-big">' + (r.complete ? '' : 'So far: ') + r.total + ' <span>of 100</span> · ' + esc(shortBand(r.band)) + ' · grade ' + r.grade + (r.provisional ? ' · provisional' : '') + '</p>' +
        '<p>Business Quality <strong>' + r.bq + '</strong> of 75 · Share Attractiveness <strong>' + r.sa + '</strong> of 25' +
        (r.total !== r.raw ? ' · before the cap: ' + r.raw : '') + '</p>';
      html += '<div class="ce-bars">' + Object.keys(DIMS).map(function (d) {
        var pct = 100 * r.dims[d] / DIMS[d][1];
        return '<div class="ce-barrow"><span>' + DIMS[d][0] + '</span><span class="ce-track"><span style="width:' + pct + '%"></span></span><span>' + r.dims[d] + '/' + DIMS[d][1] + '</span></div>';
      }).join('') + '</div>';
      var notes = [];
      if (!r.complete) { notes.push(r.missingParts.length + ' of ' + r.parts.length + ' parts still need figures: ' + r.missingParts.join(', ') + '.'); }
      if (r.capReasons.length) { notes.push('Capped at 54 because: ' + r.capReasons.join('; ') + '.'); }
      notes.push('Evidence: ' + r.flaggedPts + ' points rest on estimated, unverified, unavailable or missing figures (grade ' + r.grade + (r.grade === 'D' ? ', provisional' : '') + ').');
      if (r.restated) { notes.push('Accounts restated: the score is provisional until a full new audited year.'); }
      if (r.ceilingDropped) { notes.push('The position ceiling comes from the band below (' + r.ceiling + '), because ' + (r.provisional ? 'the score is provisional' : 'Business Quality is under 38 or Share Attractiveness under 13') + '.'); }
      if (r.cls.hydro || r.cls.insurer) { notes.push('Compare this score only with other ' + (r.cls.hydro ? 'hydropower' : 'insurance') + ' companies.'); }
      html += '<ul>' + notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>';
    }
    resultBox.innerHTML = html;
    tbody.innerHTML = r.parts.map(function (p) {
      return '<tr class="' + (p.status === 'missing' ? 'is-missing' : '') + '"><td>' + esc(p.name) + '</td><td>' + (p.status === 'missing' ? '—' : p.pts) + ' / ' + p.max + '</td><td>' + esc(p.status) + '</td><td>' + esc(p.why) + '</td></tr>';
    }).join('');

    var size = sizing(r, f);
    summary.innerHTML = (current ? '<strong>' + esc(current) + '</strong> · ' : '') + done + ' of ' + r.parts.length + ' parts scored · ' +
      (r.excluded ? '<span class="ce-bad">excluded</span>' : done === 0 ? 'enter figures, or press "Load an example"' : 'total ' + r.total + ' · ' + esc(shortBand(r.band)) + ' · grade ' + r.grade);
    if (done === 0 && !r.excluded) { resultBox.innerHTML = '<p>No figures yet. Choose the type of company, then fill in each part from the company\'s reports. The score updates as you type.</p>'; }
    answer(r, size);
    save(f);
  }
  function shortBand(b) { return (b || '').replace(' combined score', '').replace('Weak / Avoid - ', ''); }

  function sizing(r, f) {
    var num = function (k) { var v = parseFloat(f[k]); return isNaN(v) ? null : v; };
    var money = num('money'), active = num('active'), adv = num('adv20'), sector = num('sector_now'), sp = num('sector_pct');
    if (sp === null) { sp = 25; }
    if (r.excluded || money === null) { sizeBox.innerHTML = money === null ? '<p>Enter your share money to see the rupee limits.</p>' : ''; return null; }
    var m = /([\d.]+)%-([\d.]+)%/.exec(r.ceiling || '');
    var lo = m ? +m[1] : 0, hi = m ? +m[2] : 0;
    var lines = [], max = money * hi / 100;
    lines.push('Limit 1, band ceiling (' + (m ? r.ceiling.replace('-', '–') : 'no new money') + '): ' + (hi ? rs(money * lo / 100) + ' to ' + rs(money * hi / 100) : 'Rs 0'));
    if (adv !== null) { lines.push('Limit 2, liquidity (half a day\'s turnover): ' + rs(adv / 2)); max = Math.min(max, adv / 2); }
    if (sector !== null) { var room = Math.max(0, money * sp / 100 - sector); lines.push('Limit 3, sector room at ' + sp + '%: ' + rs(room)); max = Math.min(max, room); }
    if (active !== null) { lines.push('Season allowance (Step 2): ' + rs(active)); max = Math.min(max, active); }
    sizeBox.innerHTML = '<ul>' + lines.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('') + '</ul><p class="ce-big2">Most you may hold: ' + rs(max) + '</p><p>A ceiling, not a target. Buy less when the price is only fair, the company is new to you, or it would be hard to sell.</p>';
    return max;
  }

  function answer(r, max) {
    var cls, msg;
    if (r.excluded) { cls = 'a-reject'; msg = '<strong>Reject.</strong> A final fraud finding excludes the company.'; }
    else if (!r.complete) { cls = 'a-wait'; msg = '<strong>Not finished.</strong> ' + r.missingParts.length + ' of ' + r.parts.length + ' parts still need figures. Until they are filled in or marked "Not available", there is no answer.'; }
    else if (r.grade === 'D' || r.restated) { cls = 'a-ev'; msg = '<strong>Not enough evidence.</strong> More than 20 points rest on figures you could not check' + (r.restated ? ', or the accounts were restated' : '') + '. Do not buy until they can be checked.'; }
    else if (r.total < 55) { cls = r.capReasons.length ? 'a-reject' : 'a-wait'; msg = '<strong>' + (r.capReasons.length ? 'Reject for now' : 'Wait or Reject') + '.</strong> The total is ' + r.total + ', under 55, so no new money.' + (r.capReasons.length ? ' A hard rule caps it; look again only when the problem is cleared.' : ' Wait if only the price is wrong; Reject if the business is weak.'); }
    else { cls = 'a-buy'; msg = '<strong>Eligible for new money' + (max !== null ? ', up to ' + rs(max) : '') + '.</strong> Eligible is not an instruction to buy: check price against value, your readiness, the season and your sell rules in the checklist first. Wait is right if the price is only fair.'; }
    answerBox.className = 'ce-answer ' + cls;
    answerBox.innerHTML = msg;
  }

  /* ---------- companies ---------- */
  function save(f) {
    db.companies[current || '(unnamed)'] = f; db.last = current; store(); fillSaved();
  }
  function fillSaved() {
    saved.innerHTML = '';
    Object.keys(db.companies).filter(function (k) { return k !== '(unnamed)'; }).sort().forEach(function (k) { var o = document.createElement('option'); o.value = k; saved.appendChild(o); });
  }
  function open(name) {
    current = name; nameInput.value = name;
    writeForm(db.companies[name || '(unnamed)']); run();
  }

  var EXAMPLE = { sector: 'commercial', price: 570, roes: [12, 13, 14], car: 13.4, tier1: 11.2, cet1: 10.5, profits: [50, 55, 60, 58, 66, 72], writeback_max: 10,
    promoter_fall: 0, pledged: 2, audit: 'emphasis', independents: 2, legal_min: 1, tests_met: 'yes', late_filings: 0,
    turnover_avg: 30000000, turnover_median: 26000000, days_traded: 100, free_float: 49, eps_ttm: 30, bvps: 237.5, median_pe: 16, median_pb: 1.6, peers: 20,
    roe_ge_median: 'yes', npl_ok: 'yes', moat: '8', concentration: 25, loan_cagr: 9, system_cagr: 8, deposit_cagr: 9, system_verified: true,
    gross_npl: 3.1, class_npl: 5.71, adj_npl: 3.2, adj_npl_prev: 3.3, restructured: 1, eps_series: [20, 22, 21, 24, 23, 25],
    div_cash: [true, true, true, true, true], div_payout: [45, 45, 45, 45, 45], div_source: 'genuine', money: 200000, active: 100000, adv20: 30000000, sector_now: 40000, status: {} };

  fields.forEach(function (el) { el.addEventListener(el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input', run); });
  statuses.forEach(function (s) { s.addEventListener('change', run); });
  nameInput.addEventListener('change', function () {
    var name = nameInput.value.trim();
    if (name && !current && db.companies['(unnamed)'] && !db.companies[name]) { db.companies[name] = db.companies['(unnamed)']; delete db.companies['(unnamed)']; }
    open(name);
  });
  bar.addEventListener('click', function (e) {
    var act = e.target.getAttribute && e.target.getAttribute('data-act');
    if (act === 'new') { open(''); nameInput.focus(); }
    if (act === 'clear') { db.companies[current || '(unnamed)'] = {}; writeForm({}); run(); }
    if (act === 'print') { window.print(); }
    if (act === 'example') { current = 'Example: Ramesh\'s Bank A (made-up)'; nameInput.value = current; writeForm(EXAMPLE); run(); }
    if (act === 'export') {
      var data = { tool: 'Canon Score Engine', rubric: E.VERSION, company: current, saved_on: new Date().toISOString(), inputs: readForm(), result: E.scoreCompany(toEngine(readForm())) };
      var blob = new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' });
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob);
      a.download = 'canon-score-' + (current || 'company').replace(/[^\w-]+/g, '-') + '.json';
      document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    }
  });
  var fileInput = bar.querySelector('input[type="file"]');
  fileInput.addEventListener('change', function () {
    var file = fileInput.files && fileInput.files[0]; if (!file) { return; }
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var data = JSON.parse(reader.result);
        if (!data || typeof data.inputs !== 'object') { throw new Error('not a Canon Score Engine file'); }
        current = String(data.company || file.name.replace(/\.json$/, '')).slice(0, 80); nameInput.value = current;
        writeForm(data.inputs); run();
      } catch (err) { answerBox.className = 'ce-answer a-reject'; answerBox.textContent = 'That file could not be opened: ' + err.message; }
      fileInput.value = '';
    };
    reader.readAsText(file);
  });

  fillSaved();
  open(current);
})();
