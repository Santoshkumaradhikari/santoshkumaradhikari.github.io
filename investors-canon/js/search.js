/* The Investor's Canon — chapter search widget.
   Self-contained: carries its own small chapter index (121 chapters, no
   network request), builds its own overlay, and wires up to any button
   with the class "nav-search-btn" already present in the page header.
   Works the same whether the page is a chapter file (one folder deep) or
   a hub page (index/framework/glossary/study-guide) in the Canon root. */
(function () {
  "use strict";

  var CHAPTERS = [{"n":"0.1","t":"Nepal’s Credit Cycle: The Hidden Equity Cycle","s":"ch-0-1-credit-cycle.html","p":"Part 0"},{"n":"0.2","t":"NRB Policy → Equity Price Transmission: The Central Causal Chain","s":"ch-0-2-nrb-transmission.html","p":"Part 0"},{"n":"0.3","t":"Liquidity Regimes in Nepal: The Four-Phase Framework","s":"ch-0-3-liquidity-regimes.html","p":"Part 0"},{"n":"1","t":"NRB’s Monetary Policy Framework","s":"ch-01-nrb-monetary-policy.html","p":"Part I"},{"n":"2","t":"Credit Policy and Its Direct Impact on NEPSE","s":"ch-02-credit-policy-impact.html","p":"Part I"},{"n":"3","t":"NRB Policy Transmission — From Announcement to Share Price","s":"ch-03-nrb-policy-transmission.html","p":"Part I"},{"n":"4","t":"Nepal’s External Sector and NEPSE Implications","s":"ch-04-external-sector.html","p":"Part I"},{"n":"5","t":"How India’s Economy Affects NEPSE","s":"ch-05-india-economy.html","p":"Part I"},{"n":"6","t":"Global Macro and Event-Driven Risk","s":"ch-06-global-macro-risk.html","p":"Part I"},{"n":"7","t":"What Is NEPSE and Why It Behaves Differently","s":"ch-07-nepse-reality.html","p":"Part II"},{"n":"8","t":"Regulatory Architecture of the Nepal Capital Market","s":"ch-08-regulatory-architecture.html","p":"Part II"},{"n":"9","t":"Market Participants in NEPSE","s":"ch-09-market-participants.html","p":"Part II"},{"n":"10","t":"Trading Mechanics in NEPSE","s":"ch-10-trading-mechanics.html","p":"Part II"},{"n":"11","t":"The Liquidity Problem — NEPSE’s Most Critical Structural Characteristic","s":"ch-11-liquidity-problem.html","p":"Part II"},{"n":"12","t":"Market Microstructure Failures in NEPSE","s":"ch-12-microstructure-failures.html","p":"Part II"},{"n":"13","t":"Ordinary Shares","s":"ch-13-ordinary-shares.html","p":"Part III"},{"n":"14","t":"IPOs and the Primary Market","s":"ch-14-ipos.html","p":"Part III"},{"n":"15","t":"Rights Issues and FPOs","s":"ch-15-rights-issues-fpos.html","p":"Part III"},{"n":"16","t":"Mutual Funds in Nepal","s":"ch-16-mutual-funds.html","p":"Part III"},{"n":"17","t":"Debentures and Bonds in Nepal","s":"ch-17-debentures-bonds.html","p":"Part III"},{"n":"18","t":"What Does Not Yet Exist in Nepal","s":"ch-18-what-doesnt-exist.html","p":"Part III"},{"n":"19","t":"The Governance Landscape in Nepal","s":"ch-19-governance-landscape.html","p":"Part IV"},{"n":"20","t":"Promoter Behaviour — The Most Underanalysed Risk in NEPSE","s":"ch-20-promoter-behaviour.html","p":"Part IV"},{"n":"21","t":"Insider Trading and Information Asymmetry in Nepal","s":"ch-21-insider-trading.html","p":"Part IV"},{"n":"22","t":"Conglomerate Cross-Holdings and Promoter Webs in Nepal","s":"ch-22-conglomerate-crossholdings.html","p":"Part IV"},{"n":"23","t":"Governance Scoring for NEPSE Companies","s":"ch-23-governance-scoring.html","p":"Part IV"},{"n":"24","t":"Reading Financial Statements Under Nepal Standards","s":"ch-24-reading-financial-statements.html","p":"Part V"},{"n":"25","t":"The Balance Sheet — Deep Reading","s":"ch-25-balance-sheet.html","p":"Part V"},{"n":"26","t":"The Income Statement — Deep Reading","s":"ch-26-income-statement.html","p":"Part V"},{"n":"27","t":"The Cash Flow Statement — The Truth Teller","s":"ch-27-cash-flow-statement.html","p":"Part V"},{"n":"28","t":"Red Flags in Nepali Financial Statements","s":"ch-28-red-flags.html","p":"Part V"},{"n":"29","t":"Banking Sector Accounting Logic","s":"ch-29-banking-accounting.html","p":"Part VI"},{"n":"30","t":"Development Bank and Finance Company Accounting","s":"ch-30-development-bank-finance.html","p":"Part VI"},{"n":"31","t":"Microfinance (MFI) Accounting Logic","s":"ch-31-microfinance-accounting.html","p":"Part VI"},{"n":"32","t":"Hydropower Project Accounting Logic","s":"ch-32-hydropower-accounting.html","p":"Part VI"},{"n":"33","t":"Insurance Sector Accounting","s":"ch-33-insurance-accounting.html","p":"Part VI"},{"n":"34","t":"Manufacturing, Trading & Hotel Sector Accounting","s":"ch-34-manufacturing-trading-hotel.html","p":"Part VI"},{"n":"35","t":"Capital Gains Tax in Nepal","s":"ch-35-capital-gains-tax.html","p":"Part VII"},{"n":"36","t":"Dividend and Interest Taxation","s":"ch-36-dividend-interest-tax.html","p":"Part VII"},{"n":"37","t":"Tax Treatment of Rights and Bonus Shares","s":"ch-37-rights-bonus-tax.html","p":"Part VII"},{"n":"38","t":"Tax Planning for the Long-Term NEPSE Investor","s":"ch-38-tax-planning.html","p":"Part VII"},{"n":"39","t":"Valuation Ratios in the NEPSE Context","s":"ch-39-valuation-ratios.html","p":"Part VII"},{"n":"40","t":"Profitability Ratios — Sector by Sector","s":"ch-40-profitability-ratios.html","p":"Part VII"},{"n":"41","t":"Asset Quality, Capital, Solvency & Efficiency Ratios","s":"ch-41-asset-quality-ratios.html","p":"Part VII"},{"n":"42","t":"Understanding Project Finance","s":"ch-42-project-finance.html","p":"Part VIII"},{"n":"43","t":"The Hydropower Financial Model","s":"ch-43-hydropower-financial-model.html","p":"Part VIII"},{"n":"44","t":"Evaluating a Hydropower Stock on NEPSE","s":"ch-44-evaluating-hydropower-stock.html","p":"Part VIII"},{"n":"45","t":"The Philosophy of Valuation","s":"ch-45-philosophy-valuation.html","p":"Part IX"},{"n":"46","t":"Discounted Cash Flow (DCF) Valuation","s":"ch-46-dcf-valuation.html","p":"Part IX"},{"n":"47","t":"Relative Valuation (Comps)","s":"ch-47-relative-valuation-comps.html","p":"Part IX"},{"n":"48","t":"Dividend Discount Model (DDM)","s":"ch-48-dividend-discount-model.html","p":"Part IX"},{"n":"49","t":"Book Value and Net Asset Value Approaches","s":"ch-49-book-value-nav.html","p":"Part IX"},{"n":"50","t":"Why Nepali Investors Systematically Lose Money","s":"ch-50-why-nepali-investors-lose.html","p":"Part X"},{"n":"51","t":"Core Behavioural Biases for the NEPSE Investor","s":"ch-51-core-behavioural-biases.html","p":"Part X"},{"n":"52","t":"Building Investor Temperament","s":"ch-52-building-investor-temperament.html","p":"Part X"},{"n":"53","t":"Behavioural Training Exercises","s":"ch-53-behavioural-training-exercises.html","p":"Part X"},{"n":"54","t":"Liquidity as a First-Order Investment Risk in NEPSE","s":"ch-54-liquidity-first-order-risk.html","p":"Part XI"},{"n":"55","t":"Exit Risk in NEPSE","s":"ch-55-exit-risk.html","p":"Part XI"},{"n":"56","t":"Position Size vs. ADV Rule: The Governing Law for NEPSE","s":"ch-56-adv-rule.html","p":"Part XI"},{"n":"57","t":"Free Float-Based Allocation Limits","s":"ch-57-free-float-allocation-limits.html","p":"Part XI"},{"n":"58","t":"Circuit Trap Exit Modelling","s":"ch-58-circuit-trap-exit-modelling.html","p":"Part XI"},{"n":"59","t":"Asset Allocation Within Nepal’s Investment Universe","s":"ch-59-asset-allocation.html","p":"Part XII"},{"n":"60","t":"Equity Portfolio Construction for NEPSE","s":"ch-60-equity-portfolio-construction.html","p":"Part XII"},{"n":"61","t":"Portfolio Risk Management","s":"ch-61-portfolio-risk-management.html","p":"Part XII"},{"n":"62","t":"Systematic and Disciplined Investing","s":"ch-62-systematic-disciplined-investing.html","p":"Part XII"},{"n":"63","t":"Philosophy of the Canon Scoring System","s":"ch-63-canon-scoring-philosophy.html","p":"Part XIII"},{"n":"64","t":"The Seven-Dimension Company Quality Score (0–100)","s":"ch-64-seven-dimension-score.html","p":"Part XIII"},{"n":"65","t":"Sector-Specific Sub-Score Adjustments","s":"ch-65-sector-subscore-adjustments.html","p":"Part XIII"},{"n":"66","t":"Using the Canon Score in Portfolio Decisions","s":"ch-66-using-canon-score-portfolio.html","p":"Part XIII"},{"n":"67","t":"Long-Term Value Investing on NEPSE","s":"ch-67-long-term-value-investing.html","p":"Part XIV"},{"n":"68","t":"Dividend Income Strategy","s":"ch-68-dividend-income-strategy.html","p":"Part XIV"},{"n":"69","t":"IPO, Rights Issue & Sector Rotation Strategies","s":"ch-69-ipo-rights-sector-rotation.html","p":"Part XIV"},{"n":"70","t":"Research and Tracking Systems for the Nepali Investor","s":"ch-70-research-tracking-systems.html","p":"Part XIV"},{"n":"71","t":"The Banking Sector Playbook","s":"ch-71-banking-sector-playbook.html","p":"Part XIV"},{"n":"72","t":"The Hydropower Sector Playbook","s":"ch-72-hydropower-sector-playbook.html","p":"Part XIV"},{"n":"73","t":"The Microfinance Sector Playbook","s":"ch-73-microfinance-sector-playbook.html","p":"Part XIV"},{"n":"74","t":"The Insurance Sector Playbook","s":"ch-74-insurance-sector-playbook.html","p":"Part XIV"},{"n":"75","t":"The Manufacturing & Hotel Sector Playbook","s":"ch-75-manufacturing-hotel-playbook.html","p":"Part XIV"},{"n":"76","t":"The Liquidity-Based Entry and Exit Playbook","s":"ch-76-liquidity-entry-exit-playbook.html","p":"Part XIV"},{"n":"77","t":"The IPO Playbook","s":"ch-77-ipo-playbook.html","p":"Part XIV"},{"n":"78","t":"The Rights Issue Playbook","s":"ch-78-rights-issue-playbook.html","p":"Part XIV"},{"n":"79","t":"The Backtesting Mindset","s":"ch-79-backtesting-mindset.html","p":"Part XV"},{"n":"80","t":"Calibrating Your Scoring Model Against NEPSE History","s":"ch-80-calibrating-scoring-model.html","p":"Part XV"},{"n":"81","t":"Testing and Refining Exit Rules","s":"ch-81-testing-refining-exit-rules.html","p":"Part XV"},{"n":"82","t":"Measuring and Managing Model Drift","s":"ch-82-measuring-managing-model-drift.html","p":"Part XV"},{"n":"83","t":"Case Study 1 — A Commercial Bank","s":"ch-83-case-study-commercial-bank.html","p":"Part XVI"},{"n":"84","t":"Case Study 2 — A Hydropower Plant","s":"ch-84-case-study-hydropower-plant.html","p":"Part XVI"},{"n":"85","t":"Case Study 3 — A Microfinance Institution","s":"ch-85-case-study-microfinance-institution.html","p":"Part XVI"},{"n":"86","t":"Case Study 4 — A Manufacturing Company","s":"ch-86-case-study-manufacturing-company.html","p":"Part XVI"},{"n":"87","t":"Case Study 5 — A Rights Issue Decision","s":"ch-87-case-study-rights-issue.html","p":"Part XVI"},{"n":"88","t":"Case Study 6 — An IPO Analysis","s":"ch-88-case-study-ipo-analysis.html","p":"Part XVI"},{"n":"89","t":"Case Study 7 — A Bank Failure or Near-Failure","s":"ch-89-case-study-bank-failure.html","p":"Part XVI"},{"n":"90","t":"Case Study 8 — The 2021 NEPSE Mania","s":"ch-90-case-study-nepse-mania.html","p":"Part XVI"},{"n":"91","t":"Case Study 9 — A Hydropower Overrun and Delay","s":"ch-91-case-study-hydropower-overrun.html","p":"Part XVI"},{"n":"92","t":"Case Study 10 — An Insurance Company","s":"ch-92-case-study-insurance-company.html","p":"Part XVI"},{"n":"93","t":"Case Study 11 — A Hotel Sector Investment","s":"ch-93-case-study-hotel-investment.html","p":"Part XVI"},{"n":"94","t":"The Daily, Weekly, Monthly, Quarterly & Annual Routines","s":"ch-94-daily-weekly-monthly-annual-routines.html","p":"Part XVII"},{"n":"95","t":"Writing Your Personal Investment Constitution","s":"ch-95-investment-constitution.html","p":"Part XVII"},{"n":"96","t":"Rules for Overriding the Model","s":"ch-96-overriding-the-model.html","p":"Part XVII"},{"n":"97","t":"Maximum Drawdown and Loss Rules","s":"ch-97-drawdown-loss-rules.html","p":"Part XVII"},{"n":"98","t":"The Constitution Review and Update Protocol","s":"ch-98-constitution-review-protocol.html","p":"Part XVII"},{"n":"99","t":"The Full Investment Memo — A Complete Worked Example","s":"ch-99-full-investment-memo.html","p":"Part XVII"},{"n":"100","t":"The Full Portfolio Construction Walkthrough","s":"ch-100-portfolio-construction-walkthrough.html","p":"Part XVII"},{"n":"101","t":"Pre-Buy Checklists","s":"ch-101-pre-buy-checklists.html","p":"Part XVIII"},{"n":"102","t":"Financial Model Templates","s":"ch-102-financial-model-templates.html","p":"Part XVIII"},{"n":"103","t":"Position Sizing and Portfolio Management Tools","s":"ch-103-position-sizing-portfolio-tools.html","p":"Part XVIII"},{"n":"104","t":"Performance Monitoring Tools","s":"ch-104-performance-monitoring-tools.html","p":"Part XVIII"},{"n":"105","t":"The Canon Data Pipeline","s":"ch-105-canon-data-pipeline.html","p":"Part XVIII"},{"n":"106","t":"The NEPSE Data Handbook — Historical Almanac","s":"ch-106-nepse-data-handbook-almanac.html","p":"Part XVIII"},{"n":"107","t":"Keeping the Canon Current","s":"ch-107-keeping-canon-current.html","p":"Part XVIII"},{"n":"108","t":"Adapting to Market Evolution","s":"ch-108-adapting-to-market-evolution.html","p":"Part XVIII"},{"n":"109","t":"The Lifelong Investor’s Mindset","s":"ch-109-lifelong-investor-mindset.html","p":"Part XVIII"},{"n":"110","t":"The NEPSE Regulatory Change Tracker","s":"ch-110-nepse-regulatory-change-tracker.html","p":"Part XVIII"},{"n":"111","t":"Building Your Personal Research Library","s":"ch-111-personal-research-library.html","p":"Part XVIII"},{"n":"112","t":"Technology Tools for the NEPSE Investor","s":"ch-112-technology-tools-nepse-investor.html","p":"Part XVIII"},{"n":"113","t":"The Annual Financial Calendar for NEPSE","s":"ch-113-annual-financial-calendar.html","p":"Part XVIII"},{"n":"114","t":"Communication Protocols — Broker, AGM, SEBON","s":"ch-114-communication-protocols.html","p":"Part XVIII"},{"n":"115","t":"Multi-Generational Wealth Building Through NEPSE","s":"ch-115-multigenerational-wealth-building.html","p":"Part XVIII"},{"n":"116","t":"Teaching the Canon — Sharing Knowledge Responsibly","s":"ch-116-teaching-the-canon.html","p":"Part XVIII"},{"n":"117","t":"The Canon Audit — Annual Self-Assessment","s":"ch-117-canon-audit.html","p":"Part XVIII"},{"n":"118","t":"Final Synthesis — The Complete Canon Investor","s":"ch-118-final-synthesis.html","p":"Part XVIII"}];

  // Volume colours (Nepal colour layer, 25 Nov 2026). Each chapter takes the
  // colour of its volume: 1 Foundations blue, 2 Analysis crimson,
  // 3 Execution marigold, 4 Mastery green (see css/style.css). We also add a
  // small coloured "Volume · Part" chip above the chapter title.
  (function volumeColour() {
    var m = window.location.pathname.match(/\/chapters\/ch-(\d+)(?:-(\d+))?[a-z]?-/);
    if (!m) { return; }
    var num = m[1] === "0" ? 0 : parseInt(m[1], 10);
    var vol = num <= 23 ? 1 : num <= 49 ? 2 : num <= 82 ? 3 : 4;
    var NAMES = { 1: "Foundations", 2: "Analysis", 3: "Execution", 4: "Mastery" };
    document.documentElement.setAttribute("data-volume", String(vol));
    var key = m[1] === "0" ? "ch-0-" + m[2] + "-" : "ch-" + m[1] + "-";
    var part = "";
    for (var i = 0; i < CHAPTERS.length; i++) {
      if (CHAPTERS[i].s.indexOf(key) === 0) { part = CHAPTERS[i].p; break; }
    }
    function addChip() {
      var h1 = document.querySelector("main h1");
      if (!h1 || document.querySelector(".vol-chip")) { return; }
      var a = document.createElement("a");
      a.className = "vol-chip";
      a.href = "../index.html#volume-" + vol;
      a.title = "Volume " + vol + (part ? ", " + part : "") + " — back to this volume in the contents";
      a.innerHTML = '<span class="vol-dot" aria-hidden="true"></span>Volume ' + vol + " · " + NAMES[vol];
      var kicker = h1.previousElementSibling;
      var before = kicker && kicker.classList.contains("chapter-kicker") ? kicker : h1;
      before.parentNode.insertBefore(a, before);
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", addChip);
    } else {
      addChip();
    }
  })();

  // Figure out, from the current URL, whether chapter links need a
  // "chapters/" prefix (hub pages) or not (we are already inside chapters/).
  var inChaptersDir = /\/chapters\//.test(window.location.pathname);

  function hrefFor(slug) {
    return inChaptersDir ? slug : "chapters/" + slug;
  }

  function buildOverlay() {
    var overlay = document.createElement("div");
    overlay.className = "canon-search-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Search the Investor's Canon");
    overlay.hidden = true;

    overlay.innerHTML =
      '<div class="canon-search-panel">' +
        '<div class="canon-search-field">' +
          '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
          '<input type="text" class="canon-search-input" placeholder="Search chapter titles… (e.g. hydropower, tax, IPO)" aria-label="Search chapters" autocomplete="off">' +
          '<button type="button" class="canon-search-close" aria-label="Close search">&#10005;</button>' +
        '</div>' +
        '<p class="canon-search-hint">' + CHAPTERS.length + ' chapters. Type to filter — Enter opens the top result, Esc closes.</p>' +
        '<ul class="canon-search-results" role="listbox"></ul>' +
      '</div>';

    document.body.appendChild(overlay);
    return overlay;
  }

  function render(list, resultsEl) {
    if (!list.length) {
      resultsEl.innerHTML = '<li class="canon-search-empty">No chapter matches that. Try a different word.</li>';
      return;
    }
    var html = "";
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      html +=
        '<li>' +
          '<a href="' + hrefFor(c.s) + '" class="canon-search-result" role="option" data-idx="' + i + '">' +
            '<span class="csr-num">' + c.n + '</span>' +
            '<span class="csr-body"><span class="csr-title">' + c.t + '</span>' +
            '<span class="csr-part">' + c.p + '</span></span>' +
          '</a>' +
        '</li>';
    }
    resultsEl.innerHTML = html;
  }

  function filterChapters(query) {
    var q = query.trim().toLowerCase();
    if (!q) return CHAPTERS;
    return CHAPTERS.filter(function (c) {
      return c.t.toLowerCase().indexOf(q) !== -1 ||
             c.p.toLowerCase().indexOf(q) !== -1 ||
             c.n.toLowerCase().indexOf(q) !== -1;
    });
  }

  function init() {
    var trigger = document.querySelector(".nav-search-btn");
    if (!trigger) return;

    var overlay = null;
    var input, resultsEl, closeBtn;

    function open() {
      if (!overlay) {
        overlay = buildOverlay();
        input = overlay.querySelector(".canon-search-input");
        resultsEl = overlay.querySelector(".canon-search-results");
        closeBtn = overlay.querySelector(".canon-search-close");
        render(CHAPTERS, resultsEl);

        input.addEventListener("input", function () {
          render(filterChapters(input.value), resultsEl);
        });
        input.addEventListener("keydown", function (e) {
          if (e.key === "Escape") { close(); }
          if (e.key === "Enter") {
            var first = resultsEl.querySelector(".canon-search-result");
            if (first) window.location.href = first.getAttribute("href");
          }
        });
        closeBtn.addEventListener("click", close);
        overlay.addEventListener("click", function (e) {
          if (e.target === overlay) close();
        });
      }
      overlay.hidden = false;
      document.body.classList.add("canon-search-locked");
      input.value = "";
      render(CHAPTERS, resultsEl);
      setTimeout(function () { input.focus(); }, 0);
    }

    function close() {
      if (overlay) overlay.hidden = true;
      document.body.classList.remove("canon-search-locked");
      trigger.focus();
    }

    trigger.addEventListener("click", open);

    document.addEventListener("keydown", function (e) {
      // Keyboard shortcut: "/" opens search, same convention as many sites.
      if (e.key === "/" && !overlay) {
        var tag = (document.activeElement && document.activeElement.tagName) || "";
        if (tag !== "INPUT" && tag !== "TEXTAREA") {
          e.preventDefault();
          open();
        }
      } else if (e.key === "/" && overlay && overlay.hidden) {
        var tag2 = (document.activeElement && document.activeElement.tagName) || "";
        if (tag2 !== "INPUT" && tag2 !== "TEXTAREA") {
          e.preventDefault();
          open();
        }
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
