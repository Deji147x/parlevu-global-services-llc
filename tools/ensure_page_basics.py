"""Make every public page crawlable, shareable and trackable. Idempotent.

For each root page (and its upload-queue copy) this adds whatever is missing:
  - share tags: og:type/title/description/url/image + twitter:card
  - a hero image on blog posts and pillar pages (images/blog/<slug>.jpg must exist)
  - the lead script (parlevu-estimator.js), which feeds the Hermes lead API
  - a first-screen "Get my free cash offer" button under the headline (jumps to #offer)
  - an on-page offer form (data-parlevu-magnet="valuation") on blog posts,
    pillar pages and what-we-buy, tagged with the seller's situation when the
    page is about one (foreclosure, divorce, inherited, landlord)

Usage:
  python tools/ensure_page_basics.py            # dry run, prints what it would change
  python tools/ensure_page_basics.py --apply
"""
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = "https://parlevugloballlc.com/"
DEFAULT_OG = "images/blog/we-buy-houses.jpg"
SCRIPT_TAG = '<script src="/parlevu-estimator.js?v=20261116" defer data-api="https://api.parlevugloballlc.com"></script>'
SKIP = {"thank-you.html", "404.html"}
FORM_PAGES = re.compile(r"^(blog-.+|pillar-.+|sell-house-fast-.+|what-we-buy)\.html$")
NOT_POSTS = {"blog.html"}

SITUATIONS = [  # (filename pattern, data-situation, form heading)
    (r"foreclos", "foreclosure", "Behind on payments? Get a free, no-obligation cash offer before the auction"),
    (r"divorce", "divorce", "Selling in a divorce? Get one written as-is offer you can both review"),
    (r"inherit|probate", "inherited", "Inherited a house? Get a free, no-obligation as-is offer"),
    (r"tenant|landlord|rental", "tired landlord", "Selling a rental? Get a free as-is offer, tenants in place"),
    (r"fsbo|by-owner|without-realtor|zillow", None, "Selling by owner? Get a free backup cash offer to compare"),
]
DEFAULT_FORM_TITLE = "Get a free, no-obligation cash offer on your house"
TOP_CTA = ('<p class="article-cta-top" style="display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:0 0 28px">'
           '<a href="#offer" class="btn btn-primary">Get my free cash offer</a>'
           '<a href="tel:+16676468306" style="font-weight:600">or call (667) 646-8306</a></p>')


def img_size(rel):
    try:
        from PIL import Image
        with Image.open(REPO / rel) as im:
            return im.size
    except Exception:
        return 1200, 630


def attr(s):
    return html.escape(html.unescape(s), quote=True)


def fix(name, t, report):
    nl = "\r\n" if "\r\n" in t else "\n"
    title_m = re.search(r"<title>(.*?)</title>", t, re.S)
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', t)
    canon_m = re.search(r'<link rel="canonical" href="([^"]+)"/?>', t)
    if not canon_m:
        report.append("NO CANONICAL - skipped share tags")
    h2t = re.search(r'<h([12]) class="article-title">(.*?)</h\1>', t, re.S)
    head = h2t.group(2) if h2t else (title_m.group(1) if title_m else name)
    page_title = re.sub(r"<[^>]+>", "", head).strip()
    slug = name[:-5]
    hero_rel = None
    for cand in (f"images/blog/{slug[5:] if slug.startswith('blog-') else slug}.jpg", f"images/blog/{slug}.jpg"):
        if (REPO / cand).exists():
            hero_rel = cand
            break
    content_imgs = [s for s in re.findall(r'<img[^>]*src="([^"]+)"', t) if "logo" not in s]

    # 1. hero image on posts and pillars
    is_post = name.startswith("blog-") and name not in NOT_POSTS
    if not content_imgs and (is_post or name.startswith("pillar-")):
        if hero_rel:
            w, h = img_size(hero_rel)
            alt = attr(page_title)
            block = (f'<div style="margin-bottom:28px;border-radius:var(--radius-xl);overflow:hidden"><img decoding="async" '
                     f'src="{hero_rel}" alt="{alt}" width="{w}" height="{h}" style="width:100%;height:auto;display:block" '
                     f'fetchpriority="high"/></div>')
            if h2t:
                t = t.replace(h2t.group(0), h2t.group(0) + nl + "    " + block, 1)
                report.append(f"hero image {hero_rel}")
            else:
                m = re.search(r"\n<h2>", t)
                if m:
                    t = t[:m.start()] + nl + block + t[m.start():]
                    report.append(f"hero image {hero_rel} (before first h2)")
                else:
                    report.append("NO ANCHOR for hero image")
            content_imgs = [hero_rel]
        else:
            report.append(f"NO IMAGE FILE for hero ({slug})")

    # 2. share tags
    if canon_m:
        og_img = content_imgs[0] if content_imgs and not content_imgs[0].startswith("http") else DEFAULT_OG
        og_img = SITE + og_img.lstrip("/")
        want = [
            ('property="og:type"', f'<meta property="og:type" content="{"article" if is_post else "website"}"/>'),
            ('property="og:title"', f'<meta property="og:title" content="{attr(page_title)}"/>'),
            ('property="og:description"', f'<meta property="og:description" content="{desc_m.group(1) if desc_m else attr(page_title)}"/>'),
            ('property="og:url"', f'<meta property="og:url" content="{canon_m.group(1)}"/>'),
            ('property="og:image"', f'<meta property="og:image" content="{og_img}"/>'),
            ('name="twitter:card"', '<meta name="twitter:card" content="summary_large_image"/>'),
        ]
        add = [tag for key, tag in want if key not in t]
        if add:
            t = t.replace(canon_m.group(0), canon_m.group(0) + "".join(nl + "  " + a for a in add), 1)
            report.append("share tags: " + ", ".join(re.search(r'(?:property|name)="([^"]+)"', a).group(1) for a in add))

    # 3. offer form
    if FORM_PAGES.match(name) and name not in NOT_POSTS and "data-parlevu-magnet" not in t:
        sit, heading = None, DEFAULT_FORM_TITLE
        for pat, s, head in SITUATIONS:
            if re.search(pat, name):
                sit, heading = s, head
                break
        form = ('<div data-parlevu-magnet="valuation"' + (f' data-situation="{sit}"' if sit else "")
                + f' data-title="{attr(heading)}"></div>')
        anchors = [r'<div class="article-faq', r'<h2>(?:Frequently Asked|Questions About|Common Questions|FAQ)',
                   r'<div style="background:var\(--navy\)', r'\n</section>']
        for a in anchors:
            m = re.search(a, t)
            if m:
                t = t[:m.start()] + form + nl + nl + "    " + t[m.start():].lstrip(" ") if a.startswith("<div") \
                    else t[:m.start()] + nl + form + nl + t[m.start():]
                report.append(f"offer form ({sit or 'no tag'})")
                break
        else:
            report.append("NO ANCHOR for offer form")

    # 4. first-screen offer button that jumps to the on-page form
    if "data-parlevu-magnet" in t and 'id="offer"' not in t:
        t = t.replace("<div data-parlevu-magnet=", '<div id="offer" data-parlevu-magnet=', 1)
    h1a = re.search(r'<h1 class="article-title">.*?</h1>', t, re.S)
    if h1a and 'id="offer"' in t and "article-cta-top" not in t and "pillar-cta" not in t:
        end = h1a.end()
        img = re.match(r'\s*<div[^>]*>\s*<img[^>]*>\s*</div>', t[end:])
        if img:
            end += img.end()
        t = t[:end] + nl + "    " + TOP_CTA + t[end:]
        report.append("top offer button")

    # 5. lead script
    if "parlevu-estimator.js" not in t and "</body>" in t:
        t = t.replace("</body>", SCRIPT_TAG + nl + "</body>", 1)
        report.append("lead script")
    return t


def main():
    apply = "--apply" in sys.argv
    pages = sorted(p.name for p in REPO.glob("*.html") if p.name not in SKIP)
    changed = 0
    for name in pages:
        for p in (REPO / name, REPO / "upload-queue" / name):
            if not p.exists():
                continue
            t = p.read_bytes().decode("utf-8")
            report = []
            new = fix(name, t, report)
            if report and p.parent == REPO:
                print(f"{name}: " + "; ".join(report))
            if new != t:
                changed += 1
                if apply:
                    p.write_bytes(new.encode("utf-8"))
    print(f"\n{changed} files {'updated' if apply else 'would change'}")


if __name__ == "__main__":
    main()
