/* Canon Nepali translation toggle — powered by Google Translate.
   The nav button sets/clears the `googtrans` cookie (/en/ne) and reloads;
   when the cookie is active on load, the Google Translate element is
   injected (hidden) and auto-translates the page to Nepali. */
(function () {
  'use strict';

  var COOKIE = 'googtrans';

  function getCookie() {
    var m = document.cookie.match(/(?:^|;\s*)googtrans=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function setCookie(value) {
    var host = location.hostname;
    var domains = ['', host];
    if (host.indexOf('.') !== -1) domains.push('.' + host);
    domains.forEach(function (d) {
      var dom = d ? '; domain=' + d : '';
      if (value === null) {
        document.cookie = COOKIE + '=; path=/' + dom + '; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      } else {
        document.cookie = COOKIE + '=' + value + '; path=/' + dom;
      }
    });
  }

  var active = /\/ne$/.test(getCookie());

  function updateButtons() {
    var btns = document.querySelectorAll('.nav-translate-btn');
    for (var i = 0; i < btns.length; i++) {
      var btn = btns[i];
      btn.textContent = active ? 'EN' : 'नेपाली';
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      btn.title = active
        ? 'Switch back to English'
        : 'Read this page in Nepali (Google Translate)';
      btn.setAttribute('aria-label', btn.title);
      if (active) btn.classList.add('is-active');
      else btn.classList.remove('is-active');
    }
  }

  window.canonTranslateInit = function () {
    /* global google */
    new google.translate.TranslateElement(
      { pageLanguage: 'en', includedLanguages: 'ne,en', autoDisplay: false },
      'google_translate_element'
    );
  };

  function loadWidget() {
    if (document.getElementById('canon-gt-script')) return;
    var holder = document.createElement('div');
    holder.id = 'google_translate_element';
    holder.className = 'gt-hidden notranslate';
    document.body.appendChild(holder);
    var s = document.createElement('script');
    s.id = 'canon-gt-script';
    s.src = 'https://translate.google.com/translate_a/element.js?cb=canonTranslateInit';
    s.defer = true;
    document.body.appendChild(s);
  }

  function onClick() {
    if (active) {
      setCookie(null);
    } else {
      setCookie('/en/ne');
    }
    location.reload();
  }

  function bind() {
    updateButtons();
    var btns = document.querySelectorAll('.nav-translate-btn');
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener('click', onClick);
    }
    if (active) loadWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
