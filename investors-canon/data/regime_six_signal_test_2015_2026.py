"""Six-signal (five testable) regime vote, Chapter 80 Lesson 80.8. Rules: regime-six-signal-rules-2026-11-27.txt. Run: python3 regime_six_signal_test_2015_2026.py"""
import regime_test_2015_2026 as sim
rows = sim.rows
ORDER = [2, 1, 3, 4]
def votes(i):
    r = rows[i]; cg = float(r["cg"]); dg = float(r["dg"]); ib = float(r["ib"])
    sets = []
    if cg >= 15: sets.append({1})
    elif i >= 4:
        d = cg - float(rows[i-4]["cg"])
        sets.append({4} if d >= 1 else {2, 3} if d <= -1 else {3, 4})
    sets.append({1, 4} if dg >= 15 else {3, 4} if dg >= 10 else {2})
    mid = sim.corridor_mid(r["month"], ib); mid = 5.0 if mid is None else mid
    sets.append({2} if ib > mid else {1, 4} if ib <= mid - 1.5 else {3})
    y = sim.npl_latest(r["month"])
    sets.append({2, 3} if sim.NPL[y] - sim.NPL[y-1] >= 0.2 else {1, 4})
    if i >= 4:
        ch = float(r["nepse"]) / float(rows[i-4]["nepse"]) - 1
        sets.append({1, 4} if ch >= 0.10 else {2, 3} if ch <= -0.10 else {3, 4})
    return sets
def make_phase(tie="order"):
    prev = {"p": 1}
    def ph_i(i):
        sets = votes(i); cnt = {p: sum(p in s for s in sets) for p in (1, 2, 3, 4)}
        top = max(cnt.values()); best = [p for p in ORDER if cnt[p] == top]
        p = best[0] if (tie == "order" or len(best) == 1 or prev["p"] not in best) else prev["p"]
        prev["p"] = p; return p
    return ph_i
def run_six(tie="order", **kw):
    f = make_phase(tie); readings = [f(i) for i in range(len(rows))]
    it = iter(readings); old = sim.phase
    sim.phase = lambda r: next(it)
    try: return sim.run(**kw), readings
    finally: sim.phase = old
def summary(label, o):
    n = (len(o) - 1) / 4; cy, bh = o[-1]["v"], o[-1]["bh"]
    print(f"{label}: final {cy:.3f} ({(cy**(1/n)-1)*100:+.1f}%/yr)  b&h {bh:.3f} ({(bh**(1/n)-1)*100:+.1f}%/yr)  "
          f"worst fall {sim.dd([x['v'] for x in o])*100:.1f}% (b&h {sim.dd([x['bh'] for x in o])*100:.1f}%)")
    for a, b in [("2016-07", "2018-07"), ("2021-07", "2022-10"), ("2022-10", "2026-07")]:
        print(f"   {a}->{b}: {sim.window(o, a, b, 'v')*100:+.1f}%  b&h {sim.window(o, a, b, 'bh')*100:+.1f}%")
if __name__ == "__main__":
    o, rd = run_six()
    print("month    3-sig 6-sig acted  w")
    for i, x in enumerate(o): print(f"{x['month']}  {sim.phase(rows[i])}     {rd[i]}     {x['phase']}    {x['w']:.3f}")
    summary("three-signal rule (Lesson 80.8)", sim.run())
    summary("six-signal vote (5 testable)", o)
    summary("six-signal vote, ties keep previous", run_six(tie="keep")[0])
    summary("six-signal vote, +2%/yr dividends", run_six(div=0.02)[0])
    summary("six-signal vote, one reading enough", run_six(confirm=1)[0])
