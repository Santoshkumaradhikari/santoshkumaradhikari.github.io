// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const siteNav = document.getElementById('siteNav');

if (navToggle && siteNav) {
  const getFocusableEls = () =>
    siteNav.querySelectorAll('a[href], button, [tabindex]:not([tabindex="-1"])');

  const setNavOpen = (isOpen) => {
    siteNav.classList.toggle('open', isOpen);
    navToggle.setAttribute('aria-expanded', String(isOpen));
  };

  navToggle.addEventListener('click', () => {
    setNavOpen(!siteNav.classList.contains('open'));
  });

  siteNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setNavOpen(false));
  });

  // Escape closes the menu and returns focus to the toggle button
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && siteNav.classList.contains('open')) {
      setNavOpen(false);
      navToggle.focus();
    }
  });

  // Keep Tab focus cycling inside the open mobile menu
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

  // If the window is resized past the mobile breakpoint while the menu
  // is open, close it so it can't get stuck open behind desktop styles.
  const desktopQuery = window.matchMedia('(min-width: 721px)');
  desktopQuery.addEventListener('change', (e) => {
    if (e.matches && siteNav.classList.contains('open')) {
      setNavOpen(false);
    }
  });
}

// Skip link: move keyboard focus to main content, not just scroll to it
const skipLink = document.querySelector('.skip-link');
const mainContent = document.getElementById('main');
if (skipLink && mainContent) {
  skipLink.addEventListener('click', () => {
    mainContent.focus();
  });
}

// Footer year
const yearEl = document.getElementById('year');
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}
