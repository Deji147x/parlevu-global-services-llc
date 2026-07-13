"""Build content-calendar.json — 120 SEO post briefs for Parlevu Global Services LLC.

Deterministic and re-runnable: edit the topic/city lists below and re-run to
refill the queue. Existing published entries are preserved (matched by slug).

Usage:  python tools/build_calendar.py [--start YYYY-MM-DD]
"""
import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"

STATES = {
    "MD": {"name": "Maryland", "hub": "sell-house-fast-maryland.html"},
    "VA": {"name": "Virginia", "hub": "sell-house-fast-virginia.html"},
    "DC": {"name": "Washington DC", "hub": "sell-house-fast-washington-dc.html"},
}

# 13 seller situations x 3 states = 39 long-tail posts (highest intent)
SITUATIONS = [
    ("foreclosure", "Facing Foreclosure in {st}? Your Options to Sell Fast and Protect Your Credit", "stop foreclosure {stl}", "Foreclosure Help"),
    ("inherited-probate", "Selling an Inherited House in {st}: Probate Rules, Taxes, and Your Fastest Options", "sell inherited house {stl}", "Inherited Properties"),
    ("divorce", "Selling a House During Divorce in {st}: A Clear Path Forward", "selling house during divorce {stl}", "Life Transitions"),
    ("liens-violations", "Can You Sell a House With Liens or Code Violations in {st}? Yes — Here's How", "sell house with lien {stl}", "Legal Issues"),
    ("fire-damage", "Selling a Fire-Damaged House in {st}: What Insurance Won't Tell You", "sell fire damaged house {stl}", "Distressed Property"),
    ("water-mold", "Selling a House With Water Damage or Mold in {st}", "sell house with mold {stl}", "Distressed Property"),
    ("foundation", "How to Sell a House With Foundation Problems in {st}", "sell house foundation problems {stl}", "Distressed Property"),
    ("hoarder-house", "Selling a Hoarder House in {st}: No Cleanout Required", "sell hoarder house {stl}", "Distressed Property"),
    ("bad-tenants", "Selling a Rental Property With Tenants in {st}: Rights, Rules, and Cash Options", "sell rental property with tenants {stl}", "Landlord Exit"),
    ("vacant-house", "Selling a Vacant or Abandoned House in {st} Before It Costs You More", "sell vacant house {stl}", "Landlord Exit"),
    ("underwater-mortgage", "Owe More Than Your {st} Home Is Worth? How to Sell an Underwater House", "sell underwater house {stl}", "Financial Hardship"),
    ("relocation", "Relocating From {st}? How to Sell Your House Fast Before the Move", "sell house fast relocation {stl}", "Life Transitions"),
    ("downsizing", "Downsizing in {st}: A Retiree's Guide to Selling Without the Stress", "downsizing selling home {stl}", "Life Transitions"),
]

# City pages — 36 "sell my house fast in {city}" posts
CITIES = {
    "MD": ["Baltimore", "Columbia", "Silver Spring", "Rockville", "Frederick",
           "Annapolis", "Bowie", "Glen Burnie", "Dundalk", "Towson",
           "Upper Marlboro", "Waldorf", "Gaithersburg", "Hagerstown"],
    "VA": ["Alexandria", "Arlington", "Fairfax", "Woodbridge", "Manassas",
           "Fredericksburg", "Richmond", "Norfolk", "Virginia Beach",
           "Chesapeake", "Hampton", "Newport News"],
    "DC": ["Anacostia", "Petworth", "Brookland", "Columbia Heights",
           "Deanwood", "Congress Heights", "Fort Totten", "Shaw",
           "Trinidad", "Capitol Hill", "Ivy City", "Woodridge"],
}

# Process / education short-tails — 24 posts (rotate state focus for local flavor)
PROCESS = [
    ("how-cash-buyers-work", "How Cash Home Buyers Work in {st}: The Complete Process Explained", "how do cash home buyers work"),
    ("how-offers-calculated", "How Cash Offers Are Calculated on {st} Homes (Real Numbers)", "how do cash buyers determine offer price"),
    ("closing-costs", "Who Pays Closing Costs When Selling a House in {st}?", "who pays closing costs {stl}"),
    ("paperwork-checklist", "Paperwork You Need to Sell Your House in {st}: Complete Checklist", "paperwork to sell house {stl}"),
    ("sell-without-realtor", "How to Sell Your House Without a Realtor in {st}", "sell house without realtor {stl}"),
    ("as-is-cost", "How Much Do You Really Lose Selling a House As-Is in {st}?", "how much do you lose selling as is"),
    ("timeline", "How Fast Can You Really Sell a House for Cash in {st}? The Honest Timeline", "how fast can I sell my house for cash"),
    ("avoid-scams", "How to Spot a Legitimate Cash Home Buyer in {st} (and Avoid Scams)", "are we buy houses companies legitimate"),
]

# Comparison / trust — 12 posts
COMPARISON = [
    ("cash-vs-listing", "Selling for Cash vs. Listing With an Agent in {st}: Real Cost Comparison", "cash offer vs listing {stl}"),
    ("ibuyer-vs-local", "iBuyers vs. Local Cash Buyers in {st}: Which Gets You More?", "ibuyer vs cash buyer {stl}"),
    ("fsbo-vs-cash", "FSBO vs. Cash Sale in {st}: Which Saves You More Money?", "fsbo vs cash sale {stl}"),
    ("best-time-to-sell", "Best (and Worst) Time to Sell a House in {st}", "best time to sell house {stl}"),
]

# Market / seasonal — 9 posts
MARKET = [
    ("market-update", "{st} Housing Market Update: What Sellers Need to Know Right Now", "{stl} housing market"),
    ("home-values", "What's My House Worth? Understanding {st} Home Values", "what is my house worth {stl}"),
    ("winter-selling", "Selling Your {st} House in the Off-Season: Why Cash Buyers Don't Care About the Calendar", "sell house winter {stl}"),
]

CTA_VARIANTS = ["offer", "consult", "call"]

IMG_STYLES = [
    "professional real estate photography, warm natural light",
    "editorial photo style, golden hour lighting",
    "clean architectural photography, bright daylight",
    "documentary photo style, soft morning light",
]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:70].rstrip("-")


def brief(slug, title, keyword, state, category, city=None, kind="situation"):
    stname = STATES[state]["name"]
    place = city or stname
    return {
        "slug": slug,
        "title": title,
        "primary_keyword": keyword,
        "secondary_keywords": [
            f"we buy houses {place.lower()}",
            f"cash home buyers {place.lower()}",
            f"sell my house fast {place.lower()}",
        ],
        "state": state,
        "city": city,
        "category": category,
        "kind": kind,
        "hub": STATES[state]["hub"],
        "image_prompt": f"{title.split(':')[0]}, {place}, residential house exterior, "
                        f"{IMG_STYLES[hash(slug) % len(IMG_STYLES)]}, no text, no watermark",
        "cta_variant": CTA_VARIANTS[hash(slug) % len(CTA_VARIANTS)],
        "status": "queued",
        "publish_date": None,
    }


def build_briefs():
    briefs = []
    # 1) situations x states (39)
    for key, title_t, kw_t, cat in SITUATIONS:
        for st in STATES:
            stname = STATES[st]["name"]
            briefs.append(brief(
                f"{key}-{st.lower()}",
                title_t.format(st=stname),
                kw_t.format(stl=stname.lower()),
                st, cat, kind="situation"))
    # 2) city pages (36)
    for st, cities in CITIES.items():
        for city in cities[:12]:
            briefs.append(brief(
                f"sell-my-house-fast-{slugify(city)}",
                f"Sell My House Fast in {city}: How Cash Buyers Help "
                f"{'DC' if st == 'DC' else city} Homeowners",
                f"sell my house fast {city.lower()}",
                st, "Local Guides", city=city, kind="city"))
    # 3) process x rotating state (24)
    for i, (key, title_t, kw_t) in enumerate(PROCESS):
        for st in STATES:
            stname = STATES[st]["name"]
            briefs.append(brief(
                f"{key}-{st.lower()}",
                title_t.format(st=stname),
                kw_t.format(stl=stname.lower()) if "{stl}" in kw_t else kw_t,
                st, "Selling Guides", kind="process"))
    # 4) comparison x states (12)
    for key, title_t, kw_t in COMPARISON:
        for st in STATES:
            stname = STATES[st]["name"]
            briefs.append(brief(
                f"{key}-{st.lower()}",
                title_t.format(st=stname),
                kw_t.format(stl=stname.lower()),
                st, "Comparisons", kind="comparison"))
    # 5) market x states (9)
    for key, title_t, kw_t in MARKET:
        for st in STATES:
            stname = STATES[st]["name"]
            briefs.append(brief(
                f"{key}-{st.lower()}",
                title_t.format(st=stname),
                kw_t.format(stl=stname.lower()),
                st, "Market Updates", kind="market"))
    return briefs[:120]


def interleave_for_calendar(briefs):
    """Order posts so each 30-day cycle mixes states and kinds (no 30 straight
    MD posts) — Google prefers topical + geographic variety over bursts."""
    by_state = {"MD": [], "VA": [], "DC": []}
    for b in briefs:
        by_state[b["state"]].append(b)
    ordered, i = [], 0
    while any(by_state.values()):
        st = ["MD", "VA", "DC"][i % 3]
        if by_state[st]:
            ordered.append(by_state[st].pop(0))
        i += 1
    return ordered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None, help="First publish date YYYY-MM-DD")
    args = ap.parse_args()
    start = date.fromisoformat(args.start) if args.start else date.today() + timedelta(days=1)

    published = {}
    if CAL.exists():
        for e in json.loads(CAL.read_text(encoding="utf-8"))["posts"]:
            if e.get("status") == "published":
                published[e["slug"]] = e

    briefs = interleave_for_calendar(build_briefs())
    d = start
    for b in briefs:
        if b["slug"] in published:
            b.update(published[b["slug"]])
            continue
        b["publish_date"] = d.isoformat()
        d += timedelta(days=1)

    CAL.write_text(json.dumps({
        "site": "https://www.parlevugloballlc.com",
        "cadence": "1 post/day",
        "generated": date.today().isoformat(),
        "posts": briefs,
    }, indent=2), encoding="utf-8")
    print(f"Wrote {len(briefs)} briefs to {CAL} (first publish {start})")


if __name__ == "__main__":
    main()
