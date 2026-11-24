"""The Investor's Canon - case study: Everest Bank (EBL) and NIC Asia Bank (NICA) under rubric 1.5.0.

Every input below is listed, with its source and status, in canon-case-ebl-nica-v1.5.0.csv (same folder).
Run:  python3 canon_case_ebl_nica_v1_5_0.py
It uses the reference functions in canon_score_reference_v1_5_0.py, so the points come from the written rules.
Data cut-off 23 Nov 2026 (7 Mangsir 2083); share prices 13 Nov 2026. Teaching material, not investment advice.
Corrected 23 Nov 2026 after review: NICA promoter check 4 -> 0 (repeated insider selling); valuation parts counted as estimated.
Second review 23 Nov 2026: EBL capital verified on one date (mid-Oct 2026), so it leaves the estimated count (61 -> 54).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canon_score_reference_v1_5_0 as R

MED_PE, MED_PB = 20.52, 1.535          # 19 listed commercial banks, price 13 Nov 2026
SYS_LOAN_CAGR, CLASS_NPL = 6.54, 5.44  # FY 2077/78 -> 2082/83; industry gross NPL mid-July 2026


def ebl():
    s, notes = {}, {}
    s["roe"] = R.roe_points([13.94, 16.21, 15.10])                       # avg 15.08
    s["car"] = R.car_points(11.78, 11.0, all_components_met=True)        # mid-Oct 2026: CET1 = Tier 1 9.45%, total 11.78% (same date)
    s["earnings"] = R.earnings_quality([1767, 2540, 3362, 3703, 4840, 5070], "lender", writeback_share_max=3.2)
    a = 6                                                                # holding stable (estimated)
    b = 4                                                                # pledging not verified: at most 4
    s["promoter"] = min(a, b)
    s["audit"] = R.AUDIT["emphasis"]                                     # FY 2081/82 report; FY 2082/83 not read
    s["board"] = R.board_points(late_filings=0, independents=1, legal_min=1)
    s["turnover"] = R.turnover_points(24.55e6, 21.51e6, 1.0)
    s["float"] = R.float_points(40.77)
    s["pe"] = R.pe_points(20.26 / MED_PE, roe_ge_median=True, lender_npl_ok=True)
    s["pb"] = R.pb_points(2.92 / MED_PB, roe_ge_median=True, lender_npl_ok=True)
    s["moat"] = 8                                                        # ROE >= sector 4 of 5 (estimated); lowest NPL
    s["concentration"] = 2                                               # not found: at most the lower middle row
    s["loan_growth"] = R.lender_growth_points(13.03, SYS_LOAN_CAGR, 14.55, gross_npl=0.49, class_gross_npl=CLASS_NPL,
                                              adj_npl=None, adj_npl_prev=None, restructured_pct=0.0)
    s["eps"] = R.eps_points([12.26, 17.63, 23.34, 25.70, 33.59, 35.19])
    s["dividends"] = R.dividend_consistency([True] * 5, [18.7, 26.3, 18.5, 36.6, 26.1])
    s["source"] = 2                                                      # no stated reason found: middle row
    unverified_or_estimated = {"promoter": 6, "audit": 5, "board": 4, "float": 5, "valuation": 15,
                               "moat": 8, "concentration": 7, "source": 4}   # valuation: full-year, not trailing, figures
    return s, unverified_or_estimated, dict(problematic=False, capital_below_min=False, restated=False)


def nica():
    s = {}
    s["roe"] = R.roe_points([2.38, -14.03, 0.70])
    s["car"] = R.car_points(11.12, 11.0, all_components_met=False)       # Tier 1 = CET1 6.27% < 8.5% / 7%
    s["earnings"] = R.earnings_quality([3250, 4215, 4445, 700, -3872, 180], "lender", writeback_share_max=0)
    # 51% unchanged, but promoters sold shares with no stated reason in FY 2081/82 and FY 2082/83:
    # "repeated insider selling" (Chapter 64, two of the last three years) -> A = 0; pledging not verified -> B at most 4
    s["promoter"] = min(0, 4)
    s["audit"] = 2                                                       # opinion not read: at most lower middle row
    s["board"] = R.board_points(late_filings=2, independents=1, legal_min=1)   # two late AGMs
    s["turnover"] = R.turnover_points(24.85e6, 15.88e6, 1.0)
    s["float"] = R.float_points(49.0)
    s["pe"] = R.pe_points(280.3 / MED_PE, roe_ge_median=False, lender_npl_ok=False)
    s["pb"] = R.pb_points(1.98 / MED_PB, roe_ge_median=False, lender_npl_ok=False)
    s["moat"] = 5                                                        # rule text: licence without proof (gap reported)
    s["concentration"] = 2
    s["loan_growth"] = R.lender_growth_points(-5.05, SYS_LOAN_CAGR, 3.68, gross_npl=9.26, class_gross_npl=CLASS_NPL)
    s["eps"] = R.eps_points([21.79, 28.25, 29.80, 4.69, -25.96, 1.21])
    s["dividends"] = R.dividend_consistency([False] * 5, [None] * 5)
    s["source"] = 2                                                      # no table row fits exactly: lower of nearest (4, 2)
    unverified_or_estimated = {"promoter": 6, "audit": 5, "float": 5, "valuation": 15, "concentration": 7}
    return s, unverified_or_estimated, dict(problematic=False, capital_below_min=True, restated=True)


DIMS = {1: ("roe", "car", "earnings"), 2: ("promoter", "audit", "board"), 3: ("turnover", "float"),
        4: ("pe", "pb"), 5: ("moat", "concentration"), 6: ("loan_growth", "eps"), 7: ("dividends", "source")}


def report(name, fn):
    s, flagged, lim = fn()
    d = {k: sum(s[x] for x in v) for k, v in DIMS.items()}
    gov = d[2]
    total = R.total_with_limits(d, gov, pledging_pts=s["promoter"], audit_pts=s["audit"],
                                capital_below_min=lim["capital_below_min"])
    bq = d[1] + d[2] + d[5] + d[6] + d[7]
    sa = d[3] + d[4]
    flagged_pts = sum(flagged.values())
    provisional = flagged_pts > 20 or lim["restated"]
    print(f"{name}: " + ", ".join(f"D{k} {v}" for k, v in d.items()))
    print(f"  sub-scores {s}")
    print(f"  Business Quality {bq}/75, Share Attractiveness {sa}/25, Canon Score {total}/100")
    print(f"  unverified + estimated points {flagged_pts} -> provisional {provisional}; capital below minimum {lim['capital_below_min']}")
    print(f"  band {R.band(total)[0]}; position ceiling {R.ceiling(total, bq, sa, provisional)}")
    return total, bq, sa


# ---------------------------------------------------------------- Lesson 64A.11: residual income cross-check
# Recorded, not scored. Value = book value per share + present value of future residual income,
# residual income = (ROE - cost of equity) x opening book value; terminal residual income grows at g for ever.
# ROE paths are a reviewer's assumptions (23 Nov 2026), not this book's forecasts.

def riv(b0, roes, payout, ke, g, terminal_roe):
    b, pv = b0, 0.0
    for t, r in enumerate(roes, 1):
        pv += (r - ke) * b / (1 + ke) ** t
        b *= 1 + r * (1 - payout)
    tv = (terminal_roe - ke) * b / (ke - g) / (1 + ke) ** len(roes)
    return b0 + pv + tv


EBL_PATH = dict(b0=243.01, roes=[.15, .148, .146, .144, .142], payout=.40, terminal_roe=.14)       # mid-Oct 2026 book
NICA_PATH = dict(b0=148.24, roes=[.025, .055, .085, .105, .12], payout=0.0, terminal_roe=.125)     # post-rights book
NICA_TERP = (342 + 0.5 * 100) / 1.5          # 13 Nov 2026 close, one Rs 100 right for every two shares


def implied_ke(path, price, g=.05):
    lo, hi = g + 1e-4, .30
    for _ in range(100):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if riv(ke=m, g=g, **path) > price else (lo, m)
    return m


def riv_report():
    out = {}
    for ke in (.095, .12, .135):
        e, n = riv(ke=ke, g=.05, **EBL_PATH), riv(ke=ke, g=.05, **NICA_PATH)
        out[ke] = (round(e, 1), round(n, 1))
        print(f"  ke {ke:.1%}: EBL value {e:7.1f} (price/value {713 / e:.2f}); NICA value {n:6.1f} (TERP/value {NICA_TERP / n:.2f})")
    print(f"  implied cost of equity: EBL {implied_ke(EBL_PATH, 713):.2%}, NICA {implied_ke(NICA_PATH, NICA_TERP):.2%}")
    for t in (.10, .12, .14):
        p = dict(EBL_PATH, terminal_roe=t)
        print(f"  EBL long-run ROE {t:.0%}: " + ", ".join(f"{k:.1%} -> {riv(ke=k, g=.05, **p):.1f}" for k in (.095, .12, .135)))
    print(f"  NICA post-rights Tier 1 {(14711 + 7458.8) / 234705:.2%}, total CAR {(26042 + 7458.8) / 234705:.2%} (mid-July RWE)")
    return out


if __name__ == "__main__":
    e = report("EBL", ebl)
    n = report("NICA", nica)
    assert e == (74, 57, 17) and n == (33, 19, 14), "scores changed - update the chapter"
    print("Residual income cross-check (Lesson 64A.11):")
    r = riv_report()
    assert round(riv(ke=.12, g=.05, **dict(EBL_PATH, terminal_roe=.10)), 1) == 209.9
    assert r[.12] == (329.8, 130.9) and r[.135] == (265.6, 100.8) and r[.095] == (533.9, 227.9), "RIV changed - update the chapter"
    print("checks pass")
