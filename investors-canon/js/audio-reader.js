(function injectCopyright() {
  var footer = document.querySelector('.site-footer .wrap');
  if (!footer) { return; }
  var line = footer.querySelector('.copyright-line');
  if (!line) {
    // No-JS fallback markup is absent on this page — build the line from scratch.
    line = document.createElement('p');
    line.className = 'copyright-line';
    line.innerHTML = '© <span class="copyright-year"></span> Santosh Kumar Adhikari. All rights reserved.';
    footer.appendChild(line);
  }
  // Keep the year current whether the line was server-rendered or injected here.
  var yearEl = line.querySelector('.copyright-year');
  if (yearEl) { yearEl.textContent = new Date().getFullYear(); }
})();

(function () {
  if (!('speechSynthesis' in window)) {
    var hideEls = document.querySelectorAll('.nav-audio-btn, .audio-bar');
    for (var h = 0; h < hideEls.length; h++) { hideEls[h].style.display = 'none'; }
    return;
  }

  var synth = window.speechSynthesis;
  var state = 'idle'; // idle | playing | paused
  var chunks = [];
  var currentIndex = -1;
  var currentRate = 1;
  var currentVoiceURI = '';
  var voicesList = [];
  var gen = 0; // generation counter to ignore stale onend/onerror callbacks
  var bar = null; // floating player DOM refs, built once

  /* ---------- preferences (best-effort; site still works if storage is blocked) ---------- */
  function loadPrefs() {
    try {
      var r = window.localStorage.getItem('canon-audio-rate');
      if (r) { currentRate = parseFloat(r) || 1; }
      var v = window.localStorage.getItem('canon-audio-voice');
      if (v) { currentVoiceURI = v; }
    } catch (e) { /* ignore */ }
  }
  function saveRate(rate) {
    try { window.localStorage.setItem('canon-audio-rate', String(rate)); } catch (e) { /* ignore */ }
  }
  function saveVoice(uri) {
    try { window.localStorage.setItem('canon-audio-voice', uri); } catch (e) { /* ignore */ }
  }


  /* ---------- pronunciation ----------
     Speech engines mangle the shorthand this book uses constantly. Left
     untouched, "NRB" becomes a word, "2081/82" becomes "two thousand and
     eighty-one slash eighty-two", and an em-dash gets no pause at all, which
     is a large part of why synthetic reading sounds mechanical. This rewrites
     the *spoken* string only; nothing on the page changes. */

  var SPOKEN = {
    'NEPSE': 'NEP-see',
    'NRB': 'N R B',
    'SEBON': 'SEE-bon',
    'CDSC': 'C D S C',
    'ASBA': 'AZ-buh',
    'BOID': 'B O I D',
    'TMS': 'T M S',
    'IPO': 'I P O',
    'FPO': 'F P O',
    'AGM': 'A G M',
    'NAV': 'N A V',
    'EPS': 'E P S',
    'ROE': 'R O E',
    'ROA': 'R O A',
    'NPL': 'N P L',
    'CAR': 'C A R',
    'CASA': 'CAH-suh',
    'NIM': 'N I M',
    'DCF': 'D C F',
    'DDM': 'D D M',
    'XIRR': 'X I R R',
    'TWR': 'T W R',
    'PPA': 'P P A',
    'COD': 'C O D',
    'NEA': 'N E A',
    'MFI': 'M F I',
    'CGT': 'C G T',
    'GDP': 'G D P',
    'CPI': 'C P I',
    'CRR': 'C R R',
    'SLR': 'S L R',
    'NFRS': 'N F R S',
    'EDIS': 'E D I S',
    'GLOF': 'glof'
  };

  function speechify(text) {
    var s = text;

    // Fiscal years: 2081/82 -> "2081 to 82" (engines say "slash" otherwise)
    s = s.replace(/\b(\d{4})\/(\d{2})\b/g, '$1 to $2');

    // Ratios: 1:1 -> "1 to 1"
    s = s.replace(/\b(\d+)\s*:\s*(\d+)\b/g, '$1 to $2');

    // Valuation multiples: 2.19x -> "2.19 times"
    s = s.replace(/\b(\d+(?:\.\d+)?)x\b/g, '$1 times');

    // Currency and symbols
    s = s.replace(/\bRs\.?\s?(?=\d)/g, 'rupees ');
    s = s.replace(/\bNPR\s?(?=\d)/g, 'rupees ');
    s = s.replace(/(\d)\s?%/g, '$1 percent');

    // Acronyms, whole-word only so "CAR" inside "CARE" is untouched
    for (var key in SPOKEN) {
      if (!Object.prototype.hasOwnProperty.call(SPOKEN, key)) { continue; }
      s = s.replace(new RegExp('\\b' + key + '\\b', 'g'), SPOKEN[key]);
    }

    // Dashes become real pauses rather than being swallowed silently
    s = s.replace(/\s*[\u2014\u2013]\s*/g, ', ');

    return s;
  }

  /* ---------- content extraction ---------- */
  function getReadableChunks() {
    var root = document.querySelector('.chapter, .framework-page');
    var container = (root || document.body).cloneNode(true);
    var stripSelector = root
      ? '.chapter-nav, .print-bar, .audio-bar, .audio-player-bar, script'
      : '.site-header, .site-footer, .reading-progress-container, .print-bar, .audio-bar, .audio-player-bar, script';
    var strip = container.querySelectorAll(stripSelector);
    for (var i = 0; i < strip.length; i++) { strip[i].parentNode.removeChild(strip[i]); }

    var nodes = container.querySelectorAll('h1, h2, h3, h4, p, li, blockquote');
    var out = [];
    for (var j = 0; j < nodes.length; j++) {
      var t = (nodes[j].textContent || '').replace(/\s+/g, ' ').trim();
      if (t) { out.push(speechify(t)); }
    }
    if (!out.length) {
      var whole = (container.textContent || '').replace(/\s+/g, ' ').trim();
      if (whole) { out.push(whole); }
    }
    return out;
  }

  /* ---------- floating player bar (built once, reused) ---------- */
  function svg(pathHtml, viewBox) {
    return '<svg viewBox="' + (viewBox || '0 0 24 24') + '" aria-hidden="true" fill="currentColor">' + pathHtml + '</svg>';
  }
  var ICON_PLAY = svg('<path d="M6 4l14 8-14 8V4z"></path>');
  var ICON_PAUSE = svg('<rect x="5" y="4" width="4" height="16" rx="1"></rect><rect x="15" y="4" width="4" height="16" rx="1"></rect>');
  var ICON_BACK = svg('<path d="M11 19l-9-7 9-7v14z"></path><path d="M22 19l-9-7 9-7v14z"></path>', '0 0 24 24');
  var ICON_FWD = svg('<path d="M13 5l9 7-9 7V5z"></path><path d="M2 5l9 7-9 7V5z"></path>', '0 0 24 24');
  var ICON_CLOSE = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"></path></svg>';

  function buildBar() {
    if (bar) { return bar; }
    var el = document.createElement('div');
    el.className = 'audio-player-bar';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Audio player');
    el.hidden = true;
    el.innerHTML =
      '<div class="ap-inner">' +
        '<button type="button" class="ap-btn ap-back" title="Previous paragraph" aria-label="Previous paragraph">' + ICON_BACK + '</button>' +
        '<button type="button" class="ap-btn ap-playpause" title="Play" aria-label="Play">' + ICON_PLAY + '</button>' +
        '<button type="button" class="ap-btn ap-fwd" title="Next paragraph" aria-label="Next paragraph">' + ICON_FWD + '</button>' +
        '<div class="ap-progress">' +
          '<div class="ap-progress-text">Paragraph 0 of 0</div>' +
          '<div class="ap-progress-track"><div class="ap-progress-fill"></div></div>' +
        '</div>' +
        '<select class="ap-speed" title="Playback speed" aria-label="Playback speed">' +
          '<option value="1">1x</option>' +
          '<option value="1.25">1.25x</option>' +
          '<option value="1.5">1.5x</option>' +
          '<option value="2">2x</option>' +
        '</select>' +
        '<select class="ap-voice" title="Voice" aria-label="Voice"><option value="">Default voice</option></select>' +
        '<button type="button" class="ap-btn ap-close" title="Close player" aria-label="Close player">' + ICON_CLOSE + '</button>' +
      '</div>';
    document.body.appendChild(el);

    bar = {
      root: el,
      back: el.querySelector('.ap-back'),
      playpause: el.querySelector('.ap-playpause'),
      fwd: el.querySelector('.ap-fwd'),
      progressText: el.querySelector('.ap-progress-text'),
      progressFill: el.querySelector('.ap-progress-fill'),
      speed: el.querySelector('.ap-speed'),
      voice: el.querySelector('.ap-voice'),
      close: el.querySelector('.ap-close')
    };

    bar.back.addEventListener('click', function () { speak(currentIndex - 1); });
    bar.fwd.addEventListener('click', function () { speak(currentIndex + 1); });
    bar.playpause.addEventListener('click', function () { playPauseToggle(); });
    bar.close.addEventListener('click', function () { stopPlayer(); });
    bar.speed.addEventListener('change', function () {
      currentRate = parseFloat(bar.speed.value) || 1;
      saveRate(currentRate);
      if (state === 'playing' || state === 'paused') { speak(currentIndex); }
    });
    bar.voice.addEventListener('change', function () {
      currentVoiceURI = bar.voice.value;
      saveVoice(currentVoiceURI);
      if (state === 'playing' || state === 'paused') { speak(currentIndex); }
    });

    return bar;
  }

  function populateVoices() {
    var b = buildBar();
    voicesList = synth.getVoices ? synth.getVoices() : [];
    if (!voicesList.length) { return; }
    var current = b.voice.value;
    b.voice.innerHTML = '<option value="">Default voice</option>';
    for (var i = 0; i < voicesList.length; i++) {
      var v = voicesList[i];
      var opt = document.createElement('option');
      opt.value = v.voiceURI;
      opt.textContent = v.name + (v.lang ? ' (' + v.lang + ')' : '');
      b.voice.appendChild(opt);
    }
    var target = currentVoiceURI || current;
    if (target) {
      var match = false;
      for (var j = 0; j < b.voice.options.length; j++) {
        if (b.voice.options[j].value === target) { match = true; break; }
      }
      if (match) { b.voice.value = target; }
    }
  }
  if (synth.addEventListener) {
    synth.addEventListener('voiceschanged', populateVoices);
  } else {
    synth.onvoiceschanged = populateVoices;
  }

  /* Voices the platforms ship that actually sound human, best first. The
     browser's own default is frequently a legacy formant-synth voice, which
     is what produces the "robot" impression, so we pick deliberately rather
     than letting it choose. Matched case-insensitively on substrings. */
  var PREFERRED_VOICES = [
    'microsoft aria online',      // Edge neural, excellent
    'microsoft guy online',
    'microsoft libby online',
    'microsoft sonia online',
    'google uk english female',   // Chrome, natural
    'google uk english male',
    'google us english',
    'ava (premium)',              // macOS high quality
    'ava (enhanced)',
    'samantha (enhanced)',
    'serena (premium)',
    'daniel (enhanced)',
    'samantha',                   // macOS default-but-decent
    'daniel',
    'karen',
    'moira',
    'tessa'
  ];

  /* Voices to actively avoid: novelty and legacy formant voices that some
     browsers still return first. */
  var POOR_VOICES = ['albert', 'bad news', 'bahh', 'bells', 'boing', 'bubbles',
    'cellos', 'deranged', 'fred', 'good news', 'jester', 'junior', 'kathy',
    'organ', 'ralph', 'superstar', 'trinoids', 'whisper', 'wobble', 'zarvox'];

  function scoreVoice(v) {
    var name = (v.name || '').toLowerCase();
    for (var p = 0; p < POOR_VOICES.length; p++) {
      if (name.indexOf(POOR_VOICES[p]) !== -1) { return -1; }
    }
    for (var i = 0; i < PREFERRED_VOICES.length; i++) {
      if (name.indexOf(PREFERRED_VOICES[i]) !== -1) {
        return 1000 - i;                       // earlier in list = better
      }
    }
    var s = 0;
    if (/en[-_]GB/i.test(v.lang)) { s += 40; } // book is British-spelled
    else if (/^en/i.test(v.lang)) { s += 30; }
    if (/natural|neural|premium|enhanced/i.test(name)) { s += 50; }
    if (v.localService === false) { s += 10; } // cloud voices usually better
    return s;
  }

  /* Best available English voice, used when the reader has not chosen one. */
  function pickBestVoice() {
    if (!voicesList.length) { return null; }
    var best = null, bestScore = -1;
    for (var i = 0; i < voicesList.length; i++) {
      var v = voicesList[i];
      if (!/^en/i.test(v.lang || '')) { continue; }
      var s = scoreVoice(v);
      if (s > bestScore) { bestScore = s; best = v; }
    }
    return bestScore > 0 ? best : null;
  }

  function getSelectedVoice() {
    if (currentVoiceURI && voicesList.length) {
      for (var i = 0; i < voicesList.length; i++) {
        if (voicesList[i].voiceURI === currentVoiceURI) { return voicesList[i]; }
      }
    }
    // No explicit choice: pick the best available rather than the browser default.
    return pickBestVoice();
  }

  /* ---------- old trigger buttons (nav icon + bottom labeled button) ---------- */
  function updateTriggerButtons() {
    var buttons = document.querySelectorAll('.nav-audio-btn, .audio-bar-btn');
    var isActive = state === 'playing' || state === 'paused';
    var label = state === 'playing' ? 'Pause' : (state === 'paused' ? 'Resume Listening' : 'Listen to this Page');
    var aria = state === 'playing' ? 'Pause reading' : (state === 'paused' ? 'Resume reading' : 'Read this page aloud');
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      if (isActive) { btn.classList.add('is-playing'); } else { btn.classList.remove('is-playing'); }
      btn.setAttribute('aria-label', aria);
      btn.setAttribute('title', aria);
      var labelEl = btn.querySelector('.audio-btn-label');
      if (labelEl) { labelEl.textContent = label; }
    }
  }

  function updateBarUI() {
    var b = buildBar();
    var active = state === 'playing' || state === 'paused';
    b.root.hidden = !active;
    b.playpause.innerHTML = state === 'playing' ? ICON_PAUSE : ICON_PLAY;
    b.playpause.setAttribute('aria-label', state === 'playing' ? 'Pause' : 'Play');
    b.playpause.setAttribute('title', state === 'playing' ? 'Pause' : 'Play');
    var total = chunks.length;
    var pos = Math.min(currentIndex + 1, total);
    b.progressText.textContent = total ? ('Paragraph ' + pos + ' of ' + total) : 'Paragraph 0 of 0';
    b.progressFill.style.width = total ? (Math.max(0, pos) / total * 100) + '%' : '0%';
    b.back.disabled = currentIndex <= 0;
    b.fwd.disabled = total ? currentIndex >= total - 1 : true;
    b.speed.value = String(currentRate);
    if (currentVoiceURI) { b.voice.value = currentVoiceURI; }
  }

  function updateAll() {
    updateTriggerButtons();
    updateBarUI();
  }

  /* ---------- playback core ---------- */
  function speak(index) {
    if (!chunks.length) { return; }
    if (index < 0) { index = 0; }
    if (index >= chunks.length) { stopPlayer(); return; }
    currentIndex = index;
    gen++;
    var myGen = gen;
    var utterance = new SpeechSynthesisUtterance(chunks[index]);
    utterance.rate = currentRate;
    /* Slightly below the engine default: long-form prose read at pitch 1.0
       sounds clipped and mechanical. 0.95 is noticeably warmer without
       sounding slowed down. */
    utterance.pitch = 0.95;
    utterance.volume = 1;
    var voice = getSelectedVoice();
    if (voice) {
      try { utterance.voice = voice; } catch (e) { /* invalid/stale voice reference; fall back to default */ }
    }
    utterance.onend = function () {
      if (myGen !== gen) { return; }
      if (state === 'playing') {
        if (currentIndex + 1 < chunks.length) { speak(currentIndex + 1); }
        else { stopPlayer(); }
      }
    };
    utterance.onerror = function () { /* interrupted by cancel() elsewhere; ignore */ };
    try {
      synth.cancel();
      synth.speak(utterance);
    } catch (e) { /* ignore transient speechSynthesis errors */ }
    state = 'playing';
    updateAll();
  }

  function openAndPlay() {
    chunks = getReadableChunks();
    if (!chunks.length) { return; }
    populateVoices();
    speak(0);
  }

  function playPauseToggle() {
    if (state === 'idle') {
      openAndPlay();
    } else if (state === 'playing') {
      synth.pause();
      state = 'paused';
      updateAll();
    } else if (state === 'paused') {
      synth.resume();
      state = 'playing';
      updateAll();
    }
  }

  function stopPlayer() {
    gen++;
    synth.cancel();
    state = 'idle';
    currentIndex = -1;
    updateAll();
  }

  /* ---------- wire up ---------- */
  loadPrefs();
  buildBar();
  var triggers = document.querySelectorAll('.nav-audio-btn, .audio-bar-btn');
  for (var k = 0; k < triggers.length; k++) {
    triggers[k].addEventListener('click', playPauseToggle);
  }
  window.addEventListener('beforeunload', function () { synth.cancel(); });
  updateAll();
})();
