#!/usr/bin/env python3
"""
Daily NEPSE market data refresh for The Investor's Canon.

Fetches the latest closing data from ShareSansar's market page, sanity-checks
it, and regenerates investors-canon/data/live-market-data.html.

Safety rules:
  * If the fetch fails, or any REQUIRED section cannot be parsed, or a value
    fails its plausibility check, the script exits non-zero WITHOUT touching
    the data page. The site keeps the last good snapshot.
  * Optional sections (forex, gold, top gainers/losers) are simply omitted
    from the page if their layout changes.

Source: https://www.sharesansar.com/market (NEPSE data, server-rendered tables)
"""
import html as H
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SOURCE = "https://www.sharesansar.com/market"
OUT = "investors-canon/data/live-market-data.html"
NPT = timezone(timedelta(hours=5, minutes=45))


def log(msg):
    print(f"[data-refresh] {msg}", flush=True)


def fetch(url, timeout=90):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; CanonDataRefresh/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(frag):
    return H.unescape(re.sub(r"<[^>]+>", " ", frag)).strip()


def to_num(s):
    s = s.strip()
    if not s:
        raise ValueError("empty number")
    first = s.split()[0]  # e.g. "4,398,915.85 Millions" -> "4,398,915.85"
    return float(first.replace(",", "").replace("%", "").strip())


def all_tables(page):
    out = []
    for m in re.finditer(r"<table[^>]*>", page, re.I):
        e = page.find("</table>", m.start())
        if e != -1:
            out.append(page[m.start(): e + 8])
    return out


def table_rows(tbl):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S | re.I):
        cells = [strip_tags(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        if cells:
            rows.append(cells)
    return rows


def find_table(page, *needles):
    for t in all_tables(page):
        low = t.lower()
        if all(n.lower() in low for n in needles):
            return t
    return None


def table_after_heading(page, heading):
    i = page.lower().find(heading.lower())
    if i == -1:
        return None
    t = page.find("<table", i)
    if t == -1:
        return None
    e = page.find("</table>", t)
    return page[t: e + 8] if e != -1 else None


def find_row(rows, name):
    for r in rows:
        if r and r[0].lower() == name.lower():
            return r
    for r in rows:
        if r and r[0].lower().startswith(name.lower()):
            return r
    return None


def must_num(s, what):
    try:
        return to_num(s)
    except Exception:
        sys.exit(f"FATAL: cannot parse {what} from {s!r}")


def fmt(x, digits=2):
    return f"{x:,.{digits}f}"


def pct_span(pt, pct):
    cls = "up" if pt > 0 else ("down" if pt < 0 else "flat")
    sign = "+" if pt > 0 else ""
    return f'<span class="{cls}">{sign}{fmt(pt)} ({sign}{pct:g}%)</span>'


def pt_span(pt):
    cls = "up" if pt > 0 else ("down" if pt < 0 else "flat")
    return f'<span class="{cls}">{pt:+.2f}</span>'


def main():
    log("fetching " + SOURCE)
    try:
        page = fetch(SOURCE)
    except Exception as ex:
        sys.exit(f"FATAL: could not fetch source page: {ex}")
    log(f"fetched {len(page)} bytes")

    # ---- data date -------------------------------------------------------
    m = re.search(r"As\s+of[^0-9]{0,120}?(\d{4}-\d{2}-\d{2})", page, re.S)
    if not m:
        sys.exit("FATAL: could not find 'As of <date>' on source page - layout may have changed")
    data_date = m.group(1)
    try:
        d = datetime.strptime(data_date, "%Y-%m-%d")
    except ValueError:
        sys.exit(f"FATAL: bad data date '{data_date}'")
    now = datetime.now(NPT)
    age = now - d.replace(tzinfo=NPT)
    if not (timedelta(days=-1) <= age <= timedelta(days=14)):
        sys.exit(f"FATAL: data date {data_date} is {age.days} days old/out of range")
    log(f"data as of {data_date}")

    # ---- required: main indices ------------------------------------------
    idx_tbl = find_table(page, "NEPSE Index", "Close")
    if not idx_tbl:
        sys.exit("FATAL: indices table (NEPSE Index + Close) not found")
    idx_rows = table_rows(idx_tbl)
    nepse_row = find_row(idx_rows, "NEPSE Index")
    sens_row = find_row(idx_rows, "Sensitive Index")
    if not nepse_row or len(nepse_row) < 8:
        sys.exit(f"FATAL: NEPSE index row not parseable: {nepse_row}")
    nepse_close = must_num(nepse_row[-4], "NEPSE index close")
    nepse_pt = must_num(nepse_row[-3], "NEPSE index point change")
    nepse_pct = must_num(nepse_row[-2], "NEPSE index % change")
    nepse_to = must_num(nepse_row[-1], "NEPSE index turnover")
    if not (200 < nepse_close < 12000):
        sys.exit(f"FATAL: NEPSE close out of plausible range: {nepse_close}")
    log(f"NEPSE index {fmt(nepse_close)} ({nepse_pt:+.2f}, {nepse_pct:+.2f}%)")
    sens = None
    if sens_row and len(sens_row) >= 8:
        try:
            sens = (to_num(sens_row[-4]), to_num(sens_row[-3]), to_num(sens_row[-2]))
        except Exception:
            sens = None  # optional line; skip if malformed

    # ---- required: market summary ----------------------------------------
    sum_tbl = find_table(page, "Total Turnovers")
    if not sum_tbl:
        sys.exit("FATAL: market summary table (Total Turnovers) not found")
    smap = {}
    for r in table_rows(sum_tbl):
        if len(r) >= 2:
            smap[r[0].lower()] = r[1]
    def sm(key):
        for k, v in smap.items():
            if key.lower() in k:
                return v
        return None
    total_to = sm("Total Turnovers")
    mcap_m = sm("Total Market Cap")
    if not total_to or not mcap_m:
        sys.exit(f"FATAL: market summary incomplete: {list(smap)}")
    mcap = must_num(mcap_m, "total market cap")  # NPR millions
    if not (1_000_000 < mcap < 200_000_000):
        sys.exit(f"FATAL: total market cap out of plausible range (NPR millions): {mcap}")
    log(f"total turnover {total_to}; market cap {fmt(mcap, 0)} NPR millions")

    # ---- required: sub-indices -------------------------------------------
    sub_tbl = find_table(page, "Banking SubIndex", "Turnover")
    if not sub_tbl:
        sys.exit("FATAL: sub-indices table not found")
    subs = []
    for r in table_rows(sub_tbl):
        if len(r) >= 8 and r[0].lower() != "sub index":
            try:
                subs.append((r[0], to_num(r[-4]), to_num(r[-3]), to_num(r[-2]), to_num(r[-1])))
            except ValueError:
                continue
    if len(subs) < 10:
        sys.exit(f"FATAL: only {len(subs)} sub-indices parsed (expected 10+)")
    log(f"sub-indices parsed: {len(subs)}")

    # ---- optional: forex, gold, movers ------------------------------------
    usd = None
    fx_tbl = find_table(page, "USD", "Buy")
    if fx_tbl:
        row = find_row(table_rows(fx_tbl), "USD")
        if row and len(row) >= 3:
            try:
                usd = (to_num(row[1]), to_num(row[2]))
            except Exception:
                usd = None
    gold = None
    gm = re.search(r"Hallmark\s+Gold.{0,300}?Rs\.([\d,]+)/\s*tola", page, re.S)
    if gm:
        gc = re.search(r"Hallmark\s+Gold.{0,400}?\(\s*([-\d,]+)\s*\)", page, re.S)
        try:
            gold = (to_num(gm.group(1)), to_num(gc.group(1)) if gc else None)
        except Exception:
            gold = None

    def movers(heading):
        t = table_after_heading(page, heading)
        if not t:
            return []
        out = []
        for r in table_rows(t):
            if len(r) >= 4 and r[0].lower() != "symbol":
                try:
                    out.append((r[0], to_num(r[1]), to_num(r[2]), to_num(r[3])))
                except ValueError:
                    continue
            if len(out) == 5:
                break
        return out
    gainers = movers("Top Gainers")
    losers = movers("Top Losers")
    if gainers:
        log(f"top gainers: {[g[0] for g in gainers]}")
    if losers:
        log(f"top losers: {[l[0] for l in losers]}")

    # ---- render ------------------------------------------------------------
    esc = H.escape
    subs_html = "\n".join(
        f"<tr><td>{esc(n)}</td><td class='n'>{fmt(c)}</td><td class='n'>{pct_span(p, pc)}</td><td class='n'>{fmt(t, 0)}</td></tr>"
        for n, c, p, pc, t in subs
    )
    movers_html = lambda label, rows: (
        f"<h3>{label}</h3><table><tr><th>Symbol</th><th>Last (Rs.)</th><th>Change</th><th>%</th></tr>"
        + "".join(
            f"<tr><td>{esc(s)}</td><td class='n'>{fmt(l)}</td><td class='n'>{pt_span(p)}</td><td class='n'>{pc:+g}%</td></tr>"
            for s, l, p, pc in rows
        )
        + "</table>"
    ) if rows else ""

    sens_html = ""
    if sens:
        sens_html = f"<p>NEPSE Sensitive Index: <strong>{fmt(sens[0])}</strong> &nbsp; {pct_span(sens[1], sens[2])}</p>"

    sm_rows = []
    for label, key, digits in [
        ("Total turnover (Rs.)", "Total Turnovers", 2),
        ("Total shares traded", "Total Traded Shares", 0),
        ("Total transactions", "Total Transaction", 0),
        ("Total scrips traded", "Total Scrips Traded", 0),
    ]:
        v = sm(key)
        if v:
            try:
                sm_rows.append((label, fmt(to_num(v), digits), 0))
            except Exception:
                pass  # optional row; skip if malformed
    sm_rows.append(("Total market cap (Rs.)", f"{mcap / 1000:,.1f} thousand crore" if mcap < 100_000_000 else f"{mcap / 1_000_000:,.2f} lakh crore", 0))
    fm = sm("Floated Market Cap")
    if fm:
        try:
            sm_rows.append(("Floated market cap (Rs.)", fmt(to_num(fm), 2), 0))
        except Exception:
            pass
    sm_html = "".join(f"<tr><td>{esc(l)}</td><td class='n'>{esc(v)}</td></tr>" for l, v, _ in sm_rows)

    fx_html = ""
    if usd:
        fx_html = (
            "<h3>Reference rates</h3><table>"
            f"<tr><td>USD (buy / sell, Rs.)</td><td class='n'>{fmt(usd[0])} / {fmt(usd[1])}</td></tr>"
            + (f"<tr><td>Hallmark gold (Rs./tola)</td><td class='n'>{fmt(gold[0], 0)}"
               + (f" ({gold[1]:+,.0f})" if gold and gold[1] is not None else "")
               + "</td></tr>" if gold else "")
            + "</table>"
        )

    generated = now.strftime("%d %b %Y, %H:%M NPT")
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEPSE Market Data — Daily Snapshot | The Investor's Canon</title>
<meta name="description" content="Automatically refreshed daily snapshot of NEPSE indices, market summary, sub-indices and reference rates. Data as of {data_date}.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://santoshkumaradhikari.com.np/investors-canon/data/live-market-data.html">
<style>
body {{ font-family: Georgia, 'Times New Roman', serif; color:#1a1a1a; line-height:1.6; margin:0; background:#fbfaf7; }}
main {{ max-width: 52rem; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
a {{ color:#7a1f1f; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
h1 {{ font-size:1.9rem; margin:.3rem 0 .5rem; }} h2 {{ font-size:1.3rem; margin-top:2.2rem; border-bottom:1px solid #e3e0d8; padding-bottom:.35rem; }}
h3 {{ font-size:1.05rem; margin-top:1.6rem; }}
.kicker {{ font-family: system-ui, sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:#666; margin:0; }}
.banner {{ background:#fff; border:1px solid #e3e0d8; border-left:4px solid #7a1f1f; border-radius:6px; padding:.8rem 1.1rem; font-size:.92rem; font-family: system-ui, sans-serif; }}
.headline {{ background:#fff; border:1px solid #e3e0d8; border-radius:8px; padding:1.1rem 1.3rem; margin:1.2rem 0; }}
.headline .idx {{ font-size:2.4rem; font-weight:bold; }}
table {{ border-collapse:collapse; width:100%; margin:.9rem 0; font-family: system-ui, sans-serif; font-size:.92rem; }}
th, td {{ border:1px solid #e3e0d8; padding:.45rem .65rem; text-align:left; }}
th {{ background:#f4f2ec; }}
td.n, th.n {{ text-align:right; white-space:nowrap; }}
.up {{ color:#1a7f37; }} .down {{ color:#c0392b; }} .flat {{ color:#555; }}
footer {{ font-size:.85rem; color:#666; font-family: system-ui, sans-serif; border-top:1px solid #e3e0d8; margin-top:2.5rem; padding-top:1rem; }}
.cols {{ display:flex; gap:1.5rem; flex-wrap:wrap; }} .cols > div {{ flex:1 1 12rem; }}
@media print {{ .banner {{ border-left-color:#999; }} }}
</style>
</head>
<body>
<main>
  <p class="kicker">The Investor's Canon · Data Appendix</p>
  <h1>NEPSE Market Data — Daily Snapshot</h1>

  <div class="banner">
    This page is <strong>automatically refreshed after every trading day</strong> (Mon–Fri, 16:30 NPT) by a scheduled job.
    It is a machine-generated supplement to the Canon — the book's chapters remain manually verified against primary sources.
    Figures are as of <strong>{data_date}</strong> (last published trading session). Generated {generated}.
  </div>

  <div class="headline">
    <div class="kicker">NEPSE Index · Close</div>
    <div class="idx">{fmt(nepse_close)}</div>
    {pct_span(nepse_pt, nepse_pct)} &nbsp;·&nbsp; session turnover Rs. {nepse_to / 100_000_000:,.2f} arba
    {sens_html}
  </div>

  <h2>Market Summary</h2>
  <table><tr><th>Measure</th><th class="n">Value</th></tr>{sm_html}</table>

  <h2>Sector Sub-Indices</h2>
  <table>
    <tr><th>Sub-index</th><th class="n">Close</th><th class="n">Change</th><th class="n">Turnover (Rs.)</th></tr>
    {subs_html}
  </table>

  <div class="cols">
    <div>{fx_html}</div>
    <div>{movers_html("Top Gainers", gainers)}</div>
    <div>{movers_html("Top Losers", losers)}</div>
  </div>

  <p><a href="../index.html">← Back to The Investor's Canon</a></p>

  <footer>
    <p>Data: NEPSE, via <a href="https://www.sharesansar.com/market">ShareSansar market summary</a>
    (source: <a href="https://www.nepalstock.com/">nepalstock.com</a>). If a figure here disagrees with a primary
    source, trust the primary source. Automated refresh runs after each trading day; if the job fails, this page keeps
    its last good snapshot and the run is visible in the repository's Actions log.</p>
    <p>Educational material only. Nothing on this site is investment advice.</p>
    <p>© 2026 Santosh Kumar Adhikari. All rights reserved.</p>
  </footer>
</main>
</body>
</html>
"""

    import os
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_doc)
    log(f"wrote {OUT} ({len(html_doc)} bytes)")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as ex:  # e.g. a value that looks like a cell but is not a number
        sys.exit(f"FATAL: unexpected error: {type(ex).__name__}: {ex}")
