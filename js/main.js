(function () {
  'use strict';

  // ---- Menu mobile ----
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.querySelector('.nav');
  var overlay = document.querySelector('.nav-overlay');

  function closeNav() {
    if (!nav) return;
    nav.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '☰';
    }
  }

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var isOpen = nav.classList.toggle('open');
      if (overlay) overlay.classList.toggle('open', isOpen);
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      toggle.textContent = isOpen ? '✕' : '☰';
    });
  }

  if (overlay) overlay.addEventListener('click', closeNav);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeNav();
  });

  // ---- Apparition au défilement ----
  var fadeEls = document.querySelectorAll('.fade-in');
  if (fadeEls.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    Array.prototype.forEach.call(fadeEls, function (el) { observer.observe(el); });
  } else {
    Array.prototype.forEach.call(fadeEls, function (el) { el.classList.add('visible'); });
  }

  // ---- Lien de navigation actif ----
  var path = window.location.pathname.replace(/\/$/, '');
  Array.prototype.forEach.call(
    document.querySelectorAll('.nav a:not(.lang-switch)'),
    function (link) {
      var href = link.getAttribute('href').replace(/\/$/, '');
      if (href === path) link.classList.add('active');
    }
  );
})();
