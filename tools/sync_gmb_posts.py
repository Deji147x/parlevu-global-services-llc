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


def summarize(brief):
    kw = brief.get("primary_keyword", "")
    city = brief.get("city") or brief.get("state") or "Maryland"
    body = (f"{brief['title']} "
            f"If you're weighing {kw} in {city}, here's what actually matters: "
            "what it costs, how long it takes, and how to sell as-is for cash "
            "with no repairs, no agent commissions, and no listing fees.")
    return textwrap.shorten(body, width=SUMMARY_LIMIT, placeholder=" ...")


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
