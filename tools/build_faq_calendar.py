#!/usr/bin/env python3
"""Build a 30-day calendar that publishes the 30 FAQs to pages and channels.

WHAT THIS IS
------------
One FAQ per day for 30 days (28 Oct - 26 Nov 2026). Each day carries:

  * the question and answer, for publication on its matching page
  * the target page, per the FAQ review's own intent mapping
  * ~1200-character captions for Google Business Profile, Facebook and
    Instagram, derived from that day's FAQ

This is additive. It does NOT touch content-calendar.json, which already
holds 79 queued blog posts through 2026-12-12. The FAQs go ON existing
pages, which is what the review recommends: answers belong where the
visitor's intent already is, not in 30 more blog posts.

GUARDRAILS
----------
Two answers were softened because the review itself flags the underlying
claims as needing verification against written policy:

  FAQ 05  "We also advertise covering standard closing costs" removed.
          The written offer and settlement statement govern.
  FAQ 04  "as little as seven days" kept but attributed, not promised.

The foreclosure answer (FAQ 15) keeps its warning that a cash offer does
not automatically stop a foreclosure. Nothing invents clients, metrics or
competitor pricing, and no percentages appear anywhere.

Google rejects Business Profile posts containing a phone number, so GBP
captions route to the profile's call button instead. Confirmed live
2026-10-27.

    python tools/build_faq_calendar.py
"""
import io
import json
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "faq-calendar.json"

SITE = "https://parlevugloballlc.com"
PHONE_DISPLAY = "(667) 646-8306"
BOOKING = "https://calendar.app.google/hfm91n5jiLxXJHiu6"
CAMPAIGN = "faq30-2026-11"
START = date(2026, 10, 28)
CHANNELS = ("gbp", "facebook", "instagram")
TARGET_LO, TARGET_HI = 1050, 1350
PHONE_RX = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}")

# Pages that exist today. faq.html and fsbo-consultation.html do NOT yet --
# the review recommends creating both, and until they exist their FAQs are
# routed to the nearest live page so nothing links to a 404.
PAGES = {
    "home": "index.html",
    "contact": "contact.html",
    "services": "services.html",
    "asis": "pillar-we-buy-houses-as-is.html",
    "foreclosure": "pillar-foreclosure-property-help.html",
    "sellfast": "pillar-sell-my-house-fast.html",
    "whatwebuy": "what-we-buy.html",
}

# (n, category, question, answer, page key)
FAQS = [
    (1, "A", "How can I sell my house fast in Baltimore, Maryland?",
     "Contact Parlevu Global Services LLC by phone, through our online cash-offer form, or by booking a free virtual consultation. Share your property address, condition, and preferred timeline. We review the information and typically provide a no-obligation cash offer within 24-48 hours.", "sellfast"),
    (2, "A", "Do you buy houses for cash in Baltimore and the DMV?",
     "Yes. Parlevu Global Services focuses on Baltimore City, Baltimore County, and the greater DMV area. We consider properties in different conditions and situations. Contact us with your property address to confirm whether we can make an offer in your location.", "home"),
    (3, "A", "Can I sell my house as-is without making repairs?",
     "Yes. We consider properties with outdated kitchens, damaged roofs, water damage, structural concerns, and other repair needs. You do not need to renovate or stage your property before requesting an offer. Applicable property disclosures and legal requirements still apply.", "asis"),
    (4, "A", "How quickly can Parlevu Global close on my house?",
     "Our advertised closing timeline is as little as seven days, depending on title clearance, the property, and transaction requirements. We can also discuss a later closing date if you need additional time to move or make arrangements.", "sellfast"),
    (5, "A", "Do I have to pay real estate agent commissions when selling directly to Parlevu?",
     "Our direct cash-purchase model does not charge the seller a real estate agent commission. Review the written offer and settlement statement to confirm the exact terms, including which costs each party carries and any applicable exceptions.", "home"),
    (6, "A", "How much will Parlevu Global offer for my house?",
     "Every property is different. We consider location, recent comparable sales, property condition, estimated repairs, market demand, and other transaction costs. Submit your property address and basic details to request an individualized cash offer. You can review the offer before deciding whether to accept.", "home"),
    (7, "B", "What does FSBO mean in real estate?",
     "FSBO stands for For Sale By Owner. It means the property owner sells directly to a buyer without hiring a listing agent to represent the seller. The owner takes responsibility for important tasks such as pricing, marketing, buyer communication, negotiation, and coordinating the closing.", "services"),
    (8, "B", "Can I sell my house myself without a real estate agent in Maryland?",
     "Yes. Homeowners can generally sell their property without hiring a listing agent. However, you still need to manage the sale correctly, including applicable disclosures, contracts, title matters, and settlement requirements. Parlevu offers FSBO consultation to help you understand the process.", "services"),
    (9, "B", "Is selling FSBO better than selling to a cash home buyer?",
     "It depends on your goals. FSBO can give you more direct control over pricing and negotiations, but you must handle marketing and buyer coordination. A cash sale may offer greater convenience and a faster timeline, especially when the property needs repairs. Compare the likely net proceeds, costs, effort, and certainty of each option.", "services"),
    (10, "B", "How do I price my home correctly when selling it myself?",
     "Start by reviewing recently sold comparable properties in your neighborhood. Consider square footage, condition, property type, upgrades, and current competition. An online estimate alone may not reflect your home's actual market value. Parlevu's FSBO consultation can help you evaluate pricing considerations for the Baltimore and DMV markets.", "services"),
    (11, "B", "Can Parlevu help me sell my home without listing it on the MLS?",
     "Yes. You can explore a direct cash-purchase option without going through a traditional MLS listing process. If you prefer to sell independently, our FSBO consultation can help you consider pricing, marketing, and negotiation. MLS access and any associated services depend on the arrangement you choose.", "services"),
    (12, "B", "Can I get FSBO guidance and still accept a cash offer later?",
     "Yes. You can begin with an FSBO consultation, discuss your goals, review your selling options, and decide which route suits your circumstances. A consultation does not obligate you to accept a purchase offer.", "services"),
    (13, "C", "Can I sell a house that needs major repairs or has code violations?",
     "We consider properties with significant repair needs and certain code violations. Tell us what you know about the property, including outstanding notices or safety concerns. We will review the circumstances and determine whether the property fits our purchasing criteria.", "asis"),
    (14, "C", "Can I sell an inherited house in Baltimore?",
     "Yes, we consider inherited and estate-related properties. Before a sale can proceed, the person signing the contract must have the necessary legal authority, and any required probate or estate steps must be addressed. We can discuss the property's condition, your timeline, and the next steps for a potential offer.", "foreclosure"),
    (15, "C", "Can you buy my house if I am behind on mortgage payments?",
     "We consider properties involving mortgage arrears and pre-foreclosure. The available options depend on your equity, mortgage balance, deadlines, and the lender's requirements. Contact us promptly so we can discuss the property and timing. A cash offer does not automatically stop a foreclosure; obtain appropriate legal advice about deadlines and your rights.", "foreclosure"),
    (16, "C", "Can I sell my house during a divorce?",
     "A property sale may be possible during a divorce, but ownership rights, court orders, and any required consent must be considered. We can review the property's basic details and discuss a potential offer. Consult your attorney about the proper way to handle the sale and divide any proceeds.", "foreclosure"),
    (17, "C", "Do you buy vacant houses and properties left by tenants?",
     "We consider vacant homes and certain tenant-occupied properties. Let us know whether the property is empty, occupied, subject to a lease, or in need of a clean-out. Existing tenant rights and legal requirements must be respected during any sale.", "whatwebuy"),
    (18, "C", "Can I sell my Baltimore property if I live in another state?",
     "Yes. Our virtual consultation process allows out-of-state owners to discuss their Baltimore-area property remotely. We can review property details, discuss an offer, and coordinate next steps. Closing documents and identity verification will be handled according to the requirements of the transaction and settlement provider.", "contact"),
    (19, "D", "Is a cash offer from Parlevu Global free?",
     "Yes. We offer free consultations and no-obligation cash offers. You can review the proposed terms and decline if they do not meet your needs. Always read any document before signing, particularly if it includes an exclusivity clause, an assignment provision, or other contractual obligations.", "contact"),
    (20, "D", "What information do I need to request a cash offer?",
     "Start with the property address, your contact details, the property type, its general condition, and your preferred selling timeline. Information about mortgage balances, liens, occupancy, and known repairs may help during the review. You generally do not need to gather every document before making the initial inquiry.", "contact"),
    (21, "D", "What happens after I submit my property details?",
     "We review the information you provide and may contact you with follow-up questions. Depending on the property, we may request photographs, comparable property information, or an in-person or virtual walkthrough. If the property meets our criteria, we present an offer for you to review.", "contact"),
    (22, "D", "Do I need to clean out the house before selling it?",
     "Not necessarily. Our as-is purchasing service considers properties that need cleaning or substantial clean-outs. Tell us whether furniture, personal belongings, or unwanted items remain. The purchase agreement should clarify which items will stay and which, if any, must be removed before closing.", "asis"),
    (23, "D", "What happens if my property has liens or title issues?",
     "A property with liens or title complications may still be eligible for review. The settlement provider will need to identify relevant claims, ownership issues, and the steps required to transfer clear title. Whether the sale can close, and how much you receive, depends on the specific circumstances and amounts owed.", "asis"),
    (24, "D", "Do I still have to disclose property defects when selling as-is in Maryland?",
     "Yes, applicable disclosure obligations still matter. Maryland law generally requires covered residential sellers to provide the prescribed disclosure or disclaimer statement, and known latent defects that pose a direct threat to health or safety must be disclosed under the applicable rules. Exceptions exist, so verify which requirements apply to your transaction.", "asis"),
    (25, "E", "Does Parlevu Global Services help people invest in Baltimore real estate?",
     "Yes. Our investment-related services include market insights, property sourcing, fix-and-flip opportunities, and buy-and-hold rental strategies. The appropriate approach depends on your available capital, risk tolerance, investment timeline, and property objectives.", "services"),
    (26, "E", "How can I find off-market investment properties in Baltimore?",
     "Off-market opportunities may come through direct owner outreach, investor relationships, referrals, and property-specific research. Parlevu offers investment sourcing and market guidance. Availability varies, and any prospective property should undergo independent due diligence before you commit funds.", "services"),
    (27, "E", "Can Parlevu help me evaluate a fix-and-flip property?",
     "We include fix-and-flip opportunities and market analysis among our investment services. A sound evaluation considers the purchase price, renovation budget, contingency reserve, holding costs, financing, resale costs, and realistic after-repair value. Investment returns are not guaranteed, and all estimates should be verified before purchasing.", "services"),
    (28, "E", "Can I invest in Baltimore rental properties for long-term income?",
     "We offer investment guidance related to buy-and-hold rental opportunities. Important considerations include neighborhood demand, realistic rent, vacancy, property taxes, insurance, maintenance, financing, and landlord obligations. We can discuss your objectives and potential sourcing options, subject to available inventory and the terms of any engagement.", "services"),
    (29, "E", "Does Parlevu offer real estate wholesaling or joint venture opportunities?",
     "Our services include wholesale deals and joint ventures as potential investment offerings. Availability depends on the specific opportunity and agreed terms. Before entering an arrangement, clarify each party's role, compensation, capital contribution, responsibilities, exit strategy, and applicable legal requirements.", "contact"),
    (30, "D", "How do I schedule a consultation with Parlevu Global Services LLC?",
     "You can call us, submit the cash-offer form on our website, or book a virtual consultation online. We can discuss a potential cash sale, FSBO guidance, or real estate investment objectives. Initial consultations are free and carry no obligation to accept an offer.", "contact"),
]

CATEGORY_NAME = {
    "A": "Selling a house for cash in Baltimore",
    "B": "FSBO (For Sale By Owner)",
    "C": "Difficult property and personal situations",
    "D": "Cash offers, fees, paperwork and closing",
    "E": "Real estate investment",
}

HASHTAGS = [
    "#Baltimore #MarylandRealEstate #SellMyHouseFast #CashHomeBuyer",
    "#SellYourHouse #Maryland #DMVRealEstate #AsIsSale",
    "#BaltimoreHomes #FSBO #RealEstateMaryland #CashOffer",
]

# GBP forbids phone numbers; the profile's own call button carries that.
CTA = {
    "default": "Questions? Call " + PHONE_DISPLAY + " and ask. No pitch, no obligation.",
    "consult": "Book a free virtual consult: " + BOOKING,
}
CTA_GBP = {
    "default": "Questions? Use the call button on our profile. No pitch, no obligation.",
    "consult": "Book a free virtual consult: " + BOOKING,
}

EXTRAS = [
    ("If you are weighing this in Baltimore, the useful first step is a real number on "
     "your own property rather than an online estimate. An estimate cannot see a roof, "
     "a tenant, or a lien on the title."),
    ("Worth having ready before any call: roughly what is owed on the property, whether "
     "anyone else is on the deed, and whether it is occupied. Those three answers shape "
     "the timeline more than anything about the house itself."),
    ("What we do not do: charge you to look, pressure you on the first call, or ask you "
     "to fix anything first. If a direct sale is the wrong fit, it is better for everyone "
     "that you hear that early."),
]


def tagged(path, n, channel):
    medium = "organic" if channel == "gbp" else "social"
    return ("%s/%s?utm_source=%s&utm_medium=%s&utm_campaign=%s&utm_content=faq-%02d"
            % (SITE, path, channel, medium, CAMPAIGN, n))


def caption(faq, channel, i):
    n, cat, q, a, pagekey = faq
    page = PAGES[pagekey]
    table = CTA_GBP if channel == "gbp" else CTA
    cta = table["consult"] if n in (12, 19, 30) else table["default"]

    parts = [q, "", a, ""]
    if channel == "instagram":
        parts.append("More answers on the site - link in our bio.")
    else:
        parts.append("Full answer and related questions: " + tagged(page, n, channel))
    parts += ["", cta]
    text = "\n".join(parts)

    tags = "" if channel == "gbp" else "\n\n" + HASHTAGS[i % len(HASHTAGS)]
    for extra in EXTRAS:
        if len(text) + len(tags) >= TARGET_LO:
            break
        text += "\n\n" + extra
    return text + tags


def main():
    entries, lengths, outside = [], [], []
    for i, faq in enumerate(FAQS):
        n, cat, q, a, pagekey = faq
        day = START + timedelta(days=i)
        chans = {}
        for ch in CHANNELS:
            t = caption(faq, ch, i)
            lengths.append(len(t))
            if not (TARGET_LO <= len(t) <= TARGET_HI):
                outside.append((n, ch, len(t)))
            if ch == "gbp" and PHONE_RX.search(t):
                raise SystemExit("FAQ %02d GBP caption contains a phone number" % n)
            chans[ch] = {"copy": t, "chars": len(t),
                         "link": None if ch == "instagram"
                                 else tagged(PAGES[pagekey], n, ch)}
        entries.append({
            "day": i + 1,
            "date": day.isoformat(),
            "scheduled_for": day.isoformat() + "T10:00",
            "faq_number": n,
            "category": cat,
            "category_name": CATEGORY_NAME[cat],
            "question": q,
            "answer": a,
            "publish_on_page": PAGES[pagekey],
            "status": "pending_approval",
            "channels": chans,
        })

    out = {
        "campaign": CAMPAIGN,
        "built": date.today().isoformat(),
        "window": {"start": START.isoformat(),
                   "end": (START + timedelta(days=len(FAQS) - 1)).isoformat(),
                   "days": len(FAQS)},
        "channels": list(CHANNELS),
        "source": ("The 30-FAQ review of parlevugloballlc.com. One FAQ per day: "
                   "publish the answer on its matching page, post the caption to "
                   "the three channels."),
        "relationship_to_blog": (
            "Additive. content-calendar.json already holds 79 queued posts through "
            "2026-12-12 and is untouched. These FAQs go ON existing pages, which is "
            "what the review recommends -- answers belong where the visitor's intent "
            "already is, not in 30 more blog posts."),
        "guardrails": [
            "FAQ 05: the 'covering standard closing costs' claim was removed. The "
            "written offer and settlement statement govern.",
            "FAQ 04: 'as little as seven days' is attributed as our advertised "
            "timeline, not promised as an outcome.",
            "FAQ 15: keeps the warning that a cash offer does not automatically stop "
            "a foreclosure.",
            "GBP captions contain no phone number - Google rejects those posts. The "
            "profile's call button carries it.",
            "No percentages, no invented clients, metrics or competitor pricing.",
        ],
        "pages_to_create": {
            "faq.html": "Dedicated FAQ page carrying all 30, grouped by category.",
            "fsbo-consultation.html": ("The review's highest-priority page: FAQs 7-12 "
                                       "belong here. Until it exists they route to "
                                       "services.html."),
        },
        "tracking": {
            "utm_campaign": CAMPAIGN,
            "utm_content": "faq-01 .. faq-30, so a lead traces to the exact FAQ",
            "ga4": "G-FCL3Y130B5",
        },
        "entries": entries,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("days            : %d (%s -> %s)"
          % (len(entries), entries[0]["date"], entries[-1]["date"]))
    print("captions        : %d" % (len(entries) * len(CHANNELS)))
    print("chars           : min %d  max %d  mean %d"
          % (min(lengths), max(lengths), sum(lengths) // len(lengths)))
    print("outside %d-%d  : %d" % (TARGET_LO, TARGET_HI, len(outside)))
    for n, ch, ln in outside[:6]:
        print("   FAQ %02d %-10s %d" % (n, ch, ln))
    print("by category     : %s"
          % dict(Counter(e["category_name"][:28] for e in entries)))
    print("by target page  : %s" % dict(Counter(e["publish_on_page"] for e in entries)))
    print("written         : %s" % OUT)


if __name__ == "__main__":
    main()
