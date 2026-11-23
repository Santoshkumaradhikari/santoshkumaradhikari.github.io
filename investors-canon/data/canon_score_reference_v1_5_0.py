"""The Investor's Canon - reference calculation for Canon Score rubric 1.5.0 (Chapter 64).

Purpose: show that the written rules give one answer. Each function follows one table
or rule in Chapter 64. Run this file to check it against
canon-score-test-cases-v1.5.0.json (same folder):  python3 canon_score_reference_v1_4_3.py

Conventions (Chapter 64 ground rules):
- "X to under Y" includes X, not Y; "over X up to Y" includes Y, not X;
  "or more / or higher / or less / at least" include the figure; "under / over" do not.
- Percentages are written as numbers (15 means 15%).
- A five-year record = five year-on-year comparisons from six annual figures, oldest first.
  Loss years and "the last five years" refer to the five most recent figures.
- "Grew" = strictly higher than the year before.
- A big swing = change of more than 50% up or down, or any change into or out of a loss.
This is a teaching reference, not investment software.
"""
import json, os, sys

# ---------------------------------------------------------------- helpers
def comparisons(series):
    """five year-on-year pairs from six figures, oldest first"""
    assert len(series) == 6, "need six annual figures"
    return list(zip(series[:-1], series[1:]))

def big_swing(prev, cur):
    if (prev < 0) != (cur < 0):      # into or out of a loss
        return True
    if prev == 0:
        return cur != 0
    return abs(cur - prev) / abs(prev) > 0.5

def n_big_swings(series, ignore_loss_transitions=False):
    n = 0
    for a, b in comparisons(series):
        if ignore_loss_transitions and (a < 0) != (b < 0):
            continue
        n += big_swing(a, b)
    return n

# ---------------------------------------------------------------- Dimension 1
def roe_points(roes, equity_nonpositive=False):
    """roes: three annual ROEs (%), oldest first"""
    if equity_nonpositive or any(r < 0 for r in roes):
        return 1
    avg = sum(roes) / 3
    if avg >= 15:
        return 8 if min(roes) >= 10 else 6
    if avg >= 10:
        return 6
    if avg >= 7:
        return 4
    return 1

def car_points(car, minimum, all_components_met=True, breach_in_last_3y=False):
    if car < minimum or not all_components_met:
        return 0
    gap = car - minimum
    pts = 7 if gap >= 2.0 else 5 if gap >= 0.5 else 3
    return min(pts, 3) if breach_in_last_3y else pts

def insurer_points(solvency_pct, nia_2026_verified=False):
    pts = 7 if solvency_pct >= 200 else 5 if solvency_pct >= 130 else 3 if solvency_pct >= 100 else 0
    return pts if nia_2026_verified else min(pts, 3)   # unverified until NIA 2026 directive is read

def de_points(de, equity_nonpositive=False):
    if equity_nonpositive:
        return 0
    return 3 if de < 1.0 else 2 if de < 2.0 else 1 if de < 3.0 else 0

def cover_points(cover=None, no_interest_bearing_debt=False, operating_loss=False):
    if operating_loss:
        return 0
    if no_interest_bearing_debt:
        return 4
    return 4 if cover >= 5 else 3 if cover >= 3 else 1 if cover >= 1.5 else 0

def earnings_quality(profits, sector="other", cash_conversion=None, writeback_share_max=None, insurer_gain_share_max=None):
    """profits: six annual net profits, oldest first"""
    recent = profits[1:]
    losses = sum(p < 0 for p in recent)
    grew = sum(b > a for a, b in comparisons(profits))
    not_grew = 5 - grew
    swings = n_big_swings(profits, ignore_loss_transitions=True)   # loss rows already price loss years
    if losses >= 2 or swings >= 2:
        pts = 1
    elif losses == 1:
        pts = 2
    elif grew >= 4:
        pts = 5
    elif not_grew == 2:
        pts = 3
    else:
        pts = 2
    deduct = 0
    if sector == "other" and cash_conversion is not None and sum(profits[-3:]) > 0 and cash_conversion < 0.5:
        deduct = 1
    if sector == "lender" and writeback_share_max is not None and writeback_share_max > 25:
        deduct = 1
    if sector == "insurer" and insurer_gain_share_max is not None and insurer_gain_share_max > 25:
        deduct = 1
    return max(0, pts - deduct)

# ---------------------------------------------------------------- Dimension 2
def promoter_points(fall_points_unexplained, pledged_pct, repeated_selling=False):
    """fall_points_unexplained: fall in promoter % of all shares over 3 years after explained changes (negative = rise)"""
    f = fall_points_unexplained
    if repeated_selling or f > 5:
        a = 0
    elif f >= 3:
        a = 2
    elif f >= 1:
        a = 4
    else:
        a = 6
    b = 6 if pledged_pct < 10 else 4 if pledged_pct < 25 else 2 if pledged_pct <= 50 else 0
    return min(a, b)

AUDIT = {"clean": 5, "emphasis": 4, "restated_or_large_rpt": 3, "qualified_limited": 2,
         "qualified_serious_or_going_concern": 1, "adverse_disclaimer_undisclosed_rpt": 0}

def board_points(penalised=False, late_filings=0, independents=0, legal_min=1, tests_met=False):
    if penalised:
        return 0
    if late_filings >= 2 or independents < legal_min:
        return 1
    if late_filings == 1:
        return 2
    if independents > legal_min and tests_met:
        return 4
    return 3

# ---------------------------------------------------------------- Dimension 3
def turnover_points(avg_rs, median_rs=None, share_of_days_traded=1.0, block_value_excluded_rs=0):
    """avg_rs: ordinary-market average; pass identified block/negotiated value per day as block_value_excluded_rs"""
    avg_rs = avg_rs - block_value_excluded_rs
    base = avg_rs
    if median_rs is not None and avg_rs > 2 * median_rs:
        base = median_rs
    pts = 5 if base >= 5_000_000 else 3 if base >= 1_000_000 else 1 if base >= 200_000 else 0
    if share_of_days_traded < 0.5:
        pts = min(pts, 1)
    return pts

def float_points(pct):
    return 5 if pct >= 40 else 3 if pct >= 25 else 1 if pct >= 10 else 0

# ---------------------------------------------------------------- Dimension 4
def pe_points(rel, ttm_eps_negative=False, roe_ge_median=True, lender_npl_ok=True):
    if ttm_eps_negative:
        return 0
    if rel <= 0.8:
        return 8 if (roe_ge_median and lender_npl_ok) else 6
    return 6 if rel <= 1.1 else 3 if rel <= 1.5 else 1

def pb_points(rel, book_negative=False, roe_ge_median=True, lender_npl_ok=True):
    if book_negative:
        return 0
    if rel <= 0.8:
        return 7 if (roe_ge_median and lender_npl_ok) else 5
    return 5 if rel <= 1.1 else 3 if rel <= 1.5 else 1

def valuation_points(pe=None, pb=None, pre_cod=False, **kw):
    if pre_cod:                      # P/E not applicable; no ROE, so discount gate fails
        p = pb_points(pb, roe_ge_median=False)
        return int(p / 7 * 15 + 0.5)
    return pe_points(pe, **{k: v for k, v in kw.items() if k in ("ttm_eps_negative", "roe_ge_median", "lender_npl_ok")}) + \
           pb_points(pb, **{k: v for k, v in kw.items() if k in ("book_negative", "roe_ge_median", "lender_npl_ok")})

# ---------------------------------------------------------------- Dimension 5
def concentration_points(largest_pct):
    return 7 if largest_pct <= 20 else 4 if largest_pct <= 40 else 2 if largest_pct <= 60 else 0

# ---------------------------------------------------------------- Dimension 6
def revenue_points(revenue, merger_without_combined=False, insufficient_history=False):
    """revenue: six annual figures, oldest first; insufficient_history: fewer than four comparisons available"""
    if insufficient_history:
        return 3
    if revenue[0] <= 0:              # zero / part-year start: growth-years test on last four comparisons
        last4 = comparisons(revenue)[1:]
        return 3 if sum(b > a for a, b in last4) >= 3 else 0
    cagr = ((revenue[-1] / revenue[0]) ** (1 / 5) - 1) * 100
    grew = sum(b > a for a, b in comparisons(revenue))
    swings = n_big_swings(revenue)
    if cagr < 0 or swings >= 2:
        pts = 0
    elif cagr >= 15:
        pts = 8 if grew >= 4 else 6
    elif cagr >= 8:
        pts = 6
    else:
        pts = 3
    return min(pts, 6) if merger_without_combined else pts

def lender_growth_points(lender_cagr, system_cagr, deposit_cagr, credit_peak=False,
                         gross_npl=None, class_gross_npl=None, adj_npl=None, adj_npl_prev=None,
                         restructured_pct=0.0, system_verified=True):
    diff = lender_cagr - system_cagr
    if credit_peak and diff > 5:
        return 0                     # final: skip steps 2-4
    if lender_cagr < 0 <= system_cagr and system_cagr > 0:
        row = 2
    elif abs(diff) <= 5:
        row = 8
    elif abs(diff) <= 10:
        row = 5
    else:
        row = 2
    ladder = [8, 5, 2]
    idx = ladder.index(row)
    drops = 0
    if lender_cagr - deposit_cagr > 5:
        drops += 1
    npl_drop = (gross_npl is not None and class_gross_npl is not None and adj_npl is not None and adj_npl_prev is not None
                and gross_npl > class_gross_npl and adj_npl > adj_npl_prev)
    if npl_drop or restructured_pct > 5:
        drops += 1
    pts = ladder[min(idx + drops, 2)]
    if not system_verified:
        pts = min(pts, 5)
    return pts

def eps_points(eps, insufficient_history=False):
    """eps: six annual basic EPS on a comparable share count, oldest first"""
    if insufficient_history:
        return 2
    rose = sum(b > a and b > 0 for a, b in comparisons(eps))
    swings = n_big_swings(eps)
    negatives = sum(e < 0 for e in eps[1:])
    if rose < 2 or negatives >= 3:
        pts = 0
    elif rose == 2 or swings >= 2:
        pts = 2
    elif rose == 3:
        pts = 4 if swings <= 1 else 2
    else:
        pts = 7 if swings == 0 else 4 if swings == 1 else 2
    if eps[-1] < 0 or negatives >= 2:
        pts = min(pts, 2)
    return pts

# ---------------------------------------------------------------- Dimension 7
def dividend_consistency(real_cash, payout):
    """real_cash: five booleans (real cash dividend each year); payout: five cash payout ratios in %, or None where not applicable"""
    paid = sum(real_cash)
    outside = sum(1 for c, p in zip(real_cash, payout) if c and (p is None or p < 30 or p > 70))
    if paid == 5:
        return 6 if outside <= 1 else 4
    if paid == 4:
        return 4
    if paid >= 2:
        return 2
    return 0

def source_points(from_capital_or_reserves=False, partly_one_off=False, stated_reason=True, reserves_ok=True):
    if from_capital_or_reserves:
        return 0
    if partly_one_off or not stated_reason or not reserves_ok:
        return 2
    return 4

# ---------------------------------------------------------------- combining
BANDS = [(85, "Exceptional combined score", "6%-8%"), (70, "Strong", "4%-6%"), (55, "Adequate", "1.5%-3%"),
         (45, "Weak / Avoid - watch list", "no new money"), (0, "Weak / Avoid - exclude", "no new money")]

def total_with_limits(dims, governance_total, pledging_pts, audit_pts, problematic=False,
                      capital_below_min=False, disclaimer=False, fraud=False):
    total = sum(dims.values())
    if fraud:
        return None                  # excluded
    if governance_total < 5 or pledging_pts == 0 or audit_pts <= 1 or problematic or capital_below_min or disclaimer:
        total = min(total, 54)
    return total

def band(total):
    for floor, name, ceiling in BANDS:
        if total >= floor:
            return name, ceiling

def ceiling(total, business_quality, share_attractiveness, provisional=False):
    i = next(k for k, (floor, _, _) in enumerate(BANDS) if total >= floor)
    if (i <= 1 and (business_quality < 38 or share_attractiveness < 13)) or provisional:
        i += 1                       # one band down at most, even if both rules apply
    return BANDS[min(i, len(BANDS) - 1)][2]

# ---------------------------------------------------------------- test runner
FUNCS = {k: v for k, v in globals().items() if callable(v) and not k.startswith('_')}

def run(path):
    cases = json.load(open(path))["cases"]
    bad = 0
    for c in cases:
        got = FUNCS[c["function"]](**c["inputs"])
        if isinstance(got, tuple):
            got = list(got)
        ok = got == c["expected"]
        bad += not ok
        print(("PASS" if ok else "FAIL"), c["id"], c["function"], "expected", c["expected"], "got", got)
    print(f"{len(cases) - bad} of {len(cases)} cases pass")
    return bad

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(1 if run(os.path.join(here, "canon-score-test-cases-v1.5.0.json")) else 0)
