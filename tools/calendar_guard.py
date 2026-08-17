"""Shared safety helpers for every content-calendar.json builder.

WHY THIS EXISTS
---------------
Each builder used to rewrite the calendar wholesale, carrying over only
entries with status == "published". That had three destructive effects:

  1. Queued posts from *other* builders were silently deleted (build_calendar.py
     knows 120 template briefs; the calendar held 322 entries).
  2. Deliberately removed briefs came back from the dead, because "removed"
     was not a status anyone preserved.
  3. Posts marked "generated" — which are LIVE on the site — were reset to
     "queued" and would republish, overwriting live pages with fresh AI text
     and inserting duplicate cards into blog.html.

Builders must call merge_briefs() instead of assigning cal["posts"] directly.

Usage:
    from calendar_guard import merge_briefs, in_service_area, safe_slug
    cal["posts"] = merge_briefs(cal["posts"], new_briefs)
"""
import re

# Statuses that must never be overwritten or re-queued by a builder.
#   published / generated -> the post is live; re-queuing republishes over it
#   removed               -> a deliberate human decision; never resurrect
PROTECTED_STATUSES = {"published", "generated", "removed"}

# Places outside the MD/VA/DC service area. Briefs naming any of these are
# rejected: ranking for them attracts traffic that cannot convert.
OUT_OF_AREA_TERMS = {
    "methow", "duncan", "big canoe", "canadarago", "dominican", "punta cana",
    "cannon beach", "canyon lake", "canton il", "volcan", "panama",
    "florida", "texas", "oregon", "illinois", "tennessee", "ohio", "michigan",
    "arizona", "colorado", "georgia", "carolina", "alabama", "missouri",
    "kentucky", "indiana", "wisconsin", "minnesota", "iowa", "kansas",
    "nevada", "utah", "idaho", "montana", "wyoming", "dakota", "nebraska",
    "oklahoma", "arkansas", "louisiana", "mississippi", "maine", "vermont",
    "new hampshire", "rhode island", "connecticut", "new jersey",
    "pennsylvania", "massachusetts", "new york", "california", "alaska",
    "hawaii",
}


def _service_terms():
    """In-market place names, sourced from build_calendar.py so the allowlist
    never drifts from the templates that generate real posts."""
    try:
        from build_calendar import STATES, CITIES
    except ImportError:
        return set()
    terms = set()
    for code, meta in STATES.items():
        terms.add(code.lower())
        terms.add(meta["name"].lower())
    for cities in CITIES.values():
        terms.update(c.lower() for c in cities)
    return terms


def in_service_area(text: str) -> bool:
    """True if a brief is safe to publish for a MD/VA/DC audience.

    Geo-neutral briefs ("Is FSBO a good idea?") pass — they are legitimate
    national-intent queries a Maryland page can answer. Only briefs naming an
    explicitly out-of-area place are rejected.
    """
    t = (text or "").lower()
    if any(term in t for term in OUT_OF_AREA_TERMS):
        # An in-area mention wins over an ambiguous match (e.g. "Columbia" is
        # a Maryland city as well as a place elsewhere).
        return any(term in t for term in _service_terms())
    return True


def safe_slug(text: str, maxlen: int = 60) -> str:
    """Slugify, truncating on a hyphen boundary rather than mid-word.

    The old behaviour (`text[:50]`, then `base[:30]`) produced slugs like
    'methow-valley-real-estate-for-' and 'how-to-list-real-estate-for-sa'.
    """
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    if len(s) <= maxlen:
        return s
    cut = s[:maxlen]
    if "-" in cut:
        cut = cut[:cut.rindex("-")]
    return cut.strip("-") or s[:maxlen].strip("-")


def merge_briefs(existing, new_briefs, verbose=True):
    """Merge freshly-built briefs into the existing calendar, non-destructively.

    Rules, in order:
      - slug not present            -> append it
      - status in PROTECTED_STATUSES -> leave completely untouched
      - status queued               -> refresh metadata, but keep publish_date
                                       so the schedule does not shuffle

    Entries in `existing` whose slug no builder produced are always carried
    through; this is what stops one builder from deleting another's posts.
    """
    merged = list(existing)
    by_slug = {p.get("slug"): p for p in merged}

    added = updated = protected = 0
    for b in new_briefs:
        slug = b.get("slug")
        current = by_slug.get(slug)

        if current is None:
            merged.append(b)
            by_slug[slug] = b
            added += 1
            continue

        if current.get("status") in PROTECTED_STATUSES:
            protected += 1
            continue

        keep_date = current.get("publish_date")
        current.update(b)
        if keep_date:
            current["publish_date"] = keep_date
        updated += 1

    if verbose:
        print(f"  merge: +{added} new, {updated} refreshed, "
              f"{protected} protected, {len(merged)} total "
              f"(was {len(existing)})")
    return merged


def removed_slugs(posts):
    """Slugs a human deliberately removed — never regenerate these."""
    return {p.get("slug") for p in posts if p.get("status") == "removed"}


def status_counts(posts):
    """Status histogram, for before/after regression assertions."""
    counts = {}
    for p in posts:
        counts[p.get("status")] = counts.get(p.get("status"), 0) + 1
    return counts
