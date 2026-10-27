#!/usr/bin/env python3
"""Queue social-calendar.json entries into Buffer. Google Business Profile first.

WHY THIS REPLACES post_to_buffer.py
-----------------------------------
post_to_buffer.py calls Buffer's legacy v1 REST API at api.bufferapp.com.
That endpoint returns 401 for current tokens and Buffer retires it on
2026-02-01. The live API is GraphQL at https://api.buffer.com. This tool
speaks that one.

WHY BUFFER FOR GBP RATHER THAN GOOGLE'S OWN API
-----------------------------------------------
The Google Business Profile API is allowlisted: quota is 0 QPM until Google
approves access, which is why tools/sync_gmb_posts.py has only ever rendered
drafts. Buffer is already an approved GBP partner, so posting through Buffer
needs no allowlist and no OAuth of our own. Connect the Google Business
Profile channel in Buffer once and GBP becomes automatable today.

SAFETY
------
Dry run is the default. Nothing reaches a social account without --publish.
Posts already queued are recorded in buffer_posted.json and skipped, so a
re-run cannot double-post.

Acceptance is not delivery. createPost returning an id means Buffer took the
post, not that the network published it; check Buffer afterwards for anything
that matters.

USAGE
  python tools/buffer_poster.py --channels
  python tools/buffer_poster.py --date 2026-10-28                  # dry run
  python tools/buffer_poster.py --date 2026-10-28 --services gbp
  python tools/buffer_poster.py --slug sell-my-house-fast-baltimore
  python tools/buffer_poster.py --date 2026-10-28 --publish        # sends
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "social-calendar.json")
STATE = os.path.join(REPO, "buffer_posted.json")
ENV = os.path.join(REPO, ".env")
API = "https://api.buffer.com"

# social-calendar.json channel key -> Buffer service identifier.
SERVICE = {"facebook": "facebook", "instagram": "instagram", "gbp": "googlebusiness"}


def load_token():
    if not os.path.exists(ENV):
        sys.exit("no .env at %s" % ENV)
    text = io.open(ENV, encoding="utf-8-sig").read()
    env = dict(re.findall(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)$", text, re.M))
    tok = (env.get("BUFFER_ACCESS_TOKEN") or "").strip().strip('"').strip("'")
    if not tok:
        sys.exit("BUFFER_ACCESS_TOKEN not set. Run: python tools/set_buffer_token.py")
    return tok


def gql(token, query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "parlevu-buffer-poster"})
    try:
        raw = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        sys.exit("Buffer HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:200]))
    d = json.loads(raw)
    if d.get("errors"):
        sys.exit("Buffer API error: %s"
                 % "; ".join(x.get("message", "?") for x in d["errors"]))
    return d.get("data") or {}


def channels(token):
    d = gql(token, "query { account { organizations { id name } } }")
    orgs = ((d.get("account")) or {}).get("organizations") or []
    out = []
    for org in orgs:
        c = gql(token,
                "query($id: OrganizationId!) { channels(input: { organizationId: $id }) "
                "{ id name service } }", {"id": org["id"]})
        for ch in (c.get("channels") or []):
            out.append({"org": org.get("name"), **ch})
    return out


def create_post(token, channel_id, service, text, due_at, link=None):
    """Queue one post. Google Business Profile has its own vocabulary.

    The metadata key for GBP is `google`, NOT `googlebusiness`; the type enum
    is event|offer|whats_new; and a whats_new post carries its own link and
    button. Instagram and Facebook both reject a post with no declared type.
    """
    if service == "instagram":
        metadata = {"instagram": {"type": "post", "shouldShareToFeed": True}}
    elif service == "facebook":
        metadata = {"facebook": {"type": "post"}}
    elif service == "googlebusiness":
        metadata = {"google": {"type": "whats_new",
                               "detailsWhatsNew": {"button": "learn_more",
                                                   "link": link or None}}}
    else:
        metadata = None

    inp = {"text": text, "channelId": channel_id, "schedulingType": "automatic",
           "mode": "customScheduled" if due_at else "addToQueue"}
    if due_at:
        inp["dueAt"] = due_at
    if metadata:
        inp["metadata"] = metadata

    d = gql(token, """mutation($input: CreatePostInput!) {
        createPost(input: $input) {
          ... on PostActionSuccess { post { id dueAt } }
          ... on MutationError { message }
        } }""", {"input": inp})
    res = d.get("createPost") or {}
    # The union, not the HTTP status, says whether this worked.
    post = res.get("post")
    if post and post.get("id"):
        return post
    raise RuntimeError("Buffer rejected the post: %s"
                       % (res.get("message") or json.dumps(res)[:160]))


def load_state():
    if os.path.exists(STATE):
        try:
            return json.loads(io.open(STATE, encoding="utf-8").read())
        except Exception:
            pass
    return {}


def save_state(state):
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(state, indent=1, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", action="store_true",
                    help="list connected Buffer channels and exit")
    ap.add_argument("--date", help="queue entries whose blog_publish_date is this day")
    ap.add_argument("--slug", help="queue entries for this blog slug")
    ap.add_argument("--services", default="gbp,facebook,instagram",
                    help="comma list of social-calendar channels (default all three)")
    ap.add_argument("--role", default="primary", choices=["primary", "alternate", "any"],
                    help="which calendar entries to use (default primary)")
    ap.add_argument("--publish", action="store_true",
                    help="actually send. Without this nothing leaves the machine.")
    args = ap.parse_args()

    token = load_token()
    live = channels(token)

    if args.channels:
        print("Connected Buffer channels (%d):" % len(live))
        for ch in live:
            print("   %-16s %-32s %s" % (ch["service"], ch["name"][:32], ch["id"]))
        if not any(c["service"] == "googlebusiness" for c in live):
            print("\n  No Google Business Profile channel is connected.")
            print("  Connect it in Buffer (Channels -> Add -> Google Business Profile),")
            print("  then re-run. GBP needs no Google API allowlist via Buffer.")
        return

    if not (args.date or args.slug):
        sys.exit("give --date YYYY-MM-DD or --slug, or --channels to list")

    cal = json.loads(io.open(CAL, encoding="utf-8").read())
    wanted = [s.strip() for s in args.services.split(",") if s.strip()]
    for w in wanted:
        if w not in SERVICE:
            sys.exit("unknown service %r. Known: %s" % (w, ", ".join(SERVICE)))

    entries = [e for e in cal["posts"]
               if (args.date is None or e["blog_publish_date"] == args.date)
               and (args.slug is None or e["blog_slug"] == args.slug)
               and (args.role == "any" or e["role"] == args.role)]
    if not entries:
        sys.exit("no calendar entries matched")

    by_service = {}
    for ch in live:
        by_service.setdefault(ch["service"], []).append(ch)

    state = load_state()
    mode = "PUBLISH" if args.publish else "DRY RUN"
    print("%s - %d entry(s), services: %s\n" % (mode, len(entries), ",".join(wanted)))

    queued = skipped = failed = 0
    for e in entries:
        for key in wanted:
            service = SERVICE[key]
            found = by_service.get(service) or []
            if not found:
                print("  SKIP  %-34s %-12s no %s channel connected in Buffer"
                      % (e["blog_slug"][:34], key, service))
                skipped += 1
                continue
            if len(found) > 1:
                print("  SKIP  %-34s %-12s %d channels match %s - ambiguous, refusing"
                      % (e["blog_slug"][:34], key, len(found), service))
                skipped += 1
                continue
            ch = found[0]

            state_key = "%s|%s" % (e["blog_slug"], ch["id"])
            if state_key in state:
                print("  SKIP  %-34s %-12s already queued %s"
                      % (e["blog_slug"][:34], key, state[state_key].get("at", "")[:10]))
                skipped += 1
                continue

            body = e["channels"][key]
            text, link = body["copy"], body.get("link")
            due = e["scheduled_for"] + ":00Z" if len(e["scheduled_for"]) == 16 else None

            if not args.publish:
                print("  QUEUE %-34s %-12s %4d chars -> %s"
                      % (e["blog_slug"][:34], key, body["chars"], ch["name"][:24]))
                if link:
                    print("        link: %s" % link[:96])
                queued += 1
                continue

            try:
                post = create_post(token, ch["id"], service, text, due, link)
                state[state_key] = {"at": datetime.utcnow().isoformat() + "Z",
                                    "bufferPostId": post["id"],
                                    "dueAt": post.get("dueAt"),
                                    "service": service, "link": link}
                save_state(state)
                print("  SENT  %-34s %-12s buffer id=%s"
                      % (e["blog_slug"][:34], key, post["id"]))
                queued += 1
            except Exception as exc:
                print("  FAIL  %-34s %-12s %s" % (e["blog_slug"][:34], key, exc))
                failed += 1

    print("\n%s: %d queued, %d skipped, %d failed" % (mode, queued, skipped, failed))
    if not args.publish:
        print("Nothing was sent. Re-run with --publish to queue these in Buffer.")
    elif queued:
        print("Queued in Buffer. Acceptance is not delivery -- check Buffer for"
              " anything that matters.")


if __name__ == "__main__":
    main()
