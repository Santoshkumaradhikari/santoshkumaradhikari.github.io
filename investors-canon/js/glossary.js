/* Glossary page: instant search, topic filter, letter jump, term of the day.
   Without JavaScript every term is still shown, in A–Z order. */
(function () {
  'use strict';
  var page = document.querySelector('.glossary-page');
  if (!page) { return; }

  var search = page.querySelector('.gl-search');
  var filters = page.querySelector('.gl-filters');
  var input = document.getElementById('gl-q');
  var clearBtn = page.querySelector('.gl-clear');
  var countEl = document.getElementById('gl-count');
  var results = document.getElementById('gl-results');
  var empty = document.getElementById('gl-empty');
  var chips = Array.prototype.slice.call(page.querySelectorAll('.gl-chip'));
  var letters = Array.prototype.slice.call(page.querySelectorAll('.gl-jump a'));
  var sections = Array.prototype.slice.call(page.querySelectorAll('.gl-section'));
  var cards = Array.prototype.slice.call(page.querySelectorAll('.gl-term'));
  var total = cards.length;
  var activeCat = '';

  search.hidden = false;
  filters.hidden = false;

  /* keep the search bar just under the sticky site header */
  var header = document.querySelector('.site-header');
  function setTop() {
    var h = header ? header.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty('--gl-top', Math.round(h) + 'px');
  }
  setTop();
  window.addEventListener('resize', setTop);

  /* remember each card's home and its plain text, for restoring and highlighting */
  function norm(s) {
    return (s || '').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '');
  }
  cards.forEach(function (c, i) {
    c._home = c.parentNode;
    c._idx = i;
    c._term = norm(c.getAttribute('data-term'));
    c._full = norm(c.getAttribute('data-full'));
    c._np = norm(c.getAttribute('data-np'));
    c._hay = norm(c.textContent.replace(/\s+/g, ' ') + ' ' + c.className.replace(/c-/g, ''));
    c._hl = Array.prototype.slice.call(c.querySelectorAll('[data-hl]')).map(function (el) {
      return { el: el, text: el.textContent };
    });
  });

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function reEsc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function highlight(c, tokens) {
    c._hl.forEach(function (h) {
      if (!tokens.length) { h.el.textContent = h.text; return; }
      var re = new RegExp('(' + tokens.map(reEsc).join('|') + ')', 'gi');
      h.el.innerHTML = esc(h.text).replace(re, '<mark>$1</mark>');
    });
  }

  function score(c, q, tokens) {
    var s = 0;
    if (c._term === q || c._full === q || c._np === q) { s += 1000; }
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      if (c._hay.indexOf(t) === -1 && c._term.indexOf(t) === -1 && c._full.indexOf(t) === -1 && c._np.indexOf(t) === -1) { return -1; }
      if (c._term.indexOf(t) === 0) { s += 120; }
      else if (c._term.indexOf(t) > -1) { s += 70; }
      if (c._full.indexOf(t) > -1) { s += 45; }
      if (c._np.indexOf(t) > -1) { s += 45; }
      s += 4;
    }
    return s;
  }

  function setUrl(q) {
    try {
      var u = new URL(window.location.href);
      if (q) { u.searchParams.set('q', q); } else { u.searchParams.delete('q'); }
      if (activeCat) { u.searchParams.set('topic', activeCat); } else { u.searchParams.delete('topic'); }
      history.replaceState(null, '', u.pathname + u.search + u.hash);
    } catch (e) { /* older browser: skip */ }
  }

  function render() {
    var raw = input.value.trim();
    var q = norm(raw);
    var tokens = q ? q.split(/\s+/).filter(Boolean) : [];
    var shown = 0;
    clearBtn.hidden = !raw;
    page.classList.toggle('is-searching', !!q);
    page.classList.toggle('is-filtered', !!activeCat);

    if (q) {
      var hits = [];
      cards.forEach(function (c) {
        var okCat = !activeCat || c.getAttribute('data-cat') === activeCat;
        var s = okCat ? score(c, q, tokens) : -1;
        c.hidden = s < 0;
        highlight(c, s < 0 ? [] : tokens);
        if (s >= 0) { hits.push({ c: c, s: s }); }
      });
      cards.forEach(function (c) { if (c.hidden && c.parentNode !== c._home) { c._home.appendChild(c); } });
      hits.sort(function (a, b) { return b.s - a.s || a.c._idx - b.c._idx; });
      hits.forEach(function (h) { results.appendChild(h.c); });
      shown = hits.length;
      results.hidden = !shown;
      sections.forEach(function (s) { s.hidden = true; });
    } else {
      cards.forEach(function (c) {
        var ok = !activeCat || c.getAttribute('data-cat') === activeCat;
        c.hidden = !ok;
        highlight(c, []);
        if (ok) { shown++; }
      });
      /* put cards back in A–Z order inside each section */
      cards.forEach(function (c) { c._home.appendChild(c); });
      results.hidden = true;
      sections.forEach(function (s) {
        s.hidden = !s.querySelector('.gl-term:not([hidden])');
      });
    }

    letters.forEach(function (a) {
      var sec = document.getElementById('letter-' + a.getAttribute('data-letter').toLowerCase());
      a.classList.toggle('is-off', !!q || !sec || sec.hidden);
    });
    empty.hidden = shown > 0;
    var topic = '';
    chips.forEach(function (ch) { if (ch.getAttribute('aria-pressed') === 'true' && activeCat) { topic = ch.firstChild.textContent.trim(); } });
    countEl.textContent = (shown === total && !q) ? total + ' terms' :
      'Showing ' + shown + ' of ' + total + ' terms' + (topic ? ' in ' + topic : '') + (raw ? ' for “' + raw + '”' : '');
    setUrl(raw);
  }

  var timer;
  input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(render, 60); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { input.value = ''; render(); }
    if (e.key === 'Enter') {
      e.preventDefault();
      var first = results.querySelector('.gl-term:not([hidden])');
      if (first) { first.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    }
  });
  clearBtn.addEventListener('click', function () { input.value = ''; render(); input.focus(); });

  chips.forEach(function (ch) {
    ch.addEventListener('click', function () {
      activeCat = ch.getAttribute('data-cat') || '';
      chips.forEach(function (o) { o.setAttribute('aria-pressed', o === ch ? 'true' : 'false'); });
      render();
    });
  });

  var bookSearch = page.querySelector('.gl-book-search');
  if (bookSearch) {
    bookSearch.addEventListener('click', function () {
      var b = document.querySelector('.nav-search-btn');
      if (b) { b.click(); }
    });
  }

  /* going to a term (see-also chips, start-here chips, shared links) */
  function reveal(id, instant) {
    var el = id && document.getElementById(id);
    if (!el || !el.classList.contains('gl-term')) { return; }
    if (el.hidden || input.value || activeCat) {
      input.value = ''; activeCat = '';
      chips.forEach(function (o) { o.setAttribute('aria-pressed', o.getAttribute('data-cat') ? 'false' : 'true'); });
      render();
    }
    el.classList.remove('is-flash'); void el.offsetWidth; el.classList.add('is-flash');
    el.scrollIntoView({ behavior: instant ? 'auto' : 'smooth', block: 'start' });
  }
  page.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) { return; }
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (el && el.classList.contains('gl-term')) {
      e.preventDefault();
      history.replaceState(null, '', '#' + id);
      reveal(id);
    }
  });

  window.addEventListener('hashchange', function () {
    reveal(decodeURIComponent(window.location.hash.slice(1)), true);
  });

  /* term of the day: the same for everyone on a given day */
  var today = document.getElementById('gl-today');
  if (today && total) {
    var day = Math.floor((Date.now() + 5.75 * 3600e3) / 864e5); /* Nepal time */
    var pick = cards[(day * 37) % total];
    var def = pick.querySelector('.gl-def').textContent;
    var m = def.match(/^.*?[.!?](?=\s|$)/);
    var first = m ? m[0] : def;
    today.className = 'gl-today c-' + pick.getAttribute('data-cat');
    today.innerHTML = '<span class="gl-today-label">Term of the day</span><a href="#' + pick.id + '">' +
      esc(pick.querySelector('.gl-name').textContent) + '</a> — ' + esc(first);
    today.hidden = false;
  }

  /* floating "back to search" button */
  var topBtn = document.createElement('button');
  topBtn.type = 'button';
  topBtn.className = 'gl-top-btn';
  topBtn.textContent = '↑ Search terms';
  document.body.appendChild(topBtn);
  topBtn.addEventListener('click', function () {
    search.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(function () { input.focus({ preventScroll: true }); }, 350);
  });
  var searchTop = 0;
  function onScroll() {
    if (!searchTop) { searchTop = search.getBoundingClientRect().top + window.pageYOffset; }
    topBtn.classList.toggle('is-on', window.pageYOffset > searchTop + 1400);
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  /* start from the address bar: ?q=…&topic=… or #term */
  try {
    var params = new URL(window.location.href).searchParams;
    if (params.get('topic')) {
      chips.forEach(function (o) {
        var on = o.getAttribute('data-cat') === params.get('topic');
        if (on) { activeCat = params.get('topic'); }
      });
      chips.forEach(function (o) { o.setAttribute('aria-pressed', (o.getAttribute('data-cat') || '') === activeCat ? 'true' : 'false'); });
    }
    if (params.get('q')) { input.value = params.get('q'); }
  } catch (e) { /* ignore */ }
  render();
  if (window.location.hash.length > 1) {
    var h = decodeURIComponent(window.location.hash.slice(1));
    if (document.getElementById(h) && document.getElementById(h).classList.contains('gl-term')) {
      setTimeout(function () { reveal(h, true); }, 60);
    }
  }
})();
