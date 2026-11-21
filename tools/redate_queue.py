#!/usr/bin/env python3
"""Re-date the queued posts to match what the publisher actually delivers.

THE PROBLEM
publish_date in content-calendar.json was set optimistically and the queue has
drifted far behind it:

  52 queued, 31 of them dated on or before today, oldest 24 days late.
  Measured throughput: 1.07 posts/day.
  The calendar says everything ships by 2026-12-12; at the real rate it is
  2027-01-08.

Nothing is broken. publish_next.py takes the first queued entry in calendar
order whatever its date, so posts keep going out one a day. What breaks is
every decision made FROM those dates:

  health_check reports a growing "overdue" count that is structural, not a
  fault, so a number meant to signal a problem signals nothing.

  Anything keyed to publish_date is wrong. That assumption already put a
  Google Business Profile post in front of customers on 2026-10-28 pointing
  at a page that had not published yet.

WHAT THIS DOES
Re-dates queued posts one per day from tomorrow, in their existing order, so
publish_date once again predicts when a post actually appears. Published and
removed entries are never touched. Order is preserved exactly -- this changes
when, never what or in what sequence.

  python tools/redate_queue.py                  # dry run
  python tools/redate_queue.py --rate 1.5       # if you publish faster
  python tools/redate_queue.py --apply
"""
import argparse
import io
import json
import os
from datetime import date, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "content-calendar.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=1.0,
                    help="posts per day to assume (default 1.0)")
    ap.add_argument("--start", help="first date to use (default: tomorrow)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cal = json.loads(io.open(CAL, encoding="utf-8").read())
    posts = cal["posts"]

    # Preserve existing order; only queued entries move.
    queued = [p for p in posts if p.get("status") == "queued"]
    if not queued:
        print("nothing queued")
        return

    start = (date.fromisoformat(args.start) if args.start
             else date.today() + timedelta(days=1))

    today = date.today().isoformat()
    before_overdue = sum(1 for p in queued if (p.get("publish_date") or "") <= today)
    before_last = max((p.get("publish_date") or "") for p in queued)

    per_day = max(1, int(round(args.rate)))
    changes = []
    day = start
    i = 0
    for p in queued:
        new = day.isoformat()
        if p.get("publish_date") != new:
            changes.append((p["slug"], p.get("publish_date"), new))
        p["publish_date"] = new
        i += 1
        if i % per_day == 0:
            day += timedelta(days=1)

    after_last = max(p["publish_date"] for p in queued)
    after_overdue = sum(1 for p in queued if p["publish_date"] <= today)

    print("queued posts      : %d" % len(queued))
    print("rate assumed      : %.2f/day" % args.rate)
    print()
    print("  overdue  before %-4d  ->  after %d" % (before_overdue, after_overdue))
    print("  last date before %s  ->  after %s" % (before_last, after_last))
    print("  entries re-dated : %d" % len(changes))
    print()
    for slug, old, new in changes[:8]:
        print("    %-42s %s -> %s" % (slug[:42], old, new))
    if len(changes) > 8:
        print("    ... and %d more" % (len(changes) - 8))

    if not args.apply:
        print("\nDRY RUN - content-calendar.json not written.")
        return

    cal["updated"] = date.today().isoformat()
    io.open(CAL, "w", encoding="utf-8", newline="\n").write(
        json.dumps(cal, indent=1, ensure_ascii=False) + "\n")
    print("\nAPPLIED to content-calendar.json")
    print("Order and content unchanged; only publish_date moved.")


if __name__ == "__main__":
    main()
