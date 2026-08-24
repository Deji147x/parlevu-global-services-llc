"""Replace stock-photo fallbacks with generated hero images.

When Pollinations fails, publish_next.py falls back to a hotlinked Unsplash
photo from a pool of 8. Across many posts that pool repeats badly (one image
was shared by 6 posts on 2026-08-24). This retries generation for every post
still on a fallback and rewrites the references in place.

Idempotent: posts that already have images/blog/{slug}.jpg are skipped, and a
post is only rewritten once its image is actually on disk.

Usage:
  python tools/backfill_images.py                # dry run, shows what it would do
  python tools/backfill_images.py --apply        # generate and rewrite
  python tools/backfill_images.py --apply --limit 5   # pace against rate limits
"""
import argparse
import glob
import io
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BLOG = REPO / "blog.html"
UPLOAD_QUEUE = REPO / "upload-queue"

sys.path.insert(0, str(REPO / "tools"))
from gen_image import generate as gen_img  # noqa: E402

STOCK = re.compile(r'https://images\.unsplash\.com/[^"\']+')


def posts_on_fallback():
    out = []
    for fn in sorted(glob.glob(str(REPO / "blog-*.html"))):
        p = Path(fn)
        slug = p.name[len("blog-"):-len(".html")]
        html = p.read_text(encoding="utf-8")
        if STOCK.search(html):
            out.append((slug, p))
    return out


def rewrite(path: Path, slug: str, new_src: str) -> bool:
    html = path.read_text(encoding="utf-8")
    updated = STOCK.sub(new_src, html)
    if updated == html:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def rewrite_card(slug: str, new_src: str) -> bool:
    """Swap the stock URL inside just this post's card on the blog index."""
    html = BLOG.read_text(encoding="utf-8")
    marker = f"<!-- Post: {slug} "
    i = html.find(marker)
    if i == -1:
        return False
    end = html.find("<!-- Post:", i + len(marker))
    if end == -1:
        end = len(html)
    block = html[i:end]
    new_block = STOCK.sub(new_src, block)
    if new_block == block:
        return False
    BLOG.write_text(html[:i] + new_block + html[end:], encoding="utf-8", newline="\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually generate and rewrite")
    ap.add_argument("--limit", type=int, help="process at most N posts this run")
    ap.add_argument("--delay", type=int, default=10, help="seconds between posts (rate limiting)")
    args = ap.parse_args()

    targets = posts_on_fallback()
    if args.limit:
        targets = targets[:args.limit]
    if not targets:
        print("No posts are using a stock fallback.")
        return

    print(f"{'APPLY' if args.apply else 'DRY RUN'} - {len(targets)} post(s) on stock photos\n")
    done = failed = 0
    for n, (slug, path) in enumerate(targets, 1):
        print(f"[{n}/{len(targets)}] {slug}")
        if not args.apply:
            continue
        prompt = f"{slug.replace('-', ' ')}, real estate editorial photography, no text, no watermark"
        result = gen_img(slug, prompt)
        if result.startswith("http"):
            print("    still failing - left on fallback")
            failed += 1
        else:
            a = rewrite(path, slug, result)
            b = rewrite_card(slug, result)
            uq = UPLOAD_QUEUE / path.name
            if uq.exists():
                rewrite(uq, slug, result)
            print(f"    generated {result}  (post={a} card={b})")
            done += 1
        if n < len(targets):
            time.sleep(args.delay)

    if args.apply:
        print(f"\nbackfilled {done}, still failing {failed}")
        if done:
            print("blog.html and upload-queue updated; commit when ready")


if __name__ == "__main__":
    main()
