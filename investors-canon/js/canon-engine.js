/* The Investor's Canon — Canon Score engine, rubric 1.6.0 (Chapter 64).
   A line-by-line JavaScript port of data/canon_score_reference_v1_6_0.py.
   Every function takes one object of named inputs, exactly like the Python keyword
   arguments, so the published test cases (data/canon-score-test-cases-v1.6.0.json)
   run unchanged: `node tools/test-canon-engine.js`.
   scoreCompany() then combines the sixteen parts, the hard limits, the
   missing-data rule and the evidence grade, and records how every point was reached.
   Teaching tool, not investment advice. */
(function (root) {
  'use strict';

  /* ---------------------------------------------------------------- helpers */
  function comparisons(series) {
    if (!series || series.length !== 6) { throw new Error('need six annual figures'); }
    var out = [];
    for (var i = 0; i < 5; i++) { out.push([series[i], series[i + 1]]); }
    return out;
  }
  function bigSwing(prev, cur) {
    if ((prev < 0) !== (cur < 0)) { return true; }
    if (prev === 0) { return cur !== 0; }
    return Math.abs(cur - prev) / Math.abs(prev) > 0.5;
  }
  function nBigSwings(series, ignoreLossTransitions) {
    var n = 0;
    comparisons(series).forEach(function (p) {
      if (ignoreLossTransitions && ((p[0] < 0) !== (p[1] < 0))) { return; }
      if (bigSwing(p[0], p[1])) { n++; }
    });
    return n;
  }
  function count(arr, fn) { var n = 0; for (var i = 0; i < arr.length; i++) { if (fn(arr[i], i)) { n++; } } return n; }
  function dflt(v, d) { return v === undefined ? d : v; }

  /* ---------------------------------------------------------------- Dimension 1 */
  function roe_points(o) {
    var roes = o.roes;
    if (o.equity_nonpositive || roes.some(function (r) { return r < 0; })) { return 1; }
    var avg = (roes[0] + roes[1] + roes[2]) / 3;
    if (avg >= 15) { return Math.min.apply(null, roes) >= 10 ? 8 : 6; }
    if (avg >= 10) { return 6; }
    if (avg >= 7) { return 4; }
    return 1;
  }
  function car_points(o) {
    var all = dflt(o.all_components_met, true);
    if (o.car < o.minimum || !all) { return 0; }
    var gap = o.car - o.minimum;
    var pts = gap >= 2.0 ? 7 : gap >= 0.5 ? 5 : 3;
    return o.breach_in_last_3y ? Math.min(pts, 3) : pts;
  }
  function insurer_ratio_to_score(o) {
    if (o.without_transitional_pct === undefined || o.without_transitional_pct === null) { return o.reported_pct; }
    return Math.min(o.reported_pct, o.without_transitional_pct);
  }
  function insurer_points(o) {
    var s = o.solvency_pct;
    return s >= 200 ? 7 : s >= 130 ? 5 : s >= 100 ? 3 : 0;
  }
  function de_points(o) {
    if (o.equity_nonpositive) { return 0; }
    var d = o.de;
    return d < 1.0 ? 3 : d < 2.0 ? 2 : d < 3.0 ? 1 : 0;
  }
  function cover_points(o) {
    if (o.operating_loss) { return 0; }
    if (o.no_interest_bearing_debt) { return 4; }
    var c = o.cover;
    return c >= 5 ? 4 : c >= 3 ? 3 : c >= 1.5 ? 1 : 0;
  }
  function earnings_quality(o) {
    var profits = o.profits, sector = dflt(o.sector, 'other');
    var recent = profits.slice(1);
    var losses = count(recent, function (p) { return p < 0; });
    var grew = count(comparisons(profits), function (p) { return p[1] > p[0]; });
    var notGrew = 5 - grew;
    var swings = nBigSwings(profits, true);
    var pts;
    if (losses >= 2 || swings >= 2) { pts = 1; }
    else if (losses === 1) { pts = 2; }
    else if (grew >= 4) { pts = 5; }
    else if (notGrew === 2) { pts = 3; }
    else { pts = 2; }
    var deduct = 0;
    var last3 = profits[3] + profits[4] + profits[5];
    if (sector === 'other' && o.cash_conversion !== undefined && o.cash_conversion !== null && last3 > 0 && o.cash_conversion < 0.5) { deduct = 1; }
    if (sector === 'lender' && o.writeback_share_max !== undefined && o.writeback_share_max !== null && o.writeback_share_max > 25) { deduct = 1; }
    if (sector === 'insurer' && o.insurer_gain_share_max !== undefined && o.insurer_gain_share_max !== null && o.insurer_gain_share_max > 25) { deduct = 1; }
    return Math.max(0, pts - deduct);
  }

  /* ---------------------------------------------------------------- Dimension 2 */
  function promoter_points(o) {
    var f = o.fall_points_unexplained, a, b, p = o.pledged_pct;
    if (o.repeated_selling || f > 5) { a = 0; }
    else if (f >= 3) { a = 2; }
    else if (f >= 1) { a = 4; }
    else { a = 6; }
    b = p < 10 ? 6 : p < 25 ? 4 : p <= 50 ? 2 : 0;
    return Math.min(a, b);
  }
  var AUDIT = { clean: 5, emphasis: 4, restated_or_large_rpt: 3, qualified_limited: 2,
    qualified_serious_or_going_concern: 1, adverse_disclaimer_undisclosed_rpt: 0 };
  function board_points(o) {
    var late = dflt(o.late_filings, 0), ind = dflt(o.independents, 0), min = dflt(o.legal_min, 1);
    if (o.penalised) { return 0; }
    if (late >= 2 || ind < min) { return 1; }
    if (late === 1) { return 2; }
    if (ind > min && o.tests_met) { return 4; }
    return 3;
  }

  /* ---------------------------------------------------------------- Dimension 3 */
  function turnover_points(o) {
    var avg = o.avg_rs - dflt(o.block_value_excluded_rs, 0);
    var base = avg;
    if (o.median_rs !== undefined && o.median_rs !== null && avg > 2 * o.median_rs) { base = o.median_rs; }
    var pts = base >= 5000000 ? 5 : base >= 1000000 ? 3 : base >= 200000 ? 1 : 0;
    if (dflt(o.share_of_days_traded, 1.0) < 0.5) { pts = Math.min(pts, 1); }
    return pts;
  }
  function float_points(o) {
    var p = o.pct;
    return p >= 40 ? 5 : p >= 25 ? 3 : p >= 10 ? 1 : 0;
  }

  /* ---------------------------------------------------------------- Dimension 4 */
  function pe_points(o) {
    if (o.ttm_eps_negative) { return 0; }
    var ok = dflt(o.roe_ge_median, true) && dflt(o.lender_npl_ok, true);
    if (o.rel <= 0.8) { return ok ? 8 : 6; }
    return o.rel <= 1.1 ? 6 : o.rel <= 1.5 ? 3 : 1;
  }
  function pb_points(o) {
    if (o.book_negative) { return 0; }
    var ok = dflt(o.roe_ge_median, true) && dflt(o.lender_npl_ok, true);
    if (o.rel <= 0.8) { return ok ? 7 : 5; }
    return o.rel <= 1.1 ? 5 : o.rel <= 1.5 ? 3 : 1;
  }
  function valuation_points(o) {
    if (o.pre_cod) {
      var p = pb_points({ rel: o.pb, roe_ge_median: false });
      return Math.floor(p / 7 * 15 + 0.5);
    }
    return pe_points({ rel: o.pe, ttm_eps_negative: o.ttm_eps_negative, roe_ge_median: o.roe_ge_median, lender_npl_ok: o.lender_npl_ok }) +
      pb_points({ rel: o.pb, book_negative: o.book_negative, roe_ge_median: o.roe_ge_median, lender_npl_ok: o.lender_npl_ok });
  }

  /* ---------------------------------------------------------------- Dimension 5 */
  function concentration_points(o) {
    var p = o.largest_pct;
    return p <= 20 ? 7 : p <= 40 ? 4 : p <= 60 ? 2 : 0;
  }

  /* ---------------------------------------------------------------- Dimension 6 */
  function revenue_points(o) {
    var r = o.revenue;
    if (o.insufficient_history) { return 3; }
    if (r[0] <= 0) {
      var last4 = comparisons(r).slice(1);
      return count(last4, function (p) { return p[1] > p[0]; }) >= 3 ? 3 : 0;
    }
    var cagr = (Math.pow(r[5] / r[0], 1 / 5) - 1) * 100;
    var grew = count(comparisons(r), function (p) { return p[1] > p[0]; });
    var swings = nBigSwings(r, false);
    var pts;
    if (cagr < 0 || swings >= 2) { pts = 0; }
    else if (cagr >= 15) { pts = grew >= 4 ? 8 : 6; }
    else if (cagr >= 8) { pts = 6; }
    else { pts = 3; }
    return o.merger_without_combined ? Math.min(pts, 6) : pts;
  }
  function lender_growth_points(o) {
    var diff = o.lender_cagr - o.system_cagr, row;
    if (o.credit_peak && diff > 5) { return 0; }
    if (o.lender_cagr < 0 && 0 <= o.system_cagr && o.system_cagr > 0) { row = 2; }
    else if (Math.abs(diff) <= 5) { row = 8; }
    else if (Math.abs(diff) <= 10) { row = 5; }
    else { row = 2; }
    var ladder = [8, 5, 2], idx = ladder.indexOf(row), drops = 0;
    if (o.lender_cagr - o.deposit_cagr > 5) { drops++; }
    var have = function (v) { return v !== undefined && v !== null; };
    var nplDrop = have(o.gross_npl) && have(o.class_gross_npl) && have(o.adj_npl) && have(o.adj_npl_prev) &&
      o.gross_npl > o.class_gross_npl && o.adj_npl > o.adj_npl_prev;
    if (nplDrop || dflt(o.restructured_pct, 0) > 5) { drops++; }
    var pts = ladder[Math.min(idx + drops, 2)];
    if (dflt(o.system_verified, true) === false) { pts = Math.min(pts, 5); }
    return pts;
  }
  function eps_points(o) {
    var e = o.eps;
    if (o.insufficient_history) { return 2; }
    var rose = count(comparisons(e), function (p) { return p[1] > p[0] && p[1] > 0; });
    var swings = nBigSwings(e, false);
    var negatives = count(e.slice(1), function (x) { return x < 0; });
    var pts;
    if (rose < 2 || negatives >= 3) { pts = 0; }
    else if (rose === 2 || swings >= 2) { pts = 2; }
    else if (rose === 3) { pts = swings <= 1 ? 4 : 2; }
    else { pts = swings === 0 ? 7 : swings === 1 ? 4 : 2; }
    if (e[5] < 0 || negatives >= 2) { pts = Math.min(pts, 2); }
    return pts;
  }

  /* ---------------------------------------------------------------- Dimension 7 */
  function dividend_consistency(o) {
    var paid = count(o.real_cash, function (c) { return !!c; });
    var outside = count(o.real_cash, function (c, i) { var p = o.payout[i]; return c && (p === null || p === undefined || p < 30 || p > 70); });
    if (paid === 5) { return outside <= 1 ? 6 : 4; }
    if (paid === 4) { return 4; }
    if (paid >= 2) { return 2; }
    return 0;
  }
  function source_points(o) {
    if (o.from_capital_or_reserves) { return 0; }
    if (o.partly_one_off || dflt(o.stated_reason, true) === false || dflt(o.reserves_ok, true) === false) { return 2; }
    return 4;
  }

  /* ---------------------------------------------------------------- combining */
  var BANDS = [[85, 'Exceptional combined score', '6%-8%'], [70, 'Strong', '4%-6%'], [55, 'Adequate', '1.5%-3%'],
    [45, 'Weak / Avoid - watch list', 'no new money'], [0, 'Weak / Avoid - exclude', 'no new money']];
  function insurer_solvency_cap(o) {
    return o.solvency_pct !== undefined && o.solvency_pct !== null && !!o.official_source && o.solvency_pct < 100;
  }
  function total_with_limits(o) {
    var total = 0;
    Object.keys(o.dims).forEach(function (k) { total += o.dims[k]; });
    if (o.fraud) { return null; }
    var insCap = insurer_solvency_cap({ solvency_pct: o.insurer_solvency_pct, official_source: o.solvency_official });
    if (o.governance_total < 5 || o.pledging_pts === 0 || o.audit_pts <= 1 || o.problematic || o.capital_below_min ||
        o.disclaimer || insCap) { total = Math.min(total, 54); }
    return total;
  }
  function evidence_grade(o) {
    var p = o.points_flagged;
    if (p < 0) { throw new Error('points cannot be negative'); }
    return p === 0 ? 'A' : p <= 10 ? 'B' : p <= 20 ? 'C' : 'D';
  }
  function bandIndex(total) { for (var i = 0; i < BANDS.length; i++) { if (total >= BANDS[i][0]) { return i; } } return BANDS.length - 1; }
  function band(o) { var b = BANDS[bandIndex(o.total)]; return [b[1], b[2]]; }
  function ceiling(o) {
    var i = bandIndex(o.total);
    if ((i <= 1 && (o.business_quality < 38 || o.share_attractiveness < 13)) || o.provisional) { i += 1; }
    return BANDS[Math.min(i, BANDS.length - 1)][2];
  }

  /* ================================================================
     scoreCompany: the sixteen parts, with sector routing, the missing-data
     rule, hard limits, evidence grade and a written trace for every point.
     ================================================================ */
  var CLASSES = {
    commercial: { label: 'Commercial bank (class A)', lender: true, total: 11, tier1: 8.5, cet1: 7 },
    devbank_national: { label: 'National-level development bank (class B)', lender: true, total: 11, tier1: 8.5, cet1: 7 },
    devbank_other: { label: 'Other development bank (class B)', lender: true, total: 10, tier1: 6, cet1: null },
    finance: { label: 'Finance company (class C)', lender: true, total: 10, tier1: 6, cet1: null },
    mfi: { label: 'Microfinance institution (class D)', lender: true, total: 8, tier1: 4, cet1: null },
    hydro: { label: 'Hydropower, operating', hydro: true },
    hydro_precod: { label: 'Hydropower, not yet producing (pre-COD)', hydro: true, precod: true },
    life: { label: 'Life insurer', insurer: true },
    nonlife: { label: 'Non-life insurer', insurer: true },
    other: { label: 'Manufacturing, hotel, trading or other company' }
  };
  /* missing-data caps: unavailable / unverified parts score no higher than the middle row
     (lower of two middle rows), unless the table sets its own limit (Chapter 64 conventions) */
  var MIDDLE = { roe: 4, capital_bank: 3, capital_ins: 3, capital_debt: 2, earnings: 2, promoter: 2, audit: 2, board: 2,
    turnover: 1, float: 1, pe: 6, pb: 5, pb_precod: 11, moat: 2, concentration: 2, growth_rev: 3, growth_lender: 5, eps: 2,
    div_record: 2, div_source: 2 };

  function n(v) { return (v === '' || v === null || v === undefined || isNaN(+v)) ? null : +v; }
  function series(arr, len) {
    if (!arr || arr.length !== len) { return null; }
    var out = arr.map(n);
    return out.some(function (x) { return x === null; }) ? null : out;
  }
  function f1(x) { return Math.round(x * 100) / 100; }

  function scoreCompany(inp) {
    var cls = CLASSES[inp.sector] || CLASSES.other;
    var isLender = !!cls.lender, isIns = !!cls.insurer, isHydro = !!cls.hydro;
    var parts = [], problems = [], flags = [];

    function add(key, dim, name, max, pts, why, status, capKey, autoFlag) {
      status = status || 'verified';
      var note = '';
      if (pts === null && (status === 'unverified' || status === 'unavailable') && capKey !== undefined && MIDDLE[capKey] !== undefined) {
        /* no figures, but the reader has marked the part as not checkable: Chapter 64's missing-data rule */
        parts.push({ key: key, dim: dim, name: name, max: max, pts: MIDDLE[capKey], why: 'No figures; marked ' + status + ', so scored at the middle row (' + MIDDLE[capKey] + '), as Chapter 64\'s missing-data rule allows at most.', status: status, flagged: true });
        return MIDDLE[capKey];
      }
      if (pts === null) {             /* the figures needed were not entered */
        parts.push({ key: key, dim: dim, name: name, max: max, pts: 0, why: 'Not enough figures entered yet.', status: 'missing', flagged: true });
        return 0;
      }
      if ((status === 'unverified' || status === 'unavailable') && capKey !== undefined && MIDDLE[capKey] !== undefined && pts > MIDDLE[capKey]) {
        note = ' Marked ' + status + ', so capped at the middle row: ' + MIDDLE[capKey] + ' (was ' + pts + ').';
        pts = MIDDLE[capKey];
      }
      var flagged = status !== 'verified' || !!autoFlag;
      parts.push({ key: key, dim: dim, name: name, max: max, pts: pts, why: why + note + (autoFlag ? ' ' + autoFlag : ''), status: autoFlag && status === 'verified' ? 'unverified (by rule)' : status, flagged: flagged });
      return pts;
    }
    var st = inp.status || {};

    /* ---- Dimension 1: Financial Strength (20) */
    var roes = series(inp.roes, 3);
    add('roe', 'fin', 'Three-year average ROE', 8,
      roes ? roe_points({ roes: roes, equity_nonpositive: !!inp.equity_nonpositive }) : null,
      roes ? 'ROEs ' + roes.join('%, ') + '% → average ' + f1((roes[0] + roes[1] + roes[2]) / 3) + '%, lowest ' + Math.min.apply(null, roes) + '%.' : '',
      st.roe, 'roe');

    var capBelow = false, insPct = null, insOfficial = false;
    if (isLender) {
      var car = n(inp.car), t1 = n(inp.tier1), ce = n(inp.cet1);
      var compsKnown = t1 !== null && (cls.cet1 === null || ce !== null);
      var compsMet = (t1 === null || t1 >= cls.tier1) && (cls.cet1 === null || ce === null || ce >= cls.cet1);
      var capPts = car === null ? null : car_points({ car: car, minimum: cls.total, all_components_met: compsMet, breach_in_last_3y: !!inp.breach_3y });
      if (car !== null && (car < cls.total || !compsMet)) { capBelow = true; }
      var capStatus = st.capital || 'verified';
      if (car !== null && !compsKnown && capStatus === 'verified') { capStatus = 'unverified'; }
      add('capital', 'fin', 'Capital cushion (CAR)', 7, capPts,
        car === null ? '' : 'CAR ' + car + '% against ' + cls.total + '% (Tier 1 ' + (t1 === null ? 'not entered' : t1 + '% vs ' + cls.tier1 + '%') +
          (cls.cet1 ? ', common equity ' + (ce === null ? 'not entered' : ce + '% vs ' + cls.cet1 + '%') : '') + ')' +
          (compsMet ? '' : '; a layer is below its minimum') + (inp.breach_3y ? '; breach in the last 3 years caps at 3' : '') +
          (compsKnown ? '.' : '. All layers not entered, so treated as unverified.'),
        capStatus, 'capital_bank');
    } else if (isIns) {
      var rep = n(inp.solvency), wt = n(inp.solvency_wt);
      if (rep !== null) {
        insPct = insurer_ratio_to_score({ reported_pct: rep, without_transitional_pct: wt });
        insOfficial = !!inp.solvency_official;
      }
      add('capital', 'fin', 'Solvency cushion', 7, insPct === null ? null : insurer_points({ solvency_pct: insPct }),
        insPct === null ? '' : 'Solvency ratio scored: ' + insPct + '%' + (wt !== null ? ' (the lower of ' + rep + '% and ' + wt + '% without transitional provisions)' : '') + '.' +
          (insOfficial ? '' : ' Not from an official source, so it cannot fire the cap.'),
        st.capital, 'capital_ins');
    } else {
      var de = n(inp.de), cov = n(inp.cover);
      var dp = (de === null && !inp.equity_nonpositive) ? null : de_points({ de: de, equity_nonpositive: !!inp.equity_nonpositive });
      var cp = (cov === null && !inp.no_debt && !inp.operating_loss) ? null : cover_points({ cover: cov, no_interest_bearing_debt: !!inp.no_debt, operating_loss: !!inp.operating_loss });
      add('capital', 'fin', 'Leverage (debt-to-equity + interest cover)', 7, (dp === null || cp === null) ? null : dp + cp,
        'Debt-to-equity ' + (inp.equity_nonpositive ? 'n/a, equity zero or negative' : de + '×') + ' → ' + dp + ' of 3; interest cover ' +
          (inp.operating_loss ? 'operating loss' : inp.no_debt ? 'no interest-bearing debt' : cov + '×') + ' → ' + cp + ' of 4.',
        st.capital, 'capital_debt');
    }

    var profits = series(inp.profits, 6);
    var eqSector = isLender ? 'lender' : isIns ? 'insurer' : 'other';
    add('earnings', 'fin', 'Earnings quality', 5,
      profits ? earnings_quality({ profits: profits, sector: eqSector, cash_conversion: n(inp.cash_conversion), writeback_share_max: n(inp.writeback_max), insurer_gain_share_max: n(inp.gain_max) }) : null,
      profits ? 'Six profits, oldest first: ' + profits.join(', ') + '. Profit check: ' +
        (eqSector === 'other' ? 'cash conversion ' + (n(inp.cash_conversion) === null ? 'not entered' : n(inp.cash_conversion)) :
          eqSector === 'lender' ? 'largest write-back / one-off share ' + (n(inp.writeback_max) === null ? 'not entered' : n(inp.writeback_max) + '%') :
            'largest realised-gain / reserve-release share ' + (n(inp.gain_max) === null ? 'not entered' : n(inp.gain_max) + '%')) + '.' : '',
      st.earnings, 'earnings');

    /* ---- Dimension 2: Governance (15) */
    var fall = n(inp.promoter_fall), pledged = n(inp.pledged);
    var promoPts = (fall === null || (pledged === null && !inp.pledge_unverified)) ? null :
      promoter_points({ fall_points_unexplained: fall, pledged_pct: pledged === null ? 0 : pledged, repeated_selling: !!inp.repeated_selling });
    var promoWhy = fall === null ? '' : 'Unexplained fall ' + fall + ' points' + (inp.repeated_selling ? ', repeated insider selling' : '') +
      '; pledged ' + (pledged === null ? 'not found' : pledged + '%') + '; the check takes the lower part.';
    if (promoPts !== null && inp.pledge_unverified && promoPts > 4) { promoWhy += ' Pledging not verified, so at most 4 (was ' + promoPts + ').'; promoPts = 4; }
    var pledgingPts = add('promoter', 'gov', 'Promoter holding and pledging', 6, promoPts, promoWhy, st.promoter || (inp.pledge_unverified ? 'unverified' : 'verified'), 'promoter');
    var auditPts = add('audit', 'gov', 'Audit opinion and related-party dealings', 5,
      inp.audit in AUDIT ? AUDIT[inp.audit] : null, inp.audit in AUDIT ? 'Category: ' + (AUDIT_LABEL[inp.audit] || inp.audit) + '.' : '', st.audit, 'audit');
    var ind = n(inp.independents), lmin = n(inp.legal_min);
    var bp = ind === null ? null : board_points({ penalised: !!inp.penalised, late_filings: n(inp.late_filings) || 0, independents: ind, legal_min: lmin === null ? 1 : lmin, tests_met: inp.tests_met === 'yes' });
    var bwhy = ind === null ? '' : ind + ' independent director(s) against a legal minimum of ' + (lmin === null ? 1 : lmin) + '; ' + (n(inp.late_filings) || 0) + ' late filing(s)' + (inp.penalised ? '; penalised for disclosure' : '') + '; attendance and audit-committee tests ' + (inp.tests_met === 'yes' ? 'met' : inp.tests_met === 'no' ? 'not met' : 'not checked') + '.';
    if (bp === 4 && inp.tests_met !== 'yes') { bp = 3; }
    add('board', 'gov', 'Disclosure and board', 4, bp, bwhy, st.board, 'board');

    /* ---- Dimension 3: Liquidity (10) */
    var avg = n(inp.turnover_avg), med = n(inp.turnover_median), days = n(inp.days_traded);
    add('turnover', 'liq', 'Average daily turnover, 6 months', 5,
      avg === null ? null : turnover_points({ avg_rs: avg, median_rs: med, share_of_days_traded: days === null ? 1 : days / 100, block_value_excluded_rs: n(inp.block_excluded) || 0 }),
      avg === null ? '' : 'Average Rs ' + avg.toLocaleString('en-IN') + (med !== null ? ', median Rs ' + med.toLocaleString('en-IN') + (avg > 2 * med ? ' (average over twice the median, so the median is used)' : '') : '') + (days !== null ? '; traded on ' + days + '% of days' : '') + '.',
      st.turnover, 'turnover');
    var fl = n(inp.free_float);
    add('float', 'liq', 'Free float', 5, fl === null ? null : float_points({ pct: fl }), fl === null ? '' : 'Free float ' + fl + '%.', st.float, 'float');

    /* ---- Dimension 4: Valuation (15) */
    var price = n(inp.price), eps = n(inp.eps_ttm), bvps = n(inp.bvps), mpe = n(inp.median_pe), mpb = n(inp.median_pb);
    var peers = n(inp.peers);
    var roeGe = inp.roe_ge_median !== 'no', nplOk = !isLender || inp.npl_ok !== 'no';
    var cashFailed = !isLender && !isIns && n(inp.cash_conversion) !== null && n(inp.cash_conversion) < 0.5;
    var gateOk = roeGe && nplOk && !cashFailed;
    var fewPeers = peers !== null && peers < 5;
    var peerFlag = fewPeers ? 'Fewer than five peers: unverified, scored in the "in line" row.' : '';
    if (cls.precod) {
      var relpb0 = (price !== null && bvps && mpb) ? price / bvps / mpb : null;
      var bookNeg0 = bvps !== null && bvps <= 0;
      var vp = (relpb0 === null && !bookNeg0) ? null : bookNeg0 ? 0 : fewPeers ? Math.floor(5 / 7 * 15 + 0.5) : valuation_points({ pb: relpb0, pre_cod: true });
      add('pb', 'val', 'Valuation (pre-COD: P/B only, scaled to 15)', 15, vp,
        relpb0 === null ? (bookNeg0 ? 'Book value zero or negative.' : '') : 'P/B ' + f1(price / bvps) + '× ÷ median ' + mpb + '× = ' + relpb0.toFixed(3) + ' (unrounded). P/E not applicable before COD; scaled from 7 to 15.',
        st.pb, 'pb_precod', peerFlag);
    } else {
      var lossEps = eps !== null && eps <= 0;
      var relpe = (price !== null && eps && eps > 0 && mpe) ? price / eps / mpe : null;
      var pep = lossEps ? 0 : relpe === null ? null : fewPeers ? 6 : pe_points({ rel: relpe, roe_ge_median: gateOk, lender_npl_ok: true });
      add('pe', 'val', 'P/E against sector median', 8, pep,
        lossEps ? 'Trailing 12-month EPS zero or negative: 0.' : relpe === null ? '' : 'P/E ' + f1(price / eps) + ' ÷ median ' + mpe + ' = ' + relpe.toFixed(3) + ' (unrounded)' + (relpe <= 0.8 ? (gateOk ? '; discount earned' : '; discount not earned, scored in line') : '') + '.',
        st.pe, 'pe', peerFlag);
      var bookNeg = bvps !== null && bvps <= 0;
      var relpb = (price !== null && bvps && bvps > 0 && mpb) ? price / bvps / mpb : null;
      var pbp = bookNeg ? 0 : relpb === null ? null : fewPeers ? 5 : pb_points({ rel: relpb, roe_ge_median: gateOk, lender_npl_ok: true });
      add('pb', 'val', 'P/B against sector median', 7, pbp,
        bookNeg ? 'Book value zero or negative: 0.' : relpb === null ? '' : 'P/B ' + f1(price / bvps) + ' ÷ median ' + mpb + ' = ' + relpb.toFixed(3) + ' (unrounded)' + (relpb <= 0.8 ? (gateOk ? '; discount earned' : '; discount not earned, scored in line') : '') + '.',
        st.pb, 'pb', peerFlag);
    }

    /* ---- Dimension 5: Durability (15) */
    var moat = n(inp.moat);
    add('moat', 'dur', 'Moat', 8, moat, moat === null ? '' : MOAT_LABEL[moat] || '', st.moat, 'moat');
    if (isHydro && inp.single_buyer !== false) {
      add('concentration', 'dur', 'Concentration', 7, 0, 'Single-buyer PPA with NEA: 0 by Chapter 64\'s provisional rule; compare only with other hydropower companies.', 'verified', 'concentration');
    } else if (isIns) {
      var cIns = n(inp.concentration);
      add('concentration', 'dur', 'Concentration', 7, cIns === null ? 2 : Math.min(2, concentration_points({ largest_pct: cIns })),
        'Insurer concentration is unverified until Chapter 65 sets an insurer table: capped at 2.', 'unverified (by rule)', 'concentration', '');
    } else {
      var conc = n(inp.concentration);
      add('concentration', 'dur', 'Concentration', 7, conc === null ? null : concentration_points({ largest_pct: conc }),
        conc === null ? '' : 'Largest single exposure ' + conc + '%' + (isLender ? ' (biggest loan sector or region)' : '') + '.', st.concentration, 'concentration');
    }

    /* ---- Dimension 6: Growth (15) */
    if (isLender) {
      var lc = n(inp.loan_cagr), sc = n(inp.system_cagr), dc = n(inp.deposit_cagr);
      var gp = (lc === null || sc === null || dc === null) ? null : lender_growth_points({
        lender_cagr: lc, system_cagr: sc, deposit_cagr: dc, credit_peak: !!inp.credit_peak,
        gross_npl: n(inp.gross_npl), class_gross_npl: n(inp.class_npl), adj_npl: n(inp.adj_npl), adj_npl_prev: n(inp.adj_npl_prev),
        restructured_pct: n(inp.restructured) || 0, system_verified: inp.system_verified !== false });
      add('growth', 'gro', 'Loan growth against the system', 8, gp,
        gp === null ? '' : 'Loan CAGR ' + lc + '% vs system ' + sc + '% (difference ' + f1(lc - sc) + ' points); deposits ' + dc + '%' + (inp.credit_peak ? '; credit peak' : '') + (n(inp.restructured) > 5 ? '; restructured loans over 5%' : '') + '.',
        st.growth, 'growth_lender');
    } else {
      var rev = series(inp.revenue, 6);
      var insuff = !!inp.revenue_insufficient;
      var rp = insuff ? 3 : rev ? revenue_points({ revenue: rev, merger_without_combined: !!inp.merger }) : null;
      var rwhy = insuff ? 'Fewer than four comparisons: 3, counted as unverified.' : rev ? (rev[0] > 0 ? 'Revenue CAGR ' + f1((Math.pow(rev[5] / rev[0], 0.2) - 1) * 100) + '% over five years.' : 'Zero or part-year start: growth-years test.') + (inp.merger ? ' Merger without combined figures: at most 6.' : '') : '';
      add('growth', 'gro', isIns ? 'Net earned premium growth' : 'Revenue growth', 8, rp, rwhy, insuff ? 'unverified' : st.growth, 'growth_rev');
    }
    var epsS = series(inp.eps_series, 6);
    var epsInsuff = !!inp.eps_insufficient;
    add('eps', 'gro', 'EPS growth (comparable share count)', 7, epsInsuff ? 2 : epsS ? eps_points({ eps: epsS }) : null,
      epsInsuff ? 'Fewer than six EPS figures: at most 2, counted as unverified.' : epsS ? 'Six EPS figures: ' + epsS.join(', ') + '.' : '', epsInsuff ? 'unverified' : st.eps, 'eps');

    /* ---- Dimension 7: Dividends (10) */
    var cashArr = inp.div_cash, payArr = inp.div_payout;
    var haveDiv = cashArr && cashArr.length === 5;
    add('div_record', 'div', 'Dividend record, 5 years', 6,
      haveDiv ? dividend_consistency({ real_cash: cashArr.map(function (c) { return !!c; }), payout: (payArr || []).map(n) }) : null,
      haveDiv ? 'Real cash in ' + count(cashArr, function (c) { return !!c; }) + ' of 5 years; payouts ' + (payArr || []).map(function (p, i) { return cashArr[i] ? (n(p) === null ? 'n/a' : n(p) + '%') : '—'; }).join(', ') + '.' : '',
      st.div_record, 'div_record');
    var srcPts = inp.div_source in SOURCE ? SOURCE[inp.div_source] : null;
    add('div_source', 'div', 'Dividend source and reason', 4, srcPts, srcPts === null ? '' : SOURCE_LABEL[inp.div_source], st.div_source, 'div_source');

    /* ---- totals */
    var dims = { fin: 0, gov: 0, liq: 0, val: 0, dur: 0, gro: 0, div: 0 };
    parts.forEach(function (p) { dims[p.dim] += p.pts; });
    var bq = dims.fin + dims.gov + dims.dur + dims.gro + dims.div;
    var sa = dims.liq + dims.val;
    var raw = bq + sa;
    var flaggedPts = 0, missingParts = [];
    parts.forEach(function (p) { if (p.flagged) { flaggedPts += p.max; } if (p.status === 'missing') { missingParts.push(p.name); } });
    var disclaimer = inp.audit === 'adverse_disclaimer_undisclosed_rpt' && !!inp.disclaimer;
    var isMissing = function (key) { return parts.some(function (p) { return p.key === key && p.status === 'missing'; }); };
    var govComplete = !isMissing('promoter') && !isMissing('audit') && !isMissing('board');
    var capReasons = [];
    if (govComplete && dims.gov < 5) { capReasons.push('governance total under 5 of 15'); }
    if (!isMissing('promoter') && pledgingPts === 0) { capReasons.push('promoter/pledging check scored 0'); }
    if (auditPts <= 1 && inp.audit in AUDIT) { capReasons.push('audit check scored ' + auditPts); }
    if (inp.problematic) { capReasons.push('NRB "problematic" status'); }
    if (capBelow) { capReasons.push('capital below the minimum in a layer'); }
    if (insurer_solvency_cap({ solvency_pct: insPct, official_source: insOfficial })) { capReasons.push('official insurer solvency under 100%'); }
    var total = total_with_limits({ dims: dims, governance_total: govComplete ? dims.gov : 15, pledging_pts: isMissing('promoter') ? 6 : pledgingPts,
      audit_pts: inp.audit in AUDIT ? auditPts : 5, problematic: !!inp.problematic, capital_below_min: capBelow, disclaimer: disclaimer,
      fraud: !!inp.fraud, insurer_solvency_pct: insPct, solvency_official: insOfficial });
    var grade = evidence_grade({ points_flagged: flaggedPts });
    var provisional = grade === 'D' || !!inp.restated;
    var out = { cls: cls, parts: parts, dims: dims, bq: bq, sa: sa, raw: raw, total: total, capReasons: capReasons,
      flaggedPts: flaggedPts, grade: grade, provisional: provisional, restated: !!inp.restated, excluded: total === null,
      complete: missingParts.length === 0, missingParts: missingParts };
    if (total !== null) {
      var b = band({ total: total });
      out.band = b[0]; out.bandCeiling = b[1];
      out.ceiling = ceiling({ total: total, business_quality: bq, share_attractiveness: sa, provisional: provisional });
      out.ceilingDropped = out.ceiling !== out.bandCeiling;
    }
    return out;
  }
  var AUDIT_LABEL = { clean: 'clean opinion; related-party dealings small and disclosed', emphasis: 'clean with an emphasis-of-matter note',
    restated_or_large_rpt: 'restated year, or large related-party dealings though disclosed', qualified_limited: 'qualified on a limited, explained matter',
    qualified_serious_or_going_concern: 'qualified on loans, provisions or related-party dealings, a scope limit or a going-concern doubt',
    adverse_disclaimer_undisclosed_rpt: 'adverse opinion, disclaimer, or undisclosed related-party dealings' };
  var MOAT_LABEL = { 8: 'High barriers with five-year proof.', 5: 'Moderate barriers, or a licence without proof.', 2: 'Low barriers; commodity-like business.', 0: 'A structural regulatory or technological threat.' };
  var SOURCE = { genuine: 4, partly: 2, capital: 0 };
  var SOURCE_LABEL = { genuine: 'Genuine distributable profit, reserves intact, reason stated for profit kept.', partly: 'Partly one-off or revaluation gains, or profit kept with no stated reason.', capital: 'Paid out of capital or reserves.' };

  var API = { comparisons: comparisons, big_swing: bigSwing, roe_points: roe_points, car_points: car_points,
    insurer_ratio_to_score: insurer_ratio_to_score, insurer_points: insurer_points, de_points: de_points, cover_points: cover_points,
    earnings_quality: earnings_quality, promoter_points: promoter_points, board_points: board_points, turnover_points: turnover_points,
    float_points: float_points, pe_points: pe_points, pb_points: pb_points, valuation_points: valuation_points,
    concentration_points: concentration_points, revenue_points: revenue_points, lender_growth_points: lender_growth_points,
    eps_points: eps_points, dividend_consistency: dividend_consistency, source_points: source_points,
    insurer_solvency_cap: insurer_solvency_cap, total_with_limits: total_with_limits, evidence_grade: evidence_grade,
    band: band, ceiling: ceiling, scoreCompany: scoreCompany, CLASSES: CLASSES, AUDIT: AUDIT, VERSION: '1.6.0' };
  if (typeof module !== 'undefined' && module.exports) { module.exports = API; } else { root.CanonEngine = API; }
})(this);
