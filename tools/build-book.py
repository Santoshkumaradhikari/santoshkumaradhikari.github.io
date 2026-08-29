#!/usr/bin/env python3
"""Generate investors-canon/book.html — the whole Canon on one printable page.

Run from the repository root:

    python3 tools/build-book.py

Why a page rather than a committed PDF: a real PDF would be a ~10 MB binary in
git that silently goes stale the moment any chapter is edited, and there is no
PDF engine in this toolchain to regenerate it reliably. A single HTML page that
the browser prints gives the same result — one file, one PDF — stays in sync
because it is rebuilt from the chapters themselves, and costs the repository a
few hundred KB of text instead of megabytes of binary.

The per-chapter print buttons are untouched. This is purely additive.

Reads investors-canon/index.html for the authoritative order, then splices in
each chapter's <article> element. Nothing is retyped, so the merged book cannot
drift from the individual chapters.
"""

import html
import os
import re
import sys

CANON = "investors-canon"
OUT = os.path.join(CANON, "book.html")
DOMAIN = "https://santoshkumaradhikari.com.np"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def build_structure(idx):
    """Walk the TOC in document order, yielding volumes, parts and chapters."""
    pattern = re.compile(
        r'<h2 class="volume-title">(?P<vol>.*?)</h2>'
        r'|<div class="toc-part-head"><span class="part-roman">(?P<roman>[^<]+)</span>'
        r'(?P<pname>[^<]*)</div>'
        r'|href="chapters/(?P<file>[^"]+)"><span class="ch-num">(?P<num>[^<]*)</span>'
        r'<span class="ch-title">(?P<title>[^<]*)</span>',
        re.S,
    )
    for m in pattern.finditer(idx):
        if m.group("vol") is not None:
            yield ("volume", re.sub(r"<[^>]+>", "", m.group("vol")).strip())
        elif m.group("roman") is not None:
            yield ("part", m.group("roman").strip(), m.group("pname").strip())
        else:
            yield ("chapter", m.group("file"), m.group("num"), m.group("title"))


def extract_article(path):
    """Pull a chapter's <article> body, minus anything that is page furniture."""
    c = read(path)
    m = re.search(r'<article class="chapter">(.*?)</article>', c, re.S)
    if not m:
        return None
    body = m.group(1)
    # prev/next navigation is meaningless in a single continuous document
    body = re.sub(r'<div class="chapter-nav">.*?</div>', "", body, flags=re.S)
    # the per-chapter mini-TOC links to heading ids that are not unique once
    # 121 chapters share one page, so drop it and the ids it points at
    body = re.sub(r'<nav class="chapter-toc".*?</nav>', "", body, flags=re.S)
    body = re.sub(r'<h2 id="[^"]*">', "<h2>", body)
    # a document has one <h1>; chapter titles become styled <h2>s here
    body = re.sub(r"<h1>(.*?)</h1>", r'<h2 class="bk-ch-title">\1</h2>', body, flags=re.S)
    # Chapters link to each other by filename. Inside the merged book those
    # relative paths do not resolve, so point them at the in-page anchors.
    body = re.sub(
        r'href="(ch-[0-9-]+)-[^"#]*\.html"',
        lambda mm: 'href="#' + mm.group(1).rstrip("-") + '"',
        body,
    )
    return body.strip()


def main():
    if not os.path.isdir(CANON):
        sys.exit("Run this from the repository root.")

    idx = read(os.path.join(CANON, "index.html"))
    pieces = []
    toc = []
    n_ch = n_vol = n_part = 0

    for item in build_structure(idx):
        if item[0] == "volume":
            n_vol += 1
            title = html.unescape(item[1])
            pieces.append(
                '<section class="bk-volume">\n'
                f'  <h2 class="bk-volume-title">{html.escape(title)}</h2>\n'
                "</section>"
            )
            toc.append(f'<li class="bk-toc-vol">{html.escape(title)}</li>')

        elif item[0] == "part":
            n_part += 1
            roman, name = item[1], html.unescape(item[2])
            pieces.append(
                '<section class="bk-part">\n'
                f'  <p class="bk-part-roman">{html.escape(roman)}</p>\n'
                f"  <h2>{html.escape(name)}</h2>\n"
                "</section>"
            )
            toc.append(
                f'<li class="bk-toc-part">{html.escape(roman)} &mdash; '
                f"{html.escape(name)}</li>"
            )

        else:
            _, fname, num, title = item
            path = os.path.join(CANON, "chapters", fname)
            body = extract_article(path)
            if body is None:
                print("  skipped (no article): " + fname)
                continue
            n_ch += 1
            anchor = "ch-" + num.replace(".", "-")
            pieces.append(
                f'<article class="chapter bk-chapter" id="{anchor}">\n{body}\n</article>'
            )
            toc.append(
                f'<li class="bk-toc-ch"><a href="#{anchor}">'
                f'<span class="bk-toc-num">{html.escape(num)}</span>'
                f"{title}</a></li>"
            )

    doc = TEMPLATE.format(
        domain=DOMAIN,
        toc="\n      ".join(toc),
        body="\n\n".join(pieces),
        n_ch=n_ch,
    )
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)

    size = os.path.getsize(OUT)
    print(f"  {OUT} written")
    print(f"  {n_vol} volumes, {n_part} parts, {n_ch} chapters")
    print(f"  {size / 1048576:.2f} MB")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Investor's Canon &mdash; Complete Book (Print Edition)</title>
<meta name="description" content="The complete Investor's Canon on a single page: all 121 chapters across four volumes, formatted for printing or saving as one PDF.">
<link rel="canonical" href="{domain}/investors-canon/book.html">
<meta property="og:type" content="book">
<meta property="og:title" content="The Investor's Canon &mdash; Complete Book (Print Edition)">
<meta property="og:description" content="The complete Investor's Canon on a single page: all 121 chapters across four volumes, formatted for printing or saving as one PDF.">
<meta property="og:url" content="{domain}/investors-canon/book.html">
<meta property="og:image" content="{domain}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Investor's Canon &mdash; Nepal Edition, by Santosh Kumar Adhikari">
<meta property="og:site_name" content="Santosh Kumar Adhikari">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{domain}/og-image.png">
<meta name="twitter:title" content="The Investor's Canon &mdash; Complete Book (Print Edition)">
<meta name="twitter:description" content="The complete Investor's Canon on a single page: all 121 chapters across four volumes, formatted for printing or saving as one PDF.">
<meta name="author" content="Santosh Kumar Adhikari">
<meta name="robots" content="noindex, follow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Serif+4:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#16233d">
<link rel="stylesheet" href="css/style.css">
<style>
  /* ---- single-document layout, screen ---- */
  .bk-hero {{ max-width: 820px; margin: 0 auto; padding: 64px 24px 32px; text-align: center; }}
  .bk-hero h1 {{ font-family: var(--display); font-size: 46px; line-height: 1.12; margin: 0 0 18px; font-weight: 500; }}
  .bk-actions {{ margin: 26px 0 8px; }}
  .bk-note {{ font-family: var(--sans); font-size: 13.5px; color: var(--ink-soft); max-width: 60ch; margin: 0 auto; }}

  .bk-toc {{ max-width: 820px; margin: 0 auto 40px; padding: 0 24px; font-family: var(--sans); }}
  .bk-toc ul {{ list-style: none; padding: 0; margin: 0; }}
  .bk-toc li {{ padding: 3px 0; }}
  .bk-toc-vol {{ font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;
                font-size: 12.5px; margin-top: 22px; color: var(--gold); }}
  .bk-toc-part {{ font-weight: 600; font-size: 13.5px; margin-top: 12px; color: var(--ink-soft); }}
  .bk-toc-ch a {{ display: flex; gap: 12px; font-size: 14px; color: var(--ink); text-decoration: none; }}
  .bk-toc-ch a:hover {{ color: var(--gold); }}
  .bk-toc-num {{ min-width: 42px; color: var(--ink-faint); font-variant-numeric: tabular-nums; }}

  .bk-volume {{ max-width: 820px; margin: 0 auto; padding: 56px 24px 8px; text-align: center; }}
  .bk-volume .bk-volume-title {{ font-family: var(--display); font-size: 34px; font-weight: 500; margin: 0;
                  border-top: 2px solid var(--gold); border-bottom: 2px solid var(--gold); padding: 18px 0; }}
  .bk-chapter .bk-ch-title {{ font-family: var(--display); font-size: 38px; line-height: 1.22;
                  margin: 0 0 34px; font-weight: 500; letter-spacing: -0.01em; border: 0; padding: 0; }}
  /* the merged page repeats each chapter's dates + sources note; keep them,
     they are correct per chapter */
  .bk-part {{ max-width: 820px; margin: 0 auto; padding: 34px 24px 4px; }}
  .bk-part-roman {{ font-family: var(--sans); font-size: 12px; font-weight: 700;
                   letter-spacing: 0.16em; text-transform: uppercase; color: var(--gold); margin: 0 0 6px; }}
  .bk-part h2 {{ font-family: var(--display); font-size: 25px; font-weight: 500; margin: 0; border: 0; padding: 0; }}
  .bk-chapter {{ border-top: 1px solid var(--rule); }}

  /* ---- print: one continuous PDF ---- */
  @media print {{
    .skip-link, .site-header, .site-footer, .bk-actions, .print-bar,
    .audio-bar, .audio-player-bar, .nav-audio-btn, .nav-print-btn,
    .reading-progress-container {{ display: none !important; }}

    /* each volume, part and chapter starts on a fresh sheet */
    .bk-volume, .bk-part, .bk-chapter {{ break-before: page; page-break-before: always; }}
    .bk-hero, .bk-toc {{ break-after: page; page-break-after: always; }}
    .bk-hero {{ padding-top: 22vh; }}

    .bk-toc-ch a {{ color: #000 !important; }}
    .bk-chapter {{ border-top: 0; }}

    /* keep headings with the text that follows them */
    h1, h2, h3 {{ break-after: avoid; page-break-after: avoid; }}
    table, .callout, .recap, blockquote {{ break-inside: avoid; page-break-inside: avoid; }}
    p, li {{ orphans: 3; widows: 3; }}
  }}

  @page {{ margin: 18mm 16mm; }}
</style>
</head>
<body>

<a href="#main" class="skip-link">Skip to main content</a>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html">The Investor's <span>Canon</span></a>
    <nav class="header-links">
      <a href="index.html">Contents</a>
      <a href="framework.html">Framework</a>
      <a href="study-guide.html">Study Guide</a>
      <a href="glossary.html">Glossary</a>
      <a href="{domain}/">Santosh Adhikari &rarr;</a>
      <button type="button" class="nav-translate-btn notranslate" aria-pressed="false" aria-label="Read this page in Nepali (Google Translate)" title="Read this page in Nepali (Google Translate)">नेपाली</button>
    </nav>
  </div>
</header>

<main id="main" tabindex="-1">

  <div class="bk-hero">
    <h1>The Investor's Canon</h1>
    <p class="bk-note">
      The complete book on one page &mdash; all {n_ch} chapters across four volumes,
      in reading order. Use your browser's Print command and choose
      <strong>Save as PDF</strong> to get the whole Canon as a single file.
    </p>
    <p class="bk-actions">
      <button type="button" class="btn btn-primary" data-print="">Save the whole book as PDF</button>
      <a class="btn btn-ghost" href="index.html">Back to Contents</a>
    </p>
    <p class="bk-note">
      This is a large document. Give the page a moment to finish laying out
      before printing, and expect the PDF to run to several hundred pages.
      Individual chapters can still be printed on their own from any chapter page.
    </p>
  </div>

  <nav class="bk-toc" aria-label="Table of contents">
    <ul>
      {toc}
    </ul>
  </nav>

{body}

</main>

<footer class="site-footer">
  <div class="wrap" style="max-width:920px;">
    The Canon is complete and is revised as Nepal's rules and data change. Have a question, correction, or a
    topic you want covered? Reach out via
    <a href="{domain}/">santoshkumaradhikari.com.np</a>.
    <p class="footer-disclaimer">Educational material only. Nothing on this site is investment advice, a solicitation, or a
    recommendation to buy or sell any security. Markets carry risk &mdash; always do your own research and consult a
    licensed professional before acting.</p>
    <p class="copyright-line">&copy; <span class="copyright-year">2026</span> Santosh Kumar Adhikari. All rights reserved.</p>
  </div>
</footer>

<script>
  (function () {{
    var y = document.querySelector('.copyright-year');
    if (y) {{ y.textContent = new Date().getFullYear(); }}
    document.addEventListener('click', function (e) {{
      var el = e.target;
      while (el && el !== document) {{
        if (el.hasAttribute && el.hasAttribute('data-print')) {{ window.print(); return; }}
        el = el.parentNode;
      }}
    }});
  }})();
</script>
<script src="js/translate.js" defer></script>

</body>
</html>
"""


if __name__ == "__main__":
    main()
