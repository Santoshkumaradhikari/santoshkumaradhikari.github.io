#!/usr/bin/env python3
"""One-off application of the 2026-08-29 site audit fixes.

Run from the repository root:  python3 tools/apply-audit-fixes.py

What it does (idempotent — safe to re-run):
  1.  Dark-mode fix: table.figures th readable in dark mode.
  2.  Unified footer + investment disclaimer on every Canon page.
  3.  Favicon / apple-touch-icon / theme-color / og:image / twitter:image
      on every page, og:locale corrected to en_GB.
  4.  Per-chapter "First published / Last verified" dates (from git) shown
      on the page and mirrored into datePublished/dateModified in JSON-LD.
  5.  BreadcrumbList JSON-LD on chapters; Book JSON-LD on the hub.
  6.  scope="col" on all data-table header cells.
  7.  Heading ids + an "In this chapter" mini-TOC on long chapters.
  8.  A primary-data-sources note on every chapter.
  9.  Hub: title-filter search box, reading-time pills, clearer hero copy,
      "Whole Book" link labelled with its size.
  10. Mobile: header nav becomes a scrollable row instead of a 3-row wrap.
  11. Google Fonts payload trimmed to the weights the CSS actually uses.
  12. Inline onclick handlers replaced with data attributes + delegated JS.
  13. <noscript> rule so the audio button never shows where it cannot work.
"""

import html
import json
import math
import os
import re
import subprocess
import sys

CANON = "investors-canon"
DOMAIN = "https://santoshkumaradhikari.com.np"
OG_IMAGE = DOMAIN + "/og-image.png"

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, c):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(c)


def git_date(path, first=False):
    """YYYY-MM-DD of the file's first or last commit."""
    args = ["git", "log", "--format=%cs", "--follow", "--", path]
    out = subprocess.run(args, capture_output=True, text=True).stdout.split()
    if not out:
        return None
    return out[-1] if first else out[0]


def pretty(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m)]} {y}"


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.lower()
    text = re.sub(r"[’'\u2019]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60].rstrip("-") or "section"


# --------------------------------------------------------------------------
# Shared snippets
# --------------------------------------------------------------------------

HEAD_ICONS = (
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
    '<meta name="theme-color" content="#16233d">\n'
)

def og_image_block():
    return (
        f'<meta property="og:image" content="{OG_IMAGE}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta property="og:image:alt" content="The Investor&#x27;s Canon — Nepal Edition, by Santosh Kumar Adhikari">\n'
    )

TWITTER_IMAGE = f'<meta name="twitter:image" content="{OG_IMAGE}">\n'

FOOTER_CANON = """<footer class="site-footer">
  <div class="wrap" style="max-width:920px;">
    The Canon is complete and is revised as Nepal's rules and data change. Have a question, correction, or a
    topic you want covered? Reach out via
    <a href="https://santoshkumaradhikari.com.np/">santoshkumaradhikari.com.np</a>.
    <p class="footer-disclaimer">Educational material only. Nothing on this site is investment advice, a solicitation, or a
    recommendation to buy or sell any security. Markets carry risk — always do your own research and consult a
    licensed professional before acting.</p>
    <p class="copyright-line">&copy; <span class="copyright-year">2026</span> Santosh Kumar Adhikari. All rights reserved.</p>
  </div>
</footer>"""

SOURCES_NOTE = """<div class="sources-note">
    <span class="sources-label">Primary data sources</span>
    Figures, rates and rules referenced in this chapter can be verified against the primary sources:
    <a href="https://www.nrb.org.np/" rel="noopener">Nepal Rastra Bank</a> (monetary policy, credit and BFI data),
    <a href="https://www.sebon.gov.np/" rel="noopener">SEBON</a> (regulation and issue approvals),
    <a href="https://www.nepalstock.com/" rel="noopener">NEPSE</a> (prices, indices and turnover),
    <a href="https://www.cdsc.com.np/" rel="noopener">CDSC</a> (settlement and demat data) and
    <a href="https://ird.gov.np/" rel="noopener">Inland Revenue Department</a> (tax rates and rulings).
    If a figure here disagrees with the primary source, trust the primary source and
    <a href="https://santoshkumaradhikari.com.np/">tell me</a>.
  </div>"""

NOSCRIPT_HIDE = "<noscript><style>.nav-audio-btn,.audio-bar{display:none}</style></noscript>\n"

CSS_APPEND = """
/* ================================================================
   2026-08-29 audit fixes
   ================================================================ */

/* Dark mode: table header text used var(--bg), which in dark mode is
   near-black on navy (1.29:1). Use the ink colour instead. */
@media (prefers-color-scheme: dark) {
  table.figures th { color: var(--ink); }
}

/* Mobile header: one scrollable row of links instead of a 3-row wrap. */
@media (max-width: 640px) {
  .header-links {
    flex-basis: 100%;
    display: flex;
    align-items: center;
    gap: 16px;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    padding-bottom: 2px;
  }
  .header-links::-webkit-scrollbar { display: none; }
  .header-links a { margin-left: 0; flex: 0 0 auto; }
}

/* Chapter publication dates */
.chapter-dates {
  font-family: var(--sans);
  font-size: 12.5px;
  color: var(--ink-faint);
  margin: -6px 0 26px;
}

/* "In this chapter" mini-TOC */
.chapter-toc {
  font-family: var(--sans);
  font-size: 14px;
  background: var(--bg-alt);
  border: 1px solid var(--rule);
  border-radius: 10px;
  padding: 16px 20px;
  margin: 0 0 32px;
}
.chapter-toc-label {
  display: block;
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--gold);
  margin-bottom: 8px;
}
.chapter-toc ol { margin: 0; padding-left: 20px; }
.chapter-toc li { margin: 3px 0; }
.chapter-toc a { color: var(--ink-soft); text-decoration: none; }
.chapter-toc a:hover { color: var(--gold); text-decoration: underline; }

/* Primary-sources note at the foot of each chapter */
.sources-note {
  font-family: var(--sans);
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--ink-soft);
  background: var(--bg-alt);
  border-left: 3px solid var(--gold);
  border-radius: 0 10px 10px 0;
  padding: 14px 18px;
  margin: 36px 0 0;
}
.sources-note .sources-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--gold);
  margin-bottom: 6px;
}
.sources-note a { color: inherit; }

/* Footer disclaimer */
.footer-disclaimer {
  margin: 14px auto 0;
  max-width: 720px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ink-faint);
}

/* Hub: chapter filter */
.toc-filter { max-width: 920px; margin: 0 auto 8px; padding: 0 24px; }
.toc-filter input {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--sans);
  font-size: 15px;
  color: var(--ink);
  background: var(--bg-card);
  border: 1px solid var(--rule-strong);
  border-radius: 10px;
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
}
.toc-filter input:focus { outline: 2px solid var(--gold-bright); outline-offset: 1px; }
.toc-filter-empty {
  display: none;
  font-family: var(--sans);
  font-size: 14.5px;
  color: var(--ink-faint);
  text-align: center;
  margin: 18px 0 0;
}
@media print { .toc-filter { display: none !important; } }

/* Reading-time pill keeps the ready style */
.ch-status.ready { white-space: nowrap; }
"""


def ensure(content, marker, addition, anchor, before=False):
    """Insert `addition` at `anchor` unless `marker` already present."""
    if marker in content:
        return content
    if anchor not in content:
        raise SystemExit(f"anchor not found: {anchor[:60]}")
    if before:
        return content.replace(anchor, addition + anchor, 1)
    return content.replace(anchor, anchor + addition, 1)


# --------------------------------------------------------------------------
# Per-page head fixes (all pages, canon and root)
# --------------------------------------------------------------------------

def fix_head(c):
    # favicon block, right before the stylesheet/</head>
    if 'rel="icon"' not in c:
        if '<link rel="stylesheet"' in c:
            c = c.replace('<link rel="stylesheet"', HEAD_ICONS + '<link rel="stylesheet"', 1)
        else:
            c = c.replace("</head>", HEAD_ICONS + "</head>", 1)
    # og:image
    if "og:image" not in c and 'property="og:url"' in c:
        c = re.sub(r'(<meta property="og:url"[^>]*>\n)', r"\1" + og_image_block(), c, count=1)
    # twitter image + large card
    if "twitter:image" not in c and 'name="twitter:card"' in c:
        c = c.replace('<meta name="twitter:card" content="summary">',
                      '<meta name="twitter:card" content="summary_large_image">', 1)
        c = re.sub(r'(<meta name="twitter:card"[^>]*>\n)', r"\1" + TWITTER_IMAGE, c, count=1)
    # locale
    c = c.replace('<meta property="og:locale" content="en_US">',
                  '<meta property="og:locale" content="en_GB">')
    # font payload: drop unused Fraunces 400 and Source Serif 4 500
    c = c.replace("family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600",
                  "family=Fraunces:opsz,wght@9..144,500;9..144,600")
    c = c.replace("family=Source+Serif+4:wght@400;500;600;700",
                  "family=Source+Serif+4:wght@400;600;700")
    return c


def fix_canon_page(c):
    c = fix_head(c)
    # no-JS: never show a dead audio button
    if "noscript" not in c:
        c = c.replace("</head>", NOSCRIPT_HIDE + "</head>", 1)
    # inline handlers -> data attributes (delegated in audio-reader.js)
    c = c.replace(' onclick="window.print()"', ' data-print=""')
    # unified footer + disclaimer
    c = re.sub(r'<footer class="site-footer">.*?</footer>', FOOTER_CANON, c, flags=re.S)
    return c


# --------------------------------------------------------------------------
# Chapter-specific fixes
# --------------------------------------------------------------------------

def fix_chapter(path):
    c = read(path)
    c = fix_canon_page(c)

    published = git_date(path, first=True) or "2026-08-21"
    modified = git_date(path) or published

    # 1. visible dates under the kicker
    if 'class="chapter-dates"' not in c:
        c = re.sub(
            r'(<div class="chapter-kicker">[^<]*</div>\n(?:\s*<h1[^>]*>.*?</h1>))',
            lambda m: m.group(1) + f'\n  <p class="chapter-dates">First published {pretty(published)} · '
                                   f'Last verified {pretty(modified)}</p>',
            c, count=1, flags=re.S)

    # 2. JSON-LD: dates, image, mainEntityOfPage
    def enrich(m):
        data = json.loads(m.group(1))
        data.setdefault("datePublished", published)
        data["dateModified"] = modified
        data.setdefault("image", OG_IMAGE)
        data.setdefault("mainEntityOfPage", data.get("url"))
        return ('<script type="application/ld+json">'
                + json.dumps(data, ensure_ascii=False) + "</script>")
    c = re.sub(r'<script type="application/ld\+json">(\{.*?\})</script>', enrich, c, count=1)

    # 3. BreadcrumbList
    if "BreadcrumbList" not in c:
        title_m = re.search(r"<title>(.*?)(?: — The Investor.s Canon)?</title>", c, re.S)
        page_url_m = re.search(r'rel="canonical" href="([^"]+)"', c)
        crumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "The Investor's Canon",
                 "item": DOMAIN + "/investors-canon/"},
                {"@type": "ListItem", "position": 2,
                 "name": html.unescape(title_m.group(1)).strip(),
                 "item": page_url_m.group(1)},
            ],
        }
        c = re.sub(r"(</script>\n)", r"\1" + '<script type="application/ld+json">'
                   + json.dumps(crumb, ensure_ascii=False) + "</script>\n", c, count=1)

    # 4. th scope
    c = c.replace("<th>", '<th scope="col">')

    # 5. heading ids + mini-TOC (3+ sections only)
    heads = re.findall(r"<h2>(.*?)</h2>", c, re.S)
    if heads and 'class="chapter-toc"' not in c:
        used = set()
        def add_id(m):
            slug = slugify(m.group(1))
            base, i = slug, 2
            while slug in used:
                slug = f"{base}-{i}"; i += 1
            used.add(slug)
            return f'<h2 id="{slug}">{m.group(1)}</h2>'
        c = re.sub(r"<h2>(.*?)</h2>", add_id, c, flags=re.S)
        if len(heads) >= 3:
            items = []
            used2 = set()
            for h in heads:
                slug = slugify(h)
                base, i = slug, 2
                while slug in used2:
                    slug = f"{base}-{i}"; i += 1
                used2.add(slug)
                label = re.sub(r"<[^>]+>", "", h).strip()
                items.append(f'<li><a href="#{slug}">{label}</a></li>')
            toc = ('<nav class="chapter-toc" aria-label="In this chapter">'
                   '<span class="chapter-toc-label">In this chapter</span><ol>'
                   + "".join(items) + "</ol></nav>")
            # place after the dates line (or after h1 if dates missing)
            if 'class="chapter-dates"' in c:
                c = re.sub(r'(<p class="chapter-dates">.*?</p>)', r"\1\n  " + toc, c, count=1)
            else:
                c = re.sub(r"(</h1>)", r"\1\n  " + toc, c, count=1)

    # 6. sources note ahead of prev/next nav
    if 'class="sources-note"' not in c:
        c = c.replace('<div class="chapter-nav">', SOURCES_NOTE + '\n\n  <div class="chapter-nav">', 1)

    write(path, c)


# --------------------------------------------------------------------------
# Hub fixes
# --------------------------------------------------------------------------

def reading_minutes(path):
    c = read(path)
    body = re.search(r'<article class="chapter">(.*?)</article>', c, re.S)
    text = re.sub(r"<[^>]+>", " ", body.group(1) if body else c)
    return max(1, math.ceil(len(text.split()) / 220))


def fix_hub():
    p = os.path.join(CANON, "index.html")
    c = read(p)
    c = fix_canon_page(c)

    # hero: plain words first, honest chapter arithmetic
    c = c.replace(
        "A no-gap, execution-safe, 10-year investing operating system for the Nepali\n"
        "    investor — from Nepal Rastra Bank's credit cycle down to the mechanics of a\n"
        "    single NEPSE trade. 4 volumes, Part 0 plus 18 parts and 118 chapters.",
        "A complete, execution-first investing operating system for the Nepali\n"
        "    investor, built for a ten-year horizon — from Nepal Rastra Bank's credit cycle\n"
        "    down to the mechanics of a single NEPSE trade. 4 volumes, 18 parts, 118 chapters,\n"
        "    plus the three Part 0 framework chapters — 121 chapters in all.")
    c = c.replace("✓ Complete — all 118 chapters drafted and published",
                  "✓ Complete — all 121 chapters (Part 0 + chapters 1–118) are published")

    # Whole Book link: warn about the size
    c = c.replace(
        '<a href="book.html" title="The whole book on one page, ready to save as a single PDF">Whole Book</a>',
        '<a href="book.html" title="The whole book on one page (about 5 MB — best on Wi-Fi or desktop), ready to save as a single PDF">Whole Book <span aria-hidden="true">(~5 MB)</span><span class="visually-hidden">, about five megabytes</span></a>')

    # reading-time pills
    def retime(m):
        href = m.group(1)
        mins = reading_minutes(os.path.join(CANON, href))
        return m.group(0).replace(">Read now →<", f">~{mins} min · Read →<")
    if "min · Read" not in c:
        c = re.sub(r'<a class="chapter-row" href="(chapters/[^"]+)"><span class="ch-num">[^<]*</span>'
                   r'<span class="ch-title">[^<]*</span><span class="ch-status ready">Read now →</span></a>',
                   retime, c)

    # title filter
    if "toc-filter" not in c:
        filter_html = """
<div class="toc-filter">
  <label class="visually-hidden" for="chapter-filter">Filter chapters by title</label>
  <input id="chapter-filter" type="search" placeholder="Filter the 121 chapters by title — e.g. tax, hydropower, IPO…" autocomplete="off">
  <p class="toc-filter-empty" role="status">No chapter titles match. The term may still be covered inside a chapter — try the Glossary.</p>
</div>
"""
        c = re.sub(r'(<section class="roadmap">)', filter_html + r"\1", c, count=1)
        filter_js = """
<script>
  (function () {
    var input = document.getElementById('chapter-filter');
    if (!input) { return; }
    var rows = Array.prototype.slice.call(document.querySelectorAll('.chapter-row'));
    var parts = Array.prototype.slice.call(document.querySelectorAll('.toc-part'));
    var vols = Array.prototype.slice.call(document.querySelectorAll('.volume-title'));
    var empty = document.querySelector('.toc-filter-empty');
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var any = false;
      rows.forEach(function (r) {
        var hit = !q || r.textContent.toLowerCase().indexOf(q) !== -1;
        r.style.display = hit ? '' : 'none';
        if (hit) { any = true; }
      });
      parts.forEach(function (p) {
        var visible = p.querySelector('.chapter-row:not([style*="none"])');
        p.style.display = visible ? '' : 'none';
      });
      vols.forEach(function (v) {
        var section = v;
        while (section && section.tagName !== 'SECTION') { section = section.parentElement; }
        if (!section) { return; }
        var visible = section.querySelector('.chapter-row:not([style*="none"])');
        v.style.display = visible ? '' : 'none';
      });
      if (empty) { empty.style.display = any ? 'none' : 'block'; }
    });
  })();
</script>
"""
        c = c.replace('<script src="js/audio-reader.js" defer></script>',
                      filter_js + '<script src="js/audio-reader.js" defer></script>', 1)

    # upgrade schema: WebPage -> Book with hasPart chapters
    if '"@type":"Book"' not in c and '"@type": "Book"' not in c:
        rows = re.findall(r'href="chapters/([^"]+)"><span class="ch-num">([^<]*)</span>'
                          r'<span class="ch-title">([^<]*)</span>', c)
        has_part = [{
            "@type": "Chapter",
            "position": i + 1,
            "name": html.unescape(t),
            "url": f"{DOMAIN}/investors-canon/chapters/{f}",
        } for i, (f, n, t) in enumerate(rows)]
        book = {
            "@context": "https://schema.org",
            "@type": "Book",
            "name": "The Investor's Canon — Nepal Edition",
            "headline": "The Investor's Canon",
            "description": ("The Investor's Canon — Nepal Edition: a 4-volume, 18-part, 118-chapter "
                            "institution-grade guide to NEPSE investing, written in plain English and "
                            "published in full and revised as Nepal's rules and data change."),
            "url": f"{DOMAIN}/investors-canon/",
            "image": OG_IMAGE,
            "inLanguage": "en",
            "bookFormat": "https://schema.org/EBook",
            "isAccessibleForFree": True,
            "numberOfPages": len(rows),
            "dateModified": git_date(p) or "2026-08-29",
            "author": {"@type": "Person", "name": "Santosh Kumar Adhikari", "url": DOMAIN + "/"},
            "publisher": {"@type": "Person", "name": "Santosh Kumar Adhikari"},
            "hasPart": has_part,
        }
        c = re.sub(r'<script type="application/ld\+json">\{.*?\}</script>',
                   '<script type="application/ld+json">' + json.dumps(book, ensure_ascii=False) + "</script>",
                   c, count=1, flags=re.S)

    write(p, c)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    if not os.path.isdir(CANON):
        sys.exit("Run from the repository root.")

    # CSS
    css_path = os.path.join(CANON, "css", "style.css")
    css = read(css_path)
    if "2026-08-29 audit fixes" not in css:
        css += CSS_APPEND
    # visually-hidden helper if absent
    if ".visually-hidden" not in css:
        css += ("\n.visually-hidden { position: absolute; width: 1px; height: 1px;"
                " margin: -1px; padding: 0; overflow: hidden;"
                " clip: rect(0 0 0 0); white-space: nowrap; border: 0; }\n")
    write(css_path, css)

    # chapters
    chapters = sorted(
        os.path.join(CANON, "chapters", f)
        for f in os.listdir(os.path.join(CANON, "chapters")) if f.endswith(".html"))
    for ch in chapters:
        fix_chapter(ch)
    print(f"chapters fixed: {len(chapters)}")

    # hub
    fix_hub()

    # secondary canon pages
    for name in ("framework.html", "glossary.html", "study-guide.html"):
        p = os.path.join(CANON, name)
        c = fix_canon_page(read(p))
        c = c.replace(
            '<a href="book.html" title="The whole book on one page, ready to save as a single PDF">Whole Book</a>',
            '<a href="book.html" title="The whole book on one page (about 5 MB — best on Wi-Fi or desktop), ready to save as a single PDF">Whole Book <span aria-hidden="true">(~5 MB)</span><span class="visually-hidden">, about five megabytes</span></a>')
        write(p, c)

    # root pages: head fixes only (they have their own footer/design)
    for p in ("index.html", "404.html",
              "research/index.html",
              "research/nabil-bank/index.html" if os.path.exists("research/nabil-bank/index.html") else None,
              "research/chilime-hydropower/index.html" if os.path.exists("research/chilime-hydropower/index.html") else None):
        if p and os.path.exists(p):
            write(p, fix_head(read(p)))

    print("done")


if __name__ == "__main__":
    main()
