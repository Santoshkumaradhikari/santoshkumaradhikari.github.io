#!/usr/bin/env python3
"""Build investors-canon/glossary.html from investors-canon/data/glossary-terms.json.

To add or change a term, edit the JSON file and run:
    python3 tools/build-glossary.py
Everything outside the <article> (header, footer, scripts) is kept from the
current glossary.html; the head's description and structured data are refreshed.
"""
import html, json, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "investors-canon"
PAGE = ROOT / "glossary.html"
DATA = ROOT / "data" / "glossary-terms.json"
BASE = "https://santoshkumaradhikari.com.np/investors-canon/"

CATS = [  # key, label, short label
    ("market", "Market & trading", "Market"),
    ("products", "Shares, IPOs & funds", "Shares & funds"),
    ("macro", "NRB & the money cycle", "NRB & economy"),
    ("banks", "Banks & microfinance", "Banks"),
    ("hydro", "Hydropower", "Hydropower"),
    ("insurance", "Insurance", "Insurance"),
    ("accounts", "Accounts, audit & tax", "Accounts & tax"),
    ("valuation", "Ratios & valuation", "Valuation"),
    ("canon", "Canon Score & method", "Canon Score"),
    ("governance", "Governance & law", "Governance"),
    ("portfolio", "Portfolio & behaviour", "Portfolio"),
]
CAT = {k: (l, s) for k, l, s in CATS}

START = [
    ("New to NEPSE?", ["nepse", "demat-account", "meroshare", "tms", "t-2", "asba", "ipo", "circuit-limit"]),
    ("Scoring your first company", ["canon-score", "business-quality", "share-attractiveness", "bands", "hard-rule-cap-at-54", "evidence-grade", "earned-discount"]),
    ("Reading a bank", ["car", "npl", "nim", "casa", "cd-ratio", "provision-coverage", "distributable-profit"]),
    ("Studying hydropower", ["ppa", "cod", "run-of-river", "royalty", "dscr", "single-buyer-ppa", "generation-licence"]),
    ("Studying an insurer", ["solvency-ratio", "combined-ratio", "embedded-value", "persistency", "reinsurance"]),
    ("Is the price right?", ["p-e", "p-b", "roe", "cost-of-equity", "dcf", "margin-of-safety"]),
]

e = lambda s: html.escape(s, quote=True)


def chapter_titles():
    out = {}
    for p in (ROOT / "chapters").glob("*.html"):
        m = re.search(r"<h1[^>]*>(.*?)</h1>", p.read_text(encoding="utf-8"), re.S)
        out[p.stem] = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else p.stem
    return out


def ch_label(slug):
    parts = slug[3:].split("-")
    if parts[0] == "0":
        return "0." + parts[1]
    return parts[0].lstrip("0").upper() or "0"


def sort_key(t):
    return re.sub(r"[^a-z0-9]", "", t["term"].lower())


def main():
    terms = json.loads(DATA.read_text(encoding="utf-8"))
    titles = chapter_titles()
    ids = {t["id"]: t for t in terms}
    errors = []
    for t in terms:
        if t["cat"] not in CAT:
            errors.append(f"{t['term']}: unknown category {t['cat']}")
        for c in t["chapters"]:
            if c not in titles:
                errors.append(f"{t['term']}: unknown chapter {c}")
        for a in t["see_also"]:
            if a not in ids:
                errors.append(f"{t['term']}: see-also {a} not found")
    for _, lst in START:
        for i in lst:
            if i not in ids:
                errors.append(f"start-here term {i} not found")
    if len(ids) != len(terms):
        errors.append("duplicate ids")
    if errors:
        sys.exit("\n".join(errors))

    terms.sort(key=sort_key)
    n = len(terms)
    counts = {k: sum(1 for t in terms if t["cat"] == k) for k, _, _ in CATS}

    # ---- cards grouped by letter
    letters = {}
    for t in terms:
        letters.setdefault(sort_key(t)[0].upper(), []).append(t)

    def card(t):
        lab, short = CAT[t["cat"]]
        h = [f'<article class="gl-term c-{t["cat"]}" id="{t["id"]}" data-cat="{t["cat"]}" '
             f'data-term="{e(t["term"].lower())}" data-full="{e(t["full"].lower())}" '
             f'data-np="{e(t["nepali"])}">']
        h.append('  <div class="gl-term-top">')
        h.append(f'    <h3><a class="gl-name" href="#{t["id"]}" data-hl>{e(t["term"])}</a></h3>')
        h.append(f'    <span class="gl-cat">{e(short)}</span>')
        h.append('  </div>')
        if t["full"]:
            h.append(f'  <p class="gl-full" data-hl>{e(t["full"])}</p>')
        if t["nepali"]:
            h.append(f'  <p class="gl-np"><span class="gl-np-label">नेपालीमा</span> <span lang="ne" data-hl>{e(t["nepali"])}</span></p>')
        h.append(f'  <p class="gl-def" data-hl>{e(t["definition"])}</p>')
        if t["example"]:
            h.append(f'  <p class="gl-eg"><span class="gl-eg-label">In everyday terms</span> <span data-hl>{e(t["example"])}</span></p>')
        links = " ".join(
            f'<a href="chapters/{c}.html">Ch {ch_label(c)}<span class="gl-ch-title"> · {e(titles[c])}</span></a>'
            for c in t["chapters"])
        h.append(f'  <p class="gl-links"><span class="gl-links-label">Read more</span> {links}</p>')
        if t["see_also"]:
            also = " ".join(f'<a class="c-{ids[a]["cat"]}" href="#{a}">{e(ids[a]["term"])}</a>' for a in t["see_also"])
            h.append(f'  <p class="gl-also"><span class="gl-also-label">See also</span> {also}</p>')
        h.append("</article>")
        return "\n".join(h)

    jump = "\n".join(f'      <a href="#letter-{L.lower()}" data-letter="{L}">{L}</a>' for L in sorted(letters))
    chips = "\n".join(
        f'      <button type="button" class="gl-chip c-{k}" data-cat="{k}" aria-pressed="false">{e(l)} <span class="gl-chip-n">{counts[k]}</span></button>'
        for k, l, _ in CATS)
    start = "\n".join(
        f'    <div class="gl-path"><h3>{e(title)}</h3><p>' +
        " ".join(f'<a class="c-{ids[i]["cat"]}" href="#{i}">{e(ids[i]["term"])}</a>' for i in lst) +
        "</p></div>" for title, lst in START)
    sections = "\n\n".join(
        f'  <section class="gl-section" id="letter-{L.lower()}" data-letter="{L}">\n'
        f'    <h2 class="gl-letter"><span>{L}</span></h2>\n'
        f'    <div class="gl-grid">\n' + "\n".join(card(t) for t in letters[L]) + "\n    </div>\n  </section>"
        for L in sorted(letters))

    article = f'''<article class="chapter glossary-page">
  <header class="gl-hero">
    <div class="chapter-kicker">Nepal Edition · Reference</div>
    <h1>Glossary of Terms</h1>
    <p class="gl-lead">Every important word in <em>The Investor's Canon</em>, explained in plain English: NEPSE trading, NRB and the money cycle, banks, hydropower, insurance, accounts and tax, valuation, and the Canon Score itself. Most terms carry their Nepali name, an everyday example, and a link to the chapter that explains them in full.</p>
    <ul class="gl-stats" aria-label="About this glossary">
      <li><strong>{n}</strong> terms</li>
      <li><strong>{len(CATS)}</strong> topics</li>
      <li><strong>{sum(1 for t in terms if t["nepali"])}</strong> with Nepali names</li>
    </ul>
    <aside class="gl-today" id="gl-today" hidden aria-label="Term of the day"></aside>
  </header>

  <div class="gl-search" role="search" hidden>
    <div class="gl-search-box">
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      <label class="visually-hidden" for="gl-q">Search the glossary</label>
      <input id="gl-q" type="search" autocomplete="off" spellcheck="false" placeholder="Search {n} terms: try NPL, dividend, लाभांश, hydropower…">
      <button type="button" class="gl-clear" hidden aria-label="Clear search">Clear</button>
    </div>
    <p class="gl-count" id="gl-count" aria-live="polite">{n} terms</p>
  </div>

  <div class="gl-filters" hidden>
    <div class="gl-chips" role="group" aria-label="Show one topic">
      <button type="button" class="gl-chip gl-chip-all" data-cat="" aria-pressed="true">All topics <span class="gl-chip-n">{n}</span></button>
{chips}
    </div>
    <nav class="gl-jump" aria-label="Jump to letter">
{jump}
    </nav>
  </div>

  <section class="gl-start" aria-labelledby="gl-start-h">
    <h2 id="gl-start-h">Start here</h2>
    <div class="gl-paths">
{start}
    </div>
  </section>

  <div class="gl-results" id="gl-results" hidden></div>
  <div class="gl-empty" id="gl-empty" hidden>
    <p><strong>No term matches that search.</strong> Try a shorter word, an abbreviation (NPL, CAR), or the Nepali word. The book may still cover it: <button type="button" class="gl-book-search">search all chapters</button>.</p>
  </div>

{sections}

  <p class="gl-note">Facts and figures in these definitions are dated in the chapters they link to; rules and rates change, so check the latest NRB, SEBON, NEPSE and NIA notices before you act. Rules marked as Canon rules are this book's own method, not regulation.</p>

  <div class="chapter-nav">
    <a href="study-guide.html">← How to Read This Book</a>
    <a href="index.html">Back to Contents →</a>
  </div>
</article>'''

    page = PAGE.read_text(encoding="utf-8")
    a = page.index('<article class="chapter')
    b = page.index("</article>", a) + len("</article>")
    page = page[:a] + article + page[b:]

    desc = (f"A searchable, plain-English glossary of {n} NEPSE, NRB, banking, hydropower, insurance, "
            "accounting, valuation and Canon Score terms, with Nepali names, everyday examples and links to the chapter that explains each one.")
    page = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + e(desc) + m.group(2), page)
    page = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + e(desc) + m.group(2), page)
    page = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', lambda m: m.group(1) + e(desc) + m.group(2), page)
    ld = {"@context": "https://schema.org", "@type": "DefinedTermSet",
          "name": "Glossary — The Investor's Canon", "description": desc, "url": BASE + "glossary.html",
          "inLanguage": "en", "dateModified": date.today().isoformat(),
          "author": {"@type": "Person", "name": "Santosh Kumar Adhikari", "url": "https://santoshkumaradhikari.com.np/"},
          "publisher": {"@type": "Person", "name": "Santosh Kumar Adhikari"},
          "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["term"] + (f" ({t['full']})" if t["full"] else ""),
                              "description": t["definition"], "url": BASE + "glossary.html#" + t["id"]} for t in terms]}
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  lambda m: f'<script type="application/ld+json">{ld_json}</script>', page, count=1, flags=re.S)
    if "css/glossary.css" not in page:
        # after style.css, so the glossary styles can override it
        page = re.sub(r'(<link rel="stylesheet" href="css/style\.css[^>]*>)', r'\1\n<link rel="stylesheet" href="css/glossary.css?v=1">', page, count=1)
    if "js/glossary.js" not in page:
        page = page.replace('<script src="js/audio-reader.js" defer></script>',
                            '<script src="js/glossary.js?v=1" defer></script>\n<script src="js/audio-reader.js" defer></script>', 1)
    PAGE.write_text(page, encoding="utf-8")
    print(f"glossary.html: {n} terms, {len(letters)} letters")


if __name__ == "__main__":
    main()
