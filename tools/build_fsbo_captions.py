#!/usr/bin/env python3
"""Append Buffer captions for the FSBO series to BUFFER_POSTS.csv."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
CSV = REPO / "BUFFER_POSTS.csv"

HOOKS = [
    "Thinking of selling your home yourself?",
    "FSBO sellers: this one's for you.",
    "Selling by owner in the DMV?",
    "No agent? No problem — if you know the rules.",
    "Before you plant that FSBO sign, read this.",
]
TAGS = "#FSBO #ForSaleByOwner #MarylandRealEstate #BaltimoreHomes #SellYourHouse #DMVRealEstate"

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = cal["posts"] if isinstance(cal, dict) else cal
    fsbo = [p for p in posts if p.get("category") == "FSBO Support"]

    existing = CSV.read_text(encoding="utf-8") if CSV.exists() else ""
    start_n = existing.count("\n")

    with CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for i, p in enumerate(fsbo):
            url = f"https://www.parlevugloballlc.com/blog-{p['slug']}.html"
            hook = HOOKS[i % len(HOOKS)]
            kind = "📚 NEW GUIDE" if p["kind"] == "pillar" else "💡"
            caption = (f"{kind} {hook} {p['title']} — honest answers, real Maryland/Virginia/DC "
                       f"numbers, no fluff. Read it free: {url} {TAGS}")
            w.writerow([start_n + i, p["title"], p["state"], caption, url, "Scheduled " + p["publish_date"]])
    print(f"Appended {len(fsbo)} FSBO captions to {CSV.name}")

if __name__ == "__main__":
    main()
