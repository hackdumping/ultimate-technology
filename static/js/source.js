(function () {
  function byId(id) { return document.getElementById(id); }

  function applyTheme(theme) {
    const isDark = theme === 'dark';
    document.body.classList.toggle('dark', isDark);
    const toggle = byId('themeToggle');
    if (toggle) {
      toggle.textContent = isDark ? '☀' : '◐';
      toggle.setAttribute('aria-label', isDark ? 'Activer mode clair' : 'Activer mode sombre');
    }
    localStorage.setItem('ut_theme', theme);
  }

  function initTheme() {
    const saved = localStorage.getItem('ut_theme');
    if (saved === 'dark' || saved === 'light') {
      applyTheme(saved);
      return;
    }
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
  }

  function initMobileNav() {
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    const mobileNav = byId('mobileNav');
    const closeBtn = byId('closeMobileNav');

    if (mobileBtn && mobileNav) {
      mobileBtn.addEventListener('click', function () {
        mobileNav.classList.add('open');
      });
    }

    if (closeBtn && mobileNav) {
      closeBtn.addEventListener('click', function () {
        mobileNav.classList.remove('open');
      });
    }

    document.addEventListener('click', function (event) {
      if (!mobileNav || !mobileBtn) return;
      if (!mobileNav.contains(event.target) && !mobileBtn.contains(event.target)) {
        mobileNav.classList.remove('open');
      }
    });
  }

  function initScrollTop() {
    const scrollBtn = document.querySelector('.scroll-btn');
    if (!scrollBtn) return;

    window.addEventListener('scroll', function () {
      scrollBtn.style.display = window.scrollY > 420 ? 'grid' : 'none';
    });
  }

  function initPasswordToggles() {
    document.querySelectorAll('[data-toggle-password]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var inputId = btn.getAttribute('data-toggle-password');
        var input = document.getElementById(inputId);
        if (!input) return;
        var isHidden = input.type === 'password';
        input.type = isHidden ? 'text' : 'password';
        var icon = btn.querySelector('i');
        if (icon) {
          icon.classList.toggle('fa-eye', !isHidden);
          icon.classList.toggle('fa-eye-slash', isHidden);
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();

    const toggle = byId('themeToggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        const next = document.body.classList.contains('dark') ? 'light' : 'dark';
        applyTheme(next);
      });
    }

    initMobileNav();
    initScrollTop();
    initPasswordToggles();
  });
})();
