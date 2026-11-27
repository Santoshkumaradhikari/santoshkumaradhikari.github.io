"""Cycle-settings test (Chapter 80, Lesson 80.8), exactly as regime-test-rules-2026-11-17.txt. Run: python3 regime_test_2015_2026.py"""
import csv, sys
from pathlib import Path

HERE = Path(__file__).parent
rows = sorted(csv.DictReader(open(HERE / "regime-test-data-2015-2026.csv")), key=lambda r: r["month"])

# mid-July NPL ratio (commercial banks / NRB Macroeconomic Indicators Table 18). 2014 derived from the 2015 report.
NPL = {2014: 2.9, 2015: 2.57, 2016: 1.74, 2017: 1.70, 2018: 1.6, 2019: 1.5, 2020: 1.9, 2021: 1.5,
       2022: 1.3, 2023: 3.0, 2024: 3.9, 2025: 4.6, 2026: 5.7}

def corridor_mid(month, ib):
    """Midpoint of NRB's interest-rate corridor in force in that month. None = no corridor (use 5%)."""
    y, m = int(month[:4]), int(month[5:7])
    fy = y if m >= 8 else y - 1          # FY starts mid-July; Oct/Jan/Apr readings: fy = start year; Jul = previous
    if month.endswith("-07"):
        fy = y - 1
    if fy < 2016:
        return None
    if fy == 2016:   return (7.0 + (ib - 0.10)) / 2     # floor floated at interbank - 0.10 in 2016/17
    if fy in (2017, 2018): return 5.0                  # 7/3 then 6.5/3.5: midpoint 5 either way
    if fy == 2019:   return 4.5                        # 6 / 3
    if fy == 2020:   return 3.0                        # 5 / 1
    if fy == 2021:   return 3.5 if month < "2022-02" else 5.5   # 5/2, then 7/4 from 23 Feb 2022
    if fy == 2022:   return 7.0                        # 8.5 / 5.5
    if fy == 2023:   return 6.0 if month < "2023-09" else 5.0   # 7.5/4.5, later 7/3
    if fy == 2024:   return 4.75                       # 6.5 / 3
    if fy == 2025:   return 4.375                      # 6 / 2.75
    raise ValueError(month)

def npl_latest(month):
    y, m = int(month[:4]), int(month[5:7])
    return y if m >= 7 else y - 1          # mid-July figure of that year counts from the July reading on

def phase(r):
    ib = float(r["ib"]); cg = float(r["cg"])
    mid = corridor_mid(r["month"], ib)
    if (ib >= 5.0) if mid is None else (ib > mid):
        return 2
    if cg >= 15:
        return 1
    y = npl_latest(r["month"])
    if NPL[y] - NPL[y - 1] >= 0.2:
        return 3
    return 4

CAP = {1: 1.0, 2: 0.5, 3: 0.75, 4: 1.0}

def run(div=0.0, over_cap="cut", lag=1, confirm=2):
    readings = [phase(r) for r in rows]
    cur, act = 1, {}
    for i in range(len(rows)):
        if i >= confirm - 1 and all(readings[i - k] == readings[i] for k in range(confirm)) and readings[i] != cur:
            cur = readings[i]
            act[i + lag] = cur
    ph, w, v, bh, out = 1, 1.0, 1.0, 1.0, []
    for i, r in enumerate(rows):
        if i in act:
            ph = act[i]
            if ph == 1: w = 1.0
            elif ph == 2: w = min(w, 0.5)
            elif w > CAP[ph] and over_cap == "cut": w = CAP[ph]
        elif ph in (3, 4) and w < CAP[ph]:
            w = min(CAP[ph], w + 0.125)
        out.append(dict(month=r["month"], reading=readings[i], phase=ph, w=w, v=v, bh=bh, nepse=float(r["nepse"])))
        if i + 1 < len(rows):
            eq = float(rows[i + 1]["nepse"]) / float(r["nepse"]) - 1 + div / 4
            cash = float(r["tb"]) / 400
            v *= 1 + w * eq + (1 - w) * cash
            bh *= 1 + eq
    return out

def dd(series):
    peak, worst = series[0], 0
    for x in series:
        peak = max(peak, x); worst = min(worst, x / peak - 1)
    return worst

def window(out, a, b, key):
    s = {o["month"]: o[key] for o in out}
    return s[b] / s[a] - 1

if __name__ == "__main__":
    out = run()
    print("month    read phase  w     cycle   b&h    NEPSE")
    for o in out:
        print(f"{o['month']}  {o['reading']}    {o['phase']}   {o['w']:.3f}  {o['v']:.3f}  {o['bh']:.3f}  {o['nepse']:7.1f}")
    n_years = (len(out) - 1) / 4
    for label, kw in [("main (price only)", {}), ("+2%/yr dividends", {"div": 0.02}),
                      ("Phase 3 does not cut from 100%", {"over_cap": "hold"}),
                      ("act in the same quarter (no lag)", {"lag": 0}),
                      ("one reading is enough", {"confirm": 1})]:
        o = run(**kw)
        cy, bh = o[-1]["v"], o[-1]["bh"]
        print(f"\n{label}: final cycle {cy:.3f} ({(cy**(1/n_years)-1)*100:+.1f}%/yr)  b&h {bh:.3f} "
              f"({(bh**(1/n_years)-1)*100:+.1f}%/yr)  worst fall cycle {dd([x['v'] for x in o])*100:.1f}%  "
              f"b&h {dd([x['bh'] for x in o])*100:.1f}%")
        for a, b in [("2016-07", "2018-07"), ("2021-07", "2022-10"), ("2022-10", "2026-07")]:
            print(f"   {a}->{b}: cycle {window(o, a, b, 'v')*100:+.1f}%  b&h {window(o, a, b, 'bh')*100:+.1f}%")
