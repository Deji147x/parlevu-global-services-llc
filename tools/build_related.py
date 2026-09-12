"""Rewire the "Related Articles" block on every post into topic clusters.

Posts ship with a related block, but its links pooled on a handful of pages
while the long tail got nothing, and newly published posts are never picked up
because the block is written once at publish time and never revisited.

This recomputes the block for every post from the current set of published
files, so it is safe - and worth - re-running after each publish.

Relatedness is scored on the slug, because the slugs encode the taxonomy:
  <situation>-<state>      divorce-md, foreclosure-va, water-mold-dc
  sell-my-house-fast-<city>
  fsbo-<topic>

Usage:
  python tools/build_related.py              # dry run, prints what would change
  python tools/build_related.py --apply
  python tools/build_related.py --apply --count 6
"""
import argparse
import collections
import glob
import io
import os
import re
from html import escape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARD = (
    '<a href="{href}" style="display:block;background:var(--off-white);'
    'border-radius:var(--radius);padding:18px;text-decoration:none;'
    'border:1px solid var(--border)">'
    '<p style="font-size:.88rem;font-weight:600;color:var(--navy);margin:0;'
    'line-height:1.4">{title}</p></a>'
)

GRID_OPEN = ('<div style="display:grid;grid-template-columns:'
             'repeat(auto-fit,minmax(220px,1fr));gap:16px">')

STATES = {"md": "maryland", "va": "virginia", "dc": "washington dc"}
STOP = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "your", "my",
        "is", "are", "how", "what", "why", "when", "complete", "guide", "blog"}


def tokens(slug):
    return {t for t in slug.split("-") if t and t not in STOP}


def state_of(slug):
    for s in STATES:
        if slug.endswith("-" + s) or ("-%s-" % s) in slug:
            return s
    return None


def family_of(slug):
    """The situation family, i.e. the slug with any trailing state removed."""
    s = state_of(slug)
    if s and slug.endswith("-" + s):
        return slug[: -(len(s) + 1)]
    return None


def score(a, b):
    """How related is post b to post a."""
    if a == b:
        return -1
    n = 0
    fa, fb = family_of(a), family_of(b)
    if fa and fa == fb:
        n += 6                      # same situation, different state
    sa, sb = state_of(a), state_of(b)
    if sa and sa == sb:
        n += 2                      # same state
    if a.startswith("sell-my-house-fast-") and b.startswith("sell-my-house-fast-"):
        n += 3                      # neighbouring city pages
    if a.startswith("fsbo-") and b.startswith("fsbo-"):
        n += 3
    n += len(tokens(a) & tokens(b))
    return n


# Posts related in meaning but sharing no slug vocabulary. Scoring cannot see
# these, so they are paired by hand, in both directions. A slug is fixed once a
# URL is indexed, which is why a post rewritten under an old URL needs this.
RELATED_OVERRIDES = {
    "market-update": [
        "how-we-calculate-your-cash-offer",
        "fsbo-mls-vs-cash-offer",
        "why-your-fsbo-listing-isnt-selling-baltimore",
        "how-to-sell-house-fast-maryland",
    ],
}


def pick_related(slug, slugs, count):
    """Best-scoring related posts, rotating within each tied score band.

    Without the rotation every city page picks the same alphabetically-first
    neighbours, which re-concentrates inbound links on a handful of posts -
    the exact problem this script exists to fix. Rotating by a stable hash of
    the source slug spreads them while keeping the output deterministic.
    """
    bands = {}
    for other in slugs:
        s = score(slug, other)
        if s > 0:
            bands.setdefault(s, []).append(other)

    picks = []
    seed = sum(ord(c) for c in slug)
    for s in sorted(bands, reverse=True):
        band = sorted(bands[s])
        if len(band) > 1:
            off = seed % len(band)
            band = band[off:] + band[:off]
        for p in band:
            picks.append(p)
            if len(picks) == count:
                return picks
    return picks


def balance(plan, slugs):
    """Ensure no post is left without a single related-block link.

    Scoring alone leaves a tail of posts nothing points at - they are still
    reachable from the blog index, but they receive no topical link equity.
    For each such post, take the page most related to it and swap that page's
    weakest pick for this one, so the fix costs the least-relevant link.
    """
    inbound = collections.Counter()
    for src, picks in plan.items():
        for p in picks:
            inbound[p] += 1

    stranded = [s for s in slugs if inbound[s] == 0]
    for z in stranded:
        # the page most related to z, preferring one whose weakest pick is
        # weaker than the link we are about to add
        best = None
        for src in slugs:
            if src == z or not plan.get(src):
                continue
            gain = score(src, z)
            if gain <= 0:
                continue
            # drop the least-relevant pick, but never one that would strand
            # another post in the process
            droppable = [p for p in plan[src] if inbound[p] > 1]
            if not droppable:
                continue
            weakest = min(droppable, key=lambda p: score(src, p))
            if best is None or gain > best[0]:
                best = (gain, src, weakest)
        if best:
            _, src, weakest = best
            plan[src] = [z if p == weakest else p for p in plan[src]]
            inbound[weakest] -= 1
            inbound[z] += 1
    return plan


def apply_overrides(plan, slugs, count):
    """Pin hand-curated pairings, linking both ways.

    The source gets its curated list outright. Each target gets the source
    swapped in for its least-relevant pick - never a pick that is some other
    post's only related-block link, so the fix cannot strand anything.
    """
    live = set(slugs)
    inbound = collections.Counter(p for picks in plan.values() for p in picks)
    for src, targets in RELATED_OVERRIDES.items():
        if src not in live:
            continue
        targets = [t for t in targets if t in live and t != src]
        for old in plan.get(src, []):
            inbound[old] -= 1
        plan[src] = targets[:count]
        for t in plan[src]:
            inbound[t] += 1
        for t in targets:
            picks = plan.get(t) or []
            if src in picks:
                continue
            if len(picks) < count:
                picks.append(src)
            else:
                droppable = [p for p in picks if inbound[p] > 1]
                if not droppable:
                    continue
                weakest = min(droppable, key=lambda p: score(t, p))
                picks[picks.index(weakest)] = src
                inbound[weakest] -= 1
            inbound[src] += 1
            plan[t] = picks
    return plan


def title_of(path):
    h = io.open(path, encoding="utf-8").read()
    m = re.search(r'<h2 class="article-title">(.*?)</h2>', h, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    return re.sub(r"\s*\|.*$", "", m.group(1)).strip() if m else path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--count", type=int, default=4, help="related links per post")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(REPO, "blog-*.html")))
    slugs = [os.path.basename(f)[len("blog-"):-len(".html")] for f in files]
    titles = {s: title_of(os.path.join(REPO, "blog-%s.html" % s)) for s in slugs}

    plan = {s: pick_related(s, slugs, args.count) for s in slugs}
    plan = balance(plan, slugs)
    plan = apply_overrides(plan, slugs, args.count)

    changed = skipped = noblock = 0
    for slug in slugs:
        path = os.path.join(REPO, "blog-%s.html" % slug)
        h = io.open(path, encoding="utf-8").read()

        i = h.find("Related Articles")
        if i == -1:
            noblock += 1
            continue
        g = h.find(GRID_OPEN, i)
        if g == -1:
            noblock += 1
            continue
        end = h.find("</div>", g + len(GRID_OPEN))
        # walk to the grid's own closing tag (cards contain no nested divs)
        if end == -1:
            noblock += 1
            continue

        picks = plan.get(slug, [])
        if not picks:
            skipped += 1
            continue

        cards = "".join(
            CARD.format(href="blog-%s.html" % p, title=escape(titles[p]))
            for p in picks
        )
        new = h[: g + len(GRID_OPEN)] + cards + h[end:]
        if new == h:
            skipped += 1
            continue
        if args.apply:
            io.open(path, "w", encoding="utf-8", newline="\n").write(new)
        changed += 1

    print("%s: %d posts rewired, %d unchanged, %d without a related block"
          % ("APPLIED" if args.apply else "DRY RUN", changed, skipped, noblock))


if __name__ == "__main__":
    main()
