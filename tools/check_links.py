#!/usr/bin/env python3
"""Check every link on the site and report the dead ones.

WHY THIS EXISTS
Two classes of broken link reached production before anyone noticed:

  31 YouTube iframes with invented video IDs (zestimate, remax-fsbo, ...),
  which rendered as unavailable-video players on live lead-gen pages.

  1468 LinkedIn links pointing at a vanity URL that returned 404 after the
  profile was renamed -- one dead social link in essentially every footer.

Both had the same shape: content generated once, the world moved, nothing
re-checked it. The Buffer poster now verifies its targets before posting; the
site had no equivalent. This is it.

WHAT IT CHECKS
Internal links resolve against files on disk, which is fast and needs no
network. External links get one HEAD request each, falling back to GET
because some hosts reject HEAD.

Hosts that block automated requests are reported separately rather than as
failures. LinkedIn answers 999 to anything that looks like a bot, and X/Twitter
and Instagram behave similarly: calling those "broken" would bury the real
findings under noise, which is how link reports get ignored.

  python tools/check_links.py                 # internal only, no network
  python tools/check_links.py --external      # also check outbound links
  python tools/check_links.py --external --json report.json
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
SITE = "parlevugloballlc.com"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

# These answer non-2xx to automated clients whatever the page's real state.
# Reported as unverifiable, never as broken.
BOT_WALLED = ("linkedin.com", "x.com", "twitter.com", "instagram.com",
              "facebook.com", "pinterest.com", "youtube.com", "youtu.be",
              # Government sites behind WAFs that reject non-browser clients.
              # Verified by hand: sdat answers 403 to any automated request,
              # msc.fema.gov serves 200 on its real path. Neither is broken
              # for a visitor.
              "sdat.dat.maryland.gov", "msc.fema.gov")

HREF = re.compile(r'(?:href|src)="([^"#][^"]*)"', re.I)

# <link rel="preconnect"> and dns-prefetch name an ORIGIN to warm up, not a
# page to fetch. Requesting the bare origin 404s while the hint works
# perfectly, so counting those as broken buries the real findings.
PRECONNECT = re.compile(r'rel="(?:preconnect|dns-prefetch)"[^>]*href="([^"]+)"'
                        r'|href="([^"]+)"[^>]*rel="(?:preconnect|dns-prefetch)"', re.I)
YT_EMBED = re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]+)")


def pages():
    return sorted(p for p in glob.glob("*.html"))


def classify(url):
    if url.startswith("//"):
        return "external", "https:" + url
    if url.startswith(("http://", "https://")):
        return ("internal-abs", url) if SITE in url else ("external", url)
    if url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return "skip", url
    return "internal", url


def internal_path(url):
    """Strip query/fragment and the site prefix, return a repo-relative path."""
    u = url.split("#")[0].split("?")[0]
    u = re.sub(r"^https?://(?:www\.)?" + re.escape(SITE), "", u)
    return u.lstrip("/")


def head_or_get(url, timeout=20):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=timeout).status
    except urllib.error.HTTPError as e:
        # 404 is included deliberately: some hosts answer 404 to HEAD for a
        # page that serves fine on GET (maps.google.com does exactly this).
        # GET is what a visitor actually sends, so it is the honest test.
        if e.code in (403, 404, 405, 501):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                return urllib.request.urlopen(req, timeout=timeout).status
            except urllib.error.HTTPError as e2:
                return e2.code
            except Exception:
                return 0
        return e.code
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true",
                    help="also check outbound links (one request each)")
    ap.add_argument("--json", help="write the full report to this file")
    ap.add_argument("--delay", type=float, default=0.2,
                    help="seconds between external requests (default 0.2)")
    args = ap.parse_args()

    internal_bad = collections.defaultdict(list)   # target -> [pages]
    external = collections.defaultdict(list)       # url -> [pages]
    yt = collections.defaultdict(list)             # video id -> [pages]
    n_links = 0

    for page in pages():
        s = io.open(page, encoding="utf-8", errors="replace").read()
        hinted = {u for pair in PRECONNECT.findall(s) for u in pair if u}
        for vid in YT_EMBED.findall(s):
            yt[vid].append(page)
        for raw in HREF.findall(s):
            if raw in hinted:
                continue
            kind, url = classify(raw)
            if kind == "skip":
                continue
            n_links += 1
            if kind == "external":
                external[url].append(page)
            else:
                target = internal_path(url)
                if target and not os.path.exists(target):
                    internal_bad[target].append(page)

    print("pages scanned : %d" % len(pages()))
    print("links found   : %d" % n_links)
    print()

    print("=== INTERNAL: targets that do not exist on disk ===")
    if internal_bad:
        for t, where in sorted(internal_bad.items(),
                               key=lambda kv: -len(kv[1]))[:40]:
            print("  %-54s referenced by %d page(s)" % (t[:54], len(where)))
            print("        e.g. %s" % ", ".join(where[:3]))
    else:
        print("  none")
    print()

    print("=== YOUTUBE embeds (a real id is 11 characters) ===")
    if yt:
        for vid, where in sorted(yt.items()):
            flag = "" if len(vid) == 11 else "   <-- NOT A VALID ID"
            print("  %-16s %2d page(s)%s" % (vid, len(where), flag))
    else:
        print("  none")
    print()

    print("=== EXTERNAL: %d distinct URLs ===" % len(external))
    results = {}
    if not args.external:
        print("  not checked (pass --external)")
    else:
        broken, walled, ok = [], [], 0
        for i, (url, where) in enumerate(sorted(external.items()), 1):
            code = head_or_get(url)
            results[url] = code
            host = re.sub(r"^https?://(?:www\.)?", "", url).split("/")[0]
            if any(b in host for b in BOT_WALLED):
                if code and 200 <= code < 400:
                    ok += 1
                else:
                    walled.append((url, code, len(where)))
            elif code and 200 <= code < 400:
                ok += 1
            else:
                broken.append((url, code, len(where)))
            time.sleep(args.delay)

        print("  reachable            : %d" % ok)
        print("  BROKEN               : %d" % len(broken))
        for url, code, n in broken:
            print("     %-4s %-62s on %d page(s)" % (code or "ERR", url[:62], n))
        print("  unverifiable (bot-walled, not necessarily broken): %d" % len(walled))
        for url, code, n in walled[:10]:
            print("     %-4s %-62s on %d page(s)" % (code or "ERR", url[:62], n))

    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"pages": len(pages()), "links": n_links,
                        "internal_missing": {k: v for k, v in internal_bad.items()},
                        "youtube": {k: v for k, v in yt.items()},
                        "external_status": results}, indent=1) + "\n")
        print("\nreport written: %s" % args.json)

    # Non-zero exit on genuinely broken things, so this can gate a deploy.
    bad = len(internal_bad) + sum(1 for v in yt if len(v) != 11)
    if args.external:
        bad += len([1 for u, c in results.items()
                    if not (c and 200 <= c < 400)
                    and not any(b in u for b in BOT_WALLED)])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
