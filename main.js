/* ============================================================
   PARLEVU GLOBAL SERVICES LLC — Main JavaScript
   HubSpot CRM Portal ID: 246316495
   ============================================================ */

/* ── Meta pixel ──────────────────────────────────────────────
   Parlevu-Global-Investors-Pixel. Loaded here because every page
   includes main.js, so one copy covers the whole site and blog.
   One PageView per page; leads/calls/bookings are sent by track(). */
(function (f, b, e, v, n, t, s) {
  if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
  if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
  t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
})(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '924112438587196');
fbq('track', 'PageView');

document.addEventListener('DOMContentLoaded', function () {

  /* ── HubSpot CRM Integration ────────────────────────────── */
  const HS_PORTAL_ID = '246316495';


  /* -- Lead durability -------------------------------------
     The HubSpot tracking script is async+defer. A form submitted before it
     finishes loading only queues into a plain array, so redirecting on a
     fixed timer could discard the lead silently. These helpers keep a local
     copy until HubSpot has demonstrably taken over the queue. */
  const LEAD_STORE  = 'parlevu_pending_leads';
  const HS_MAX_WAIT = 4000;   // ms before redirecting regardless
  const HS_POLL     = 100;

  function readLeads() {
    try { return JSON.parse(localStorage.getItem(LEAD_STORE) || '[]'); }
    catch (e) { return []; }
  }

  function stashLead(data) {
    const ticket = 'lead_' + Date.now();
    try {
      const all = readLeads();
      all.push({ ticket: ticket, at: new Date().toISOString(), page: location.pathname, data: data });
      localStorage.setItem(LEAD_STORE, JSON.stringify(all.slice(-20)));
    } catch (e) { /* private mode or quota - submission still proceeds */ }
    return ticket;
  }

  function clearLead(ticket) {
    try {
      localStorage.setItem(LEAD_STORE,
        JSON.stringify(readLeads().filter(function (l) { return l.ticket !== ticket; })));
    } catch (e) { /* nothing to clean up */ }
  }

  // HubSpot swaps the plain _hsq array for its own object once loaded, so a
  // push that is no longer Array.prototype.push means it is live.
  function hubSpotReady() {
    const q = window._hsq;
    return !!(q && q.push && q.push !== Array.prototype.push);
  }

  function whenHubSpotReady(done) {
    if (hubSpotReady()) { done(true); return; }
    let waited = 0;
    const timer = setInterval(function () {
      waited += HS_POLL;
      if (hubSpotReady()) { clearInterval(timer); done(true); }
      else if (waited >= HS_MAX_WAIT) { clearInterval(timer); done(false); }
    }, HS_POLL);
  }

  // Anything a previous visit left behind gets one more attempt.
  function retryPendingLeads() {
    const pending = readLeads();
    if (!pending.length) return;
    whenHubSpotReady(function (ready) {
      if (!ready) return;
      pending.forEach(function (l) { pushToHubSpot(l.data); clearLead(l.ticket); });
    });
  }

  /* ── Lead attribution ───────────────────────────────────────
     Which channel produced a lead matters more than which page it
     fired on. First touch is kept for the life of the browser so a
     visitor who reads a post today and converts next week is still
     credited to the original source; last touch is per visit. */
  function readParams() {
    var q = {};
    try {
      new URLSearchParams(location.search).forEach(function (v, k) { q[k.toLowerCase()] = v; });
    } catch (e) { /* older browser - fall through to referrer only */ }
    return q;
  }

  function classify(q, ref) {
    if (q.utm_source) {
      return { source: q.utm_source, medium: q.utm_medium || 'unknown', campaign: q.utm_campaign || '' };
    }
    if (q.gclid) return { source: 'google', medium: 'cpc', campaign: '' };
    if (!ref) return { source: 'direct', medium: 'none', campaign: '' };
    var host = '';
    try { host = new URL(ref).hostname.replace(/^www\./, ''); } catch (e) { host = ref; }
    if (host === location.hostname.replace(/^www\./, '')) return null;   // internal click
    var search = /google\.|bing\.|duckduckgo\.|yahoo\./.test(host);
    var social = /facebook\.|instagram\.|linkedin\.|t\.co|x\.com|pinterest\./.test(host);
    return {
      source: host,
      medium: search ? 'organic' : (social ? 'social' : 'referral'),
      campaign: ''
    };
  }

  function attribution() {
    var q = readParams();
    var touch = classify(q, document.referrer);
    var now = new Date().toISOString().slice(0, 10);
    var first = null;
    try {
      if (touch) {
        sessionStorage.setItem('parlevu_last_touch', JSON.stringify(touch));
        if (!localStorage.getItem('parlevu_first_touch')) {
          localStorage.setItem('parlevu_first_touch',
            JSON.stringify({ source: touch.source, medium: touch.medium, campaign: touch.campaign, date: now }));
          localStorage.setItem('parlevu_landing', location.pathname.split('/').pop() || 'index.html');
        }
      }
      first = JSON.parse(localStorage.getItem('parlevu_first_touch') || 'null');
      if (!touch) touch = JSON.parse(sessionStorage.getItem('parlevu_last_touch') || 'null');
    } catch (e) { /* private mode - attribution degrades, lead still sends */ }
    touch = touch || { source: 'direct', medium: 'none', campaign: '' };
    first = first || { source: touch.source, medium: touch.medium, campaign: touch.campaign, date: now };
    var landing = 'index.html';
    try { landing = localStorage.getItem('parlevu_landing') || landing; } catch (e) {}
    return {
      lead_source: touch.source,
      lead_medium: touch.medium,
      lead_campaign: touch.campaign,
      first_source: first.source,
      first_medium: first.medium,
      first_seen: first.date,
      landing_page: landing
    };
  }

  // record the touch on every page view, not only on conversion
  attribution();

  /* ── Hermes lead API (record of truth) ─────────────────────
     Same endpoint the on-page offer forms use. The event_id is shared
     with the browser Lead event so Meta keeps one copy. Sheet and
     HubSpot stay as backups. */
  var LEAD_API = 'https://api.parlevugloballlc.com/v1/lead';

  function newEventId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, '');
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 12);
  }

  function cookieVal(n) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }

  function pushToHermes(data, formId, eventId, formMs, attr) {
    if (!window.fetch) return;
    try {
      var ga = cookieVal('_ga');
      var utm = {};
      if (attr.lead_medium !== 'none') {
        utm = { utm_source: attr.lead_source, utm_medium: attr.lead_medium, utm_campaign: attr.lead_campaign };
      }
      var notes = [];
      if (data.message) notes.push(data.message);
      notes.push('Form: ' + formId);
      fetch(LEAD_API, {
        method: 'POST',
        keepalive: true,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant: 'parlevu', magnet: formId, event_id: eventId,
          name: (data.name || '').trim(),
          email: (data.email || '').trim() || null,
          phone: (data.phone || '').trim() || null,
          address: (data.address || '').trim() || null,
          situation: data.situation || null,
          best_time: data.besttime || null,
          message: notes.join('\n').slice(0, 2000),
          hp: data.website || null,
          form_ms: formMs,
          ctx: {
            page: location.href.split('?')[0], landing_page: attr.landing_page,
            referrer: document.referrer || null, utm: utm,
            client_id: ga ? ga.split('.').slice(-2).join('.') : null,
            fbp: cookieVal('_fbp'), fbc: cookieVal('_fbc')
          }
        })
      }).catch(function () { /* Sheet + HubSpot still have it */ });
    } catch (e) { /* never block the form */ }
  }

  // Name plus a way to reach them; address helps but is not required.
  function leadProblem(data) {
    if (!(data.name || '').trim()) return 'Please add your name.';
    var email = (data.email || '').trim();
    var digits = (data.phone || '').replace(/\D/g, '');
    if (!email && !digits) return 'Please add a phone number or an email so we can send your offer.';
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'That email address looks incomplete.';
    if (digits && digits.length < 10) return 'Please enter a 10-digit phone number.';
    return null;
  }

  // Time from first keystroke to submit: the API ignores instant (bot) submits.
  var formStarted = {};
  document.addEventListener('input', function (e) {
    var f = e.target && e.target.form;
    if (f && f.id && !formStarted[f.id]) formStarted[f.id] = Date.now();
  }, true);

  function submitLead(data, formId) {
    var attr = attribution();
    var eventId = newEventId();
    var formMs = formStarted[formId] ? Date.now() - formStarted[formId] : 0;
    var params = { form_id: formId, page: location.pathname.split('/').pop() || 'index.html', event_id: eventId };
    for (var k in attr) { if (Object.prototype.hasOwnProperty.call(attr, k)) params[k] = attr[k]; }
    track('generate_lead', params);
    try { localStorage.setItem('pv_lead_done', '1'); } catch (e) { /* no exit offer after converting */ }
    const ticket = stashLead(data);
    pushToHermes(data, formId, eventId, formMs, attr);
    pushToSheet(data, params);
    pushToHubSpot(data);
    whenHubSpotReady(function (delivered) {
      if (delivered) clearLead(ticket);
      window.location.href = 'thank-you.html';
    });
  }

  // Google Apps Script web app -> "Parlevu Leads" sheet + email alert.
  // text/plain keeps this a "simple" CORS request (Apps Script can't answer a
  // preflight); keepalive lets it finish while the page moves to thank-you.html.
  var LEAD_SHEET_URL = 'https://script.google.com/macros/s/AKfycbwbb3aXQhrppEjJiVdPleQ_LakFX8X1-eYJK7UvhEr7Zj_XETG8P1v44cUpdghixVdv/exec';

  function pushToSheet(data, params) {
    if (!LEAD_SHEET_URL || !window.fetch) return;
    try {
      var body = {};
      var k;
      for (k in data) { if (Object.prototype.hasOwnProperty.call(data, k)) body[k] = data[k]; }
      for (k in params) { if (Object.prototype.hasOwnProperty.call(params, k)) body[k] = params[k]; }
      fetch(LEAD_SHEET_URL, {
        method: 'POST',
        mode: 'no-cors',
        keepalive: true,
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(body)
      }).catch(function () { /* backup only - never block the form */ });
    } catch (e) { /* backup only - never block the form */ }
  }

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
      const data = Object.fromEntries(new FormData(this).entries());
      if (showFormProblem(this, leadProblem(data))) return;
      const btn = this.querySelector('button[type="submit"]');
      btn.textContent = 'Submitting…';
      btn.disabled = true;
      submitLead(data, 'heroForm');
    });
  }

  /* ── Contact Form ───────────────────────────────────────── */
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(this).entries());
      if (showFormProblem(this, leadProblem(data))) return;
      const btn = this.querySelector('button[type="submit"]');
      btn.textContent = 'Sending…';
      btn.disabled = true;
      submitLead(data, 'contactForm');
    });
  }

  // Inline message above the submit button; returns true when there is a problem.
  function showFormProblem(form, msg) {
    var box = form.querySelector('.form-problem');
    if (!msg) { if (box) box.remove(); return false; }
    if (!box) {
      box = document.createElement('p');
      box.className = 'form-problem';
      box.setAttribute('role', 'alert');
      box.style.cssText = 'color:#b42318;font-weight:600;margin:4px 0 10px;font-size:.95rem';
      var btn = form.querySelector('button[type="submit"]');
      form.insertBefore(box, btn);
    }
    box.textContent = msg;
    track('form_error', { form_id: form.id, reason: msg.slice(0, 60) });
    return true;
  }

  /* ── Smooth Scroll for in-page anchors ──────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });


  /* ── Conversion tracking (GA4) ──────────────────────────────
     One delegated listener rather than per-link handlers, so it
     also covers links added after load. Fails silently if gtag
     is absent (e.g. consent tooling blocked it). */
  function track(name, params) {
    try {
      if (typeof gtag === 'function') gtag('event', name, params || {});
    } catch (e) { /* never let analytics break the page */ }
    // Same three actions to Meta, as standard events. No personal data is sent.
    var META = { generate_lead: 'Lead', phone_click: 'Contact', schedule_click: 'Schedule' };
    try {
      if (META[name] && typeof fbq === 'function') {
        var opts = params && params.event_id ? { eventID: params.event_id } : undefined;
        fbq('track', META[name], { content_name: (params && (params.form_id || params.page)) || '' }, opts);
      }
    } catch (e) { /* never let analytics break the page */ }
  }
  window.parlevuTrack = track;

  document.addEventListener('click', function (e) {
    const a = e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href') || '';
    const label = (a.textContent || '').trim().slice(0, 60);
    const where = location.pathname.split('/').pop() || 'index.html';

    if (href.startsWith('tel:')) {
      track('phone_click', { link_url: href, link_text: label, page: where });
    } else if (href.startsWith('mailto:')) {
      track('email_click', { link_url: href, link_text: label, page: where });
    } else if (href.indexOf('calendar.app.google') !== -1) {
      track('schedule_click', { link_url: href, link_text: label, page: where });
    }
  }, true);

window.addEventListener('load', retryPendingLeads);

  /* ── Book a Call (data-book-call) ───────────────────────── */
  document.querySelectorAll('[data-meet], [data-book-call]').forEach(el => {
    el.addEventListener('click', () => {
      track('schedule_click', { link_text: (el.textContent || 'book a call').trim().slice(0, 60), page: location.pathname.split('/').pop() || 'index.html' });
      window.open('https://calendar.app.google/hfm91n5jiLxXJHiu6', '_blank', 'noopener');
    });
  });

});
