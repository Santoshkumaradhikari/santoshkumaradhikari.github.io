(function () {
  if (!('speechSynthesis' in window)) {
    var hide = document.querySelectorAll('.nav-audio-btn, .audio-bar');
    for (var h = 0; h < hide.length; h++) { hide[h].style.display = 'none'; }
    return;
  }

  var synth = window.speechSynthesis;
  var state = 'idle'; // idle | playing | paused

  function getReadableText() {
    var root = document.querySelector('.chapter, .framework-page');
    var container = (root || document.body).cloneNode(true);
    var stripSelector = root
      ? '.chapter-nav, .print-bar, .audio-bar, script'
      : '.site-header, .site-footer, .reading-progress-container, .print-bar, .audio-bar, script';
    var strip = container.querySelectorAll(stripSelector);
    for (var i = 0; i < strip.length; i++) { strip[i].parentNode.removeChild(strip[i]); }
    return (container.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function updateButtons() {
    var buttons = document.querySelectorAll('.nav-audio-btn, .audio-bar-btn');
    var label = state === 'playing' ? 'Pause' : (state === 'paused' ? 'Resume Listening' : 'Listen to this Page');
    var aria = state === 'playing' ? 'Pause reading' : (state === 'paused' ? 'Resume reading' : 'Read this page aloud');
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      if (state === 'playing') { btn.classList.add('is-playing'); } else { btn.classList.remove('is-playing'); }
      btn.setAttribute('aria-label', aria);
      btn.setAttribute('title', aria);
      var labelEl = btn.querySelector('.audio-btn-label');
      if (labelEl) { labelEl.textContent = label; }
    }
  }

  function reset() {
    state = 'idle';
    updateButtons();
  }

  function toggle() {
    if (state === 'idle') {
      var text = getReadableText();
      if (!text) { return; }
      var utterance = new SpeechSynthesisUtterance(text);
      utterance.onend = reset;
      utterance.onerror = reset;
      synth.cancel();
      synth.speak(utterance);
      state = 'playing';
    } else if (state === 'playing') {
      synth.pause();
      state = 'paused';
    } else {
      synth.resume();
      state = 'playing';
    }
    updateButtons();
  }

  var controls = document.querySelectorAll('.nav-audio-btn, .audio-bar-btn');
  for (var j = 0; j < controls.length; j++) {
    controls[j].addEventListener('click', toggle);
  }
  window.addEventListener('beforeunload', function () { synth.cancel(); });
  updateButtons();
})();
