#!/usr/bin/env python3
"""Build investors-canon/canon-score-engine.html — the Canon Score Engine page.
The scoring itself lives in investors-canon/js/canon-engine.js (a port of
data/canon_score_reference_v1_6_0.py, checked by tools/test-canon-engine.js).
This script only writes the form and page shell:  python3 tools/build-engine.py
"""
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "investors-canon"
SRC = ROOT / "first-purchase.html"
OUT = ROOT / "canon-score-engine.html"
e = lambda s: html.escape(s, quote=True)

STATUS = '''<label class="ce-status">Evidence <select data-status="{k}">
  <option value="verified">Verified from the report</option>
  <option value="estimated">Estimated</option>
  <option value="unverified">Unverified</option>
  <option value="unavailable">Not available</option>
</select></label>'''


def num(k, label, unit="", hint="", show="", step="any", i=None):
    di = f' data-i="{i}"' if i is not None else ""
    sh = f' data-show="{show}"' if show else ""
    h = f'<span class="ce-hint">{e(hint)}</span>' if hint else ""
    u = f'<span class="ce-unit">{e(unit)}</span>' if unit else ""
    return f'<label class="ce-field"{sh}><span class="ce-label">{e(label)}</span>{h}<span class="ce-input">{u}<input type="number" step="{step}" inputmode="decimal" data-k="{k}"{di}></span></label>'


def chk(k, label, show="", checked=False):
    sh = f' data-show="{show}"' if show else ""
    c = " checked" if checked else ""
    return f'<label class="ce-check"{sh}><input type="checkbox" data-k="{k}"{c}> <span>{e(label)}</span></label>'


def sel(k, label, opts, show="", hint=""):
    sh = f' data-show="{show}"' if show else ""
    h = f'<span class="ce-hint">{e(hint)}</span>' if hint else ""
    o = "".join(f'<option value="{e(v)}">{e(t)}</option>' for v, t in opts)
    return f'<label class="ce-field ce-wide"{sh}><span class="ce-label">{e(label)}</span>{h}<select data-k="{k}">{o}</select></label>'


def row6(k, label, unit, hint, show=""):
    sh = f' data-show="{show}"' if show else ""
    cells = "".join(f'<input type="number" step="any" inputmode="decimal" data-k="{k}" data-i="{i}" aria-label="{e(label)} year {i+1}" placeholder="Y{i+1}">' for i in range(6))
    return f'<div class="ce-row6"{sh}><span class="ce-label">{e(label)} <span class="ce-unit-inline">{e(unit)}</span></span><span class="ce-hint">{e(hint)}</span><div class="ce-six">{cells}</div></div>'


def part(key, title, pts, body, show=""):
    sh = f' data-show="{show}"' if show else ""
    return f'''    <div class="ce-part" data-part="{key}"{sh}>
      <div class="ce-part-head"><h4>{e(title)} <span class="ce-max">{pts}</span></h4><output class="ce-part-score" data-out="{key}">—</output></div>
      <div class="ce-fields">{body}</div>
      {STATUS.format(k=key)}
    </div>'''


def dim(n, title, pts, parts, intro):
    return f'''  <section class="ce-dim" id="dim-{n}">
    <h3><span>{e(title)}</span> <output class="ce-dim-score" data-dim="{n}">— / {pts}</output></h3>
    <p class="ce-dim-intro">{intro}</p>
{chr(10).join(parts)}
  </section>'''


LENDER = "lender"; INS = "insurer"; NONFIN = "nonfin"; HYDRO = "hydro"; PRECOD = "precod"; NOTPRECOD = "notprecod"; NONLENDER = "nonlender"; NOTHYDRO = "nothydro"

D1 = dim("fin", "1. Financial Strength & Profitability", 20, [
    part("roe", "Three-year average ROE", "of 8",
         '<p class="ce-hint ce-block">Each year: profit for ordinary shareholders ÷ average of opening and closing equity (four year-end balance sheets).</p>' +
         num("roes", "ROE, oldest year", "%", i=0) +
         num("roes", "ROE, middle year", "%", i=1) + num("roes", "ROE, latest year", "%", i=2) +
         chk("equity_nonpositive", "Equity was zero or negative")),
    part("capital", "Capital cushion", "of 7",
         num("car", "Total CAR", "%", "Latest quarter-end, from the capital-adequacy disclosure.", show=LENDER) +
         num("tier1", "Tier 1 (core) capital", "%", show=LENDER) +
         num("cet1", "Common equity tier 1", "%", "Needed for commercial and national-level development banks.", show="cet1") +
         chk("breach_3y", "Below the requirement at any quarter-end in the last 3 years", show=LENDER) +
         num("solvency", "Official solvency ratio", "%", "Available capital ÷ risk-based capital requirement (NIA directive 2026).", show=INS) +
         num("solvency_wt", "Ratio without transitional provisions, if given", "%", "The lower of the two is scored.", show=INS) +
         chk("solvency_official", "From an official source (regulatory return, NIA disclosure or audited report)", show=INS) +
         num("de", "Debt-to-equity", "×", "All interest-bearing loans and lease liabilities ÷ equity.", show=NONFIN) +
         num("cover", "Interest cover", "×", "Operating profit ÷ all interest, including capitalised interest.", show=NONFIN) +
         chk("no_debt", "No interest-bearing debt", show=NONFIN) + chk("operating_loss", "Operating loss", show=NONFIN)),
    part("earnings", "Earnings quality", "of 5",
         row6("profits", "Net profit, six years, oldest first", "Rs (any unit, same for all six)", "Profit belonging to ordinary shareholders.") +
         num("cash_conversion", "Cash conversion, 3 years", "ratio", "3-year operating cash flow ÷ 3-year net profit. Below 0.5 loses a point.", show=NONFIN) +
         num("writeback_max", "Largest yearly share of profit from write-backs or one-off gains, last 3 years", "%", "Over 25% loses a point.", show=LENDER) +
         num("gain_max", "Largest yearly share of profit from realised gains or released reserves, last 3 years", "%", "Over 25% loses a point.", show=INS)),
], "ROE, the capital cushion and the profit record. Use audited annual reports; consolidated accounts where published.")

AUDIT = [("", "Choose the auditor's finding"), ("clean", "Clean; related-party dealings small and disclosed (5)"),
         ("emphasis", "Clean with an emphasis-of-matter note (4)"), ("restated_or_large_rpt", "Earlier year restated, or large disclosed related-party dealings (3)"),
         ("qualified_limited", "Qualified on a limited, explained matter (2)"),
         ("qualified_serious_or_going_concern", "Qualified on loans, provisions or related-party deals; scope limit; going-concern doubt (1, cap)"),
         ("adverse_disclaimer_undisclosed_rpt", "Adverse, disclaimer, or undisclosed related-party dealings (0, cap)")]
D2 = dim("gov", "2. Governance & Promoter Behaviour", 15, [
    part("promoter", "Promoter holding and pledging", "of 6",
         num("promoter_fall", "Unexplained fall in promoter holding, 3 years", "points", "Percentage points of all shares; enter a rise as a negative number. Ignore falls from mergers, required sales or new issues.") +
         num("pledged", "Pledged promoter shares ÷ all promoter shares", "%") +
         chk("pledge_unverified", "Pledge data not found (at most 4)") + chk("repeated_selling", "Unexplained insider selling in 2 of the last 3 years")),
    part("audit", "Audit opinion and related-party dealings", "of 5", sel("audit", "Audit finding", AUDIT)),
    part("board", "Disclosure and board", "of 4",
         num("independents", "Independent directors", "", "Those meeting the law's tests.", step="1") +
         num("legal_min", "Legal minimum", "", "1 for banks (BAFIA 2073); 1 for boards up to 7 and 2 for larger boards (Companies Act).", step="1") +
         num("late_filings", "Late quarterly reports or AGMs, 3 years", "", step="1") +
         chk("penalised", "Penalised by SEBON or NEPSE for a disclosure failure") +
         sel("tests_met", "Attendance (75%+) and audit-committee tests", [("unchecked", "Not checked"), ("yes", "Met"), ("no", "Not met")])),
], "Read the annual report, the related-party note, NEPSE and SEBON notices, and CDSC promoter records.")

D3 = dim("liq", "3. Liquidity & Tradability", 10, [
    part("turnover", "Average daily turnover, 6 months", "of 5",
         num("turnover_avg", "Average daily traded value", "Rs", "Ordinary market only, over all NEPSE trading days.", step="1") +
         num("turnover_median", "Median daily traded value", "Rs", "If the average is over twice the median, the median is used.", step="1") +
         num("days_traded", "Share of trading days it traded", "%", "Under 50% caps the score at 1.") +
         num("block_excluded", "Block or negotiated deals to remove, per day", "Rs", step="1")),
    part("float", "Free float", "of 5", num("free_float", "Free float", "%", "Leave out promoter, government, strategic, cross-held and locked-in shares.")),
], "Daily turnover and free float. A first screen, not proof that your own order can be sold in a panic.")

D4 = dim("val", "4. Valuation Reasonableness", 15, [
    part("pe", "P/E against the sector median", "of 8",
         num("eps_ttm", "EPS, last four quarters", "Rs") + num("median_pe", "Sector median P/E", "×", "Comparable peers only; leave out loss-makers."), show=NOTPRECOD),
    part("pb", "P/B against the sector median", "of 7 (of 15 before production)",
         num("bvps", "Book value per share", "Rs", "Latest published quarter.") + num("median_pb", "Sector median P/B", "×", "Include loss-makers with positive book value.") +
         num("peers", "Number of peer companies in each median", "", "Fewer than 5: unverified, scored in line.", step="1") +
         sel("roe_ge_median", "Is the company's ROE at or above the sector median?", [("yes", "Yes"), ("no", "No")], hint="Needed for a discount to earn the top row.") +
         sel("npl_ok", "Is its NPL at or below its class average?", [("yes", "Yes"), ("no", "No")], show=LENDER)),
], "Relative price only. A DCF or reverse DCF is a separate cross-check, not a source of points.")

D5 = dim("dur", "5. Sector & Business Model Durability", 15, [
    part("moat", "Moat", "of 8", sel("moat", "Business position", [("", "Choose"), ("8", "High barriers with proof (ROE ≥ median 4 of 5 years; lender NPL ≤ class; hydro ≥90% contracted energy, 10+ years PPA) (8)"),
                                                            ("5", "Moderate barriers, or a licence without that proof (5)"), ("2", "Low barriers; commodity-like (2)"), ("0", "Structural threat (0)")],
                                       hint="A licence alone is not a moat.")),
    part("concentration", "Concentration", "of 7",
         num("concentration", "Largest single exposure", "%", "Customer, product, region or supplier; for a lender, its biggest loan sector or region.", show="conc") +
         chk("single_buyer", "Sells all its power to NEA under one PPA (scores 0)", show=HYDRO, checked=True)),
], "Will the business still matter, and still earn, in ten years?")

D6 = dim("gro", "6. Growth Trajectory", 15, [
    part("growth", "Business growth", "of 8",
         num("loan_cagr", "Company's 5-year loan CAGR", "%", show=LENDER) + num("system_cagr", "Its class's 5-year loan CAGR", "%", "Same six year-ends, NRB figures.", show=LENDER) +
         num("deposit_cagr", "Company's 5-year deposit CAGR", "%", show=LENDER) +
         chk("credit_peak", "Credit peak now (system credit growth over 20%, or CD ratio within 5 points of the ceiling)", show=LENDER) +
         chk("system_verified", "System figure verified for the same period", show=LENDER, checked=True) +
         num("gross_npl", "Gross NPL", "%", show=LENDER) + num("class_npl", "Class average gross NPL", "%", show=LENDER) +
         num("adj_npl", "Write-off-adjusted NPL, now", "%", show=LENDER) + num("adj_npl_prev", "Write-off-adjusted NPL, a year ago", "%", show=LENDER) +
         num("restructured", "Restructured or rescheduled loans", "% of loans", show=LENDER) +
         row6("revenue", "Operating revenue, six years, oldest first", "Rs", "Insurers: net earned premium. Leave out one-off and revaluation gains.", show=NONLENDER) +
         chk("merger", "A merger in the period, without combined figures (at most 6)", show=NONLENDER) +
         chk("revenue_insufficient", "Fewer than four year-on-year comparisons (scores 3, unverified)", show=NONLENDER)),
    part("eps", "EPS growth", "of 7",
         row6("eps_series", "Basic EPS, six years, oldest first", "Rs", "On a comparable share count: adjust earlier years for later bonus and rights issues.") +
         chk("eps_insufficient", "Fewer than six EPS figures (at most 2, unverified)")),
], "Steady growth, not wild growth. For a lender, fast lending against the system is a warning.")

YEARS = "".join(f'<div class="ce-divyear"><span>Year {i+1}</span><label class="ce-check"><input type="checkbox" data-k="div_cash" data-i="{i}"> Real cash</label><input type="number" step="any" inputmode="decimal" data-k="div_payout" data-i="{i}" placeholder="payout %" aria-label="Cash payout year {i+1}"></div>' for i in range(5))
D7 = dim("div", "7. Dividend & Capital Return Discipline", 10, [
    part("div_record", "Dividend record, 5 years", "of 6",
         '<p class="ce-hint ce-block">Tick a year only for a real cash dividend (not the token cash that pays the bonus tax). Payout = cash dividend ÷ distributable profit.</p><div class="ce-divgrid">' + YEARS + '</div>' + chk("div_none", "No real cash dividend in any of the five years")),
    part("div_source", "Source and reason", "of 4", sel("div_source", "Where the dividend came from", [("", "Choose"), ("genuine", "Genuine distributable profit, reserves intact, reason stated for profit kept (4)"),
                                                                                                ("partly", "Partly one-off or revaluation gains, or no reason given for profit kept (2)"), ("capital", "Paid out of capital or reserves (0)")])),
], "Only real cash counts. The 30–70% payout range is a Canon preference, not a rule of finance.")

SECTORS = [("commercial", "Commercial bank (class A)"), ("devbank_national", "National-level development bank (class B)"),
           ("devbank_other", "Other development bank (class B)"), ("finance", "Finance company (class C)"), ("mfi", "Microfinance institution (class D)"),
           ("hydro", "Hydropower, operating"), ("hydro_precod", "Hydropower, not yet producing"), ("life", "Life insurer"), ("nonlife", "Non-life insurer"),
           ("other", "Manufacturing, hotel, trading or other")]


def main():
    sectors = "".join(f'<option value="{v}">{e(t)}</option>' for v, t in SECTORS)
    article = f'''<article class="chapter ce-page">
  <div class="chapter-kicker">Nepal Edition · Practical Tool</div>
  <h1>Canon Score Engine</h1>
  <p class="ce-lead">Type the figures from a company's own reports, and this page scores all sixteen parts of the Canon Score exactly as <a href="chapters/ch-64-seven-dimension-score.html">Chapter 64</a> (rubric 1.6.0) sets them out, applies the caps and the evidence grade, and shows how every point was reached.</p>

  <div class="ce-facts">
    <p><strong>What it does.</strong> The arithmetic and the rules, with no judgement of its own. It gives the same answers as the book's reference calculation: all 106 published test cases pass, and 6,000 random cases agree.</p>
    <p><strong>What it does not do.</strong> It does not fetch data. NEPSE, NRB and company reports have no official feed it could read reliably, and a wrongly copied figure looks just as certain as a right one. You find the figures; the engine scores them.</p>
    <p><strong>Where to find the figures.</strong> Audited annual reports and quarterly reports (company websites and NEPSE), NRB's monthly report for system figures, NIA for insurers, CDSC records for promoter holdings. Mark any figure you could not check, so the evidence grade stays honest.</p>
  </div>

  <div class="ce-bar" hidden>
    <div class="ce-bar-row">
      <label for="ce-company">Company</label>
      <input id="ce-company" type="text" placeholder="Name or NEPSE symbol" autocomplete="off" list="ce-saved">
      <datalist id="ce-saved"></datalist>
      <button type="button" class="ce-btn" data-act="new">New</button>
      <button type="button" class="ce-btn" data-act="example">Load an example</button>
      <button type="button" class="ce-btn" data-act="export">Save a file</button>
      <label class="ce-btn ce-file">Open a file<input type="file" accept="application/json,.json" data-act="import" hidden></label>
      <button type="button" class="ce-btn" data-act="clear">Clear</button>
      <button type="button" class="ce-btn ce-btn-main" data-act="print">Print</button>
    </div>
    <div class="ce-summary" aria-live="polite"></div>
  </div>

  <section class="ce-dim ce-setup">
    <h3><span>Company type and dates</span></h3>
    <div class="ce-fields">
      <label class="ce-field ce-wide"><span class="ce-label">Type of company</span><span class="ce-hint">This sets which tests apply and the capital minimum.</span><select data-k="sector">{sectors}</select></label>
      <label class="ce-field"><span class="ce-label">Share price</span><span class="ce-hint">Used for P/E and P/B.</span><span class="ce-input"><span class="ce-unit">Rs</span><input type="number" step="any" inputmode="decimal" data-k="price"></span></label>
      <label class="ce-field"><span class="ce-label">Share-price date</span><input type="date" data-k="price_date"></label>
      <label class="ce-field"><span class="ce-label">Data cut-off date</span><input type="date" data-k="cutoff_date"></label>
    </div>
  </section>

{D1}
{D2}
{D3}
{D4}
{D5}
{D6}
{D7}

  <section class="ce-dim" id="limits">
    <h3><span>Hard limits and records</span></h3>
    <p class="ce-dim-intro">These cap the total at 54, exclude the company, or make the score provisional, whatever the other parts say.</p>
    <div class="ce-fields">
      {chk("problematic", "NRB has declared the company \"problematic\" (cap 54)")}
      {chk("disclaimer", "The latest audit opinion is a disclaimer (cap 54)")}
      {chk("fraud", "A final court or regulator finding of fraud by management or controlling shareholders (excluded; allegations do not count)")}
      {chk("restated", "Accounts materially restated, without a full new audited year (provisional)")}
    </div>
  </section>

  <section class="ce-dim ce-results" id="results">
    <h3><span>Result</span></h3>
    <div class="ce-result" aria-live="polite"></div>
    <div style="overflow-x:auto;"><table class="figures ce-table"><thead><tr><th scope="col">Part</th><th scope="col">Points</th><th scope="col">Evidence</th><th scope="col">How the points were reached</th></tr></thead><tbody class="ce-tbody"></tbody></table></div>
  </section>

  <section class="ce-dim" id="size">
    <h3><span>How much could I hold?</span></h3>
    <p class="ce-dim-intro">The most you may hold is the smallest of the band's ceiling, the liquidity limit and the sector limit (Chapters 56 and 66). You can always buy less.</p>
    <div class="ce-fields">
      {num("money", "Whole share money (steady + active)", "Rs", step="1000")}
      {num("active", "Active part the season lets you use now", "Rs", step="1000")}
      {num("adv20", "20-day average daily turnover", "Rs", step="10000")}
      {num("sector_now", "Already in this sector, counting funds", "Rs", step="1000")}
      {num("sector_pct", "Sector ceiling", "%", "25–30%; 25 is used if left blank.")}
    </div>
    <div class="ce-size" aria-live="polite"></div>
  </section>

  <section class="ce-dim" id="answer">
    <h3><span>Suggested answer</span></h3>
    <div class="ce-answer" aria-live="polite"></div>
    <p class="ce-dim-intro">The score covers the company and its price. Your own readiness, the money season, circuit traps, price against value and your written sell rules are in the <a href="first-purchase-checklist.html">Complete First Purchase Checklist</a>; finish it before any order.</p>
  </section>

  <p class="ce-note">Rubric 1.6.0, adopted 27 November 2026. Judgement still enters in grouping exposures for concentration, the moat evidence, whether a gain is one-off, small versus large related-party dealings, and the interim insurer rules (Chapter 64). Scores are saved only in this browser; use "Save a file" to keep a copy. Education, not advice to buy or sell any share. Engine code: <a href="js/canon-engine.js">canon-engine.js</a>; reference: <a href="data/canon_score_reference_v1_6_0.py">Python</a>; tests: <a href="data/canon-score-test-cases-v1.6.0.json">106 cases</a>.</p>

  <div class="chapter-nav">
    <a href="first-purchase-checklist.html">← Complete Checklist</a>
    <a href="chapters/ch-64-seven-dimension-score.html">Chapter 64 →</a>
  </div>
</article>'''

    t = SRC.read_text(encoding="utf-8")
    title = "Canon Score Engine"
    desc = ("Score any NEPSE company on the Canon Score (rubric 1.6.0) from the figures in its own reports: all sixteen parts, caps, "
            "evidence grade, band and position ceiling, with every point explained. Tested against the book's 106 published cases.")
    old_title = re.search(r"<title>(.*?)</title>", t).group(1)
    t = t.replace(old_title, title + " — The Investor&#x27;s Canon")
    t = t.replace("Your First Share Purchase: An 8-Step Guide — The Investor's Canon", title + " — The Investor's Canon")
    od = re.search(r'<meta name="description" content="([^"]*)"', t).group(1)
    t = t.replace(od, html.escape(desc, quote=True))
    t = t.replace("investors-canon/first-purchase.html", "investors-canon/canon-score-engine.html")
    a = t.index('<article class="chapter'); b = t.index("</article>", a) + len("</article>")
    t = t[:a] + article + t[b:]
    t = re.sub(r'(<link rel="stylesheet" href="css/style\.css[^>]*>)', r'\1\n<link rel="stylesheet" href="css/engine.css?v=1">', t, count=1)
    t = t.replace('<script src="js/audio-reader.js" defer></script>',
                  '<script src="js/canon-engine.js?v=1" defer></script>\n<script src="js/engine-page.js?v=1" defer></script>\n<script src="js/audio-reader.js" defer></script>', 1)
    OUT.write_text(t, encoding="utf-8")
    print("canon-score-engine.html written")


if __name__ == "__main__":
    main()
