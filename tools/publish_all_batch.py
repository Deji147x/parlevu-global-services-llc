"""Generate all 120 posts in batch, spread across 30 days.
Fully automated: generates, commits, pushes to GitHub, stages to upload-queue.

Usage: python tools/publish_all_batch.py --start-date 2026-07-14 --posts 120 [--dry-run]
"""
import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from generate_post import generate as gen_post

def batch_generate(start_date_str, num_posts, dry_run=False):
    """Generate N posts with dates spread across calendar."""
    start = date.fromisoformat(start_date_str)
    cal = json.loads((REPO / "content-calendar.json").read_text(encoding="utf-8"))

    queued = [p for p in cal["posts"] if p["status"] == "queued"]
    if not queued:
        print("No queued posts found. Refill with build_calendar.py.")
        return

    posts_to_gen = queued[:min(num_posts, len(queued))]
    print(f"Generating {len(posts_to_gen)} posts starting {start_date_str}...")

    generated_files = []
    for i, brief in enumerate(posts_to_gen, 1):
        slug = brief["slug"]
        pub_date = start + timedelta(days=i-1)
        pct = round(100 * i / len(posts_to_gen))

        if dry_run:
            print(f"  [{pct:3d}%] {i:3d}/{len(posts_to_gen)} DRY: {slug[:40]:40s} → {pub_date}")
            continue

        try:
            html_file = gen_post(slug)
            generated_files.append(html_file)
            brief["publish_date"] = pub_date.isoformat()
            brief["status"] = "generated"
            print(f"  [{pct:3d}%] {i:3d}/{len(posts_to_gen)} {slug[:40]:40s} → {pub_date}")
            sys.stdout.flush()
        except Exception as e:
            print(f"  ERROR generating {slug}: {e}")
            continue

    if not dry_run and generated_files:
        # Update calendar with new dates
        (REPO / "content-calendar.json").write_text(
            json.dumps(cal, indent=2), encoding="utf-8")
        print(f"\nGenerated {len(generated_files)} posts.")

        # Commit
        subprocess.run(["git", "-C", str(REPO), "add", "-A"], check=True)
        msg = f"""Batch generate all {len(posts_to_gen)} posts across 30 days

Generated {len(generated_files)} blog posts with dates from {start_date_str} to {(start + timedelta(days=len(posts_to_gen)-1)).isoformat()}.
All posts include:
- SEO-optimized content (2000-3000 chars)
- Unique images (Pollinations.ai with Unsplash fallback)
- Article + FAQPage + LocalBusiness JSON-LD schema
- CTAs (appointment link + phone)
- Social media links (Facebook, Instagram, LinkedIn, X, Pinterest)
- Internal links to hubs and related posts
- Local state law callouts

Ready for daily cron publishing via publish_next.py

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"""
        subprocess.run(["git", "-C", str(REPO), "commit", "-m", msg], check=True)

        # Push
        r = subprocess.run(["git", "-C", str(REPO), "push", "origin", "main"],
                          capture_output=True, text=True)
        if r.returncode == 0:
            print("✓ Pushed to GitHub")
        else:
            print(f"WARNING: Push failed:\n{r.stderr}")

        print(f"\n✓ All {len(generated_files)} posts ready for daily publishing.")
        return generated_files
    elif dry_run:
        print(f"\nDRY RUN: Would generate {len(posts_to_gen)} posts")
        return []

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", default="2026-07-14", help="Start date (YYYY-MM-DD)")
    ap.add_argument("--posts", type=int, default=120, help="Number of posts to generate")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen without generating")
    args = ap.parse_args()

    batch_generate(args.start_date, args.posts, dry_run=args.dry_run)
