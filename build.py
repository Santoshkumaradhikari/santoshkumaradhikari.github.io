#!/usr/bin/env python3
"""
The Investor's Canon — build script
====================================
One command that keeps the whole book consistent after chapter-by-chapter edits:

    python3 build.py

What it does (all idempotent — safe to run any time):
  1. Regenerates each chapter's prev/next `chapter-nav` from chapters.yml order
  2. Bumps a chapter's JSON-LD `dateModified` — but ONLY when its body text changed
  3. Regenerates the index TOC (all volumes/parts/chapter rows) from chapters.yml
  4. Updates the index hero counts and the Book JSON-LD `hasPart` list
  5. Generates feed.xml   — Atom feed of recently-revised chapters (readers subscribe)
  6. Generates sitemap.xml — with fresh <lastmod> per page (search engines)
  7. Ensures every page advertises the feed via <link rel="alternate">

Other modes:
    python3 build.py --extract          regenerate chapters.yml from current index.html
    python3 build.py --recompute-times  recompute "~N min" reading times from word counts
    python3 build.py --date 2026-09-14  use a specific date for dateModified bumps
    python3 build.py --docs-dir site    use a different docs directory (default: docs)

Standard library only — nothing to install.
"""

import argparse
import hashlib
import html
import json
import re
import sys
import xml.sax.saxutils as sx
from datetime import date
from pathlib import Path


def fail(msg):
    print(f"  ✗ {msg}")
    sys.exit(1)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def yaml_quote(s) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ------------------------------------------------- chapters.yml mini-parser
# Parses exactly the strict, regular shape that emit_chapters_yaml() writes.
# Indentation is fixed: site keys at 2, "- id" at 2, label/parts at 4,
# "- roman" at 6, part title/chapters at 8, "- slug" at 10, chapter keys at 12.

def parse_chapters_yaml(text):
    data = {"site": {}, "volumes": []}
    site, volumes = data["site"], data["volumes"]
    vol = part = ch = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0:
            k, _, v = line.partition(":")
            if k.strip() == "site":
                site = data.setdefault("site", {})
            continue
        if indent == 2 and line.startswith("- id:"):
            vol = {"id": _scalar(line[5:]), "label": "", "parts": []}
            volumes.append(vol)
            continue
        if indent == 2:
            k, _, v = line.partition(":")
            site[k.strip()] = _scalar(v.strip())
            continue
        if indent == 4 and line.startswith("label:"):
            vol["label"] = _scalar(line[6:])
            continue
        if indent == 4 and line == "parts:":
            continue
        if indent == 6 and line.startswith("- roman:"):
            part = {"roman": _scalar(line[8:]), "title": "", "chapters": []}
            vol["parts"].append(part)
            continue
        if indent == 8 and line.startswith("title:"):
            part["title"] = _scalar(line[6:])
            continue
        if indent == 8 and line == "chapters:":
            continue
        if indent == 10 and line.startswith("- slug:"):
            ch = {"slug": _scalar(line[7:])}
            part["chapters"].append(ch)
            continue
        if indent == 12:
            k, _, v = line.partition(":")
            ch[k.strip()] = _scalar(v.strip())
            continue
        fail(f"chapters.yml: unexpected line: {raw!r}")
    n = sum(len(p["chapters"]) for v in volumes for p in v["parts"])
    if n == 0:
        fail("chapters.yml parsed but contains no chapters")
    return data


def _scalar(tok):
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    return tok


# ---------------------------------------------------------- chapters.yml emit

def emit_chapters_yaml(data):
    out = ["site:"]
    for k, v in data["site"].items():
        out.append(f"  {k}: {yaml_quote(v)}")
    out.append("volumes:")
    for vol in data["volumes"]:
        out.append(f"  - id: {yaml_quote(vol['id'])}")
        out.append(f"    label: {yaml_quote(vol['label'])}")
        out.append("    parts:")
        for part in vol["parts"]:
            out.append(f"      - roman: {yaml_quote(part['roman'])}")
            out.append(f"        title: {yaml_quote(part['title'])}")
            out.append("        chapters:")
            for ch in part["chapters"]:
                out.append(f"          - slug: {yaml_quote(ch['slug'])}")
                out.append(f"            num: {yaml_quote(ch['num'])}")
                out.append(f"            title: {yaml_quote(ch['title'])}")
                out.append(f"            minutes: {ch['minutes']}")
                out.append(f"            date_published: {yaml_quote(ch['date_published'])}")
    return "\n".join(out) + "\n"


def iter_chapters(data):
    for vol in data["volumes"]:
        for part in vol["parts"]:
            for ch in part["chapters"]:
                yield vol, part, ch


def flatten(data):
    return [ch for _, _, ch in iter_chapters(data)]


# ------------------------------------------------------------------ JSON-LD

LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def get_ld(page):
    m = LD_RE.search(page)
    return json.loads(m.group(2)) if m else None


def set_ld(page, obj):
    body = json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))
    return LD_RE.sub(lambda m: m.group(1) + body + m.group(3), page, count=1)


# ------------------------------------------------------------- page helpers

ARTICLE_RE = re.compile(r'(<article\b.*?</article>)', re.S)
NAV_RE = re.compile(r'<div class="chapter-nav">.*?</div>', re.S)
TOC_RE = re.compile(r'<section class="roadmap">.*?</section>', re.S)


def body_hash(page):
    m = ARTICLE_RE.search(page)
    if not m:
        return None
    body = NAV_RE.sub("", m.group(1))
    return hashlib.md5(re.sub(r"\s+", " ", body).encode("utf-8")).hexdigest()


def word_count(page):
    m = ARTICLE_RE.search(page)
    if not m:
        return 0
    body = re.sub(r"<[^>]+>", " ", NAV_RE.sub("", m.group(1)))
    return len(html.unescape(body).split())


def esc(s):
    return html.escape(s, quote=False)


def regen_nav(page, prev_ch, next_ch):
    if prev_ch and next_ch:
        inner = (f'\n    <a href="{prev_ch["slug"]}">← {esc(prev_ch["title"])}</a>\n'
                 f'    <a href="{next_ch["slug"]}">{esc(next_ch["title"])} →</a>\n  ')
    elif next_ch:                                   # first chapter of the book
        inner = (f'\n    <a href="../index.html">← Back to Contents</a>\n'
                 f'    <a href="{next_ch["slug"]}">{esc(next_ch["title"])} →</a>\n  ')
    elif prev_ch:                                   # last chapter of the book
        inner = (f'\n    <a href="{prev_ch["slug"]}">← {esc(prev_ch["title"])}</a>\n'
                 f'    <a href="../index.html">Back to Contents →</a>\n  ')
    else:
        inner = '\n    <a href="../index.html">← Back to Contents</a>\n  '
    return NAV_RE.sub('<div class="chapter-nav">' + inner + '</div>', page, count=1)


def ensure_feed_link(page, feed_url):
    if "application/atom+xml" in page:
        return page
    link = (f'<link rel="alternate" type="application/atom+xml" '
            f'title="Canon Updates" href="{feed_url}">\n')
    return page.replace("</head>", link + "</head>", 1)


def bump_date(page, new_date):
    ld = get_ld(page)
    if not ld or ld.get("dateModified") == new_date:
        return page, False
    ld["dateModified"] = new_date
    return set_ld(page, ld), True


# --------------------------------------------------- extraction (bootstrap)

VOL_RE = re.compile(
    r'<div class="volume-block" id="([^"]+)">\s*'
    r'<h2 class="volume-title">(.*?)</h2>'
    r'(.*?)(?=<div class="volume-block" id=|</section>)', re.S)
PART_RE = re.compile(
    r'<div class="toc-part-head"><span class="part-roman">(.*?)</span>(.*?)</div>'
    r'(.*?)\n  </div>', re.S)
ROW_RE = re.compile(
    r'<a class="chapter-row" href="chapters/([^"]+)">'
    r'<span class="ch-num">(.*?)</span>'
    r'<span class="ch-title">(.*?)</span>'
    r'<span class="ch-status[^"]*">~(\d+) min', re.S)


def extract_from_index(docs: Path):
    """Build the chapters.yml data structure from the current index.html."""
    page = read(docs / "index.html")
    vols = []
    for vm in VOL_RE.finditer(page):
        parts = []
        for pm in PART_RE.finditer(vm.group(3)):
            chapters = []
            for rm in ROW_RE.finditer(pm.group(3)):
                slug = rm.group(1)
                chp = docs / "chapters" / slug
                pub = ""
                if chp.exists():
                    ld = get_ld(read(chp))
                    pub = (ld or {}).get("datePublished", "")
                chapters.append({
                    "slug": slug,
                    "num": html.unescape(rm.group(2)),
                    "title": html.unescape(rm.group(3)),
                    "minutes": int(rm.group(4)),
                    "date_published": pub,
                })
            parts.append({
                "roman": html.unescape(pm.group(1)),
                "title": html.unescape(pm.group(2)),
                "chapters": chapters,
            })
        vols.append({
            "id": vm.group(1),
            "label": html.unescape(vm.group(2)),
            "parts": parts,
        })
    return {
        "site": {
            "base_url": "https://santoshkumaradhikari.com.np",
            "base_path": "/investors-canon",
            "title": "The Investor's Canon — Nepal Edition",
            "author": "Santosh Kumar Adhikari",
        },
        "volumes": vols,
    }


# ----------------------------------------------------- index TOC rebuild

def build_toc(data):
    volumes_html = []
    for vol in data["volumes"]:
        parts_html = []
        for part in vol["parts"]:
            rows = "\n".join(
                f'    <a class="chapter-row" href="chapters/{c["slug"]}">'
                f'<span class="ch-num">{esc(c["num"])}</span>'
                f'<span class="ch-title">{esc(c["title"])}</span>'
                f'<span class="ch-status ready">~{c["minutes"]} min · Read →</span></a>'
                for c in part["chapters"])
            parts_html.append(
                '  <div class="toc-part">\n'
                f'    <div class="toc-part-head"><span class="part-roman">{esc(part["roman"])}</span>'
                f'{esc(part["title"])}</div>\n'
                f'{rows}\n'
                '  </div>')
        volumes_html.append(
            f'<div class="volume-block" id="{vol["id"]}">\n'
            f'  <h2 class="volume-title">{esc(vol["label"])}</h2>\n'
            + "\n".join(parts_html) + "\n</div>")
    return '<section class="roadmap">\n' + "\n".join(volumes_html) + "\n</section>"


def update_index_counts(page, data):
    chapters = flatten(data)
    n_all = len(chapters)
    n_main = sum(1 for c in chapters if not c["num"].startswith("0."))
    n_parts = sum(1 for v in data["volumes"] for p in v["parts"]
                  if p["roman"].strip() != "Part 0")
    n_vols = len(data["volumes"])
    new_hero = (f"{n_vols} volumes, {n_parts} parts, {n_main} chapters, "
                f"plus the three Part 0 framework chapters — {n_all} chapters in all.")
    page = re.sub(r"\d+ volumes, \d+ parts, \d+ chapters,\s+plus the three Part 0 "
                  r"framework chapters — \d+ chapters in all\.", new_hero, page, count=1)
    page = re.sub(r"all \d+ chapters \(Part 0 \+ chapters 1–\d+\) are published",
                  f"all {n_all} chapters (Part 0 + chapters 1–{n_main}) are published",
                  page, count=1)
    return page


# ----------------------------------------------------------------- outputs

def write_feed(docs, data, cache):
    site = data["site"]
    base = site["base_url"] + site["base_path"]
    entries = []
    for c in flatten(data):
        mod = cache["chapters"].get(c["slug"], {}).get("content_date") \
              or c.get("date_published") or "1970-01-01"
        entries.append((mod, c))
    entries.sort(key=lambda x: x[0], reverse=True)
    top = entries[:40]
    feed_updated = max(e[0] for e in top)
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<feed xmlns="http://www.w3.org/2005/Atom">',
         f'  <title>{sx.escape(site["title"])}</title>',
         f'  <subtitle>Revisions and updates to {sx.escape(site["title"])}</subtitle>',
         f'  <link rel="self" href="{sx.escape(base + "/feed.xml")}"/>',
         f'  <link href="{sx.escape(base + "/")}"/>',
         f'  <id>{sx.escape(base + "/")}</id>',
         f'  <updated>{feed_updated}T00:00:00Z</updated>',
         '  <generator>Canon build.py</generator>']
    for mod, c in top:
        url = f"{base}/chapters/{c['slug']}"
        L += ['  <entry>',
              f'    <id>{sx.escape(url)}</id>',
              f'    <title>{sx.escape(c["title"])}</title>',
              f'    <link rel="alternate" href="{sx.escape(url)}"/>',
              f'    <updated>{mod}T00:00:00Z</updated>',
              f'    <published>{c.get("date_published") or mod}T00:00:00Z</published>',
              f'    <author><name>{sx.escape(site["author"])}</name></author>',
              '  </entry>']
    L.append('</feed>')
    write(docs / "feed.xml", "\n".join(L) + "\n")


def write_sitemap(docs, data, cache):
    site = data["site"]
    base = site["base_url"] + site["base_path"]

    def url(loc, lastmod, priority):
        return ("  <url>\n"
                f"    <loc>{sx.escape(loc)}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n"
                f"    <priority>{priority}</priority>\n"
                "  </url>\n")

    today = date.today().isoformat()
    body = url(base + "/", cache.get("index_date", today), "0.9")
    # every other top-level page of the book (framework, glossary, study-guide, book …)
    pages = cache.setdefault("pages", {})
    for p in sorted(docs.glob("*.html")):
        if p.name == "index.html":
            continue
        ld = get_ld(read(p))
        mod = (ld or {}).get("dateModified")
        if not mod:
            # no JSON-LD date — adopt once, then keep stable (no fake churn)
            mod = pages.setdefault(p.name, today)
        body += url(f"{base}/{p.name}", mod, "0.7")
    for c in flatten(data):
        mod = cache["chapters"].get(c["slug"], {}).get("content_date") \
              or c.get("date_published") or today
        body += url(f"{base}/chapters/{c['slug']}", mod, "0.6")
    write(docs / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + body + '</urlset>\n')


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Build The Investor's Canon")
    ap.add_argument("--docs-dir", default=None,
                    help="book folder (default: auto-detect docs/ or investors-canon/)")
    ap.add_argument("--extract", action="store_true",
                    help="regenerate chapters.yml from index.html, then exit")
    ap.add_argument("--recompute-times", action="store_true",
                    help="recompute reading minutes from word counts")
    ap.add_argument("--date", default=None,
                    help="override the dateModified bump date (YYYY-MM-DD)")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent
    # auto-detect the book folder unless --docs-dir is given
    if args.docs_dir:
        docs = root / args.docs_dir
    else:
        docs = next((root / d for d in ("docs", "investors-canon")
                     if (root / d).is_dir()), None)
        if docs is None:
            fail('no book folder found (expected "docs/" or "investors-canon/")')
    yml_path = root / "chapters.yml"
    if not docs.exists():
        fail(f"docs directory not found: {docs}")

    if args.extract or not yml_path.exists():
        print("◆ Extracting structure from index.html → chapters.yml")
        data = extract_from_index(docs)
        n = len(flatten(data))
        if n == 0:
            fail("no chapter rows found in index.html — is this the Canon index?")
        write(yml_path, emit_chapters_yaml(data))
        print(f"  ✓ wrote chapters.yml ({n} chapters, {len(data['volumes'])} volumes)")
        if args.extract:
            return

    data = parse_chapters_yaml(read(yml_path))
    chapters = flatten(data)
    n_parts_all = sum(len(v["parts"]) for v in data["volumes"])
    print(f"◆ chapters.yml: {len(data['volumes'])} volumes, {n_parts_all} parts, "
          f"{len(chapters)} chapters")

    if args.recompute_times:
        for _, _, c in iter_chapters(data):
            p = docs / "chapters" / c["slug"]
            if p.exists():
                c["minutes"] = max(1, round(word_count(read(p)) / 220))
        write(yml_path, emit_chapters_yaml(data))
        print("  ✓ reading times recomputed → chapters.yml")

    today = args.date or date.today().isoformat()
    cache_path = root / ".canon-cache.json"          # kept at repo root & committed,
    cache = json.loads(read(cache_path)) if cache_path.exists() else {"chapters": {}, "pages": {}}
    cache.setdefault("pages", {})
    first_run = not cache["chapters"]

    base = data["site"]["base_url"] + data["site"]["base_path"]
    feed_url = base + "/feed.xml"

    bump_count = nav_count = link_count = 0
    for i, (_, _, c) in enumerate(iter_chapters(data)):
        p = docs / "chapters" / c["slug"]
        if not p.exists():
            print(f"  ⚠ missing chapter file: chapters/{c['slug']}")
            continue
        page = read(p)
        orig = page

        # 1. bump dateModified only when the body text actually changed
        h = body_hash(page)
        rec = cache["chapters"].setdefault(c["slug"], {})
        if h and rec.get("hash") != h:
            if first_run:
                ld = get_ld(page)
                rec["content_date"] = (ld or {}).get("dateModified", today)
            else:
                page, changed = bump_date(page, today)
                rec["content_date"] = today
                bump_count += changed
            rec["hash"] = h

        # 2. regenerate prev/next nav from canonical order
        page = regen_nav(page,
                         chapters[i - 1] if i > 0 else None,
                         chapters[i + 1] if i + 1 < len(chapters) else None)

        # 3. advertise the feed
        page = ensure_feed_link(page, feed_url)

        if page != orig:
            nav_count += 1
            write(p, page)

    # ---- index
    idx = docs / "index.html"
    if idx.exists():
        page = read(idx)
        orig = page
        page = TOC_RE.sub(lambda _: build_toc(data), page, count=1)
        page = update_index_counts(page, data)
        ld = get_ld(page)
        if ld and "hasPart" in ld:
            ld["hasPart"] = [
                {"@type": "Chapter", "position": i + 1, "name": c["title"],
                 "url": f"{base}/chapters/{c['slug']}"}
                for i, c in enumerate(chapters)]
            ld["dateModified"] = today
            page = set_ld(page, ld)
        page = ensure_feed_link(page, feed_url)
        if page != orig:
            write(idx, page)
            print("  ✓ index.html TOC / counts / Book schema refreshed")
        cache["index_date"] = today

    # ---- other top-level pages: just advertise the feed
    for p in sorted(docs.glob("*.html")):
        if p.name == "index.html":
            continue
        page = ensure_feed_link(read(p), feed_url)
        if page != read(p):
            write(p, page)

    write_feed(docs, data, cache)
    print("  ✓ feed.xml generated")
    write_sitemap(docs, data, cache)
    print("  ✓ sitemap.xml generated")

    write(cache_path, json.dumps(cache, indent=1))
    extra = " (first run: adopted existing dates)" if first_run else ""
    print(f"◆ done — chapters touched: {nav_count}, dates bumped: {bump_count}{extra}")


if __name__ == "__main__":
    main()
