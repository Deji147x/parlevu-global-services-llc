#!/usr/bin/env python3
"""Generate 40 service-focused post briefs into content-calendar.json."""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calendar_guard import (  # noqa: E402
    merge_briefs, removed_slugs, in_service_area, status_counts,
)

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"

# Service posts (40 total): cluster, slug, title, keyword, cta_variant
SERVICE_POSTS = [
    # Cluster 1: As-Is (4 posts)
    ("as-is", "buy-houses-for-cash", "Buy Houses for Cash in Maryland — Fast, No Contingencies", "buy houses for cash", "offer"),
    ("as-is", "as-is-home-sales", "As-Is Home Sales in Maryland — Sell Without Repairs", "as-is home sales", "offer"),
    ("as-is", "sell-without-repairs", "Sell Your House Without Repairs — Cash Offer in 24 Hours", "sell house without repairs", "consult"),
    ("as-is", "fast-cash-offer-home", "Get a Fast Cash Offer on Your Home — 24 Hours Guaranteed", "fast cash offer home", "call"),

    # Cluster 2: Speed (4 posts)
    ("speed", "sell-quickly-maryland", "Sell Your House Quickly in Maryland for Cash", "sell house quickly maryland", "offer"),
    ("speed", "quick-home-sale", "Quick Home Sales in Maryland & DMV — Fair Cash Offers", "quick home sale", "consult"),
    ("speed", "7-day-closing", "7-Day Home Closing in Maryland — Cash Buyers", "7 day home closing", "call"),
    ("speed", "sell-before-deadline", "Sell Your Home Before Deadline — Cash Buyers Available", "sell home before deadline", "offer"),

    # Cluster 3: Cash (4 posts)
    ("cash", "cash-offer-home", "Get a Cash Offer on Your Home in 24 Hours", "cash offer home", "offer"),
    ("cash", "no-appraisal-sale", "Sell Your Home Without Appraisal — Cash Buyers in Maryland", "no appraisal home sale", "consult"),
    ("cash", "home-buying-cash", "Home Buying for Cash in Maryland — Fair Offers, No Fees", "home buying cash", "call"),
    ("cash", "avoid-financing-delays", "Avoid Financing Delays — Sell for Cash in Maryland", "avoid financing delays", "offer"),

    # Cluster 4: Distressed (5 posts)
    ("distressed", "damaged-homes-buy", "We Buy Damaged Homes in Maryland for Cash", "damaged homes buy", "offer"),
    ("distressed", "fire-damaged-house", "Sell Fire-Damaged House for Cash in Maryland", "fire damaged house", "consult"),
    ("distressed", "water-damaged-home", "Water Damaged Home? Sell for Cash in Maryland & DMV", "water damaged home", "call"),
    ("distressed", "code-violation-house", "Sell Your House With Code Violations for Cash", "code violation house", "offer"),
    ("distressed", "storm-damaged-property", "Storm Damaged Property? Cash Buyers in Maryland", "storm damaged property", "consult"),

    # Cluster 5: Probate (3 posts)
    ("probate", "inherited-property-buyers", "Sell Inherited Property Fast for Cash in Maryland", "inherited property buyers", "offer"),
    ("probate", "sell-probate-property", "Sell Probate Property in Maryland Without Court Delays", "sell probate property", "consult"),
    ("probate", "estate-home-sale", "Quick Estate Home Sale in Maryland — No Probate Delays", "estate home sale", "call"),

    # Cluster 6: Divorce (3 posts)
    ("divorce", "divorce-property-sale", "Sell Your Property Quickly During Divorce in Maryland", "divorce property sale", "offer"),
    ("divorce", "marital-home-sale", "Marital Home Sale in Maryland — Fair Cash Offer", "marital home sale", "consult"),
    ("divorce", "sell-during-divorce", "Sell Your House During Divorce — Fast Cash Sale", "sell house during divorce", "call"),

    # Cluster 7: Foreclosure (4 posts)
    ("foreclosure", "stop-foreclosure", "Stop Foreclosure in Maryland Before Auction", "stop foreclosure maryland", "offer"),
    ("foreclosure", "foreclosure-alternatives", "Foreclosure Alternatives in Maryland — Sell for Cash", "foreclosure alternatives", "consult"),
    ("foreclosure", "short-sale-vs-cash", "Short Sale vs Cash Sale — Which Is Better in Maryland?", "short sale vs cash sale", "call"),
    ("foreclosure", "foreclosure-timeline", "Maryland Foreclosure Timeline — How Fast Can You Sell?", "foreclosure timeline maryland", "offer"),

    # Cluster 8: Off-Market (2 posts)
    ("offmarket", "private-home-sale", "Private Home Sale in Maryland — No Public Listing", "private home sale", "consult"),
    ("offmarket", "avoid-realtor", "Sell Without a Realtor in Maryland — Direct Cash Sale", "avoid real estate agent", "call"),

    # Cluster 9: Baltimore County (2 posts)
    ("baltimore", "sell-fast-baltimore", "Sell Your House Fast in Baltimore County for Cash", "sell house fast baltimore", "offer"),
    ("baltimore", "baltimore-cash-buyer", "Local Cash Home Buyer in Baltimore County, Maryland", "baltimore cash home buyer", "consult"),

    # Cluster 10: Maryland (3 posts)
    ("maryland", "cash-buyers-maryland", "Cash Home Buyers Maryland — Local, Trusted, Fair", "cash home buyers maryland", "call"),
    ("maryland", "sell-fast-maryland", "Sell Your House Fast in Maryland for Cash", "sell house fast maryland", "offer"),
    ("maryland", "buy-any-condition-md", "Buy Houses Maryland in Any Condition — Fair Cash", "buy house maryland any condition", "consult"),

    # Cluster 11: DMV (3 posts)
    ("dmv", "cash-buyers-dmv", "Cash Buyers in the DMV — Maryland, Virginia, DC", "cash buyers dmv", "call"),
    ("dmv", "sell-fast-dmv", "Sell Your House Fast in the DMV for Cash", "sell house fast dmv", "offer"),
    ("dmv", "dmv-distressed-buyers", "Distressed Property Buyers in the DMV — Any Condition", "dmv distressed buyers", "consult"),
]

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = cal["posts"]
    before = status_counts(posts)
    blocked = removed_slugs(posts)
    new_briefs = []

    # Start date: Oct 27, 2026 (after FSBO series)
    current_date = datetime.fromisoformat("2026-10-27")
    cta_keys = ["offer", "consult", "call"]
    cta_idx = 0

    for cluster, slug, title, keyword, cta in SERVICE_POSTS:
        if slug in blocked or not in_service_area(f"{title} {keyword}"):
            continue
        brief = {
            "slug": slug,
            "title": title,
            "primary_keyword": keyword,
            "secondary_keywords": [
                f"{keyword.split()[0]} cash",
                f"{keyword} fast",
                f"{keyword} no repairs",
            ],
            "state": "MD",
            "city": None,
            "category": "Service" if cluster != "baltimore" and cluster != "maryland" and cluster != "dmv" else f"Service — {cluster.title()}",
            "kind": "question",
            "hub": "index.html",
            "image_prompt": f"{title} — professional real estate photography, {cluster} context, Maryland/DMV, clean minimal design, no text, no watermark",
            "youtube_embed": None,  # Will be populated from youtube_library.json
            "external_links": [],  # Will be populated based on cluster
            "cta_variant": cta,
            "status": "queued",
            "publish_date": current_date.isoformat().split("T")[0],
            "cluster": cluster,
        }

        new_briefs.append(brief)

        # Increment date every 2 posts (2 posts per day)
        if len([p for p in new_briefs if p.get("cluster") == cluster]) % 2 == 0:
            current_date += timedelta(days=1)

    # Merge, don't append: this script had no slug dedup, so a second run
    # duplicated every service post.
    cal["posts"] = posts = merge_briefs(posts, new_briefs)
    cal["cadence"] = "1-2 posts/day (service posts) Oct 27 - Dec 31"
    cal["updated"] = datetime.now().isoformat().split("T")[0]

    CAL.write_text(json.dumps(cal, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(new_briefs)} service briefs")
    print(f"   before: {before}")
    print(f"   after : {status_counts(posts)}")

if __name__ == "__main__":
    main()
