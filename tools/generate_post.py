"""Generate one SEO blog post HTML from a content-calendar.json brief.

Content strategy: 100% ORIGINAL content. Competitor research informed the
topic/keyword selection in the calendar; nothing is copied from any site.

Text engine: local Ollama (llama3.2, free) via http://localhost:11434.
If Ollama is down or returns unusable output, a built-in deterministic
writer produces the post from original parameterized copy, so the daily
cron never publishes a broken/empty page.

Target length: 2000-3000 characters of body text (per site owner's spec).

Usage:  python tools/generate_post.py <slug> [--out blog-<slug>.html]
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
TEMPLATE = REPO / "tools" / "post_template.html"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
CHAR_MIN, CHAR_MAX = 2000, 3000

STATE_FACTS = {
    "MD": {
        "name": "Maryland",
        "disclosure": "Maryland requires the Seller's Disclosure and Disclaimer Statement for residential sales — even in as-is sales, known material defects must be disclosed.",
        "foreclosure": "Maryland foreclosures are quasi-judicial and can move from Notice of Intent to auction in as little as 90-120 days, but homeowners can sell at any point before the auction.",
        "transfer": "Maryland transfer and recordation taxes typically total 1.5-3% depending on the county; cash buyers like Parlevu often structure offers so sellers keep more at closing.",
    },
    "VA": {
        "name": "Virginia",
        "disclosure": "Virginia is a 'buyer beware' state using the Residential Property Disclosure Statement, but sellers still cannot actively conceal known defects.",
        "foreclosure": "Virginia uses fast non-judicial foreclosure — a home can go from notice to auction in under 60 days, so acting early matters more here than almost anywhere.",
        "transfer": "Virginia's grantor tax and regional congestion taxes are modest, and in a cash sale there are no lender fees at all.",
    },
    "DC": {
        "name": "Washington DC",
        "disclosure": "DC requires a Seller's Property Condition Disclosure for most residential sales, and pre-1978 homes carry federal lead-paint disclosure duties.",
        "foreclosure": "DC foreclosures are judicial and slower than in Maryland or Virginia, but interest, fees, and stress compound the longer you wait.",
        "transfer": "DC transfer and recordation taxes are among the region's highest (up to 2.9% combined), which makes avoiding agent commissions especially valuable.",
    },
}

CTA_TEXT = {
    "offer": ("Get a Fair Cash Offer on Your {place} Home",
              "No repairs. No cleaning. No showings. We buy {place} homes in any condition and close on your schedule."),
    "consult": ("Talk Through Your Options — Free, No Pressure",
                "Every situation is different. Book a free consultation and we'll walk through what your {place} home could sell for — cash offer or otherwise."),
    "call": ("Need to Sell Your {place} House Fast? Let's Talk Today",
             "One call gets you a real number. We answer, we show up, and we close when you're ready."),
}

STATIC_POSTS = [
    ("blog-we-buy-houses.html", "Selling Tips", "What Does \"We Buy Houses\" Really Mean?"),
    ("blog-foreclosure-prevention.html", "Foreclosure Help", "Foreclosure Prevention: Your Options as a Baltimore Homeowner"),
    ("blog-inherited-property.html", "Inherited Properties", "How to Sell an Inherited Property in Baltimore"),
    ("blog-selling-as-is.html", "As-Is Sales", "Selling an As-Is Property in Baltimore"),
    ("blog-fsbo-vs-agent.html", "FSBO Guide", "FSBO vs. Traditional Agent"),
]


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def place_of(brief) -> str:
    return brief["city"] or STATE_FACTS[brief["state"]]["name"]


# ---------------------------------------------------------------- Ollama ----
def ollama_generate(brief) -> dict | None:
    facts = STATE_FACTS[brief["state"]]
    place = place_of(brief)
    prompt = f"""You are an expert real-estate content writer for Parlevu Global Services LLC,
a cash home buying company serving Maryland, Virginia and Washington DC.
Write an ORIGINAL blog post. Do not copy any existing text.

Topic/title: {brief['title']}
Primary SEO keyword (use naturally 3-4 times): {brief['primary_keyword']}
Secondary keywords (use each once): {', '.join(brief['secondary_keywords'])}
Location focus: {place}
Local fact to weave in: {facts['disclosure']} {facts['foreclosure']}
Tone: helpful, direct, empathetic, expert. Audience: homeowner who needs to sell.
Total body length across intro+sections: 1800 to 2600 characters. Short punchy paragraphs.

Respond with ONLY valid JSON in exactly this shape:
{{"meta_desc": "150-char meta description containing the primary keyword",
 "intro": "2-3 sentence opening that names the reader's situation",
 "sections": [
   {{"heading": "question-style H2", "paragraphs": ["...", "..."]}},
   {{"heading": "question-style H2", "paragraphs": ["..."]}},
   {{"heading": "question-style H2", "paragraphs": ["..."]}}
 ],
 "faqs": [
   {{"q": "...", "a": "2-3 sentence answer"}},
   {{"q": "...", "a": "2-3 sentence answer"}},
   {{"q": "...", "a": "2-3 sentence answer"}}
 ]}}"""
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps({"model": OLLAMA_MODEL, "prompt": prompt,
                             "stream": False, "format": "json",
                             "options": {"temperature": 0.7, "num_predict": 2500}}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read())["response"]
        return normalize(json.loads(data), brief)
    except Exception as e:
        print(f"  ollama unavailable/invalid ({type(e).__name__}: {e}); using built-in writer")
        return None


def normalize(raw, brief):
    """Coerce a loosely-shaped model response into the expected structure,
    filling any gaps from the fallback writer. Returns None if unsalvageable."""
    fb = fallback_generate(brief)
    if not isinstance(raw, dict):
        return None
    post = {
        "meta_desc": str(raw.get("meta_desc") or fb["meta_desc"])[:158],
        "intro": str(raw.get("intro") or fb["intro"]),
        "sections": [],
        "faqs": [],
    }
    for s in raw.get("sections") or []:
        if not isinstance(s, dict):
            continue
        heading = s.get("heading") or s.get("title") or s.get("h2")
        paras = s.get("paragraphs") or s.get("content") or s.get("text")
        if isinstance(paras, str):
            paras = [paras]
        paras = [str(p) for p in (paras or []) if str(p).strip()]
        if heading and paras:
            post["sections"].append({"heading": str(heading), "paragraphs": paras})
    for f in raw.get("faqs") or []:
        if not isinstance(f, dict):
            continue
        q = f.get("q") or f.get("question")
        a = f.get("a") or f.get("answer")
        if q and a:
            post["faqs"].append({"q": str(q), "a": str(a)})
    if not post["sections"]:
        return None  # nothing usable — use fallback entirely
    # fit_length() tops up short posts with fallback sections afterwards
    while len(post["faqs"]) < 3:
        post["faqs"].append(fb["faqs"][len(post["faqs"]) % len(fb["faqs"])])
    return post


# ------------------------------------------------------- Fallback writer ----
def fallback_generate(brief) -> dict:
    """Original parameterized copy — never copied from any external source."""
    place = place_of(brief)
    st = STATE_FACTS[brief["state"]]
    kw = brief["primary_keyword"]
    topic = brief["title"].split(":")[0].rstrip("?")
    return {
        "meta_desc": f"{topic} — what {place} homeowners need to know, plus how to get a fair cash offer with no repairs, fees, or delays. {kw}."[:158],
        "intro": (f"If you're searching for \"{kw}\", you're probably under some pressure — a deadline, "
                  f"a property that needs work, or a situation that can't wait for a 90-day listing. "
                  f"The good news: {place} homeowners have more options than most people realize, and "
                  f"some of them can put cash in your hands in under two weeks."),
        "sections": [
            {"heading": f"What {place} Homeowners Should Know First",
             "paragraphs": [
                 f"{st['disclosure']} That matters no matter how you sell — to a cash buyer, "
                 f"through an agent, or on your own. Being upfront about the property's condition "
                 f"protects you legally and actually speeds up a cash sale, because investors "
                 f"price the repairs in from day one.",
                 f"{st['foreclosure']} Timing is the single biggest lever you control. The earlier "
                 f"you explore your options, the more of them you have."]},
            {"heading": "How a Cash Sale Actually Works",
             "paragraphs": [
                 "The process is simpler than most sellers expect: you share the property address "
                 "and a few details, receive a written offer (usually within 24-48 hours), pick "
                 "your own closing date, and sell completely as-is — no repairs, no cleaning, no "
                 "showings, no agent commissions.",
                 f"{st['transfer']} A reputable buyer will walk you through the numbers line by "
                 f"line so you know exactly what you'll net at closing before you sign anything."]},
            {"heading": "Is a Cash Offer the Right Move for You?",
             "paragraphs": [
                 f"A cash sale trades a little top-line price for speed, certainty, and zero "
                 f"out-of-pocket costs. If your {place} home is in great shape and you have months "
                 f"to spare, listing may net more. If the property needs work, the timeline is "
                 f"tight, or you simply want it done, a direct sale to a local buyer like Parlevu "
                 f"Global Services is often the stronger net result — and there's no obligation "
                 f"in finding out what your number would be."]},
        ],
        "faqs": [
            {"q": f"How fast can I sell my house in {place}?",
             "a": "With a cash buyer, most sales close in 7-21 days from the first phone call. "
                  "You pick the closing date — we've closed in under a week when a seller needed it, "
                  "and we can also wait if you need more time to move."},
            {"q": "Do I need to make repairs or clean out the property?",
             "a": "No. Cash buyers purchase strictly as-is. Leave behind anything you don't want — "
                  "furniture, junk, even a property full of belongings. The offer already accounts "
                  "for the condition."},
            {"q": "Are there any fees or commissions?",
             "a": "No agent commissions and no hidden fees. In most of our purchases the seller's "
                  "closing costs are covered, so the offer you accept is very close to the cash "
                  "you walk away with."},
            {"q": f"Is Parlevu Global Services a local {st['name']} buyer?",
             "a": "Yes — we're a Baltimore-based, Black- and indigenous-owned real estate investment "
                  "firm buying homes across Maryland, Virginia, and Washington DC. You deal directly "
                  "with us, not a lead-reseller."},
        ],
    }


# ------------------------------------------------------------- Rendering ----
def body_chars(post) -> int:
    n = len(post["intro"])
    for s in post["sections"]:
        n += len(s["heading"]) + sum(len(p) for p in s["paragraphs"])
    return n


def fit_length(post, brief):
    """Nudge body into the 2000-3000 char window."""
    fb = fallback_generate(brief)
    # too short -> append fallback sections until in range
    i = 0
    while body_chars(post) < CHAR_MIN and i < len(fb["sections"]):
        sec = fb["sections"][i]
        if sec["heading"] not in [s["heading"] for s in post["sections"]]:
            post["sections"].append(sec)
        i += 1
    # too long -> drop trailing paragraphs
    while body_chars(post) > CHAR_MAX:
        for s in reversed(post["sections"]):
            if len(s["paragraphs"]) > 1:
                s["paragraphs"].pop()
                break
        else:
            if len(post["sections"]) > 2:
                post["sections"].pop()
            else:
                break
    return post


def render(brief, post, hero_img, published_slugs) -> str:
    place = place_of(brief)
    filename = f"blog-{brief['slug']}.html"
    today = date.today()
    date_human = today.strftime("%B %d, %Y").replace(" 0", " ")

    sec_html = []
    for i, s in enumerate(post["sections"]):
        sid = f"s{i+1}"
        sec_html.append(
            f'    <h2 id="{sid}" style="color:var(--navy);font-size:1.4rem;margin:44px 0 18px">{esc(s["heading"])}</h2>')
        for p in s["paragraphs"]:
            sec_html.append(
                f'    <p style="color:var(--text-body);line-height:1.8;margin-bottom:18px">{esc(p)}</p>')
        # mid-article inline CTA after the first section
        if i == 0:
            sec_html.append(
                '    <div style="background:rgba(201,168,76,.1);border:1px solid var(--gold);border-radius:var(--radius);padding:20px;margin:8px 0 28px">'
                '<p style="font-weight:700;color:var(--navy);margin-bottom:8px;font-family:\'Montserrat\',sans-serif">💡 Skip the guesswork</p>'
                f'<p style="font-size:.9rem;color:var(--text-body);margin:0;line-height:1.7">Want a real number for your {esc(place)} home? '
                '<a href="contact.html" style="color:var(--gold);font-weight:700">Request a free, no-obligation cash offer</a> '
                'or call <a href="tel:+16676468306" style="color:var(--gold);font-weight:700">(667) 646-8306</a>.</p></div>')
    body = "\n".join(sec_html)

    faq_html = "\n".join(
        f'      <details class="faq-item-article"><summary>{esc(f["q"])}</summary>'
        f'<div class="faq-answer"><p>{esc(f["a"])}</p></div></details>'
        for f in post["faqs"])

    faq_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                       for f in post["faqs"]]})

    article_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": brief["title"],
        "description": post["meta_desc"],
        "image": f"https://www.parlevugloballlc.com/{hero_img}" if not hero_img.startswith("http") else hero_img,
        "author": {"@type": "Organization", "name": "Parlevu Global Services LLC",
                   "url": "https://www.parlevugloballlc.com"},
        "publisher": {"@type": "Organization", "name": "Parlevu Global Services LLC",
                      "logo": {"@type": "ImageObject",
                               "url": "https://www.parlevugloballlc.com/logo.png"}},
        "datePublished": today.isoformat(), "dateModified": today.isoformat(),
        "mainEntityOfPage": f"https://www.parlevugloballlc.com/{filename}",
        "keywords": ", ".join([brief["primary_keyword"]] + brief["secondary_keywords"])})

    localbiz_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "RealEstateAgent",
        "name": "Parlevu Global Services LLC",
        "url": "https://www.parlevugloballlc.com",
        "telephone": "+1-667-646-8306",
        "email": "info@parlevugloballlc.com",
        "address": {"@type": "PostalAddress", "streetAddress": "3333 Windsor Ave",
                    "addressLocality": "Baltimore", "addressRegion": "MD",
                    "postalCode": "21216", "addressCountry": "US"},
        "areaServed": [{"@type": "State", "name": "Maryland"},
                       {"@type": "State", "name": "Virginia"},
                       {"@type": "City", "name": "Washington"},
                       {"@type": "City", "name": place}],
        "priceRange": "$$"})

    # related: state hub + 2 most recent published or static posts
    related = [(brief["hub"], "Local Guides",
                f"Sell Your House Fast in {STATE_FACTS[brief['state']]['name']}")]
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    pub = [p for p in cal["posts"]
           if p["status"] == "published" and p["slug"] != brief["slug"]][-2:]
    for p in pub:
        related.append((f"blog-{p['slug']}.html", p["category"], p["title"]))
    for f, c, t in STATIC_POSTS:
        if len(related) >= 3:
            break
        related.append((f, c, t))
    related_html = "\n".join(
        f'        <a href="{f}" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border);transition:var(--transition)" '
        f'onmouseover="this.style.borderColor=\'var(--gold)\'" onmouseout="this.style.borderColor=\'var(--border)\'">'
        f'<span style="font-size:.7rem;font-family:\'Montserrat\',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">{esc(c)}</span>'
        f'<p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">{esc(t)}</p></a>'
        for f, c, t in related[:3])

    cta_head, cta_sub = CTA_TEXT[brief["cta_variant"]]
    words = body_chars(post) // 5
    html = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "{{TITLE}}": esc(brief["title"]),
        "{{META_DESC}}": esc(post["meta_desc"]),
        "{{FILENAME}}": filename,
        "{{HERO_IMG}}": hero_img,
        "{{IMG_ALT}}": esc(f"{brief['primary_keyword']} — {place}"),
        "{{CATEGORY}}": esc(brief["category"]),
        "{{HEADER_H1}}": esc(brief["category"]),
        "{{HEADER_SUB}}": esc(f"Practical guidance for {place} homeowners from Parlevu Global Services."),
        "{{DATE_HUMAN}}": date_human,
        "{{READ_TIME}}": str(max(2, round(words / 200))),
        "{{INTRO}}": esc(post["intro"]),
        "{{BODY}}": body,
        "{{CTA_HEADLINE}}": esc(cta_head.format(place=place)),
        "{{CTA_SUB}}": esc(cta_sub.format(place=place)),
        "{{FAQ_HTML}}": faq_html,
        "{{RELATED_LINKS}}": related_html,
        "{{ARTICLE_JSONLD}}": article_jsonld,
        "{{FAQ_JSONLD}}": faq_jsonld,
        "{{LOCALBUSINESS_JSONLD}}": localbiz_jsonld,
    }.items():
        html = html.replace(k, v)
    return html


def generate(slug: str, hero_img: str | None = None) -> Path:
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    brief = next((p for p in cal["posts"] if p["slug"] == slug), None)
    if not brief:
        raise SystemExit(f"slug not found in calendar: {slug}")

    post = ollama_generate(brief)
    engine = "ollama" if post else "fallback"
    post = fit_length(post or fallback_generate(brief), brief)
    print(f"  body: {body_chars(post)} chars ({engine} engine)")

    if hero_img is None:
        sys.path.insert(0, str(REPO / "tools"))
        from gen_image import generate as gen_img
        hero_img = gen_img(slug, brief["image_prompt"])

    out = REPO / f"blog-{slug}.html"
    out.write_text(render(brief, post, hero_img,
                          [p["slug"] for p in cal["posts"] if p["status"] == "published"]),
                   encoding="utf-8")
    print(f"  wrote {out.name}")
    return out


if __name__ == "__main__":
    generate(sys.argv[1])
