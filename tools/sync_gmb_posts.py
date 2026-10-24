"""Build Google Business Profile local-post payloads from content-calendar.json.

Status: DRY-RUN ONLY. The GBP API is allowlisted (Google must approve access;
quota is 0 QPM until then), so this script never calls the network. It renders
exactly what would be posted so the copy can be reviewed offline.

Flow:
  1. Read published posts from content-calendar.json.
  2. Render a localPosts payload for each (summary, CTA, media URL).
  3. Print them, or write to --out for review / handoff.

Going live later needs: approved GBP API access, OAuth credentials (service
accounts are generally NOT supported), and the location name
(accounts/{account}/locations/{location}). Wire those into post_payloads().

Usage:
  python tools/sync_gmb_posts.py --dry-run
  python tools/sync_gmb_posts.py --dry-run --limit 5 --since 2026-08-01
  python tools/sync_gmb_posts.py --dry-run --out gmb-payloads.json
"""
import argparse
import json
import textwrap
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
SITE = "https://parlevugloballlc.com"

# GBP caps local-post summaries at 1500 chars; keep well under for readability.
SUMMARY_LIMIT = 700


def published(cal, since=None, limit=None):
    out = []
    for p in cal["posts"]:
        if p.get("status") != "published":
            continue
        on = p.get("published_on")
        if since and (not on or on < since):
            continue
        out.append(p)
    out.sort(key=lambda p: p.get("published_on") or "", reverse=True)
    return out[:limit] if limit else out


# The Business Profile is a Baltimore listing. A post's own city/state field
# describes who the article is for, not where the profile is, so using it put
# "in VA" and "in DC" on a Baltimore profile. Local relevance is the whole point
# of this channel, so the copy always speaks from Baltimore.
HOME = "Baltimore"
WIDER = "Baltimore and the DMV"

# Rotated so a month of weekly posts does not read as one template. Index is
# derived from the slug, so a given post always renders the same way.
OPENERS = [
    "{title}",
    "{title} Here is the short version for {home} homeowners.",
    "A question we get from {home} sellers: {title}",
]

CLOSERS = [
    "We buy houses in {wider} as-is, with no repairs, no agent commissions and "
    "a closing date you choose.",
    "If selling as-is would suit you better than listing, we buy throughout "
    "{wider} with no commissions and no repair bill.",
    "We buy as-is across {wider}. No realtor, no fees, and you pick the "
    "timeline.",
]


def summarize(brief):
    """One self-contained paragraph, complete sentences, never truncated."""
    title = brief["title"].strip()
    if not title.endswith((".", "?", "!")):
        title += "."
    i = sum(ord(c) for c in brief["slug"]) % len(OPENERS)
    opener = OPENERS[i].format(title=title, home=HOME)
    closer = CLOSERS[i % len(CLOSERS)].format(wider=WIDER)
    body = opener + " " + closer
    if len(body) <= SUMMARY_LIMIT:
        return body
    # Drop the opener's extra sentence rather than cut a word in half.
    short = title + " " + closer
    return short if len(short) <= SUMMARY_LIMIT else title


def payload(brief):
    slug = brief["slug"]
    p = {
        "languageCode": "en-US",
        "summary": summarize(brief),
        "topicType": "STANDARD",
        "callToAction": {
            "actionType": "LEARN_MORE",
            "url": f"{SITE}/blog-{slug}.html",
        },
    }
    img = REPO / "images" / "blog" / f"{slug}.jpg"
    if img.exists():
        p["media"] = [{
            "mediaFormat": "PHOTO",
            "sourceUrl": f"{SITE}/images/blog/{slug}.jpg",
        }]
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="render payloads without calling the API (default, and currently the only mode)")
    ap.add_argument("--live", action="store_true",
                    help="reserved; refuses to run until GBP API access is approved")
    ap.add_argument("--limit", type=int, help="only the N most recent published posts")
    ap.add_argument("--since", help="only posts published on/after YYYY-MM-DD")
    ap.add_argument("--out", help="write payloads to this JSON file instead of stdout")
    args = ap.parse_args()

    if args.live:
        raise SystemExit(
            "--live is not implemented. The GBP API requires allowlist approval "
            "(0 QPM until granted) plus OAuth credentials and a location name. "
            "Request access via Google's GBP API contact form first."
        )

    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = published(cal, since=args.since, limit=args.limit)
    if not posts:
        print("No published posts matched.")
        return

    payloads = [{"slug": p["slug"], "published_on": p.get("published_on"),
                 "localPost": payload(p)} for p in posts]

    if args.out:
        Path(args.out).write_text(json.dumps(payloads, indent=2), encoding="utf-8")
        print(f"Wrote {len(payloads)} payload(s) to {args.out}")
        return

    print(f"DRY RUN — {len(payloads)} local post(s) would be created "
          f"(nothing sent; generated {date.today().isoformat()})\n")
    for i, item in enumerate(payloads, 1):
        lp = item["localPost"]
        print(f"[{i}] {item['slug']}  (published {item['published_on']})")
        print(f"    summary: {lp['summary'][:120]}...")
        print(f"    cta    : {lp['callToAction']['actionType']} -> {lp['callToAction']['url']}")
        print(f"    media  : {lp['media'][0]['sourceUrl'] if 'media' in lp else '(none)'}")
        print()


if __name__ == "__main__":
    main()
