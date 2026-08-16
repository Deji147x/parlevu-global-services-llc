#!/usr/bin/env python3
"""Append Buffer captions for 75 Q&A posts to BUFFER_POSTS.csv."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
CSV = REPO / "BUFFER_POSTS.csv"

HOOKS = [
    "Got a FSBO question? 🏠",
    "Selling your house yourself?",
    "FSBO Q&A: ",
    "Real answers to real FSBO questions.",
    "What every FSBO seller should know. 👇",
]

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = cal["posts"] if isinstance(cal, dict) else cal
    qa_posts = [p for p in posts if p.get("category") == "FSBO Q&A"]

    existing = CSV.read_text(encoding="utf-8") if CSV.exists() else ""
    start_n = existing.count("\n")

    with CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for i, p in enumerate(qa_posts):
            url = f"https://www.parlevugloballlc.com/blog-{p['slug']}.html"
            hook = HOOKS[i % len(HOOKS)]
            variant = p.get("angle", "answer").split()[0]
            caption = (f"{hook} {p['title'][:60]} — honest answers, real Maryland/Virginia/DC "
                       f"numbers, zero pressure. Read free: {url} "
                       f"#FSBO #ForSaleByOwner #DIYRealEstate #MarylandHomes #SellYourHouse")
            w.writerow([start_n + i, p["title"], p["state"], caption, url, "Scheduled " + p["publish_date"]])

    print(f"✅ Appended {len(qa_posts)} Q&A captions to {CSV.name}")
    print(f"   Schedule 3x/week (Mon/Wed/Fri at 8 AM ET) starting Aug 1")

if __name__ == "__main__":
    main()
