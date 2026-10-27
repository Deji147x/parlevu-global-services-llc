#!/usr/bin/env python3
"""Attach a topic-matched image to every FAQ social caption.

WHY THIS IS NOT COSMETIC
------------------------
Instagram rejects text-only posts and Buffer requires a declared media type
for them, so until every Instagram entry carries an image those 30 captions
cannot publish at all. Images also lift Facebook and Google Business Profile,
which matters when the measured Facebook reach is 7-15 impressions per post.

HOW IMAGES ARE CHOSEN
---------------------
Each FAQ gets the blog image whose slug best matches its subject, scored on
keyword overlap. An image is used at most twice across the run, so a month of
posts does not show the same picture ten times. Anything unmatched is listed
for generation with gen_image.py rather than silently left blank -- a missing
image is an Instagram post that will not send.

Images are referenced by their live URL. Buffer fetches them, so they must be
publicly reachable: verified 200 image/jpeg, and .htaccess line 54 explicitly
allows jpg.

    python tools/attach_faq_images.py            # dry run
    python tools/attach_faq_images.py --apply
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "faq-calendar.json"
SITE = "https://parlevugloballlc.com"
MAX_REUSE = 2

# Subject keywords per FAQ, used to score candidate images. Written per
# question rather than per category so, for example, the divorce question does
# not land on a generic cash-offer photo.
TOPICS = {
    1: ["sell-my-house-fast", "cash-offer", "fast"],
    2: ["we-buy-houses", "cash-buyers", "baltimore", "dmv"],
    3: ["as-is", "no-repairs", "repairs", "damaged"],
    4: ["closing", "7-day", "timeline", "close"],
    5: ["commission", "fees", "realtor", "agent"],
    6: ["cash-offer", "calculate", "offer", "price"],
    7: ["fsbo", "for-sale-by-owner"],
    8: ["fsbo", "without-agent", "without-realtor", "maryland"],
    9: ["fsbo-vs", "vs-agent", "compare", "fsbo"],
    10: ["price", "pricing", "appraisal", "comps", "value"],
    11: ["mls", "listing", "without-mls"],
    12: ["fsbo", "consultation", "cash-offer"],
    13: ["code-violation", "repairs", "damaged", "condition"],
    14: ["inherited", "probate", "estate"],
    15: ["foreclosure", "behind", "mortgage", "pre-foreclosure"],
    16: ["divorce"],
    17: ["tenant", "vacant", "squatter", "rental"],
    18: ["out-of-state", "relocation", "virtual", "remote"],
    19: ["cash-offer", "free", "no-obligation"],
    20: ["cash-offer", "documents", "paperwork", "information"],
    21: ["process", "walkthrough", "steps", "what-happens"],
    22: ["clean-out", "clutter", "belongings", "hoarder"],
    23: ["lien", "title", "violations"],
    24: ["disclosure", "lead-paint", "defects"],
    25: ["invest", "investment", "investor"],
    26: ["off-market", "wholesale", "invest"],
    27: ["flip", "renovation", "rehab", "arv"],
    28: ["rental", "landlord", "buy-and-hold", "income"],
    29: ["wholesale", "joint-venture", "invest"],
    30: ["contact", "consultation", "schedule", "call"],
}


def score(slug, keys):
    s = 0
    for k in keys:
        if k in slug:
            s += len(k)          # longer, more specific matches win
    return s


def main():
    apply = "--apply" in sys.argv
    cal = json.loads(CAL.read_text(encoding="utf-8"))

    images = sorted(os.path.basename(p)[:-4]
                    for p in glob.glob(str(REPO / "images" / "blog" / "*.jpg")))
    used = Counter()
    assigned, unmatched = {}, []

    for e in cal["entries"]:
        n = e["faq_number"]
        keys = TOPICS.get(n, [])
        ranked = sorted(
            ((score(img, keys), img) for img in images),
            key=lambda t: (-t[0], used[t[1]], t[1]))
        pick = None
        for sc, img in ranked:
            if sc <= 0:
                break
            if used[img] < MAX_REUSE:
                pick = img
                break
        if pick:
            used[pick] += 1
            assigned[n] = pick
        else:
            unmatched.append(n)

    print("matched   : %d / %d" % (len(assigned), len(cal["entries"])))
    print("unmatched : %s" % (unmatched or "none"))
    print("distinct images used: %d  (max reuse %d)" % (len(used), MAX_REUSE))
    over = [i for i, c in used.items() if c > MAX_REUSE]
    print("over reuse cap: %s" % (over or "none"))
    print()
    for e in cal["entries"][:8]:
        n = e["faq_number"]
        print("  FAQ %02d  %-46s %s" % (n, e["question"][:46],
                                        assigned.get(n, "-- NONE --")))

    if not apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return

    for e in cal["entries"]:
        img = assigned.get(e["faq_number"])
        url = (SITE + "/images/blog/" + img + ".jpg") if img else None
        for ch, body in e["channels"].items():
            body["image"] = url
        e["image_slug"] = img

    cal["media_policy"] = (
        "Every caption carries a topic-matched image. Instagram REQUIRES media "
        "-- a text-only Instagram post is rejected by the platform, so an entry "
        "without an image cannot publish there. Images are referenced by live "
        "URL because Buffer fetches them; they must stay publicly reachable. "
        "No image is used more than %d times across the 30 days." % MAX_REUSE)
    CAL.write_text(json.dumps(cal, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("\nAPPLIED to %s" % CAL.name)


if __name__ == "__main__":
    main()
