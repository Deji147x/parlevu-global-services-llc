#!/usr/bin/env python3
"""Add the missing image, and the owner's posting slot, to scheduled GBP posts.

WHY
---
The ten Google Business Profile posts were queued before images were attached
to the calendar and before the owner supplied their posting times, so they
carry neither. Verified against Buffer: googlebusiness 0/10 with an image,
facebook 10/10, instagram 10/10.

That matters on the channel it matters most on. GBP is the highest local
intent surface here, an image is the stated minimum standard, and the posts
are also still on the old flat 10:00 slot rather than the 08:29 / 09:45 /
18:44 rotation.

HOW
---
Buffer exposes editPost, which accepts assets and dueAt, so each post is
amended in place. Nothing is deleted and no post is recreated, which means
no risk of losing a slot or double-posting if a call fails partway.

Only posts still in "scheduled" state are touched. A post that has already
sent is left alone and reported, because amending a published post is not
what anyone means by fixing the queue.

    python tools/fix_gbp_media.py            # dry run
    python tools/fix_gbp_media.py --apply
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from buffer_poster import load_token, gql, to_utc  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "buffer_posted.json")
FAQ_CAL = os.path.join(REPO, "faq-calendar.json")


def main():
    apply = "--apply" in sys.argv
    token = load_token()
    state = json.loads(io.open(STATE, encoding="utf-8").read())
    cal = json.loads(io.open(FAQ_CAL, encoding="utf-8").read())

    # faq-NN -> (image url, scheduled_for) from the current calendar
    want, links = {}, {}
    for e in cal["entries"]:
        k = "faq-%02d" % e["faq_number"]
        want[k] = (e["channels"]["gbp"]["image"], e["scheduled_for"])
        links[k] = e["channels"]["gbp"]["link"]

    todo, skipped = [], []
    for key, v in state.items():
        if v.get("service") != "googlebusiness":
            continue
        slug = key.split("|")[0]
        pid = v["bufferPostId"]
        d = gql(token,
                "query($id: PostId!) { post(input:{id:$id}) "
                "{ id status dueAt assets { ... on ImageAsset { source } } } }",
                {"id": pid})
        p = d.get("post") or {}
        if p.get("status") != "scheduled":
            skipped.append((slug, p.get("status"), "already sent"))
            continue
        has_img = len(p.get("assets") or []) > 0
        img, sched = want.get(slug, (None, None))
        if not img:
            # Blog-caption posts (not FAQs) have no entry in faq-calendar.
            skipped.append((slug, p.get("status"), "not a FAQ post"))
            continue
        new_due = to_utc(sched) if sched else None
        todo.append((slug, pid, img, new_due, p.get("dueAt"), has_img))

    print("GBP posts scheduled : %d" % (len(todo) + len(skipped)))
    print("to amend            : %d" % len(todo))
    for slug, status, why in skipped:
        print("   skip %-24s %-10s %s" % (slug, status, why))
    print()
    for slug, pid, img, new_due, old_due, has_img in todo:
        print("   %-10s img=%s -> %s   dueAt %s -> %s"
              % (slug, "yes" if has_img else "NO", img.split("/")[-1][:30],
                 (old_due or "")[:16], (new_due or "")[:16]))

    if not apply:
        print("\nDRY RUN - nothing changed. Re-run with --apply.")
        return

    ok = fail = 0
    for slug, pid, img, new_due, old_due, has_img in todo:
        # editPost REPLACES the input rather than merging it. Omitting
        # metadata stripped the Google Business type and every edit was
        # rejected with "posts require a type (event, offer, or whats_new)",
        # so the type and its Learn more button must be re-sent each time.
        inp = {"id": pid,
               "assets": [{"image": {"url": img}}],
               "metadata": {"google": {
                   "type": "whats_new",
                   "detailsWhatsNew": {"button": "learn_more",
                                       "link": links.get(slug)}}}}
        if new_due:
            inp["dueAt"] = new_due
        try:
            d = gql(token, """mutation($input: EditPostInput!) {
                editPost(input: $input) {
                  ... on PostActionSuccess { post { id dueAt } }
                  ... on MutationError { message }
                } }""", {"input": inp})
            res = d.get("editPost") or {}
            if res.get("post", {}).get("id"):
                print("   OK   %-10s %s" % (slug, res["post"].get("dueAt", "")[:16]))
                ok += 1
            else:
                print("   FAIL %-10s %s" % (slug, res.get("message") or res))
                fail += 1
        except SystemExit as e:
            print("   FAIL %-10s %s" % (slug, e))
            fail += 1

    print("\namended: %d, failed: %d" % (ok, fail))


if __name__ == "__main__":
    main()
