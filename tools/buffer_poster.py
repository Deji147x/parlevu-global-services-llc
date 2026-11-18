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
import time
import urllib.error
import urllib.request
from datetime import date, datetime, time as dtime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "social-calendar.json")
FAQ_CAL = os.path.join(REPO, "faq-calendar.json")
STATE = os.path.join(REPO, "buffer_posted.json")
_HEAD_CACHE = {}
# Buffer rate-limits bulk creation (HTTP 429 after roughly 60 calls in quick
# succession). Pace every mutation rather than burst and retry.
RATE_SLEEP = 1.2
ENV = os.path.join(REPO, ".env")
API = "https://api.buffer.com"

# social-calendar.json channel key -> Buffer service identifier.
SERVICE = {"facebook": "facebook", "instagram": "instagram", "gbp": "googlebusiness"}

# Google Business Profile rejects posts containing a phone number; the CTA
# button carries it instead. Confirmed live on 2026-10-27.
PHONE_RX = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}")


def load_token():
    if not os.path.exists(ENV):
        sys.exit("no .env at %s" % ENV)
    text = io.open(ENV, encoding="utf-8-sig").read()
    env = dict(re.findall(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)$", text, re.M))
    tok = (env.get("BUFFER_ACCESS_TOKEN") or "").strip().strip('"').strip("'")
    if not tok:
        sys.exit("BUFFER_ACCESS_TOKEN not set. Run: python tools/set_buffer_token.py")
    return tok


# Buffer's rate limit is a monthly call quota (3000 on the free plan), and it
# covers reads as well as writes: once spent, even a status query is refused.
# Only wait inline for a genuinely short Retry-After.
MAX_WAIT = 120
_QUOTA_WARNED = [False]


def _int_header(resp, name):
    try:
        v = resp.headers.get(name)
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _warn_if_quota_low(headers):
    """Say something while there is still quota left to act on."""
    try:
        remaining = headers.get("X-RateLimit-Remaining")
        limit = headers.get("X-RateLimit-Limit")
        if remaining is None:
            return
        remaining = int(remaining)
    except (TypeError, ValueError):
        return
    if remaining <= 200 and not _QUOTA_WARNED[0]:
        _QUOTA_WARNED[0] = True
        print("  !! Buffer quota low: %s of %s calls left. A full bulk run "
              "costs roughly one call per post; consider --limit."
              % (remaining, limit or "?"))


def gql(token, query, variables=None, _retry=0):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "parlevu-buffer-poster"})
    try:
        resp = urllib.request.urlopen(req, timeout=45)
        raw = resp.read().decode("utf-8", "replace")
        _warn_if_quota_low(resp.headers)
    except urllib.error.HTTPError as e:
        # Buffer's limit is a MONTHLY quota (3000 calls on the free plan), not
        # a short rolling window. An earlier version retried 429 with 60/120/
        # 180s backoff, which was useless: it burned six more minutes and more
        # quota against a limit that resets weeks away.
        #
        # Retry-After says exactly how long. Trust it: a short wait is worth
        # sitting out, a long one means stop and tell the operator when the
        # quota returns rather than pretending progress is possible.
        if e.code == 429:
            retry_after = _int_header(e, "Retry-After")
            reset_at = _int_header(e, "X-RateLimit-Reset")
            limit = e.headers.get("X-RateLimit-Limit") or "?"
            if retry_after is not None and retry_after <= MAX_WAIT and _retry < 2:
                print("  .. rate limited, Retry-After %ds (retry %d/2)"
                      % (retry_after, _retry + 1))
                time.sleep(retry_after + 1)
                return gql(token, query, variables, _retry + 1)
            when = ""
            if reset_at:
                when = time.strftime(" (resets %Y-%m-%d %H:%M UTC)",
                                     time.gmtime(reset_at))
            hrs = " in about %.1f hours" % (retry_after / 3600.0) if retry_after else ""
            sys.exit(
                "Buffer quota exhausted: limit %s calls%s.\n"
                "Not retrying -- the quota returns%s, so retrying now only\n"
                "spends more of it. Nothing was lost: buffer_posted.json\n"
                "records what already exists, so re-running later resumes\n"
                "exactly where this stopped." % (limit, when, hrs))
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


def create_post(token, channel_id, service, text, due_at, link=None, image=None,
                draft=False):
    """Queue one post. Google Business Profile has its own vocabulary.

    The metadata key for GBP is `google`, NOT `googlebusiness`; the type enum
    is event|offer|whats_new; and a whats_new post carries its own link and
    button. Instagram and Facebook both reject a post with no declared type.

    Instagram additionally rejects a post with no media at all, so an entry
    without an image cannot publish there. Buffer fetches the image by URL,
    which is why the calendar stores live URLs rather than local paths.
    """
    if service == "instagram" and not image:
        raise RuntimeError(
            "Instagram requires media and this entry has no image. "
            "Run tools/attach_faq_images.py --apply.")
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

    # A draft sits in Buffer's Drafts tab and is never sent by Buffer: the
    # operator publishes it by hand. That is the point of --draft, so a draft
    # deliberately carries no dueAt -- a send time on something nobody
    # scheduled is just a trap waiting to fire.
    if draft:
        # mode and schedulingType are required by the schema even for a
        # draft; omitting them is rejected outright. addToQueue keeps the
        # post off the calendar while saveToDraft is what actually parks it
        # in the Drafts tab.
        inp = {"text": text, "channelId": channel_id, "saveToDraft": True,
               "mode": "addToQueue", "schedulingType": "automatic"}
    else:
        inp = {"text": text, "channelId": channel_id,
               "schedulingType": "automatic",
               "mode": "customScheduled" if due_at else "addToQueue"}
    if image:
        inp["assets"] = [{"image": {"url": image}}]
    if due_at and not draft:
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


def to_utc(scheduled_for):
    """Convert a calendar 'YYYY-MM-DDTHH:MM' wall-clock time to a UTC instant.

    The calendar's times are Baltimore local. An earlier version simply
    appended "Z", which told Buffer the time was already UTC: a 10:00 slot
    would have fired at 06:00 local (05:00 once EST starts on 2026-11-01).
    That is BEFORE the 09:07 daily publish task, so the post would have gone
    out pointing at a page that did not exist yet.

    DST matters across this campaign specifically: the window runs 28 Oct to
    26 Nov and clocks change on 1 Nov, so a fixed offset would be wrong for
    most of it. ZoneInfo handles the transition.
    """
    if not scheduled_for or len(scheduled_for) != 16:
        return None
    naive = datetime.strptime(scheduled_for, "%Y-%m-%dT%H:%M")
    try:
        from zoneinfo import ZoneInfo
        local = naive.replace(tzinfo=ZoneInfo("America/New_York"))
        return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        # Bare Windows Python ships no tz database and `pip install tzdata`
        # is not always available. The US Eastern rule is simple and fixed in
        # law, so compute it rather than add a dependency or guess:
        # DST runs from the 2nd Sunday in March to the 1st Sunday in November,
        # both at 02:00 local.
        offset = 4 if _is_eastern_dst(naive) else 5
        return (naive + timedelta(hours=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _nth_sunday(year, month, n):
    """Date of the nth Sunday in a month."""
    d = date(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)   # first Sunday
    return d + timedelta(weeks=n - 1)


def _is_eastern_dst(naive):
    """US Eastern DST: 2nd Sunday in March 02:00 to 1st Sunday in Nov 02:00."""
    y = naive.year
    start = datetime.combine(_nth_sunday(y, 3, 2), dtime(2, 0))
    end = datetime.combine(_nth_sunday(y, 11, 1), dtime(2, 0))
    return start <= naive < end


def head_status(url):
    """HTTP status for a HEAD request, or 0 if unreachable. Cached per run."""
    if url in _HEAD_CACHE:
        return _HEAD_CACHE[url]
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, method="HEAD",
                                   headers={"User-Agent": "parlevu-link-check"}),
            timeout=20)
        code = r.status
    except urllib.error.HTTPError as exc:
        code = exc.code
    except Exception:
        code = 0
    _HEAD_CACHE[url] = code
    return code


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
    ap.add_argument("--calendar", default="social",
                    choices=["social", "faq"],
                    help="which calendar to post from (default social)")
    ap.add_argument("--from", dest="date_from",
                    help="schedule every entry on/after this date")
    ap.add_argument("--draft", action="store_true",
                    help="create Buffer DRAFTS instead of scheduled posts; "
                         "Buffer never sends a draft, you publish it yourself")
    ap.add_argument("--skip-link-check", action="store_true",
                    help="do not verify each target URL returns 200 first")
    ap.add_argument("--limit", type=int,
                    help="stop after N successful sends (Buffer's free plan caps "
                         "how many posts a channel may hold)")
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

    if not (args.date or args.slug or args.date_from):
        sys.exit("give --date, --from YYYY-MM-DD or --slug, or --channels to list")

    # The two calendars have different shapes. Normalise to the social one:
    # a list under "posts" with blog_slug / blog_publish_date / role.
    if args.calendar == "faq":
        raw = json.loads(io.open(FAQ_CAL, encoding="utf-8").read())
        cal = {"posts": [{
            "blog_slug": "faq-%02d" % e["faq_number"],
            "blog_publish_date": e["date"],
            "scheduled_for": e["scheduled_for"],
            "role": "primary",
            "channels": e["channels"],
        } for e in raw["entries"]]}
    else:
        cal = json.loads(io.open(CAL, encoding="utf-8").read())

    wanted = [s.strip() for s in args.services.split(",") if s.strip()]
    for w in wanted:
        if w not in SERVICE:
            sys.exit("unknown service %r. Known: %s" % (w, ", ".join(SERVICE)))

    entries = [e for e in cal["posts"]
               if (args.date is None or e["blog_publish_date"] == args.date)
               and (args.date_from is None or e["blog_publish_date"] >= args.date_from)
               and (args.slug is None or e["blog_slug"] == args.slug)
               and (args.role == "any" or e["role"] == args.role)]
    if not entries:
        sys.exit("no calendar entries matched")

    by_service = {}
    for ch in live:
        by_service.setdefault(ch["service"], []).append(ch)

    state = load_state()
    mode = ("DRAFT" if args.draft else "PUBLISH") if args.publish else "DRY RUN"
    print("%s - %d entry(s), services: %s\n" % (mode, len(entries), ",".join(wanted)))

    queued = skipped = failed = 0
    done = False
    for e in entries:
        if done:
            break
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
            due = to_utc(e["scheduled_for"])

            # Never promote a page that does not exist. On 2026-10-28 a GBP
            # post went live pointing at blog-fast-cash-offer-home.html, which
            # was still queued: the calendar assumed a post's publish_date
            # predicted WHICH post would publish that day, but publish_next.py
            # takes the first queued entry in calendar order, and that post was
            # fourth in line. The link 404'd on the channel with the highest
            # local intent.
            #
            # A link check costs one HEAD request per post and makes that
            # failure impossible for any calendar, not just the one that
            # caused it.
            if link and not args.skip_link_check:
                code = head_status(link)
                if code != 200:
                    print("  SKIP  %-34s %-12s target returns %s, refusing to"
                          " promote a dead link: %s"
                          % (e["blog_slug"][:34], key, code, link.split("?")[0]))
                    skipped += 1
                    continue

            # Google rejects any post containing a phone number ("Google
            # Business posts cannot contain phone numbers. Use the CTA button
            # instead."). Catch it here rather than spending a round trip and
            # a scheduled slot discovering it.
            if service == "googlebusiness" and PHONE_RX.search(text):
                print("  SKIP  %-34s %-12s contains a phone number; Google rejects"
                      " these. Rebuild with tools/build_social_calendar.py"
                      % (e["blog_slug"][:34], key))
                skipped += 1
                continue

            if not args.publish:
                print("  QUEUE %-34s %-12s %4d chars  img=%s -> %s"
                      % (e["blog_slug"][:34], key, body["chars"],
                         "yes" if body.get("image") else "NO", ch["name"][:20]))
                if link:
                    print("        link: %s" % link[:96])
                queued += 1
                continue

            try:
                post = create_post(token, ch["id"], service, text, due, link,
                                   body.get("image"), draft=args.draft)
                time.sleep(RATE_SLEEP)
                state[state_key] = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "bufferPostId": post["id"],
                                    "dueAt": post.get("dueAt"),
                                    "service": service, "link": link}
                save_state(state)
                print("  SENT  %-34s %-12s buffer id=%s"
                      % (e["blog_slug"][:34], key, post["id"]))
                queued += 1
                if args.limit and queued >= args.limit:
                    print("  -- stopping at --limit %d" % args.limit)
                    done = True
                    break
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
