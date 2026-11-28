#!/usr/bin/env python3
"""Build investors-canon/first-purchase-checklist.html — the complete, interactive
First Purchase checklist. Every item here comes from first-purchase.html; when the
guide changes, change the matching item below and run:
    python3 tools/build-checklist.py
The page shell (header, footer, scripts) is copied from first-purchase.html.
"""
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "investors-canon"
SRC = ROOT / "first-purchase.html"
OUT = ROOT / "first-purchase-checklist.html"
e = lambda s: html.escape(s, quote=False)

# kind: "gate" = failing it ends the study (Reject / Stop); "ev" = evidence gate (Not enough evidence)
# Each item: (id, kind, text, hint)
PART1 = [
 ("a", "Step 1 — Am I ready?", "step-1", "Once, before any company. Redo it if your life changes.", [
  ("a1", "gate", "About six months of household costs are set aside in a bank account or fixed deposit I will not touch.", "Keep more if income is irregular (business, remittance, seasonal work) or many people depend on you."),
  ("a2", "", "If the emergency money is in a fixed deposit, I know the penalty for breaking it early, and a month or two of it is in a savings account I can reach the same day.", ""),
  ("a3", "gate", "I have no loan costing about 12% a year or more (credit card, moneylender, costly personal loan).", "Cheaper loans, such as a home loan well below 12%, are fine if my income covers the instalments safely. The 12% line is the guide's suggestion."),
  ("a4", "gate", "This money will not be needed for at least five years.", "Not money for a wedding, admission fees, a land payment or a trip abroad."),
  ("a5", "gate", "None of it is borrowed, and I will not use a margin loan.", "Margin lenders sell your shares when prices fall, as many Nepali investors learned in 2021–22."),
  ("a6", "", "I accept that shares can stay below what I paid for longer than five years.", "NEPSE fell about 43%, from 3,198.60 (18 Aug 2021) to 1,815.13 (25 Sep 2022)."),
  ("a7", "", "My bank account is open and linked.", ""),
  ("a8", "", "My demat account is open with a depository participant, I have my 16-digit BOID, and my MeroShare login works.", ""),
  ("a9", "", "My broker account is open with a licensed NEPSE broker, and I can log in to its TMS.", ""),
  ("a10", "", "I understand T+2: shares and money change hands two working days after the trade, and I will not plan to sell shares before they appear in MeroShare.", ""),
  ("a11", "", "My share money is split into a steady part (a monthly mutual-fund SIP) and an active part (shares I choose), with at least half in the steady part while I am learning.", "Canon rule, Lesson 59.7."),
  ("a12", "", "I chose the fund after checking what it holds (banks, hydropower), its yearly fees, how much it overlaps with shares I will buy, and how I get out (open-ended buys units back; closed-end must be sold on NEPSE, often below NAV).", "Chapter 16."),
  ("a13", "", "If no suitably diversified fund exists, I keep the steady part in fixed deposits or government savings bonds until one does.", "The guide's suggestion."),
  ("a14", "", "My monthly SIP is running.", ""),
  ("a15", "", "I have written: \"I have Rs ___ for shares: Rs ___ steady, Rs ___ active, and I will not need it for five years.\"", "Step 1 check."),
 ]),
 ("b", "Step 2 — What season is the market in?", "step-2", "Once a quarter. It decides how much of the active part you may use, not which share.", [
  ("b1", "", "I read NRB's latest monthly report, \"Current Macroeconomic and Financial Situation\".", ""),
  ("b2", "", "I applied Chapter 0.3's decision rule: three main signals in a fixed order (bank lending, spare money in banks, interest rates), with other figures as background only, never as votes.", "Section 0.3.7."),
  ("b3", "gate", "Two quarterly checks in a row agree on the phase.", "One reading can mislead. Acting a quarter late on a true signal costs less than acting at once on a false one."),
  ("b4", "", "I set my active part from the phase table: Phase 1 up to 100% (never more); Phase 2 cut to 50%, no new buying, repay margin; Phase 3 rebuild from 50% toward 75%, only scores of 70+ at low prices; Phase 4 rebuild toward 100% in half-steps.", "Canon rule, Lesson 59.7. The steady part keeps buying in every phase."),
  ("b5", "", "Money taken out of the active part in Phase 2 goes to fixed deposits or treasury bills (after comparing rates, tax and lock-in), not to land or a relative's business.", ""),
  ("b6", "", "I wrote the phase and my reason in my notebook before any order: \"The phase is ___; I may put up to Rs ___ into individual shares now.\"", "Step 2 check."),
 ]),
]

PART2 = [
 ("c", "Step 3 — Is it worth studying?", "step-3", "Mostly removing: skip the stalls with rotten vegetables before you compare prices.", [
  ("c1", "gate", "I can say in one simple sentence how this company earns money.", "If not, leave the sector for later. It is not banned, just not for now."),
  ("c2", "gate", "It is listed and trades on NEPSE.", "An IPO is a separate decision (Chapter 77)."),
  ("c3", "gate", "Its average daily turnover over six months is at least Rs 2 lakh.", "Scores: Rs 50 lakh+ = 5; Rs 10–50 lakh = 3; Rs 2–10 lakh = 1; under Rs 2 lakh = 0 and remove."),
  ("c4", "", "I also checked the 20-day average and the median day, so a few frantic days do not mislead me.", ""),
  ("c5", "gate", "My planned holding is no more than about half of one day's 20-day average turnover.", "Chapter 56: sell within 5 trading days at 10% of each day's trading."),
  ("c6", "", "I worked out how many days I would need to sell at normal, half and a quarter of normal turnover, and I could bear the slowest answer.", "Exit days = position ÷ (daily turnover × 10%)."),
  ("c7", "", "I know no turnover formula guarantees an exit: on lower-circuit days sell orders queue and many are never filled. I looked at how it traded on the market's worst days.", "Chapter 58."),
  ("c8", "gate", "It shows no circuit-trap pattern: limit hits day after day on tiny turnover, a small free float, and a rise driven by a rumour rather than results.", ""),
  ("c9", "", "I know the 15% daily limit on each ordinary share (since 20 April 2026) and the market-wide breakers: a 5% index move in the first two hours pauses trading for 15 minutes; 8% stops it for the day.", "Chapters 8 and 10."),
  ("c10", "gate", "No red flag: more than half of promoter shares pledged, or a lender selling pledged shares; an auditor's disclaimer; a fraud or \"problematic institution\" notice; a bank or insurer below its capital requirement.", "Smaller pledges are scored in Step 4, not removed here."),
  ("c11", "", "My shortlist covers 3–4 sectors, and I aim for about four or five shares in the end, not ten banks.", "Companies in one sector often fall together (microfinance 2021–26; the Rasuwa flood of 26 Aug 2026)."),
 ]),
 ("d", "Step 4 — Can I trust the people?", "step-4", "Governance: 15 points in three checks. Check it before you trust the numbers.", [
  ("d1", "", "I read the annual report (board, auditor's opinion, related-party note, promoter list), recent quarterly reports, NEPSE and SEBON notices, NRB notices for a lender, and the news (disputes, court cases, ownership changes).", ""),
  ("d2", "", "Promoter holding over 3 years: stable or rising 6; fell 1 to under 3 points 4; fell 3–5 points 2; fell over 5 points or repeated insider selling 0. I counted only unexplained falls (not mergers, required sales or new issues), and watched for selling after a lock-in ended.", "Check 1, part A."),
  ("d3", "", "Pledged promoter shares ÷ all promoter shares: under 10% 6; 10–25% 4; 25–50% 2; over 50% 0. If I could not find pledge data, I scored no more than 4 and wrote \"pledging not verified\".", "Check 1, part B."),
  ("d4", "", "Check 1 is the lower of the two parts. I also looked at how the promoters' other companies treated small shareholders.", ""),
  ("d5", "", "I read the related-party note: loans to directors' firms, untendered contracts with promoters' firms, purchases from promoters' firms, judged by size and whether the terms were at arm's length.", ""),
  ("d6", "", "I scored the audit opinion: clean, small disclosed related-party deals 5; emphasis of matter 4; restated year or large disclosed related-party deals 3; qualified on a limited explained matter 2; qualified on loans, provisions or related-party deals, a scope limit or going-concern doubt 1; adverse, disclaimer or undisclosed related-party deals 0.", "Check 2."),
  ("d7", "", "I compared the first, unaudited yearly profit with the audited figure, and noted whether revisions keep going the same way.", "Nabil's FY 2081/82 profit fell from Rs 7.13 arba to Rs 5.92 arba at audit (Chapter 83)."),
  ("d8", "", "Quarterly reports and the AGM were on time for 3 years; I noted any late filing or SEBON or NEPSE disclosure penalty.", ""),
  ("d9", "", "Independent directors: how many compared with the law's minimum, whether they attend at least three-quarters of meetings, and whether one sits on the audit committee. Scored 4/3/2/1/0.", "Check 3."),
  ("d10", "gate", "No governance hard rule fires: Check 1 is above 0, Check 2 is above 1, and the governance total is at least 5 of 15.", "If one fires, the whole score is capped at 54: no new money."),
  ("d11", "", "I wrote the governance score out of 15, with one line of reasons for each check.", "Step 4 check."),
 ]),
 ("e", "Step 5 — Are the numbers healthy?", "step-5", "Financial Strength: 20 points in three parts.", [
  ("e1", "", "ROE: three-year average, each year as profit ÷ average of opening and closing equity. 15%+ with no year below 10% = 8; 10–15% = 6; 7–10% = 4; under 7% or any loss = 1.", "Part A."),
  ("e2", "", "I compared ROE with the cost of equity (low-to-mid teens in Nepal; the book uses 12% for banks, 14.5% for hydropower), not with the deposit rate, and did not count high ROE from heavy borrowing or thin provisions as quality.", ""),
  ("e3", "", "I used the right cushion test. Bank: CAR in all three layers (11% total, 8.5% Tier 1, 7% common equity); 13%+ = 7, 11.5–13% = 5, 11–11.5% = 3. Microfinance: CAR against 8%. Insurer: solvency ratio on NIA's ladder (200%+ = 7, 130–200% = 5, 100–130% = 3). Others: debt-to-equity (3 points) plus interest cover (4 points), counting capitalised interest.", "Part B."),
  ("e4", "", "For a bank: no quarter-end below the requirement in the last 3 years (otherwise at most 3 points). If I found only the total CAR, I marked the capital part unverified.", ""),
  ("e5", "", "For an insurer: if the report gives two ratios (with and without transitional provisions), I used the lower. I noted that below 130% NIA restricts cash dividends.", "NIA Risk Based Capital and Solvency Directive 2026."),
  ("e6", "", "For hydropower: I wrote down the DSCR (cash available for lenders ÷ principal and interest due).", ""),
  ("e7", "gate", "No financial hard limit: a lender's capital is not below its minimum in any layer, an insurer's solvency is at least 100%, there is no NRB \"problematic\" status and no fraud.", "Any one caps the score at 54."),
  ("e8", "", "Profit record over six years (five comparisons): no loss and grew in 4+ = 5; no loss, flat or falling in exactly 2 = 3; flat or falling in 3+, or one loss = 2; two or more losses or erratic = 1.", "Part C."),
  ("e9", "", "Profit check, minus 1 if it fails: non-financial — 3-year operating cash flow at least half of 3-year profit; lender — no year with over a quarter of profit from write-backs or one-off gains; insurer — no year with over a quarter from realised investment gains or released reserves.", ""),
  ("e10", "", "I watched for profit up but cash down, one-off gains, and the bonus-share illusion (compare total profit, not just EPS).", ""),
  ("e11", "", "Sector notes written (they change no points): bank NPL against its class, naming the series, and CD ratio against NRB's 90% ceiling; hydropower production stage, same-quarter comparison, royalty step-up after 15 years, single-river risk; insurer profit from investments versus insurance.", ""),
  ("e12", "", "I wrote the financial strength score out of 20.", "Step 5 check."),
 ]),
 ("f", "Step 6 — Is it a good business?", "step-6", "Business Quality (75) and Liquidity (10).", [
  ("f1", "", "Moat: 8 only with proof (ROE at or above the sector median in 4 of 5 years; a lender also NPL at or below its class average; hydropower at least 90% of contracted energy in 2 of 3 years and 10+ years left on its PPAs); licence or regulated position without proof 5; low barriers 2; structural threat 0.", "A licence is not a moat."),
  ("f2", "", "Concentration: largest single exposure (customer, product, region, supplier; for a lender, its biggest loan sector or region) 20% or less 7; to 40% 4; to 60% 2; over 60% 0. Hydropower selling to NEA alone scores 0; an insurer's is unverified and capped at 2.", ""),
  ("f3", "", "Growth: a bank's five-year loan CAGR compared with the system's (within 5 points 8; 5–10 points 5; over 10 points or shrinking 2), then the credit-peak, loans-versus-deposits and rising-NPL adjustments. Others: five-year revenue CAGR (15%+ 8; 8–15% 6; 0–8% 3; shrinking 0). I noted any merger.", ""),
  ("f4", "", "EPS on the same share count (adjusted for bonus and rights): rose in 4+ of 5 with no big swing 7; 3 of 5 4; 2 of 5 or very volatile 2; fewer, or negative in 3+ years 0.", ""),
  ("f5", "", "Dividends: only real cash counts (a token cash part that pays the bonus tax is a bonus year); payout = cash ÷ distributable profit. Record 6/4/2/0; source and reason 4/2/0. A 30–70% payout is a Canon preference, not a rule.", ""),
  ("f6", "", "Liquidity: turnover points (5/3/1/0) plus free float (40%+ 5; 25–40% 3; 10–25% 1; under 10% 0).", ""),
  ("f7", "", "I wrote Business Quality out of 75 and Liquidity out of 10, and I can point to the table row behind every number.", "Step 6 check."),
  ("f8", "", "Evidence grade: I listed each of the sixteen parts that rests on unavailable, unverified or estimated figures, counted each part's full points once, and wrote the grade (A none; B 1–10; C 11–20; D over 20).", ""),
  ("f9", "ev", "No more than 20 points rest on unverified figures, and I could test every gate.", "If not, the answer is \"Not enough evidence\", or at least a provisional score with a ceiling one band lower."),
  ("f10", "", "For hydropower and insurers I compared only with the same sector, and I remember that some points share the same evidence.", ""),
 ]),
 ("g", "Step 7 — Is today's price sensible?", "step-7", "Valuation: 15 points, which completes the Canon Score.", [
  ("g1", "", "Peer group by business model (operating hydropower apart from projects being built; life apart from non-life; commercial banks apart from development banks and finance companies; microfinance on its own), on one price date, with the latest four quarters of profit and at least five peers.", "Fewer than five peers: mark unverified and score in the \"in line\" row."),
  ("g2", "", "P/E ratio ÷ sector median, unrounded: 0.8 or less 8 (if earned); to 1.1 6; to 1.5 3; over 1.5 1; loss 0. A hydropower plant not yet producing: P/E not applicable.", ""),
  ("g3", "", "P/B ratio ÷ sector median: 0.8 or less 7 (if earned); to 1.1 5; to 1.5 3; over 1.5 1; zero or negative book 0.", ""),
  ("g4", "", "If it looks cheap, the discount is earned: ROE at or above the sector median and, for a bank, NPL at or below its class figure. Otherwise I scored the \"in line\" row.", ""),
  ("g5", "", "Beside each ratio I wrote the price and its date, the earnings period, the book-value period and the source of each figure.", ""),
  ("g6", "", "I asked the four questions: will today's profits last? Is ROE above the cost of equity? What growth does the price assume? What could permanently cut what it earns?", ""),
  ("g7", "", "Plain-number check: the sector itself is not so expensive that \"cheap for the sector\" is still dear.", ""),
  ("g8", "", "For a bank: justified P/B = (ROE − g) ÷ (cost of equity − g), compared with the actual P/B.", ""),
  ("g9", "", "Price versus value: today's price does not need heroic growth (reverse DCF, or justified P/B). If I built a DCF, I used FCFE, a finite life for hydropower, a range rather than one number, and a margin of safety.", "Not scored; it should change your Step 8 decision."),
  ("g10", "", "Total = Business Quality + Share Attractiveness, with any cap applied after adding; band found; and I checked the ceiling rules (Business Quality under 38 or Share Attractiveness under 13 with a total of 70+, or a provisional score, takes the ceiling of the band below, one band at most).", ""),
  ("g11", "gate", "The total, after any cap, is 55 or more.", "55+ makes it eligible for new money. It is never an instruction to buy."),
 ]),
 ("h", "Step 8, part A — How much?", "step-8", "The most you may hold is the smallest of three limits. You may buy less.", [
  ("h1", "", "Limit 1, the band's ceiling, as a share of my whole share money (steady plus active): Exceptional 6–8% (8% is the absolute maximum); Strong 4–6%; Adequate 1.5–3%; Watch list and Avoid nothing new.", "Chapter 66."),
  ("h2", "", "Limit 2, liquidity: no more than about half of one day's average turnover.", "Chapter 56."),
  ("h3", "", "Limit 3, sector: no more than about 25–30% in one sector, counting my mutual fund's holdings (look-through) and company-by-company overlap.", "Chapters 60, 61 and 66."),
  ("h4", "", "My amount is no more than the smallest of the three, and less if the price is only fair, the company is new to me, or it would be hard to sell. More debt, thinner trading or more overlap means a smaller amount.", ""),
  ("h5", "", "It fits within what the season allows me to use from the active part (Step 2).", ""),
  ("h6", "", "I worked out the round-trip cost: commission (0.36% up to Rs 50,000, minimum Rs 10; lower for larger trades), SEBON fee 0.015% each way, DP charge about Rs 25 per company per selling day, and capital gains tax (3.75% if held over 365 days, 5% otherwise, for resident individuals). It is a small share of the amount.", "Rates as of November 2026; check your broker's schedule."),
  ("h7", "", "If the amount is large enough, I will buy in two or three parts, and I wrote what allows the later parts (a better price, or results that confirm my reason).", ""),
 ]),
 ("i", "Step 8, part B — When will I sell?", "step-8", "Write it before you buy, while you are calm.", [
  ("i1", "", "Why I am buying, in one or two lines.", ""),
  ("i2", "", "What would prove me wrong: specific signs I can check.", ""),
  ("i3", "", "What I will do then: sell, reduce, or hold without adding.", ""),
  ("i4", "", "I know the seven reasons to sell or reduce: reason proven wrong; governance worse; business weaker (score 45–54 stop adding, below 45 a candidate to sell); price far ahead of value; hard to sell; one share over 8% or a sector over 25–30%; my own needs change.", ""),
  ("i5", "", "I know a 10–15% fall alone is not proof I was wrong, and a 30% rise alone is not a reason to sell.", ""),
  ("i6", "", "My next re-score date (after the next quarterly results) is in my calendar, and I will re-score at once after fraud news, an NRB or SEBON action, an audit qualification, a lender selling pledged shares, a disaster at a plant, or a large rights issue.", ""),
  ("i7", "", "I will never add to a company whose score is falling just because it is cheaper, and I will cut the active part to about half if two checks agree on Phase 2.", ""),
  ("i8", "", "I noted known future dates (royalty step-up, tax holiday ending, lock-in expiry, PPA end).", ""),
 ]),
 ("j", "Placing the order", "step-8", "Only after the answer is Buy.", [
  ("j1", "", "My answer is written (Buy, Wait, Reject or Not enough evidence), and the decision record below is filled in.", ""),
  ("j2", "", "In TMS I checked the company's symbol carefully (similar names exist).", ""),
  ("j3", "", "The share is trading normally today and is not rushing toward its 15% upper limit.", ""),
  ("j4", "", "I entered the quantity and a limit price, and read the total value and charges before pressing buy.", ""),
  ("j5", "", "The order was actually filled, not just placed.", ""),
  ("j6", "", "I paid on time for settlement.", ""),
  ("j7", "", "After T+2 the shares appear in MeroShare, and I know I must approve EDIS when I sell.", ""),
  ("j8", "", "My notebook has the date, the price paid, the scores, and my three written lines.", ""),
 ]),
]

RECORD = ["Company and symbol", "Price and its date", "Business Quality + Share Attractiveness = total; band; evidence grade",
          "Value range (or justified P/B) and margin of safety", "Answer: Buy / Wait / Reject / Not enough evidence",
          "Amount, and which limit binds", "Main reason to buy", "Main way this could fail", "What would prove me wrong", "Review date"]


def section(sec, part):
    sid, title, anchor, intro, items = sec
    lis = []
    for iid, kind, text, hint in items:
        cls = "fpc-item" + (" is-gate" if kind == "gate" else " is-ev" if kind == "ev" else "")
        tag = ('<span class="fpc-tag fpc-tag-gate">Gate</span> ' if kind == "gate" else
               '<span class="fpc-tag fpc-tag-ev">Evidence gate</span> ' if kind == "ev" else "")
        h = f'\n        <span class="fpc-hint">{e(hint)}</span>' if hint else ""
        lis.append(f'''    <li class="{cls}" data-id="{iid}" data-kind="{kind}">
      <label><input type="checkbox" data-id="{iid}"> <span class="fpc-body">{tag}<span class="fpc-text">{e(text)}</span>{h}</span></label>
    </li>''')
    return f'''  <section class="fpc-sec" id="sec-{sid}" data-part="{part}">
    <h3><span class="fpc-sec-title">{e(title)}</span> <span class="fpc-sec-count" aria-live="polite"></span></h3>
    <p class="fpc-sec-intro">{e(intro)} <a href="first-purchase.html#{anchor}">Read this step in the guide</a></p>
    <ol class="fpc-list">
{chr(10).join(lis)}
    </ol>
  </section>'''


def main():
    n_items = sum(len(s[4]) for s in PART1 + PART2)
    n_gates = sum(1 for s in PART1 + PART2 for i in s[4] if i[1] in ("gate", "ev"))
    rec = "\n".join(f'      <tr><th scope="row">{e(r)}</th><td><textarea rows="2" data-rec="{i}" aria-label="{e(r)}"></textarea></td></tr>'
                    for i, r in enumerate(RECORD))
    article = f'''<article class="chapter fpc-page">
  <div class="chapter-kicker">Nepal Edition · Practical Guide</div>
  <h1>The Complete First Purchase Checklist</h1>
  <p class="fpc-lead">Every check in <a href="first-purchase.html">Your First Share Purchase</a>, in order, with nothing left out: {n_items} checks across eight steps, plus a score-and-size calculator and a decision record. Tick as you go; your ticks are saved in this browser for each company you study.</p>

  <div class="fpc-legend">
    <p><span class="fpc-tag fpc-tag-gate">Gate</span> Failing a gate ends the study, however good the rest looks. Part 1 gates mean <strong>stop and fix it first</strong>; company gates mean <strong>Reject</strong>.</p>
    <p><span class="fpc-tag fpc-tag-ev">Evidence gate</span> Failing it means <strong>Not enough evidence</strong>: do not buy until the figures can be checked.</p>
    <p>Four possible answers for every company: <strong>Buy</strong>, <strong>Wait</strong>, <strong>Reject</strong>, <strong>Not enough evidence</strong>. Deciding not to buy is a valid decision.</p>
  </div>

  <div class="fpc-bar" hidden>
    <div class="fpc-bar-row">
      <label for="fpc-company">Company</label>
      <input id="fpc-company" type="text" placeholder="Type a company name or symbol" autocomplete="off" list="fpc-saved">
      <datalist id="fpc-saved"></datalist>
      <button type="button" class="fpc-btn" data-act="new">New company</button>
      <button type="button" class="fpc-btn" data-act="reset">Clear this company</button>
      <button type="button" class="fpc-btn fpc-btn-main" data-act="print">Print or save as PDF</button>
    </div>
    <div class="fpc-progress" aria-hidden="true"><span></span></div>
    <p class="fpc-status" aria-live="polite"></p>
  </div>

  <h2 id="part-1">Part 1 — About you</h2>
  <p>Do this once, and redo it when your life or the season changes. It is the same for every company.</p>
{chr(10).join(section(s, 1) for s in PART1)}

  <h2 id="part-2">Part 2 — About each company</h2>
  <p>Do this for every company you study. Type its name in the box above so its ticks are kept separately.</p>
{chr(10).join(section(s, 2) for s in PART2)}

  <h2 id="calculator">Score and size calculator</h2>
  <p>Enter the points you scored in each dimension. The calculator applies Chapter 64's caps and Chapter 66's ceilings. It does arithmetic only: the judgement in each score is still yours. <strong>To score from the company's raw figures instead</strong> (ROE, CAR, NPL, prices, promoter holdings and so on), use the <a href="canon-score-engine.html">Canon Score Engine</a>: it works out all sixteen parts for you and shows how every point was reached.</p>
  <div class="fpc-calc">
    <fieldset>
      <legend>Business Quality (75)</legend>
      <label>Financial strength <span>of 20</span><input type="number" min="0" max="20" step="1" data-calc="fin"></label>
      <label>Governance <span>of 15</span><input type="number" min="0" max="15" step="1" data-calc="gov"></label>
      <label>Durability <span>of 15</span><input type="number" min="0" max="15" step="1" data-calc="dur"></label>
      <label>Growth <span>of 15</span><input type="number" min="0" max="15" step="1" data-calc="gro"></label>
      <label>Dividends <span>of 10</span><input type="number" min="0" max="10" step="1" data-calc="div"></label>
    </fieldset>
    <fieldset>
      <legend>Share Attractiveness (25)</legend>
      <label>Liquidity <span>of 10</span><input type="number" min="0" max="10" step="1" data-calc="liq"></label>
      <label>Valuation <span>of 15</span><input type="number" min="0" max="15" step="1" data-calc="val"></label>
      <label>Unverified or estimated parts <span>full points</span><input type="number" min="0" max="100" step="1" data-calc="unv"></label>
      <label class="fpc-check"><input type="checkbox" data-calc="cap"> A hard rule fires (cap at 54)</label>
    </fieldset>
    <fieldset>
      <legend>Your money and the market</legend>
      <label>Whole share money <span>Rs</span><input type="number" min="0" step="1000" data-calc="money"></label>
      <label>Active part you may use now <span>Rs</span><input type="number" min="0" step="1000" data-calc="active"></label>
      <label>20-day average daily turnover <span>Rs</span><input type="number" min="0" step="10000" data-calc="adv"></label>
      <label>Already in this sector, counting funds <span>Rs</span><input type="number" min="0" step="1000" data-calc="sector"></label>
      <label>Sector ceiling <span>%</span><input type="number" min="0" max="100" step="1" data-calc="secpct" placeholder="25"></label>
    </fieldset>
    <output class="fpc-result" aria-live="polite"><p>Enter the seven scores to see the total, band and ceilings.</p></output>
  </div>

  <h2 id="record">Decision record</h2>
  <p>Fill one in for each company. If you cannot fill it in, you are not ready to place the order.</p>
  <div class="fpc-answer" aria-live="polite"></div>
  <div style="overflow-x:auto;">
  <table class="figures fpc-record">
    <tbody>
{rec}
    </tbody>
  </table>
  </div>

  <p class="fpc-note">This checklist follows <a href="first-purchase.html">Your First Share Purchase</a> and the Canon Score rubric 1.6.0 (<a href="chapters/ch-64-seven-dimension-score.html">Chapter 64</a>, <a href="chapters/ch-66-using-canon-score-portfolio.html">Chapter 66</a>). Rates and rules were checked on 28 November 2026; check the latest NEPSE, SEBON, CDSC, NRB and NIA notices before you act. It is education, not advice to buy or sell any share. For sector-by-sector versions, see <a href="chapters/ch-101-pre-buy-checklists.html">Chapter 101, Pre-Buy Checklists</a>.</p>

  <div class="chapter-nav">
    <a href="first-purchase.html">← Your First Share Purchase</a>
    <a href="glossary.html">Glossary of Terms →</a>
  </div>
</article>'''

    t = SRC.read_text(encoding="utf-8")
    title = "The Complete First Purchase Checklist"
    desc = (f"An interactive, printable checklist of all {n_items} checks in the First Purchase guide, step by step, "
            "with gates, a Canon Score and position-size calculator, and a decision record for each NEPSE company.")
    old_title = re.search(r"<title>(.*?)</title>", t).group(1)
    t = t.replace(old_title, html.escape(title, quote=False) + " — The Investor&#x27;s Canon")
    t = t.replace("Your First Share Purchase: An 8-Step Guide — The Investor's Canon", title + " — The Investor's Canon")
    od = re.search(r'<meta name="description" content="([^"]*)"', t).group(1)
    t = t.replace(od, html.escape(desc, quote=True))
    t = t.replace("investors-canon/first-purchase.html", "investors-canon/first-purchase-checklist.html")
    a = t.index('<article class="chapter'); b = t.index("</article>", a) + len("</article>")
    t = t[:a] + article + t[b:]
    if "css/checklist.css" not in t:
        t = re.sub(r'(<link rel="stylesheet" href="css/style\.css[^>]*>)', r'\1\n<link rel="stylesheet" href="css/checklist.css?v=1">', t, count=1)
    if "js/checklist.js" not in t:
        t = t.replace('<script src="js/audio-reader.js" defer></script>',
                      '<script src="js/checklist.js?v=1" defer></script>\n<script src="js/audio-reader.js" defer></script>', 1)
    OUT.write_text(t, encoding="utf-8")
    print(f"first-purchase-checklist.html: {n_items} checks, {n_gates} gates")


if __name__ == "__main__":
    main()
