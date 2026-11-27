"""The Investor's Canon - property audit of the Canon Score reference calculation, rubric 1.6.0 (Chapter 64).

The 106 hand-worked test cases (canon-score-test-cases-v1.6.0.json) check chosen examples.
This file checks the rules themselves, over every boundary and over thousands of generated inputs:

  1. Every band boundary in the specification maps to exactly the row the written rule says
     ("X to under Y" includes X, not Y; "over X up to Y" includes Y, not X).
  2. No gaps and no overlaps: every input between the boundaries gets exactly one score.
  3. Direction: a better figure never scores lower than a worse one (monotonic tables).
  4. Range: no part ever scores above its maximum or below 0; the maxima add up to 100.
  5. Count-based tables (profit record, EPS, dividends) give one score for every possible pattern.
  6. Hard limits and position ceilings: caps never raise a score, never stack below 54,
     fraud always excludes, the insurer solvency cap (1.6.0) fires only for an official ratio
     under 100%, and the ceiling never drops more than one band.

Run:  python3 canon_score_properties_v1_6_0.py      (exit code 0 = all properties hold)
Written 25 Nov 2026 for the mathematical audit of Chapter 64. Teaching material, not investment software.
"""
import itertools, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canon_score_reference_v1_6_0 as R

FAIL = []
CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAIL.append(msg)


EPS = 1e-9


def boundaries(name, fn, table):
    """table: list of (input, expected) pairs at and either side of each boundary"""
    for x, want in table:
        got = fn(x)
        check(got == want, f"{name}({x}) = {got}, rule says {want}")


def monotone(name, fn, xs, increasing):
    vals = [fn(x) for x in xs]
    for (a, va), (b, vb) in zip(zip(xs, vals), zip(xs[1:], vals[1:])):
        ok = vb >= va if increasing else vb <= va
        check(ok, f"{name} not monotone between {a} ({va}) and {b} ({vb})")


grid = lambda lo, hi, step: [round(lo + i * step, 6) for i in range(int((hi - lo) / step) + 1)]

# ---------------------------------------------------------------- 1-3: single-number tables
# ROE: three equal years (no year below 10 unless the level itself is)
roe = lambda a: R.roe_points([a, a, a])
boundaries("roe", roe, [(15, 8), (15 - EPS, 6), (10, 6), (10 - EPS, 4), (7, 4), (7 - EPS, 1), (0, 1), (-0.01, 1)])
check(R.roe_points([16, 16, 9.99]) == 6, "roe: 15%+ average with a year below 10% must score 6")
check(R.roe_points([30, 30, -1]) == 1, "roe: any loss year must score 1")
check(R.roe_points([20, 20, 20], equity_nonpositive=True) == 1, "roe: zero/negative equity must score 1")
monotone("roe", roe, grid(-5, 30, 0.01), True)

car = lambda c: R.car_points(c, 11.0)
boundaries("car", car, [(13.0, 7), (13.0 - EPS, 5), (11.5, 5), (11.5 - EPS, 3), (11.0, 3), (11.0 - EPS, 0)])
check(R.car_points(14, 11, all_components_met=False) == 0, "car: any component below minimum must score 0")
check(R.car_points(14, 11, breach_in_last_3y=True) == 3, "car: past breach caps at 3")
monotone("car", car, grid(5, 25, 0.01), True)

boundaries("insurer", R.insurer_points,
           [(200, 7), (200 - EPS, 5), (130, 5), (130 - EPS, 3), (100, 3), (100 - EPS, 0)])
monotone("insurer", R.insurer_points, grid(0, 400, 0.01), True)
for a in grid(0, 300, 1):
    for b in (None, a - 20, a, a + 20):
        r = R.insurer_ratio_to_score(a, b)
        check(r == (a if b is None else min(a, b)), f"insurer ratio choice {a}/{b} -> {r}: must take the lower")

boundaries("de", R.de_points, [(1.0 - EPS, 3), (1.0, 2), (2.0 - EPS, 2), (2.0, 1), (3.0 - EPS, 1), (3.0, 0)])
monotone("de", R.de_points, grid(0, 6, 0.01), False)
boundaries("cover", R.cover_points, [(5, 4), (5 - EPS, 3), (3, 3), (3 - EPS, 1), (1.5, 1), (1.5 - EPS, 0)])
monotone("cover", R.cover_points, grid(0, 10, 0.01), True)

turn = lambda v: R.turnover_points(v)
boundaries("turnover", turn, [(5e6, 5), (5e6 - 1, 3), (1e6, 3), (1e6 - 1, 1), (2e5, 1), (2e5 - 1, 0)])
monotone("turnover", turn, [i * 10_000 for i in range(0, 1000)], True)
check(R.turnover_points(6e6, 1e6) == 3, "turnover: average > 2 x median must score from the median")
check(R.turnover_points(6e6, 3e6) == 5, "turnover: average exactly 2 x median is not > 2x")
check(R.turnover_points(6e6, None, 0.49) == 1, "turnover: thin trading must cap at 1")

boundaries("float", R.float_points, [(40, 5), (40 - EPS, 3), (25, 3), (25 - EPS, 1), (10, 1), (10 - EPS, 0)])
monotone("float", R.float_points, grid(0, 100, 0.01), True)

pe = lambda r: R.pe_points(r)
boundaries("pe", pe, [(0.8, 8), (0.8 + EPS, 6), (1.1, 6), (1.1 + EPS, 3), (1.5, 3), (1.5 + EPS, 1)])
check(R.pe_points(0.5, roe_ge_median=False) == 6, "pe: failed discount gate must give the in-line row")
check(R.pe_points(0.5, ttm_eps_negative=True) == 0, "pe: negative or zero TTM EPS must score 0")
monotone("pe", pe, grid(0.1, 5, 0.001), False)
pb = lambda r: R.pb_points(r)
boundaries("pb", pb, [(0.8, 7), (0.8 + EPS, 5), (1.1, 5), (1.1 + EPS, 3), (1.5, 3), (1.5 + EPS, 1)])
check(R.pb_points(0.5, lender_npl_ok=False) == 5, "pb: failed NPL gate must give the in-line row")
check(R.pb_points(0.5, book_negative=True) == 0, "pb: zero or negative book must score 0")
monotone("pb", pb, grid(0.1, 5, 0.001), False)
check(R.valuation_points(pb=0.5, pre_cod=True) == 11, "pre-COD valuation must be at most 11 (5/7 x 15)")

boundaries("concentration", R.concentration_points, [(20, 7), (20 + EPS, 4), (40, 4), (40 + EPS, 2), (60, 2), (60 + EPS, 0)])
monotone("concentration", R.concentration_points, grid(0, 100, 0.01), False)

prom = lambda f: R.promoter_points(f, 0)
boundaries("promoter A", prom, [(1 - EPS, 6), (1, 4), (3 - EPS, 4), (3, 2), (5, 2), (5 + EPS, 0), (-10, 6)])
pled = lambda p: R.promoter_points(0, p)
boundaries("promoter B", pled, [(10 - EPS, 6), (10, 4), (25 - EPS, 4), (25, 2), (50, 2), (50 + EPS, 0)])
check(R.promoter_points(0, 0, repeated_selling=True) == 0, "promoter: repeated insider selling must score 0")
monotone("promoter A", prom, grid(-5, 10, 0.01), False)
monotone("promoter B", pled, grid(0, 100, 0.01), False)

# lender loan growth: system at 8%
lg = lambda l: R.lender_growth_points(l, 8.0, l)
boundaries("loan growth", lg, [(13, 8), (13 + EPS, 5), (3, 8), (3 - EPS, 5), (18, 5), (18 + EPS, 2), (-2, 2)])
check(R.lender_growth_points(-1, 3, -1) == 2, "loan growth: shrinking while the system grows must score 2 (lower of two rows)")
check(R.lender_growth_points(-2, -4, -2) == 8, "loan growth: shrinking with a shrinking system is judged on the gap")
check(R.lender_growth_points(20, 8, 20, credit_peak=True) == 0, "loan growth: credit peak + >5 faster must score 0")
check(R.lender_growth_points(9, 8, 2) == 5, "loan growth: loans > 5 points faster than deposits must drop one row")
check(R.lender_growth_points(20, 8, 2, restructured_pct=6) == 2, "loan growth: drops cannot go below 2")
check(R.lender_growth_points(9, 8, 9, system_verified=False) == 5, "loan growth: unverified system caps at 5")

# ---------------------------------------------------------------- 5: count-based tables, every pattern
levels = [-3, -1, 1, 2, 3, 4, 8]        # includes losses, small and big moves
for seq in itertools.product(levels, repeat=6):
    eq = R.earnings_quality(list(seq), "lender")
    check(eq in (1, 2, 3, 5), f"earnings_quality{seq} = {eq} outside the table")
    ep = R.eps_points(list(seq))
    check(ep in (0, 2, 4, 7), f"eps_points{seq} = {ep} outside the table")
    if seq[-1] < 0:
        check(ep <= 2, f"eps_points{seq}: negative latest EPS must cap at 2")
    if sum(v < 0 for v in seq[1:]) >= 2:
        check(eq == 1, f"earnings_quality{seq}: two or more loss years must score 1")
for cash in itertools.product([True, False], repeat=5):
    for pays in itertools.product([20, 50, 80, None], repeat=5):
        d = R.dividend_consistency(list(cash), list(pays))
        n = sum(cash)
        want_max = 6 if n == 5 else 4 if n == 4 else 2 if n >= 2 else 0
        check(d <= want_max, f"dividend_consistency {cash} {pays} = {d} above {want_max}")
        check(d in (0, 2, 4, 6), f"dividend_consistency {cash} {pays} = {d} outside the table")

random.seed(64)
for _ in range(20_000):
    rev = [random.choice([0.0, 50, 90, 100, 120, 160, 250]) for _ in range(6)]
    if rev[0] <= 0:
        continue
    check(R.revenue_points(rev) in (0, 3, 6, 8), f"revenue_points{rev} outside the table")

# ---------------------------------------------------------------- 4: maxima add to 100
maxima = {"roe": 8, "capital": 7, "earnings": 5, "promoter": 6, "audit": 5, "board": 4, "turnover": 5, "float": 5,
          "pe": 8, "pb": 7, "moat": 8, "concentration": 7, "growth": 8, "eps": 7, "dividends": 6, "source": 4}
check(sum(maxima.values()) == 100, f"sub-score maxima add to {sum(maxima.values())}, not 100")
check(R.roe_points([99, 99, 99]) == 8 and R.car_points(99, 11) == 7 and R.de_points(0) + R.cover_points(99) == 7,
      "top rows must equal the stated maxima")

# evidence grade (1.6.0): one letter per count, never better for more missing points, D exactly when provisional (> 20)
order = "ABCD"
prev = "A"
for n in range(0, 101):
    g = R.evidence_grade(n)
    check(order.index(g) >= order.index(prev), f"evidence grade got better as missing points rose: {n} -> {g}")
    check((g == "D") == (n > 20), f"grade D must match the provisional test (> 20 points): {n} -> {g}")
    prev = g

# ---------------------------------------------------------------- 6: hard limits and ceilings
dims = {k: v for k, v in zip(range(1, 8), (20, 15, 10, 15, 15, 15, 10))}
for gov, pled, aud, prob, cap, disc in itertools.product([3, 5, 15], [0, 4, 6], [0, 1, 2, 5], *([[False, True]] * 3)):
    t = R.total_with_limits(dims, gov, pled, aud, problematic=prob, capital_below_min=cap, disclaimer=disc)
    fired = gov < 5 or pled == 0 or aud <= 1 or prob or cap or disc
    check(t == (54 if fired else 100), f"limits gov={gov} pled={pled} aud={aud} prob={prob} cap={cap} disc={disc} -> {t}")
check(R.total_with_limits(dims, 15, 6, 5, fraud=True) is None, "fraud finding must exclude")
# insurer solvency cap (1.6.0): fires only for an official ratio under 100%
for x in [i / 10 for i in range(0, 4001)]:
    for off in (False, True):
        t = R.total_with_limits(dims, 15, 6, 5, insurer_solvency_pct=x, solvency_official=off)
        check(t == (54 if (off and x < 100) else 100), f"insurer cap solvency={x} official={off} -> {t}")
check(R.total_with_limits(dims, 15, 6, 5) == 100, "no insurer ratio must not fire the insurer cap")
check(R.total_with_limits(dims, 3, 0, 0, problematic=True, insurer_solvency_pct=50, solvency_official=True) == 54,
      "insurer cap plus other caps must still cap once at 54")
check(R.total_with_limits(dims, 15, 6, 5, fraud=True, insurer_solvency_pct=50, solvency_official=True) is None,
      "fraud must exclude even when the insurer cap fires")
low = {k: 1 for k in range(1, 8)}
check(R.total_with_limits(low, 0, 0, 0, capital_below_min=True) == 7, "a cap must never raise a lower total")
for total in range(0, 101):
    i = next(k for k, b in enumerate(R.BANDS) if total >= b[0])       # the total's own band
    allowed = {R.BANDS[i][2], R.BANDS[min(i + 1, len(R.BANDS) - 1)][2]}
    for bq, sa in ((75, 25), (37, 25), (75, 12), (30, 10)):
        for prov in (False, True):
            got = R.ceiling(total, bq, sa, prov)
            check(got in allowed, f"ceiling total={total} bq={bq} sa={sa} prov={prov} -> {got}: more than one band down")
            if prov:
                check(got == R.BANDS[min(i + 1, len(R.BANDS) - 1)][2], f"provisional total={total} must take the next band's ceiling")
            if not prov and (bq >= 38 and sa >= 13):
                check(got == R.BANDS[i][2], f"total={total} with both part-scores in the top half must keep its band")

print(f"{CHECKS} property checks; {len(FAIL)} failures")
for f in FAIL[:30]:
    print("FAIL", f)
sys.exit(1 if FAIL else 0)
