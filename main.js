/* ============================================================
   PARLEVU GLOBAL SERVICES LLC — Main JavaScript
   HubSpot CRM Portal ID: 246316495
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── HubSpot CRM Integration ────────────────────────────── */
  const HS_PORTAL_ID = '246316495';

  function pushToHubSpot(data) {
    try {
      const _hsq = window._hsq = window._hsq || [];
      const nameParts = (data.name || '').trim().split(/\s+/);
      _hsq.push(['identify', {
        email:          data.email               || '',
        firstname:      nameParts[0]             || '',
        lastname:       nameParts.slice(1).join(' ') || '',
        phone:          data.phone               || '',
        address:        data.address             || '',
        hs_lead_status: 'NEW',
      }]);
      _hsq.push(['trackPageView']);

      // Optional: also submit via HubSpot Forms API once you create
      // a form in HubSpot and get its GUID. Replace FORM_GUID below:
      //
      // const FORM_GUID = 'YOUR_HUBSPOT_FORM_GUID';
      // fetch(`https://api.hsforms.com/submissions/v3/integration/submit/${HS_PORTAL_ID}/${FORM_GUID}`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     fields: [
      //       { name: 'firstname',  value: nameParts[0] || '' },
      //       { name: 'lastname',   value: nameParts.slice(1).join(' ') || '' },
      //       { name: 'email',      value: data.email   || '' },
      //       { name: 'phone',      value: data.phone   || '' },
      //       { name: 'address',    value: data.address || '' },
      //       { name: 'message',    value: data.message || '' },
      //     ],
      //     context: { pageUri: window.location.href, pageName: document.title }
      //   })
      // });
    } catch (e) {
      // HubSpot not yet loaded — contact still queued via tracking code
    }
  }

  /* ── Mobile Nav ─────────────────────────────────────────── */
  const hamburger = document.querySelector('.hamburger');
  const mobileNav = document.querySelector('.mobile-nav');

  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      mobileNav.classList.toggle('open');
    });
    mobileNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        hamburger.classList.remove('active');
        mobileNav.classList.remove('open');
      });
    });
  }

  /* ── Active Nav Link ────────────────────────────────────── */
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.navbar-nav a, .mobile-nav a').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });

  /* ── Sticky Nav Shadow ──────────────────────────────────── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 30
        ? '0 4px 35px rgba(0,0,0,.5)'
        : '0 2px 24px rgba(0,0,0,.35)';
    }, { passive: true });
  }

  /* ── FAQ Accordion ──────────────────────────────────────── */
  document.querySelectorAll('.faq-question').forEach(q => {
    q.addEventListener('click', function () {
      const item = this.closest('.faq-item');
      const isOpen = item.classList.contains('active');
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
      if (!isOpen) item.classList.add('active');
    });
  });

  /* ── Scroll Reveal ──────────────────────────────────────── */
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const ro = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('visible'); ro.unobserve(e.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(el => ro.observe(el));
  }

  /* ── Counter Animations ─────────────────────────────────── */
  const counters = document.querySelectorAll('.counter');
  if (counters.length) {
    const co = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        const el = e.target;
        const target = +el.dataset.target;
        const suffix = el.dataset.suffix || '';
        const prefix = el.dataset.prefix || '';
        let current = 0;
        const inc = target / 55;
        const t = setInterval(() => {
          current += inc;
          if (current >= target) { el.textContent = prefix + target + suffix; clearInterval(t); }
          else el.textContent = prefix + Math.floor(current) + suffix;
        }, 18);
        co.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(c => co.observe(c));
  }

  /* ── Hero Form ──────────────────────────────────────────── */
  const heroForm = document.getElementById('heroForm');
  if (heroForm) {
    heroForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = this.querySelector('button[type="submit"]');
      btn.textContent = 'Submitting…';
      btn.disabled = true;

      const data = Object.fromEntries(new FormData(this).entries());
      pushToHubSpot(data);                       // → HubSpot CRM contact created

      setTimeout(() => { window.location.href = 'thank-you.html'; }, 900);
    });
  }

  /* ── Contact Form ───────────────────────────────────────── */
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = this.querySelector('button[type="submit"]');
      btn.textContent = 'Sending…';
      btn.disabled = true;

      const data = Object.fromEntries(new FormData(this).entries());
      pushToHubSpot(data);                       // → HubSpot CRM contact created

      setTimeout(() => { window.location.href = 'thank-you.html'; }, 1000);
    });
  }

  /* ── Smooth Scroll for in-page anchors ──────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

  /* ── Book a Call (data-book-call) ───────────────────────── */
  document.querySelectorAll('[data-meet], [data-book-call]').forEach(el => {
    el.addEventListener('click', () => window.open('https://calendar.app.google/hfm91n5jiLxXJHiu6', '_blank', 'noopener'));
  });

});
