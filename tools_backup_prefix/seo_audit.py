#!/usr/bin/env python3
"""On-page SEO audit across all HTML pages in the repo."""
import re
import json
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parent.parent

def audit_page(path):
    html = path.read_text(encoding='utf-8', errors='replace')
    issues = []

    # Title
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    title = m.group(1).strip() if m else None
    if not title:
        issues.append(("CRITICAL", "missing <title>"))
    elif len(title) > 65:
        issues.append(("MEDIUM", f"title too long ({len(title)} chars)"))

    # Meta description
    m = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    desc = m.group(1).strip() if m else None
    if not desc:
        issues.append(("CRITICAL", "missing meta description"))
    elif len(desc) > 165:
        issues.append(("MEDIUM", f"meta desc too long ({len(desc)} chars)"))
    elif len(desc) < 70:
        issues.append(("MEDIUM", f"meta desc too short ({len(desc)} chars)"))

    # Canonical
    m = re.search(r'<link rel="canonical" href="(.*?)"', html)
    canonical = m.group(1) if m else None
    if not canonical:
        issues.append(("HIGH", "missing canonical"))

    # H1 count
    h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if len(h1s) == 0:
        issues.append(("HIGH", "no H1"))
    elif len(h1s) > 1:
        issues.append(("HIGH", f"multiple H1s ({len(h1s)})"))

    # Images without alt
    imgs = re.findall(r'<img\b[^>]*>', html)
    noalt = [i for i in imgs if 'alt=' not in i]
    if noalt:
        issues.append(("MEDIUM", f"{len(noalt)} img(s) missing alt"))
    # Generic alt text
    generic = [i for i in imgs if 'alt="Blog post hero image"' in i]
    if generic:
        issues.append(("MEDIUM", f"{len(generic)} img(s) with generic alt text"))

    # Schema
    has_article = '"@type":"Article"' in html or '"@type": "Article"' in html
    has_faq = '"@type":"FAQPage"' in html or '"@type": "FAQPage"' in html

    # Word count of body (rough)
    body = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', body)
    words = len(text.split())
    if words < 350:
        issues.append(("HIGH", f"thin content ({words} words)"))

    # OG image path check (relative vs absolute)
    m = re.search(r'<meta property="og:image" content="(.*?)"', html)
    og_img = m.group(1) if m else None
    if not og_img:
        issues.append(("LOW", "missing og:image"))

    # Internal links to other blog posts
    internal_blog_links = len(re.findall(r'href="blog-[^"]+\.html"', html))

    # Hero image reference
    hero = re.search(r'src="(images/blog/[^"]+)"', html)
    hero_path = hero.group(1) if hero else None
    hero_missing = False
    if hero_path and not (REPO / hero_path).exists():
        hero_missing = True
        issues.append(("HIGH", f"hero image file missing: {hero_path}"))

    return {
        "file": path.name, "title": title, "title_len": len(title) if title else 0,
        "desc_len": len(desc) if desc else 0, "canonical": canonical,
        "h1_count": len(h1s), "words": words,
        "article_schema": has_article, "faq_schema": has_faq,
        "internal_blog_links": internal_blog_links,
        "issues": issues,
    }

def main():
    pages = sorted(REPO.glob("*.html"))
    results = [audit_page(p) for p in pages]

    # Duplicate titles
    titles = Counter(r["title"] for r in results if r["title"])
    dupes = {t: c for t, c in titles.items() if c > 1}

    # Sitemap coverage
    sitemap = (REPO / "sitemap.xml").read_text(encoding='utf-8') if (REPO / "sitemap.xml").exists() else ""
    sitemap_urls = set(re.findall(r'<loc>https?://[^/]+/([^<]*)</loc>', sitemap))
    on_disk = set(p.name for p in pages)
    not_in_sitemap = sorted(n for n in on_disk if n not in sitemap_urls and not sitemap_urls.__contains__(n))
    in_sitemap_not_disk = sorted(u for u in sitemap_urls if u and u not in on_disk)

    # Broken internal links
    broken = []
    for p in pages:
        html = p.read_text(encoding='utf-8', errors='replace')
        for href in re.findall(r'href="([a-zA-Z0-9\-_]+\.html)"', html):
            if not (REPO / href).exists():
                broken.append((p.name, href))

    # Summary
    total_issues = Counter()
    for r in results:
        for sev, _ in r["issues"]:
            total_issues[sev] += 1

    out = {
        "total_pages": len(pages),
        "issue_counts": dict(total_issues),
        "duplicate_titles": dupes,
        "pages_not_in_sitemap": not_in_sitemap,
        "sitemap_urls_missing_on_disk": in_sitemap_not_disk,
        "broken_internal_links": broken[:50],
        "broken_link_count": len(broken),
        "pages": results,
    }
    (REPO / "research" / "seo_audit_results.json").write_text(json.dumps(out, indent=2), encoding='utf-8')

    print(f"Pages scanned: {len(pages)}")
    print(f"Issue counts: {dict(total_issues)}")
    print(f"Duplicate titles: {len(dupes)}")
    for t, c in list(dupes.items())[:10]:
        print(f"  x{c}: {t[:70]}")
    print(f"Pages NOT in sitemap: {len(not_in_sitemap)}")
    for n in not_in_sitemap[:20]:
        print(f"  - {n}")
    print(f"Sitemap URLs missing on disk: {in_sitemap_not_disk}")
    print(f"Broken internal links: {len(broken)}")
    for src, tgt in broken[:20]:
        print(f"  {src} -> {tgt}")
    print("\nPages with CRITICAL/HIGH issues:")
    for r in results:
        crit = [i for i in r["issues"] if i[0] in ("CRITICAL", "HIGH")]
        if crit:
            print(f"  {r['file']}: {crit}")

if __name__ == "__main__":
    main()
