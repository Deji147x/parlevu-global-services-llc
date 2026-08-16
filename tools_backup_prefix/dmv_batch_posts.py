"""Generate 8 high-value DMV batch posts with all CTA/social elements.
Write in Parlevu's voice: direct, no-nonsense, local-focused.
Publish immediately (not on calendar schedule).

Usage: python tools/dmv_batch_posts.py
"""
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from gen_image import generate as gen_img
from generate_post import render, normalize, esc, STATE_FACTS, STATIC_POSTS, CTA_TEXT
from generate_post import OLLAMA_URL, OLLAMA_MODEL

# High-intent DMV keywords — direct competitors focus on these
DMV_BRIEFS = [
    {
        "slug": "we-buy-houses-baltimore-fast",
        "title": "We Buy Houses Baltimore Fast — No Realtor, No Wait, No Repairs",
        "kw": "we buy houses baltimore fast",
        "state": "MD",
        "city": "Baltimore",
        "category": "Cash Buyer Process",
        "intro_hook": "Your Baltimore home can close in a week. No agent. No repairs. We handle it.",
    },
    {
        "slug": "cash-offer-baltimore-maryland",
        "title": "Get a Real Cash Offer on Your Baltimore House in 24 Hours",
        "kw": "cash offer baltimore maryland",
        "state": "MD",
        "city": "Baltimore",
        "category": "Quick Sales",
        "intro_hook": "Forget the 90-day listing grind. Get a written cash offer from Parlevu in one day.",
    },
    {
        "slug": "sell-house-arlington-virginia",
        "title": "Sell Your House in Arlington Virginia for Cash — No Fees, No Delays",
        "kw": "sell house arlington virginia cash",
        "state": "VA",
        "city": "Arlington",
        "category": "Local Guides",
        "intro_hook": "Arlington homes move fast in our market. We move faster.",
    },
    {
        "slug": "cash-home-buyers-dc-washington",
        "title": "Cash Home Buyers in Washington DC — Fair Offers, Fast Closing",
        "kw": "cash home buyers washington dc",
        "state": "DC",
        "city": "Washington",
        "category": "DC Services",
        "intro_hook": "DC's transfer taxes are brutal. Selling for cash cuts through them.",
    },
    {
        "slug": "sell-inherited-house-maryland-fast",
        "title": "Sell Your Inherited House in Maryland Fast — Probate or No Probate",
        "kw": "sell inherited house maryland fast",
        "state": "MD",
        "city": None,
        "category": "Inherited Properties",
        "intro_hook": "Inherited a Maryland property? We buy it as-is. No probate delays.",
    },
    {
        "slug": "baltimore-house-buyers-we-buy-any-condition",
        "title": "Baltimore House Buyers — We Buy Any Condition, Any Situation",
        "kw": "baltimore house buyers we buy any condition",
        "state": "MD",
        "city": "Baltimore",
        "category": "Problem Properties",
        "intro_hook": "Fire damage? Tenants? Hoarder house? We've bought them all.",
    },
    {
        "slug": "sell-house-fast-alexandria-virginia",
        "title": "Sell Your House Fast in Alexandria Virginia — Local Cash Buyers",
        "kw": "sell house fast alexandria virginia",
        "state": "VA",
        "city": "Alexandria",
        "category": "Local Guides",
        "intro_hook": "Alexandria market is competitive. We close faster than any agent can list.",
    },
    {
        "slug": "fair-cash-offer-dc-distressed-property",
        "title": "Get a Fair Cash Offer on Your DC Property — Even if It Needs Repairs",
        "kw": "fair cash offer dc distressed property",
        "state": "DC",
        "city": None,
        "category": "Distressed Property",
        "intro_hook": "Your DC rowhouse doesn't need to be perfect. We buy it exactly as it sits.",
    },
]


def gen_dmv_post_content(brief) -> dict:
    """Generate DMV-focused content in Parlevu's voice (direct, local, action-oriented)."""
    place = brief["city"] or STATE_FACTS[brief["state"]]["name"]
    facts = STATE_FACTS[brief["state"]]

    # Parlevu's voice: experienced, no fluff, focused on speed and fairness
    sections = [
        {
            "heading": f"Why {place} Homeowners Choose Direct Cash Sales",
            "paragraphs": [
                f"We've closed over 100 deals across Maryland, Virginia, and DC. {place} is our backyard. We know the market — what homes sell for, what repair costs actually are, and how to close fast without the agent middleman taking 5-6%.",
                f"Most sellers we talk to have already listed for 30-60 days with zero offers. Or they're dealing with a situation that won't wait: foreclosure breathing down their neck, inherited property sitting vacant, or a property that needs $30K in repairs just to pass inspection.",
                "Here's the thing: traditional buyers using bank financing can't touch distressed properties. Appraisers kill the deal. That's why our buyer pool is almost entirely investors and cash buyers — people who can close on anything.",
            ]
        },
        {
            "heading": f"How We Buy {place} Houses — The Process",
            "paragraphs": [
                "Step 1: You call or fill out our form. Tell us about the property — address, condition, any special circumstances. Two minutes, max.",
                "Step 2: We inspect it (usually the same day or next morning). We're not sending appraisers or financing contingencies — we're pricing what we see and what the market will bear.",
                "Step 3: We send a written offer. This is binding on us, non-binding on you. You review it. Most sellers say yes on the spot.",
                f"Step 4: We close on your timeline. Seven days? We can do that. Thirty days? Even better — gives you time to plan. We handle all closing costs. No surprises.",
            ]
        },
        {
            "heading": f"What Happens to Your {place} Home After Closing",
            "paragraphs": [
                "Honestly? We either renovate it and resell, or we hold it as a rental. Depends on the property and the market. Either way, you don't have to think about it anymore. It's not your problem.",
                f"That's the real value of selling to us. No more property taxes, insurance, maintenance, tenant headaches, or vacant house decay. One check. Done.",
            ]
        },
    ]

    faqs = [
        {
            "q": f"How much less will I get selling for cash vs. listing in {place}?",
            "a": f"Cash buyers typically offer 70–85% of a home's after-repair value (ARV) to account for repair costs, carrying costs, and our margin. But you save 5-6% in agent commissions and avoid paying for repairs, staging, and a 2-3 month carrying cost. Net difference is often smaller than you'd think.",
        },
        {
            "q": "Do you really buy any condition?",
            "a": "Yes. Fire damage, water damage, mold, foundation issues, occupied by tenants, full of junk — we've bought all of it. The price reflects the condition, but the offer is real and we close.",
        },
        {
            "q": f"What if I owe more than my {place} house is worth?",
            "a": "We can work with that. Short sale situations are common. We handle the lender negotiations; you walk away debt-free. No deficiency on your credit.",
        },
    ]

    return {
        "meta_desc": f"{brief['title']} — Parlevu Global Services buys {place} homes for cash in 24-48 hours. No repairs, no fees, no agent commission. Fair offer guaranteed.",
        "intro": brief["intro_hook"],
        "sections": sections,
        "faqs": faqs,
    }


def render_dmv_post(brief) -> str:
    place = brief["city"] or STATE_FACTS[brief["state"]]["name"]
    filename = f"blog-{brief['slug']}.html"
    today = date.today()
    date_human = today.strftime("%B %d, %Y").replace(" 0", " ")

    post = gen_dmv_post_content(brief)

    # Build sections HTML
    sec_html = []
    for i, s in enumerate(post["sections"]):
        sid = f"s{i+1}"
        sec_html.append(
            f'    <h2 id="{sid}" style="color:var(--navy);font-size:1.4rem;margin:44px 0 18px">{esc(s["heading"])}</h2>')
        for p in s["paragraphs"]:
            sec_html.append(
                f'    <p style="color:var(--text-body);line-height:1.8;margin-bottom:18px">{esc(p)}</p>')
        if i == 0:
            sec_html.append(
                '    <div style="background:rgba(201,168,76,.1);border:1px solid var(--gold);border-radius:var(--radius);padding:20px;margin:8px 0 28px">'
                '<p style="font-weight:700;color:var(--navy);margin-bottom:8px;font-family:\'Montserrat\',sans-serif">📞 Not ready to sell yet?</p>'
                f'<p style="font-size:.9rem;color:var(--text-body);margin:0;line-height:1.7">Just want to know what your {esc(place)} home is worth? '
                '<a href="https://calendar.app.google/hfm91n5jiLxXJHiu6" style="color:var(--gold);font-weight:700">Schedule a free consultation</a> — '
                'no pressure, no obligation.</p></div>')
    body = "\n".join(sec_html)

    # FAQ HTML
    faq_html = "\n".join(
        f'      <details class="faq-item-article"><summary>{esc(f["q"])}</summary>'
        f'<div class="faq-answer"><p>{esc(f["a"])}</p></div></details>'
        for f in post["faqs"])

    # Social links at bottom (added to footer area)
    social_html = '''      <div style="display:flex;gap:12px;justify-content:center;margin-bottom:24px">
        <a href="https://www.facebook.com/ParlevuGlobalServices/" target="_blank" rel="noopener" aria-label="Facebook" title="Follow Parlevu on Facebook"><i class="fab fa-facebook-f" style="font-size:1.2rem;color:var(--navy)"></i></a>
        <a href="https://www.instagram.com/ParlevuGlobalServices/" target="_blank" rel="noopener" aria-label="Instagram" title="Follow Parlevu on Instagram"><i class="fab fa-instagram" style="font-size:1.2rem;color:var(--navy)"></i></a>
        <a href="https://www.linkedin.com/in/parlevu-global-services-llc-508b2024b/" target="_blank" rel="noopener" aria-label="LinkedIn" title="Connect on LinkedIn"><i class="fab fa-linkedin-in" style="font-size:1.2rem;color:var(--navy)"></i></a>
        <a href="https://x.com/ParlevuGlobal/" target="_blank" rel="noopener" aria-label="X" title="Follow Parlevu on X"><i class="fab fa-x-twitter" style="font-size:1.2rem;color:var(--navy)"></i></a>
        <a href="https://www.pinterest.com/ParlevuGlobal/" target="_blank" rel="noopener" aria-label="Pinterest" title="Follow Parlevu on Pinterest"><i class="fab fa-pinterest-p" style="font-size:1.2rem;color:var(--navy)"></i></a>
      </div>'''

    # Schema
    faq_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                       for f in post["faqs"]]})

    article_jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": brief["title"],
        "description": post["meta_desc"],
        "author": {"@type": "Organization", "name": "Parlevu Global Services LLC",
                   "url": "https://www.parlevugloballlc.com"},
        "publisher": {"@type": "Organization", "name": "Parlevu Global Services LLC",
                      "logo": {"@type": "ImageObject",
                               "url": "https://www.parlevugloballlc.com/logo.png"}},
        "datePublished": today.isoformat(), "dateModified": today.isoformat(),
        "mainEntityOfPage": f"https://www.parlevugloballlc.com/{filename}",
        "keywords": brief["kw"]})

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
                       {"@type": "City", "name": place}]})

    related_html = f'''        <a href="services.html" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">Services</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">All Parlevu Buying Services</p></a>
        <a href="about.html" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">About Us</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">Who We Are & How We Buy</p></a>
        <a href="https://calendar.app.google/hfm91n5jiLxXJHiu6" target="_blank" rel="noopener" style="display:block;background:var(--off-white);border-radius:var(--radius);padding:18px;text-decoration:none;border:1px solid var(--border)"><span style="font-size:.7rem;font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold)">Book Now</span><p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:8px 0 0;line-height:1.4">Schedule a Free Consultation</p></a>'''

    template = REPO / "tools" / "post_template.html"
    html = template.read_text(encoding="utf-8")

    for k, v in {
        "{{TITLE}}": esc(brief["title"]),
        "{{META_DESC}}": esc(post["meta_desc"]),
        "{{FILENAME}}": filename,
        "{{HERO_IMG}}": f"images/blog/dmv-{brief['slug']}.jpg",
        "{{IMG_ALT}}": esc(f"{brief['kw']} — {place}"),
        "{{CATEGORY}}": esc(brief["category"]),
        "{{HEADER_H1}}": esc(brief["category"]),
        "{{HEADER_SUB}}": esc(f"Direct from Parlevu Global Services — {place}'s trusted cash home buyer."),
        "{{DATE_HUMAN}}": date_human,
        "{{READ_TIME}}": "4",
        "{{INTRO}}": esc(post["intro"]),
        "{{BODY}}": body,
        "{{CTA_HEADLINE}}": esc(f"Ready to Sell Your {place} Home for Cash?"),
        "{{CTA_SUB}}": "Get a real offer in 24 hours. No repairs, no fees, no agent commission.",
        "{{FAQ_HTML}}": faq_html,
        "{{RELATED_LINKS}}": related_html,
        "{{ARTICLE_JSONLD}}": article_jsonld,
        "{{FAQ_JSONLD}}": faq_jsonld,
        "{{LOCALBUSINESS_JSONLD}}": localbiz_jsonld,
    }.items():
        html = html.replace(k, v)

    # Add social links before footer
    html = html.replace("</section>\n\n<footer", f"</section>\n\n<section style=\"text-align:center;padding:20px 0;background:rgba(201,168,76,.05);border-top:1px solid var(--border)\">\n  <p style=\"font-size:.85rem;color:var(--text-muted);margin-bottom:12px\">Follow us for more real estate insights</p>\n{social_html}\n</section>\n\n<footer")

    return html, filename


def main():
    print(f"Generating {len(DMV_BRIEFS)} high-value DMV posts...")
    for i, brief in enumerate(DMV_BRIEFS):
        print(f"  [{i+1}/{len(DMV_BRIEFS)}] {brief['slug']}")
        hero = gen_img(f"dmv-{brief['slug']}", brief['title'] + " — " + (brief['city'] or STATE_FACTS[brief['state']]['name']))
        html, filename = render_dmv_post(brief)
        (REPO / filename).write_text(html, encoding="utf-8")
    print(f"Done. All {len(DMV_BRIEFS)} posts rendered. Ready to stage & push.")


if __name__ == "__main__":
    main()
