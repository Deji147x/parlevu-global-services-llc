"""On-page SEO standard for every public page. Idempotent.

  - Posts: the headline (h2.article-title) becomes the page's single <h1>; the
    category label in the dark header becomes a styled <p class="page-header-cat">.
  - <title>: 30-65 characters. Long titles drop the " | Parlevu ..." suffix;
    short ones gain " | Parlevu Global Services".
  - meta description: at least 110 characters. Short ones gain a call to action
    (og:description is kept in step when it matched the old text).

Usage:
  python tools/fix_onpage_seo.py            # dry run
  python tools/fix_onpage_seo.py --apply
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP = {"404.html", "thank-you.html"}
SUFFIX = " | Parlevu Global Services"
TITLE_OVERRIDES = {"what-we-buy.html": "What Houses We Buy in Maryland, Virginia &amp; DC | Parlevu Global"}
CTAS = [" Get a free, no-obligation as-is cash offer from Parlevu Global Services.",
        " Get a free, no-obligation cash offer.",
        " Free cash offer, no obligation."]


def fix(name, t, report):
    # 1. one real H1 per post
    if '<h2 class="article-title">' in t:
        h1 = re.search(r"(<div class=\"page-header-inner\">.*?)<h1>(.*?)</h1>", t, re.S) or \
             re.search(r"()<h1>(.*?)</h1>", t, re.S)
        if h1:
            t = t.replace(f"<h1>{h1.group(2)}</h1>", f'<p class="page-header-cat">{h1.group(2)}</p>', 1)
        t = re.sub(r'<h2 class="article-title">(.*?)</h2>', r'<h1 class="article-title">\1</h1>', t, count=1, flags=re.S)
        report.append("h1 = headline")

    # 2. title length
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    if m:
        old = m.group(1).strip()
        new = TITLE_OVERRIDES.get(name, old)
        if len(new) > 65 and " | " in new:
            new = new.split(" | ")[0].strip()
        elif len(new) < 30 and "Parlevu" not in new:
            new = new + SUFFIX
        if new != old:
            t = t.replace(m.group(0), f"<title>{new}</title>", 1)
            report.append(f"title {len(old)}->{len(new)}")

    # 3. description length
    d = re.search(r'<meta name="description" content="([^"]*)"', t)
    if d and len(d.group(1)) < 110:
        old = d.group(1)
        base = old.rstrip()
        if base and base[-1] not in ".!?":
            base += "."
        for cta in CTAS:
            if len(base + cta) <= 160:
                new = base + cta
                break
        else:
            new = base
        if new != old:
            t = t.replace(d.group(0), f'<meta name="description" content="{new}"', 1)
            t = t.replace(f'<meta property="og:description" content="{old}"',
                          f'<meta property="og:description" content="{new}"', 1)
            report.append(f"desc {len(old)}->{len(new)}")
    return t


def main():
    apply = "--apply" in sys.argv
    changed = 0
    for p in sorted(REPO.glob("*.html")):
        if p.name in SKIP:
            continue
        for f in (p, REPO / "upload-queue" / p.name):
            if not f.exists():
                continue
            t = f.read_bytes().decode("utf-8")
            report = []
            new = fix(p.name, t, report)
            if report and f.parent == REPO:
                print(f"{p.name}: " + "; ".join(report))
            if new != t:
                changed += 1
                if apply:
                    f.write_bytes(new.encode("utf-8"))
    print(f"\n{changed} files {'updated' if apply else 'would change'}")


if __name__ == "__main__":
    main()
