"""The Investor's Canon - reconciliation of the published package for Canon Score rubric 1.5.0 (Chapter 64).

Checks that the five files that make up the rubric say the same thing:
  1. the chapter page (chapters/ch-64-seven-dimension-score.html) - every scoring table,
  2. the specification (canon-score-spec-v1.5.0.json) - every band,
  3. the reference calculation (canon_score_reference_v1_5_0.py) - via the 91 test cases,
  4. the property audit (canon_score_properties_v1_5_0.py),
  5. the case-study calculation (canon_case_ebl_nica_v1_5_0.py),
rebuilds the HUBL worked example (Lesson 64.6) from its stated inputs, and checks the case study page
(chapters/ch-64a-two-banks-scored.html): its glance-table scores and provisional-parts table against the case
script, and its printed file fingerprints against the input file and script.

For each of the 21 scoring tables it compares, row by row: the points, the table maximum, every threshold
number in the specification's row text, and the boundary words ("under", "or more", "up to", "over", "or less").
Run from this folder:  python3 canon_score_reconcile_v1_5_0.py      (exit code 0 = the package agrees)
Written 25 Nov 2026. Teaching material, not investment software.
"""
import contextlib, hashlib, html, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "chapters", "ch-64-seven-dimension-score.html")
SPEC = json.load(open(os.path.join(HERE, "canon-score-spec-v1.5.0.json")))
D = SPEC["dimensions"]

# chapter table (in page order) -> specification band list and stated maximum
MAP = [
    ("3-year average ROE", D[0]["sub"][0]["bands"], 8),
    ("Regulatory capital cushion", D[0]["sub"][1]["bands"], 7),
    ("Solvency cushion (insurers", D[0]["sub"][2]["bands"], 7),
    ("Debt-to-equity", D[0]["sub"][3]["parts"][0]["bands"], 3),
    ("Interest cover", D[0]["sub"][3]["parts"][1]["bands"], 4),
    ("Profit record", D[0]["sub"][4]["bands"], 5),
    ("Promoter holding, last 3 years", D[1]["sub"][0]["bands"]["A_holding"], 6),
    ("Share of promoter shares pledged", D[1]["sub"][0]["bands"]["B_pledged"], 6),
    ("Audit opinion and related-party", D[1]["sub"][1]["bands"], 5),
    ("Disclosure and board structure", D[1]["sub"][2]["bands"], 4),
    ("Average daily turnover", D[2]["sub"][0]["bands"], 5),
    ("Free float", D[2]["sub"][1]["bands"], 5),
    ("Current P/E", D[3]["sub"][0]["bands"], 8),
    ("Current P/B", D[3]["sub"][1]["bands"], 7),
    ("Business position", D[4]["sub"][0]["bands"], 8),
    ("Largest single exposure", D[4]["sub"][1]["bands"], 7),
    ("5-year revenue CAGR", D[5]["sub"][0]["bands"], 8),
    ("Lender's loan growth", D[5]["sub"][1]["bands"], 8),
    ("EPS on a comparable share count", D[5]["sub"][2]["bands"], 7),
    ("Dividend record, last 5 years", D[6]["sub"][0]["bands"], 6),
    ("Source and reason", D[6]["sub"][1]["bands"], 4),
]
ALIAS = {"0.2": {"200,000", "2 lakh"}, "1": {"1"}, "5": {"5"}}   # Rs 0.2 million is printed as Rs 200,000
WORDS = ["to under", "up to", "or more", "or less", "over", "under"]
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")

fail, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fail.append(msg)


page = open(PAGE).read()
tables = re.findall(r'<table class="figures">(.*?)</table>', page, flags=re.S)
txt = lambda c: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()

for title, bands, mx in MAP:
    tab = next((t for t in tables if title in txt(re.findall(r"<tr>(.*?)</tr>", t, flags=re.S)[0])), None)
    ok(tab is not None, f"table '{title}' not found in the chapter")
    if tab is None:
        continue
    rows = re.findall(r"<tr>(.*?)</tr>", tab, flags=re.S)
    head = txt(rows[0])
    ok(f"(of {mx})" in head, f"'{title}': chapter header {head!r} does not state a maximum of {mx}")
    body = [[txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)] for r in rows[1:]]
    ok(len(body) == len(bands), f"'{title}': chapter has {len(body)} rows, specification {len(bands)}")
    for (text, pts), cells in zip(bands, body):
        page_text, page_pts = " ".join(cells[:-1]), cells[-1]
        ok(page_pts == str(pts), f"'{title}': row '{text}' scores {pts} in the specification, {page_pts} in the chapter")
        for n in NUM.findall(re.sub(r"Lesson \d+\.\d+", "", text)):   # skip cross-references such as "Lesson 64.2"
            alts = {n} | ALIAS.get(n, set())
            ok(any(a in page_text for a in alts), f"'{title}': threshold {n} in '{text}' not found in chapter row '{page_text}'")
        for w in WORDS:
            if re.search(rf"\b{w}\b", text) and not w == "under":
                ok(re.search(rf"\b{w}\b", page_text, flags=re.I) is not None, f"'{title}': boundary words '{w}' in '{text}' missing from '{page_text}'")

# dimension maxima: Lesson 64.1 table vs specification
first = [[txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)] for r in re.findall(r"<tr>(.*?)</tr>", tables[0], flags=re.S)[1:8]]
for dim, row in zip(D, first):
    ok(row[2] == str(dim["points"]), f"Lesson 64.1: {row[1]} shows {row[2]}, specification {dim['points']}")
ok(sum(d["points"] for d in D) == 100, "specification dimension points do not add up to 100")
for name, dims in (("business_quality_score", [1, 2, 5, 6, 7]), ("share_attractiveness_score", [3, 4])):
    ok(SPEC["outputs"][name]["dimensions"] == dims, f"specification outputs.{name} dimensions changed")
ok(SPEC["version"] == "1.5.0", "specification version is not 1.5.0")

# HUBL (Lesson 64.6) rebuilt from its stated inputs with the reference functions: must give 87 = 68 + 19
import canon_score_reference_v1_5_0 as R
h = {
    "roe": R.roe_points([11.0, 15.2, 16.4]),
    "car": R.car_points(12.8, 11.0, all_components_met=True),                 # Tier 1 = CET1 10.3%
    "earnings": R.earnings_quality([100, 108, 117, 117, 127, 138], "lender", writeback_share_max=8),
    "promoter": R.promoter_points(0, 5),                                       # stable at 51%; under 10% pledged
    "audit": R.AUDIT["clean"],
    "board": R.board_points(late_filings=0, independents=2, legal_min=1, tests_met=True),
    "turnover": R.turnover_points(3.2e6, 2.6e6, 1.0),
    "float": R.float_points(49),
    "pe": R.pe_points(13.5 / 15.8), "pb": R.pb_points(1.3 / 1.5),
    "moat": 8,                                                                 # ROE >= median 4 of 5; NPL below average
    "concentration": R.concentration_points(30),
    "growth": R.lender_growth_points(11, 9, 10.5, gross_npl=2.9, class_gross_npl=4.0, adj_npl=3.1, adj_npl_prev=3.4,
                                     restructured_pct=1.2),
    "eps": R.eps_points([20.0, 21.6, 23.4, 23.4, 25.3, 27.4]),
    "dividends": R.dividend_consistency([True] * 5, [40] * 5), "source": 4,
}
bq = sum(h[k] for k in ("roe", "car", "earnings", "promoter", "audit", "board", "moat", "concentration", "growth", "eps", "dividends", "source"))
sa = sum(h[k] for k in ("turnover", "float", "pe", "pb"))
ok((bq, sa, bq + sa) == (68, 19, 87), f"HUBL rebuilt as {bq} + {sa} = {bq + sa}, chapter says 68 + 19 = 87")
for k, want in (("roe", 6), ("car", 5), ("earnings", 5), ("promoter", 6), ("audit", 5), ("board", 4), ("turnover", 3),
                ("float", 5), ("pe", 6), ("pb", 5), ("concentration", 4), ("growth", 8), ("eps", 7), ("dividends", 6)):
    ok(h[k] == want, f"HUBL {k}: reference gives {h[k]}, chapter shows {want}")

# Case study 64A: page vs case script vs files
import canon_case_ebl_nica_v1_5_0 as C
CASE = open(os.path.join(HERE, "..", "chapters", "ch-64a-two-banks-scored.html")).read()
ctabs = re.findall(r'<table class="figures">(.*?)</table>', CASE, flags=re.S)
rows_of = lambda t: [[txt(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S)] for r in re.findall(r"<tr>(.*?)</tr>", t, flags=re.S)]
with contextlib.redirect_stdout(io.StringIO()):
    got = {"EBL": C.report("EBL", C.ebl), "NICA": C.report("NICA", C.nica)}      # (total, bq, sa)
glance = next(rows_of(t) for t in ctabs if "Business Quality Score" in txt(t))
gl = {r[0].split(" (")[0]: r for r in glance}
for bank, col in (("EBL", 2), ("NICA", 3)):
    total, bq, sa = got[bank]
    for label, want in (("Business Quality Score", bq), ("Share Attractiveness Score", sa), ("Canon Score", total)):
        ok(gl.get(label, [""] * 4)[col] == str(want), f"64A glance table: {bank} {label} shows {gl.get(label, [''] * 4)[col]!r}, case script {want}")
PARTS = {"Promoter and pledging": ["promoter"], "Audit opinion": ["audit"], "Disclosure and board": ["board"], "Free float": ["float"],
         "P/E": ["valuation"], "P/B": ["valuation"], "Moat": ["moat"], "Concentration": ["concentration"], "Dividend source and reason": ["source"]}
prov = next((rows_of(t) for t in ctabs if "What would resolve it" in txt(t)), None)
ok(prov is not None, "64A provisional-parts table not found")
if prov:
    for bank, col, fn in (("EBL", 1, C.ebl), ("NICA", 2, C.nica)):
        flagged = fn()[1]
        page = {r[0]: r[col] for r in prov[1:]}
        val = sum(int(page[p]) for p in PARTS if page.get(p, "—").isdigit())
        ok(page.get("Total") == str(sum(flagged.values())), f"64A provisional total {bank}: page {page.get('Total')}, case script {sum(flagged.values())}")
        ok(val == sum(flagged.values()), f"64A provisional parts {bank} add to {val}, case script {sum(flagged.values())}")
        for p, keys in PARTS.items():
            if keys[0] == "valuation":
                continue
            want = sum(flagged.get(k, 0) for k in keys)
            ok(page.get(p, "—") == (str(want) if want else "—"), f"64A provisional part {p} {bank}: page {page.get(p)}, case script {want}")
        ok(int(page.get("P/E", "0")) + int(page.get("P/B", "0")) == flagged.get("valuation", 0), f"64A P/E + P/B {bank} != valuation {flagged.get('valuation')}")
for fname in ("canon-case-ebl-nica-v1.5.0.csv", "canon_case_ebl_nica_v1_5_0.py"):
    digest = hashlib.sha256(open(os.path.join(HERE, fname), "rb").read()).hexdigest()
    ok(digest in CASE, f"64A page does not print the current fingerprint of {fname} ({digest[:12]}...)")

# the executable files
for script, expect in (("canon_score_reference_v1_5_0.py", "91 of 91 cases pass"),
                       ("canon_score_properties_v1_5_0.py", "0 failures"),
                       ("canon_case_ebl_nica_v1_5_0.py", "checks pass")):
    out = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True).stdout
    ok(expect in out, f"{script} did not report '{expect}'")

print(f"{checks} reconciliation checks across {len(MAP)} scoring tables, the HUBL example and Case Study 64A; {len(fail)} disagreements")
for f in fail:
    print("DISAGREE", f)
sys.exit(1 if fail else 0)
