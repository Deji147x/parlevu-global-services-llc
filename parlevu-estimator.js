/* Parlevu lead magnets: home-value estimator + free valuation request.
 * Mount:  <div data-parlevu-magnet="estimator"></div>   or   data-parlevu-magnet="valuation"
 *         <script src="/parlevu-estimator.js?v=1" defer data-api="https://api.parlevugloballlc.com"></script>
 * Every step sends one event_id to the browser (gtag + fbq) and the Lead API (server copy), so Meta dedupes.
 */
(function () {
  "use strict";
  var script = document.currentScript;
  var API = (script && script.getAttribute("data-api")) || "https://api.parlevugloballlc.com";
  var TENANT = "parlevu";
  var BOOK_URL = (script && script.getAttribute("data-book")) || "https://calendar.app.google/hfm91n5jiLxXJHiu6";
  var SMS_TEXT = "Yes, Parlevu Global Services may text me about my property. Msg & data rates may apply. " +
    "Reply STOP to opt out. Consent is not required to sell.";

  function uid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "");
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 12);
  }
  function cookie(n) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + n + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }
  function gaClientId() {
    var g = cookie("_ga");
    return g ? g.split(".").slice(-2).join(".") : null;
  }
  function utm() {
    var out = {}, p = new URLSearchParams(location.search);
    ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"].forEach(function (k) {
      if (p.get(k)) out[k] = p.get(k);
    });
    try {
      if (Object.keys(out).length) sessionStorage.setItem("pv_utm", JSON.stringify(out));
      else out = JSON.parse(sessionStorage.getItem("pv_utm") || "{}");
      if (!sessionStorage.getItem("pv_landing")) sessionStorage.setItem("pv_landing", location.pathname);
    } catch (e) {}
    return out;
  }
  function ctx() {
    var landing = null;
    try { landing = sessionStorage.getItem("pv_landing"); } catch (e) {}
    return { page: location.href.split("?")[0], landing_page: landing, referrer: document.referrer || null,
             utm: utm(), client_id: gaClientId(), fbp: cookie("_fbp"), fbc: cookie("_fbc") };
  }
  function post(path, body) {
    return fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" },
                               body: JSON.stringify(body), keepalive: true })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { j._status = r.status; return j; }); });
  }
  function track(name, params, metaName) {
    var id = uid();
    params = params || {};
    if (window.gtag) gtag("event", name, Object.assign({ event_id: id }, params));
    if (window.fbq && metaName) fbq("track", metaName, params, { eventID: id });
    post("/v1/event", { tenant: TENANT, name: name, event_id: id, params: params, ctx: ctx() }).catch(function () {});
    return id;
  }
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function el(html) { var d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; }

  var CSS = ".pvm{max-width:560px;margin:0 auto;text-align:left;padding:24px;border-radius:14px;background:#0b1a2e;color:#fff;" +
    "font-family:inherit;box-shadow:0 10px 30px rgba(0,0,0,.18)}.pvm h3{margin:0 0 6px;font-size:1.35rem;color:#fff !important}" +
    ".pvm p.sub{margin:0 0 16px;color:#c9d3e0;font-size:.95rem}.pvm label{display:block;font-size:.85rem;margin:10px 0 4px;color:#dfe6ef}" +
    ".pvm input,.pvm select,.pvm textarea{width:100%;box-sizing:border-box;padding:11px 12px;border-radius:8px;border:1px solid #33465f;" +
    "background:#10243d;color:#fff;font-size:1rem}.pvm .row{display:flex;gap:10px}.pvm .row>div{flex:1}" +
    ".pvm button{margin-top:16px;width:100%;padding:13px;border:0;border-radius:8px;background:#d4a843;color:#0b1a2e;" +
    "font-weight:700;font-size:1rem;cursor:pointer}.pvm button[disabled]{opacity:.6}.pvm .chk{display:flex;gap:8px;align-items:flex-start;" +
    "font-size:.8rem;color:#c9d3e0;margin-top:12px}.pvm .chk input{width:auto;margin-top:2px}.pvm .hp{position:absolute;left:-9999px}" +
    ".pvm .err{color:#ffb4a8;font-size:.85rem;margin-top:8px}.pvm .big{font-size:1.8rem;font-weight:800;color:#d4a843;margin:8px 0}" +
    ".pvm .fine{font-size:.78rem;color:#9fb0c5;margin-top:10px}@media(max-width:480px){.pvm .row{flex-direction:column;gap:0}}";

  function injectCss() {
    if (document.getElementById("pvm-css")) return;
    var s = document.createElement("style"); s.id = "pvm-css"; s.textContent = CSS; document.head.appendChild(s);
  }

  function contactFields() {
    return '<label>Your name</label><input name="name" autocomplete="name" required maxlength="120">' +
      '<div class="row"><div><label>Email</label><input name="email" type="email" autocomplete="email" maxlength="120"></div>' +
      '<div><label>Phone</label><input name="phone" type="tel" autocomplete="tel" maxlength="30"></div></div>' +
      '<label class="chk"><input type="checkbox" name="sms"> <span>' + SMS_TEXT + '</span></label>' +
      '<div class="hp" aria-hidden="true"><input name="website" tabindex="-1" autocomplete="off"></div>';
  }

  var startedMagnets = {};
  function attachStart(root, magnet) {
    var started = 0;
    linkLabels(root);
    root.addEventListener("input", function () {
      if (!started) started = Date.now();
      if (!startedMagnets[magnet]) { startedMagnets[magnet] = 1; track("magnet_start", { magnet: magnet }); }
    });
    return function () { return started ? Date.now() - started : 0; };
  }
  // Tie each <label> to the field after it, so screen readers and taps on the label work.
  var fieldSeq = 0;
  function linkLabels(root) {
    root.querySelectorAll("label:not(.chk)").forEach(function (lb) {
      var f = lb.nextElementSibling;
      if (f && /INPUT|SELECT|TEXTAREA/.test(f.tagName)) {
        if (!f.id) f.id = "pvm-f" + (++fieldSeq);
        lb.htmlFor = f.id;
      }
    });
  }

  function watchView(root, magnet) {
    if (!("IntersectionObserver" in window)) { track("magnet_view", { magnet: magnet }, "ViewContent"); return; }
    var io = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { io.disconnect(); track("magnet_view", { magnet: magnet }, "ViewContent"); }
    }, { threshold: 0.4 });
    io.observe(root);
  }

  function submitLead(form, magnet, extra, formMs) {
    var f = new FormData(form), eventId = uid();
    var body = Object.assign({
      tenant: TENANT, magnet: magnet, event_id: eventId,
      name: (f.get("name") || "").trim(), email: (f.get("email") || "").trim() || null,
      phone: (f.get("phone") || "").trim() || null, sms_opt_in: !!f.get("sms"),
      sms_consent_text: f.get("sms") ? SMS_TEXT : null, hp: f.get("website") || null,
      form_ms: formMs(), ctx: ctx()
    }, extra);
    if (!body.email && !body.phone) return Promise.reject(new Error("Please add an email or phone number."));
    return post("/v1/lead", body).then(function (r) {
      if (!r.ok) throw new Error((r.detail && r.detail[0] && r.detail[0].msg) || "Something went wrong. Please call us.");
      // Browser copy of the same Lead, same event_id → Meta keeps one.
      if (window.gtag) gtag("event", "generate_lead", { event_id: eventId, magnet: magnet });
      if (window.fbq) fbq("track", "Lead", { content_name: magnet }, { eventID: eventId });
      if (magnet === "valuation") {
        if (window.gtag) gtag("event", "valuation_request", { event_id: eventId });
        if (window.fbq) fbq("track", "Schedule", {}, { eventID: eventId });
      }
      return r;
    });
  }

  function mountEstimator(root) {
    var magnet = "estimator", step1 = {};
    root.innerHTML = "";
    var box = el('<div class="pvm"><h3>What could your house sell for as-is?</h3>' +
      '<p class="sub">Free, no obligation. See a market-value range for your property in under a minute.</p>' +
      '<form novalidate><label>Property address</label><input name="address" autocomplete="street-address" required maxlength="200">' +
      '<div class="row"><div><label>ZIP code</label><input name="zip" inputmode="numeric" maxlength="5" required></div>' +
      '<div><label>Condition</label><select name="condition"><option value="good">Good, move-in ready</option>' +
      '<option value="fair" selected>Fair, needs updates</option><option value="needs work">Needs work</option>' +
      '<option value="major repairs">Major repairs</option></select></div></div>' +
      '<div class="row"><div><label>When do you want to sell?</label><select name="timeline"><option value="asap">As soon as possible</option>' +
      '<option value="30-60">30–60 days</option><option value="3-6 months">3–6 months</option><option value="just exploring">Just exploring</option></select></div>' +
      '<div><label>Your situation</label><select name="situation"><option value="">Prefer not to say</option><option value="inherited">Inherited the house</option>' +
      '<option value="relocating">Relocating</option><option value="tired landlord">Tired landlord</option><option value="divorce">Divorce</option>' +
      '<option value="behind on payments">Behind on payments</option><option value="vacant">House is vacant</option><option value="other">Other</option></select></div></div>' +
      '<label class="chk"><input type="checkbox" name="owner" checked> <span>I own this property (or I\'m the heir)</span></label>' +
      '<button type="submit">See my range →</button><div class="err"></div></form></div>');
    root.appendChild(box);
    var form = box.querySelector("form"), err = box.querySelector(".err"), formMs = attachStart(form, magnet);
    watchView(box, magnet);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var f = new FormData(form);
      if (!f.get("address") || !/^\d{5}$/.test(f.get("zip") || "")) { err.textContent = "Please add the address and a 5-digit ZIP."; return; }
      step1 = { address: f.get("address").trim(), zip: f.get("zip"), condition: f.get("condition"),
                timeline: f.get("timeline"), situation: f.get("situation") || null, is_owner: !!f.get("owner") };
      showContact();
    });

    function showContact() {
      box.innerHTML = '<h3>Where should we send your range?</h3><p class="sub">We\'ll show it on the next screen and email you a copy.</p>' +
        '<form novalidate>' + contactFields() + '<button type="submit">Show my range</button><div class="err"></div>' +
        '<p class="fine">We never sell your information. By continuing you agree we may contact you about your property.</p></form>';
      var f2 = box.querySelector("form"), err2 = box.querySelector(".err"), ms = attachStart(f2, magnet), btn = f2.querySelector("button");
      f2.addEventListener("submit", function (e) {
        e.preventDefault(); err2.textContent = ""; btn.disabled = true;
        submitLead(f2, magnet, step1, function () { return Math.max(ms(), formMs()); }).then(function (r) {
          return post("/v1/estimate", { tenant: TENANT, lead_id: r.lead_id, address: step1.address, zip: step1.zip, condition: step1.condition });
        }).then(showResult).catch(function (x) { err2.textContent = x.message; btn.disabled = false; });
      });
    }

    function showResult(r) {
      if (!r.ok) {
        box.innerHTML = '<h3>Thanks, we\'ve got it.</h3><p class="sub">' + (r.message || "We'll review your property by hand and reach out within one business day.") + '</p>';
        return;
      }
      track("estimate_shown", { magnet: magnet });
      var html = '<h3>Estimated market value</h3><div class="big">' + money(r.value_low) + ' – ' + money(r.value_high) + '</div>';
      if (r.offer_low != null) html += '<p class="sub">Typical as-is cash range for this condition: <b>' + money(r.offer_low) + ' – ' + money(r.offer_high) + '</b></p>';
      html += '<p class="sub">Want a firm number? We\'ll do a quick walkthrough and send a written offer.</p>' +
        '<button type="button" data-book>Book a free walkthrough</button><p class="fine">' + r.disclaimer + '</p>';
      box.innerHTML = html;
      box.querySelector("[data-book]").addEventListener("click", function () {
        if (window.gtag) gtag("event", "book_click", { magnet: magnet });
        window.open(BOOK_URL, "_blank", "noopener");
      });
    }
  }

  function mountValuation(root) {
    var magnet = "valuation";
    root.innerHTML = "";
    var box = el('<div class="pvm"><h3>Request a free home valuation</h3>' +
      '<p class="sub">A local specialist reviews your property and calls you with a value. No obligation.</p>' +
      '<form novalidate><label>Property address</label><input name="address" autocomplete="street-address" maxlength="200" required>' +
      '<div class="row"><div><label>ZIP code</label><input name="zip" inputmode="numeric" maxlength="5"></div>' +
      '<div><label>Best time to call</label><select name="best_time"><option>Morning</option><option>Afternoon</option><option>Evening</option></select></div></div>' +
      contactFields() + '<button type="submit">Request my valuation</button><div class="err"></div></form></div>');
    root.appendChild(box);
    var form = box.querySelector("form"), err = box.querySelector(".err"), ms = attachStart(form, magnet), btn = form.querySelector("button");
    watchView(box, magnet);
    form.addEventListener("submit", function (e) {
      e.preventDefault(); err.textContent = "";
      var f = new FormData(form);
      if (!f.get("address")) { err.textContent = "Please add the property address."; return; }
      btn.disabled = true;
      submitLead(form, magnet, { address: f.get("address").trim(), zip: f.get("zip") || null, best_time: f.get("best_time") }, ms)
        .then(function () { box.innerHTML = '<h3>Request received.</h3><p class="sub">We\'ll call you at your preferred time, usually within one business day.</p>'; })
        .catch(function (x) { err.textContent = x.message; btn.disabled = false; });
    });
  }

  function init() {
    injectCss(); utm();
    document.querySelectorAll("[data-parlevu-magnet]").forEach(function (n) {
      var kind = n.getAttribute("data-parlevu-magnet");
      if (kind === "estimator") mountEstimator(n); else if (kind === "valuation") mountValuation(n);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
