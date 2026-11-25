/* Visitor counting for santoshkumaradhikari.com.np (added 25 Nov 2026).

   The counting service is GoatCounter (dashboard: santoshcanon.goatcounter.com).
   It works without cookies and stores no personal data about visitors.

   - Page views are counted by GoatCounter's own count.js, loaded on every page.
   - This file adds "events": a +1 each time someone taps an important button
     or downloads a data file, so the dashboard shows which features are used.
   - It never sends what a visitor types (search words, contact-form text).

   Each event appears in the dashboard under its name, for example
   "click-listen" or "download-nepse-daily-turnover-2022-2026.csv". */
(function () {
  "use strict";

  function send(path, title) {
    var gc = window.goatcounter;
    if (gc && typeof gc.count === "function") {
      try { gc.count({ path: path, title: title || path, event: true }); } catch (e) { /* never break the page */ }
    }
  }

  // Buttons: [CSS selector, event name, description shown in the dashboard]
  var BUTTONS = [
    [".nav-search-btn", "click-search", "Search button"],
    [".nav-audio-btn, .audio-bar-btn", "click-listen", "Listen (read aloud)"],
    [".nav-translate-btn", "click-nepali", "Read in Nepali"],
    ["[data-print], .print-toggle, .print-bar-btn", "click-print", "Print or save as PDF"],
    [".theme-toggle", "click-day-night", "Day/night switch"],
    [".vol-chip", "click-volume-chip", "Volume chip on a chapter"],
    [".features-more a, a.btn-primary[href$='explore.html']", "click-take-the-tour", "Take the full tour"]
  ];

  // Sister sites on the same domain
  var SISTER = [
    [/^\/cv-website\//, "click-cv", "Opened the CV site"],
    [/^\/gosaikunda-website\//, "click-gosaikunda-atlas", "Opened the Gosaikunda Field Atlas"]
  ];

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) { return; }

    for (var i = 0; i < BUTTONS.length; i++) {
      if (t.closest(BUTTONS[i][0])) { send(BUTTONS[i][1], BUTTONS[i][2]); return; }
    }

    var a = t.closest("a[href]");
    if (!a) { return; }
    var url;
    try { url = new URL(a.getAttribute("href"), window.location.href); } catch (err) { return; }

    if (url.protocol === "mailto:") { send("click-email", "Email link"); return; }

    if (url.host === window.location.host) {
      var file = url.pathname.match(/\/data\/([^\/]+\.(?:csv|json|py))$/i);
      if (file) { send("download-" + file[1], "Download: " + file[1]); return; }
      if (/feed\.xml$/.test(url.pathname)) { send("click-feed", "Updates feed"); return; }
      for (var j = 0; j < SISTER.length; j++) {
        if (SISTER[j][0].test(url.pathname)) { send(SISTER[j][1], SISTER[j][2]); return; }
      }
      return; // ordinary page links are already counted as page views
    }

    if (url.protocol === "http:" || url.protocol === "https:") {
      send("out-" + url.host, "Outbound link: " + url.host);
    }
  }, true);

  // Contact form on the home page: count that it was used, never its contents
  document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "contactForm") { send("contact-form-used", "Contact form used"); }
  }, true);
})();
