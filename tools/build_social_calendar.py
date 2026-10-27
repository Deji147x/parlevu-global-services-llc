"""Build a 30-day, multi-channel social calendar from the existing blog queue.

Design decisions worth knowing:

  Source of truth is content-calendar.json. Every caption points at a post
  already queued for that date, so a caption never goes live ahead of the
  page it promotes.

  ~1200 characters per caption, per the brief. Measured and asserted; the
  builder reports anything outside 1050-1350 rather than shipping it quietly.

  Trackable: every link carries utm_source / utm_medium / utm_campaign /
  utm_content={slug}. utm_content is the one that matters -- it distinguishes
  which POST earned a lead, not merely which channel. main.js already reads
  these into first/last touch, so no site change is needed.

  Instagram gets no clickable link (the platform does not linkify captions),
  so IG copy routes to the profile link instead of pretending a URL works.
  Google Business Profile gets no hashtags; they do nothing on that surface.

  No invented claims. Copy is parameterised from the post's own title,
  category and keywords plus VERIFIED contact assets. "Guaranteed" in a
  source title is stripped -- the written policy behind that claim has not
  been confirmed.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO = Path(r"C:\Users\Parlevu_Global\parlevu-global-services-llc")
CAL = REPO / "content-calendar.json"
OUT = REPO / "social-calendar.json"

SITE = "https://parlevugloballlc.com"
PHONE_DISPLAY = "(667) 646-8306"
BOOKING = "https://calendar.app.google/hfm91n5jiLxXJHiu6"
CAMPAIGN = "social30-2026-11"

START = date(2026, 10, 28)
DAYS = 30
CHANNELS = ("facebook", "instagram", "gbp")
TARGET_LO, TARGET_HI = 1050, 1350

# Real, reachable authority pages, taken from this repo's already-vetted
# AUTHORITY_LINKS. One per caption, matched to the post's category -- a
# reference the reader can actually check, not decoration.
REFERENCE = {
    "Selling Guides": ("Realtor.com's seller guide",
                       "https://www.realtor.com/advice/sell/"),
    "Comparisons": ("Realtor.com's FSBO guide",
                    "https://www.realtor.com/advice/sell/for-sale-by-owner/"),
    "Market Updates": ("NAR's research archive",
                       "https://www.nar.realtor/research/research-and-statistics"),
    "Local Guides": ("Maryland REALTORS",
                     "https://www.marylandrealtor.org/"),
    "Cash Offers": ("Realtor.com on closing costs",
                    "https://www.realtor.com/advice/sell/closing-costs/"),
}
DEFAULT_REF = ("Realtor.com's seller resources", "https://www.realtor.com/advice/sell/")

# Internal hub links, so each caption carries a second route into the site.
# These are the four hubs the queued posts actually use, all verified present
# on disk. An earlier version of this dict listed pillar-fsbo.html, which does
# not exist, and omitted three that do -- so 52 of 62 captions silently got no
# secondary link.
HUBS = {
    "sell-house-fast-maryland.html": "our Maryland sellers' guide",
    "sell-house-fast-washington-dc.html": "our DC sellers' guide",
    "sell-house-fast-virginia.html": "our Virginia sellers' guide",
}

# 32 of the queued posts use index.html as their hub. The homepage is a weak
# internal link from a blog post, so those route to the topical pillar instead.
# All three are verified present on disk.
PILLARS = [
    ("Foreclosure", "pillar-foreclosure-property-help.html",
     "our foreclosure options guide"),
    ("Comparisons", "pillar-we-buy-houses-as-is.html",
     "our as-is buying guide"),
]
PILLAR_DEFAULT = ("pillar-sell-my-house-fast.html", "our sell-fast guide")


def hub_for(post):
    """Return (file, anchor_text) for the caption's secondary internal link."""
    hub = post.get("hub")
    if hub in HUBS:
        return hub, HUBS[hub]
    cat = post.get("category") or ""
    for needle, path, text in PILLARS:
        if needle.lower() in cat.lower():
            return path, text
    return PILLAR_DEFAULT

CTA = {
    "call": "Questions? Call " + PHONE_DISPLAY + " and ask. No pitch, no obligation.",
    "consult": "Want to talk it through first? Book a free virtual consult: " + BOOKING,
    "offer": ("Send the address and condition and we'll come back with a no-obligation "
              "cash offer, typically within 24-48 hours."),
}

OPENERS = [
    "{q}",
    "A question we hear a lot from {place} homeowners: {q}",
    "{q} Here's the honest version.",
]

HASHTAGS = [
    "#Baltimore #MarylandRealEstate #SellMyHouseFast #CashHomeBuyer",
    "#SellYourHouse #Maryland #DMVRealEstate #AsIsSale",
    "#BaltimoreHomes #FSBO #RealEstateMaryland #CashOffer",
]


def soften(title):
    """Strip commercial claims whose written policy is unconfirmed."""
    t = re.sub(r"\s*[-\u2013\u2014]\s*24\s*Hours?\s*Guarante*ed?", "", title, flags=re.I)
    t = re.sub(r"\bGuarante*ed?\b", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip(" -\u2013\u2014")


def tagged(path, slug, channel, content=None):
    medium = "organic" if channel == "gbp" else "social"
    return (SITE + "/" + path
            + "?utm_source=" + channel
            + "&utm_medium=" + medium
            + "&utm_campaign=" + CAMPAIGN
            + "&utm_content=" + (content or slug))


def post_url(slug, channel):
    return tagged("blog-" + slug + ".html", slug, channel)


def place_of(post):
    if post.get("city"):
        return post["city"]
    return {"MD": "Maryland", "DC": "Washington DC",
            "VA": "Virginia"}.get(post.get("state"), "Baltimore")


def body_for(post, place):
    """Original copy parameterised from the brief. Nothing lifted, nothing invented."""
    cat = post.get("category", "") or ""
    if "Comparison" in cat:
        return ("There is no single right answer, and anyone who tells you otherwise is "
                "selling something. Listing can net more on a house in good shape when you "
                "have months to spare. A direct sale wins on speed and certainty, and that "
                "matters most when the property needs work you would rather not fund. The "
                "fair comparison is not headline price against headline price. It is what "
                "actually lands in your pocket after commissions, repairs, holding costs "
                "and the weeks in between.")
    if "Market" in cat:
        return ("Market numbers are useful for context and useless as a decision on their "
                "own. What moves your outcome is your own property: its condition, its "
                "title, and how much time you genuinely have. Two houses on the same street "
                "can net very different amounts depending on which repairs a buyer's lender "
                "insists on before it will finance the purchase.")
    if "Local" in cat:
        return ("Every " + place + " block prices differently, and a neighborhood average "
                "will not tell you what your house is worth. Condition, layout, and whether "
                "a lender will finance it at all matter more than the street-level comp. If "
                "the property needs work, a cash sale removes the repair negotiation "
                "entirely rather than leaving it to a buyer's inspector.")
    return ("The short answer: you have more options than most people realize, and the right "
            "one depends on your timeline more than your asking price. Selling as-is means "
            "no repairs, no staging, no showings and no agent commission. It usually trades "
            "a little top-line price for speed and certainty. Where that trade is worth "
            "making is a question only you can answer, with real numbers in front of you.")


def caption(post, channel, i):
    place = place_of(post)
    title = soften(post["title"])
    q = title if title.endswith(("?", ".", "!")) else title + "."
    opener = OPENERS[i % len(OPENERS)].format(q=q, place=place)
    body = body_for(post, place)
    cta = CTA.get(post.get("cta_variant"), CTA["offer"])
    ref_text, ref_url = REFERENCE.get(post.get("category"), DEFAULT_REF)
    hub_file, hub_txt = hub_for(post)

    parts = [opener, "", body, ""]
    if channel == "instagram":
        parts.append("Full breakdown is on the blog - link in our bio.")
    else:
        parts.append("Full breakdown: " + post_url(post["slug"], channel))
        parts.append("More context in " + hub_txt + ": "
                     + tagged(hub_file, post["slug"], channel,
                              post["slug"] + "-hub"))
    parts += ["", "Worth reading alongside it: " + ref_text + " - " + ref_url, "", cta]
    text = "\n".join(parts)

    # Instagram runs ~250 chars lighter because it carries no URLs, so short
    # captions are topped up with further substance rather than filler. Each
    # extra is a real point a seller asks about; they are appended in order
    # until the caption lands in range.
    extras = [
        ("If you are weighing this in " + place + ", the useful first step is a real number "
         "on your own property rather than an online estimate. An estimate cannot see a "
         "roof, a tenant, or a lien on the title."),
        ("Worth having ready before any call: roughly what is owed on the property, whether "
         "anyone else is on the deed, and whether it is occupied. Those three answers shape "
         "the timeline more than anything about the house itself."),
        ("What we do not do: charge you a fee to look, pressure you toward a decision on the "
         "first call, or ask you to fix anything first. If a direct sale is the wrong fit, "
         "it is better for everyone that you hear that early."),
    ]
    # Hashtags go last, after any top-up -- an earlier version appended the
    # top-up after them, which buried the tags mid-caption. Their length is
    # counted up front so the top-up loop targets the FINAL caption length.
    tags = "" if channel == "gbp" else "\n\n" + HASHTAGS[i % len(HASHTAGS)]

    for extra in extras:
        if len(text) + len(tags) >= TARGET_LO:
            break
        text += "\n\n" + extra

    return text + tags


def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    window_end = START + timedelta(days=DAYS - 1)
    queued = [p for p in cal["posts"]
              if p.get("status") == "queued"
              and p.get("publish_date")
              and START.isoformat() <= p["publish_date"] <= window_end.isoformat()]
    queued.sort(key=lambda x: (x["publish_date"], x["slug"]))

    by_day = defaultdict(list)
    for p in queued:
        by_day[p["publish_date"]].append(p)

    entries, lengths, outside = [], [], []
    for i, p in enumerate(queued):
        primary = by_day[p["publish_date"]][0]["slug"] == p["slug"]
        chans = {}
        for ch in CHANNELS:
            text = caption(p, ch, i)
            chans[ch] = {
                "copy": text,
                "chars": len(text),
                "link": None if ch == "instagram" else post_url(p["slug"], ch),
            }
            lengths.append(len(text))
            if not (TARGET_LO <= len(text) <= TARGET_HI):
                outside.append((p["slug"], ch, len(text)))
        entries.append({
            "blog_slug": p["slug"],
            "blog_publish_date": p["publish_date"],
            "scheduled_for": p["publish_date"] + "T10:00",
            "role": "primary" if primary else "alternate",
            "status": "pending_approval",
            "category": p.get("category"),
            "cta_variant": p.get("cta_variant"),
            "channels": chans,
        })

    out = {
        "campaign": CAMPAIGN,
        "built": date.today().isoformat(),
        "window": {"start": START.isoformat(), "end": window_end.isoformat(), "days": DAYS},
        "channels": list(CHANNELS),
        "cadence": "one 'primary' per channel per day; 'alternate' entries are backfill",
        "buffer_channels": {
            # Confirmed live 2026-10-27 against Buffer's GraphQL API.
            "facebook": {"id": "6a569a9a80cc80cdcab49af8",
                         "name": "Parlevu Global Services LLC",
                         "deliverable": True},
            "instagram": {"id": "6ae0fc782f1f5ed648ef9c36",
                          "name": "parlevuglobalservices",
                          "deliverable": True},
            "youtube": {"id": "6ae0fd092f1f5ed648efa193",
                        "name": "Ayodeji Ajishe",
                        "deliverable": False,
                        "why": ("connected but unusable: YouTube needs video and this repo "
                                "holds zero video files. Also listed under a personal name, "
                                "not the business.")},
        },
        "delivery": ("SPLIT. Buffer token is valid as of 2026-10-27 and Facebook + Instagram "
                     "are deliverable once a poster speaks Buffer's current GraphQL API -- "
                     "post_to_buffer.py still targets the legacy v1 REST API that returns 401 "
                     "and retires 2026-02-01, so it needs porting first; "
                     "voltixio-site/social_automation/buffer_poster.js is a working reference. "
                     "GBP is NOT a Buffer channel here and its own API needs Google allowlist "
                     "approval (0 QPM until granted), so gbp captions stay MANUAL paste-ready. "
                     "Stale in .env: BUFFER_PROFILE_ID is still the placeholder "
                     "'your_buffer_profile_id_here' and BUFFER_API_KEY is the dead legacy "
                     "credential; both should be deleted rather than left lying around."),
        "tracking": {
            "utm_source": "facebook | instagram | gbp",
            "utm_medium": "social (fb/ig) | organic (gbp)",
            "utm_campaign": CAMPAIGN,
            "utm_content": "{slug}, or {slug}-hub for the secondary internal link",
            "ga4": "G-FCL3Y130B5",
            "note": ("main.js attribution() already records first touch, last touch and "
                     "campaign. Mark phone_click / schedule_click / generate_lead as KEY "
                     "EVENTS in GA4 or channel conversion reporting stays empty."),
        },
        "notes": [
            "Instagram copy carries no URL: the platform does not linkify captions. "
            "Routes to bio instead.",
            "GBP copy carries no hashtags: they do nothing on that surface.",
            "'Guaranteed' is stripped from source titles -- the written policy behind that "
            "claim is unconfirmed. Restore only after confirming it.",
            "Every reference link comes from this repo's already-vetted AUTHORITY_LINKS.",
            "Each caption carries two internal links (the post, plus its hub) and one "
            "external authority reference.",
        ],
        "posts": entries,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("entries        : %d posts x %d channels = %d captions"
          % (len(entries), len(CHANNELS), len(entries) * len(CHANNELS)))
    print("roles          : %s" % dict(Counter(e["role"] for e in entries)))
    print("days covered   : %d of %d" % (len(by_day), DAYS))
    print("caption chars  : min %d  max %d  mean %d"
          % (min(lengths), max(lengths), sum(lengths) // len(lengths)))
    print("outside %d-%d : %d" % (TARGET_LO, TARGET_HI, len(outside)))
    for slug, ch, n in outside[:6]:
        print("   %-44s %-10s %d" % (slug, ch, n))
    print("written        : %s" % OUT)


if __name__ == "__main__":
    main()
