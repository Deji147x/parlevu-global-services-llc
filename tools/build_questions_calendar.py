#!/usr/bin/env python3
"""Generate 75 Q&A briefs (3 per question from CSV) into content-calendar.json.

Strategy: Parse questionfinder-for-sale-by-owner-real-estate.csv, create 3 variants
per question (direct answer, deeper dive, comparison), stagger 3/day for 25 days.

Each post includes:
- YouTube embed (curated from Zillow, Realtor.com, RE/MAX)
- 2-3 external authority backlinks per post
- 3 CTA variants rotating
- Humanized, SEO-optimized 400-600 word content
"""
import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calendar_guard import (  # noqa: E402
    merge_briefs, removed_slugs, in_service_area, safe_slug, status_counts,
)

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / ".." / "Downloads" / "questionfinder-for-sale-by-owner-real-estate.csv"
CAL = REPO / "content-calendar.json"

# YouTube sources -- EMPTY ON PURPOSE.
#
# This list used to hold five invented video IDs (zestimate, realtor-guide,
# remax-fsbo, nar-pricing, zillow-marketing). Real YouTube IDs are 11
# characters; those were slugs that never existed, so every post built from
# this file shipped an iframe that rendered as an unavailable-video player.
# 31 of them reached production before being stripped on 2026-10-27.
#
# Leave this empty unless you have REAL 11-character video IDs you own or
# have permission to embed. validate_youtube() below rejects anything else,
# so a bad ID fails the build instead of reaching a live page.
YOUTUBE_SOURCES = []


def validate_youtube(entry):
    """Reject anything that is not a real 11-character YouTube ID."""
    m = re.search(r'[?&]v=([A-Za-z0-9_-]+)', entry.get('url', ''))
    if not m or len(m.group(1)) != 11:
        raise SystemExit(
            'Refusing to build: %r is not a valid YouTube ID. Real IDs are 11 '
            'characters. See the note on YOUTUBE_SOURCES.' % entry.get('url')
        )
    return entry

# External authority sources for backlinks (2-3 per post)
AUTHORITY_LINKS = {
    "pricing": [
        {"url": "https://www.realtor.com/advice/sell/", "text": "Realtor.com Seller Resources"},
        {"url": "https://www.zillow.com/sellers-guide/", "text": "Zillow Seller's Guide"},
    ],
    "costs": [
        {"url": "https://www.nar.realtor/research/research-and-statistics", "text": "NAR Research & Statistics"},
        {"url": "https://www.realtor.com/advice/sell/closing-costs/", "text": "Realtor.com: Closing Costs"},
    ],
    "process": [
        {"url": "https://www.realtor.com/advice/sell/for-sale-by-owner/", "text": "Realtor.com: FSBO Guide"},
        {"url": "https://www.marylandrealtor.org/", "text": "Maryland REALTORS® Association"},
    ],
    "comparison": [
        {"url": "https://www.realtor.com/advice/sell/", "text": "Realtor.com Comparison Tools"},
        {"url": "https://www.zillow.com/sellers-guide/", "text": "Zillow Agent vs FSBO"},
    ],
    "zillow": [
        {"url": "https://www.zillow.com/sellers-guide/", "text": "Zillow For Sale By Owner"},
        {"url": "https://www.zillow.com/sellers-guide/mls/", "text": "Zillow MLS Information"},
    ],
}

# CTA rotation (use short keys to match CTA_TEXT in generate_post.py)
CTAS = [
    "offer",
    "consult",
    "call",
]

def slugify(text):
    """Convert text to URL-safe slug, truncating on a word boundary.

    The old implementation sliced at [:50] mid-word, producing slugs like
    'how-to-list-real-estate-for-sa'. Delegates to calendar_guard.safe_slug.
    """
    return safe_slug(text, maxlen=60)

def get_authority_links(keyword):
    """Get 2-3 relevant authority links based on keyword."""
    if "price" in keyword.lower() or "cost" in keyword.lower():
        links = AUTHORITY_LINKS["pricing"] + AUTHORITY_LINKS["costs"]
    elif "process" in keyword.lower() or "how" in keyword.lower():
        links = AUTHORITY_LINKS["process"]
    elif "compare" in keyword.lower() or "vs" in keyword.lower():
        links = AUTHORITY_LINKS["comparison"]
    elif "zillow" in keyword.lower():
        links = AUTHORITY_LINKS["zillow"]
    else:
        links = AUTHORITY_LINKS["process"]
    return links[:3]

def main():
    # Read CSV
    if not CSV.exists():
        print(f"ERROR: keyword source not found:\n  {CSV.resolve()}\n"
              "Export it from questionfinder and place it there, or point CSV\n"
              "at the current file. Nothing was written.")
        return 1

    questions = []
    skipped_geo = []
    with open(CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row.get("Question", "").strip()
            if not q:
                continue
            # Reject keywords outside the MD/VA/DC service area — ranking for
            # "punta cana real estate for sale by owner" wins traffic that
            # cannot convert.
            if not in_service_area(q):
                skipped_geo.append(q)
                continue
            questions.append({
                "question": q,
                "volume": int(row.get("Volume/mo", 0) or 0),
                "signal": int(row.get("Google signal", 0) or 0),
            })

    if skipped_geo:
        print(f"  skipped {len(skipped_geo)} out-of-area keywords:")
        for q in skipped_geo[:5]:
            print(f"     - {q}")
        if len(skipped_geo) > 5:
            print(f"     ... and {len(skipped_geo) - 5} more")

    # Load existing calendar
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = cal["posts"]
    before = status_counts(posts)
    blocked = removed_slugs(posts)
    new_briefs = []

    # Find highest published date to resume after
    max_date = datetime.fromisoformat("2026-07-29")
    for p in posts:
        if p.get("status") == "queued" and p.get("publish_date"):
            try:
                d = datetime.fromisoformat(p["publish_date"])
                if d > max_date:
                    max_date = d
            except:
                pass

    # Generate 3 variants per question (75 total)
    current_date = datetime.fromisoformat("2026-07-29")
    post_count = 0
    cta_idx = 0

    for q_idx, q in enumerate(questions):
        question = q["question"]
        base_slug = slugify(question)

        # ONE post per question, not three.
        #
        # The old 3-variant split (what-is / complete-guide / vs-realtor) put
        # three near-identical pages against the same keyword, so they competed
        # with each other in the SERP instead of one page ranking. 69 such
        # duplicates were removed by hand on 2026-08-16. Complete Guide is kept
        # because it is the format that survived that dedup.
        variants = [
            {
                "suffix": "complete-guide",
                "title_prefix": "Complete Guide: ",
                "angle": "Deeper dive with statistics and local context",
                "image_style": "professional house inspection, closing process, paperwork",
            },
        ]

        for variant in variants:
            slug = safe_slug(f"{base_slug}-{variant['suffix']}", maxlen=70)
            if slug in blocked:
                continue

            brief = {
                "slug": slug,
                "title": f"{variant['title_prefix']}{question}",
                "primary_keyword": question,
                "secondary_keywords": [
                    f"FSBO {question.split()[0].lower()}",
                    f"for sale by owner {question.split()[-1].lower()}",
                ],
                "state": "MD",
                "city": None,
                "category": "FSBO Q&A",
                "kind": "question",
                "hub": "fsbo-support-maryland-virginia-dc.html",
                "image_prompt": f"{question} — {variant['image_style']}, professional real estate photography, Maryland/Virginia/DC context, no text, no watermark",
                "youtube_embed": (validate_youtube(YOUTUBE_SOURCES[post_count % len(YOUTUBE_SOURCES)])
                                  if YOUTUBE_SOURCES else None),
                "external_links": get_authority_links(question),
                "angle": variant["angle"],
                "cta_variant": CTAS[cta_idx % len(CTAS)],
                "status": "queued",
                "publish_date": current_date.isoformat().split("T")[0],
            }

            new_briefs.append(brief)
            post_count += 1
            cta_idx += 1

            # One post per day. The old 3/day burst existed only because each
            # question produced three variants.
            current_date += timedelta(days=1)

    # Merge instead of append-and-overwrite: protects published/generated/
    # removed entries and never deletes another builder's queued posts.
    cal["posts"] = merge_briefs(posts, new_briefs)
    posts = cal["posts"]
    cal["cadence"] = "1 post/day"
    cal["updated"] = datetime.now().isoformat().split("T")[0]

    CAL.write_text(json.dumps(cal, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {post_count} Q&A briefs from {len(questions)} in-area questions "
          f"(1 per question)")
    print(f"   before: {before}")
    print(f"   after : {status_counts(posts)}")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
