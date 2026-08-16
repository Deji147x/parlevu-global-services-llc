"""Post latest blog posts to Buffer.com via API.
Requires: BUFFER_API_KEY environment variable

Usage: python tools/post_to_buffer.py [--posts 3] [--schedule MON,WED,FRI]
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_PROFILE_ID = os.getenv("BUFFER_PROFILE_ID")
SITE_URL = os.getenv("SITE_URL", "https://www.parlevugloballlc.com")

if not BUFFER_API_KEY:
    print("ERROR: BUFFER_API_KEY not set. Set it in .env file or environment.")
    sys.exit(1)

if not BUFFER_PROFILE_ID:
    print("ERROR: BUFFER_PROFILE_ID not set. Get it from Buffer account settings.")
    sys.exit(1)


def get_latest_posts(count=3):
    """Get the N most recently published posts from calendar."""
    cal_path = REPO / "content-calendar.json"
    if not cal_path.exists():
        print("content-calendar.json not found")
        return []

    cal = json.loads(cal_path.read_text(encoding="utf-8"))
    published = [p for p in cal["posts"] if p["status"] == "published"]
    return sorted(published, key=lambda x: x.get("publish_date", ""), reverse=True)[:count]


def post_to_buffer(post_data, profile_id, schedule_time=None):
    """Post to Buffer using API v1."""
    url = "https://api.bufferapp.com/1/updates/create.json"

    text = f"""✨ {post_data['title']}

{post_data.get('intro', 'Read the full article').split('.')[0]}.

Learn more about selling your {post_data.get('location', 'home')} for cash. No repairs. No fees. No agent commissions.

#CashBuyer #RealEstate #{post_data['state']}"""

    payload = {
        "access_token": BUFFER_API_KEY,
        "profile_ids[]": profile_id,
        "text": text,
        "link": f"{SITE_URL}/blog-{post_data['slug']}.html",
    }

    if schedule_time:
        payload["scheduled_at"] = int(schedule_time.timestamp())
    else:
        payload["now"] = True

    req_data = urllib.parse.urlencode(payload).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=req_data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        if result.get("success"):
            print(f"  ✓ Posted to Buffer: {post_data['title']}")
            return True
        else:
            print(f"  ✗ Buffer error: {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"  ✗ Failed to post: {e}")
        return False


def schedule_posts(posts, schedule_days=None):
    """Schedule posts for 3x per week (Mon/Wed/Fri)."""
    if schedule_days is None:
        schedule_days = [0, 2, 4]  # Monday, Wednesday, Friday

    now = datetime.now()
    scheduled = []

    for i, post in enumerate(posts):
        # Find next occurrence of scheduled day
        days_ahead = (schedule_days[i % len(schedule_days)] - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # If today is the day, schedule for next week

        schedule_time = now + timedelta(days=days_ahead, hours=9)  # 9 AM posting time
        scheduled.append((post, schedule_time))
        print(f"Scheduling '{post['title']}' for {schedule_time.strftime('%A %I:%M %p')}")

    return scheduled


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=3, help="Number of posts to share")
    ap.add_argument("--profile-id", help="Override BUFFER_PROFILE_ID")
    ap.add_argument("--now", action="store_true", help="Post immediately (don't schedule)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be posted")
    args = ap.parse_args()

    profile_id = args.profile_id or BUFFER_PROFILE_ID
    posts = get_latest_posts(args.posts)

    if not posts:
        print("No published posts found in calendar")
        return

    print(f"Found {len(posts)} published posts. Preparing to share {len(posts)} to Buffer...\n")

    if args.now:
        print("Posting immediately...\n")
        for post in posts:
            if args.dry_run:
                print(f"  DRY: {post['title']}")
            else:
                post_to_buffer(post, profile_id)
    else:
        scheduled = schedule_posts(posts)
        print()
        for post, schedule_time in scheduled:
            if args.dry_run:
                print(f"  DRY: {post['title']} → {schedule_time.strftime('%A')}")
            else:
                post_to_buffer(post, profile_id, schedule_time)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
