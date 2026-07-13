"""Build the three state hub pages (MD / VA / DC) — the top of the local-SEO
silo. Every geo blog post links up to its state hub; hubs link to contact.

Run once (re-run safe — overwrites):  python tools/build_hubs.py
"""
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from build_calendar import CITIES  # noqa: E402

TEMPLATE = REPO / "tools" / "post_template.html"

HUBS = {
    "sell-house-fast-maryland.html": {
        "state": "MD", "name": "Maryland",
        "title": "Sell Your House Fast in Maryland — Cash Offers in 24-48 Hours",
        "kw": "sell my house fast maryland",
        "meta": "Sell your Maryland house fast for cash. Local Baltimore-based buyer, offers in 24-48 hours, close in as little as 7 days. No repairs, no fees, no commissions.",
        "intro": "Whether you're in Baltimore, the DC suburbs, or Western Maryland, selling a house the traditional way takes 60-90 days you may not have. Parlevu Global Services is a Baltimore-based cash buyer purchasing homes across Maryland in any condition — with written offers in 24-48 hours and closings on your schedule.",
        "law": "Maryland sellers must complete the Seller's Disclosure and Disclaimer Statement even in as-is sales, and Maryland's quasi-judicial foreclosure process can move to auction in as little as 90-120 days. A direct cash sale can be completed well inside that window.",
    },
    "sell-house-fast-virginia.html": {
        "state": "VA", "name": "Virginia",
        "title": "Sell Your House Fast in Virginia — Local Cash Home Buyers",
        "kw": "sell my house fast virginia",
        "meta": "Sell your Virginia house fast for cash — Northern Virginia to Hampton Roads. Offers in 24-48 hours, close in as little as 7 days. No repairs, fees, or commissions.",
        "intro": "From Alexandria and Arlington down to Richmond and Hampton Roads, Virginia homeowners choose cash sales for one reason: certainty. Parlevu Global Services buys Virginia homes in any condition with written offers in 24-48 hours — no repairs, no showings, no agent commissions.",
        "law": "Virginia is a 'buyer beware' state, but sellers still can't conceal known defects — and Virginia's non-judicial foreclosure is one of the fastest in the country, sometimes under 60 days from notice to auction. If you're behind on payments, moving early preserves your equity and your credit.",
    },
    "sell-house-fast-washington-dc.html": {
        "state": "DC", "name": "Washington DC",
        "title": "Sell Your House Fast in Washington DC — Fair Cash Offers",
        "kw": "sell my house fast washington dc",
        "meta": "Sell your DC house fast for cash — all quadrants and neighborhoods. Offers in 24-48 hours, close in as little as 7 days. No repairs, no fees, no commissions.",
        "intro": "DC rowhomes, condos, and inherited family properties come with some of the region's highest transfer taxes and strictest regulations. Parlevu Global Services buys across all four quadrants in any condition — written offers in 24-48 hours, and we handle the paperwork.",
        "law": "DC requires a Seller's Property Condition Disclosure for most residential sales, pre-1978 homes carry federal lead-paint disclosure duties, and combined transfer/recordation taxes can reach 2.9% — which makes skipping the 5-6% agent commission especially valuable in a direct sale.",
    },
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', '&quot;')


def build(filename, h):
    cities = CITIES[h["state"]][:12]
    city_grid = "\n".join(
        f'      <div style="background:var(--off-white);border-radius:var(--radius);padding:16px;border-left:3px solid var(--gold)">'
        f'<p style="font-weight:700;color:var(--navy);font-size:.85rem;margin:0">📍 {esc(c)}</p></div>'
        for c in cities)
    body = f"""    <h2 style="color:var(--navy);font-size:1.4rem;margin:44px 0 18px">How Selling to Parlevu Works in {h['name']}</h2>
    <p style="color:var(--text-body);line-height:1.8;margin-bottom:18px">Three steps: tell us about the property (2 minutes, phone or form), receive a written cash offer within 24-48 hours, then pick your closing date — as fast as 7 days or as far out as you need. You sell strictly as-is: no repairs, no cleanouts, no showings, and no agent commissions.</p>
    <p style="color:var(--text-body);line-height:1.8;margin-bottom:28px">{esc(h['law'])}</p>
    <h2 style="color:var(--navy);font-size:1.4rem;margin:44px 0 18px">Areas We Buy In</h2>
    <p style="color:var(--text-body);line-height:1.8;margin-bottom:18px">We buy houses throughout {h['name']}, including:</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:36px">
{city_grid}
    </div>
    <h2 style="color:var(--navy);font-size:1.4rem;margin:44px 0 18px">Situations We Help With</h2>
    <p style="color:var(--text-body);line-height:1.8;margin-bottom:18px">Foreclosure and missed payments, inherited or probate properties, divorce, code violations and liens, fire or water damage, problem tenants, vacant houses, hoarder homes, underwater mortgages, job relocation, and downsizing. If the house has become the problem, we're the exit.</p>"""

    faqs = [
        (f"How fast can you buy my {h['name']} house?",
         "Written offer in 24-48 hours; closing in as little as 7 days once you accept. You choose the date — we work around your timeline, not the other way around."),
        ("Do you charge fees or commissions?",
         "No. There are no agent commissions and no service fees, and in most purchases we cover the seller's standard closing costs."),
        ("What condition does the house need to be in?",
         "Any condition. We buy as-is — including homes with major repairs needed, full of belongings, or occupied by tenants."),
    ]
    faq_html = "\n".join(
        f'      <details class="faq-item-article"><summary>{esc(q)}</summary><div class="faq-answer"><p>{esc(a)}</p></div></details>'
        for q, a in faqs)
    faq_jsonld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                             "mainEntity": [{"@type": "Question", "name": q,
                                             "acceptedAnswer": {"@type": "Answer", "text": a}}
                                            for q, a in faqs]})
    article_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "WebPage",
        "name": h["title"], "description": h["meta"],
        "url": f"https://www.parlevugloballlc.com/{filename}"})
    localbiz = json.dumps({
        "@context": "https://schema.org", "@type": "RealEstateAgent",
        "name": "Parlevu Global Services LLC", "url": "https://www.parlevugloballlc.com",
        "telephone": "+1-667-646-8306", "email": "info@parlevugloballlc.com",
        "address": {"@type": "PostalAddress", "streetAddress": "3333 Windsor Ave",
                    "addressLocality": "Baltimore", "addressRegion": "MD",
                    "postalCode": "21216", "addressCountry": "US"},
        "areaServed": [{"@type": "State", "name": "Maryland"},
                       {"@type": "State", "name": "Virginia"},
                       {"@type": "City", "name": "Washington"}],
        "priceRange": "$$"})
    related = """        <a href="services.html" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">Services</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">Everything We Do for Sellers</p></a>
        <a href="blog.html" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">Blog</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">All Seller Guides &amp; Local Articles</p></a>
        <a href="contact.html" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">Contact</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">Get Your Cash Offer Today</p></a>"""

    html = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "{{TITLE}}": esc(h["title"]),
        "{{META_DESC}}": esc(h["meta"]),
        "{{FILENAME}}": filename,
        "{{HERO_IMG}}": f"images/blog/hub-{h['state'].lower()}.jpg",
        "{{IMG_ALT}}": esc(h["kw"]),
        "{{CATEGORY}}": "Local Guides",
        "{{HEADER_H1}}": esc(f"We Buy Houses in {h['name']}"),
        "{{HEADER_SUB}}": esc(h["meta"]),
        "{{DATE_HUMAN}}": date.today().strftime("%B %d, %Y").replace(" 0", " "),
        "{{READ_TIME}}": "4",
        "{{INTRO}}": esc(h["intro"]),
        "{{BODY}}": body,
        "{{CTA_HEADLINE}}": esc(f"Get Your {h['name']} Cash Offer — Free &amp; No Obligation").replace("&amp;amp;", "&amp;"),
        "{{CTA_SUB}}": "Tell us about the property once. Written offer in 24-48 hours. Close whenever you're ready.",
        "{{FAQ_HTML}}": faq_html,
        "{{RELATED_LINKS}}": related,
        "{{ARTICLE_JSONLD}}": article_jsonld,
        "{{FAQ_JSONLD}}": faq_jsonld,
        "{{LOCALBUSINESS_JSONLD}}": localbiz,
    }.items():
        html = html.replace(k, v)
    (REPO / filename).write_text(html, encoding="utf-8")
    print(f"wrote {filename}")


if __name__ == "__main__":
    for fn, h in HUBS.items():
        build(fn, h)
