// Progressive enhancement marker: CSS only hides .fade-in elements once
// this class is present, so content stays visible if this script fails.
document.documentElement.classList.add('js-enabled');

// ---------------------------------------------------------------------------
// Theme toggle (manual override on top of the FOUC-safe inline script in
// index.html's <head>, which already set data-theme before first paint).
// ---------------------------------------------------------------------------
const themeToggle = document.getElementById('themeToggle');
const iconSun = document.getElementById('iconSun');
const iconMoon = document.getElementById('iconMoon');
const htmlRoot = document.documentElement;

function syncThemeIcon(theme) {
  const isDark = theme === 'dark';
  // Announce both the current state and what activating the control will do.
  if (themeToggle) {
    themeToggle.setAttribute('aria-pressed', String(isDark));
    themeToggle.setAttribute(
      'aria-label',
      isDark ? 'Switch to light theme' : 'Switch to dark theme'
    );
  }
  if (!iconSun || !iconMoon) return;
  iconSun.style.display = isDark ? 'block' : 'none';
  iconMoon.style.display = isDark ? 'none' : 'block';
}

syncThemeIcon(htmlRoot.getAttribute('data-theme'));

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const next = htmlRoot.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    htmlRoot.setAttribute('data-theme', next);
    syncThemeIcon(next);
    try {
      localStorage.setItem('theme', next);
    } catch (e) {
      // Private browsing / storage disabled — theme just won't persist.
    }
  });
}

// ---------------------------------------------------------------------------
// Mobile nav: toggle, focus trap, Escape key, resize-safe close.
// ---------------------------------------------------------------------------
const navToggle = document.getElementById('navToggle');
const siteNav = document.getElementById('siteNav');

if (navToggle && siteNav) {
  const desktopQuery = window.matchMedia('(min-width: 721px)');

  const getFocusableEls = () =>
    siteNav.querySelectorAll('a[href], button, [tabindex]:not([tabindex="-1"])');

  const setNavOpen = (isOpen, moveFocus) => {
    siteNav.classList.toggle('open', isOpen);
    navToggle.setAttribute('aria-expanded', String(isOpen));
    // Hide the panel from assistive tech when it is visually closed, but only
    // in the mobile layout — on desktop the nav is always on screen.
    if (!desktopQuery.matches) {
      siteNav.setAttribute('aria-hidden', String(!isOpen));
    } else {
      siteNav.removeAttribute('aria-hidden');
    }
    // Opening a menu should put the user inside it, otherwise a keyboard user
    // has to tab back through the header to reach what they just opened.
    if (isOpen && moveFocus) {
      const focusable = getFocusableEls();
      if (focusable.length) { focusable[0].focus(); }
    }
  };

  navToggle.addEventListener('click', () => {
    setNavOpen(!siteNav.classList.contains('open'), true);
  });

  siteNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setNavOpen(false, false));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && siteNav.classList.contains('open')) {
      setNavOpen(false, false);
      navToggle.focus();
    }
  });

  siteNav.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab' || !siteNav.classList.contains('open')) return;

    const focusable = getFocusableEls();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });

  desktopQuery.addEventListener('change', (e) => {
    if (e.matches) {
      siteNav.removeAttribute('aria-hidden');
      if (siteNav.classList.contains('open')) { setNavOpen(false); }
    } else {
      siteNav.setAttribute('aria-hidden', String(!siteNav.classList.contains('open')));
    }
  });
}

// ---------------------------------------------------------------------------
// Skip link: move keyboard focus to main content, not just scroll to it.
// ---------------------------------------------------------------------------
const skipLink = document.querySelector('.skip-link');
const mainContent = document.getElementById('main');
if (skipLink && mainContent) {
  skipLink.addEventListener('click', () => {
    mainContent.focus();
  });
}

// ---------------------------------------------------------------------------
// Footer year
// ---------------------------------------------------------------------------
const yearEl = document.getElementById('year');
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// ---------------------------------------------------------------------------
// Scroll-reveal fade-in. Guarded so a browser without IntersectionObserver
// just shows everything immediately instead of staying hidden.
// ---------------------------------------------------------------------------
const fadeEls = document.querySelectorAll('.fade-in');
if (fadeEls.length && 'IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

  fadeEls.forEach((el) => revealObserver.observe(el));
} else {
  fadeEls.forEach((el) => el.classList.add('visible'));
}

// ---------------------------------------------------------------------------
// Scrollspy: highlight the nav link matching whichever section is in view.
// Uses a scroll-position check (the section whose top has crossed a fixed
// line near the top of the viewport) rather than IntersectionObserver —
// simpler to reason about and avoids edge cases when a section is taller
// than the observer's margin-shrunk root. Nav still works as plain anchor
// links even if any of this fails.
// ---------------------------------------------------------------------------
const navLinks = document.querySelectorAll('[data-nav-link]');
if (navLinks.length) {
  const linksBySection = new Map();
  navLinks.forEach((link) => {
    const id = link.getAttribute('href').slice(1);
    const section = document.getElementById(id);
    if (section) linksBySection.set(section, link);
  });
  const sections = Array.from(linksBySection.keys());

  const setActiveLink = (activeLink) => {
    navLinks.forEach((link) => link.classList.toggle('is-active', link === activeLink));
  };

  const ACTIVE_LINE = 120; // px from the top of the viewport

  const updateActiveSection = () => {
    // Walk sections top-to-bottom; the active one is the last whose top has
    // already crossed above the active line (i.e. it's the section we're
    // currently "inside" while scrolling down).
    let current = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top - ACTIVE_LINE <= 0) {
        current = section;
      }
    }
    const activeLink = linksBySection.get(current);
    if (activeLink) setActiveLink(activeLink);
  };

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => {
      updateActiveSection();
      ticking = false;
    });
  }, { passive: true });

  updateActiveSection();
}
