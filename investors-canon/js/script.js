/**
 * The Investor's Canon — Master JavaScript
 * Handles reading progress, theme toggling, smooth scrolling, and mobile tooltips.
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  /* =========================================================
     1. Reading Progress Bar
     ========================================================= */
  const initProgressBar = () => {
    const progressBar = document.getElementById('reading-progress');
    if (!progressBar) return;

    const updateProgress = () => {
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrollTop = document.documentElement.scrollTop;
      const scrollPercentage = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
      progressBar.style.width = scrollPercentage + '%';
    };

    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress, { passive: true });
    updateProgress();
  };

  /* =========================================================
     2. Dark Mode Toggle (with LocalStorage)
     ========================================================= */
  const initThemeToggle = () => {
    const themeBtn = document.createElement('button');
    themeBtn.className = 'theme-toggle';
    themeBtn.setAttribute('aria-label', 'Toggle Dark Mode');
    themeBtn.innerHTML = '🌓';
    document.body.appendChild(themeBtn);

    const savedTheme = localStorage.getItem('canon-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }

    themeBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('canon-theme', newTheme);
    });
  };

  /* =========================================================
     3. Smooth Anchor Scrolling
     ========================================================= */
  const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          const headerOffset = 70; 
          const elementPosition = targetElement.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  };

  /* =========================================================
     4. Mobile Tooltip Support (Jargon)
     ========================================================= */
  const initMobileTooltips = () => {
    const jargons = document.querySelectorAll('.jargon');
    
    jargons.forEach(jargon => {
      jargon.addEventListener('touchstart', (e) => {
        jargons.forEach(j => { if (j !== jargon) j.classList.remove('active-tooltip') });
        jargon.classList.toggle('active-tooltip');
        e.stopPropagation();
      }, { passive: true });
    });

    document.addEventListener('touchstart', () => {
      jargons.forEach(j => j.classList.remove('active-tooltip'));
    }, { passive: true });
  };

  initProgressBar();
  initThemeToggle();
  initSmoothScroll();
  initMobileTooltips();
});