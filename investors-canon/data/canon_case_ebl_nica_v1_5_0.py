"""The Investor's Canon - case study: Everest Bank (EBL) and NIC Asia Bank (NICA) under rubric 1.5.0.

Every input below is listed, with its source and status, in canon-case-ebl-nica-v1.5.0.csv (same folder).
Run:  python3 canon_case_ebl_nica_v1_5_0.py
It uses the reference functions in canon_score_reference_v1_5_0.py, so the points come from the written rules.
Data cut-off 23 Nov 2026 (7 Mangsir 2083); share prices 13 Nov 2026. Teaching material, not investment advice.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canon_score_reference_v1_5_0 as R

MED_PE, MED_PB = 20.52, 1.535          # 19 listed commercial banks, price 13 Nov 2026
SYS_LOAN_CAGR, CLASS_NPL = 6.54, 5.44  # FY 2077/78 -> 2082/83; industry gross NPL mid-July 2026


def ebl():
    s, notes = {}, {}
    s["roe"] = R.roe_points([13.94, 16.21, 15.10])                       # avg 15.08
    s["car"] = R.car_points(11.78, 11.0, all_components_met=True)        # Tier 1 9.98% at Q4; Q1 Tier 1 not read
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
    unverified_or_estimated = {"car": 7, "promoter": 6, "audit": 5, "board": 4, "float": 5,
                               "moat": 8, "concentration": 7, "source": 4}
    return s, unverified_or_estimated, dict(problematic=False, capital_below_min=False, restated=False)


def nica():
    s = {}
    s["roe"] = R.roe_points([2.38, -14.03, 0.70])
    s["car"] = R.car_points(11.12, 11.0, all_components_met=False)       # Tier 1 = CET1 6.27% < 8.5% / 7%
    s["earnings"] = R.earnings_quality([3250, 4215, 4445, 700, -3872, 180], "lender", writeback_share_max=0)
    s["promoter"] = min(6, 4)                                            # 51% unchanged (estimated); pledging not verified
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
    unverified_or_estimated = {"promoter": 6, "audit": 5, "float": 5, "concentration": 7}
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


if __name__ == "__main__":
    e = report("EBL", ebl)
    n = report("NICA", nica)
    assert e == (74, 57, 17) and n == (37, 23, 14), "scores changed - update the chapter"
    print("checks pass")
