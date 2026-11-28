/* Complete First Purchase Checklist: saved ticks per company, progress,
   gates, a Canon Score / position-size calculator and a suggested answer.
   Without JavaScript the page is still a full printable checklist. */
(function () {
  'use strict';
  var page = document.querySelector('.fpc-page');
  if (!page) { return; }

  var KEY = 'canon-fpc-v1';
  var bar = page.querySelector('.fpc-bar');
  var nameInput = document.getElementById('fpc-company');
  var saved = document.getElementById('fpc-saved');
  var progress = page.querySelector('.fpc-progress span');
  var status = page.querySelector('.fpc-status');
  var answerBox = page.querySelector('.fpc-answer');
  var result = page.querySelector('.fpc-result');
  var boxes = Array.prototype.slice.call(page.querySelectorAll('.fpc-item input[type="checkbox"]'));
  var calcEls = Array.prototype.slice.call(page.querySelectorAll('[data-calc]'));
  var recEls = Array.prototype.slice.call(page.querySelectorAll('[data-rec]'));
  var sections = Array.prototype.slice.call(page.querySelectorAll('.fpc-sec'));
  bar.hidden = false;

  /* keep the bar under the sticky site header */
  var header = document.querySelector('.site-header');
  function setTop() {
    document.documentElement.style.setProperty('--fpc-top', Math.round(header ? header.getBoundingClientRect().height : 0) + 'px');
  }
  setTop(); window.addEventListener('resize', setTop);

  /* ---------- storage (per-browser; never required) ---------- */
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function store(db) {
    try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) { /* private mode: fine */ }
  }
  var db = load();
  db.you = db.you || {};            /* Part 1 ticks, shared by all companies */
  db.companies = db.companies || {}; /* name -> {ticks, calc, rec} */
  var current = db.last || '';

  function comp() {
    var k = current || '(unnamed)';
    db.companies[k] = db.companies[k] || { ticks: {}, calc: {}, rec: {} };
    return db.companies[k];
  }
  function partOf(box) { return box.closest('.fpc-sec').getAttribute('data-part'); }

  function fillSaved() {
    saved.innerHTML = '';
    Object.keys(db.companies).filter(function (k) { return k !== '(unnamed)'; }).sort().forEach(function (k) {
      var o = document.createElement('option'); o.value = k; saved.appendChild(o);
    });
  }

  function applyState() {
    var c = comp();
    boxes.forEach(function (b) {
      var id = b.getAttribute('data-id');
      b.checked = partOf(b) === '1' ? !!db.you[id] : !!c.ticks[id];
    });
    calcEls.forEach(function (el) {
      var k = el.getAttribute('data-calc');
      if (el.type === 'checkbox') { el.checked = !!c.calc[k]; }
      else if (k === 'money' || k === 'active' || k === 'phase') { el.value = db.you[k] != null ? db.you[k] : ''; }
      else { el.value = c.calc[k] != null ? c.calc[k] : ''; }
    });
    recEls.forEach(function (el) { el.value = c.rec[el.getAttribute('data-rec')] || ''; });
    nameInput.value = current;
    refresh();
  }

  /* ---------- progress and gates ---------- */
  function refresh() {
    var done = 0, openGate1 = [], openGate2 = [], openEv = [], openWait = [];
    boxes.forEach(function (b) {
      var li = b.closest('.fpc-item');
      li.classList.toggle('is-checked', b.checked);
      if (b.checked) { done++; return; }
      var kind = li.getAttribute('data-kind');
      if (kind === 'gate') { (partOf(b) === '1' ? openGate1 : openGate2).push(li); }
      if (kind === 'ev') { openEv.push(li); }
      if (kind === 'wait') { openWait.push(li); }
    });
    sections.forEach(function (s) {
      var bs = s.querySelectorAll('input[type="checkbox"]'), n = 0;
      for (var i = 0; i < bs.length; i++) { if (bs[i].checked) { n++; } }
      s.querySelector('.fpc-sec-count').textContent = n + ' of ' + bs.length + ' done';
      s.classList.toggle('is-done', n === bs.length);
    });
    progress.style.width = (100 * done / boxes.length) + '%';
    var gates = openGate1.length + openGate2.length + openEv.length + openWait.length;
    status.innerHTML = done + ' of ' + boxes.length + ' checks done' +
      (current ? ' for <strong>' + esc(current) + '</strong>' : '') + ' · ' +
      (gates ? '<span class="is-bad">' + gates + ' gate' + (gates > 1 ? 's' : '') + ' still open</span>' : 'all gates passed');
    var calc = calculate();
    suggest(done, openGate1, openGate2, openEv, openWait, calc);
  }

  /* ---------- calculator (Chapter 64 and 66 rules) ---------- */
  function num(k) {
    var el = page.querySelector('[data-calc="' + k + '"]');
    if (!el || el.value === '') { return null; }
    var v = parseFloat(el.value); return isNaN(v) ? null : v;
  }
  var BANDS = [
    { name: 'Exceptional', min: 85, lo: 6, hi: 8 },
    { name: 'Strong', min: 70, lo: 4, hi: 6 },
    { name: 'Adequate', min: 55, lo: 1.5, hi: 3 },
    { name: 'Watch list', min: 45, lo: 0, hi: 0 },
    { name: 'Avoid', min: 0, lo: 0, hi: 0 }
  ];
  function bandIndex(t) { for (var i = 0; i < BANDS.length; i++) { if (t >= BANDS[i].min) { return i; } } return 4; }
  function rs(v) { return 'Rs ' + Math.round(v).toLocaleString('en-IN'); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  function calculate() {
    var parts = { fin: 20, gov: 15, dur: 15, gro: 15, div: 10, liq: 10, val: 15 };
    var v = {}, missing = [], bad = [];
    Object.keys(parts).forEach(function (k) {
      v[k] = num(k);
      if (v[k] === null) { missing.push(k); }
      else if (v[k] < 0 || v[k] > parts[k]) { bad.push(k); }
    });
    if (missing.length) {
      result.innerHTML = '<p>Enter the seven scores to see the total, band and ceilings.</p>';
      return null;
    }
    if (num('unv') === null) {
      result.innerHTML = '<p>Enter the unverified or estimated points too (0 if every part was checked). A blank is not treated as zero.</p>';
      return null;
    }
    if (bad.length) {
      result.innerHTML = '<p><strong>Check your entries:</strong> a score is above its maximum or below zero.</p>';
      return null;
    }
    var bq = v.fin + v.gov + v.dur + v.gro + v.div, sa = v.liq + v.val, total = bq + sa;
    var capOn = !!page.querySelector('[data-calc="cap"]').checked || v.gov < 5;
    var shown = capOn ? Math.min(total, 54) : total;
    var bi = bandIndex(shown), ci = bi, notes = [];
    var unv = num('unv') || 0;
    var grade = unv === 0 ? 'A' : unv <= 10 ? 'B' : unv <= 20 ? 'C' : 'D';
    if (v.gov < 5) { notes.push('Governance under 5 of 15 is itself a hard rule.'); }
    if (capOn && total > 54) { notes.push('A hard rule caps the total at 54 (it was ' + total + ').'); }
    var drop = false;
    if (bi <= 1 && (bq < 38 || sa < 13)) { drop = true; notes.push((bq < 38 ? 'Business Quality is under 38' : 'Share Attractiveness is under 13') + ', so the ceiling comes from the band below.'); }
    if (grade === 'D') { drop = true; notes.push('More than 20 points are unverified (grade D): the score is provisional and the ceiling comes from the band below.'); }
    if (drop) { ci = Math.min(bi + 1, 4); }
    var band = BANDS[bi], cb = { name: BANDS[ci].name, lo: BANDS[ci].lo, hi: BANDS[ci].hi };
    var hot = !!page.querySelector('[data-calc="hot"]').checked;
    if (hot && cb.hi > 3) { cb.lo = 1.5; cb.hi = 3; notes.push('The sector is overheated: no position larger than a small side position (1.5–3%), whatever the score.'); }
    var phaseEl = page.querySelector('[data-calc="phase"]'), phase = phaseEl ? phaseEl.value : '';
    var seasonBlock = phase === '2' || (phase === '3' && shown < 70);
    if (phase === '2') { notes.push('Phase 2: the active part buys nothing new, however good the score.'); }
    if (phase === '3' && shown < 70) { notes.push('Phase 3: only scores of 70 or more, at low prices.'); }
    var value = num('value'), price = num('price'), mos = null;
    if (value !== null && price !== null && value > 0) {
      mos = (value - price) / value;
      notes.push('Margin of safety: (' + value + ' − ' + price + ') ÷ ' + value + ' = ' + Math.round(mos * 1000) / 10 + '%. The most you pay at a 35% margin is Rs ' + (Math.round(value * 0.65 * 100) / 100) + '.' + (mos >= 0.35 ? ' Passes.' : ' Fails: Wait.'));
    }
    var money = num('money'), active = num('active'), adv = num('adv'), sector = num('sector');
    var secpct = num('secpct'); if (secpct === null) { secpct = 25; }
    var limits = [], max = null;
    if (money !== null) {
      limits.push('Limit 1, band ceiling: ' + (cb.hi ? cb.lo + '–' + cb.hi + '% = ' + rs(money * cb.lo / 100) + ' to ' + rs(money * cb.hi / 100) : 'no new money'));
      max = cb.hi ? money * cb.hi / 100 : 0;
      if (adv !== null) { limits.push('Limit 2, liquidity: half a day\'s turnover = ' + rs(adv / 2)); max = Math.min(max, adv / 2); }
      if (sector !== null) { var room = Math.max(0, money * secpct / 100 - sector); limits.push('Limit 3, sector room at ' + secpct + '%: ' + rs(room)); max = Math.min(max, room); }
      if (active !== null) { limits.push('Season allowance from Step 2: ' + rs(active)); max = Math.min(max, active); }
      if (seasonBlock) { limits.push('Season check: no new buying now'); max = 0; }
    }
    var html = '<p class="fpc-big">Total ' + shown + ' of 100 · ' + band.name + ' · grade ' + grade + '</p>' +
      '<p>Business Quality ' + bq + ' of 75 · Share Attractiveness ' + sa + ' of 25' +
      (ci !== bi ? ' · ceiling taken from <strong>' + cb.name + '</strong>' : '') + '</p>';
    if (notes.length) { html += '<ul>' + notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>'; }
    if (limits.length) {
      html += '<p style="margin-top:8px"><strong>How much:</strong></p><ul>' + limits.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('') + '</ul>';
      html += '<p><strong>Most you may hold: ' + rs(max) + '.</strong> This is a ceiling, not a target: buy less if the price is only fair or it would be hard to sell.</p>';
    } else {
      html += '<p>Add your share money (and turnover, sector holdings, season allowance) to see the rupee limits.</p>';
    }
    result.innerHTML = html;
    return { total: shown, eligible: shown >= 55, grade: grade, max: max, band: band.name, phase: phase, seasonBlock: seasonBlock, value: value, price: price, mos: mos };
  }

  /* ---------- suggested answer ---------- */
  function suggest(done, g1, g2, ev, wt, calc) {
    var cls = '', msg = '';
    if (g1.length) {
      cls = 'a-stop'; msg = '<strong>Stop: Part 1 is not finished.</strong> ' + g1.length + ' readiness or season gate' + (g1.length > 1 ? 's are' : ' is') + ' still open. Fix that before studying any company.';
    } else if (g2.length) {
      cls = 'a-reject'; msg = '<strong>Not yet: ' + g2.length + ' company gate' + (g2.length > 1 ? 's' : '') + ' open.</strong> If a gate truly fails, the answer is <strong>Reject</strong>. If you have not checked it yet, check it.';
    } else if (ev.length || (calc && calc.grade === 'D')) {
      cls = 'a-ev'; msg = '<strong>Not enough evidence.</strong> Too much rests on figures you could not check. Do not buy until they can be checked.';
    } else if (!calc) {
      cls = ''; msg = done ? '<strong>Enter the seven scores in the calculator</strong> to finish the decision.' : '';
    } else if (!calc.eligible) {
      cls = 'a-wait'; msg = '<strong>Wait or Reject.</strong> The total (' + calc.total + ') is under 55, so no new money. Wait if only the price is wrong; Reject if the business is weak or capped.';
    } else if (!calc.phase) {
      cls = ''; msg = '<strong>Choose the season</strong> (Step 2) in the calculator to finish the decision.';
    } else if (calc.seasonBlock) {
      cls = 'a-wait'; msg = '<strong>Wait.</strong> The season check fails: ' + (calc.phase === '2' ? 'in Phase 2 the active part buys nothing new.' : 'in Phase 3 only scores of 70 or more are bought.');
    } else if (calc.value === null || calc.price === null) {
      cls = 'a-ev'; msg = '<strong>Not enough evidence yet.</strong> The price check needs your own value estimate and today\'s price. Enter both in the calculator.';
    } else if (calc.mos < 0.35) {
      cls = 'a-wait'; msg = '<strong>Wait.</strong> The price check fails: the margin of safety is ' + Math.round(calc.mos * 1000) / 10 + '%, below the 35% needed. A price of Rs ' + (Math.round(calc.value * 0.65 * 100) / 100) + ' or less would pass, if your value estimate still holds.';
    } else if (wt.length) {
      cls = 'a-wait'; msg = '<strong>Wait:</strong> ' + wt.length + ' price or season check' + (wt.length > 1 ? 's are' : ' is') + ' not ticked.';
    } else if (done < boxes.length) {
      cls = 'a-wait'; msg = '<strong>Almost:</strong> every gate is passed and the total is ' + calc.total + ' (' + calc.band + '), but ' + (boxes.length - done) + ' checks are not ticked yet. Finish them, especially the sell rules, before you buy.';
    } else {
      cls = 'a-buy'; msg = '<strong>Buy is allowed' + (calc.max !== null ? ', up to ' + rs(calc.max) : '') + '.</strong> Every check is ticked and every gate passed. Buying is still your choice, and buying less than the limit is often wiser.';
    }
    answerBox.className = 'fpc-answer ' + cls;
    answerBox.innerHTML = msg ? '<span class="fpc-tag" style="background:#1b1a17">Suggested answer</span> ' + msg : '';
  }

  /* ---------- events ---------- */
  boxes.forEach(function (b) {
    b.addEventListener('change', function () {
      var id = b.getAttribute('data-id');
      if (partOf(b) === '1') { db.you[id] = b.checked; } else { comp().ticks[id] = b.checked; }
      store(db); refresh();
    });
  });
  calcEls.forEach(function (el) {
    el.addEventListener(el.type === 'checkbox' ? 'change' : 'input', function () {
      var k = el.getAttribute('data-calc');
      var val = el.type === 'checkbox' ? el.checked : el.value;
      if (k === 'money' || k === 'active' || k === 'phase') { db.you[k] = val; } else { comp().calc[k] = val; }
      store(db); refresh();
    });
  });
  recEls.forEach(function (el) {
    el.addEventListener('input', function () { comp().rec[el.getAttribute('data-rec')] = el.value; store(db); });
  });
  function switchTo(name) {
    current = name.trim();
    db.last = current; comp(); store(db); fillSaved(); applyState();
  }
  nameInput.addEventListener('change', function () {
    var name = nameInput.value.trim();
    /* first time a name is typed: keep the unnamed ticks under that name */
    if (name && !current && db.companies['(unnamed)'] && !db.companies[name]) {
      db.companies[name] = db.companies['(unnamed)']; delete db.companies['(unnamed)'];
    }
    switchTo(name);
  });
  bar.addEventListener('click', function (e) {
    var act = e.target.getAttribute && e.target.getAttribute('data-act');
    if (act === 'new') { switchTo(''); nameInput.value = ''; nameInput.focus(); }
    if (act === 'reset') {
      var c = comp(); c.ticks = {}; c.calc = {}; c.rec = {};
      store(db); applyState();
    }
    if (act === 'print') { window.print(); }
  });

  fillSaved();
  applyState();
})();
